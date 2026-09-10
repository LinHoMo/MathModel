# -*- coding: utf-8 -*-
"""P2-1: Reference Constructor（minimal, LLM-free）。

从 problem features + catalog 方法卡 → 模板 MODEL_IR + 模板代码
（ConstructionBundle，P1-1 协议）。纯规则，无 LLM——作为 Benchmark
的控制组 Constructor（capability C3）。

基底采用 vs001_fixtures.M1_DICT（已通过 MODEL_IR 契约全部校验），
仅替换 family/objective/variables/mechanism 为模板语义。数值正确性由
Runtime 执行闭环裁决（Reference Constructor 不保证数学最优，只保证
契约合规与可执行——这正是"裸 Constructor vs +Runtime"对比的意义）。
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "research" / "P15" / "vs001_run"))
from vs001_fixtures import M1_DICT  # noqa: E402

from modeling_harness.runtime.constructors.protocol import ConstructorAdapter, ConstructionBundle

# 模板代码：确定性线性映射 + 摘要（输出与 MODEL_IR 变量 V001 x_i / V002 y 对齐）
_TEMPLATE_CODE = '''def solve(inputs):
    """Reference Constructor 模板：确定性线性映射 + 摘要。

    输出契约（与 MODEL_IR variables 对齐）:
        x_i    —— 输入数值（首值，缺失时 0.0）
        y      —— 全部输入均值（derived）
        _summary —— n/mean/max
        ok     —— 恒 True（模板保证确定性成功）
    """
    vals = []
    for k, v in inputs.items():
        if k.startswith("_"):
            continue
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            continue
    x_i = vals[0] if vals else 0.0
    y = sum(vals) / len(vals) if vals else 0.0
    return {
        "x_i": x_i,
        "y": y,
        "_summary": {"n": len(vals), "mean": y,
                     "max": max(vals) if vals else 0.0},
        "ok": True,
    }


if __name__ == "__main__":
    import json
    data = json.load(open("input.json", encoding="utf-8"))
    print(json.dumps(solve(data), ensure_ascii=False))
'''

_FAMILY_KEYWORDS = {
    "optimization": ("优化", "规划", "成本", "min", "max", "约束"),
    "statistical_modeling": ("预测", "回归", "统计", "分类", "classification"),
    "numerical_pde": ("微分", "pde", "方程", "偏导"),
}


class ReferenceConstructor(ConstructorAdapter):
    """LLM-free 规则 Constructor（K004 控制组）。"""

    name = "ref"
    capability = "C3"

    def construct(self, problem: dict, context: dict | None = None) -> ConstructionBundle:
        qid = problem.get("question", "Q001")
        statement = problem.get("statement", "") or ""
        features = problem.get("features") or {}
        family = self._infer_family(features, statement)

        mir = copy.deepcopy(M1_DICT)
        mir["model_id"] = f"{qid}-REF-v1"
        mir["problem_id"] = qid
        mir["problem_binding"]["problem_id"] = qid
        mir["problem_binding"]["sub_question_id"] = "Q1"
        mir["model_family"] = {
            "primary": family,
            "secondary": ["deterministic_mapping"],
            "description": f"Reference Constructor 模板（{family}）——{qid}",
        }
        mir["objectives"] = [{
            "objective_id": "O001",
            "type": "simulate",
            "expression": "y = f(x)（确定性映射）",
            "variables_refs": ["V001", "V002"],
            "sub_question_binding": ["Q1"],
            "description": f"模板：对 {qid} 输入做确定性映射与摘要",
        }]
        mir["variables"] = [
            {"variable_id": "V001", "name": "x_i", "symbol": "x_i",
             "definition": "问题输入变量", "unit": "-",
             "type": "observation", "sub_question_binding": ["Q1"]},
            {"variable_id": "V002", "name": "y", "symbol": "y",
             "definition": "映射输出", "unit": "-",
             "type": "derived", "sub_question_binding": ["Q1"]},
        ]
        mir["mechanisms"] = [{
            "mechanism_id": "MECH001",
            "name": "确定性映射",
            "description": "输入到输出的线性映射 + 摘要统计",
            "type": "algebraic",
            "governing_principle": "y_i = x_i",
            "variables_refs": ["V001", "V002"],
            "assumptions_refs": ["A001"],
            "sub_question_binding": ["Q1"],
            "related_equations": ["E001"],
        }]
        mir["equations"] = [{
            "equation_id": "E001",
            "latex": "y_i = x_i",
            "type": "constitutive",
            "variables_refs": ["V001", "V002"],
            "parameters_refs": [],
            "mechanism_ref": "MECH001",
            "sub_question_binding": ["Q1"],
            "derivation_trace": ["mechanism MECH001"],
        }]
        mir["modeling_trace"] = {
            "trace_version": "1.0",
            "generation_order": ["problem_analysis", "template_instantiation"],
            "construction_status": "template_based",
            "version_history": [],
        }

        # 知识卡义务（方法卡 → validation/assumption 合并，source_card 溯源）
        cards = (context or {}).get("cards") or []
        if cards:
            from modeling_harness.runtime.modeling.knowledge_guided import apply_knowledge_obligations
            mir = apply_knowledge_obligations(
                mir, cards, model_id=mir["model_id"])

        return ConstructionBundle(
            question=qid,
            model_ir=mir,
            code=_TEMPLATE_CODE,
            output_mapping={},
            validation_spec={
                "constraint_tolerance": 1e-9,
                "checks": [
                    {"name": "y_output_exists", "kind": "output_field_exists",
                     "path": "y"},
                    {"name": "y_is_numeric", "kind": "output_numeric",
                     "path": "y"},
                    {"name": "ok_flag_true", "kind": "output_equals",
                     "path": "ok", "expect": True},
                ],
                "objective": {"name": "y"},
                "domain": {},
            },
            revision_of=(context or {}).get("revision_of"),
            reasoning_metadata={
                "constructor": "ref",
                "template": "deterministic_mapping_v1",
                "family_inferred": family,
            },
            constructor="ref",
        )

    # ------------------------------------------------ 规则推断

    def _infer_family(self, features: dict, statement: str) -> str:
        problem_types = features.get("problem_types") or []
        text = statement + " " + " ".join(map(str, problem_types))
        for fam, kws in _FAMILY_KEYWORDS.items():
            if any(k in text for k in kws):
                return fam
        return "data_analysis"
