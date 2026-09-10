# -*- coding: utf-8 -*-
"""P1-M3 候选竞技场 fixtures（外部 Model Constructor 手写注入，LLM-free）。

候选 A = VS-001 M1（故意错误：ell_body=1.925，数值验证 FAIL）
候选 B = VS-001 M2（修正：ell_body=1.65，数值验证 PASS）
两者为同一问题的并列候选（sibling，非修订关系），各自独立执行/验证。
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))
if str(Path(__file__).resolve().parent.parent / "vs001_run") not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vs001_run"))

from vs001_fixtures import C1_CODE, C2_CODE, M1_DICT, M2_DICT, VALIDATION_SPEC  # noqa: E402,F401

# 候选列表（每个 = {"model_ir": dict, "code": str}）
# 候选 A：约束系数错误（体板间距声明 1.65，实际按 1.925 建模）→ 数值验证 FAIL
# 候选 B：约束系数正确（1.65）→ 数值验证 PASS
CANDIDATES = [
    {"model_ir": M1_DICT, "code": C1_CODE},
    {"model_ir": M2_DICT, "code": C2_CODE},
]

# 期望：chosen = 候选 B 的 model_id（VR 约束违反最小者）
EXPECTED_CHOSEN_MODEL_ID = "M2024A-Q1-v2"
