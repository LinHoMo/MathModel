#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""执行状态管理 —— 跨 runtime 执行协议的状态层。

设计要点
--------
* **单一事实源**：`projects/<项目>/work/state.json`（脚本读写，可靠）
* **可读镜像**：`projects/<项目>/work/STATE.md`（agent 读，直观），由脚本自动渲染
* **零依赖**：只用标准库，任何 Python 3 都能跑
* **不依赖 cwd**：路径基于本文件位置推导仓库根

为什么要外置状态
----------------
流程原本依赖模型的对话记忆：19 个 agent、平均 159 行 SKILL.md，
全量注入必爆上下文，模型只能"挑看起来重要的做"。
把进度写进文件后，agent 每次只需读 STATE.md 就知道下一步——
**让文件系统记住流程，而不是让模型记住流程**。

用法
----
    python core/tools/state.py <project> init
    python core/tools/state.py <project> status
    python core/tools/state.py <project> advance <hand> <agent> [--output <path>]
    python core/tools/state.py <project> fail <hand> <agent> --reason "..."
    python core/tools/state.py <project> reset [--to hand/agent]
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# 执行顺序：与 catalog.yaml 的 hands.stage_order / agents.stage 一致
PIPELINE = [
    ("modeler", "problem-parser", 1),
    ("modeler", "type-classifier", 2),
    ("modeler", "literature-searcher", 1.5),
    ("modeler", "method-matcher", 3),
    ("modeler", "model-builder", 4),
    ("modeler", "dag-builder", 4.5),
    ("modeler", "assumption-validator", 5),
    ("modeler", "spec-auditor", 6),
    ("programmer", "template-selector", 1),
    ("programmer", "code-implementer", 2),
    ("programmer", "test-runner", 3),
    ("programmer", "result-verifier", 4),
    ("programmer", "guardrails-checker", 5),
    ("programmer", "hash-auditor", 6),
    ("writer", "structure-planner", 1),
    ("writer", "section-writer", 2),
    ("writer", "figure-generator", 3),
    ("writer", "reference-curator", 4),
    ("writer", "consistency-checker", 5),
    ("writer", "guardrails-checker", 6),
    ("writer", "final-validator", 7),
    # P2 新增的评审手：5 人评审团 (stage 1 并行) + weakness-hunter + revision-planner + revision-executor
    ("reviewer", "scorer-academic", 1),
    ("reviewer", "scorer-engineering", 1),
    ("reviewer", "scorer-judge", 1),
    ("reviewer", "scorer-reader", 1),
    ("reviewer", "scorer-adversarial", 1),
    ("reviewer", "weakness-hunter", 2),
    ("reviewer", "revision-planner", 3),
    ("reviewer", "revision-executor", 4),
]

# 本项目历史上并存过四套状态文件，各记各的。统一由 state.json 接管，
# 旧文件保留但不再作为事实源（legacy 字段记录其哈希以便追溯）。
LEGACY_STATE_FILES = [
    ("output", "checkpoint.json"),
    ("work", "audit_log.json"),
    ("work", "audit_chain.json"),
    ("work", "final_audit_log.json"),
]

STATE_VERSION = "1.0"


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path):
    try:
        return "sha256:" + hashlib.sha256(
            Path(path).read_bytes()
        ).hexdigest()
    except Exception:
        return ""


def project_dir(project):
    p = Path(project)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        # 允许直接传项目名
        p = ROOT / "projects" / project
    return p


def state_path(project):
    return project_dir(project) / "work" / "state.json"


def md_path(project):
    return project_dir(project) / "work" / "STATE.md"


def _empty_state(project):
    return {
        "version": STATE_VERSION,
        "project": Path(project_dir(project)).name,
        "created": _now(),
        "updated": _now(),
        "current": {"hand": "modeler", "agent": "problem-parser", "stage": 1},
        "completed": [],
        "failed": [],
        "q_states": {},                 # P2-4 按子问局部回修预留
        "ai_usage_ledger": {},          # P2-1 AI 使用披露预留
        "legacy": {},
        "decision_log_path": "work/decision_log.json",
    }


