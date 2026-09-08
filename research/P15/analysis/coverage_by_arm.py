# -*- coding: utf-8 -*-
"""Per-run sub-question coverage + L2 score by arm (2020_B deep dive)."""
import json, pathlib

cm = json.loads(pathlib.Path('research/P15/experiments/P15-K001/key/condition_map.json').read_text(encoding='utf-8'))['map']
runs = pathlib.Path('research/P15/experiments/P15-K001/runs')

scores = {}
for f in pathlib.Path('research/P15/analysis/raw/scores').glob('*.json'):
    if '.template' in f.name:
        continue
    d = json.loads(f.read_text(encoding='utf-8'))
    dims = d['dimensions']
    l2 = (dims['L2.1']['score'] + dims['L2.2']['score'] + dims['L2.4']['score'] +
          dims['L2.5']['score'] + dims['L2.6']['score'] * 3 + dims['L2.7']['score'])
    scores[d['submission_id']] = round(l2 / 13 * 100, 1)

for problem in ['2020_B', '2018_A', '2019_C']:
    print('===', problem)
    for sid, cond in sorted(cm.items(), key=lambda kv: kv[1].get('arm', '')):
        if cond.get('problem_id') != problem:
            continue
        mi = json.loads((runs / sid / 'model_ir.json').read_text(encoding='utf-8'))
        pb = mi.get('problem_binding', {})
        sq = pb.get('sub_question_id')
        nq = len(pb.get('sub_questions', {}) or {})
        print('  %s arm=%s sq=%s n_subq_fields=%d MCQ=%s validations=%d mechanisms=%d' % (
            sid[:8], cond.get('arm'), sq, nq, scores.get(sid),
            len(mi.get('validations', [])), len(mi.get('mechanisms', []))))
