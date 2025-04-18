#!/usr/bin/env python3
import os
import sys
import time
import random
import json

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import zipfile
import tempfile
import os, sys, time, random, json, zipfile, tempfile
from urllib.parse import urlparse
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

# Access PROXY
PROXY = os.getenv("PROXY")

class LinkedInScraper:
    def __init__(self, input_file, output_file):
        self.input_file  = input_file
        self.output_file = output_file
        self.driver      = self._init_driver()
        self.profiles    = []
        self._load_input_file()



    def _init_driver(self):
        # parse out user:pass, host:port
        p = urlparse(PROXY)
        # netloc is "user:pass@host:port"
        user_pass, host_port = p.netloc.rsplit("@", 1)
        proxy_user, proxy_pass = user_pass.split(":", 1)
        proxy_host, proxy_port = host_port.split(":", 1)

        # build a tiny extension on the fly
        manifest = {
          "version": "1.0.0",
          "manifest_version": 2,
          "name": "Proxy Auth Extension",
          "permissions": ["proxy","tabs","unlimitedStorage","storage","<all_urls>","webRequest","webRequestBlocking"],
          "background": {"scripts":["background.js"]}
        }
        background_js = f"""
        var config = {{
          mode: "fixed_servers",
          rules: {{
            singleProxy: {{
              scheme: "http",
              host: "{proxy_host}",
              port: parseInt({proxy_port})
            }},
            bypassList: []
          }}
        }};
        chrome.proxy.settings.set({{value: config, scope: "regular"}}, function(){{}});
        chrome.webRequest.onAuthRequired.addListener(
          function(details) {{
            return {{authCredentials: {{username: "{proxy_user}", password: "{proxy_pass}"}}}};
          }},
          {{urls: ["<all_urls>"]}},
          ["blocking"]
        );
        """
        # write extension to temp zip
        plugin = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        with zipfile.ZipFile(plugin.name, "w") as zp:
            zp.writestr("manifest.json", json.dumps(manifest))
            zp.writestr("background.js", background_js)

        opts = webdriver.ChromeOptions()
        opts.add_argument("--log-level=3")
        opts.add_argument("--start-maximized")
        # load our proxy‑auth extension
        opts.add_extension(plugin.name)
        # stealth flags
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument(
          "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/122.0.0.0 Safari/537.36"
        )

        driver = webdriver.Chrome(
          service=Service(ChromeDriverManager().install()),
          options=opts
        )
        # mask webdriver
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
          "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })
        return driver

    def _load_input_file(self):
        with open(self.input_file, "r", encoding="utf-8") as f:
            self.people = json.load(f)
        print("[INFO] Input file loaded.")
    
    def scrape(self):
        for person in self.people:
            for idx, url_info in enumerate(person.get("search_results", [])):
                url = url_info["url"] if isinstance(url_info, dict) else url_info
                print(f"[INFO] Visiting {url}")
                try:
                    profile = LinkedInProfile(
                        self.driver,
                        person.get("name"),
                        url,
                        idx,
                        person.get("human"),
                        person.get("image")
                    )
                    data = profile.extract_all()
                    self.profiles.append(data)
                except Exception as e:
                    print(f"[ERROR] Failed {url}: {e}")
                break
            break
        self._save_output()

    def _save_output(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, indent=2)
        print(f"[INFO] Saved {len(self.profiles)} profiles to {self.output_file}")

    def close(self):
        self.driver.quit()


