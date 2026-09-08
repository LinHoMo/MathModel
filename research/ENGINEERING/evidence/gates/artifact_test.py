#!/usr/bin/env python3
"""Test artifact persistence and run record creation."""
import sys
from pathlib import Path
import json

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')
sys.path.insert(0, str(mathmodel))

print("=" * 60)
print("Artifact & Run Record Test")
print("=" * 60)

# 1. Artifact persistence
print("\n1. Artifact Persistence")
art_dir = mathmodel / "projects" / "v3-real-2024a" / "artifacts"
print(f"   Artifacts dir exists: {art_dir.exists()}")
if art_dir.exists():
    # Try to write a test artifact
    test_file = art_dir / "data" / "test_artifact.json"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(json.dumps({"test": "value", "model": "test_model"}), encoding='utf-8')
    print(f"   Write test artifact: OK")
    print(f"   File exists: {test_file.exists()}")
    print(f"   File content: {test_file.read_text()}")
    
    # Clean up
    test_file.unlink(missing_ok=True)
    print(f"   Cleanup: OK")
    
    # Check existing artifact structure
    print(f"\n   Artifact subdirectories:")
    for sub in ["data", "code", "figures", "results", "tables"]:
        sub_dir = art_dir / sub
        print(f"     {sub}: exists={sub_dir.exists()}")
else:
    print(f"   Artifacts dir DOES NOT exist")

# 2. Run record creation
print("\n2. Run Record Creation")
runs_dir = mathmodel / "projects" / "v3-real-2024a" / "state" / "runs"
print(f"   Runs dir exists: {runs_dir.exists()}")
if runs_dir.exists():
    # Try to write a test run record
    test_run = runs_dir / "test_run.json"
    test_run.write_text(json.dumps({"test": "run", "model_provider": "openai", "skill_version": "e3b0c44290"}), encoding='utf-8')
    print(f"   Write test run record: OK")
    print(f"   File exists: {test_run.exists()}")
    content = json.loads(test_run.read_text())
    print(f"   model_provider: {content.get('model_provider')}")
    print(f"   skill_version: {content.get('skill_version')}")
    
    # Clean up
    test_run.unlink(missing_ok=True)
    print(f"   Cleanup: OK")
else:
    print(f"   Runs dir DOES NOT exist")

# 3. Check current status for run_type indicators
print("\n3. Current Status Analysis")
status_path = mathmodel / "projects" / "v3-real-2024a" / "work" / "state.json"
with open(status_path, 'r', encoding='utf-8') as f:
    status = json.load(f)

print(f"   Current step: {status.get('current', {}).get('hand')}/{status.get('current', {}).get('agent')}")
print(f"   Completed: {len(status.get('completed', []))}/29")
print(f"   Run phase: {status.get('run', {}).get('phase', 'N/A')}")

# Check registry for provider info
registry_path = mathmodel / "projects" / "v3-real-2024a" / "work" / "registry.json"
if registry_path.exists():
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    artifact_count = len(registry.get('artifacts', {}))
    print(f"\n   Registry artifact count: {artifact_count}")
    
    # Check for provider field
    providers = set()
    for art_id, art in registry.get('artifacts', {}).items():
        p = art.get('provider', '')
        if p:
            providers.add(p)
    print(f"   Artifacts with provider: {len(providers)} distinct")
    if providers:
        print(f"   Provider IDs: {providers}")
    
    # Check question specs
    q001 = registry.get('artifacts', {}).get('Q001', {})
    print(f"\n   Q001 artifact type: {q001.get('type', 'N/A')}")
    if q001.get('data'):
        print(f"   Q001 data keys: {list(q001['data'].keys())}")
    else:
        print(f"   Q001 data: None/empty")
    
    # Check for model_provider in any artifact
    for art_id, art in registry.get('artifacts', {}).items():
        mp = art.get('model_provider', '')
        sv = art.get('skill_version', '')
        if mp or sv:
            print(f"   {art_id}: model_provider={mp!r}, skill_version={sv!r}")

print("\n" + "=" * 60)