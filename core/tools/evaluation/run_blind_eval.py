#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_blind_eval.py — Generate blind evaluation prompts for P13-3D.

Each question gets one evaluation prompt containing:
- Question text
- Three anonymized papers (X/Y/Z, randomly ordered)
- Three corresponding anonymized artifacts

The evaluator outputs Paper Quality (4 dimensions) + mutation log.
"""
import json
import random
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parent.parent.parent.parent
papers_dir = ROOT / "projects" / "P13-3D" / "output" / "papers"
artifacts_dir = ROOT / "projects" / "P13-3D" / "output" / "artifacts"
eval_dir = ROOT / "projects" / "P13-3D" / "output" / "evaluation"
eval_dir.mkdir(parents=True, exist_ok=True)

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = [
    {"id": "2024_A", "name": "七鳃鳗性别比"},
    {"id": "2021_C", "name": "亚洲大黄蜂"},
    {"id": "2022_B", "name": "两库水资源"},
]

# Load question texts
bench_path = ROOT / "core" / "knowledge" / "problems" / "CUMCM-Bench.json"
bench = json.loads(bench_path.read_text(encoding="utf-8"))
q_texts = {}
for q in bench.get("problems", []):
    if q.get("id") in ["2024_A", "2021_C", "2022_B"]:
        q_texts[q["id"]] = q.get("text", q.get("problem_text", f"题目 {q['id']}"))

EVAL_INSTRUCTIONS = """你是一个数学建模论文盲评评委。请对以下三份论文进行独立评分。

## 评分维度（每项 0-100 分）

1. **Mathematical correctness**（数学正确性）：公式/推导/量纲是否正确
2. **Problem alignment**（问题对齐）：论文是否回答了题目要求的所有子问题
3. **Completeness**（完整性）：模型组件覆盖度（变量/约束/目标/假设/方程）
4. **Communication**（表达质量）：结构清晰度、可读性、图表规范性

## 输出格式（严格 JSON）

```json
{
  "papers": [
    {
      "id": "X",
      "scores": {
        "math_correctness": <0-100>,
        "problem_alignment": <0-100>,
        "completeness": <0-100>,
        "communication": <0-100>
      },
      "comments": "<中文评语>"
    },
    {
      "id": "Y",
      "scores": {...},
      "comments": "..."
    },
    {
      "id": "Z",
      "scores": {...},
      "comments": "..."
    }
  ],
  "mutation_audit": [
    {
      "paper_id": "<X/Y/Z>",
      "mutations": [
        {
          "type": "<deletion/addition/modification/renaming/semantic_drift>",
          "severity": "<critical/major/minor>",
          "category": "<variables/constraints/objective/mechanism/assumptions>",
          "affected_object": "<具体对象>",
          "description": "<描述>"
        }
      ]
    }
  ]
}
```

## 注意事项

- 论文已匿名化（X/Y/Z），请勿猜测作者身份
- 只评分论文内容，不评分排版格式
- 每份论文独立评分，不要互相比较
- 输出纯 JSON，不要其他文字
"""

for q_info in QUESTIONS:
    qid = q_info["id"]

    # Load papers and artifacts
    papers = {}
    artifacts = {}
    for arm in ARMS:
        pf = papers_dir / f"{qid}_{arm}.md"
        af = artifacts_dir / f"{qid}_{arm}.json"
        if pf.exists() and af.exists():
            papers[arm] = pf.read_text(encoding="utf-8")
            artifacts[arm] = json.loads(af.read_text(encoding="utf-8"))

    if len(papers) < 3:
        print(f"SKIP {qid}: only {len(papers)} papers")
        continue

    # Randomize arm order
    arms_list = list(papers.keys())
    random.shuffle(arms_list)
    mapping = {arm: chr(ord("X") + i) for i, arm in enumerate(arms_list)}

    print(f"{qid}: {mapping}")

    # Build evaluation prompt
    q_text = q_texts.get(qid, q_info["name"])

    eval_parts = [
        f"# Paper Quality Evaluation — {qid} ({q_info['name']})\n",
        EVAL_INSTRUCTIONS,
        f"\n## 题目原文\n\n{q_text}\n",
    ]

    # Add papers in random order
    for arm in arms_list:
        anon_id = mapping[arm]
        eval_parts.append(f"\n## 论文 {anon_id}\n")
        eval_parts.append(papers[arm])

    # Add artifacts for reference
    eval_parts.append("\n## 匿名建模产物（仅供参考）\n")
    for arm in arms_list:
        anon_id = mapping[arm]
        eval_parts.append(f"\n### 产物 {anon_id}\n")
        eval_parts.append(f"```json\n{json.dumps(artifacts[arm], ensure_ascii=False, indent=2)}\n```")

    # Save
    eval_file = eval_dir / f"{qid}_eval_prompt.md"
    eval_file.write_text("\n".join(eval_parts), encoding="utf-8")

    # Save mapping (not visible to evaluator)
    mapping_file = eval_dir / f"{qid}_arm_mapping.json"
    mapping_file.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  eval prompt -> {eval_file.name}")
    print(f"  mapping -> {mapping_file.name}")

print("\nDone. 3 evaluation prompts generated.")
