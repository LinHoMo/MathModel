# -*- coding: utf-8 -*-
import json

with open(r'C:/Users/Lin/Desktop/Programs/MathModel/research/REPOSITORY_AUDIT/commits.json', encoding='utf-8') as f:
    data = json.load(f)

if isinstance(data, dict):
    print("API message:", data.get("message"))
else:
    print("commits:", len(data))
    for c in data:
        print(c['commit']['author']['date'], "|", c['commit']['author']['name'], "|", c['commit']['message'][:80].replace("\n", " "))
