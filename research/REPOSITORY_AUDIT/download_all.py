# -*- coding: utf-8 -*-
"""Download all blobs from BZDmathclub/bzd-math-modeling-skills via raw.githubusercontent.com"""
import json
import os
import urllib.request
import urllib.parse

BASE = "https://raw.githubusercontent.com/BZDmathclub/bzd-math-modeling-skills/main/"
DEST = r"C:/Users/Lin/Desktop/Programs/MathModel/research/REPOSITORY_AUDIT/src"

with open(r'C:/Users/Lin/Desktop/Programs/MathModel/research/REPOSITORY_AUDIT/tree_main.json', encoding='utf-8') as f:
    data = json.load(f)

blobs = [i for i in data['tree'] if i['type'] == 'blob']
print("total blobs:", len(blobs))

ok, fail = 0, []
for i, blob in enumerate(blobs):
    path = blob['path']
    url = BASE + urllib.parse.quote(path, safe='/')
    local = os.path.join(DEST, path.replace('/', os.sep))
    os.makedirs(os.path.dirname(local), exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as r:
            content = r.read()
        with open(local, 'wb') as f:
            f.write(content)
        ok += 1
    except Exception as e:
        fail.append((path, str(e)))
    if (i + 1) % 20 == 0:
        print("progress %d/%d" % (i + 1, len(blobs)))

print("downloaded OK:", ok)
print("failed:", len(fail))
for p, e in fail:
    print("FAIL:", p, "|", e)
