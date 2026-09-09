# -*- coding: utf-8 -*-
"""F.md 长度平衡：加候选对比的可选建议（E4 公平性 + 长度对齐）"""
import io

p = 'research/P15/protocol/frozen_specs_k002/prompt_templates/F.md'
t = io.open(p, encoding='utf-8').read()

# 在输出要求段末尾加一句通用建模建议（不强制结构，保持自由文本属性）
anchor = '输出格式：仅 Markdown 文档本身，不要输出其他解释文字。'
addition = '\n\n**候选模型对比**：建模过程中若比较了多个候选模型/方法，请说明各自优劣与最终选择依据（这是模型构建质量的必要部分，务必覆盖）。'

if anchor in t:
    io.open(p, 'w', encoding='utf-8', newline='').write(t.replace(anchor, anchor + addition))
    print('F.md UPDATED')
else:
    print('anchor NOT FOUND')

def clen(p):
    return len(io.open(p, encoding='utf-8').read())
f, s, sv = (clen('research/P15/protocol/frozen_specs_k002/prompt_templates/%s.md' % x) for x in ('F', 'S', 'SV'))
print(f'F={f} S={s} SV={sv}')
print(f'F/S 长度差 = {abs(f-s)/min(f,s)*100:.2f}%')
