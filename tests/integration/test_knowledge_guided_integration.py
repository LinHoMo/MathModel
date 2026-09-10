# -*- coding: utf-8 -*-
"""P1-2 验收：Knowledge Guided Construction 接入生产路径。

验收语义（ROADMAP P1-2）：
  * shared["knowledge_guide"][qid] 配置知识卡 → 外部 MODEL_IR 登记时嵌入
    知识卡义务：validations 带 source_card 溯源 + knowledge_refs
  * 不覆盖建模者已有声明（merge 语义）
  * 默认关闭（无配置 → 行为不变）
  * 全闭环仍跑通（知识引导不破坏执行/验证）
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "tests" / "integration"))

from _real_session import MINIMAL_VALIDATION_SPEC, _minimal_mir  # noqa: E402

from runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402

OK_CODE = """def solve(inputs):
    a = float(inputs["a"]); x = float(inputs["x"]); b = float(inputs["b"])
    return {"y": a * x + b, "ok": True}


if __name__ == "__main__":
    import json
    data = json.load(open("input.json", encoding="utf-8"))
    print(json.dumps(solve(data), ensure_ascii=False))
"""

LOOP_NODES = [
    "problem_analysis", "literature_search", "model_selection",
    "model_construction", "model_critique", "assumption_check",
    "code_generation", "model_execution", "model_validation",
]

# BZD 试点卡（存在 core/knowledge/methods/cards/mc-bzd-*.yaml）
GUIDE_CARDS = ["mc-bzd-model-fit", "mc-bzd-validation-obligations"]


def _session(tmp_path, guide=None):
    s = RuntimeSession(
        Path(tmp_path) / "proj", ["Q001"], max_workers=1,
        execution_adapter=LocalPythonAdapter(),
        external_model_irs={"Q001": _minimal_mir("Q001")},
        external_code={"Q001": OK_CODE},
        validation_specs={"Q001": dict(MINIMAL_VALIDATION_SPEC)})
    if guide is not None:
        s.executor_impl.shared["knowledge_guide"] = {"Q001": guide}
    return s


def _step(session):
    results = {}
    for nid in LOOP_NODES:
        results[nid] = session.engine.step(nid)
    return results


def _mirs(session):
    return [a for a in session.registry.list_by_type("model_ir")]


class TestKnowledgeGuidedConstruction:
    """P1-2 验收。"""

    def test_default_off_unchanged(self, tmp_path):
        """无 knowledge_guide 配置 → MODEL_IR 原样登记（无 knowledge_refs）。"""
        s = _session(tmp_path)
        _step(s)
        mir = _mirs(s)[0].data or {}
        assert not mir.get("knowledge_refs"), "默认关闭不应有知识溯源"
        assert not mir.get("_knowledge_guided")

    def test_guide_embeds_sourced_obligations(self, tmp_path):
        """配置知识卡 → validations 带 source_card 溯源 + knowledge_refs。"""
        s = _session(tmp_path, guide=GUIDE_CARDS)
        _step(s)
        mir = _mirs(s)[0].data or {}
        assert mir.get("knowledge_refs"), "知识引导后必须有 knowledge_refs"
        assert mir.get("_knowledge_guided"), "必须标记知识引导"
        sourced = [v for v in (mir.get("validations") or [])
                   if v.get("source_card")]
        assert sourced, "validations 必须含 source_card 溯源的义务"
        cards = {r["id"] for r in mir["knowledge_refs"]}
        assert GUIDE_CARDS[0] in cards

    def test_does_not_overwrite_modeler_declarations(self, tmp_path):
        """知识引导 merge 语义：不覆盖建模者已有 validations。"""
        base = _minimal_mir("Q001")
        base["validations"] = [{
            "validation_id": "VUSER1",
            "type": "constraint",
            "method": "建模者声明",
            "status": "required",
            "targets_refs": [],
        }] + list(base.get("validations") or [])
        s = RuntimeSession(
            Path(tmp_path) / "proj", ["Q001"], max_workers=1,
            execution_adapter=LocalPythonAdapter(),
            external_model_irs={"Q001": base},
            external_code={"Q001": OK_CODE},
            validation_specs={"Q001": dict(MINIMAL_VALIDATION_SPEC)})
        s.executor_impl.shared["knowledge_guide"] = {"Q001": GUIDE_CARDS}
        _step(s)
        mir = _mirs(s)[0].data or {}
        ids = [v.get("validation_id") for v in mir.get("validations") or []]
        assert "VUSER1" in ids, "建模者声明不得被覆盖"
        assert any(v.get("source_card") for v in mir.get("validations") or [])

    def test_full_loop_still_green_with_guide(self, tmp_path):
        """知识引导后执行/验证闭环仍跑通（义务嵌入不破坏能力链）。"""
        s = _session(tmp_path, guide=GUIDE_CARDS)
        results = _step(s)
        assert results["model_execution"].status == "pass"
        assert results["model_validation"].status == "pass"
