# -*- coding: utf-8 -*-
"""Knowledge-guided Construction — LLM-free 机械映射（正式模块）。

P1-M4 知识引导演示的正式化：知识卡 → MODEL_IR 候选/假设/义务 三类接入点，
全部可溯源（source_card + knowledge_refs）。本模块只做机械映射，不判 PASS、
不生成数值、不指定"必须用 X"（Modeling Knowledge Governance v1.1 铁律）。

接入点（每项义务带 source_card，MODEL_IR 嵌入时补契约 id）：
- candidates    : 知识卡 → 候选模型提议（family/rationale/knowledge_refs）
- assumptions   : required_conditions/prerequisites → assumptions（type 推断）
- validations   : card.validation → validations（type 推断 + status=required）
- risks         : card.risks → risks（结构化记录 + source_card）
- dependencies  : card.requires → dependencies（from_type=knowledge_card + from_id）
- claim_obligations : 论文投影类义务（评审知识，如摘要/图表）单独归口，
                    不进模型验证义务（验证义务只承载可执行检查）。

边界：
- 知识 = Constraint/Prior；最终由执行/验证裁决（LLM-free 铁律）。
- 无知识不自动判错；knowledge coverage 约束 evaluation 不约束 creativity。
"""

from __future__ import annotations

from typing import Any

# 卡 → 义务目标分类（仅用于把"评审/论文投影"类知识从模型验证义务中分离）
_CLAIM_TARGET_KEYWORDS = ("摘要", "图表", "论文", "评审", "排版")

# validation type 推断关键词（与 model_ir.schema.json validations.type 对齐）
_VALIDATION_TYPE_RULES: list[tuple[tuple[str, ...], str]] = [
    (("敏感性", "扰动", "排序"), "sensitivity"),
    (("收敛", "误差"), "convergence"),
    (("量纲", "约束逐条", "约束", "边界"), "limit"),
    (("复现", "确定性"), "reproducibility"),
]


def _infer_target(text: str) -> str:
    """按内容推断义务目标：claim（论文投影）或 validation（可执行验证）。"""
    return "claim" if any(k in text for k in _CLAIM_TARGET_KEYWORDS) else "validation"


def _infer_validation_type(text: str) -> str:
    for keywords, vtype in _VALIDATION_TYPE_RULES:
        if any(k in text for k in keywords):
            return vtype
    return "constraint"


_CLAIM_CARD_MARKERS = ("judging-criteria", "review", "criteria")


def _is_claim_card(card) -> bool:
    """评审/论文投影类知识卡：整卡义务归口 claim（不进模型验证义务）。

    卡级判定优先于文本推断——评审知识卡（judging-criteria 等）的 validation
    字段本质是论文投影义务（摘要/图表/结论呈现），冒充模型验证义务会产生
    "评审知识→可执行验证"的虚假能力信号。
    """
    cid = str(getattr(card, "card_id", "")).lower()
    return any(m in cid for m in _CLAIM_CARD_MARKERS)


def map_card_obligations_v2(card) -> dict[str, list[dict]]:
    """方法卡 → 分类义务（v2：validation/claim 分离 + type 推断）。

    与 candidates.map_card_obligations 兼容（validations/assumptions/risks/
    dependencies 同形），额外产出 claim_obligations。
    评审知识卡（judging-criteria）整卡归口 claim；其余卡按文本推断。
    """
    validations, claims = [], []
    if _is_claim_card(card):
        claims = [{"obligation": v, "source_card": card.card_id,
                   "type": _infer_validation_type(v)}
                  for v in (card.validation or [])]
    else:
        for v in (card.validation or []):
            (claims if _infer_target(v) == "claim" else validations).append(
                {"obligation": v, "source_card": card.card_id,
                 "type": _infer_validation_type(v)})
    return {
        "validations": validations,
        "claim_obligations": claims,
        "assumptions": [
            {"assumption": a, "source_card": card.card_id}
            for a in ((card.required_conditions or [])
                      + (card.prerequisites or []))],
        "risks": [
            {"source": "knowledge_card", "id": card.card_id,
             "level": "medium", "title": r, "source_card": card.card_id}
            for r in (card.risks or [])],
        "dependencies": list(card.requires or []),
    }


def _dedup(items: list[dict]) -> list[dict]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict] = []
    for it in items:
        key = (it.get("source_card"), it.get("obligation")
               or it.get("assumption") or it.get("title") or str(it))
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


