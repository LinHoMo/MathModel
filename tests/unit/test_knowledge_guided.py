# -*- coding: utf-8 -*-
"""knowledge_guided 正式模块单元测试（LLM-free 机械映射）。"""

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from modeling_harness.runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402
from modeling_harness.runtime.modeling import knowledge_guided as kg  # noqa: E402

_CARDS_DIR = _REPO / "src" / "modeling_harness" / "knowledge"


@pytest.fixture(scope="module")
def retriever() -> KnowledgeRetriever:
    return KnowledgeRetriever(_CARDS_DIR)


def _card(retriever, cid: str):
    return retriever.cards[cid]


def test_map_card_obligations_v2_validation_split(retriever):
    """judging-criteria（摘要/图表）→ claim；model-fit → validation。"""
    judge = kg.map_card_obligations_v2(_card(retriever, "mc-bzd-judging-criteria"))
    fit = kg.map_card_obligations_v2(_card(retriever, "mc-bzd-model-fit"))
    assert all(o["source_card"] == "mc-bzd-judging-criteria"
               for o in judge["claim_obligations"])
    assert judge["validations"] == []
    assert fit["validations"], "model-fit 应产出验证义务"
    assert all(o["source_card"] == "mc-bzd-model-fit" for o in fit["validations"])


def test_validation_type_inference(retriever):
    """type 推断：敏感性→sensitivity、量纲/约束→limit、误差/收敛→convergence。"""
    sens = _card(retriever, "mc-bzd-sensitivity")
    obl = kg.map_card_obligations_v2(sens)
    assert all(v["type"] == "sensitivity" for v in obl["validations"])
    fail = kg.map_card_obligations_v2(_card(retriever, "mc-bzd-failure-modes"))
    types = {v["type"] for v in fail["validations"]}
    assert "limit" in types  # 量纲一致性/约束逐条


def test_apply_knowledge_obligations_embeds_provenance(retriever):
    cards = [_card(retriever, "mc-bzd-model-fit"),
             _card(retriever, "mc-bzd-validation-obligations")]
    base = {
        "model_id": "M0", "validations": [], "assumptions": [],
        "risks": [], "dependencies": [],
    }
    mir = kg.apply_knowledge_obligations(base, cards, model_id="M-KG-TEST")
    assert mir["model_id"] == "M-KG-TEST"
    assert len(mir["validations"]) >= 2
    assert len(mir["assumptions"]) >= 1
    assert all(v.get("source_card") for v in mir["validations"])
    assert all(v.get("validation_id", "").startswith("KG") for v in mir["validations"])
    assert all(v.get("status") == "required" for v in mir["validations"])
    assert any(d.get("from_type") == "knowledge_card"
               for d in mir["dependencies"])
    assert {"id": "mc-bzd-model-fit", "version": cards[0].version} \
        in mir["knowledge_refs"]


def test_apply_does_not_overwrite_existing_declarations(retriever):
    """知识只增义务，不覆盖建模者已有声明（merge 语义）。"""
    cards = [_card(retriever, "mc-bzd-model-fit")]
    existing = {
        "model_id": "M0", "validations": [{
            "validation_id": "V0", "obligation": "建模者自声明验证",
            "source_card": "modeler", "status": "required"}],
        "assumptions": [{"assumption_id": "A0",
                         "assumption": "建模者自声明假设", "source_card": "modeler"}],
        "risks": [], "dependencies": [],
    }
    mir = kg.apply_knowledge_obligations(existing, cards, model_id="M0")
    vids = [v["validation_id"] for v in mir["validations"]]
    assert "V0" in vids  # 保留建模者声明
    assert any(v.get("source_card") == "mc-bzd-model-fit" for v in mir["validations"])


def test_obligation_provenance_lists_source_cards(retriever):
    cards = [_card(retriever, "mc-bzd-model-fit"),
             _card(retriever, "mc-bzd-sensitivity")]
    mir = kg.apply_knowledge_obligations(
        {"model_id": "M0", "validations": [], "assumptions": [],
         "risks": [], "dependencies": []},
        cards, model_id="M0")
    prov = kg.obligation_provenance(mir)
    assert prov
    cards_in_prov = {e["card_id"] for e in prov if "card_id" in e}
    assert "mc-bzd-model-fit" in cards_in_prov
    assert "mc-bzd-sensitivity" in cards_in_prov
    # 每一项都应有 item_id 与文本
    assert all(e.get("item_id") for e in prov)
    assert all(e.get("text") for e in prov)


def test_no_cards_no_op(retriever):
    """无卡：apply 不改变义务（知识缺失不阻断、不编造）。"""
    base = {"model_id": "M0", "validations": [], "assumptions": [],
            "risks": [], "dependencies": []}
    mir = kg.apply_knowledge_obligations(base, [], model_id="M0")
    assert mir["validations"] == []
    assert mir["assumptions"] == []
    assert mir["knowledge_refs"] == []


def test_build_guided_candidate_shape(retriever):
    """引导候选：{model_ir, code} 形状 + 义务嵌入。"""
    cards = [_card(retriever, "mc-bzd-validation-obligations")]
    cand = kg.build_guided_candidate(
        {"model_id": "M0", "validations": [], "assumptions": [],
         "risks": [], "dependencies": []},
        "def solve(inputs): return {'ok': True}",
        cards, model_id="M-GUIDED")
    assert set(cand) == {"model_ir", "code"}
    assert cand["model_ir"]["model_id"] == "M-GUIDED"
    assert cand["model_ir"]["validations"]


def test_judging_criteria_not_in_model_validations(retriever):
    """judging-criteria 义务不进模型验证义务（论文投影归口）。"""
    cards = [_card(retriever, "mc-bzd-judging-criteria")]
    mir = kg.apply_knowledge_obligations(
        {"model_id": "M0", "validations": [], "assumptions": [],
         "risks": [], "dependencies": []},
        cards, model_id="M0")
    assert mir["validations"] == []  # 摘要/图表类义务被归口 claim，不冒充验证
