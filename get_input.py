##################################
#FOR FINAL RUN ON COMPLETE INPUT##
##################################
import json
from is_human import detect_human_in_image

# Path to your input JSON file
input_path = "dataset/test.json"

# Load the list of profiles
with open(input_path, "r", encoding="utf-8") as f:
    data_list = json.load(f)

# Process each entry and add "human" field
for data in data_list:
    img_url = data.get("image")
    if img_url:
        try:
            is_human = detect_human_in_image(img_url)
            data["human"] = int(is_human)
        except Exception as e:
            print(f"[WARN] Failed to process image for {data.get('name', 'Unknown')}: {e}")
            data["human"] = -1  # Or None if you prefer

# Save updated profiles to a new JSON file
output_path = "temp/input.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data_list, f, indent=4, ensure_ascii=False)

print(f"✅ Annotated JSON saved to {output_path}")