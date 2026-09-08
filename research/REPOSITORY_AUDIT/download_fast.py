# -*- coding: utf-8 -*-
"""Concurrent download of essential text files from BZD repo."""
import json
import os
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

BASE = "https://raw.githubusercontent.com/BZDmathclub/bzd-math-modeling-skills/main/"
DEST = r"C:/Users/Lin/Desktop/Programs/MathModel/research/REPOSITORY_AUDIT/src"

with open(r'C:/Users/Lin/Desktop/Programs/MathModel/research/REPOSITORY_AUDIT/tree_main.json', encoding='utf-8') as f:
    data = json.load(f)

blobs = [i for i in data['tree'] if i['type'] == 'blob']

SKIP_SUFFIX = ('.pdf', '.docx', '.xlsx', '.zip', '~$')
ESSENTIAL_ONLY = True  # skip binaries

def wanted(blob):
    p = blob['path']
    if p.endswith(SKIP_SUFFIX):
        return False
    # keep all text-like files: md, yaml, py, json, csv, txt, html, gitignore
    if p.endswith(('.md', '.yaml', '.yml', '.py', '.json', '.csv', '.txt', '.html', '.gitignore')):
        return True
    return False

targets = [b for b in blobs if wanted(b)]
print("target text files:", len(targets))

def fetch(blob):
    path = blob['path']
    url = BASE + urllib.parse.quote(path, safe='/')
    local = os.path.join(DEST, path.replace('/', os.sep))
    os.makedirs(os.path.dirname(local), exist_ok=True)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=60) as r:
                content = r.read()
            with open(local, 'wb') as f:
                f.write(content)
            return (path, 'ok', len(content))
        except Exception as e:
            last = str(e)
    return (path, 'fail', last)

ok = fail = 0
with ThreadPoolExecutor(max_workers=12) as ex:
    for path, status, info in ex.map(fetch, targets):
        if status == 'ok':
            ok += 1
        else:
            fail += 1
            print("FAIL:", path, "|", info)

print("done ok:", ok, "fail:", fail)
