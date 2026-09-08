# -*- coding: utf-8 -*-
import json

with open(r'C:/Users/Lin/Desktop/Programs/MathModel/research/REPOSITORY_AUDIT/src/skills/论文自查类/bzd-model-dictionary/assets/model-dictionary.json', encoding='utf-8') as f:
    data = json.load(f)

print("root keys:", list(data.keys()))
print("数据集名称:", data.get("数据集名称"))
print("制作方:", data.get("制作方"))
print("使用许可:", str(data.get("使用许可"))[:200])
print("版权与传播声明:", str(data.get("版权与传播声明"))[:200])
rows = data.get("数据", [])
print("record count:", len(rows))
if rows:
    print("first record keys:", list(rows[0].keys()))
    print(json.dumps(rows[0], ensure_ascii=False, indent=1)[:1500])
    # category distribution
    from collections import Counter
    cat = Counter(r.get("模型大类", "") for r in rows)
    print("模型大类 distribution:", dict(cat.most_common(20)))
    group = Counter(r.get("具体分组", "") for r in rows)
    print("具体分组 top:", dict(group.most_common(20)))
