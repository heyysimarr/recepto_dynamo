import json
from pathlib import Path
from collections import Counter

# Load both JSON files
with open("temp/google_links.json") as f:
    json1 = json.load(f)

with open("temp/ddg_links.json") as f:
    json2 = json.load(f)

# Count frequency of each URL across both files
all_urls = []
for p in json1 + json2:
    all_urls.extend(p.get("search_results", []))

url_freq = Counter(all_urls)

# Merge and sort search_results by frequency (and include frequency)
merged = []
for prof1, prof2 in zip(json1, json2):
    combined_urls = set(prof1.get("search_results", []) + prof2.get("search_results", []))
    sorted_urls = sorted(combined_urls, key=lambda url: -url_freq[url])
    
    merged_profile = prof1.copy()
    merged_profile["search_results"] = [
        {"url": url, "count": url_freq[url]} for url in sorted_urls
    ]
    merged.append(merged_profile)

# Save merged output
output_path = Path("temp/merged_links.json")
with output_path.open("w", encoding="utf-8") as f:
    json.dump(merged, f, ensure_ascii=False, indent=2)

print("✅ Merged and frequency-sorted search_results (with counts) saved to 'temp/merged_links.json'")
