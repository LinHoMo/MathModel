#!/usr/bin/env python3
"""Post-run artifact analysis."""
import json, os
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')
proj = mathmodel / 'projects' / 'v3-real-2024a'

# Check registry
reg_path = proj / 'work' / 'registry.json'
if os.path.exists(reg_path):
    with open(reg_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    print('Registry artifacts:')
    for art_id in sorted(registry.get('artifacts', {}).keys()):
        art = registry['artifacts'][art_id]
        art_type = art.get('type', 'N/A')
        prov = art.get('provider', '-')
        status = art.get('status', '-')
        has_data = art.get('data') is not None and art['data'] != {}
        data_keys = list(art.get('data', {}).keys()) if has_data else []
        print(f'  {art_id:8s}: type={art_type:12s} provider={prov:8s} status={status:6s} data={has_data} keys={data_keys}')
else:
    print('Registry not found')

# Check state
status_path = proj / 'work' / 'state.json'
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)
print(f'\nState: current={status.get("current", {}).get("hand")}/{status.get("current", {}).get("agent")}, completed={len(status.get("completed", []))}')

# Check evidence graph
eg_path = proj / 'state' / 'evidence_graph.json'
if os.path.exists(eg_path):
    with open(eg_path, 'r', encoding='utf-8') as f:
        eg = json.load(f)
    print(f'\nEvidence graph: {len(eg.get("relations", []))} relations, {len(eg.get("claims", []))} claims')
else:
    print(f'\nEvidence graph not found')