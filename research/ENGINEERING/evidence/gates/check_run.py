#!/usr/bin/env python3
"""Check run record structure."""
import json, os
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')

# Check the run record
runs_dir = mathmodel / 'projects' / 'v3-real-2024a' / 'state' / 'runs'
print('Run records:')
for f in sorted(os.listdir(runs_dir)):
    fp = runs_dir / f
    with open(fp, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
        print(f'  {f}:')
        # Safely print key fields
        progress = data.get('progress', {})
        completed = progress.get('completed', 0) if progress else 'N/A'
        blocked = len(progress.get('blocked', {})) if progress else 'N/A'
        failures = len(progress.get('failures', {})) if progress else 'N/A'
        claims = data.get('claims', 'N/A')
        print(f'    progress.completed: {completed}/16')
        print(f'    progress.blocked: {blocked}')
        print(f'    progress.failures: {failures}')
        print(f'    claims: {claims}')
        # Check for hash/provenance fields
        for key in list(data.keys())[:30]:  # First 30 keys
            val = data.get(key, '')
            if 'hash' in key.lower() or 'provenance' in key.lower() or 'sha' in key.lower():
                print(f'    *** {key}: {str(val)[:80]}')
        # Print all keys
        # print(f'    All keys: {list(data.keys())}')