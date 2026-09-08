#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_p13_3d.py — P13-3D Model → Paper Conversion 实验执行器。

三臂（B0/MMA/B1）× 三题（2024_A/2021_C/2022_B）= 9 份论文
→ Fidelity Gate（双向变异检测）
→ Paper Quality 盲评

用法:
  python run_p13_3d.py --project P13-3D --phase generate
  python run_p13_3d.py --project P13-3D --phase fidelity
  python run_p13_3d.py --project P13-3D --phase evaluate
  python run_p13_3d.py --project P13-3D --phase aggregate
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Project root (file is at core/tools/evaluation/)
ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]
sys.path.insert(0, str(ROOT / "core" / "tools"))

# --- Constants ---
ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = [
    {"id": "2024_A", "name": "七鳃鳗性别比", "regime": "mechanism"},
    {"id": "2021_C", "name": "亚洲大黄蜂", "regime": "data"},
    {"id": "2022_B", "name": "两库水资源", "regime": "optimization"},
]

# Arm mapping (anonymized for blind evaluation)
ARM_MAP = {"X": "B0", "Y": "MMA", "Z": "B1-F"}


def _project_dir(project: str) -> Path:
    return ROOT / "research" / project


def _output_dir(project: str) -> Path:
    return _project_dir(project) / "output"


def phase_generate(project: str):
    """Phase 1: Generate papers from frozen artifacts.

    For each (question, arm):
    1. Load frozen MODEL_ARTIFACT
    2. Run Writer (same prompt, same LLM, different artifact)
    3. Save paper as .md
    """
    out = _output_dir(project)
    artifacts_dir = out / "artifacts"
    papers_dir = out / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)

    # Check if artifacts exist
    existing = list(artifacts_dir.glob("*.json"))
    if not existing:
        print("No artifacts found in output/artifacts/.")
        print("Expected files: {question_id}_{arm}.json for each (question, arm) pair.")
        print("Example: 2024_A_B0.json, 2024_A_MMA.json, 2024_A_B1-F.json")
        print("\nPlease place frozen MODEL_ARTIFACT files in output/artifacts/ first.")
        return

    # Load writer prompt
    writer_prompt_path = ROOT / "core" / "Modeler" / "knowledge" / "writer_prompt_p13_3d.md"
    if not writer_prompt_path.exists():
        print(f"Writer prompt not found: {writer_prompt_path}")
        print("Creating default writer prompt...")
        _create_writer_prompt(writer_prompt_path)

    writer_prompt = writer_prompt_path.read_text(encoding="utf-8")

    print(f"Found {len(existing)} artifacts. Generating papers...")
    print(f"Writer prompt: {writer_prompt_path}")

    for q in QUESTIONS:
        for arm in ARMS:
            artifact_file = artifacts_dir / f"{q['id']}_{arm}.json"
            paper_file = papers_dir / f"{q['id']}_{arm}.md"

            if not artifact_file.exists():
                print(f"  [SKIP] {artifact_file.name} not found")
                continue

            if paper_file.exists():
                print(f"  [SKIP] {paper_file.name} already exists")
                continue

            print(f"  [GEN] {q['id']} × {arm}...", end=" ")

            # Load artifact
            artifact = json.loads(artifact_file.read_text(encoding="utf-8"))

            # Construct writer input
            writer_input = _construct_writer_input(q, artifact, writer_prompt)

            # Save writer input for manual/AI execution
            input_file = papers_dir / f"{q['id']}_{arm}_writer_input.md"
            input_file.write_text(writer_input, encoding="utf-8")

            print(f"writer input saved → {input_file.name}")

    print(f"\nWriter inputs generated in {papers_dir}/")
    print("Next: Run Writer on each *_writer_input.md to produce papers.")


def _construct_writer_input(question: dict, artifact: dict, writer_prompt: str) -> str:
    """Construct the input for the Writer."""
    # Anonymize artifact (remove any arm-identifying info)
    anon_artifact = json.loads(json.dumps(artifact))
    for key in ["arm", "agent", "model_name", "prompt_version"]:
        anon_artifact.pop(key, None)

    return f"""{writer_prompt}

---

## 题目原文

{question['name']}（{question['id']}，{question['regime']} 类）

## 匿名建模产物（MODEL_ARTIFACT）

```json
{json.dumps(anon_artifact, ensure_ascii=False, indent=2)}
```

---

请根据上述建模产物，撰写完整的数学建模论文。
"""


