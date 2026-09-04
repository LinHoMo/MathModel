#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""orchestrator.py —— 自动化编排器：一键跑完 29 步。

功能：
- 按 PIPELINE 顺序逐步推进
- 每步：读 SKILL.md -> 执行 Procedure -> 跑门禁 -> 通过则 advance，失败则按 Iteration 修正重试(最多 3 轮)
- 并行阶段 (Reviewer 5 人评审团) 自动并发
- 失败回退：block/refine 触发上游手回退并重跑
- 状态持久化：state.py 管理 progress

用法：
    python core/tools/orchestrator.py <项目> [--max-rounds N] [--resume] [--dry-run]
    python core/tools/orchestrator.py <项目> --v3 [--competition cumcm]   # V3 DAG 干跑
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "core" / "tools"))

import state as S


MAX_RETRY_PER_STEP = 3
DEFAULT_MAX_ROUNDS = 4


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run(cmd: list[str], cwd: Optional[Path] = None, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    """运行命令，返回 CompletedProcess。"""
    return subprocess.run(
        cmd,
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, **(env or {}), "PYTHONIOENCODING": "utf-8"},
    )


def _skill_path(hand: str, agent: str) -> Path:
    return ROOT / "core" / hand.capitalize() / "agents" / agent / "SKILL.md"


def _parse_skill(skill_path: Path) -> dict:
    """解析 SKILL.md，返回 Procedure/Contract/Iteration。"""
    if not skill_path.exists():
        return {}
    txt = skill_path.read_text(encoding="utf-8", errors="replace")
    sections = {}
    current = None
    for line in txt.splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current:
            sections[current].append(line)
    # 合并为字符串
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _run_gate(project: str, hand: str, agent: str, level: str = "artifact") -> tuple[int, str]:
    """跑门禁，返回 (exit_code, output)。"""
    cmd = [sys.executable, str(ROOT / "core" / "tools" / "gate.py"), project]
    if level == "artifact":
        cmd += ["--level", "artifact", hand, agent]
    elif level == "hand":
        cmd += ["--level", "hand", hand]
    elif level == "delivery":
        cmd += ["--level", "delivery", hand]
    elif level == "all":
        cmd += ["--level", "all"]
    r = _run(cmd)
    return r.returncode, r.stdout + r.stderr


def _advance_state(project: str, hand: str, agent: str, output: str) -> int:
    """调用 state.py advance，返回 exit_code。"""
    cmd = [
        sys.executable, str(ROOT / "core" / "tools" / "state.py"), project,
        "advance", hand, agent, "--output", output
    ]
    r = _run(cmd)
    return r.returncode


def _get_agent_output_artifact(hand: str, agent: str) -> str:
    """从 PIPELINE/ARTIFACT_PROBE 获取该 agent 的主产物路径。"""
    probe = S.ARTIFACT_PROBE.get((hand, agent))
    return probe or ""


def _is_parallel_band(hand: str, agent: str) -> bool:
    """判断是否为并行带 (Reviewer 5 评分员同 stage=1)。"""
    if hand != "reviewer":
        return False
    return agent.startswith("scorer-")


def _run_score_compute(project: str) -> int:
    """跑 score_compute.py 生成 5 张评分卡 + 聚合。"""
    cmd = [sys.executable, str(ROOT / "core" / "tools" / "score_compute.py"), project]
    r = _run(cmd)
    return r.returncode


def _run_score_artifact(project: str, round_no: int = 1) -> tuple[int, str]:
    """跑 score_artifact.py 判定 verdict，返回 (exit_code, verdict)。"""
    cmd = [sys.executable, str(ROOT / "core" / "tools" / "score_artifact.py"), project, "--round", str(round_no)]
    r = _run(cmd)
    verdict = "unknown"
    for line in (r.stdout + r.stderr).splitlines():
        if line.strip().startswith("verdict:") or "verdict:" in line:
            verdict = line.split("verdict:")[-1].strip()
            break
    return r.returncode, verdict


