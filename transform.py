import json

# Read the content from a.json
with open('a.json', 'r') as infile:
    data = json.load(infile)

# Write the formatted JSON to b.json
with open('b.json', 'w') as outfile:
    json.dump(data, outfile, indent=4)