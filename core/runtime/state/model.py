"""V3 多维 State Model — 系统现在处于什么状态。

设计（与 docs/architecture/V3.1_ARCHITECTURE.md §1.2 一致）:
    * State 是**派生视图**，不是内容仓库——研究内容在 Artifact payload，
      State 只存状态与聚合视图。
    * 维度: problem / questions / models / experiments / evidence / narrative /
      paper / review / workflow / run。
    * 29-step 线性编号退役为 legacy（core/runtime/legacy 负责映射）。
    * Question 是一等执行单元（Per-Qi）：独立状态机 + 依赖声明。

持久化: projects/<p>/state/status.json。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

STATE_VERSION = 3

# ------------------------------------------------------------- Question 状态机
#
# pending → analyzing → modeled → experimenting → validated → complete
#                                    │                 │
#                                    └──→ failed ──────┘（可回 experimenting 重试）
# 任意非终态 → blocked（依赖阻塞，可恢复）
# complete 为该 Question 的稳定态（Artifact 层仍可继续演化）

QUESTION_STATES = (
    "pending", "analyzing", "modeled", "experimenting",
    "validated", "complete", "failed", "blocked",
)

_QUESTION_TRANSITIONS: dict[str, set[str]] = {
    "pending":       {"analyzing", "blocked", "failed"},
    "analyzing":     {"modeled", "blocked", "failed", "analyzing"},
    "modeled":       {"experimenting", "blocked", "failed", "analyzing"},
    "experimenting": {"validated", "failed", "blocked", "experimenting"},
    "validated":     {"complete", "blocked", "failed", "experimenting"},
    "failed":        {"analyzing", "modeled", "experimenting", "failed"},
    "blocked":       {"pending", "analyzing", "modeled", "experimenting", "blocked"},
    "complete":      {"complete", "failed"},   # complete 后仍可被失效传播打回
}

# 问题级维度状态
DIMENSION_STATES = ("pending", "in_progress", "partial", "complete", "blocked")


class StateError(ValueError):
    """State 操作非法。"""


def _utcnow() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def can_question_transition(cur: str, target: str) -> bool:
    if cur not in QUESTION_STATES or target not in QUESTION_STATES:
        return False
    return target in _QUESTION_TRANSITIONS[cur]


class ProjectState:
    """多维项目状态（读写 projects/<p>/state/status.json）。"""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.data: dict = self._empty()
        if self.path.exists():
            self.load()

    # ------------------------------------------------------------ 初始化

    @staticmethod
    def _empty() -> dict:
        return {
            "schema_version": STATE_VERSION,
            "project": "",
            "state": {
                "problem": {"status": "pending"},
                "questions": {},
                "models": {"status": "pending", "candidates": [], "selected": []},
                "experiments": {"status": "pending", "by_question": {}},
                "evidence": {"status": "pending", "graph_version": 0,
                             "claims_supported": 0, "claims_total": 0},
                "narrative": {"status": "pending"},
                "paper": {"status": "pending", "sections_written": 0,
                          "sections_total": 0},
                "review": {"status": "pending", "rounds_completed": 0,
                           "verdict": None},
            },
            "workflow": {
                "current_nodes": [],
                "completed_nodes": [],
                "blocked_nodes": [],
                "waiting_approval": [],
                "retries": {},
                "notes": [],
            },
            "run": {"phase": "init", "started_at": _utcnow(), "updated_at": _utcnow()},
        }

    def _infer_project(self) -> str:
        parts = self.path.parts
        if "state" in parts:
            i = parts.index("state")
            if i >= 1 and parts[i - 1]:
                return parts[i - 1]
        return ""

    # ------------------------------------------------------------ 持久化

    def load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if raw.get("schema_version") != STATE_VERSION:
            raise StateError(f"status.json 版本不兼容: {raw.get('schema_version')!r}")
        self.data = raw
        if not self.data.get("project"):
            self.data["project"] = self._infer_project()

    def save(self) -> None:
        self.data["run"]["updated_at"] = _utcnow()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # ------------------------------------------------------------ Problem

    def set_problem_status(self, status: str) -> None:
        if status not in DIMENSION_STATES:
            raise StateError(f"非法 problem 状态: {status!r}")
        self.data["state"]["problem"]["status"] = status

    # ------------------------------------------------------------ Questions

    def ensure_question(self, question_id: str, *, dependencies: list[str] | None = None) -> dict:
        qs = self.data["state"]["questions"]
        if question_id not in qs:
            qs[question_id] = {
                "status": "pending",
                "models": [],
                "experiments": [],
                "claims": [],
                "dependencies": list(dependencies or []),
                "retry_count": 0,
                "failure_reason": None,
                "last_updated": _utcnow(),
            }
        return qs[question_id]

    def set_question_status(self, question_id: str, status: str,
                            *, failure_reason: str | None = None) -> dict:
        q = self.ensure_question(question_id)
        if not can_question_transition(q["status"], status):
            raise StateError(
                f"Question {question_id} 非法状态转换: {q['status']} → {status}")
        q["status"] = status
        q["last_updated"] = _utcnow()
        if status == "failed":
            q["retry_count"] += 1
            q["failure_reason"] = failure_reason
        elif status in ("analyzing", "modeled", "experimenting"):
            q["failure_reason"] = None
        return q

    def question_status(self, question_id: str) -> str:
        q = self.data["state"]["questions"].get(question_id)
        return q["status"] if q else "pending"

    def attach(self, question_id: str, kind: str, artifact_id: str) -> dict:
        """把 Artifact 挂到 Question 名下（kind: models/experiments/claims）。"""
        q = self.ensure_question(question_id)
        if kind not in ("models", "experiments", "claims"):
            raise StateError(f"非法挂载类型: {kind!r}")
        if artifact_id not in q[kind]:
            q[kind].append(artifact_id)
        q["last_updated"] = _utcnow()
        return q

    def blocked_by_dependencies(self, question_id: str) -> list[str]:
        """返回尚未 complete/validated 的依赖 Question。"""
        q = self.data["state"]["questions"].get(question_id)
        if not q:
            return []
        blocked = []
        for dep in q.get("dependencies", []):
            dq = self.data["state"]["questions"].get(dep)
            if not dq or dq["status"] not in ("complete", "validated"):
                blocked.append(dep)
        return blocked

    # ------------------------------------------------------------ 维度

    def set_dimension(self, name: str, status: str, **fields) -> None:
        dim = self.data["state"].get(name)
        if dim is None or not isinstance(dim, dict):
            raise StateError(f"未知状态维度: {name!r}")
        if status is not None:
            if status not in DIMENSION_STATES:
                raise StateError(f"非法维度状态: {status!r}")
            dim["status"] = status
        for k, v in fields.items():
            dim[k] = v

    def dimension(self, name: str) -> dict:
        dim = self.data["state"].get(name)
        if dim is None:
            raise StateError(f"未知状态维度: {name!r}")
        return dim

    # ------------------------------------------------------------ Workflow

    def workflow_complete(self, node_id: str) -> None:
        wf = self.data["workflow"]
        if node_id not in wf["completed_nodes"]:
            wf["completed_nodes"].append(node_id)
        for key in ("current_nodes", "blocked_nodes", "waiting_approval"):
            if node_id in wf[key]:
                wf[key].remove(node_id)

    def workflow_block(self, node_id: str, reason: str = "") -> None:
        wf = self.data["workflow"]
        if node_id not in wf["blocked_nodes"]:
            wf["blocked_nodes"].append(node_id)
        if node_id in wf["current_nodes"]:
            wf["current_nodes"].remove(node_id)
        if reason:
            wf.setdefault("notes", []).append(
                {"node": node_id, "note": reason, "at": _utcnow()})

    def workflow_waiting(self, node_id: str) -> None:
        wf = self.data["workflow"]
        if node_id not in wf["waiting_approval"]:
            wf["waiting_approval"].append(node_id)
        if node_id in wf["current_nodes"]:
            wf["current_nodes"].remove(node_id)

    def workflow_approve(self, node_id: str) -> None:
        wf = self.data["workflow"]
        if node_id in wf["waiting_approval"]:
            wf["waiting_approval"].remove(node_id)

    def workflow_set_current(self, node_ids: list[str]) -> None:
        self.data["workflow"]["current_nodes"] = list(node_ids)

    def workflow_record_retry(self, node_id: str) -> int:
        wf = self.data["workflow"]
        wf["retries"][node_id] = wf["retries"].get(node_id, 0) + 1
        return wf["retries"][node_id]

    def workflow_reset(self, node_ids: list[str]) -> None:
        """partial rerun：从 completed 中摘除指定节点（引擎计算受影响下游后调用）。"""
        wf = self.data["workflow"]
        drop = set(node_ids)
        wf["completed_nodes"] = [n for n in wf["completed_nodes"] if n not in drop]
        for key in ("current_nodes", "blocked_nodes", "waiting_approval"):
            wf[key] = [n for n in wf[key] if n not in drop]
        wf["retries"] = {n: c for n, c in wf["retries"].items() if n not in drop}

    # ------------------------------------------------- Registry/Graph 派生

    def refresh_from(self, registry, graph) -> dict:
        """从 Registry + EvidenceGraph 派生聚合视图（State 是派生层的落点）。"""
        st = self.data["state"]
        qs = {a.artifact_id for a in registry.list_by_type("question")}
        for qid in qs:
            self.ensure_question(qid)
        # 清理 registry 中已不存在的 question（一般不会发生，防御）
        for qid in list(st["questions"]):
            if qid not in qs:
                del st["questions"][qid]

        st["models"]["candidates"] = [a.artifact_id for a in registry.list_by_type("model")]
        st["models"]["selected"] = [
            a.artifact_id for a in registry.list_by_type("model")
            if a.status in ("validated", "published")]
        for exp in registry.list_by_type("experiment"):
            q = exp.question
            if q and q in st["questions"]:
                self.attach(q, "experiments", exp.artifact_id)
        for claim in registry.list_by_type("claim"):
            q = claim.question
            if q and q in st["questions"]:
                self.attach(q, "claims", claim.artifact_id)
        cov = graph.coverage() if graph else {}
        st["evidence"].update({
            "graph_version": getattr(graph, "graph_version", 0),
            "claims_supported": cov.get("claims_supported", 0),
            "claims_total": cov.get("claims_total", 0),
            "coverage_ratio": cov.get("coverage_ratio"),
        })
        # 问题状态自动晋级：有 claim 被支撑 → validated
        for qid, q in st["questions"].items():
            if q["status"] in ("experimenting",) and q["claims"]:
                supported = any(
                    any(e["relation"] == "supports" and e["to"] == c
                        for e in graph.relations)
                    for c in q["claims"])
                if supported and can_question_transition(q["status"], "validated"):
                    q["status"] = "validated"
                    q["last_updated"] = _utcnow()
        return self.summary()

    def summary(self) -> dict:
        st = self.data["state"]
        return {
            "project": self.data.get("project"),
            "problem": st["problem"]["status"],
            "questions": {qid: q["status"] for qid, q in st["questions"].items()},
            "models_selected": st["models"].get("selected", []),
            "evidence": {k: st["evidence"].get(k) for k in
                         ("graph_version", "claims_supported", "claims_total",
                          "coverage_ratio")},
            "workflow": {
                "completed": len(self.data["workflow"]["completed_nodes"]),
                "blocked": list(self.data["workflow"]["blocked_nodes"]),
                "waiting": list(self.data["workflow"]["waiting_approval"]),
            },
            "phase": self.data["run"].get("phase"),
        }
