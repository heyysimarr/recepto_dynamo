import os
import time
import random
import sys
from selenium.webdriver.chrome.options import Options
import json
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

class LinkedInScraper:
    def __init__(self, input_file, output_file):
        self.username = os.getenv("LINKEDIN_USERNAME")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        self.input_file = input_file
        self.output_file = output_file
        self.driver = self._init_driver()
        self.profiles = []
        self._load_input_file()

    def _init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--log-level=3")
        options.add_argument("--start-maximized")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def _load_input_file(self):
        with open(self.input_file, "r", encoding="utf-8") as f:
            self.people = json.load(f)
        print("[INFO] Input file loaded.")

    def login(self):
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(random.uniform(20, 30))

        try:
            checkbox = self.driver.find_element(By.ID, "rememberMeOptIn-checkbox")
            if checkbox.is_selected():
                label = self.driver.find_element(By.CSS_SELECTOR, "label[for='rememberMeOptIn-checkbox']")
                label.click()
        except Exception as e:
            print("[WARN] Could not uncheck 'Remember me':", e)

        self.driver.find_element(By.ID, "username").send_keys(self.username)
        time.sleep(random.uniform(0, 10))
        self.driver.find_element(By.ID, "password").send_keys(self.password + Keys.RETURN)
        time.sleep(random.uniform(5, 10))

    def scrape(self):
        for person in self.people:
            for idx, url_info in enumerate(person.get("search_results", [])):
                try:
                    url = url_info["url"] if isinstance(url_info, dict) else url_info
                    print(f"[INFO] Visiting: {url}")
                    profile = LinkedInProfile(self.driver, person["name"], url, idx, person["human"], person["image"])
                    profile_data = profile.extract_all()
                    self.profiles.append(profile_data)
                except Exception as e:
                    print(f"[ERROR] Failed to process {url}: {e}")
                #break
            #break
        self._save_output()

    def _save_output(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, indent=2)
        print(f"[INFO] Scraped data saved to {self.output_file}")

    def close(self):
        self.driver.quit()

class LinkedInProfile:
    def __init__(self, driver, original_name, profile_url, index, human, drive):
        self.driver = driver
        self.original_name = original_name
        self.profile_url = profile_url
        self.human = human
        self.drive = drive
        self.index = index
        self.data = {
            "index": index,
            "profile_url": profile_url,
            "original_name": original_name,
            "human":human,
            "drive_link": drive
        }

    def extract_all(self):
        self.driver.get(self.profile_url)
        time.sleep(random.uniform(5, 10))

        self.data["name"] = self._extract_name()
        self.data["one_liner_about"] = self._extract_one_liner()
        self.data["full_about"] = self._extract_full_about()
        self.data["experience"] = self._extract_experience()
        time.sleep(random.uniform(5, 10))
        self.data["education"] = self._extract_education()
        time.sleep(random.uniform(5, 10))
        self.data["image"] = self._extract_image()
        return self.data

    def _extract_name(self):
        try:
            return self.driver.find_element(By.CSS_SELECTOR, "h1.inline.t-24.v-align-middle.break-words").text.strip()
        except Exception as e:
            print(f"[DEBUG] Name not found: {e}")
            return None

    def _extract_one_liner(self):
        try:
            return self.driver.find_element(By.CSS_SELECTOR, "div.text-body-medium.break-words").text.strip()
        except Exception as e:
            print(f"[DEBUG] One-liner not found: {e}")
            return None

    def _extract_full_about(self):
        try:
            about_section = self.driver.find_element(By.XPATH, "//section[.//h2[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'about')]]")
            about_text = about_section.text.strip()
            if about_text.lower().startswith("about"):
                about_text = about_text[len("about"):].strip()
            return about_text
        except Exception as e:
            print(f"[DEBUG] Full about not found: {e}")
            return None

    def _extract_experience(self):
        experiences = []
        try:
            original_url = self.driver.current_url
            if "linkedin.com/in/" in original_url:
                exp_url = original_url.split("?")[0] + "/details/experience/"
                self.driver.get(exp_url)
                time.sleep(2)

                entries = self.driver.find_elements(
                    By.XPATH,
                    "//section[contains(@class, 'artdeco-card')]//li[contains(@class, 'artdeco-list__item')]"
                )
                for el in entries:
                    try:
                        role_el = el.find_element(
                            By.CSS_SELECTOR,
                            "div.display-flex.align-items-center.mr1.hoverable-link-text.t-bold span[aria-hidden='true']"
                        )
                        role = role_el.text.strip()
                    except:
                        role = None

                    try:
                        company_el = el.find_element(
                            By.CSS_SELECTOR,
                            "span.t-14.t-normal span[aria-hidden='true']"
                        )
                        company_raw = company_el.text.strip()
                        company = ProfileExtractor.deduplicate_text(company_raw)
                    except:
                        company = None

                    date, location = None, None
                    try:
                        spans = el.find_elements(By.CSS_SELECTOR, "span.t-14.t-normal.t-black--light")
                        if len(spans) >= 1:
                            date = ProfileExtractor.get_clean_text(spans[0])
                        if len(spans) >= 2:
                            location = ProfileExtractor.get_clean_text(spans[1])
                    except:
                        pass

                    if any([role, company, date, location]):
                        experiences.append({
                            "role": role,
                            "company": company,
                            "date": date,
                            "location": location
                        })
                self.driver.get(original_url)
                time.sleep(1)

        except Exception as e:
            print(f"[DEBUG] Experience not found: {e}")
        return experiences

    def _extract_education(self):
        education = []
        try:
            original_url = self.driver.current_url
            if "linkedin.com/in/" in original_url:
                edu_url = original_url.split("?")[0] + "/details/education/"
                self.driver.get(edu_url)
                time.sleep(2)
                entries = self.driver.find_elements(
                    By.XPATH, "//section[contains(@class, 'artdeco-card')]//li[contains(@class, 'artdeco-list__item')]"
                )
                for el in entries:
                    try:
                        institution_el = el.find_element(
                            By.CSS_SELECTOR,
                            "div.display-flex.align-items-center.mr1.hoverable-link-text.t-bold span[aria-hidden='true']"
                        )
                        institution = institution_el.text.strip()
                    except:
                        institution = None
                    try:
                        degree = el.find_element(By.CSS_SELECTOR, "span.t-normal.t-14 span[aria-hidden='true']").text.strip()
                    except:
                        degree = None
                    if institution or degree:
                        education.append({"institution": institution, "degree": degree})
                self.driver.get(original_url)
                time.sleep(1)
        except Exception as e:
            print(f"[DEBUG] Education not found: {e}")
        return education
    
    def _extract_image(self):
        try:
            img_element = self.driver.find_element(
                By.CSS_SELECTOR, "img.pv-top-card-profile-picture__image--show"
            )
            img_url = img_element.get_attribute("src")
            return img_url
        except Exception as e:
            print(f"[DEBUG] Profile image not found: {e}")
            return None    

class ProfileExtractor:
    @staticmethod
    def deduplicate_text(text):
        seen = set()
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line and line not in seen:
                seen.add(line)
                lines.append(line)
        return " ".join(lines)

    @staticmethod
    def get_clean_text(element):
        try:
            return element.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text.strip()
        except:
            return ProfileExtractor.deduplicate_text(element.text.strip())

# === MAIN EXECUTION ===
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python sele_linkedin_oop.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    scraper = LinkedInScraper(input_file=input_file, output_file=output_file)
    scraper.login()
    scraper.scrape()
    scraper.close()
