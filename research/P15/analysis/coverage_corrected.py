# -*- coding: utf-8 -*-
"""Corrected per-run MCQ + coverage + 2019_C artifact consistency check."""
import json, pathlib, hashlib

cm = json.loads(pathlib.Path('research/P15/experiments/P15-K001/key/condition_map.json').read_text(encoding='utf-8'))['map']
runs = pathlib.Path('research/P15/experiments/P15-K001/runs')

PRIMARY = ['L2.1', 'L2.2', 'L2.4', 'L2.5', 'L2.6', 'L2.7']

scores = {}
for f in pathlib.Path('research/P15/analysis/raw/scores').glob('*.json'):
    if '.template' in f.name:
        continue
    d = json.loads(f.read_text(encoding='utf-8'))
    dims = d['dimensions']
    s = sum(int(dims[k]['score']) for k in PRIMARY)
    scores[d['submission_id']] = round(s / 13 * 100, 1)

print('=== 2020_B corrected MCQ ===')
for sid, cond in sorted(cm.items(), key=lambda kv: kv[1].get('arm', '')):
    if cond.get('problem_id') != '2020_B':
        continue
    print('  %s arm=%s MCQ=%s' % (sid[:8], cond.get('arm'), scores.get(sid)))

# objectives / variables coverage of a full-score run vs FAIL run
print()
print('=== 2020_B full-score run (47378190) structure ===')
mi = json.loads((runs / '47378190-0d2b-41c6-8e02-0d2b47378190' if (runs / '47378190-0d2b-41c6-8e02-0d2b47378190').exists() else runs / next(x for x in runs.iterdir() if x.name.startswith('47378190')) / 'model_ir.json').read_text(encoding='utf-8')) if False else None

# find by prefix
for d in runs.iterdir():
    if d.name.startswith('47378190'):
        mi = json.loads((d / 'model_ir.json').read_text(encoding='utf-8'))
        print('  objectives:', len(mi.get('objectives', [])))
        for o in mi.get('objectives', []):
            print('    -', json.dumps(o, ensure_ascii=False)[:120])
        print('  problem_binding:', json.dumps(mi.get('problem_binding', {}), ensure_ascii=False)[:250])
        break

print()
print('=== 2019_C artifact hash consistency across arms ===')
h_by_arm = {}
for sid, cond in sorted(cm.items(), key=lambda kv: kv[1].get('arm', '')):
    if cond.get('problem_id') != '2019_C':
        continue
    d = next(x for x in runs.iterdir() if x.name.startswith(sid[:8]))
    mi = json.loads((d / 'model_ir.json').read_text(encoding='utf-8'))
    h = hashlib.sha256(json.dumps(mi, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:10]
    h_by_arm.setdefault(cond.get('arm'), []).append(h)
    print('  %s arm=%s MCQ=%s hash=%s' % (sid[:8], cond.get('arm'), scores.get(sid), h))
print()
for arm, hashes in h_by_arm.items():
    print('  arm %s distinct hashes: %d / %d' % (arm, len(set(hashes)), len(hashes)))
