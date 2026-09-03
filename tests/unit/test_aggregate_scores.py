# -*- coding: utf-8 -*-
"""aggregate_scores.py 的单元测试。

锁住三件此前坏掉的事：
  1. work/score_card.json 有了唯一生成者（此前无人产出，只能手写）；
  2. 对抗卡取 final_score 而非 weighted_score（该卡根本没有后者）；
  3. blocking 两路归集后真的能到 verdict（此前聚合卡的 blocking[] 是死数据）。
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import aggregate_scores as AG  # noqa: E402
import score_artifact as SA  # noqa: E402
import weight_profiles as WP  # noqa: E402

SCHEMA = ROOT / "core" / "schemas" / "score_card.schema.json"
REAL = ROOT / "projects" / "cumcm2024a"


# ------------------------------------------------------------------ 构造工具
def _card(scorer, weighted, refs=None, sub=None):
    return {
        "scorer": f"scorer-{scorer}",
        "dimension": f"{scorer}_quality",
        "weight": 0.2,
        "sub_scores": sub or {},
        "weighted_score": weighted,
        "evidence_refs": [f"main.tex:{scorer}"] if refs is None else refs,
        "verdict_contribution": "pass",
    }


def _adv(final=5.5, deductions=(), fail_reason=None, blocking_issues=None):
    """对抗卡与其余 4 张结构不同：没有 weighted_score，只有 base/final_score。"""
    c = {
        "scorer": "scorer-adversarial",
        "dimension": "adversarial_review",
        "weight": 0.15,
        "base_score": 10,
        "deductions": list(deductions),
        "final_score": final,
        "evidence_refs": ["main.tex:24"],
        "skeptic_additions": {"citation_padding_count": 2},
        "verdict_contribution": "fail" if fail_reason else "pass",
    }
    if fail_reason is not None:
        c["fail_reason"] = fail_reason
    if blocking_issues is not None:
        c["blocking_issues"] = blocking_issues
    return c


def _full_set(adv=None):
    return {
        "academic": _card("academic", 7.5),
        "engineering": _card("engineering", 7.2),
        "judge": _card("judge", 6.9),
        "reader": _card("reader", 7.5),
        "adversarial": adv if adv is not None else _adv(),
    }


def _write(proj, cards, weakness=None, topic=None):
    work = proj / "work"
    work.mkdir(parents=True, exist_ok=True)
    for s, c in cards.items():
        (work / f"score_card_{s}.json").write_text(
            json.dumps(c, ensure_ascii=False), encoding="utf-8")
    if weakness is not None:
        (work / "weakness_report.json").write_text(
            json.dumps(weakness, ensure_ascii=False), encoding="utf-8")
    if topic is not None:
        (work / "type_classification.json").write_text(
            json.dumps({"problem_type": topic}, ensure_ascii=False), encoding="utf-8")
    return proj


@pytest.fixture
def proj(tmp_path):
    return _write(tmp_path, _full_set())


# ------------------------------------------------------------------ 取分
def test_adversarial_uses_final_score(proj):
    card, _ = AG.build(proj)
    adv = next(d for d in card["dimensions"] if d["name"] == "scorer-adversarial")
    assert adv["score"] == 5.5, "对抗卡没有 weighted_score，必须取 final_score"


def test_others_use_weighted_score(proj):
    card, _ = AG.build(proj)
    got = {d["name"]: d["score"] for d in card["dimensions"]}
    assert got["scorer-academic"] == 7.5
    assert got["scorer-judge"] == 6.9


def test_score_falls_back_to_sub_scores_mean(tmp_path):
    broken = _card("academic", None)
    broken["sub_scores"] = {"a": {"score": 6}, "b": {"score": 8}}
    _write(tmp_path, _full_set() | {"academic": broken})
    card, notes = AG.build(tmp_path)
    assert next(d for d in card["dimensions"]
                if d["name"] == "scorer-academic")["score"] == 7.0
    assert not any("无可用分数" in n for n in notes), "子项均分应视为有效分数"


# ------------------------------------------------------------------ 权重
def test_type_weights_applied(tmp_path):
    _write(tmp_path, _full_set(), topic="A")
    card, _ = AG.build(tmp_path)
    expected = WP.get_weights("A")
    assert card["topic_type"] == "A"
    assert {d["name"]: d["weight"] for d in card["dimensions"]} == expected
    assert round(sum(expected.values()), 4) == 1.0


def test_fallback_weights_when_topic_unknown(proj):
    card, notes = AG.build(proj)
    assert card["topic_type"] is None
    assert {d["name"]: d["weight"] for d in card["dimensions"]} == AG.FALLBACK_WEIGHTS
    assert any("固定权重" in n for n in notes)


def test_type_override_wins(tmp_path):
    _write(tmp_path, _full_set(), topic="A")
    card, _ = AG.build(tmp_path, type_override="C")
    assert card["topic_type"] == "C"
    assert {d["name"]: d["weight"] for d in card["dimensions"]} == WP.get_weights("C")


def test_weighted_score_is_recomputed_not_trusted(tmp_path):
    """cumcm2024a 的手写卡曾把 weighted_score 写成 7.07，实算是 6.99。"""
    _write(tmp_path, _full_set(), topic="A")
    card, _ = AG.build(tmp_path)
    w = WP.get_weights("A")
    expected = sum(s * w[f"scorer-{k}"] for k, s in
                   [("academic", 7.5), ("engineering", 7.2), ("judge", 6.9),
                    ("reader", 7.5), ("adversarial", 5.5)])
    assert card["weighted_score"] == round(expected, 3)


# ------------------------------------------------------------------ 证据
def test_evidence_joins_refs(proj):
    card, _ = AG.build(proj)
    ev = next(d for d in card["dimensions"] if d["name"] == "scorer-academic")["evidence"]
    assert "main.tex:academic" in ev


def test_evidence_falls_back_to_sub_scores(tmp_path):
    c = _card("reader", 7.0, refs=[],
              sub={"structure_clarity": {"score": 7, "evidence": "章节层次清晰"}})
    _write(tmp_path, _full_set() | {"reader": c})
    card, _ = AG.build(tmp_path)
    ev = next(d for d in card["dimensions"] if d["name"] == "scorer-reader")["evidence"]
    assert "章节层次清晰" in ev, "refs 为空时必须退回子项证据，否则 compute() 会报「无证据」"


# ------------------------------------------------------------------ blocking
def test_blocking_from_fatal_deduction_real_spelling():
    """实产物的字段名：dimension / amount / finding。"""
    adv = _adv(deductions=[
        {"amount": 1.5, "dimension": "internal_contradiction_Skeptic",
         "finding": "摘要 t*=412.83 与结果 360.25 不一致（blocking 级内部矛盾）"},
        {"amount": 0.5, "dimension": "antipatterns", "finding": "创新贡献薄弱"},
    ])
    out = AG.adversarial_blocking(adv)
    assert len(out) == 1, "只有含致命字样的扣分项才升格为 blocking"
    assert out[0]["source"] == "scorer-adversarial/deduction"
    assert "412.83" in out[0]["issue"]


def test_blocking_from_fatal_deduction_doc_spelling():
    """旧文档的字段名：category / points / evidence。漏认这套 = fail-open。"""
    adv = _adv(deductions=[
        {"points": 1.0, "category": "edge_cases",
         "evidence": "致命：模型失效边界未讨论"},
    ])
    out = AG.adversarial_blocking(adv)
    assert len(out) == 1
    assert out[0]["issue"].startswith("致命")


def test_blocking_from_fail_reason():
    adv = _adv(fail_reason="blocking 级内部矛盾 + 引用填充 2 处")
    out = AG.adversarial_blocking(adv)
    assert [b["source"] for b in out] == ["scorer-adversarial/verdict"]


def test_blocking_from_blocking_issues_list():
    adv = _adv(blocking_issues=["edge_cases: 模型失效边界未讨论"])
    out = AG.adversarial_blocking(adv)
    assert len(out) == 1
    assert out[0]["source"] == "scorer-adversarial/blocking_issues"


def test_blocking_from_weakness_hits():
    w = {"counts": {"blocking": 1, "major": 2},
         "hits": [{"id": "skeptic#internal_contradiction", "severity": "blocking",
                   "evidence": "摘要与 all_results.json 数值相差 14.6%",
                   "suggestion": "立即修正摘要数值"},
                  {"id": "antipatterns#15", "severity": "major",
                   "evidence": "灵敏度未覆盖阈值通道"}]}
    out = AG.weakness_blocking(w)
    assert len(out) == 1, "major 不进 blocking"
    assert out[0]["source"] == "weakness-hunter/skeptic#internal_contradiction"
    assert out[0]["action_required"] == "立即修正摘要数值"


def test_blocking_two_paths_merge_and_dedupe(tmp_path):
    adv = _adv(fail_reason="摘要数值与结果不一致（blocking）")
    w = {"counts": {"blocking": 1},
         "hits": [{"id": "skeptic#x", "severity": "blocking", "evidence": "同一处矛盾"}]}
    _write(tmp_path, _full_set(adv=adv), weakness=w)
    card, _ = AG.build(tmp_path)
    sources = [b["source"] for b in card["blocking"]]
    assert sources == ["scorer-adversarial/verdict", "weakness-hunter/skeptic#x"]


def test_dedupe_by_source_and_issue():
    a = {"source": "s", "issue": "i", "severity": "blocking"}
    assert AG.dedupe([a, dict(a), {"source": "s", "issue": "j"}]) == [a, {"source": "s", "issue": "j"}]


def test_missing_weakness_report_is_noted_not_fatal(proj):
    card, notes = AG.build(proj)
    assert card is not None
    assert any("weakness_report" in n for n in notes)


def test_missing_source_card_is_fatal(tmp_path):
    cards = _full_set()
    del cards["judge"]
    _write(tmp_path, cards)
    card, notes = AG.build(tmp_path)
    assert card is None
    assert any("score_card_judge.json" in n for n in notes)


# ------------------------------------------------------------------ verify
def test_compare_clean_after_write(proj, capsys):
    assert AG.main([str(proj)]) == 0
    assert AG.main([str(proj), "--verify"]) == 0
    assert "[PASS]" in capsys.readouterr().out


def test_compare_flags_handwritten_card(tmp_path):
    """cumcm2024a 的手写卡就是这三类偏差同时出现：分数抬高、blocking 清空、无生成者标记。"""
    adv = _adv(final=5.5, deductions=[
        {"amount": 1.5, "dimension": "internal_contradiction_Skeptic",
         "finding": "摘要与结果数值不一致（blocking 级内部矛盾）"}],
        fail_reason="blocking 级内部矛盾 + 引用填充 2 处")
    w = {"counts": {"blocking": 1},
         "hits": [{"id": "skeptic#x", "severity": "blocking", "evidence": "同一处矛盾"}]}
    _write(tmp_path, _full_set(adv=adv), weakness=w)

    AG.main([str(tmp_path)])
    p = tmp_path / "work" / "score_card.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    assert len(d["blocking"]) == 3, "致命扣分项 / fail_reason / weakness 命中三路都该被收进来"
    d["generated_by"] = "hand"
    d["weighted_score"] = 9.9
    d["blocking"] = []
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")

    fresh, _ = AG.build(tmp_path)
    joined = "\n".join(AG.compare(d, fresh))
    assert "疑似手写" in joined
    assert "weighted_score 不一致" in joined
    assert joined.count("blocking 缺失") == 3


def test_compare_flags_stale_card_after_source_update(proj):
    """分卡改过而聚合卡没重跑，必须被判为不一致。"""
    AG.main([str(proj)])
    p = proj / "work" / "score_card_judge.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["weighted_score"] = 4.0
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    assert AG.main([str(proj), "--verify"]) == 1


def test_verify_missing_aggregate_exits_1(proj):
    assert AG.main([str(proj), "--verify"]) == 1


def test_verify_missing_source_card_exits_2(tmp_path):
    _write(tmp_path, {"academic": _card("academic", 7.0)})
    assert AG.main([str(tmp_path), "--verify"]) == 2


def test_cli_writes_card_and_reports(proj, capsys):
    assert AG.main([str(proj)]) == 0
    out = capsys.readouterr().out
    assert "加权均分" in out
    saved = json.loads((proj / "work" / "score_card.json").read_text(encoding="utf-8"))
    assert saved["generated_by"] == "aggregate_scores.py"


def test_cli_json_mode(proj, capsys):
    assert AG.main([str(proj), "--json"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["generated_by"] == "aggregate_scores.py"


def test_cli_nonexistent_project_exits_2(tmp_path):
    assert AG.main([str(tmp_path / "nope")]) == 2


# ------------------------------------------------------------------ schema
def test_generated_card_satisfies_schema_required(proj):
    card, _ = AG.build(proj)
    required = json.loads(SCHEMA.read_text(encoding="utf-8"))["required"]
    missing = [k for k in required if k not in card]
    assert not missing, f"聚合卡缺 schema required 字段: {missing}"
    for d in card["dimensions"]:
        assert set(["name", "score", "weight", "evidence"]) <= set(d)
        assert 0 <= d["score"] <= 10
        assert d["evidence"], "evidence 为空会触发 score_artifact.compute() 的「无证据」告警"


# ------------------------------------------------- score_artifact 侧的消费
def test_merge_blocking_folds_card_into_counts():
    """decide() 只读 weakness.counts.blocking，聚合卡的 blocking[] 此前是死数据。"""
    weakness = {"counts": {"blocking": 0, "major": 1}, "hits": []}
    card_blocking = [{"source": "scorer-adversarial/verdict", "issue": "摘要数值矛盾",
                      "severity": "blocking", "action_required": "修正"}]
    merged_w, merged = SA.merge_blocking(weakness, card_blocking)
    assert merged_w["counts"]["blocking"] == 1
    assert merged == card_blocking
    assert weakness["counts"]["blocking"] == 0, "不得改写传入的 weakness"


def test_merge_blocking_does_not_double_count():
    """聚合卡里已经含 weakness 那一路，合并时必须去重。"""
    weakness = {"counts": {"blocking": 1},
                "hits": [{"id": "skeptic#x", "severity": "blocking", "evidence": "矛盾"}]}
    card_blocking = AG.weakness_blocking(weakness)
    merged_w, merged = SA.merge_blocking(weakness, card_blocking)
    assert len(merged) == 1
    assert merged_w["counts"]["blocking"] == 1


def test_blocking_without_weakness_report_still_blocks():
    """weakness_report 缺失时，对抗卡的 fail 判定此前完全丢失（fail-open）。"""
    merged_w, merged = SA.merge_blocking(None, [{"source": "s", "issue": "i",
                                                 "severity": "blocking",
                                                 "action_required": "a"}])
    assert merged_w["counts"]["blocking"] == 1
    verdict, reason = SA.decide(8.0, 8.0, ["scorer-judge"], merged_w, 6, 4, 1)
    assert verdict == "block"
    assert "1 个阻塞项" in reason


def test_verdict_block_end_to_end(tmp_path, monkeypatch, capsys):
    """分卡 → 聚合 → verdict 全链路：对抗卡 fail 时必须 block，EXIT 2。"""
    adv = _adv(final=5.5, fail_reason="blocking 级内部矛盾（摘要 vs 结果数值不一致）")
    _write(tmp_path, _full_set(adv=adv), topic="A")
    assert AG.main([str(tmp_path)]) == 0
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["score_artifact.py", str(tmp_path), "--json"])
    assert SA.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["verdict"] == "block"
    assert result["topic_type"] == "A"
    assert result["weighted"] == json.loads(
        (tmp_path / "work" / "score_card.json").read_text(encoding="utf-8"))["weighted_score"]


def test_decide_pass_when_no_blocking_and_scores_ok():
    verdict, _ = SA.decide(7.5, 7.0, ["scorer-reader"],
                           {"counts": {"blocking": 0}}, 6, 4, 1)
    assert verdict == "pass"


# ------------------------------------------------------------------ 接线
def test_gate_wires_aggregate_check():
    """gate 的 scorer-adversarial 必须校验聚合卡，否则手写卡又能蒙混过关。"""
    import inspect

    import gate

    fns = gate.GATES[("reviewer", "scorer-adversarial")]
    src = "\n".join(inspect.getsource(f) for f in fns)
    assert "_check_score_card_aggregated" in src


@pytest.mark.skipif(not (REAL / "work" / "score_card_adversarial.json").exists(),
                    reason="cumcm2024a 评分卡未入库")
def test_real_project_aggregate_verifies(capsys):
    """入库的聚合卡必须与入库的 5 张分卡一致——这条一旦红，说明有人手改了卡。"""
    assert AG.main([str(REAL), "--verify"]) == 0
    assert "[PASS]" in capsys.readouterr().out
