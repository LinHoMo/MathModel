# -*- coding: utf-8 -*-
"""迁移 m4_fixtures 到正式模块 knowledge_guided（保持候选形状兼容）。"""
from pathlib import Path

p = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\m4_run\m4_fixtures.py")
s = p.read_text(encoding="utf-8")

REPLACEMENTS = []

# 1) import 替换
REPLACEMENTS.append((
    "from modeling_harness.runtime.modeling.candidates import _merge_obligations, map_card_obligations  # noqa: E402",
    "from modeling_harness.runtime.modeling.knowledge_guided import requires_to_dependencies  # noqa: E402",
))

# 2) _requires_to_dependencies 函数体委托
old_fn_start = s.index("def _requires_to_dependencies(cards, model_id: str) -> list[dict]:")
old_fn_end = s.index("def _with_ids(oblig: dict) -> dict:")
new_fn = (
    "def _requires_to_dependencies(cards, model_id: str) -> list[dict]:\n"
    '    """方法卡 requires → MODEL_IR.dependencies 结构化声明（正式模块委托）。"""\n'
    "    return requires_to_dependencies(cards, model_id)\n\n\n"
)
s = s[:old_fn_start] + new_fn + s[old_fn_end:]

# 3) build_guided_candidate 函数体委托
old_fn_start = s.index("def build_guided_candidate() -> dict:")
old_fn_end = s.index("def build_unguided_candidate() -> dict:")
new_fn = (
    "def build_guided_candidate() -> dict:\n"
    '    """知识引导候选：建模者自身声明（M2 基线）∪ BZD 卡义务（正式模块嵌入）。"""\n'
    "    from modeling_harness.runtime.modeling.knowledge_guided import apply_knowledge_obligations\n"
    "    cards = bzd_cards()\n"
    "    mir = dict(M2_DICT)\n"
    '    mir["model_id"] = GUIDED_MODEL_ID\n'
    "    # FIX-3.1（audit P1-03/P1-09）：多候选竞技场中 implementation_ref 指向\n"
    "    # 候选自身的 model_id（registry 按创建顺序分配 CODE001/CODE002 编号，\n"
    "    # 外部声明的实现引用以 model_id 为稳定标识，避免与内部编号错位）。\n"
    '    mir["solvers"] = [dict(s, implementation_ref=GUIDED_MODEL_ID)\n'
    "                      for s in mir.get(\"solvers\") or []]\n"
    "    mir = apply_knowledge_obligations(mir, cards, model_id=GUIDED_MODEL_ID)\n"
    '    return {"model_ir": mir, "code": C2_CODE}\n\n\n'
)
s = s[:old_fn_start] + new_fn + s[old_fn_end:]

p.write_text(s, encoding="utf-8")
print("m4_fixtures migrated OK")