def _create_writer_prompt(path: Path):
    """Create the default Writer prompt for P13-3D."""
    prompt = """# P13-3D Writer Prompt（自然撰写指令）

你是一个数学建模论文撰写者。请根据提供的建模产物（MODEL_ARTIFACT），撰写完整的数学建模论文。

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

## 重要提醒

- 严格基于提供的建模产物撰写，不要自行添加产物中没有的变量、约束或假设。
- 如果产物中缺少某个子问题的模型，如实说明"该子问题的模型待补充"。
- 保持学术论文的客观、严谨风格。
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prompt, encoding="utf-8")
    print(f"Default writer prompt created: {path}")


def phase_fidelity(project: str):
    """Phase 2: Run Fidelity Gate on all generated papers.

    For each (question, arm):
    1. Load artifact
    2. Load paper
    3. Run fidelity_gate.py
    4. Save audit log
    """
    from evaluation.fidelity_gate import compute_fidelity

    out = _output_dir(project)
    artifacts_dir = out / "artifacts"
    papers_dir = out / "papers"
    fidelity_dir = out / "fidelity"
    fidelity_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for q in QUESTIONS:
        for arm in ARMS:
            artifact_file = artifacts_dir / f"{q['id']}_{arm}.json"
            paper_file = papers_dir / f"{q['id']}_{arm}.md"
            audit_file = fidelity_dir / f"{q['id']}_{arm}_fidelity.json"

            if not artifact_file.exists():
                print(f"  [SKIP] {q['id']} × {arm}: artifact not found")
                continue
            if not paper_file.exists():
                print(f"  [SKIP] {q['id']} × {arm}: paper not found")
                continue

            print(f"  [CHECK] {q['id']} × {arm}...", end=" ")

            artifact = json.loads(artifact_file.read_text(encoding="utf-8"))
            paper = paper_file.read_text(encoding="utf-8")

            result = compute_fidelity(artifact, paper)
            result["problem_id"] = q["id"]
            result["arm"] = arm
            result["regime"] = q["regime"]

            # Save audit log
            audit_file.write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            results.append(result)
            print(f"Fidelity: {result['fidelity_score']:.1%} — {result['summary']}")

    # Save summary
    summary_file = fidelity_dir / "fidelity_summary.json"
    summary_file.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Print summary table
    if results:
        print("\n" + "=" * 60)
        print("FIDELITY GATE SUMMARY")
        print("=" * 60)
        print(f"{'Question':<12} {'Arm':<8} {'Fidelity':>10} {'Critical':>10} {'Major':>8} {'Minor':>8}")
        print("-" * 60)
        for r in results:
            mc = r["mutation_count"]
            print(f"{r['problem_id']:<12} {r['arm']:<8} {r['fidelity_score']:>9.1%} "
                  f"{mc['critical']:>10} {mc['major']:>8} {mc['minor']:>8}")


def phase_evaluate(project: str):
    """Phase 3: Set up blind evaluation for Paper Quality.

    Generates evaluation prompts for each question.
    """
    out = _output_dir(project)
    papers_dir = out / "papers"
    eval_dir = out / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)

    for q in QUESTIONS:
        eval_file = eval_dir / f"{q['id']}_eval_prompt.md"

        # Collect papers for this question
        paper_files = []
        for arm in ARMS:
            pf = papers_dir / f"{q['id']}_{arm}.md"
            if pf.exists():
                paper_files.append((arm, pf))

        if len(paper_files) < 3:
            print(f"  [SKIP] {q['id']}: only {len(paper_files)}/3 papers available")
            continue

        # Build evaluation prompt
        prompt_parts = [
            f"# Paper Quality Evaluation — {q['id']} ({q['name']})\n",
            "你是一个数学建模论文评委。请对以下三份论文进行盲评。",
            "论文已匿名化（标记为 X/Y/Z），请勿猜测作者身份。\n",
            "## 评分维度\n",
            "1. **Mathematical correctness**（0-100）：公式/推导/量纲正确性",
            "2. **Problem alignment**（0-100）：论文是否回答了题目要求",
            "3. **Completeness**（0-100）：模型组件覆盖度",
            "4. **Communication**（0-100）：表达清晰度、结构合理性\n",
            "## 输出格式\n",
            "```json",
            '{',
            '  "papers": [',
            '    {"id": "X", "scores": {"math_correctness": N, "problem_alignment": N, "completeness": N, "communication": N}, "comments": "..."},',
            '    {"id": "Y", "scores": {...}, "comments": "..."},',
            '    {"id": "Z", "scores": {...}, "comments": "..."}',
            '  ]',
            '}',
            "```\n",
            "---\n",
        ]

        # Add papers (anonymized order)
        import random
        random.seed(42)
        shuffled = list(paper_files)
        random.shuffle(shuffled)

        for i, (arm, pf) in enumerate(shuffled):
            anon_label = chr(ord("X") + i)
            content = pf.read_text(encoding="utf-8")
            prompt_parts.append(f"## 论文 {anon_label}\n")
            prompt_parts.append(content)
            prompt_parts.append("")

        # Save prompt
        eval_file.write_text("\n".join(prompt_parts), encoding="utf-8")
        print(f"  [EVAL] {q['id']}: evaluation prompt → {eval_file.name}")

    print(f"\nEvaluation prompts generated in {eval_dir}/")
    print("Next: Run blind evaluation on each *_eval_prompt.md.")


def phase_aggregate(project: str):
    """Phase 4: Aggregate results from fidelity + paper quality evaluation.

    Produces final P13-3D results table.
    """
    out = _output_dir(project)
    fidelity_dir = out / "fidelity"
    eval_dir = out / "evaluation"

    # Load fidelity results
    fidelity_file = fidelity_dir / "fidelity_summary.json"
    if fidelity_file.exists():
        fidelity_results = json.loads(fidelity_file.read_text(encoding="utf-8"))
    else:
        fidelity_results = []
        print("No fidelity results found.")

    # Load paper quality results
    pq_results = []
    for q in QUESTIONS:
        pq_file = eval_dir / f"{q['id']}_paper_quality.json"
        if pq_file.exists():
            pq = json.loads(pq_file.read_text(encoding="utf-8"))
            pq["problem_id"] = q["id"]
            pq_results.append(pq)

    # Build aggregate table
    print("\n" + "=" * 70)
    print("P13-3D AGGREGATE RESULTS — Model → Paper Conversion")
    print("=" * 70)

    if fidelity_results:
        print("\n--- Fidelity Scores ---")
        print(f"{'Question':<12} {'Arm':<8} {'Fidelity':>10} {'Mutations':>12}")
        print("-" * 45)
        for r in fidelity_results:
            mc = r["mutation_count"]
            print(f"{r['problem_id']:<12} {r['arm']:<8} {r['fidelity_score']:>9.1%} "
                  f"{mc['total']:>12}")

        # Arm means
        print("\n--- Arm Means (Fidelity) ---")
        for arm in ARMS:
            arm_scores = [r["fidelity_score"] for r in fidelity_results if r["arm"] == arm]
            if arm_scores:
                mean_score = sum(arm_scores) / len(arm_scores)
                print(f"  {arm}: {mean_score:.1%} (n={len(arm_scores)})")

    if pq_results:
        print("\n--- Paper Quality ---")
        print("(Requires manual evaluation results in *_paper_quality.json)")

    # Save aggregate
    aggregate = {
        "experiment": "P13-3D",
        "phase": "aggregate",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fidelity_summary": fidelity_results,
        "paper_quality_summary": pq_results,
    }
    aggregate_file = out / "evaluation" / "p13_3d_aggregate.json"
    aggregate_file.write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nAggregate saved to {aggregate_file}")


def main():
    parser = argparse.ArgumentParser(description="P13-3D Experiment Executor")
    parser.add_argument("--project", default="P13-3D", help="Project name")
    parser.add_argument("--phase", required=True,
                        choices=["generate", "fidelity", "evaluate", "aggregate"],
                        help="Experiment phase to run")
    args = parser.parse_args()

    phases = {
        "generate": phase_generate,
        "fidelity": phase_fidelity,
        "evaluate": phase_evaluate,
        "aggregate": phase_aggregate,
    }

    print(f"P13-3D — Phase: {args.phase}")
    print(f"Project: {args.project}")
    print("=" * 50)

    phases[args.phase](args.project)


if __name__ == "__main__":
    main()
