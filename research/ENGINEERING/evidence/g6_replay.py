#!/usr/bin/env python3
"""G6: Replay verification."""
import json, os
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')

# Check the state and registry from the V3 run
status_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'state.json'
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

registry_path = mathmodel / 'projects' / 'v3-real-2024a' / 'work' / 'registry.json'
if os.path.exists(registry_path):
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    print('=== Run Record Artifacts ===')
    for art_id in sorted(registry.get('artifacts', {}).keys()):
        art = registry['artifacts'][art_id]
        # Check for provenance/hash fields
        provenance = art.get('provenance', art.get('depends_on', art.get('parent', 'N/A')))
        data_hash = art.get('data_hash', art.get('hash', 'N/A'))
        print(f'  {art_id}: type={art.get("type")}, provenance={provenance}, data_hash={data_hash}')
    
    print()
    print('=== State Completeness ===')
    print(f'  Completed steps: {len(status.get("completed", []))}')
    print(f'  Current: {status.get("current", {}).get("hand")}/{status.get("current", {}).get("agent")}')
    print(f'  Run phase: {status.get("run", {}).get("phase")}')
    
    # Check for run records
    runs_dir = mathmodel / 'projects' / 'v3-real-2024a' / 'state' / 'runs'
    if runs_dir.exists():
        print(f'  Runs directory: {len(os.listdir(runs_dir))} files')
        for f in os.listdir(runs_dir):
            fp = os.path.join(runs_dir, f)
            with open(fp, 'r', encoding='utf-8') as fh:
                run_data = json.load(fh)
                print(f'    {f}: runs={run_data.get("progress", {}).get("completed", 0)}/16, '
                      f'blocked={len(run_data.get("progress", {}).get("blocked", {}))}, '
                      f'failures={len(run_data.get("progress", {}).get("failures", {}))}')
    else:
        print(f'  Runs directory does not exist')
else:
    print('Registry not found')