class LinkedInProfile:
    def __init__(self, driver, original_name, profile_url, index, human, drive):
        self.driver        = driver
        self.original_name = original_name
        self.profile_url   = profile_url
        self.index         = index
        self.human         = human
        self.drive         = drive
        self.data = {
            "index": index,
            "profile_url": profile_url,
            "original_name": original_name,
            "human": human,
            "drive_link": drive
        }

    def extract_all(self):
        self.driver.get(self.profile_url)
        time.sleep(random.uniform(5, 10))

        self.data["name"]             = self._extract_name()
        self.data["one_liner_about"]  = self._extract_one_liner()
        self.data["full_about"]       = self._extract_full_about()
        self.data["experience"]       = self._extract_experience()
        time.sleep(random.uniform(3, 6))
        self.data["education"]        = self._extract_education()
        time.sleep(random.uniform(3, 6))
        self.data["image"]            = self._extract_image()
        return self.data

    def _extract_name(self):
        try:
            return self.driver.find_element(
                By.CSS_SELECTOR,
                "h1.inline.t-24.v-align-middle.break-words"
            ).text.strip()
        except Exception:
            return None

    def _extract_one_liner(self):
        try:
            return self.driver.find_element(
                By.CSS_SELECTOR,
                "div.text-body-medium.break-words"
            ).text.strip()
        except Exception:
            return None

    def _extract_full_about(self):
        try:
            about = self.driver.find_element(
                By.XPATH,
                "//section[.//h2[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'about')]]"
            ).text.strip()
            return about[len("About"):].strip() if about.lower().startswith("about") else about
        except Exception:
            return None

    def _extract_experience(self):
        experiences = []
        try:
            base = self.driver.current_url.split("?")[0]
            self.driver.get(f"{base}/details/experience/")
            time.sleep(2)
            items = self.driver.find_elements(
                By.XPATH,
                "//section[contains(@class,'artdeco-card')]//li[contains(@class,'artdeco-list__item')]"
            )
            for el in items:
                role = company = date = location = None
                try:
                    role = el.find_element(
                        By.CSS_SELECTOR,
                        "div.display-flex.align-items-center.mr1.hoverable-link-text.t-bold span[aria-hidden='true']"
                    ).text.strip()
                except: pass
                try:
                    raw = el.find_element(
                        By.CSS_SELECTOR,
                        "span.t-14.t-normal span[aria-hidden='true']"
                    ).text.strip()
                    company = ProfileExtractor.deduplicate_text(raw)
                except: pass
                spans = el.find_elements(By.CSS_SELECTOR, "span.t-14.t-normal.t-black--light")
                if spans:
                    date = ProfileExtractor.get_clean_text(spans[0])
                    if len(spans) > 1:
                        location = ProfileExtractor.get_clean_text(spans[1])
                if any([role, company, date, location]):
                    experiences.append({
                        "role": role,
                        "company": company,
                        "date": date,
                        "location": location
                    })
            # back to main profile
            self.driver.get(self.profile_url)
            time.sleep(1)
        except Exception:
            pass
        return experiences

    def _extract_education(self):
        education = []
        try:
            base = self.driver.current_url.split("?")[0]
            self.driver.get(f"{base}/details/education/")
            time.sleep(2)
            items = self.driver.find_elements(
                By.XPATH,
                "//section[contains(@class,'artdeco-card')]//li[contains(@class,'artdeco-list__item')]"
            )
            for el in items:
                inst = deg = None
                try:
                    inst = el.find_element(
                        By.CSS_SELECTOR,
                        "div.display-flex.align-items-center.mr1.hoverable-link-text.t-bold span[aria-hidden='true']"
                    ).text.strip()
                except: pass
                try:
                    deg = el.find_element(
                        By.CSS_SELECTOR,
                        "span.t-normal.t-14 span[aria-hidden='true']"
                    ).text.strip()
                except: pass
                if inst or deg:
                    education.append({"institution": inst, "degree": deg})
            self.driver.get(self.profile_url)
            time.sleep(1)
        except Exception:
            pass
        return education

    def _extract_image(self):
        try:
            return self.driver.find_element(
                By.CSS_SELECTOR,
                "img.pv-top-card-profile-picture__image--show"
            ).get_attribute("src")
        except Exception:
            return None


class ProfileExtractor:
    @staticmethod
    def deduplicate_text(text: str) -> str:
        seen, lines = set(), []
        for ln in text.splitlines():
            ln = ln.strip()
            if ln and ln not in seen:
                lines.append(ln)
                seen.add(ln)
        return " ".join(lines)

    @staticmethod
    def get_clean_text(el) -> str:
        try:
            return el.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text.strip()
        except:
            return ProfileExtractor.deduplicate_text(el.text.strip())


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python sele_linkedin_oop.py <input.json> <output.json>")
        sys.exit(1)

    inp, outp = sys.argv[1], sys.argv[2]
    scraper = LinkedInScraper(inp, outp)
    scraper.scrape()
    scraper.close()