def _collect_legacy(project):
    """读取历史四套状态文件的哈希，归档到 legacy 字段（不删除原文件）。"""
    base = project_dir(project)
    legacy = {}
    for sub, name in LEGACY_STATE_FILES:
        f = base / sub / name
        if f.exists():
            legacy[f"{sub}/{name}"] = _sha256_file(f)
    return legacy


def load(project):
    p = state_path(project)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[state] 读取失败 {p}: {e}", file=sys.stderr)
        return None


def save(project, state):
    p = state_path(project)
    p.parent.mkdir(parents=True, exist_ok=True)
    # current 永远由 completed 推导，杜绝 pipeline 扩容 / 手工改动后的过期 current。
    state["current"] = _first_incomplete(state.get("completed", []))
    state["updated"] = _now()
    p.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    render_md(project, state)
    return p


def render_md(project, state):
    """渲染给人/agent 读的 STATE.md。"""
    cur = _first_incomplete(state.get("completed", [])) or {}
    completed = state.get("completed", [])
    total = len(PIPELINE)
    done = len(completed)

    lines = [
        "# 执行状态（由 core/tools/state.py 自动维护，请勿手改）",
        "",
        f"- 项目：`{state.get('project')}`",
        f"- 进度：**{done}/{total}**（{done * 100 // total}%）",
        f"- 更新时间：{state.get('updated')}",
        "",
        "## 下一步",
        "",
    ]

    if done >= total:
        lines.append(f"全部 {total} 步已完成。运行 `python core/tools/gate.py <project> all` 做全链路终检。")
    else:
        lines.append(f"- **手**：`{cur.get('hand')}`")
        lines.append(f"- **Agent**：`{cur.get('agent')}`（stage {cur.get('stage')}）")
        lines.append(
            f"- **读**：`{cur.get('hand', '').capitalize()}/agents/{cur.get('agent')}/SKILL.md`"
        )
        lines.append(
            f"- **门禁**：`python core/tools/gate.py {state.get('project')} "
            f"{cur.get('hand')} {cur.get('agent')}`"
        )

    lines += ["", "## 已完成", ""]
    if not completed:
        lines.append("（无）")
    else:
        lines.append("| # | hand | agent | stage | 输出 | 时间 |")
        lines.append("|---|---|---|---|---|---|")
        for i, c in enumerate(completed, 1):
            out = c.get("output") or "—"
            lines.append(
                f"| {i} | {c.get('hand')} | {c.get('agent')} | {c.get('stage')} "
                f"| `{out}` | {c.get('timestamp', '')[:19]} |"
            )

    if state.get("failed"):
        lines += ["", "## 失败记录", ""]
        for f in state["failed"][-10:]:
            lines.append(
                f"- `{f.get('hand')}/{f.get('agent')}` — {f.get('reason', '')} "
                f"（{f.get('timestamp', '')[:19]}）"
            )

    lines += [
        "",
        "---",
        "",
        "本文件由脚本生成。执行协议见仓库根 `AGENTS.md`。",
    ]

    mp = md_path(project)
    mp.parent.mkdir(parents=True, exist_ok=True)
    mp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return mp


# 各 agent 的主产物，用于从文件系统反推进度（中断恢复 / 历史项目接管）
ARTIFACT_PROBE = {
    ("modeler", "problem-parser"): "work/question_spec.json",
    ("modeler", "type-classifier"): "work/type_classification.json",
    ("modeler", "literature-searcher"): "work/literature_evidence.json",
    ("modeler", "method-matcher"): "work/method_candidates.json",
    ("modeler", "model-builder"): "work/model_draft.md",
    ("modeler", "dag-builder"): "work/model_dag.json",
    ("modeler", "assumption-validator"): "work/assumption_validation.json",
    ("modeler", "spec-auditor"): "output/MODEL_SPEC.md",
    ("programmer", "template-selector"): "work/template_plan.json",
    ("programmer", "code-implementer"): "code/main.py",
    ("programmer", "test-runner"): "work/test_report.json",
    ("programmer", "result-verifier"): "work/result_validation.json",
    ("programmer", "guardrails-checker"): "work/guardrails_report_programmer.json",
    ("programmer", "hash-auditor"): "output/CODE_DELIVERABLES.md",
    ("writer", "structure-planner"): "work/paper_structure.json",
    ("writer", "section-writer"): "paper/main.tex",
    ("writer", "figure-generator"): "paper/figures",
    ("writer", "reference-curator"): "paper/references.bib",
    ("writer", "consistency-checker"): "work/consistency_report.json",
    ("writer", "guardrails-checker"): "work/guardrails_report_writer.json",
    ("writer", "final-validator"): "output/PAPER_SPEC.md",
    ("reviewer", "scorer-academic"): "work/score_card_academic.json",
    ("reviewer", "scorer-engineering"): "work/score_card_engineering.json",
    ("reviewer", "scorer-judge"): "work/score_card_judge.json",
    ("reviewer", "scorer-reader"): "work/score_card_reader.json",
    ("reviewer", "scorer-adversarial"): "work/score_card_adversarial.json",
    ("reviewer", "weakness-hunter"): "work/weakness_report.json",
    ("reviewer", "revision-planner"): "work/revision_plan.json",
    ("reviewer", "revision-executor"): "work/execution_report.json",
}


