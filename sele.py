#!/usr/bin/env python3
import json
import sys
import time
import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys


import ollama

import re

def generate_query(person):
    prompt = f"""
You are a search engine assistant. Based on the details below, generate a highly specific and concise search query that will help locate this exact person online (e.g., LinkedIn, Twitter, company pages). Prioritize uniqueness and disambiguation — include company, role, location, and any known identifiers. Avoid general terms.

Details:
- Full Name: {person.get("name", "")}
- Bio / Intro: {person.get("intro", "")}
- Timezone / Location: {person.get("timezone", "")}
- Industry: {person.get("company_industry", "")}
- Company Size: {person.get("company_size", "")}
- Known Social Profiles: {', '.join(person.get("social_profile", []))}

Only return the search query. Do not include any explanation.

Query:"""

    try:
        response = ollama.chat(
            model='deepseek-r1:14b',
            messages=[{"role": "user", "content": prompt}]
        )
        output = response['message']['content'].strip()

        # Remove <think>...</think> blocks
        query_only = re.sub(r"<think>.*?</think>", "", output, flags=re.DOTALL).strip()

    except Exception as e:
        print(f"Failed to generate query for {person['name']}: {e}")
        query_only = person.get("name", "")  # fallback

    print(query_only)
    return query_only



def init_driver():
    options = Options()
    options.add_argument("--headless=new")  # Run headless
    #options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=options)
    return driver


def safe_search_duckduckgo(driver, query, max_results=10):
    search_url = "https://duckduckgo.com/"
    driver.get(search_url)
    time.sleep(random.uniform(1, 2))

    search_box = driver.find_element(By.NAME, "q")
    search_box.clear()
    search_box.send_keys(query + Keys.ENTER)

    #time.sleep(random.uniform(2, 4))
    time.sleep(10)

    # Collect result URLs
    links = driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="result-title-a"]')
    urls = []
    for link in links:
        
        url = link.get_attribute("href")
        print(url)
        if url and url.startswith("http"):
            urls.append(url)
        if len(urls) >= max_results:
            break
        
    return urls


def main():
    if len(sys.argv) != 3:
        print("Usage: python duckduckbot.py <input_json> <output_json>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    driver = init_driver()
    results = []

    for person in data:
        try:
            query = generate_query(person)
        except ValueError as e:
            print(f"Skipping record: {e}")
            continue

        print(f"Searching: {query}")
        try:
            search_results = safe_search_duckduckgo(driver, query)
        except Exception as e:
            print(f"Search failed for {person['name']}: {e}")
            search_results = []

        person["search_results"] = search_results
        results.append(person)

        time.sleep(random.uniform(3, 6))  # Sleep between requests

    driver.quit()

    results.sort(key=lambda x: len(x.get("search_results", [])), reverse=True)
    shortlisted = results[:10]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(shortlisted, f, indent=2, ensure_ascii=False)

    print(f"Shortlisted {len(shortlisted)} people and saved results to {output_file}")


if __name__ == "__main__":
    main()
