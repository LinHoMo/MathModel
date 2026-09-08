#!/usr/bin/env python3
import json, os
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')
registry_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'registry.json'

with open(registry_path, 'r', encoding='utf-8') as f:
    registry = json.load(f)

print('=== POST-V3 EXECUTION ARTIFACT ANALYSIS ===')
print()

for art_id in sorted(registry.get('artifacts', {}).keys()):
    art = registry['artifacts'][art_id]
    art_type = art.get('type', 'N/A')
    prov = art.get('provider', '-')
    status = art.get('status', '-')
    has_data = art.get('data') is not None and art['data'] != {}
    data_keys = list(art.get('data', {}).keys()) if has_data else []
    
    print(f'  {art_id:8s}: type={art_type:12s} provider={prov:8s} status={status:6s} data_exists={has_data} keys={data_keys}')

print()
print('Key findings:')
models = [aid for aid, a in registry['artifacts'].items() if a.get('type') == 'model']
results = [aid for aid, a in registry['artifacts'].items() if a.get('type') == 'result']
claims = [aid for aid, a in registry['artifacts'].items() if a.get('type') == 'claim']
print(f'  Models: {len(models)} - {models}')
print(f'  Results: {len(results)} - {results}')
print(f'  Claims: {len(claims)} - {claims}')