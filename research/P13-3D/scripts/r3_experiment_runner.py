#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r3_experiment_runner.py — R3 Real Writer Experiment Runner.

Generates prompts for W0 and W1 conditions, saves them for execution,
and provides evaluation pipeline for generated papers.

Usage:
  # Generate prompts
  python r3_experiment_runner.py generate-prompts

  # Evaluate papers (after manual generation)
  python r3_experiment_runner.py evaluate --condition W0
  python r3_experiment_runner.py evaluate --condition W1
  python r3_experiment_runner.py evaluate --all

  # Freeze results
  python r3_experiment_runner.py freeze

  # Run hypothesis tests
  python r3_experiment_runner.py hypothesis-test
"""
import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent
R2_ARTIFACTS = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
R3_MAPS = ROOT / "research" / "P13-3D-R3" / "output" / "maps"
R3_DIR = ROOT / "research" / "P13-3D-R3"
R3_PROMPTS = R3_DIR / "prompts"
R3_PAPERS = R3_DIR / "real_papers"
R3_EVAL = R3_DIR / "real_evaluation"
R3_STATE = R3_DIR / "state"

for d in [R3_PROMPTS, R3_PAPERS, R3_EVAL, R3_STATE]:
    d.mkdir(parents=True, exist_ok=True)

# Configuration
ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

TITLES = {
    "2019_A": "高压油管的压力控制",
    "2022_A": "波浪能最大输出功率设计",
    "2017_B": "拍照赚钱的任务定价",
    "2022_C": "古代玻璃制品的成分分析与鉴别",
    "2020_B": "穿越沙漠",
    "2024_B": "生产过程中的决策问题",
    "2023_C": "蔬菜类商品的自动定价与补货决策",
    "2024_C": "农作物的种植策略",
}

# System prompts
W0_SYSTEM_PROMPT = """你是一个数学建模竞赛论文撰写专家。你的任务是根据提供的模型构件（MODEL_ARTIFACT），撰写一篇完整的、可提交的数学建模竞赛论文。

论文要求：
1. 结构完整：摘要、问题重述、模型假设、符号说明、模型建立与求解、候选模型对比、选定模型说明、灵敏度分析、模型评价、结论
2. 数学规范：所有公式使用 LaTeX 格式，变量有明确定义
3. 逻辑连贯：从问题分析到模型建立到求解到评价，逻辑清晰
4. 语言流畅：中文撰写，学术语言风格
5. 篇幅适中：15-20 页

请注意：你必须完整呈现模型构件中的所有元素，包括：
- 所有变量和参数
- 所有机制（方程）
- 目标函数
- 所有约束条件
- 所有假设
- 所有候选模型及其优缺点
- 选定模型及其选择理由
- 完整的灵敏度分析计划"""

W1_SYSTEM_PROMPT = """你是一个数学建模竞赛论文撰写专家。你的任务是根据提供的模型构件（MODEL_ARTIFACT）和结构化映射（MODEL_PAPER_MAP），撰写一篇完整的、可提交的数学建模竞赛论文。

论文要求：
1. 结构完整：摘要、问题重述、模型假设、符号说明、模型建立与求解、候选模型对比、选定模型说明、灵敏度分析、模型评价、结论
2. 数学规范：所有公式使用 LaTeX 格式，变量有明确定义
3. 逻辑连贯：从问题分析到模型建立到求解到评价，逻辑清晰
4. 语言流畅：中文撰写，学术语言风格
5. 篇幅适中：15-20 页

重要：你必须严格按照结构化映射组织论文结构。结构化映射指定了：
- 每个模型构件应该出现在论文的哪个章节
- 每个章节需要包含哪些模型构件
- 候选模型的对比结构
- 灵敏度分析的参数和指标

请确保：
1. 每个模型构件都在映射指定的章节中出现
2. 不要在映射指定的章节之外添加额外的模型构件
3. 保持映射中定义的元素关系"""


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_w0_prompt(qid: str, arm: str) -> dict:
    """Generate W0 prompt for one artifact."""
    artifact_file = R2_ARTIFACTS / f"{qid}_{arm.replace('-', '_')}.json"
    artifact = json.loads(artifact_file.read_text(encoding="utf-8"))

    user_prompt = f"""## 模型构件 (MODEL_ARTIFACT)

### 基本信息
- 问题ID：{qid}
- 问题类型：{artifact.get('problem_type', 'unknown')}
- 问题标题：{TITLES.get(qid, 'unknown')}

### 变量 (variables)
```json
{json.dumps(artifact.get('variables', []), ensure_ascii=False, indent=2)}
```

### 参数 (parameters)
```json
{json.dumps(artifact.get('parameters', []), ensure_ascii=False, indent=2)}
```

