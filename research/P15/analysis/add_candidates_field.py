# -*- coding: utf-8 -*-
"""S/SV 模板：model_family 增加 candidates 字段（E4 机械支撑）— 修正模式"""
import io, re

OLD = '`{"primary": "...", "secondary": [...]}`，primary 用受控词表'
NEW = ('`{"primary": "...", "secondary": [...], "candidates": [{"family": "...", "rationale": "选择/排除依据"}]}`'
       '（`candidates` 记录候选模型对比：≥2 个候选 + 各自选择/排除依据，是机理选择的质量证据；无对比写空数组），'
       'primary 用受控词表')

for p in ['research/P15/protocol/frozen_specs_k002/prompt_templates/S.md',
          'research/P15/protocol/frozen_specs_k002/prompt_templates/SV.md']:
    t = io.open(p, encoding='utf-8').read()
    if OLD in t:
        io.open(p, 'w', encoding='utf-8', newline='').write(t.replace(OLD, NEW))
        print(p, 'UPDATED')
    else:
        m = re.search(r'model_family[^\n]{0,160}', t)
        print(p, 'PATTERN NOT FOUND')
        print('  实际:', m.group(0) if m else '未找到')

def clen(p):
    return len(io.open(p, encoding='utf-8').read())
f, s, sv = (clen('research/P15/protocol/frozen_specs_k002/prompt_templates/%s.md' % x) for x in ('F', 'S', 'SV'))
print(f'F={f} S={s} SV={sv}')
print(f'F/S 长度差 = {abs(f-s)/min(f,s)*100:.2f}%')
print(f'S/SV 长度差 = {abs(s-sv)/min(s,sv)*100:.2f}%')
