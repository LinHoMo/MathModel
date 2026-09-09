# -*- coding: utf-8 -*-
"""P1-M4 知识义务映射单测：方法卡 → 候选义务声明（机械映射，可溯源）。

覆盖：
- map_card_obligations：card.validation/required_conditions+prerequisites/risks/requires
  → 候选 validations/assumptions/risks/dependencies（每项带 source_card）
- _merge_obligations 去重合并
- generate_candidates 为每个候选填充义务（P8-4 候选构造路径）
- BZD 试点卡：5 张落盘、yaml 合法、source_type=BZD、被 retriever 可检索

运行: py -3.12 -m pytest tests/runtime/test_knowledge_obligation_mapping.py -q
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest  # noqa: E402

from runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402
from runtime.modeling.candidates import (CandidateArena,  # noqa: E402
                                         _merge_obligations,
                                         map_card_obligations)

KNOWLEDGE_ROOT = REPO / "core" / "knowledge"
BZD_CARD_IDS = [
    "mc-bzd-model-fit",
    "mc-bzd-failure-modes",
    "mc-bzd-validation-obligations",
    "mc-bzd-judging-criteria",
    "mc-bzd-sensitivity",
]


@pytest.fixture()
def retriever():
    return KnowledgeRetriever(KNOWLEDGE_ROOT)


def test_bzd_cards_loaded_and_sourced(retriever):
    """验收②：BZD 试点卡 5 张落盘、yaml 合法、source_type=BZD、可检索。"""
    for cid in BZD_CARD_IDS:
        card = retriever.cards[cid]
        assert card.source_type == "BZD", cid
        assert card.requires and card.risks and card.validation, \
            f"{cid}: 须有 requires/risks/validation 字段（供映射消费）"
    # 检索：features 含 knowledge_guide → 全部 BZD 卡可命中
    recs = retriever.recommend({"problem_types": ["knowledge_guide"]}, top_k=10)
    hit = {r.card.card_id for r in recs}
    assert set(BZD_CARD_IDS) <= hit, set(BZD_CARD_IDS) - hit


def test_map_card_obligations_source_card(retriever):
    """验收①：映射义务每项带 source_card，可溯源到 card_id。"""
    card = retriever.cards["mc-bzd-validation-obligations"]
    oblig = map_card_obligations(card)

    assert oblig["validations"], "validation 义务非空"
    for v in oblig["validations"]:
        assert v["source_card"] == card.card_id
        assert v["obligation"]
    for a in oblig["assumptions"]:
        assert a["source_card"] == card.card_id
        assert a["assumption"]
    for r in oblig["risks"]:
        assert r["source_card"] == card.card_id
        assert r["title"]
    # requires → dependencies（保序）
    assert oblig["dependencies"] == list(card.requires)


def test_map_card_obligations_assumptions_from_conditions(retriever):
    """required_conditions + prerequisites → assumptions。"""
    card = retriever.cards["mc-bzd-model-fit"]
    oblig = map_card_obligations(card)
    assert len(oblig["assumptions"]) == len(card.required_conditions) \
        + len(card.prerequisites)


def test_merge_obligations_dedup():
    """合并去重：同 (source_card, 文本) 只保留一项，dependencies 保序去重。"""
    a = {"validations": [{"obligation": "v1", "source_card": "c1"}],
         "assumptions": [], "risks": [], "dependencies": ["d1", "d2"]}
    b = {"validations": [{"obligation": "v1", "source_card": "c1"},
                         {"obligation": "v2", "source_card": "c2"}],
         "assumptions": [], "risks": [], "dependencies": ["d2", "d3"]}
    merged = _merge_obligations(a, b)
    assert [v["obligation"] for v in merged["validations"]] == ["v1", "v2"]
    assert merged["dependencies"] == ["d1", "d2", "d3"]


def test_generate_candidates_populates_obligations(retriever):
    """验收①：generate_candidates 产出的候选带方法卡义务（BZD 卡为 matched card）。"""
    features = {"problem_types": ["knowledge_guide"], "has_data": True}
    arena = CandidateArena(retriever)
    cands = arena.generate_candidates("Q", features, top_cards=1)
    assert cands, "应生成 ≥1 候选"
    for c in cands:
        assert c.validations, "候选必须带 validations 义务"
        ref_ids = {ref.get("id") for ref in c.knowledge_refs}
        assert ref_ids, "knowledge_refs 非空（可溯源）"
        # 义务 source_card 必须落在 knowledge_refs 引用的卡片内（hybrid 含次优卡）
        for v in c.validations:
            assert v["source_card"] in ref_ids, (v, ref_ids)
        for r in c.risks:
            if r.get("source_card"):
                assert r["source_card"] in ref_ids
        # 主方法卡 requires → dependencies（hybrid 为多卡并集，用超集断言）
        assert set(c.dependencies) >= set(retriever.cards[c.base_card].requires)
        assert c.base_card in ref_ids


def test_bzd_cards_do_not_pollute_other_queries(retriever):
    """BZD 卡不干扰既有检索（独立 problem_types 命名空间）。"""
    recs = retriever.recommend({"problem_types": ["evaluation"]}, top_k=10)
    assert not any(r.card.card_id.startswith("mc-bzd-") for r in recs)
