#!/usr/bin/env python3
"""G6: Full replay verification."""
import json, os, hashlib
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')

# Load the original run record
runs_dir = mathmodel / 'projects' / 'v3-real-2024a' / 'state' / 'runs'
orig_file = runs_dir / '1027df74ffde.json'
with open(orig_file, 'r', encoding='utf-8') as f:
    original = json.load(f)

print('=== ORIGINAL RUN RECORD ===')
print(f'File: {orig_file.name}')

# Safely print hash fields
for hf in ['prompt_hash', 'input_hash', 'artifact_hash', 'evidence_hash', 'decision_log_hash']:
    val = original.get(hf, 'MISSING')
    print(f'{hf}: {val}')

print()

# Load the current state
status_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'state.json'
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

print('=== CURRENT STATE ===')
cur = status.get('current', {})
print(f'current step: {cur.get("hand")}/{cur.get("agent")}')
print(f'completed: {len(status.get("completed", []))} steps')

# Check registry
registry_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'registry.json'
reg_exists = os.path.exists(registry_path)
if reg_exists:
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    print(f'registry artifacts: {len(registry.get("artifacts", {}))}')
else:
    print('registry not found')

# Check if we can verify hash consistency
print()
print('=== HASH VERIFICATION ===')
hash_fields = ['prompt_hash', 'input_hash', 'artifact_hash', 'evidence_hash', 'decision_log_hash']
for hf in hash_fields:
    orig_val = original.get(hf, 'MISSING')
    if hf == 'input_hash':
        input_file = mathmodel / 'projects' / 'v3-real-2024a' / 'inputs' / 'cumcm2024A.txt'
        if os.path.exists(input_file):
            computed = hashlib.sha256(input_file.read_bytes()).hexdigest()
            match_str = 'MATCH' if computed == orig_val else 'MISMATCH'
            print(f'  {hf}: orig={orig_val[:20]}... computed={computed[:20]}... {match_str}')
    elif hf == 'artifact_hash':
        if reg_exists:
            art_count = len(registry.get('artifacts', {}))
            computed = hashlib.sha256(str(art_count).encode()).hexdigest()
            match_str = 'MATCH' if computed == orig_val else 'MISMATCH'
            print(f'  {hf}: orig={orig_val[:20]}... computed={art_count} artifacts {match_str}')
    elif hf == 'evidence_hash':
        eg_path = mathmodel / 'projects' / 'v3-real-2024a' / 'state' / 'evidence_graph.json'
        if os.path.exists(eg_path):
            with open(eg_path, 'r', encoding='utf-8') as f:
                eg = json.load(f)
            print(f'  evidence_graph exists, relations: {len(eg.get("relations", []))}')
    else:
        print(f'  {hf}: {str(orig_val)[:80]}')

# Also check state.json for hash fields
print()
print('=== STATE.JSON HASH FIELDS ===')
for key in list(status.keys()):
    val = status.get(key, '')
    kl = key.lower()
    if 'hash' in kl or 'sha' in kl or 'provenance' in kl:
        print(f'  {key}: {str(val)[:80]}')