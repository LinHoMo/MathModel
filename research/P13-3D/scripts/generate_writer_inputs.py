#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_writer_inputs.py — Generate blind writer inputs for P13-3D.

Writer receives only: question text + anonymized artifact (X/Y/Z).
No arm identity, no prior scores, no evaluation results.
"""
import json
import random
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parent.parent.parent
artifacts_dir = ROOT / "research" / "P13-3D" / "output" / "artifacts"
papers_dir = ROOT / "research" / "P13-3D" / "output" / "papers"
papers_dir.mkdir(parents=True, exist_ok=True)

QUESTIONS = [
    {"id": "2024_A", "name": "七鳃鳗性别比", "regime": "mechanism"},
    {"id": "2021_C", "name": "亚洲大黄蜂", "regime": "data"},
    {"id": "2022_B", "name": "两库水资源", "regime": "optimization"},
]
ARMS = ["B0", "MMA", "B1-F"]

WRITER_PROMPT = """# 数学建模论文撰写

请根据提供的建模产物，撰写完整的数学建模论文。

## 撰写要求

1. **问题重述**：用自己的语言重新描述题目要求，明确要回答的子问题。
2. **假设**：列出建模产物中明确声明的假设，说明每个假设的合理性。
3. **符号说明**：整理建模产物中的变量和参数，用表格呈现。
4. **模型建立**：
   - 目标函数/估计量：完整写出数学表达式。
   - 约束条件：逐条列出，附物理/工程解释。
   - 机理方程：写出状态转移方程或核心方程组。
   - 模型选择理由：为什么选这个模型而非其他候选。
5. **求解方法**：描述求解思路（数值/解析/仿真），给出算法步骤。

## 格式要求

- 公式用 LaTeX（$$...$$ 或 \\[...\\]）
- 无实验数据处以"待实验验证"或占位符标注
- 不要编造数据或实验结果
- 中文撰写
- 标题用 `# 建模论文`

## 重要提醒

- 严格基于提供的建模产物撰写，不要自行添加产物中没有的变量、约束或假设。
- 如果产物中缺少某个子问题的模型，如实说明"该子问题的模型待补充"。
- 保持学术论文的客观、严谨风格。
"""

# Load question texts
bench_path = ROOT / "core" / "knowledge" / "problems" / "CUMCM-Bench.json"
bench = json.loads(bench_path.read_text(encoding="utf-8"))
q_texts = {}
for q in bench.get("problems", []):
    if q.get("id") in ["2024_A", "2021_C", "2022_B"]:
        q_texts[q["id"]] = q.get("text", q.get("problem_text", f"题目 {q['id']}"))

# Generate
for q_info in QUESTIONS:
    qid = q_info["id"]

    artifacts = {}
    for arm in ARMS:
        path = artifacts_dir / f"{qid}_{arm}.json"
        if path.exists():
            artifacts[arm] = json.loads(path.read_text(encoding="utf-8"))

    if len(artifacts) < 3:
        print(f"SKIP {qid}: only {len(artifacts)} artifacts")
        continue

    arms_list = list(artifacts.keys())
    random.shuffle(arms_list)
    mapping = {arm: chr(ord("X") + i) for i, arm in enumerate(arms_list)}

    print(f"{qid}: {mapping}")

    for arm, anon_id in mapping.items():
        artifact = artifacts[arm]

        anon_artifact = {k: v for k, v in artifact.items()
                        if k not in ["arm", "agent", "model_name", "prompt_version",
                                     "mma_raw_output", "reconstruction_set"]}

        q_text = q_texts.get(qid, q_info["name"])
        artifact_json = json.dumps(anon_artifact, ensure_ascii=False, indent=2)

        writer_input = f"""# 数学建模论文撰写

## 题目原文

{q_text}

## 匿名建模产物（Identity: {anon_id}）

```json
{artifact_json}
```

---

{WRITER_PROMPT}
"""

        out_path = papers_dir / f"{qid}_{arm}_writer_input.md"
        out_path.write_text(writer_input, encoding="utf-8")
        print(f"  {arm} -> {anon_id} -> {out_path.name}")

print("\nDone. 9 writer inputs generated.")
