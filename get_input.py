import json
import os
from is_human import detect_human_in_image

def prompt(field_name, default=None):
    value = input(f"{field_name}: ").strip()
    return value if value else default

def prompt_list(field_name):
    value = input(f"{field_name} (comma-separated): ").strip()
    return [v.strip() for v in value.split(",")] if value else []

data = {
    "name": prompt("Name", None),
    "image": prompt("Image URL", None),
    "intro": prompt("Intro", None),
    "timezone": prompt("Timezone", None),
    "company_industry": prompt("Company Industry", None),
    "company_size": prompt("Company Size", None),
    "social_profile": prompt_list("Social Profiles")
}
# Safely create the output directory
if data["image"] is not None:
    ans = detect_human_in_image(data["image"])
    if ans:
        data["human"] = 1
    else:
        data["human"] = 0


dir_name = "temp"
os.makedirs(dir_name, exist_ok=True)

output_path = os.path.join(dir_name, "input.json")
with open(output_path, "w") as f:
    json.dump([data], f, indent=4)

print(f"✅ JSON saved to {output_path}")

##################################
#FOR FINAL RUN ON COMPLETE INPUT##
##################################
# import json
# import os
# from is_human import detect_human_in_image

# # Path to your input JSON file
# input_path = ""

# # Load the list of profiles
# with open(input_path, "r", encoding="utf-8") as f:
#     data_list = json.load(f)

# # Process each entry and add "human" field
# for data in data_list:
#     img_url = data.get("image")
#     if img_url:
#         try:
#             is_human = detect_human_in_image(img_url)
#             data["human"] = int(is_human)
#         except Exception as e:
#             print(f"[WARN] Failed to process image for {data.get('name', 'Unknown')}: {e}")
#             data["human"] = -1  # Or None if you prefer

# # Save updated profiles to a new JSON file
# output_path = "temp/input.json"
# with open(output_path, "w", encoding="utf-8") as f:
#     json.dump(data_list, f, indent=4, ensure_ascii=False)

# print(f"✅ Annotated JSON saved to {output_path}")