def merge_obligations(base: dict, extra: dict) -> dict:
    """合并两份义务声明（去重保序；validation/claim/assumption/risk/dependency）。"""
    out = dict(base)
    for key in ("validations", "claim_obligations", "assumptions", "risks"):
        out[key] = _dedup(list(base.get(key, [])) + list(extra.get(key, [])))
    out["dependencies"] = list(dict.fromkeys(
        list(base.get("dependencies", [])) + list(extra.get("dependencies", []))))
    return out


def _with_contract_ids(oblig: dict, prefix: str) -> dict:
    """为义务补 MODEL_IR 契约 id（validation_id/assumption_id），幂等。

    职责说明：core 负责机械编号（确定性、可审计）；编号仅为契约标识，
    不承载任何能力判断。
    """
    out = {k: list(v) for k, v in oblig.items()}
    for i, v in enumerate(out.get("validations", []), 1):
        v = dict(v)
        v.setdefault("validation_id", f"{prefix}VAL{i:02d}")
        v.setdefault("status", "required")
        out["validations"][i - 1] = v
    for i, a in enumerate(out.get("assumptions", []), 1):
        a = dict(a)
        a.setdefault("assumption_id", f"{prefix}ASM{i:02d}")
        out["assumptions"][i - 1] = a
    return out


def requires_to_dependencies(cards, model_id: str) -> list[dict]:
    """知识卡 requires → MODEL_IR.dependencies 结构化声明（可溯源）。"""
    deps, i = [], 0
    for c in cards:
        for req in (c.requires or []):
            i += 1
            deps.append({
                "dependency_id": f"DEPKG{i:02d}",
                "from_type": "knowledge_card",
                "from_id": c.card_id,
                "to_type": "model",
                "to_id": model_id,
                "relation": "requires",
                "note": req,
            })
    return deps


def apply_knowledge_obligations(model_ir: dict, cards,
                                model_id: str | None = None) -> dict:
    """把知识卡义务嵌入 MODEL_IR（合并 + 契约 id + dependencies + knowledge_refs）。

    不覆盖建模者已有声明（merge 语义）；不改动 variables/equations/objectives
    （知识只增义务，不代建模）。
    """
    oblig = {"validations": [], "claim_obligations": [],
             "assumptions": [], "risks": [], "dependencies": []}
    for c in cards:
        oblig = merge_obligations(oblig, map_card_obligations_v2(c))
    oblig = _with_contract_ids(oblig, prefix="KG")

    mir = dict(model_ir)
    mir["model_id"] = model_id or mir.get("model_id", "M-KG")
    merged = merge_obligations(
        {"validations": mir.get("validations", []),
         "assumptions": mir.get("assumptions", []),
         "risks": mir.get("risks", []),
         "dependencies": []},
        {k: v for k, v in oblig.items() if k != "claim_obligations"})
    mir["validations"] = merged["validations"]
    mir["assumptions"] = merged["assumptions"]
    mir["risks"] = merged["risks"]
    mir["dependencies"] = list(mir.get("dependencies", [])) \
        + requires_to_dependencies(cards, mir["model_id"])
    mir["knowledge_refs"] = [{"id": c.card_id, "version": c.version}
                             for c in cards]
    return mir


def obligation_provenance(model_ir: dict) -> list[dict]:
    """可审计清单：MODEL_IR 中哪些项来自哪张知识卡。

    返回 [{target, field, card_id, item_id, text}]；无知识来源的项不含 card_id。
    """
    out: list[dict] = []
    for f, id_key, text_key in (
        ("validations", "validation_id", "obligation"),
        ("assumptions", "assumption_id", "assumption"),
        ("risks", "id", "title"),
    ):
        for item in model_ir.get(f, []) or []:
            entry = {"target": f, "field": id_key,
                     "item_id": item.get(id_key), "text": item.get(text_key)}
            sc = item.get("source_card")
            if sc:
                entry["card_id"] = sc
            out.append(entry)
    return out


def build_guided_candidate(model_ir_base: dict, code: str, cards,
                           model_id: str) -> dict:
    """知识引导候选：建模者声明（base）∪ 知识卡义务（去重，带 source_card）。

    返回 {"model_ir": ..., "code": ...}（外部 Model Constructor 可直接注入
    arena / 执行管线）。数值与代码仍由外部提供，本模块只增义务。
    """
    mir = apply_knowledge_obligations(model_ir_base, cards, model_id=model_id)
    return {"model_ir": mir, "code": code}
