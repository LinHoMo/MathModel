"""DecisionLog — 参与未来决策的连续决策记忆（V3 P2）。

区别于 V2 decision_log（历史日志）：决策是一等实体，可被推翻（invalidated），
推翻后在检索中降权并附带「为何被推翻」；供 method-selection 与 critic 消费。

持久化: projects/<p>/state/decisions.json（原子写）
契约: core/schemas/v3/decision/decision.schema.json（必填字段在此 fail-closed 校验）
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DECISIONS_VERSION = 3
DECISION_ID_RE = re.compile(r"^D\d{1,6}$")


class DecisionLogError(ValueError):
    """Decision Log 操作非法。"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Decision:
    decision_id: str
    question: str
    chosen: str
    alternatives: list[str]
    criteria: list[str]
    evidence_ids: list[str]
    reasoning: str
    confidence: float
    reversible: bool
    created_by: str
    created_at: str
    status: str = "active"
    question_type: str = ""
    # ---- P8-8 Decision Trace：知识版本绑定（历史决策可重现，CI-07）----
    knowledge_refs: list[dict] = field(default_factory=list)  # [{id, version}]
    failure_refs: list[str] = field(default_factory=list)     # 影响决策的失败记忆
    required_validation: list[str] = field(default_factory=list)
    score_breakdown: dict = field(default_factory=dict)
    consequences: list[str] = field(default_factory=list)
    invalidated_by: str | None = None
    invalidated_reason: str | None = None
    invalidated_at: str | None = None

    @property
    def active(self) -> bool:
        return self.status == "active"

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict, where: str = "decision") -> "Decision":
        for key in ("decision_id", "question", "chosen", "reasoning", "created_by"):
            if not isinstance(d.get(key), str) or not d[key].strip():
                raise DecisionLogError(f"{where}: 缺少必填字符串字段 '{key}'")
        if not DECISION_ID_RE.match(d["decision_id"]):
            raise DecisionLogError(
                f"{where}: decision_id '{d['decision_id']}' 不匹配 ^D\\d{{1,6}}$")
        for key in ("alternatives", "criteria"):
            v = d.get(key)
            if not isinstance(v, list) or not v or \
                    not all(isinstance(x, str) for x in v):
                raise DecisionLogError(f"{where}: '{key}' 须为非空字符串列表")
        if not isinstance(d.get("evidence_ids"), list):
            raise DecisionLogError(f"{where}: 'evidence_ids' 须为列表（可为空）")
        conf = d.get("confidence")
        if not isinstance(conf, (int, float)) or not 0.0 <= float(conf) <= 1.0:
            raise DecisionLogError(f"{where}: confidence 须为 [0,1] 数值")
        if not isinstance(d.get("reversible"), bool):
            raise DecisionLogError(f"{where}: reversible 须为 bool")
        if not isinstance(d.get("knowledge_refs", []), list)                 or not isinstance(d.get("failure_refs", []), list)                 or not isinstance(d.get("required_validation", []), list)                 or not isinstance(d.get("score_breakdown", {}), dict):
            raise DecisionLogError(f"{where}: P8 追踪字段类型非法")
        status = d.get("status", "active")
        if status not in ("active", "invalidated"):
            raise DecisionLogError(f"{where}: status 非法 {status!r}")
        return cls(
            decision_id=d["decision_id"],
            question=d["question"],
            chosen=d["chosen"],
            alternatives=d["alternatives"],
            criteria=d["criteria"],
            evidence_ids=d.get("evidence_ids", []),
            reasoning=d["reasoning"],
            confidence=float(conf),
            reversible=d["reversible"],
            created_by=d["created_by"],
            created_at=d.get("created_at", _now()),
            status=status,
            question_type=d.get("question_type", "") or "",
            consequences=d.get("consequences", []) or [],
            knowledge_refs=d.get("knowledge_refs", []) or [],
            failure_refs=d.get("failure_refs", []) or [],
            required_validation=d.get("required_validation", []) or [],
            score_breakdown=d.get("score_breakdown", {}) or {},
            invalidated_by=d.get("invalidated_by"),
            invalidated_reason=d.get("invalidated_reason"),
            invalidated_at=d.get("invalidated_at"),
        )


