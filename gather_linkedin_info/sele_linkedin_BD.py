import requests
import time
import argparse
import json
from dotenv import load_dotenv
import os

start_time = time.time()
# Load the .env file
load_dotenv()

# # Access API_KEY, DATASET_ID, and BASE
# API_KEY = os.getenv("API_KEY")
# DATASET_ID = os.getenv("DATASET_ID")
# BASE = os.getenv("BASE")

# def get_profile_brightdata(link, api_key):
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json",
#     }
#     params = {
#         "dataset_id": DATASET_ID,
#         "include_errors": "true",
#     }

#     # Step 1: Trigger snapshot
#     trigger = requests.post(
#         f"{BASE}/trigger",
#         headers=headers,
#         params=params,
#         json=[{"url": link}],
#     )
#     trigger.raise_for_status()
#     snap_resp = trigger.json()
#     snapshot_id = snap_resp.get("snapshot_id")
#     if not snapshot_id:
#         raise RuntimeError(f"No snapshot_id in trigger response: {snap_resp}")

#     # Step 2: Poll for results
#     download_url = f"{BASE}/snapshot/{snapshot_id}"
#     for attempt in range(30):  # up to 2 minutes
#         r = requests.get(download_url, headers=headers)

#         if r.status_code == 202:
#             print(f"[{attempt+1:02d}/30] Not ready yet...")
#             time.sleep(5)
#             continue

#         if r.status_code == 404:
#             raise RuntimeError(f"Snapshot not found: {snapshot_id}")
        
#         r.raise_for_status()
#         print(json.dumps(r.json(), indent=2))
#         return r.json()

#     raise TimeoutError("Timed out waiting for snapshot to be ready")

# def parse_profile(profile_data):
#     """Parses the BrightData response and formats it with all available fields."""
#     return {
#         # Identifiers & URLs
#         # "linkedin_id": profile_data.get("id") or profile_data.get("linkedin_id"),
#         # "input_url": profile_data.get("input", {}).get("url") or profile_data.get("input_url"),
#         # "profile_url": profile_data.get("url"),

#         # Basic info
#         "name": profile_data.get("name"),
#         "city": profile_data.get("city"),
#         "country_code": profile_data.get("country_code"),
#         "location": profile_data.get("location"),
#         "full_about" : profile_data.get("about"),

#         # Company
#         # "current_company": profile_data.get("current_company"),
#         # "current_company_name": profile_data.get("current_company_name"),
#         # "current_company_company_id": profile_data.get("current_company_company_id"),

#         # Visuals
#         "image": profile_data.get("avatar"),
#         "banner_image": profile_data.get("banner_image"),
#         "default_avatar": profile_data.get("default_avatar"),

#         # Stats
#         # "followers": profile_data.get("followers"),
#         # "connections": profile_data.get("connections"),

#         # Summary / About
#         # "people_also_viewed": profile_data.get("people_also_viewed", []),
#         # "similar_profiles": profile_data.get("similar_profiles", []),
#         # "activity": profile_data.get("activity", []),

#         # Education
#         #"education_details": profile_data.get("educations_details"),
#         "education": profile_data.get("education", []),

#         # Experience / Organizations
#         "experience": profile_data.get("experience") or [],
#         "organizations": profile_data.get("organizations", []),

#         # Extras
#         #"honors_and_awards": profile_data.get("honors_and_awards"),
#         #"memorialized_account": profile_data.get("memorialized_account"),
#         #"timestamp": profile_data.get("timestamp"),
#     }

# def main(INPUT_FILE, OUTPUT_FILE):
#     with open(INPUT_FILE, "r", encoding="utf-8") as f:
#         people = json.load(f)
#     print("Loaded input file.")

#     all_profiles_data = []

#     for person in people:
#         for index, profile in enumerate(person.get("search_results", [])):
#             profile_url = profile["url"]  # Extract just the URL
#             print(f"Fetching: {profile_url}")
#             try:
#                 raw = get_profile_brightdata(profile_url, API_KEY)
#                 parsed = parse_profile(raw)

#                 parsed.update({
#                     "index": index,
#                     "profile_url": profile_url,
#                     "original_name": person.get("name"),
#                     "human":person.get("human"),
#                     "drive_link": person.get("image")
#                 })

