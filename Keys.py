import json
# This class is used to reference keys, such as API keys.

with open("keys.txt") as key_file:
    key_json = json.load(key_file)

geocoder_key = key_json.get("geocoder")

