# -*- coding: utf-8 -*-
"""v1.1 重评 F/S 分组对比 — 读 runs_v11_scores/ + condition_map"""
import json, glob, os
BASE = 'research/P15/experiments/P15-K002-precheck'
cond = json.load(open(f'{BASE}/key/condition_map.json', encoding='utf-8'))['map']
files = sorted(glob.glob(f'{BASE}/runs_v11_scores/*.json'))
print('评分文件数:', len(files))

rows = []
for f in files:
    s = json.load(open(f, encoding='utf-8'))
    sid = os.path.basename(f)[:-5]
    meta = cond.get(sid, {})
    dims = s['dimensions']
    L1 = sum(v['score'] for k, v in dims.items() if k.startswith('L1'))
    L2 = sum(v['score'] for k, v in dims.items() if k.startswith('L2'))
    L3 = sum(v['score'] for k, v in dims.items() if k.startswith('L3'))
    L4 = sum(v['score'] for k, v in dims.items() if k.startswith('L4'))
    e4 = s.get('l26_four_elements', {}).get('E4')
    rows.append({'sid': sid[:8], 'problem': meta.get('problem_id', '?'),
                 'arm': meta.get('arm', '?'), 'L1': L1, 'L2': L2, 'L3': L3,
                 'L4': L4, 'E4': e4, 'tot': L1 + L2 + L3 + L4})
rows.sort(key=lambda r: (r['problem'], r['arm']))

hdr = f"{'题':7} {'臂':3} {'sid':9} {'L1':>3} {'L2':>3} {'L3':>3} {'L4':>3} {'tot':>4} {'E4':>4}"
print(hdr)
for r in rows:
    print(f"{r['problem']:7} {r['arm']:3} {r['sid']:9} {r['L1']:3} {r['L2']:3} "
          f"{r['L3']:3} {r['L4']:3} {r['tot']:4} {str(r['E4']):>4}")

print("\n=== F vs S 对比 ===")
for prob in sorted(set(r['problem'] for r in rows)):
    grp = [r for r in rows if r['problem'] == prob]
    f = [r for r in grp if r['arm'] == 'F']
    s = [r for r in grp if r['arm'] == 'S']
    if f and s:
        d_l2 = s[0]['L2'] - f[0]['L2']
        d_tot = s[0]['tot'] - f[0]['tot']
        print(f"{prob}: F L2={f[0]['L2']} S L2={s[0]['L2']} ΔL2={d_l2:+d} | "
              f"F tot={f[0]['tot']} S tot={s[0]['tot']} Δtot={d_tot:+d}")

# L2 分布
l2s = [r['L2'] for r in rows]
print(f"\nL2 分布: {sorted(l2s)}  均值={sum(l2s)/len(l2s):.2f}")
# E4 按臂
for arm in ('F', 'S'):
    grp = [r for r in rows if r['arm'] == arm]
    e4s = [r['E4'] for r in grp]
    print(f"E4 {arm} 臂: {e4s}  pass={sum(1 for e in e4s if e)}/{len(e4s)}")