def _pipeline_index(hand, agent):
    """返回 (hand, agent) 在 PIPELINE 中的下标；未知返回 None。"""
    for i, (h, a, _) in enumerate(PIPELINE):
        if (h, a) == (hand, agent):
            return i
    return None


def _artifact_exists(f):
    """产物是否真实存在：目录需非空，避免空目录被误判为已完成。"""
    try:
        if f.is_dir():
            return any(f.iterdir())
        return f.exists()
    except OSError:
        return False


def _sort_key(c):
    """completed 排序键：按 pipeline 顺序，未知项排到末尾（不抛 StopIteration）。"""
    i = _pipeline_index(c.get("hand"), c.get("agent"))
    return (i if i is not None else len(PIPELINE), c.get("timestamp", ""))


def _first_incomplete(completed):
    """返回第一条未完成的 PIPELINE 步骤（按顺序），全部完成返回 None。

    与 `len(completed)` 定位不同：本函数按 (hand, agent) 匹配，
    正确处理中途存在缺口的场景（例如缺 literature-searcher 但 method-matcher 已完成）。
    """
    done = {(c.get("hand"), c.get("agent")) for c in completed}
    for hand, agent, stage in PIPELINE:
        if (hand, agent) not in done:
            return {"hand": hand, "agent": agent, "stage": stage}
    return None


def sync_from_artifacts(project, state):
    """按产物存在性反推已完成步骤。

    中断恢复、换 session、换模型、接管历史项目时，
    不需要任何对话记忆——文件系统本身就是进度。
    """
    base = project_dir(project)
    completed = []
    for hand, agent, stage in PIPELINE:
        rel = ARTIFACT_PROBE.get((hand, agent))
        if not rel:
            continue
        f = base / rel
        if _artifact_exists(f):
            completed.append({
                "hand": hand,
                "agent": agent,
                "stage": stage,
                "timestamp": "",
                "output": rel,
                "output_hash": _sha256_file(f),
                "source": "artifact-scan",
            })
    state["completed"] = completed
    state["current"] = _first_incomplete(completed)
    return state


def cmd_init(project, args):
    p = project_dir(project)
    if not p.exists():
        print(f"[state] 项目目录不存在: {p}", file=sys.stderr)
        return 1
    st = _empty_state(project)
    st["legacy"] = _collect_legacy(project)
    sync_from_artifacts(project, st)
    save(project, st)
    done = len(st["completed"])
    print(f"[state] 已初始化 {state_path(project)}")
    print(f"[state] 从产物反推进度: {done}/{len(PIPELINE)} 步已完成")
    if st["legacy"]:
        print(f"[state] 已归档 {len(st['legacy'])} 个历史状态文件的哈希（保留原文件）")
    if st["current"]:
        c = st["current"]
        print(f"[state] 下一步: {c['hand']}/{c['agent']}")
    return 0


def cmd_sync(project, args):
    st = load(project)
    if st is None:
        return cmd_init(project, args)
    sync_from_artifacts(project, st)
    save(project, st)
    print(f"[state] 已从产物同步进度: {len(st['completed'])}/{len(PIPELINE)}")
    return 0