#                 all_profiles_data.append(parsed)
#             except Exception as e:
#                 print(f"Error fetching {profile_url}: {e}")
#                 all_profiles_data.append({
#                     "index": index,
#                     "profile_url": profile_url,
#                     "original_name": person.get("name"),
#                     "name": None,
#                     "one_liner_about": None,
#                     "full_about": None,
#                     "experience": [],
#                     "education": [],
#                     "human":person.get("human"),
#                     "drive_link": person.get("image"),
#                     "error": str(e),
#                 })

#     # Save all results
#     with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
#         json.dump(all_profiles_data, f, indent=2)
#     print(f"Saved all profiles to {OUTPUT_FILE}")

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Fetch LinkedIn profiles from BrightData API.")
#     parser.add_argument("input_path", type=str, help="Path to input JSON file")
#     parser.add_argument("output_path", type=str, help="Path to output JSON file")

#     args = parser.parse_args()
#     main(args.input_path, args.output_path)


# import os
# import asyncio
# import aiohttp
# import argparse
# import json
# from datetime import datetime
# from dotenv import load_dotenv

# # Utility to timestamp logs
# def log(msg):
#     print(f"[{datetime.utcnow().isoformat()}] {msg}")

# # Load environment
# load_dotenv()
# API_KEY = os.getenv("API_KEY")
# DATASET_ID = os.getenv("DATASET_ID")
# BASE = os.getenv("BASE")

# # Concurrency, polling, and retry settings
# MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", 3))         # Lower default to avoid overloading
# POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", 5))         # seconds between polling
# MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 50))            # max polls per snapshot
# MAX_RETRIES = int(os.getenv("MAX_RETRIES", 2))               # trigger+poll retries on timeout

# async def trigger_snapshot(session, url):
#     log(f"trigger_snapshot: URL={url}")
#     headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
#     params = {"dataset_id": DATASET_ID, "include_errors": "true"}
#     resp = await session.post(f"{BASE}/trigger", headers=headers, params=params, json=[{"url": url}])
#     log(f"trigger_snapshot: status={resp.status}")
#     resp.raise_for_status()
#     data = await resp.json()
#     snapshot_id = data.get("snapshot_id")
#     if not snapshot_id:
#         raise RuntimeError(f"No snapshot_id in trigger response: {data}")
#     log(f"trigger_snapshot: snapshot_id={snapshot_id}")
#     return snapshot_id

# async def poll_snapshot(session, snapshot_id):
#     log(f"poll_snapshot: snapshot_id={snapshot_id} start")
#     headers = {"Authorization": f"Bearer {API_KEY}"}
#     url = f"{BASE}/snapshot/{snapshot_id}?format=json"

#     for attempt in range(1, MAX_ATTEMPTS + 1):
#         log(f"poll_snapshot[{snapshot_id}]: attempt {attempt}/{MAX_ATTEMPTS}")
#         async with session.get(url, headers=headers) as resp:
#             status = resp.status
#             ctype = resp.headers.get("Content-Type", "")
#             log(f"poll_snapshot[{snapshot_id}]: status={status}, Content-Type={ctype}")
#             if status == 202:
#                 await asyncio.sleep(POLL_INTERVAL)
#                 continue
#             if status == 404:
#                 raise RuntimeError(f"Snapshot not found: {snapshot_id}")
#             if "application/json" not in ctype:
#                 text = await resp.text()
#                 raise RuntimeError(f"Unexpected content-type {ctype}: {text[:200]!r}")

#             raw = await resp.json()
#             # Unwrap list responses
#             if isinstance(raw, list):
#                 log(f"poll_snapshot[{snapshot_id}]: unwrapping list of length {len(raw)}")
#                 data = raw[0] if raw else {}
#             else:
#                 data = raw

#             log(f"poll_snapshot[{snapshot_id}]: success JSON keys={list(data.keys())}")
#             print(data)
#             return data

#     raise TimeoutError(f"Snapshot {snapshot_id} did not become ready after {MAX_ATTEMPTS} attempts")