def _execute_step(project: str, hand: str, agent: str, dry_run: bool = False) -> tuple[bool, str]:
    """
    执行单步：读 SKILL -> 跑门禁 -> advance。
    返回 (success, verdict_or_error)。
    """
    skill_path = _skill_path(hand, agent)
    if not skill_path.exists():
        return False, f"SKILL.md 不存在: {skill_path}"

    skill = _parse_skill(skill_path)
    artifact = _get_agent_output_artifact(hand, agent)

    print(f"\n{'='*60}")
    print(f"执行步骤: {hand}/{agent} (stage {next(s for h,a,s in S.PIPELINE if (h,a)==(hand,agent))})")
    print(f"产物: {artifact}")
    print(f"{'='*60}")

    if dry_run:
        print(f"[DRY-RUN] 跳过实际执行")
        return True, "dry-run"

    # 特殊处理：Reviewer 阶段的特殊流程
    if hand == "reviewer" and agent == "scorer-academic":
        # 5 人评审团并行：统一跑 score_compute
        print("[并行阶段] 执行 5 人评审团评分...")
        rc = _run_score_compute(project)
        if rc != 0:
            return False, f"score_compute 失败 (exit={rc})"
        # 推进前 5 个 scorer 的状态
        for a in ["scorer-academic", "scorer-engineering", "scorer-judge", "scorer-reader", "scorer-adversarial"]:
            art = _get_agent_output_artifact("reviewer", a)
            _advance_state(project, "reviewer", a, art)
        return True, "scorers done"

    if hand == "reviewer" and agent == "weakness-hunter":
        # weakness-hunter：读 weakness_report.json (score_compute 已生成)
        art = _get_agent_output_artifact("reviewer", "weakness-hunter")
        _advance_state(project, "reviewer", "weakness-hunter", art)
        return True, "weakness-hunter done"

    if hand == "reviewer" and agent == "revision-planner":
        # revision-planner：读 revision_plan.json
        art = _get_agent_output_artifact("reviewer", "revision-planner")
        _advance_state(project, "reviewer", "revision-planner", art)
        return True, "revision-planner done"

    if hand == "reviewer" and agent == "revision-executor":
        # revision-executor：读 execution_report.json
        art = _get_agent_output_artifact("reviewer", "revision-executor")
        _advance_state(project, "reviewer", "revision-executor", art)
        return True, "revision-executor done"

    # 通用流程：跑 artifact 级门禁
    artifact = _get_agent_output_artifact(hand, agent)
    if not artifact:
        print(f"[WARN] {hand}/{agent} 无定义产物，跳过门禁")
    else:
        print(f"[门禁] {hand}/{agent} (artifact 级)...")
        rc, out = _run_gate(project, hand, agent, "artifact")
        if rc == 2:  # HARD
            print(f"[FAIL] 门禁硬失败:\n{out[-500:]}")
            return False, out
        elif rc == 3:  # ERROR
            print(f"[ERROR] 门禁异常:\n{out[-500:]}")
            return False, out
        elif rc == 1:  # SOFT
            print(f"[WARN] 门禁软失败(不阻塞):\n{out[-300:]}")

    # 推进状态
    art = _get_agent_output_artifact(hand, agent)
    rc = _advance_state(project, hand, agent, art)
    if rc != 0:
        return False, f"state advance 失败 (exit={rc})"

    # 某些 agent 后需要跑额外的门禁
    if agent in ("code-implementer", "test-runner", "result-verifier", "guardrails-checker", "hash-auditor"):
        print(f"[门禁] {hand} 级门禁...")
        rc, out = _run_gate(project, hand, None, "hand")
        if rc == 2:
            print(f"[FAIL] 手级门禁硬失败:\n{out[-500:]}")
            return False, out

    if hand == "writer" and agent == "final-validator":
        # Writer 完成后跑 delivery 门禁
        print("[门禁] writer delivery...")
        rc, out = _run_gate(project, "writer", None, "delivery")
        if rc == 2:
            print(f"[FAIL] writer delivery 硬失败:\n{out[-500:]}")
            return False, out

    if hand == "reviewer" and agent == "revision-executor":
        # 评审结束，跑 score_artifact 判定 verdict
        rc, verdict = _run_score_artifact(project)
        if rc == 2:  # block
            return False, f"block: {verdict}"
        elif rc == 1:  # refine/refine_partial
            return False, f"refine: {verdict}"

    return True, "ok"


