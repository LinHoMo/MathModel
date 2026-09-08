#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_r2_writer_inputs.py — P13-3D-R2 Phase 3: Generate 24 Writer inputs.

Protocol:
- Same Writer prompt for all 8 questions
- Blind X/Y/Z assignment (independent seed per question)
- Each Writer input contains: problem text + frozen MODEL_ARTIFACT (anonymized)
- No arm identity visible to Writer
"""
import json
import hashlib
import random
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]
ARTIFACTS_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
INPUTS_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "writer_inputs"
INPUTS_DIR.mkdir(parents=True, exist_ok=True)

ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

# Problem titles for blind labeling
TITLES = {
    "2019_A": "高压油管的压力控制",
    "2022_A": "波浪能最大输出功率设计",
    "2017_B": '"拍照赚钱"的任务定价',
    "2022_C": "古代玻璃制品的成分分析与鉴别",
    "2020_B": "穿越沙漠",
    "2024_B": "生产过程中的决策问题",
    "2023_C": "蔬菜类商品的自动定价与补货决策",
    "2024_C": "农作物的种植策略",
}

# Fixed Writer prompt (same for all questions)
WRITER_PROMPT = """你是一位数学建模论文撰写专家。请根据以下信息撰写一篇完整的数学建模竞赛论文。

**题目**：{title}

**问题描述**：
{problem_text}

**模型产物（MODEL_ARTIFACT）**：
以下是建模阶段产出的结构化模型信息。请严格基于此模型撰写论文，**不得修改、补充或删除模型中的任何元素**。

```json
{artifact_json}
```

**论文要求**：
1. 按照标准数学建模论文格式撰写（摘要、问题重述、模型假设、符号说明、模型建立与求解、模型评价、参考文献）
2. 所有数学公式使用 LaTeX 格式
3. 论文中的所有变量、参数、约束、机制必须与 MODEL_ARTIFACT 完全一致
4. 不得引入 MODEL_ARTIFACT 中未定义的新变量、新约束或新机制
5. 不得修改 MODEL_ARTIFACT 中已有元素的含义或表达式
6. 摘要需概括问题、模型、主要结论
7. 模型假设需列出 MODEL_ARTIFACT 中的所有假设
8. 符号说明需列出 MODEL_ARTIFACT 中的所有变量和参数
9. 模型建立需详细展开 MODEL_ARTIFACT 中的所有机制方程
10. 模型评价需讨论局限性和改进方向

**输出格式**：LaTeX 格式的完整论文"""

# Blind arm mapping (random seed per question)
arm_mappings = {}

# Generate random mappings
rng = random.Random(42)  # Fixed seed for reproducibility
for qid in QUESTIONS:
    arms_shuffled = ARMS.copy()
    rng.shuffle(arms_shuffled)
    arm_mappings[qid] = {"X": arms_shuffled[0], "Y": arms_shuffled[1], "Z": arm_mappings.get(qid, {}).get("Z", arms_shuffled[2])}
    arm_mappings[qid]["X"] = arms_shuffled[0]
    arm_mappings[qid]["Y"] = arms_shuffled[1]
    arm_mappings[qid]["Z"] = arms_shuffled[2]

# Save arm mapping (hidden from evaluation)
mapping_path = INPUTS_DIR / "arm_mapping.json"
mapping_path.write_text(json.dumps(arm_mappings, ensure_ascii=False, indent=2), encoding="utf-8")

# Generate Writer inputs
generated = []
for qid in QUESTIONS:
    mapping = arm_mappings[qid]
    title = TITLES[qid]

    # Load problem text from artifact
    sample_artifact = json.loads((ARTIFACTS_DIR / f"{qid}_B0.json").read_text(encoding="utf-8"))

    for letter in ["X", "Y", "Z"]:
        arm = mapping[letter]
        fname = f"{qid}_{arm.replace('-', '_')}.json"
        artifact = json.loads((ARTIFACTS_DIR / fname).read_text(encoding="utf-8"))

        # Create blind input (remove any arm-identifying info)
        artifact_blind = {k: v for k, v in artifact.items() if k not in ["mma_raw_output"]}

        writer_input = WRITER_PROMPT.format(
            title=title,
            problem_text=sample_artifact.get("problem_interpretation", ""),
            artifact_json=json.dumps(artifact_blind, ensure_ascii=False, indent=2)
        )

        # Save writer input
        input_fname = f"{qid}_{letter}_writer_input.md"
        input_path = INPUTS_DIR / input_fname
        input_path.write_text(writer_input, encoding="utf-8")

        # SHA256
        sha = hashlib.sha256(writer_input.encode("utf-8")).hexdigest()

        generated.append({
            "problem_id": qid,
            "letter": letter,
            "arm": arm,
            "input_file": input_fname,
            "sha256": sha,
        })

        print(f"✓ {qid}/{letter} (arm={arm}): {input_fname}")

# Save manifest
manifest = {
    "round": "P13-3D-R2",
    "phase": "Phase 3: Writer Input Generation",
    "protocol": {
        "writer_prompt": "Fixed for all 8 questions",
        "arm_mapping": "Random per question, seed=42",
        "blind": "X/Y/Z labels, arm identity hidden",
    },
    "inputs": generated,
    "total": len(generated),
}
manifest_path = INPUTS_DIR / "manifest.json"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\nManifest: {manifest_path}")
print(f"Total: {len(generated)} writer inputs generated")
print(f"Arm mapping: {mapping_path}")