def cmd_status(project, args):
    st = load(project)
    if st is None:
        print(f"[state] 无状态文件，先运行: python core/tools/state.py {project} init")
        return 1
    # 自愈：current 与 completed 不一致时按缺口重新定位并落盘，
    # 避免 pipeline 扩容 / 手工改动后 current 停留在过期的 null 或错误步。
    computed = _first_incomplete(st.get("completed", []))
    if st.get("current") != computed:
        st["current"] = computed
        save(project, st)
    cur = computed or {}
    done = len(st.get("completed", []))
    print(f"项目: {st.get('project')}   进度: {done}/{len(PIPELINE)}")
    if done < len(PIPELINE):
        print(f"下一步: {cur.get('hand')}/{cur.get('agent')} (stage {cur.get('stage')})")
        print(f"  读:   {str(cur.get('hand','')).capitalize()}/agents/{cur.get('agent')}/SKILL.md")
        print(f"  门禁: python core/tools/gate.py {st.get('project')} {cur.get('hand')} {cur.get('agent')}")
    else:
        print("全部完成")
    print(f"状态文件: {state_path(project)}")
    print(f"可读镜像: {md_path(project)}")
    return 0


def cmd_advance(project, args):
    st = load(project)
    if st is None:
        print("[state] 无状态文件，先 init", file=sys.stderr)
        return 1

    key = (args.hand, args.agent)
    idx = _pipeline_index(*key)
    if idx is None:
        print(f"[state] 未知的 hand/agent: {key}", file=sys.stderr)
        return 1

    # 乱序跳步防护：只允许推进「当前缺口」或与当前缺口同 stage 的并行兄弟。
    # 否则会跳过串行前置步骤（例如缺 type-classifier 却直接 advance method-matcher）。
    cur = _first_incomplete(st.get("completed", []))
    if cur is not None:
        cur_idx = _pipeline_index(cur["hand"], cur["agent"])
        already_done = any(
            (c.get("hand"), c.get("agent")) == key
            for c in st.get("completed", [])
        )
        if (cur_idx is not None and idx > cur_idx
                and not already_done
                and PIPELINE[idx][2] != PIPELINE[cur_idx][2]):
            print(
                f"[state] 拒绝乱序推进 {args.hand}/{args.agent}："
                f"当前应为 {cur['hand']}/{cur['agent']}（stage {PIPELINE[cur_idx][2]}），"
                f"请先完成前置步骤。",
                file=sys.stderr,
            )
            return 1

    # ---- 门禁耦合：先判定，再写入 completed ----
    # 任何 HARD 或 ERROR 都禁止推进，避免"台账绿了但产物不达标"。
    gate_summary = {}
    gate_rc = 0
    if not getattr(args, "no_gate", False):
        gate_rc, gate_summary = _run_advance_gate(project, args.hand, args.agent)
        if gate_rc in (2, 3):  # EXIT_HARD / EXIT_ERROR：fail-closed
            if gate_rc == 2:
                print(
                    f"[state] 拒绝推进 {args.hand}/{args.agent}：门禁存在 "
                    f"{gate_summary.get('hard_fail_count', 0)} 项硬失败",
                    file=sys.stderr,
                )
                for hf in gate_summary.get("hard_fail", []):
                    print(f"          - {hf.get('name')}: {hf.get('detail')}",
                          file=sys.stderr)
            else:
                print(
                    f"[state] 拒绝推进 {args.hand}/{args.agent}：门禁执行异常，"
                    "无法证明产物通过",
                    file=sys.stderr,
                )
            print("[state] 请修正门禁问题后重跑 gate.py，再 advance。",
                  file=sys.stderr)
            return gate_rc
        if gate_rc == 1:  # EXIT_SOFT：允许推进，但保留审计信息
            print(f"[state] 提示：{args.hand}/{args.agent} 门禁有 "
                  f"{gate_summary.get('soft_fail_count', 0)} 项软失败（不阻塞推进）")

    out_hash = _sha256_file(args.output) if args.output else ""
    rec = {
        "hand": args.hand,
        "agent": args.agent,
        "stage": PIPELINE[idx][2],
        "timestamp": _now(),
        "output": args.output or "",
        "output_hash": out_hash,
    }
    if not getattr(args, "no_gate", False):
        rec["gate"] = {
            "exit_code": gate_rc,
            "hard_fail_count": gate_summary.get("hard_fail_count", 0),
            "soft_fail_count": gate_summary.get("soft_fail_count", 0),
            "hard_fail": gate_summary.get("hard_fail", []),
            "soft_fail": gate_summary.get("soft_fail", []),
        }

    # 避免重复登记
    st["completed"] = [
        c for c in st.get("completed", [])
        if (c.get("hand"), c.get("agent")) != key
    ]
    st["completed"].append(rec)
    st["completed"].sort(key=_sort_key)

    save(project, st)
    print(f"[state] 已登记 {args.hand}/{args.agent}")
    return 0


