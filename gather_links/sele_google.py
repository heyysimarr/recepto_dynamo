import json
import sys
import time
import random
import os
import urllib.parse
import re
from collections import OrderedDict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import requests

import ollama
from dotenv import load_dotenv

load_dotenv()


def random_sleep(min_seconds, max_seconds):
    time.sleep(random.uniform(min_seconds, max_seconds))
    

# Access AZURE_ENDPOINT and AZURE_API_KEY
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
print(AZURE_ENDPOINT)
AZURE_API_KEY = os.getenv("AZURE_API_KEY")


def generate_queries(person):
    prompt = f"""
You are a search engine assistant. Based on the details below, generate *5 distinct, focused search queries* to help locate this person online, specifically on platforms like LinkedIn. 
Each query should be tailored with different combinations of details to increase the chance of finding the right match.

Use the following guidelines:
1. Query with full name and intro.
2. Query with name only.
3. Query with name and all available details.
4. Query with name and timezone.
5. Query with intro and everything else except the name.

Add the word "LinkedIn" to all queries to focus the search.

Person Details:
- Full Name: {person.get("name", "")}
- Intro / Bio: {person.get("intro", "")}
- Timezone / Location: {person.get("timezone", "")}
- Industry: {person.get("company_industry", "")}
- Company Size: {person.get("company_size", "")}
- Known Social Profiles: {', '.join(person.get("social_profile", []))}

Only return the 5 queries, each on a new line, without numbering or extra explanation.
"""

    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": AZURE_API_KEY
        }

        data = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }

        response = requests.post(AZURE_ENDPOINT, headers=headers, json=data)
        response.raise_for_status()
        output = response.json()["choices"][0]["message"]["content"].strip()

        # Remove <think> blocks and split into lines
        output = re.sub(r"<think>.*?</think>", "", output, flags=re.DOTALL).strip()
        queries = [line.strip() for line in output.splitlines() if line.strip()]

    except Exception as e:
        print(f"Failed to generate queries for {person.get('name', 'unknown')}: {e}")
        queries = [person.get("name", "") + " LinkedIn"]

    print(f"Generated queries for {person.get('name', '')}:\n" + "\n".join(queries))
    return queries

def init_driver():
    options = Options()
    # options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    service = Service(log_path=os.devnull)
    return webdriver.Chrome(service=service, options=options)

def safe_search_google(driver, query, max_results=2, captcha_prompt=False):
    # Strip any prefix then restrict to LinkedIn profiles
    #query = query[3:]
    full_query = f"site:linkedin.com/in/ {query}"
    encoded = urllib.parse.quote_plus(full_query)
    url = f"https://www.google.com/search?q={encoded}"
    print(f"[DEBUG] Final Google search URL: {url}")
    driver.get(url)

    if captcha_prompt:
        input(">> Solve CAPTCHA if prompted, then press Enter to continue...")

    time.sleep(random.uniform(4, 8))

    results = set()
    page = 1
    while len(results) < max_results:
        print(f"[DEBUG] Page {page}, found {len(results)} so far.")
        anchors = driver.find_elements(By.CSS_SELECTOR, "a.zReHs")
        for a in anchors:
            href = a.get_attribute("href")
            if href and "linkedin.com/in/" in href:
                results.add(href)
                if len(results) >= max_results:
                    break

        if len(results) >= max_results:
            break

        # paginate
        try:
            nxt = driver.find_element(By.CSS_SELECTOR, f'a.fl[aria-label="Page {page+1}"]')
            nxt.click()
            page += 1
            time.sleep(random.uniform(4, 8))
        except:
            break

    return list(results)

def main():
    if len(sys.argv) != 3:
        print("Usage: python duckduckbot.py <input_json> <output_json>")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]
    with open(input_path, "r", encoding="utf-8") as f:
        people = json.load(f)

    driver = init_driver()
    final_output = []

    for j, person in enumerate (people):
        # 1) generate or reuse raw queries (no numbering)
        raw_q = generate_queries(person)
        person["query"] = raw_q

        # 2) aggregate all search results into one set
        all_links = set()
        for idx, q in enumerate(raw_q):
            print(f"Searching with query #{idx+1}: {q}")
            try:
                links = safe_search_google(driver, q, max_results=10, captcha_prompt=(idx==0 and j==0))
                all_links.update(links)
            except Exception as e:
                print(f"  Search failed on #{idx+1}: {e}")
            random_sleep(3, 6)

        person["search_results"] = list(all_links)
        final_output.append(person)
        random_sleep(3, 6)

    driver.quit()

    # ensure key order and pretty‑print once
    key_order = [
        "name", "image", "intro", "timezone",
        "human",
        "company_industry", "company_size", "social_profile",
        "query", "search_results"
    ]
    ordered_list = []
    for p in final_output:
        od = OrderedDict()
        for k in key_order:
            od[k] = p.get(k, None)
        ordered_list.append(od)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ordered_list, f, ensure_ascii=False, indent=4)

    print(f"[INFO] Final JSON written to {output_path}")

if __name__ == "__main__":
    main()