# async def fetch_profile(semaphore, session, url, meta):
#     log(f"fetch_profile: start for URL={url}")
#     async with semaphore:
#         for retry in range(1, MAX_RETRIES + 1):
#             try:
#                 snapshot_id = await trigger_snapshot(session, url)
#                 data = await poll_snapshot(session, snapshot_id)
#                 parsed = parse_profile(data)
#                 parsed.update(meta)
#                 log(f"fetch_profile: success URL={url}")
#                 return parsed
#             except TimeoutError:
#                 log(f"fetch_profile: timeout on retry {retry}/{MAX_RETRIES} for URL={url}")
#                 if retry < MAX_RETRIES:
#                     log(f"fetch_profile: re-triggering snapshot for URL={url}")
#                     continue
#                 return {**meta, "error": f"Timeout after {MAX_ATTEMPTS} polls"}
#             except Exception as e:
#                 log(f"fetch_profile: error URL={url}, error={e}")
#                 return {**meta, "error": str(e)}


# def parse_profile(data):
#     log(f"parse_profile: keys={list(data.keys())}")
#     return {
#         "name": data.get("name"),
#         "city": data.get("city"),
#         "location": data.get("location"),
#         "full_about": data.get("about"),
#         "image": data.get("avatar"),
#         "education": data.get("education", []),
#         "experience": data.get("experience", []),
#         "organizations": data.get("organizations", []),
#     }

# async def main_async(input_path, output_path):
#     log(f"main_async: loading input file {input_path}")
#     people = json.load(open(input_path, 'r', encoding='utf-8'))
#     log(f"main_async: {len(people)} entries loaded")

#     sem = asyncio.Semaphore(MAX_CONCURRENT)
#     connector = aiohttp.TCPConnector(limit_per_host=MAX_CONCURRENT)
#     timeout = aiohttp.ClientTimeout(total=None)

#     async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
#         tasks = []
#         for person in people:
#             base_meta = {"original_name": person.get("name"), "human": person.get("human"), "drive_link": person.get("image")}
#             for idx, res in enumerate(person.get("search_results", [])):
#                 link = res.get("url")
#                 meta = {**base_meta, "index": idx, "profile_url": link}
#                 tasks.append(fetch_profile(sem, session, link, meta))
#         log(f"main_async: scheduled {len(tasks)} tasks with concurrency={MAX_CONCURRENT}")
#         results = await asyncio.gather(*tasks)
#         log(f"main_async: completed tasks")

#     with open(output_path, 'w', encoding='utf-8') as f:
#         json.dump(results, f, indent=2)
#     log(f"main_async: results saved to {output_path}")

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Async LinkedIn fetch via BrightData")
#     parser.add_argument("input_path", help="Path to input JSON file")
#     parser.add_argument("output_path", help="Path to output JSON file")
#     args = parser.parse_args()
#     log(f"__main__: args={args}")
#     asyncio.run(main_async(args.input_path, args.output_path))

import os
import asyncio
import aiohttp
import argparse
import json
from datetime import datetime
from dotenv import load_dotenv

# Utility to timestamp logs
def log(msg):
    print(f"[{datetime.utcnow().isoformat()}] {msg}")

# Load environment
load_dotenv()
API_KEY = os.getenv("API_KEY")
DATASET_ID = os.getenv("DATASET_ID")
BASE = os.getenv("BASE")

# Concurrency, polling, and retry settings
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", 7))
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", 5))
MAX_ATTEMPTS = int(os.getenv("MAX_ATTEMPTS", 50))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 2))

# Global tracking
TOTAL_TASKS = 0
PROCESSED_COUNT = 0
PROCESSED_LOCK = asyncio.Lock()

async def trigger_snapshot(session, url):
    log(f"trigger_snapshot: URL={url}")
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    params = {"dataset_id": DATASET_ID, "include_errors": "true"}
    resp = await session.post(f"{BASE}/trigger", headers=headers, params=params, json=[{"url": url}])
    log(f"trigger_snapshot: status={resp.status}")
    resp.raise_for_status()
    data = await resp.json()
    snapshot_id = data.get("snapshot_id")
    if not snapshot_id:
        raise RuntimeError(f"No snapshot_id in trigger response: {data}")
    log(f"trigger_snapshot: snapshot_id={snapshot_id}")
    return snapshot_id

