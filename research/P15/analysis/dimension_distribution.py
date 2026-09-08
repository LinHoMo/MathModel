# -*- coding: utf-8 -*-
"""Extract L1-L4 dimension score distribution from 55 blinded scores."""
import json, pathlib

scores_dir = pathlib.Path('research/P15/analysis/raw/scores')
files = [f for f in scores_dir.glob('*.json') if '.template' not in f.name]
dims = ['L1.1','L1.2','L1.3','L1.4','L1.5','L2.1','L2.2','L2.3','L2.4','L2.5','L2.6','L2.7',
        'L3.1','L3.2','L3.3','L3.4','L3.5','L4.1','L4.2','L4.3','L4.4','L4.5']
agg = {}
for d in dims:
    agg[d] = {'n': 0, 'sum': 0, 'zero': 0, 'one': 0, 'two': 0}
for f in files:
    data = json.loads(f.read_text(encoding='utf-8'))
    for d in dims:
        v = data['dimensions'].get(d, {}).get('score')
        if v is None:
            continue
        agg[d]['n'] += 1
        agg[d]['sum'] += v
        if v == 0: agg[d]['zero'] += 1
        elif v == 1: agg[d]['one'] += 1
        elif v == 2: agg[d]['two'] += 1
out = {}
for d in dims:
    a = agg[d]
    out[d] = {
        'n': a['n'],
        'avg': round(a['sum'] / a['n'], 3) if a['n'] else None,
        'zero_count': a['zero'],
        'one_count': a['one'],
        'two_count': a['two'],
        'zero_rate': round(a['zero'] / a['n'], 4) if a['n'] else None,
    }
pathlib.Path('research/P15/analysis/dimension_distribution.json').write_text(
    json.dumps({'n_runs': len(files), 'dimensions': out}, ensure_ascii=False, indent=1), encoding='utf-8')
print('saved research/P15/analysis/dimension_distribution.json')
print('weakest dims (by avg):')
for d, v in sorted(out.items(), key=lambda kv: kv[1]['avg'])[:6]:
    print(' ', d, v['avg'], '0分率', v['zero_rate'])
