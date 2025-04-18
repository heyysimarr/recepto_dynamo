import requests
import time
import argparse
import json
from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Access API_KEY, DATASET_ID, and BASE
API_KEY = os.getenv("API_KEY")
DATASET_ID = os.getenv("DATASET_ID")
BASE = os.getenv("BASE")

def get_profile_brightdata(link, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    params = {
        "dataset_id": DATASET_ID,
        "include_errors": "true",
    }

    # Step 1: Trigger snapshot
    trigger = requests.post(
        f"{BASE}/trigger",
        headers=headers,
        params=params,
        json=[{"url": link}],
    )
    trigger.raise_for_status()
    snap_resp = trigger.json()
    snapshot_id = snap_resp.get("snapshot_id")
    if not snapshot_id:
        raise RuntimeError(f"No snapshot_id in trigger response: {snap_resp}")

    # Step 2: Poll for results
    download_url = f"{BASE}/snapshot/{snapshot_id}"
    for attempt in range(30):  # up to 2 minutes
        r = requests.get(download_url, headers=headers)

        if r.status_code == 202:
            print(f"[{attempt+1:02d}/30] Not ready yet...")
            time.sleep(5)
            continue

        if r.status_code == 404:
            raise RuntimeError(f"Snapshot not found: {snapshot_id}")
        
        r.raise_for_status()
        print(json.dumps(r.json(), indent=2))
        return r.json()

    raise TimeoutError("Timed out waiting for snapshot to be ready")

def parse_profile(profile_data):
    """Parses the BrightData response and formats it with all available fields."""
    return {
        # Identifiers & URLs
        # "linkedin_id": profile_data.get("id") or profile_data.get("linkedin_id"),
        # "input_url": profile_data.get("input", {}).get("url") or profile_data.get("input_url"),
        # "profile_url": profile_data.get("url"),

        # Basic info
        "name": profile_data.get("name"),
        "city": profile_data.get("city"),
        "country_code": profile_data.get("country_code"),
        "location": profile_data.get("location"),
        "full_about" : profile_data.get("about"),

        # Company
        # "current_company": profile_data.get("current_company"),
        # "current_company_name": profile_data.get("current_company_name"),
        # "current_company_company_id": profile_data.get("current_company_company_id"),

        # Visuals
        "image": profile_data.get("avatar"),
        "banner_image": profile_data.get("banner_image"),
        "default_avatar": profile_data.get("default_avatar"),

        # Stats
        # "followers": profile_data.get("followers"),
        # "connections": profile_data.get("connections"),

        # Summary / About
        # "people_also_viewed": profile_data.get("people_also_viewed", []),
        # "similar_profiles": profile_data.get("similar_profiles", []),
        # "activity": profile_data.get("activity", []),

        # Education
        #"education_details": profile_data.get("educations_details"),
        "education": profile_data.get("education", []),

        # Experience / Organizations
        "experience": profile_data.get("experience") or [],
        "organizations": profile_data.get("organizations", []),

        # Extras
        #"honors_and_awards": profile_data.get("honors_and_awards"),
        #"memorialized_account": profile_data.get("memorialized_account"),
        #"timestamp": profile_data.get("timestamp"),
    }

def main(INPUT_FILE, OUTPUT_FILE):
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        people = json.load(f)
    print("Loaded input file.")

    all_profiles_data = []

    for person in people:
        for index, profile in enumerate(person.get("search_results", [])):
            profile_url = profile["url"]  # Extract just the URL
            print(f"Fetching: {profile_url}")
            try:
                raw = get_profile_brightdata(profile_url, API_KEY)
                parsed = parse_profile(raw)

                parsed.update({
                    "index": index,
                    "profile_url": profile_url,
                    "original_name": person.get("name"),
                    "human":person.get("human"),
                    "drive_link": person.get("image")
                })

                all_profiles_data.append(parsed)
            except Exception as e:
                print(f"Error fetching {profile_url}: {e}")
                all_profiles_data.append({
                    "index": index,
                    "profile_url": profile_url,
                    "original_name": person.get("name"),
                    "name": None,
                    "one_liner_about": None,
                    "full_about": None,
                    "experience": [],
                    "education": [],
                    "human":person.get("human"),
                    "drive_link": person.get("image"),
                    "error": str(e),
                })
            break
        break

    # Save all results
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_profiles_data, f, indent=2)
    print(f"Saved all profiles to {OUTPUT_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch LinkedIn profiles from BrightData API.")
    parser.add_argument("input_path", type=str, help="Path to input JSON file")
    parser.add_argument("output_path", type=str, help="Path to output JSON file")

    args = parser.parse_args()
    main(args.input_path, args.output_path)
