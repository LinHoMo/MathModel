# -*- coding: utf-8 -*-
"""Scan all method cards for field structure quality tiers."""
import pathlib, re, json

cards = sorted(pathlib.Path('src/modeling_harness/knowledge/methods/cards').glob('*.yaml'))
fields = ['mechanism', 'formulations', 'solvers', 'structure_signals', 'requires',
          'risks', 'validation', 'anti_patterns', 'known_failures', 'match', 'applicability']
print('%-22s %5s | %s' % ('card', 'len', ' '.join('%6s' % f[:6] for f in fields)))
rows = []
for c in cards:
    text = c.read_text(encoding='utf-8')
    found = {}
    for f in fields:
        found[f] = bool(re.search(r'^%s:' % re.escape(f), text, re.M))
    rows.append({'card': c.stem, 'len': len(text), **found})
    marks = ''.join('  Y  ' if found[f] else '  -  ' for f in fields)
    print('%-22s %5d | %s' % (c.stem, len(text), marks))

# 分层
tier1 = [r['card'] for r in rows if r['mechanism'] and r['structure_signals'] and r['formulations']]
tier2 = [r['card'] for r in rows if r['mechanism'] and not r['structure_signals']]
tier3 = [r['card'] for r in rows if not r['mechanism']]
print('\nTier1 (mechanism+structure_signals+formulations):', tier1)
print('Tier2 (mechanism, no structure_signals):', tier2)
print('Tier3 (no mechanism):', tier3)
with open('research/P15/analysis/card_quality_scan.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
print('saved research/P15/analysis/card_quality_scan.json')
