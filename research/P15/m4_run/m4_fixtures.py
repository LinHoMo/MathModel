# -*- coding: utf-8 -*-
"""P1-M4 知识引导 vs 无引导 fixtures（外部 Model Constructor 手写注入，LLM-free）。

对比设计（同一问题 2024_A，同一正确求解器 C2_CODE）：
- 知识引导候选 GUIDED：MODEL_IR 的 validations/assumptions/risks 由 BZD 试点卡
  （mc-bzd-model-fit + mc-bzd-validation-obligations）机械映射填充，每项带
  source_card；knowledge_refs 指向卡 id。dependencies 追加 requires 结构化声明。
- 无引导候选 UNGUIDED：MODEL_IR 的 validations/assumptions/risks 为空
  （模拟"没有知识引导时建模者不声明验证义务"），代码同样可执行。

核心 runtime 只做登记/校验/执行/验证/选型，不判 PASS；
义务是候选声明，最终由执行/验证裁决（LLM-free 铁律）。
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO / "core") not in sys.path:
    sys.path.insert(0, str(_REPO / "core"))
if str(Path(__file__).resolve().parent.parent / "vs001_run") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vs001_run"))

from vs001_fixtures import C2_CODE, M2_DICT, VALIDATION_SPEC  # noqa: E402

from runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402
from runtime.modeling.candidates import _merge_obligations, map_card_obligations  # noqa: E402

# BZD 试点卡（知识引导义务来源；卡见 core/knowledge/methods/cards/mc-bzd-*.yaml）
GUIDE_CARD_IDS = ["mc-bzd-model-fit", "mc-bzd-validation-obligations"]
GUIDED_MODEL_ID = "M2024A-Q1-GUIDED"
UNGUIDED_MODEL_ID = "M2024A-Q1-UNGUIDED"


def bzd_cards():
    """加载 BZD 试点卡（构造 retriever → 取卡），供映射与断言共用。"""
    r = KnowledgeRetriever(_REPO / "core" / "knowledge")
    return [r.cards[cid] for cid in GUIDE_CARD_IDS]


def _requires_to_dependencies(cards, model_id: str) -> list[dict]:
    """方法卡 requires → MODEL_IR.dependencies 结构化声明（可溯源）。"""
    deps, i = [], 0
    for c in cards:
        for req in (c.requires or []):
            i += 1
            deps.append({
                "dependency_id": f"DEPBZD{i:02d}",
                "from_type": "knowledge_card",
                "from_id": c.card_id,
                "to_type": "model",
                "to_id": model_id,
                "relation": "requires",
                "note": req,
            })
    return deps


def _with_ids(oblig: dict) -> dict:
    """为映射义务补 MODEL_IR 契约要求的 id（validation_id/assumption_id）。

    map_card_obligations 产出候选级义务（无 id）；嵌入 MODEL_IR 时由外部
    Model Constructor 补齐契约 id（外部注入职责，core 只校验）。
    """
    out = dict(oblig)
    for i, v in enumerate(oblig.get("validations", []), 1):
        v = dict(v)
        v.setdefault("validation_id", f"VALBZD{i:02d}")
        out.setdefault("_validations", []).append(v)
    for i, a in enumerate(oblig.get("assumptions", []), 1):
        a = dict(a)
        a.setdefault("assumption_id", f"ASMBZD{i:02d}")
        out.setdefault("_assumptions", []).append(a)
    if "_validations" in out:
        out["validations"] = out.pop("_validations")
    if "_assumptions" in out:
        out["assumptions"] = out.pop("_assumptions")
    return out


def build_guided_candidate() -> dict:
    """知识引导候选：建模者自身声明（M2 基线）∪ BZD 卡义务（去重，带 source_card）。"""
    cards = bzd_cards()
    oblig = {"validations": [], "assumptions": [], "risks": [], "dependencies": []}
    for c in cards:
        oblig = _merge_obligations(oblig, map_card_obligations(c))
    oblig = _with_ids(oblig)

    mir = dict(M2_DICT)
    mir["model_id"] = GUIDED_MODEL_ID
    merged = _merge_obligations({
        "validations": mir.get("validations", []),
        "assumptions": mir.get("assumptions", []),
        "risks": mir.get("risks", []),
        "dependencies": [],
    }, oblig)
    mir["validations"] = merged["validations"]
    mir["assumptions"] = merged["assumptions"]
    mir["risks"] = merged["risks"]
    mir["dependencies"] = list(mir.get("dependencies", [])) \
        + _requires_to_dependencies(cards, GUIDED_MODEL_ID)
    mir["knowledge_refs"] = [{"id": c.card_id, "version": c.version}
                             for c in cards]
    return {"model_ir": mir, "code": C2_CODE}


def build_unguided_candidate() -> dict:
    """无引导候选：义务极少（1 条通用假设 + 1 条通用验证，无 knowledge 来源），
    代码可执行。MODEL_IR 契约要求 validations/assumptions 非空且带 id——
    "极少"而非空，正是"没有知识引导时建模者不声明验证义务"的量化形态。
    """
    mir = dict(M2_DICT)
    mir["model_id"] = UNGUIDED_MODEL_ID
    mir["validations"] = [{
        "validation_id": "VALBASE01",
        "type": "constraint",
        "method": "结果合理性目检（无知识引导下的最低义务）",
        "results": {},
        "pass_fail": "pending",
        "evidence_refs": [], "targets_refs": [],
    }]
    mir["assumptions"] = [{
        "assumption_id": "ASSU-BASE-01",
        "content": "模型参数在题目给定范围内取值",
    }]
    mir["risks"] = []
    return {"model_ir": mir, "code": C2_CODE}


GUIDED = build_guided_candidate()
UNGUIDED = build_unguided_candidate()
CANDIDATES = [GUIDED, UNGUIDED]