def _run_advance_gate(project, hand, agent):
    """运行 gate.py（JSON 模式）供 advance 判定。返回 (exit_code, summary_dict)。

    exit_code 语义：0=全过 1=仅软失败 2=硬失败(阻塞) 3=脚本异常(阻塞)。
    把 gate.py 当作黑盒调用，state.py 不重复实现任何判定逻辑。
    """
    gate_script = ROOT / "core" / "tools" / "gate.py"
    if not gate_script.exists():
        return 3, {}
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    try:
        r = subprocess.run(
            [sys.executable or "python", str(gate_script),
             project, hand, agent, "--json"],
            cwd=str(ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", env=env, timeout=360)
    except subprocess.TimeoutExpired:
        return 3, {}
    summary = {"hard_fail_count": 0, "soft_fail_count": 0, "hard_fail": [], "soft_fail": []}
    # gate.py --json 输出的是带缩进的多行 JSON；取首个 '{' 到末个 '}' 之间的整段解析
    raw = (r.stdout or "").strip()
    s, e = raw.find("{"), raw.rfind("}")
    if s >= 0 and e > s:
        try:
            summary = json.loads(raw[s:e + 1])
        except Exception:
            pass
    return r.returncode, summary


def cmd_fail(project, args):
    st = load(project)
    if st is None:
        print("[state] 无状态文件，先 init", file=sys.stderr)
        return 1
    st.setdefault("failed", []).append({
        "hand": args.hand,
        "agent": args.agent,
        "timestamp": _now(),
        "reason": args.reason or "",
    })
    save(project, st)
    print(f"[state] 已记录失败 {args.hand}/{args.agent}")
    return 0


def cmd_reset(project, args):
    st = load(project)
    if st is None:
        print("[state] 无状态文件，先 init", file=sys.stderr)
        return 1
    if args.to:
        hand, agent = args.to.split("/", 1)
        idx = next((i for i, (h, a, _) in enumerate(PIPELINE) if (h, a) == (hand, agent)), None)
        if idx is None:
            print(f"[state] 未知位置: {args.to}", file=sys.stderr)
            return 1
        keep = {(h, a) for h, a, _ in PIPELINE[:idx]}
        st["completed"] = [
            c for c in st.get("completed", [])
            if (c.get("hand"), c.get("agent")) in keep
        ]
        st["current"] = {"hand": hand, "agent": agent, "stage": PIPELINE[idx][2]}
        save(project, st)
        print(f"[state] 已回退到 {args.to}")
    else:
        fresh = _empty_state(project)
        fresh["legacy"] = _collect_legacy(project)
        save(project, fresh)
        print("[state] 已重置")
    return 0


def _qset(project, qid, patch):
    st = load(project)
    if st is None:
        print("[state] 无状态文件，先 init", file=sys.stderr)
        return None
    qs = st.setdefault("q_states", {})
    cur = qs.get(qid, {"status": "pending", "history": []})
    cur.update(patch)
    cur["updated"] = _now()
    cur.setdefault("history", []).append({
        "at": _now(),
        "status": cur.get("status"),
        "reason": patch.get("reason", ""),
    })
    qs[qid] = cur
    save(project, st)
    return cur


def cmd_qfail(project, args):
    """标记某个子问失败 —— 只回退该子问，不推翻全文。

    用法: python core/tools/state.py <项目> qfail Q3 writer/section-writer --reason "..."
          （第 3 个位置参数=子问号，第 4 个=责任环节）
    """
    qid = args.hand
    blamed = args.agent or ""
    if not qid:
        print("[state] 用法: qfail <子问号> <责任环节> --reason ...", file=sys.stderr)
        return 1
    cur = _qset(project, qid, {
        "status": "failed",
        "blamed": blamed,
        "reason": args.reason or "",
    })
    if cur is None:
        return 1
    print(f"[state] {qid} 已标记失败（责任环节 {blamed}）")
    print("[state] 回退范围仅限该子问，其余子问不受影响")
    return 0


def cmd_qfix(project, args):
    """标记某个子问已修复。用法: qfix Q3 --reason "..." """
    cur = _qset(project, args.hand, {"status": "fixed", "reason": args.reason or ""})
    if cur is None:
        return 1
    print(f"[state] {args.hand} 已标记修复")
    return 0


def cmd_qstatus(project, args):
    """查看按子问的进度（局部回修视图）。"""
    st = load(project)
    if st is None:
        print("[state] 无状态文件，先 init", file=sys.stderr)
        return 1
    qs = st.get("q_states", {})
    if not qs:
        print("无子问状态记录")
        return 0
    print(f"子问状态（{len(qs)} 个）:")
    for qid, v in sorted(qs.items()):
        print(f"  {qid}: {v.get('status')}" +
              (f"  责任环节 {v.get('blamed')}" if v.get("blamed") else "") +
              (f"  {v.get('reason')}" if v.get("reason") else ""))
    return 0


def decision_log_path(project):
    return project_dir(project) / "work" / "decision_log.json"


def load_decision_log(project):
    p = decision_log_path(project)
    if not p.exists():
        return {
            "project_name": Path(project_dir(project)).name,
            "created_at": _now(),
            "updated_at": _now(),
            "entries": []
        }
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[state] 读取 decision_log 失败 {p}: {e}", file=sys.stderr)
        return {"project_name": "", "created_at": _now(), "updated_at": _now(), "entries": []}


def save_decision_log(project, log):
    p = decision_log_path(project)
    p.parent.mkdir(parents=True, exist_ok=True)
    log["updated_at"] = _now()
    p.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def cmd_decision_add(project, args):
    """记录一条决策日志。
    
    用法: python core/tools/state.py <项目> decision-add \
        --stage "modeler/type-classifier" \
        --agent "type-classifier" \
        --decision-type "model_selection" \
        --question "选择题型" \
        --options '["A: 物理机理", "B: 实验数据", "C: 数据驱动"]' \
        --choice "A" \
        --rationale "题目给出物理方程" \
        --confidence 0.9 \
        --time-spent 120
    """
    import shlex
    log = load_decision_log(project)
    
    entry = {
        "timestamp": _now(),
        "stage": args.stage or "",
        "agent": args.agent or "",
        "decision_type": args.decision_type or "other",
        "question": args.question or "",
        "options": [],
        "choice": args.choice or "",
        "rationale": args.rationale or "",
        "confidence": float(args.confidence) if args.confidence else 0.0,
        "alternatives_considered": shlex.split(args.alternatives) if args.alternatives else [],
        "time_spent_seconds": int(args.time_spent) if args.time_spent else 0,
    }
    
    if args.options:
        try:
            entry["options"] = json.loads(args.options)
        except Exception:
            entry["options"] = shlex.split(args.options)
    
    log["entries"].append(entry)
    save_decision_log(project, log)
    print(f"[state] 已记录决策: {entry['stage']}/{entry['agent']} - {entry['choice']}")
    return 0


def cmd_decision_show(project, args):
    """显示决策日志。"""
    log = load_decision_log(project)
    entries = log.get("entries", [])
    if not entries:
        print("决策日志为空")
        return 0
    
    for i, e in enumerate(entries, 1):
        print(f"\n[{i}] {e.get('timestamp')}  {e.get('stage')}/{e.get('agent')}")
        print(f"    类型: {e.get('decision_type')}")
        print(f"    问题: {e.get('question')}")
        print(f"    选择: {e.get('choice')} (置信度: {e.get('confidence')})")
        print(f"    理由: {e.get('rationale')}")
        if e.get("options"):
            print(f"    选项: {e.get('options')}")
        if e.get("alternatives_considered"):
            print(f"    备选: {e.get('alternatives_considered')}")
        if e.get("time_spent_seconds"):
            print(f"    耗时: {e.get('time_spent_seconds')}s")
    return 0


def cmd_v3(project, args):
    """V3 多维状态视图（桥接 runtime/state + runtime/legacy 转换器）。

    - 项目尚无 state/status.json 时自动执行 V2→V3 转换（幂等，不动 V2 文件）
    - 已有时直接展示多维状态摘要
    """
    sys.path.insert(0, str(ROOT / "core"))
    from runtime.legacy.convert import convert_project
    from runtime.state.model import ProjectState

    pdir = project_dir(project)
    status_path = pdir / "state" / "status.json"
    if not status_path.exists():
        print("[state] 未发现 V3 state/，执行 V2→V3 转换（幂等，V2 文件不动）…")
        report = convert_project(pdir)
        print(f"[state] 转换完成: artifacts={report['registry']['total']} "
              f"relations={report['graph_relations']}")
    st = ProjectState(status_path)
    s = st.summary()
    print(f"项目: {s['project']}   phase: {s['phase']}")
    print(f"problem: {s['problem']}")
    for qid, qstatus in s["questions"].items():
        print(f"  {qid}: {qstatus}")
    ev = s["evidence"]
    print(f"evidence: graph v{ev['graph_version']}  "
          f"claims {ev['claims_supported']}/{ev['claims_total']}")
    wf = s["workflow"]
    print(f"workflow: completed={wf['completed']} blocked={wf['blocked']} "
          f"waiting={wf['waiting']}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="执行状态管理（跨 runtime 执行协议）")
    ap.add_argument("project", help="项目目录名或路径，如 cumcm2024a")
    ap.add_argument("command",
                    choices=["init", "status", "sync", "advance", "fail", "reset",
                    "qfail", "qfix", "qstatus",
                    "decision-add", "decision-show", "v3"])
    # hand/agent 仅用于 advance/fail/qfail/qfix 命令
    # 手名从 PIPELINE 动态派生：此前硬编码「modeler/programmer/writer」漏了
    # reviewer，让人以为评审手不受 state.py 管理。
    _hands = "/".join(dict.fromkeys(h for h, _a, _s in PIPELINE))
    ap.add_argument("hand", nargs="?",
                    help=f"hand（{_hands}）或 子问ID(qfail/qfix)")
    ap.add_argument("agent", nargs="?", help="agent 名（advance/fail）或 责任环节(qfail)")
    ap.add_argument("--output", help="本步产物路径（会记录 sha256）")
    ap.add_argument("--reason", help="失败原因")
    ap.add_argument("--to", help="reset 到指定 hand/agent")
    # decision-log 参数
    ap.add_argument("--stage", help="决策所属阶段，如 modeler/type-classifier")
    ap.add_argument("--decision-type", help="决策类型: model_selection/verdict/refine/parameter/template/structure/figure/reference/other")
    ap.add_argument("--question", help="决策问题描述")
    ap.add_argument("--options", help="选项列表，JSON数组或空格分隔")
    ap.add_argument("--choice", help="最终选择")
    ap.add_argument("--rationale", help="选择理由")
    ap.add_argument("--confidence", help="置信度 0-1")
    ap.add_argument("--alternatives", help="考虑的备选方案，空格分隔")
    ap.add_argument("--time-spent", help="决策耗时秒数")
    ap.add_argument("--no-gate", action="store_true",
                    help="advance 时跳过门禁校验（紧急情况用，会绕过硬失败拦截）")
    args = ap.parse_args()

    fn = {
        "init": cmd_init,
        "status": cmd_status,
        "advance": cmd_advance,
        "fail": cmd_fail,
        "reset": cmd_reset,
        "sync": cmd_sync,
        "qfail": cmd_qfail,
        "qfix": cmd_qfix,
        "qstatus": cmd_qstatus,
        "decision-add": cmd_decision_add,
        "decision-show": cmd_decision_show,
        "v3": cmd_v3,
    }[args.command]
    return fn(args.project, args)


if __name__ == "__main__":
    sys.exit(main())
