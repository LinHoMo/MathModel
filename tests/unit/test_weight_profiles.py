# -*- coding: utf-8 -*-
"""题型差异化评审权重：weight_profiles.get_weights + score_artifact.compute 接线测试。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import weight_profiles as WP  # noqa: E402
import score_artifact as SA  # noqa: E402


def test_get_weights_normalized():
    """每种题型的权重归一化（sum≈1.0），且 5 评分员齐全。"""
    for pt in ["A", "B", "C", "D", "E", "MCM", "ICM"]:
        w = WP.get_weights(pt)
        assert set(w) == {
            "scorer-academic", "scorer-engineering",
            "scorer-judge", "scorer-reader", "scorer-adversarial",
        }, f"{pt} 缺评分员"
        assert abs(sum(w.values()) - 1.0) < 1e-3, f"{pt} 权重未归一化: {sum(w.values())}"


def test_get_weights_type_differentiated():
    """不同题型应产生不同权重（非固定）。"""
    wa = WP.get_weights("A")
    wc = WP.get_weights("C")
    wm = WP.get_weights("MCM")
    assert wa != wc, "A/C 题权重应不同"
    # C 题（数据）学术权重应高于工程权重
    assert wc["scorer-academic"] > wc["scorer-engineering"]
    # MCM 可读性被最高乘子拉高：reader 应高于 engineering（被降权）
    assert wm["scorer-reader"] > wm["scorer-engineering"]


def _dims():
    """新 5 评分员命名的 score_card 维度。"""
    return [
        {"name": "scorer-academic", "score": 8, "weight": 0.25, "evidence": "推导完整"},
        {"name": "scorer-engineering", "score": 6, "weight": 0.20, "evidence": "代码可复现"},
        {"name": "scorer-judge", "score": 7, "weight": 0.25, "evidence": "有创新点"},
        {"name": "scorer-reader", "score": 7, "weight": 0.15, "evidence": "图表清晰"},
        {"name": "scorer-adversarial", "score": 6, "weight": 0.15, "evidence": "边界已测"},
    ]


def test_compute_without_type_weights_uses_self_weights():
    """无题型权重时，沿用维度自带权重（向后兼容，且不被 [0.7,1.5] 误夹紧）。"""
    dims = [
        {"name": "问题理解", "score": 8, "weight": 1.0, "evidence": "x"},
        {"name": "模型建立", "score": 7, "weight": 1.2, "evidence": "x"},
    ]
    weighted, _, _, issues = SA.compute(dims, 6, None)
    # 1.0/1.2 都在 [0.7,1.5] 内，不应产生夹紧告警
    assert not any("夹紧" in i for i in issues)
    assert weighted == (8 * 1.0 + 7 * 1.2) / (1.0 + 1.2)


def test_compute_with_type_weights_overrides_mapped_dims():
    """题型权重覆盖能映射到 5 评分员的维度，且不触发 [0.7,1.5] 夹紧。"""
    dims = _dims()
    wc = WP.get_weights("C")
    weighted, _, _, issues = SA.compute(dims, 6, None, type_weights=wc)
    # 归一化权重（各 0.15~0.30）不应被误判为超范围
    assert not any("夹紧" in i for i in issues), issues
    ws = [wc[_scorer_of(d["name"])] for d in dims]
    expected = sum(d["score"] * w for d, w in zip(dims, ws)) / sum(ws)
    assert abs(weighted - expected) < 1e-9


def test_compute_type_weights_ignore_unmapped_dims():
    """无法映射到 5 评分员的维度仍用自带权重（旧 8 维兼容，不报错）。"""
    wc = WP.get_weights("A")
    dims = [
        {"name": "scorer-academic", "score": 8, "weight": 0.25, "evidence": "x"},
        {"name": "规范与合规", "score": 6, "weight": 1.0, "evidence": "x"},  # 无法映射
    ]
    weighted, _, _, issues = SA.compute(dims, 6, None, type_weights=wc)
    # 只有 scorer-academic 用题型权重；规范与合规 用自带 1.0
    assert weighted is not None


def _scorer_of(name):
    return SA._scorer_key(name)


def test_scorer_key_mapping():
    assert SA._scorer_key("scorer-academic") == "scorer-academic"
    assert SA._scorer_key("scorer-ENGINEERING") == "scorer-engineering"
    assert SA._scorer_key("规范与合规") is None


def test_resolve_topic_type(tmp_path):
    base = tmp_path / "demo"
    (base / "work").mkdir(parents=True)
    (base / "work" / "question_spec.json").write_text(
        '{"metadata": {"contest": "CUMCM"}}', encoding="utf-8")
    (base / "work" / "type_classification.json").write_text(
        '{"problem_type": "C"}', encoding="utf-8")
    assert SA._resolve_topic_type(base) == "C"

    # MCM 覆盖优先于 problem_type
    (base / "work" / "question_spec.json").write_text(
        '{"metadata": {"contest": "MCM"}}', encoding="utf-8")
    assert SA._resolve_topic_type(base) == "MCM"
