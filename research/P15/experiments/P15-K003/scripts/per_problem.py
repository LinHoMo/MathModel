import json
from pathlib import Path
from collections import defaultdict

EXP = Path(r'C:\Users\Lin\Desktop\Programs\MathModel\research\P15\experiments\P15-K003')
cond = json.load(open(EXP / 'key' / 'condition_map.json', encoding='utf-8'))

# Load bundle scores (3 evaluator mean)
bundle_scores = defaultdict(lambda: defaultdict(list))
for ev in ['A', 'B', 'C']:
    for i in range(1, 67):
        bid = f'BUNDLE_{i:03d}'
        fpath = EXP / 'scores' / f'evaluator_{ev}' / f'{bid}.json'
        if fpath.exists():
            data = json.loads(fpath.read_text(encoding='utf-8'))
            lt = data.get('layer_totals', {})
            for L in ['L1', 'L2', 'L3', 'L4']:
                bundle_scores[bid][L].append(lt.get(L, 0))

bundle_mean = {}
for bid in bundle_scores:
    bundle_mean[bid] = {L: sum(v)/len(v) for L, v in bundle_scores[bid].items()}

# Per-problem per-arm MCQ/VAL
problem_arm = defaultdict(lambda: defaultdict(list))
for bid, info in cond.items():
    if bid not in bundle_mean:
        continue
    prob = info['problem_id']
    arm = info['arm']
    ls = bundle_mean[bid]
    mcq = (ls['L2'] + ls['L3'] + ls['L4']) / 33 * 100
    val = ls['L4'] / 9 * 100
    problem_arm[prob][arm].append((mcq, val))

print('=== 逐题逐臂 MCQ / VAL (均值, n=rep数) ===')
print(f"{'problem':<10} {'F_MCQ':>7} {'S_MCQ':>7} {'SV_MCQ':>7} {'F_VAL':>7} {'S_VAL':>7} {'SV_VAL':>7}")
for prob in sorted(problem_arm.keys()):
    row = [prob]
    for arm in ['F', 'S', 'SV']:
        vals = problem_arm[prob][arm]
        if vals:
            mcq_m = sum(v[0] for v in vals) / len(vals)
            val_m = sum(v[1] for v in vals) / len(vals)
            row.append(f'{mcq_m:.1f}')
            row.append(f'{val_m:.1f}')
        else:
            row.append('N/A')
            row.append('N/A')
    print(f"{row[0]:<10} {row[1]:>7} {row[3]:>7} {row[5]:>7} {row[2]:>7} {row[4]:>7} {row[6]:>7}")

# Per-evaluator layer means
print('\n=== 各 evaluator 逐层均值 ===')
for ev in ['A', 'B', 'C']:
    layers = defaultdict(list)
    for i in range(1, 67):
        bid = f'BUNDLE_{i:03d}'
        fpath = EXP / 'scores' / f'evaluator_{ev}' / f'{bid}.json'
        if fpath.exists():
            data = json.loads(fpath.read_text(encoding='utf-8'))
            lt = data.get('layer_totals', {})
            for L in ['L1', 'L2', 'L3', 'L4']:
                layers[L].append(lt.get(L, 0))
    means = {L: sum(v)/len(v) for L, v in layers.items()}
    print(f"  {ev}: L1={means['L1']:.2f}, L2={means['L2']:.2f}, L3={means['L3']:.2f}, L4={means['L4']:.2f}")