### 机制 (mechanism)
```json
{json.dumps(artifact.get('mechanism', []), ensure_ascii=False, indent=2)}
```

### 目标 (objective)
```json
{json.dumps(artifact.get('objective', []), ensure_ascii=False, indent=2)}
```

### 约束 (constraints)
```json
{json.dumps(artifact.get('constraints', []), ensure_ascii=False, indent=2)}
```

### 假设 (assumptions)
```json
{json.dumps(artifact.get('assumptions', []), ensure_ascii=False, indent=2)}
```

### 候选模型 (candidate_models)
```json
{json.dumps(artifact.get('candidate_models', []), ensure_ascii=False, indent=2)}
```

### 选定模型 (selected_model)
{artifact.get('selected_model', 'N/A')}

### 选择理由 (selection_reason)
{artifact.get('selection_reason', 'N/A')}

### 灵敏度计划 (sensitivity_plan)
```json
{json.dumps(artifact.get('sensitivity_plan', []), ensure_ascii=False, indent=2)}
```

---

请根据以上模型构件，撰写一篇完整的数学建模竞赛论文。论文必须包含上述所有元素，不要遗漏任何部分。"""

    return {
        "system": W0_SYSTEM_PROMPT,
        "user": user_prompt,
        "metadata": {
            "problem_id": qid,
            "arm": arm,
            "condition": "W0",
            "artifact_file": artifact_file.name,
            "artifact_sha256": compute_sha256(artifact_file.read_text(encoding="utf-8")),
            "generated_at": datetime.now().isoformat(),
        }
    }


def generate_w1_prompt(qid: str, arm: str) -> dict:
    """Generate W1 prompt for one artifact + mapping."""
    artifact_file = R2_ARTIFACTS / f"{qid}_{arm.replace('-', '_')}.json"
    map_file = R3_MAPS / f"{qid}_{arm.replace('-', '_')}_map.json"

    artifact = json.loads(artifact_file.read_text(encoding="utf-8"))
    mapping = json.loads(map_file.read_text(encoding="utf-8"))

    user_prompt = f"""## 模型构件 (MODEL_ARTIFACT)

### 基本信息
- 问题ID：{qid}
- 问题类型：{artifact.get('problem_type', 'unknown')}
- 问题标题：{TITLES.get(qid, 'unknown')}

### 变量 (variables)
```json
{json.dumps(artifact.get('variables', []), ensure_ascii=False, indent=2)}
```

### 参数 (parameters)
```json
{json.dumps(artifact.get('parameters', []), ensure_ascii=False, indent=2)}
```

### 机制 (mechanism)
```json
{json.dumps(artifact.get('mechanism', []), ensure_ascii=False, indent=2)}
```

### 目标 (objective)
```json
{json.dumps(artifact.get('objective', []), ensure_ascii=False, indent=2)}
```

### 约束 (constraints)
```json
{json.dumps(artifact.get('constraints', []), ensure_ascii=False, indent=2)}
```

### 假设 (assumptions)
```json
{json.dumps(artifact.get('assumptions', []), ensure_ascii=False, indent=2)}
```

### 候选模型 (candidate_models)
```json
{json.dumps(artifact.get('candidate_models', []), ensure_ascii=False, indent=2)}
```

### 选定模型 (selected_model)
{artifact.get('selected_model', 'N/A')}

### 选择理由 (selection_reason)
{artifact.get('selection_reason', 'N/A')}

### 灵敏度计划 (sensitivity_plan)
```json
{json.dumps(artifact.get('sensitivity_plan', []), ensure_ascii=False, indent=2)}
```

---

## 结构化映射 (MODEL_PAPER_MAP)

### 章节映射 (section_map)
```json
{json.dumps(mapping.get('section_map', []), ensure_ascii=False, indent=2)}
```

### 元素映射 (element_map)
```json
{json.dumps(mapping.get('element_map', []), ensure_ascii=False, indent=2)}
```

### 主张清单 (claim_inventory)
```json
{json.dumps(mapping.get('claim_inventory', []), ensure_ascii=False, indent=2)}
```

### 候选模型映射 (candidate_model_map)
```json
{json.dumps(mapping.get('candidate_model_map', []), ensure_ascii=False, indent=2)}
```

### 灵敏度映射 (sensitivity_map)
```json
{json.dumps(mapping.get('sensitivity_map', []), ensure_ascii=False, indent=2)}
```

### 问题映射 (question_map)
```json
{json.dumps(mapping.get('question_map', []), ensure_ascii=False, indent=2)}
```

---

