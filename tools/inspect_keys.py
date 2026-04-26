import json

with open("public_keys.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(type(data))

if isinstance(data, dict):
    for k, v in data.items():
        print("KEY:", k, "TYPE:", type(v))

print(json.dumps(data, ensure_ascii=False, indent=2)[:5000])