def _retry_step(project: str, hand: str, agent: str, max_retry: int) -> tuple[bool, str]:
    """带重试的步骤执行。"""
    for attempt in range(1, max_retry + 1):
        print(f"\n--- 尝试 {attempt}/{max_retry}: {hand}/{agent} ---")
        ok, msg = _execute_step(project, hand, agent)
        if ok:
            return True, msg
        print(f"[RETRY] 尝试 {attempt} 失败: {msg}")
        if attempt < max_retry:
            time.sleep(2)
    return False, f"重试 {max_retry} 次均失败: {msg}"


def _run_pipeline(project: str, max_rounds: int, dry_run: bool = False) -> int:
    """跑完整流水线，支持多轮审查回退。"""
    print(f"\n{'#'*60}")
    print(f"开始自动化流水线: {project} (最大轮次: {max_rounds})")
    print(f"{'#'*60}")

    # 初始化状态
    st = S.load(project)
    if st is None:
        print("[STATE] 初始化...")
        rc = S.cmd_init(project, argparse.Namespace())
        if rc != 0:
            print("[ERROR] state init 失败")
            return 2
        st = S.load(project)

    round_no = 1
    while round_no <= max_rounds:
        print(f"\n{'#'*60}")
        print(f"第 {round_no}/{max_rounds} 轮评审循环")
        print(f"{'#'*60}")

        # 遍历 PIPELINE
        i = 0
        while i < len(S.PIPELINE):
            hand, agent, _ = S.PIPELINE[i]

            # 检查是否已完成
            st = S.load(project)
            done = {(c.get("hand"), c.get("agent")) for c in st.get("completed", [])}
            if (hand, agent) in done:
                print(f"[SKIP] {hand}/{agent} 已完成")
                i += 1
                continue

            # 并行带处理：Reviewer 5 评分员同 stage
            if _is_parallel_band(hand, agent):
                # 检查整个并行带是否都未完成
                band = [a for h,a,s in S.PIPELINE if h=="reviewer" and a.startswith("scorer-")]
                band_done = all((hand, a) in done for a in band)
                if band_done:
                    for a in band:
                        i += 1
                    continue

            ok, msg = _retry_step(project, hand, agent, MAX_RETRY_PER_STEP)
            if not ok:
                print(f"[BLOCK] {hand}/{agent} 失败: {msg}")

                # 判定回退策略
                if "block" in msg.lower() or "refine" in msg.lower():
                    # 需要回退到对应手的起始
                    target_hand = hand
                    if hand == "reviewer":
                        target_hand = "writer"  # 评审失败回退到 Writer
                    elif hand == "writer":
                        target_hand = "programmer"
                    elif hand == "programmer":
                        target_hand = "modeler"

                    # 找到目标手的第一个 agent
                    first_agent = next((a for h,a,s in S.PIPELINE if h == target_hand), None)
                    if first_agent:
                        print(f"[回退] 回退到 {target_hand}/{first_agent}")
                        S.cmd_reset(project, argparse.Namespace(to=f"{target_hand}/{first_agent}"))
                        # 重置 round_no 为 1 (重新开始)
                        round_no = 1
                        break  # 跳出内层循环，重新开始新一轮
                    else:
                        return 1
                return 1

            i += 1

        # 一轮流水线跑完，检查最终 verdict
        st = S.load(project)
        review = st.get("review", {})
        verdict = review.get("verdict", "")
        if verdict == "pass":
            print("\n[SUCCESS] 最终 verdict: pass - 流水线完成!")
            return 0
        elif verdict in ("pass_with_review", "refine_partial"):
            print(f"\n[PARTIAL] 最终 verdict: {verdict} - 可提交但建议改进")
            return 0
        elif verdict in ("refine", "block"):
            round_no += 1
            if round_no <= max_rounds:
                print(f"\n[ROUND] verdict={verdict}, 进入第 {round_no} 轮")
                continue
            else:
                print(f"\n[MAX ROUNDS] 达到最大轮次 {max_rounds}, 最后 verdict={verdict}")
                return 1
        else:
            print(f"\n[UNKNOWN] verdict={verdict}")
            return 1

    return 0