请根据以上模型构件和结构化映射，撰写一篇完整的数学建模竞赛论文。严格按照映射组织结构，确保每个构件都在指定章节中完整呈现。"""

    return {
        "system": W1_SYSTEM_PROMPT,
        "user": user_prompt,
        "metadata": {
            "problem_id": qid,
            "arm": arm,
            "condition": "W1",
            "artifact_file": artifact_file.name,
            "artifact_sha256": compute_sha256(artifact_file.read_text(encoding="utf-8")),
            "map_file": map_file.name,
            "map_sha256": compute_sha256(map_file.read_text(encoding="utf-8")),
            "generated_at": datetime.now().isoformat(),
        }
    }


# ═══════════════════════════════════════════════════════════════
# Command: generate-prompts
# ═══════════════════════════════════════════════════════════════

def cmd_generate_prompts(args):
    """Generate all W0 and W1 prompts."""
    print("=" * 70)
    print("GENERATE W0 AND W1 PROMPTS")
    print("=" * 70)

    manifest = {"W0": [], "W1": []}

    for qid in QUESTIONS:
        for arm in ARMS:
            # W0 prompt
            w0_prompt = generate_w0_prompt(qid, arm)
            w0_file = R3_PROMPTS / f"{qid}_{arm.replace('-', '_')}_W0.json"
            w0_file.write_text(json.dumps(w0_prompt, ensure_ascii=False, indent=2), encoding="utf-8")
            manifest["W0"].append({
                "problem_id": qid,
                "arm": arm,
                "prompt_file": w0_file.name,
                "artifact_sha256": w0_prompt["metadata"]["artifact_sha256"],
            })
            print(f"  W0: {qid}/{arm} -> {w0_file.name}")

            # W1 prompt
            w1_prompt = generate_w1_prompt(qid, arm)
            w1_file = R3_PROMPTS / f"{qid}_{arm.replace('-', '_')}_W1.json"
            w1_file.write_text(json.dumps(w1_prompt, ensure_ascii=False, indent=2), encoding="utf-8")
            manifest["W1"].append({
                "problem_id": qid,
                "arm": arm,
                "prompt_file": w1_file.name,
                "artifact_sha256": w1_prompt["metadata"]["artifact_sha256"],
                "map_sha256": w1_prompt["metadata"]["map_sha256"],
            })
            print(f"  W1: {qid}/{arm} -> {w1_file.name}")

    # Save manifest
    manifest_path = R3_PROMPTS / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nManifest: {manifest_path}")
    print(f"Total prompts: {len(manifest['W0'])} W0 + {len(manifest['W1'])} W1")


# ═══════════════════════════════════════════════════════════════
# Command: evaluate
# ═══════════════════════════════════════════════════════════════

def cmd_evaluate(args):
    """Evaluate generated papers."""
    import sys
    sys.path.insert(0, str(ROOT / "core" / "tools" / "evaluation"))
    from stc_evaluator import compute_stc_v2

    conditions = [args.condition] if args.condition else ["W0", "W1"]

    print("=" * 70)
    print("EVALUATE PAPERS")
    print("=" * 70)

    for condition in conditions:
        print(f"\n--- {condition} ---")
        papers_dir = R3_PAPERS / condition
        if not papers_dir.exists():
            print(f"  No papers found at {papers_dir}")
            continue

        results = []
        for paper_file in sorted(papers_dir.glob("*.md")):
            # Parse filename: {qid}_{arm}.md
            parts = paper_file.stem.split("_")
            if len(parts) < 2:
                continue
            arm = parts[-1]
            qid = "_".join(parts[:-1])

            # Load artifact
            artifact_file = R2_ARTIFACTS / f"{qid}_{arm.replace('-', '_')}.json"
            if not artifact_file.exists():
                continue

            artifact = json.loads(artifact_file.read_text(encoding="utf-8"))
            paper_text = paper_file.read_text(encoding="utf-8")

            # Compute STC
            stc = compute_stc_v2(paper_text, artifact)

            results.append({
                "problem_id": qid,
                "arm": arm,
                "condition": condition,
                "stc_core": stc["stc_core"],
                "stc_meta": stc["stc_meta"],
                "stc_overall": stc["stc_overall"],
            })

            print(f"  {qid}/{arm}: STC_core={stc['stc_core']:.3f}, STC_meta={stc['stc_meta']:.3f}")

        # Save results
        eval_path = R3_EVAL / f"{condition}_results.json"
        eval_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  Saved: {eval_path}")


# ═══════════════════════════════════════════════════════════════
# Command: freeze
# ═══════════════════════════════════════════════════════════════

def cmd_freeze(args):
    """Freeze all results."""
    print("=" * 70)
    print("FREEZE RESULTS")
    print("=" * 70)

    freeze_manifest = {
        "project": "P13-3D-R3",
        "phase": "Real Writer Experiment",
        "status": "FROZEN",
        "frozen_at": datetime.now().isoformat(),
        "protocol": "R3_WRITER_PROTOCOL.md",
        "conditions": {},
    }

    for condition in ["W0", "W1"]:
        eval_path = R3_EVAL / f"{condition}_results.json"
        if eval_path.exists():
            results = json.loads(eval_path.read_text(encoding="utf-8"))
            freeze_manifest["conditions"][condition] = {
                "count": len(results),
                "sha256": compute_sha256(eval_path.read_text(encoding="utf-8")),
            }
            print(f"  {condition}: {len(results)} papers frozen")

    freeze_path = R3_EVAL / "freeze_manifest.json"
    freeze_path.write_text(json.dumps(freeze_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nFreeze manifest: {freeze_path}")


# ═══════════════════════════════════════════════════════════════
# Command: hypothesis-test
# ═══════════════════════════════════════════════════════════════

def cmd_hypothesis_test(args):
    """Run hypothesis tests H13-H18."""
    print("=" * 70)
    print("HYPOTHESIS TESTS (H13-H18)")
    print("=" * 70)

    # Load results
    w0_path = R3_EVAL / "W0_results.json"
    w1_path = R3_EVAL / "W1_results.json"

    if not w0_path.exists() or not w1_path.exists():
        print("Error: Results not found. Run evaluate first.")
        return

    w0_results = json.loads(w0_path.read_text(encoding="utf-8"))
    w1_results = json.loads(w1_path.read_text(encoding="utf-8"))

    # H13: STC_meta improvement
    w0_meta = sum(r["stc_meta"] for r in w0_results) / len(w0_results)
    w1_meta = sum(r["stc_meta"] for r in w1_results) / len(w1_results)
    h13_delta = w1_meta - w0_meta
    h13_pass = h13_delta >= 0.15

    print(f"\nH13 — Structural Transmission:")
    print(f"  STC_meta(W0): {w0_meta:.3f}")
    print(f"  STC_meta(W1): {w1_meta:.3f}")
    print(f"  Δ: {h13_delta:+.3f} (threshold: +0.15)")
    print(f"  Result: {'PASS' if h13_pass else 'FAIL'}")

    # H14: Paper Quality (placeholder - needs blind eval)
    print(f"\nH14 — Paper Quality:")
    print(f"  (Requires blind paper quality evaluation)")
    print(f"  Result: PENDING")

    # H15: Capability Transmission (placeholder)
    print(f"\nH15 — Capability Transmission Recovery:")
    print(f"  (Requires per-arm paper quality comparison)")
    print(f"  Result: PENDING")

    # H16: No Unauthorized Mutation (placeholder)
    print(f"\nH16 — No Unauthorized Mutation:")
    print(f"  (Requires mutation analysis)")
    print(f"  Result: PENDING")

    # H17: Mechanistic Mediation (placeholder)
    print(f"\nH17 — Mechanistic Mediation:")
    print(f"  (Requires per-question ΔSTC vs ΔPaper correlation)")
    print(f"  Result: PENDING")

    # H18: Core Preservation
    w0_core = sum(r["stc_core"] for r in w0_results) / len(w0_results)
    w1_core = sum(r["stc_core"] for r in w1_results) / len(w1_results)
    h18_delta = w1_core - w0_core
    h18_pass = h18_delta >= -0.05

    print(f"\nH18 — Core Preservation:")
    print(f"  STC_core(W0): {w0_core:.3f}")
    print(f"  STC_core(W1): {w1_core:.3f}")
    print(f"  Δ: {h18_delta:+.3f} (threshold: >= -0.05)")
    print(f"  Result: {'PASS' if h18_pass else 'FAIL'}")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="R3 Experiment Runner")
    subparsers = parser.add_subparsers(dest="command")

    # generate-prompts
    subparsers.add_parser("generate-prompts", help="Generate W0 and W1 prompts")

    # evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate papers")
    eval_parser.add_argument("--condition", choices=["W0", "W1"], help="Condition to evaluate")
    eval_parser.add_argument("--all", action="store_true", help="Evaluate all conditions")

    # freeze
    subparsers.add_parser("freeze", help="Freeze results")

    # hypothesis-test
    subparsers.add_parser("hypothesis-test", help="Run hypothesis tests")

    args = parser.parse_args()

    if args.command == "generate-prompts":
        cmd_generate_prompts(args)
    elif args.command == "evaluate":
        if args.all:
            args.condition = None
        cmd_evaluate(args)
    elif args.command == "freeze":
        cmd_freeze(args)
    elif args.command == "hypothesis-test":
        cmd_hypothesis_test(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
