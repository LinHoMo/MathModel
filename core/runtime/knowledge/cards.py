"""Knowledge 内容加载器 — Method Card / Failure / Pattern（零第三方依赖）。

加载 core/knowledge/ 下三组结构化 YAML，按契约必填字段做 fail-closed 校验：
任何一张卡缺字段 / ID 格式非法 → CardError，整库不加载（不允许半懂不懂地检索）。

刻意不实现完整 JSON Schema 校验器（仓库零依赖惯例）——契约的必填字段与
格式在此逐项检查，schema 文件供外部工具与人类阅读。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from ..execution.yamlio import YamlSyntaxError, load_file

CARD_ID_RE = re.compile(r"^mc-[a-z0-9-]{2,48}$")
FAILURE_ID_RE = re.compile(r"^fm-[a-z0-9-]{2,48}$")
PATTERN_ID_RE = re.compile(r"^ip-[a-z0-9-]{2,48}$")
SAMPLE_SIZES = {"small", "medium", "large"}
FAILURE_MODES = {
    "wrong-method", "wrong-usage", "no-evidence", "overclaim",
    "presentation", "numerical", "consistency",
}


class CardError(ValueError):
    """知识卡契约违反。"""


def _require_str_list(d: dict, key: str, where: str, min_items: int = 0) -> list[str]:
    v = d.get(key, [])
    if not isinstance(v, list) or len(v) < min_items or \
            not all(isinstance(x, str) for x in v):
        raise CardError(f"{where}: 字段 '{key}' 须为字符串列表（≥{min_items} 项）")
    return v


def _require_str(d: dict, key: str, where: str) -> str:
    v = d.get(key)
    if not isinstance(v, str) or not v.strip():
        raise CardError(f"{where}: 缺少必填字符串字段 '{key}'")
    return v


# ---------------------------------------------------------------- 方法卡

@dataclass
class MethodCard:
    card_id: str
    name: str
    family: str
    version: int
    problem_types: list[str]
    good_for: list[str]
    requires: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    validation: list[str] = field(default_factory=list)
    often_combined_with: list[str] = field(default_factory=list)
    anti_patterns: list[str] = field(default_factory=list)
    known_failures: list[str] = field(default_factory=list)
    reference: str = ""
    # match 块（检索打分，可缺省）
    requires_data: bool | None = None
    sample_size: list[str] = field(default_factory=list)
    time_series: bool | None = None
    multi_objective: bool = False
    handles_uncertainty: bool = False
    # ---- P8 决策字段（全部可选，向后兼容旧卡）----
    objective_types: list[str] = field(default_factory=list)
    applicability_positive: list[str] = field(default_factory=list)
    applicability_negative: list[str] = field(default_factory=list)
    required_conditions: list[str] = field(default_factory=list)
    risk: dict = field(default_factory=dict)          # 5 维 → low/medium/high
    evidence_minimum: list[str] = field(default_factory=list)
    evidence_recommended: list[str] = field(default_factory=list)
    typical_metrics: list[str] = field(default_factory=list)
    compatible_methods: list[str] = field(default_factory=list)
    incompatible_methods: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    costs: dict = field(default_factory=dict)          # {data, compute}
    robustness: str = ""                               # low/medium/high
    overfitting_risk: str = ""
    competition_suitability: str = ""
    innovation_potential: str = ""
    interpretability: str = ""
    status: str = "active"                             # active/draft/deprecated
    source_refs: list[str] = field(default_factory=list)
    confidence: float | None = None
    source_type: str = ""

    @classmethod
    def from_dict(cls, d: dict, where: str) -> "MethodCard":
        card_id = _require_str(d, "card_id", where)
        if not CARD_ID_RE.match(card_id):
            raise CardError(f"{where}: card_id '{card_id}' 不匹配 ^mc-[a-z0-9-]{{2,48}}$")
        version = d.get("version", 1)
        if not isinstance(version, int) or version < 1:
            raise CardError(f"{where}: version 须为 ≥1 整数")
        problem_types = _require_str_list(d, "problem_types", where, min_items=1)
        card = cls(
            card_id=card_id,
            name=_require_str(d, "name", where),
            family=_require_str(d, "family", where),
            version=version,
            problem_types=problem_types,
            good_for=_require_str_list(d, "good_for", where, min_items=1),
            requires=_require_str_list(d, "requires", where),
            risks=_require_str_list(d, "risks", where),
            validation=_require_str_list(d, "validation", where),
            often_combined_with=_require_str_list(d, "often_combined_with", where),
            anti_patterns=_require_str_list(d, "anti_patterns", where),
            known_failures=_require_str_list(d, "known_failures", where),
            reference=d.get("reference", "") or "",
        )
        match = d.get("match", {})
        if match:
            if not isinstance(match, dict):
                raise CardError(f"{where}: match 须为映射")
            unknown = set(match) - {"requires_data", "sample_size", "time_series",
                                    "multi_objective", "handles_uncertainty"}
            if unknown:
                raise CardError(f"{where}: match 含未知键 {sorted(unknown)}")
            rd = match.get("requires_data")
            if rd is not None and not isinstance(rd, bool):
                raise CardError(f"{where}: match.requires_data 须为 bool")
            card.requires_data = rd
            ss = match.get("sample_size", [])
            if ss:
                if not isinstance(ss, list) or not set(ss) <= SAMPLE_SIZES:
                    raise CardError(f"{where}: match.sample_size 须为 [small|medium|large] 子集")
                card.sample_size = ss
            ts = match.get("time_series")
            if ts is not None and not isinstance(ts, bool):
                raise CardError(f"{where}: match.time_series 须为 bool 或省略")
            card.time_series = ts
            card.multi_objective = bool(match.get("multi_objective", False))
            card.handles_uncertainty = bool(match.get("handles_uncertainty", False))
        _parse_card_p8(card, d, where)
        return card


_LEVELS = {"low", "medium", "high"}


def _parse_p8_simple(d: dict, where: str, severity: bool = False) -> str:
    v = d.get("severity", "medium") if severity else d.get(d.get("_k", ""), "")
    v = v or ("medium" if severity else "")
    if v not in _LEVELS:
        raise CardError(f"{where}: severity 须为 low|medium|high")
    return v


def _parse_confidence(d: dict, where: str) -> float | None:
    c = d.get("confidence")
    if c is None:
        return None
    if not isinstance(c, (int, float)) or not 0 <= c <= 1:
        raise CardError(f"{where}: confidence 须在 [0,1]")
    return float(c)


def _opt_level(d: dict, key: str, where: str) -> str:
    v = d.get(key, "") or ""
    if v and v not in _LEVELS:
        raise CardError(f"{where}: {key} 须为 low|medium|high，实际 {v!r}")
    return v


def _parse_card_p8(card: MethodCard, d: dict, where: str) -> None:
    """P8 决策字段解析（全部可选；fail-closed 校验取值域）。"""
    card.objective_types = _require_str_list(d, "objective_types", where)
    app = d.get("applicability", {})
    if app:
        if not isinstance(app, dict):
            raise CardError(f"{where}: applicability 须为映射")
        unknown = set(app) - {"positive", "negative", "required_conditions"}
        if unknown:
            raise CardError(f"{where}: applicability 含未知键 {sorted(unknown)}")
        card.applicability_positive = _require_str_list(app, "positive", where)
        card.applicability_negative = _require_str_list(app, "negative", where)
        card.required_conditions = _require_str_list(app, "required_conditions", where)
    risk = d.get("risk", {})
    if risk:
        if not isinstance(risk, dict):
            raise CardError(f"{where}: risk 须为映射")
        unknown = set(risk) - {"overfitting", "data_sensitivity",
                               "numerical_instability", "interpretability",
                               "competition_risk"}
        if unknown:
            raise CardError(f"{where}: risk 含未知键 {sorted(unknown)}")
        for k, v in risk.items():
            if v not in _LEVELS:
                raise CardError(f"{where}: risk.{k} 须为 low|medium|high")
        card.risk = dict(risk)
    ev = d.get("evidence_requirements", {})
    if ev:
        if not isinstance(ev, dict):
            raise CardError(f"{where}: evidence_requirements 须为映射")
        unknown = set(ev) - {"minimum", "recommended"}
        if unknown:
            raise CardError(f"{where}: evidence_requirements 含未知键 {sorted(unknown)}")
        card.evidence_minimum = _require_str_list(ev, "minimum", where)
        card.evidence_recommended = _require_str_list(ev, "recommended", where)
    card.typical_metrics = _require_str_list(d, "typical_metrics", where)
    card.compatible_methods = _require_str_list(d, "compatible_methods", where)
    card.incompatible_methods = _require_str_list(d, "incompatible_methods", where)
    card.prerequisites = _require_str_list(d, "prerequisites", where)
    costs = d.get("costs", {})
    if costs:
        unknown = set(costs) - {"data", "compute"}
        if unknown or any(v not in _LEVELS for v in costs.values()):
            raise CardError(f"{where}: costs 须为 {{data|compute: low|medium|high}}")
        card.costs = dict(costs)
    card.robustness = _opt_level(d, "robustness", where)
    card.overfitting_risk = _opt_level(d, "overfitting_risk", where)
    card.competition_suitability = _opt_level(d, "competition_suitability", where)
    card.innovation_potential = _opt_level(d, "innovation_potential", where)
    card.interpretability = _opt_level(d, "interpretability", where)
    card.status = d.get("status", "active") or "active"
    if card.status not in {"active", "draft", "deprecated"}:
        raise CardError(f"{where}: status 非法: {card.status!r}")
    card.source_refs = _require_str_list(d, "source_refs", where)
    conf = d.get("confidence")
    if conf is not None:
        if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
            raise CardError(f"{where}: confidence 须在 [0,1]")
        card.confidence = float(conf)
    card.source_type = d.get("source_type", "") or ""


# ---------------------------------------------------------------- 失败记忆

@dataclass
class FailureMemory:
    failure_id: str
    title: str
    problem_context: str
    method: str
    method_family: str
    failure_mode: str
    symptom: str
    root_cause: str
    detection: str
    fix: str
    avoidance: str
    applies_to: list[str] = field(default_factory=list)
    source: str = ""
    # ---- P8 决策字段 ----
    severity: str = "medium"           # low/medium/high → risk penalty 权重
    confidence: float | None = None
    detection_signal: str = ""
    recovery: list[str] = field(default_factory=list)
    version: int = 1
    status: str = "active"

    @classmethod
    def from_dict(cls, d: dict, where: str) -> "FailureMemory":
        failure_id = _require_str(d, "failure_id", where)
        if not FAILURE_ID_RE.match(failure_id):
            raise CardError(f"{where}: failure_id '{failure_id}' 不匹配 ^fm-[a-z0-9-]{{2,48}}$")
        failure_mode = _require_str(d, "failure_mode", where)
        if failure_mode not in FAILURE_MODES:
            raise CardError(f"{where}: failure_mode '{failure_mode}' 非法，可选 {sorted(FAILURE_MODES)}")
        return cls(
            failure_id=failure_id,
            title=_require_str(d, "title", where),
            problem_context=_require_str(d, "problem_context", where),
            method=_require_str(d, "method", where),
            method_family=_require_str(d, "method_family", where),
            failure_mode=failure_mode,
            symptom=_require_str(d, "symptom", where),
            root_cause=_require_str(d, "root_cause", where),
            detection=_require_str(d, "detection", where),
            fix=_require_str(d, "fix", where),
            avoidance=_require_str(d, "avoidance", where),
            applies_to=_require_str_list(d, "applies_to", where),
            source=d.get("source", "") or "",
            severity=_parse_p8_simple(d, where, severity=True),
            confidence=_parse_confidence(d, where),
            detection_signal=d.get("detection_signal", "") or "",
            recovery=_require_str_list(d, "recovery", where),
            version=d.get("version", 1) or 1,
            status=d.get("status", "active") or "active",
        )


# ---------------------------------------------------------------- 创新模式

@dataclass
class Pattern:
    pattern_id: str
    title: str
    problem_types: list[str]
    baseline_method: str
    innovation: str
    required_evidence: list[str]
    risks: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    cards: list[str] = field(default_factory=list)
    # ---- P8 决策字段 ----
    expected_benefit: str = ""
    implementation_cost: str = ""      # low/medium/high
    novelty_level: str = ""            # incremental/notable/high
    validation_protocol: list[str] = field(default_factory=list)
    competition_fit: str = ""          # low/medium/high
    version: int = 1
    status: str = "active"

    @classmethod
    def from_dict(cls, d: dict, where: str) -> "Pattern":
        pattern_id = _require_str(d, "pattern_id", where)
        if not PATTERN_ID_RE.match(pattern_id):
            raise CardError(f"{where}: pattern_id '{pattern_id}' 不匹配 ^ip-[a-z0-9-]{{2,48}}$")
        return cls(
            pattern_id=pattern_id,
            title=_require_str(d, "title", where),
            problem_types=_require_str_list(d, "problem_types", where, min_items=1),
            baseline_method=_require_str(d, "baseline_method", where),
            innovation=_require_str(d, "innovation", where),
            required_evidence=_require_str_list(d, "required_evidence", where, min_items=1),
            risks=_require_str_list(d, "risks", where),
            examples=_require_str_list(d, "examples", where),
            cards=_require_str_list(d, "cards", where),
        expected_benefit=d.get("expected_benefit", "") or "",
        implementation_cost=_opt_level(d, "implementation_cost", where),
        novelty_level=d.get("novelty_level", "") or "",
        validation_protocol=_require_str_list(d, "validation_protocol", where),
        competition_fit=_opt_level(d, "competition_fit", where),
        version=d.get("version", 1) or 1,
        status=d.get("status", "active") or "active",
        )


# ---------------------------------------------------------------- 加载

def _load_dir(directory: Path, ctor, id_attr: str) -> dict[str, object]:
    """加载目录下全部 *.yaml 为 {id: 对象}，fail-closed。"""
    out: dict[str, object] = {}
    if not directory.is_dir():
        return out
    for f in sorted(directory.glob("*.yaml")):
        where = f.relative_to(directory.parents[1] if len(directory.parts) > 1 else directory)
        try:
            d = load_file(f)
        except YamlSyntaxError as exc:
            raise CardError(f"{where}: YAML 解析失败: {exc}") from exc
        if not isinstance(d, dict):
            raise CardError(f"{where}: 顶层须为映射")
        obj = ctor.from_dict(d, str(where))
        oid = getattr(obj, id_attr)
        if oid in out:
            raise CardError(f"{where}: {id_attr} '{oid}' 重复定义")
        out[oid] = obj
    return out


def load_knowledge(knowledge_root: str | Path) -> tuple[dict[str, MethodCard],
                                                        dict[str, FailureMemory],
                                                        dict[str, Pattern]]:
    """从 core/knowledge/ 加载三组知识，返回 (cards, failures, patterns)。

    加载后做交叉引用校验：卡片引用的 known_failures / often_combined_with /
    failure.applies_to / pattern.cards 必须存在。
    """
    root = Path(knowledge_root)
    cards = _load_dir(root / "methods" / "cards", MethodCard, "card_id")
    failures = _load_dir(root / "failures", FailureMemory, "failure_id")
    patterns = _load_dir(root / "patterns", Pattern, "pattern_id")

    for card in cards.values():
        for fid in card.known_failures:
            if fid not in failures:
                raise CardError(f"mc '{card.card_id}': known_failures 引用不存在的 '{fid}'")
        for cid in card.often_combined_with:
            if cid not in cards:
                raise CardError(f"mc '{card.card_id}': often_combined_with 引用不存在的 '{cid}'")
    for fm in failures.values():
        for cid in fm.applies_to:
            if cid not in cards:
                raise CardError(f"fm '{fm.failure_id}': applies_to 引用不存在的 '{cid}'")
    for pat in patterns.values():
        for cid in pat.cards:
            if cid not in cards:
                raise CardError(f"ip '{pat.pattern_id}': cards 引用不存在的 '{cid}'")
    return cards, failures, patterns