def _run_v3(project_dir: Path, dry_run: bool = True,
            competition: str | None = None) -> int:
    """V3 模式：组合 Workflow DAG → 角色校验 → 波次干跑。

    P3 交付 dry-run（P4 接 executor 后支持实际执行）。
    """
    sys.path.insert(0, str(ROOT / "core"))
    from runtime.execution.composer import ComposeError, WorkflowComposer
    from runtime.roles import RoleError, load_roles, validate_dag_roles

    composer = WorkflowComposer(ROOT / "core" / "workflows")

    # Question 列表：优先 V3 registry，其次 V2 状态反推，最后演示用 Q001
    questions: list[str] = []
    reg_path = project_dir / "state" / "registry.json"
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
            questions = sorted(
                aid for aid, a in reg.get("artifacts", {}).items()
                if str(aid).startswith("Q"))
        except (json.JSONDecodeError, OSError):
            pass
    if not questions:
        v2_state = project_dir / "work" / "state.json"
        if v2_state.exists():
            try:
                st = json.loads(v2_state.read_text(encoding="utf-8"))
                questions = sorted(st.get("q_states", {}).keys()) or []
            except (json.JSONDecodeError, OSError):
                pass
    if not questions:
        questions = ["Q001"]

    print(f"[V3] 项目: {project_dir.name}  questions: {questions}")
    try:
        dag = composer.compose_executable(questions, competition)
        roles = load_roles(ROOT / "core" / "roles")
    except (ComposeError, RoleError) as exc:
        print(f"[V3][FAIL] {'; '.join(str(x) for x in exc.args)}", file=sys.stderr)
        return 2

    role_problems = validate_dag_roles(dag, roles)
    if role_problems:
        print(f"[V3][FAIL] 角色校验未通过:", file=sys.stderr)
        for p in role_problems:
            print(f"  - {p}", file=sys.stderr)
        return 2

    print(f"[V3] DAG: {dag.name}  节点 {len(dag.nodes)} 个  "
          f"(角色: {', '.join(sorted(roles))})")

    if not dry_run:
        print("[V3][ERROR] V3 实际执行在 P4 接入 executor；当前请使用 --dry-run",
              file=sys.stderr)
        return 2

    # ---- 波次干跑：迭代 ready 集合（同 wave 内可并行）
    completed: set[str] = set()
    wave = 0
    while True:
        ready = dag.ready_nodes(completed)
        if not ready:
            break
        wave += 1
        print(f"\n-- Wave {wave} ({len(ready)} 节点, 可并行) --")
        for nid in ready:
            n = dag.nodes[nid]
            bits = [f"type={n.type}"]
            if n.role:
                bits.append(f"role={n.role}")
            if n.validator:
                bits.append(f"validator={n.validator}")
            if n.per_question:
                bits.append("per_question")
            if n.on_fail:
                bits.append(f"on_fail→{n.on_fail}")
            print(f"  {nid:32s} {'  '.join(bits)}")
        completed |= set(ready)
    print(f"\n[V3][DRY-RUN] 共 {wave} 波 / {len(dag.nodes)} 节点，计划合法")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="自动化编排器：默认 V3 DAG 模式，--legacy 走 29 步流水线")
    ap.add_argument("project", help="项目路径或名称")
    ap.add_argument("--max-rounds", type=int, default=DEFAULT_MAX_ROUNDS, help="最大评审轮次（legacy 模式）")
    ap.add_argument("--resume", action="store_true", help="从当前状态继续（legacy 模式）")
    ap.add_argument("--dry-run", action="store_true", help="仅打印计划不执行")
    ap.add_argument("--legacy", action="store_true",
                    help="V2 legacy 模式：29 步线性流水线（state/gate 驱动）")
    ap.add_argument("--v3", action="store_true",
                    help="V3 DAG 模式（P5 起为默认，此 flag 仅为兼容保留）")
    ap.add_argument("--competition", default=None,
                    help="V3 模式赛事 profile（cumcm/mcm...，缺省用 base）")
    args = ap.parse_args()

    project = args.project
    base = Path(project)
    if not base.is_absolute():
        # 先尝试作为项目名在 projects/ 下
        base = ROOT / "projects" / project
        if not base.exists():
            # 再尝试作为相对路径
            base = ROOT / project
    if not base.exists():
        print(f"[ERROR] 项目不存在: {base}", file=sys.stderr)
        return 2

    if args.legacy:
        # V2 legacy：29 步线性流水线（P5 前的默认行为，保留一个版本周期）
        return _run_pipeline(str(base), args.max_rounds, args.dry_run)

    # P5 起默认 V3 DAG 模式（组合 Workflow DAG + 角色校验 + 波次干跑）
    return _run_v3(base, dry_run=True, competition=args.competition)


if __name__ == "__main__":
    sys.exit(main())