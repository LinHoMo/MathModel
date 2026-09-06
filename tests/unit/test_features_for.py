"""P13-1 features_for（Problem→Method 接口）单元测试。

运行: python -m pytest tests/unit/test_features_for.py -q
验证: per_question 覆盖合并 / 缺省回退全局 / 无 per_question 恒等。
Problem Profile 是 Method Retriever 的输入 DTO，不是问题本体——
本测试同时锁住"逐题特征优先"这一唯一语义。
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.handlers import features_for  # noqa: E402


def test_per_question_overrides_global():
    f = {"problem_types": ["evaluation"], "has_data": True,
         "per_question": {"Q001": {"problem_types": ["simulation"],
                                   "uncertainty": True}}}
    qf = features_for(f, "Q001")
    assert qf["problem_types"] == ["simulation"]
    assert qf["uncertainty"] is True
    assert qf["has_data"] is True            # 全局键保留
    # 其他问题不受影响
    assert features_for(f, "Q002")["problem_types"] == ["evaluation"]


def test_fallback_to_global_when_no_profile():
    f = {"problem_types": ["evaluation"], "per_question": {"Q001": {}}}
    assert features_for(f, "Q002") is f       # 恒等：无画像不改对象
    assert features_for(None, "Q001") == {}


def test_dto_is_pass_through():
    """六冻结键之外的 note 等字段透传（DTO 不解释、不扩展语义）。"""
    f = {"per_question": {"Q001": {"note": "生存率拟合", "has_data": True}}}
    qf = features_for(f, "Q001")
    assert qf["note"] == "生存率拟合"
    assert qf["has_data"] is True
