import os
import time
import random
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

# Set these safely using environment variables or a .env file
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Start Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://www.linkedin.com/login")

# Wait a random 20-30 seconds before interacting
time.sleep(random.uniform(20, 30))

# (A) Uncheck "Remember me" box if it's checked
try:
    checkbox = driver.find_element(By.ID, "rememberMeOptIn-checkbox")
    if checkbox.is_selected():
        label = driver.find_element(By.CSS_SELECTOR, "label[for='rememberMeOptIn-checkbox']")
        label.click()
except Exception as e:
    print("Could not uncheck Remember me:", e)

# (B) Input credentials
username_input = driver.find_element(By.ID, "username")
password_input = driver.find_element(By.ID, "password")

username_input.send_keys(LINKEDIN_USERNAME)
time.sleep(random.uniform(0,30))  # Brief pause before password
password_input.send_keys(LINKEDIN_PASSWORD)
password_input.send_keys(Keys.RETURN)
time.sleep(random.uniform(0,30))

input_file = "output/google.json"  # Replace with your actual file name
with open(input_file, "r", encoding="utf-8") as f:
    file = json.load(f)
print("file loaded")
all_profiles_data = []
print(file[0])
exit
# Wait for login to complete (random 10 seconds)
time.sleep(random.uniform(0, 10))
for person in file:
   for index, profile_url in enumerate(person.get("search_results", [])):
    try:

        print(f"Visiting: {profile_url}")
        driver.get(profile_url)


        # Wait to allow the profile page to load (random 5-10 seconds)
        time.sleep(random.uniform(5, 10))

        data = {
            "index": index,
            "profile_url": profile_url,
            "original_name": person.get("name")
        }
        # Optionally, save the page HTML
        # with open("profile.html", "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)

        print("Profile loaded successfully.")


            # 1. Name extraction
        try:
                name_element = driver.find_element(By.CSS_SELECTOR, "h1.inline.t-24.v-align-middle.break-words")
                name = name_element.text.strip()
                data["name"] = name
                print(f"[DEBUG] Extracted Name: {name}")
        except Exception as e:
                print(f"[DEBUG] Error extracting Name: {e}")
                data["name"] = None

            # 2. One liner About extraction
        try:
                # This selector matches a div with both classes "text-body-medium" and "break-words"
                one_liner_element = driver.find_element(By.CSS_SELECTOR, "div.text-body-medium.break-words")
                one_liner_about = one_liner_element.text.strip()
                data["one_liner_about"] = one_liner_about
                print(f"[DEBUG] Extracted one-liner About: {one_liner_about}")
        except Exception as e:
                print(f"[DEBUG] Error extracting one-liner About: {e}")
                data["one_liner_about"] = None

            # 3. Full About extraction
        try:
                # The approach is to locate a section with a header containing "About"
                # then extract all the text content from that section.
                about_section = None
                try:
                    # Try locating section by searching for an h2 element with "About"
                    about_section = driver.find_element(By.XPATH, "//section[.//h2[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'about')]]")
                except Exception as inner_e:
                    print(f"[DEBUG] Could not find About section via h2 search: {inner_e}")

                if about_section:
                    full_about_text = about_section.text.strip()
                    # Remove header text "About" if present
                    if full_about_text.lower().startswith("about"):
                        full_about_text = full_about_text[len("about"):].strip()
                    data["full_about"] = full_about_text[len("about"):].strip()
                    print(f"[DEBUG] Extracted Full About: {full_about_text[:60]}...")  # Print first 60 chars
                else:
                    print("[DEBUG] About section not found.")
                    data["full_about"] = None

        except Exception as e:
                print(f"[DEBUG] Error extracting Full About: {e}")
                data["full_about"] = None

            # 4. Experience extraction
        def deduplicate_text(text):
            """Remove duplicate lines from a text string while preserving order."""
            seen = set()
            result = []
            for line in text.splitlines():
                line = line.strip()
                if line and line not in seen:
                    seen.add(line)
                    result.append(line)
            return " ".join(result)

        experiences = []
        try:
            experience_elements = driver.find_elements(By.CSS_SELECTOR, "a[data-field='experience_company_logo']")
            print(f"[DEBUG] Found {len(experience_elements)} experience entries.")
            
            for idx, exp in enumerate(experience_elements):
                try:
                    role_el = exp.find_element(By.CSS_SELECTOR, "div.display-flex.align-items-center.mr1.hoverable-link-text.t-bold span")
                    role = role_el.text.strip()
                except Exception as e:
                    print(f"[DEBUG] Experience {idx}: Could not extract Role: {e}")
                    role = None

                try:
                    company_el = exp.find_element(By.CSS_SELECTOR, "span.t-14.t-normal")
                    company_raw = company_el.text.strip()
                    company = deduplicate_text(company_raw)
                except Exception as e:
                    print(f"[DEBUG] Experience {idx}: Could not extract Company: {e}")
                    company = None

                date = None
                location = None
                try:
                    details = exp.find_elements(By.CSS_SELECTOR, "span.t-14.t-normal.t-black--light")
                    if len(details) >= 1:
                        try:
                            date_el = details[0].find_element(By.CSS_SELECTOR, "span[aria-hidden='true']")
                            date = date_el.text.strip()
                            print("date added is", date)
                        except Exception as e:
                            print(f"[DEBUG] Experience {idx}: Fallback to full date text due to: {e}")
                            date = deduplicate_text(details[0].text.strip())
                    if len(details) >= 2:
                        try:
                            loc_el = details[1].find_element(By.CSS_SELECTOR, "span[aria-hidden='true']")
                            location = loc_el.text.strip()
                        except Exception as e:
                            print(f"[DEBUG] Experience {idx}: Fallback to full location text due to: {e}")
                            location = deduplicate_text(details[1].text.strip())
                except Exception as e:
                    print(f"[DEBUG] Experience {idx}: Could not extract date/location: {e}")
                # Skip if all fields are None
                if not any([role, company, date, location]):
                    print(f"[DEBUG] Experience {idx}: Skipped - all fields are None.")
                    continue

                exp_data = {
                    "role": role,
                    "company": company,
                    "date": date,
                    "location": location
                }
                print(f"[DEBUG] Experience {idx}: {exp_data}")
                experiences.append(exp_data)
        except Exception as e:
            print(f"[DEBUG] Error extracting Experience: {e}")

        data["experience"] = experiences

            # 5. Education extraction
        education = []

        try:
            # Step 1: Store current URL
            original_url = driver.current_url

            # Step 2: Go to the /details/education/ page
            if "linkedin.com/in/" in original_url:
                education_url = original_url.split("?")[0].replace("in.linkedin.com", "www.linkedin.com") + "/details/education/"
                driver.get(education_url)
                time.sleep(2)  # Wait for page to load — increase if needed

                # Step 3: Extract education elements
                education_elements = driver.find_elements(
                    By.XPATH,
                    "//section[contains(@class, 'artdeco-card')]//li[contains(@class, 'artdeco-list__item')]"
                )
                print(f"[DEBUG] Found {len(education_elements)} education entries.")

                for idx, edu in enumerate(education_elements):
                    try:
                        institution_el = edu.find_element(By.CSS_SELECTOR, "span.t-bold span[aria-hidden='true']")
                        institution = institution_el.text.strip()
                    except Exception as e:
                        print(f"[DEBUG] Education {idx}: Could not extract institution: {e}")
                        institution = None

                    try:
                        degree_el = edu.find_element(By.CSS_SELECTOR, "span.t-normal.t-14 span[aria-hidden='true']")
                        degree = degree_el.text.strip()
                    except Exception as e:
                        print(f"[DEBUG] Education {idx}: Could not extract degree: {e}")
                        degree = None

                    if institution or degree:
                        edu_data = {"institution": institution, "degree": degree}
                        print(f"[DEBUG] Education {idx}: {edu_data}")
                        education.append(edu_data)
                    else:
                        print(f"[DEBUG] Education {idx}: Skipped due to empty fields.")

            # Step 4: Return to original page
            driver.get(original_url)
            time.sleep(1)

        except Exception as e:
            print(f"[DEBUG] Error extracting Education: {e}")

        data["education"] = education
        time.sleep(random.uniform(0,13))  # Wait to load
    except Exception as e:
            print(f"Error visiting {profile_url}: {e}")
    all_profiles_data.append(data)

output_file = "linkedin_profiles_all_google.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_profiles_data, f, indent=2)
print(f"[DEBUG] All profiles data written to {output_file}")
# Done
driver.quit()