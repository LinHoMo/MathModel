"""P2 Failure Memory 测试：结构化字段 / 溯源 / 与方法卡的关联。

运行: python -m pytest tests/unit/test_failure_memory.py -q
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.knowledge.cards import CardError, FailureMemory, load_knowledge

KNOWLEDGE_ROOT = REPO / "core" / "knowledge"


@pytest.fixture(scope="module")
def knowledge():
    return load_knowledge(KNOWLEDGE_ROOT)


class TestFailureLibrary:
    def test_all_failures_structured(self, knowledge):
        cards, failures, _ = knowledge
        assert len(failures) >= 8
        for fm in failures.values():
            assert fm.failure_id.startswith("fm-")
            # 结构化八要素全部非空（区别于散文式 md 案例）
            for field in ("problem_context", "method", "failure_mode", "symptom",
                          "root_cause", "detection", "fix", "avoidance"):
                assert getattr(fm, field), f"{fm.failure_id} 缺 {field}"

    def test_failure_mode_enum(self, knowledge):
        valid = {"wrong-method", "wrong-usage", "no-evidence", "overclaim",
                 "presentation", "numerical", "consistency"}
        for fm in knowledge[1].values():
            assert fm.failure_mode in valid

    def test_negative_case_distillation(self, knowledge):
        """_negative/ 散文案例已蒸馏为结构化记忆并标注溯源。"""
        failures = knowledge[1]
        by_source = [f for f in failures.values()
                     if f.source.startswith("_negative/")]
        assert len(by_source) >= 3, "至少 3 条失败记忆应溯源到 _negative/ 案例"

    def test_distilled_from_real_negative_cases(self, knowledge):
        failures = knowledge[1]
        assert "fm-small-sample-deep-learning" in failures
        assert "fm-heuristic-global-optimum-claim" in failures
        assert "fm-perfect-fit-zero-error" in failures

    def test_every_card_known_failure_resolves(self, knowledge):
        cards, failures, _ = knowledge
        for card in cards.values():
            for fid in card.known_failures:
                assert fid in failures, \
                    f"{card.card_id} 引用的失败 {fid} 不存在"

    def test_pitfall_numeric_edge_distilled(self, knowledge):
        """pitfalls/numeric-edge-cases.md 的数值边界已蒸馏。"""
        failures = knowledge[1]
        assert "fm-entropy-identical-columns" in failures
        assert "fm-topsis-no-normalization" in failures


class TestFailureContract:
    def _mk_dir(self, tmp_path, content):
        d = tmp_path / "failures"
        d.mkdir(parents=True)
        (d / "bad.yaml").write_text(content, encoding="utf-8")

    BASE = ("failure_id: fm-bad\ntitle: t\nproblem_context: c\nmethod: m\n"
            "method_family: f\nfailure_mode: {mode}\nsymptom: s\n"
            "root_cause: r\ndetection: d\nfix: f\navoidance: a\n")

    def test_bad_failure_mode_rejected(self, tmp_path):
        self._mk_dir(tmp_path, self.BASE.format(mode="mystery-mode"))
        with pytest.raises(CardError, match="failure_mode"):
            load_knowledge(tmp_path)

    def test_missing_field_rejected(self, tmp_path):
        content = self.BASE.format(mode="numerical").replace("detection: d\n", "")
        self._mk_dir(tmp_path, content)
        with pytest.raises(CardError, match="detection"):
            load_knowledge(tmp_path)

    def test_bad_id_rejected(self, tmp_path):
        content = self.BASE.format(mode="numerical").replace(
            "failure_id: fm-bad", "failure_id: BAD_ID")
        self._mk_dir(tmp_path, content)
        with pytest.raises(CardError, match="fm-"):
            load_knowledge(tmp_path)

    def test_applies_to_dangling_card(self, tmp_path):
        content = self.BASE.format(mode="numerical") + \
            "applies_to: [mc-ghost]\n"
        self._mk_dir(tmp_path, content)
        with pytest.raises(CardError, match="mc-ghost"):
            load_knowledge(tmp_path)


class TestPatternLibrary:
    def test_patterns_have_required_evidence(self, knowledge):
        for pat in knowledge[2].values():
            assert pat.pattern_id.startswith("ip-")
            assert pat.baseline_method and pat.innovation
            assert pat.required_evidence, \
                f"{pat.pattern_id} 缺 required_evidence（创新必须可验证）"
            assert pat.risks, f"{pat.pattern_id} 缺 risks（防为创新而创新）"

    def test_pattern_cards_resolve(self, knowledge):
        cards, _, patterns = knowledge
        for pat in patterns.values():
            for cid in pat.cards:
                assert cid in cards, \
                    f"{pat.pattern_id} 引用不存在的方法卡 {cid}"

    def test_expected_patterns(self, knowledge):
        expected = {"ip-combined-weighting", "ip-mechanism-data-hybrid",
                    "ip-cluster-then-model", "ip-pareto-select",
                    "ip-uncertainty-overlay", "ip-two-stage-evaluation"}
        assert expected <= set(knowledge[2])