class DecisionLog:
    """项目级决策日志。构造时 load（存在则），save 持久化（原子写）。"""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.decisions: dict[str, Decision] = {}
        self._counter = 0
        # P7 并发契约：并行节点同时登记决策必须互斥
        import threading
        self._lock = threading.RLock()
        if self.path.exists():
            self.load()

    # ------------------------------------------------------------ 持久化

    def load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("schema_version") != DECISIONS_VERSION:
            raise DecisionLogError(
                f"decisions.json 版本不兼容: {raw.get('schema_version')!r}")
        self.decisions = {}
        for d in raw.get("decisions", []):
            dec = Decision.from_dict(d, where=f"decisions.json[{d.get('decision_id')}]")
            if dec.decision_id in self.decisions:
                raise DecisionLogError(f"decision_id 重复: {dec.decision_id}")
            self.decisions[dec.decision_id] = dec
        self._counter = max(
            (int(d.decision_id[1:]) for d in self.decisions.values()),
            default=0)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": DECISIONS_VERSION,
            "updated_at": _now(),
            "decisions": [d.as_dict() for d in
                          sorted(self.decisions.values(), key=lambda x: x.decision_id)],
        }
        fd, tmp = tempfile.mkstemp(dir=str(self.path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # ------------------------------------------------------------ 写入

    def next_id(self) -> str:
        n = self._counter + 1
        while f"D{n:03d}" in self.decisions:
            n += 1
        return f"D{n:03d}"

    def add(self, question: str, chosen: str, alternatives: list[str],
            criteria: list[str], reasoning: str, confidence: float,
            reversible: bool, created_by: str,
            evidence_ids: list[str] | None = None,
            question_type: str = "",
            decision_id: str | None = None,
            knowledge_refs: list[dict] | None = None,
            failure_refs: list[str] | None = None,
            required_validation: list[str] | None = None,
            score_breakdown: dict | None = None) -> Decision:
        """登记决策。缺省自动分配下一个 D 编号。"""
        with self._lock:
            return self._add_locked(question, chosen, alternatives, criteria,
                                    reasoning, confidence, reversible,
                                    created_by, evidence_ids=evidence_ids,
                                    question_type=question_type,
                                    decision_id=decision_id,
                                    knowledge_refs=knowledge_refs,
                                    failure_refs=failure_refs,
                                    required_validation=required_validation,
                                    score_breakdown=score_breakdown)

    def _add_locked(self, question, chosen, alternatives, criteria,
                    reasoning, confidence, reversible, created_by,
                    evidence_ids=None, question_type="",
                    decision_id=None, knowledge_refs=None,
                    failure_refs=None, required_validation=None,
                    score_breakdown=None) -> Decision:
        did = decision_id or self.next_id()
        dec = Decision.from_dict({
            "decision_id": did,
            "question": question,
            "chosen": chosen,
            "alternatives": alternatives,
            "criteria": criteria,
            "evidence_ids": evidence_ids or [],
            "reasoning": reasoning,
            "confidence": confidence,
            "reversible": reversible,
            "created_by": created_by,
            "created_at": _now(),
            "question_type": question_type,
            "knowledge_refs": knowledge_refs or [],
            "failure_refs": failure_refs or [],
            "required_validation": required_validation or [],
            "score_breakdown": score_breakdown or {},
        }, where=f"add({did})")
        if dec.decision_id in self.decisions:
            raise DecisionLogError(f"decision_id 已存在: {dec.decision_id}")
        self.decisions[dec.decision_id] = dec
        self._counter = max(self._counter, int(dec.decision_id[1:]))
        return dec

    def invalidate(self, decision_id: str, invalidated_by: str,
                   reason: str) -> Decision:
        """推翻决策。invalidated_by 指向新决策 ID（须已存在）或事件描述。"""
        dec = self.decisions.get(decision_id)
        if dec is None:
            raise DecisionLogError(f"决策不存在: {decision_id}")
        if dec.status != "active":
            raise DecisionLogError(f"决策已是 {dec.status}，不可再推翻: {decision_id}")
        if re.match(r"^D\d{1,6}$", invalidated_by) and \
                invalidated_by not in self.decisions:
            raise DecisionLogError(f"invalidated_by 指向不存在的决策: {invalidated_by}")
        if not reason.strip():
            raise DecisionLogError("invalidate 需要非空 reason")
        dec.status = "invalidated"
        dec.invalidated_by = invalidated_by
        dec.invalidated_reason = reason
        dec.invalidated_at = _now()
        return dec

    def record_consequence(self, decision_id: str, note: str) -> Decision:
        """追加决策后果记录（追加式，不覆盖）。"""
        dec = self.decisions.get(decision_id)
        if dec is None:
            raise DecisionLogError(f"决策不存在: {decision_id}")
        if not note.strip():
            raise DecisionLogError("后果记录不能为空")
        dec.consequences.append(note)
        return dec

    # ------------------------------------------------------------ 检索

    def get(self, decision_id: str) -> Decision:
        return self.decisions[decision_id]

    def query(self, question_type: str | None = None,
              method: str | None = None,
              text: str | None = None,
              active_only: bool = True) -> list[dict]:
        """按条件检索决策。active 决策在前；invalidated 降权附推翻说明。"""
        out = []
        for dec in sorted(self.decisions.values(), key=lambda x: x.decision_id):
            if active_only and not dec.active:
                continue
            if question_type and dec.question_type != question_type:
                continue
            if method and method.lower() not in dec.chosen.lower():
                continue
            if text and text.lower() not in (dec.question + dec.chosen + dec.reasoning).lower():
                continue
            out.append(self._view(dec))
        return out

    def _view(self, dec: Decision) -> dict:
        d = dec.as_dict()
        if not dec.active:
            d["superseded_note"] = (
                f"已被 {dec.invalidated_by} 推翻: {dec.invalidated_reason}")
        return d
