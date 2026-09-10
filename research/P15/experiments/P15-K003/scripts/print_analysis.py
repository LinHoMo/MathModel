import json
d = json.load(open(r'C:\Users\Lin\Desktop\Programs\MathModel\research\P15\experiments\P15-K003\analysis\paired_analysis.json', encoding='utf-8'))

print('=== 泛化 (4 blocks) ===')
for c in ['S−F', 'SV−F']:
    for m in ['mcq', 'val']:
        r = d['primary_results']['generalization'][c][m]
        print(f"  {c} {m}: Δ={r['mean_diff']}, CI={r['ci_95']}, d={r['cohens_d']}, sig={r['significant']}")

print('\n=== 敏感性: 主检验逐层 (18 blocks) ===')
for c in ['S−F', 'SV−F']:
    for L in ['L1', 'L2', 'L3', 'L4']:
        r = d['sensitivity_results']['main'][c][L]
        print(f"  {c} {L}: Δ={r['mean_diff']}, CI={r['ci_95']}, sig={r['significant']}")

print('\n=== ALL scope (22 blocks) ===')
for c in ['S−F', 'SV−F']:
    for m in ['mcq', 'val']:
        r = d['primary_results']['all'][c][m]
        print(f"  {c} {m}: Δ={r['mean_diff']}, CI={r['ci_95']}, d={r['cohens_d']}, sig={r['significant']}")

print('\n=== 各臂逐层均值 ===')
for arm in ['F', 'S', 'SV']:
    am = d['arm_means'][arm]
    print(f"  {arm}: MCQ={am['mcq_mean']}, VAL={am['val_mean']}, layers={am['layer_means']}")