async def poll_snapshot(session, snapshot_id):
    log(f"poll_snapshot: snapshot_id={snapshot_id} start")
    headers = {"Authorization": f"Bearer {API_KEY}"}
    url = f"{BASE}/snapshot/{snapshot_id}?format=json"

    for attempt in range(1, MAX_ATTEMPTS + 1):
        log(f"poll_snapshot[{snapshot_id}]: attempt {attempt}/{MAX_ATTEMPTS}")
        async with session.get(url, headers=headers) as resp:
            status = resp.status
            ctype = resp.headers.get("Content-Type", "")
            log(f"poll_snapshot[{snapshot_id}]: status={status}, Content-Type={ctype}")
            if status == 202:
                await asyncio.sleep(POLL_INTERVAL)
                continue
            if status == 404:
                raise RuntimeError(f"Snapshot not found: {snapshot_id}")
            if "application/json" not in ctype:
                text = await resp.text()
                raise RuntimeError(f"Unexpected content-type {ctype}: {text[:200]!r}")

            raw = await resp.json()
            # Unwrap list responses
            if isinstance(raw, list):
                log(f"poll_snapshot[{snapshot_id}]: unwrapping list of length {len(raw)}")
                data = raw[0] if raw else {}
            else:
                data = raw

            log(f"poll_snapshot[{snapshot_id}]: success JSON keys={list(data.keys())}")
            print(data)
            return data

    raise TimeoutError(f"Snapshot {snapshot_id} did not become ready after {MAX_ATTEMPTS} attempts")

async def fetch_profile(semaphore, session, url, meta):
    log(f"fetch_profile: waiting for slot for URL={url}")
    async with semaphore:
        # Log current concurrency
        active = MAX_CONCURRENT - semaphore._value
        log(f"Active workers: {active}/{MAX_CONCURRENT}")
        for retry in range(1, MAX_RETRIES + 1):
            try:
                snapshot_id = await trigger_snapshot(session, url)
                data = await poll_snapshot(session, snapshot_id)
                parsed = parse_profile(data)
                parsed.update(meta)

                # Update processed count
                global PROCESSED_COUNT
                async with PROCESSED_LOCK:
                    PROCESSED_COUNT += 1
                    log(f"Completed {PROCESSED_COUNT}/{TOTAL_TASKS} profiles")

                log(f"fetch_profile: success URL={url}")
                return parsed
            except TimeoutError:
                log(f"fetch_profile: timeout on retry {retry}/{MAX_RETRIES} for URL={url}")
                if retry < MAX_RETRIES:
                    log(f"fetch_profile: retrying ({retry+1}/{MAX_RETRIES}) for URL={url}")
                    continue
                return {**meta, "error": f"Timeout after {MAX_ATTEMPTS} polls"}
            except Exception as e:
                log(f"fetch_profile: error URL={url}, error={e}")
                return {**meta, "error": str(e)}


def parse_profile(data):
    log(f"parse_profile: keys={list(data.keys())}")
    return {
        "name": data.get("name"),
        "city": data.get("city"),
        "location": data.get("location"),
        "full_about": data.get("about"),
        "image": data.get("avatar"),
        "education": data.get("education", []),
        "experience": data.get("experience", []),
        "organizations": data.get("organizations", []),
    }

async def main_async(input_path, output_path):
    log(f"main_async: loading input file {input_path}")
    people = json.load(open(input_path, 'r', encoding='utf-8'))
    log(f"main_async: {len(people)} people entries loaded")

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    connector = aiohttp.TCPConnector(limit_per_host=MAX_CONCURRENT)
    timeout = aiohttp.ClientTimeout(total=None)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        for person in people:
            name = person.get("name")
            profiles = person.get("search_results", [])
            log(f"Assigning {len(profiles)} profiles to fetch for person: {name}")
            base_meta = {"original_name": name, "human": person.get("human"), "drive_link": person.get("image")}
            for idx, res in enumerate(profiles):
                link = res.get("url")
                meta = {**base_meta, "index": idx, "profile_url": link}
                tasks.append(fetch_profile(sem, session, link, meta))

        # Total tasks
        global TOTAL_TASKS
        TOTAL_TASKS = len(tasks)
        log(f"main_async: scheduled {TOTAL_TASKS} total tasks with concurrency={MAX_CONCURRENT}")

        results = await asyncio.gather(*tasks)
        log(f"main_async: completed all tasks")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    log(f"main_async: results saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Async LinkedIn fetch via BrightData")
    parser.add_argument("input_path", help="Path to input JSON file")
    parser.add_argument("output_path", help="Path to output JSON file")
    args = parser.parse_args()
    log(f"__main__: args={args}")
    asyncio.run(main_async(args.input_path, args.output_path))






end_time = time.time()
print(f"Time taken: {end_time - start_time:.4f} seconds")
