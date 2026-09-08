import os, json
from pathlib import Path
from collections import Counter

ROOT = Path('.')
EXCLUDE_DIRS = {'.git', '.opencode', 'node_modules', '__pycache__', '.pytest_cache',
                '.venv', 'venv', '.trae', '.zcode', '.workbuddy', '.claude'}

def classify(rel):
    if rel.startswith('core/runtime/') or rel.startswith('core/tools/') or \
       rel.startswith('core/validators/') or rel.startswith('core/schemas/') or \
       rel.startswith('core/workflows/') or rel.startswith('core/roles/') or \
       rel.startswith('core/env/') or rel.startswith('core/skills/') or \
       rel.startswith('core/evaluation/'):
        return 'runtime_source'
    if rel.startswith('core/legacy/'):
        return 'legacy_compat'
    if rel.startswith('core/knowledge/'):
        return 'knowledge'
    if rel.startswith('core/templates/'):
        return 'template'
    if rel.startswith('research/REPOSITORY_AUDIT/'):
        return 'audit_report'
    if rel.startswith('research/'):
        return 'research_artifact'
    if rel.startswith('tests/'):
        return 'test'
    if rel.startswith('docs/'):
        return 'documentation'
    if rel.startswith('projects/'):
        return 'project_instance'
    if rel.startswith('examples/'):
        return 'fixture'
    if rel.startswith('catalog/') or rel == 'catalog.yaml':
        return 'schema_registry'
    if rel.startswith('adapters/'):
        return 'generated_config'
    if rel.startswith('archives/'):
        return 'historical_archive'
    if rel in ('AGENTS.md', 'README.md', 'CHANGELOG.md', 'pyproject.toml',
               '.gitignore', 'Dockerfile', 'docker-compose.yml',
               'install.ps1', 'install.sh', '.dockerignore', 'package.json'):
        return 'project_root'
    return 'other'

inventory = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for f in files:
        fp = Path(root) / f
        rel = str(fp).replace('\\', '/')
        size = fp.stat().st_size
        ext = fp.suffix.lower()
        inventory.append({
            'path': rel,
            'size_bytes': size,
            'type': classify(rel),
            'ext': ext
        })

type_counts = Counter(i['type'] for i in inventory)
summary = {
    'total_files': len(inventory),
    'total_size_kb': round(sum(i['size_bytes'] for i in inventory) / 1024, 1),
    'by_type': dict(type_counts)
}

output = {'summary': summary, 'files': inventory}
outpath = 'research/REPOSITORY_AUDIT/FILE_INVENTORY.json'
with open(outpath, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=1)

print(f'Generated {outpath}: {summary["total_files"]} files, {summary["total_size_kb"]}KB')
print('By type:', json.dumps(dict(type_counts), indent=2))
