"""catalog_check 门禁测试：知识卡双向引用闭合 + 软依赖降级可见性。

运行: python -m pytest tests/unit/test_catalog_check.py -q

覆盖两条真实缺口（2026-09-11 修）：
1. 反向引用未闭合 —— runtime 只对 card -> failure 方向 fail-closed，
   failure.applies_to -> card.known_failures 无人校验，导致「写了失败记忆
   但方法卡检索不到」的死知识可以长期存在。
2. schema 层静默降级 —— jsonschema 缺失时第二层直接 return，输出仍为 OK，
   使「schema 全绿」的声明在缺依赖环境下名不副实。
"""

import builtins
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import pytest

from modeling_harness.cli import catalog_check as cc

KNOWLEDGE_ROOT = REPO / "src" / "modeling_harness" / "knowledge"

# 本次回灌的两张失败记忆（2026_B Q1/Q2 重做所得）
NEW_FAILURE_IDS = (
    "fm-interval-parameter-direction",            # 区间参数语义读反
    "fm-conditional-objective-hides-infeasibility",  # 条件期望掩盖不可行
)


# ---------------------------------------------------------------- 工具

def _block_jsonschema(monkeypatch):
    """让 `import jsonschema` 抛 ImportError，模拟缺依赖环境（跨环境稳定）。"""
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "jsonschema":
            raise ImportError("simulated missing jsonschema")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)


def _mini_knowledge(root: Path, card_has_fm: bool) -> None:
    """构造最小知识库：1 张卡 + 1 条失败记忆，可选是否双向闭合。"""
    (root / "methods" / "cards").mkdir(parents=True, exist_ok=True)
    (root / "failures").mkdir(parents=True, exist_ok=True)
    (root / "patterns").mkdir(parents=True, exist_ok=True)

    known = "[fm-demo-a]" if card_has_fm else "[]"
    (root / "methods" / "cards" / "mc-demo.yaml").write_text(
        "card_id: mc-demo\n"
        "name: 演示卡\n"
        "family: demo\n"
        "version: 1\n"
        "problem_types: [demo]\n"
        "good_for: [demo]\n"
        f"known_failures: {known}\n",
        encoding="utf-8")
    (root / "failures" / "fm-demo-a.yaml").write_text(
        "failure_id: fm-demo-a\n"
        "title: 演示失败记忆\n"
        "problem_context: 演示\n"
        "method: 演示\n"
        "modeling_structure: general\n"
        "failure_mode: wrong-usage\n"
        "symptom: 演示\n"
        "root_cause: 演示\n"
        "detection: 演示\n"
        "fix: 演示\n"
        "avoidance: 演示\n"
        "applies_to: [mc-demo]\n",
        encoding="utf-8")


# ---------------------------------------------------------------- 真实知识库

class TestReverseClosure:
    """failure.applies_to 与 card.known_failures 必须双向一致。"""

    def test_real_library_is_bidirectionally_closed(self):
        problems = cc.check_knowledge_cards()
        rev = [p for p in problems if "反向引用未闭合" in p]
        assert not rev, "真实知识库存在反向引用断裂:\n" + "\n".join(rev)

    def test_new_failure_cards_are_reachable(self):
        """新写的失败记忆必须至少被一张方法卡检索到，否则是死知识。"""
        from modeling_harness.runtime.knowledge.cards import load_knowledge
        cards, failures, _ = load_knowledge(KNOWLEDGE_ROOT)
        for fid in NEW_FAILURE_IDS:
            assert fid in failures, f"失败记忆缺失: {fid}"
            targets = failures[fid].applies_to
            assert targets, f"{fid} 未声明 applies_to"
            for cid in targets:
                assert fid in cards[cid].known_failures, (
                    f"{fid} 声明适用于 {cid}，但 {cid} 未将其列入 known_failures")

    def test_bearing_card_absorbs_new_failures(self):
        """2026_B 的教训必须落进测向交会卡的消费面（否则重跑不会触发）。"""
        from modeling_harness.runtime.knowledge.cards import load_knowledge
        cards, _, _ = load_knowledge(KNOWLEDGE_ROOT)
        card = cards["mc-bearing-triangulation"]
        for fid in NEW_FAILURE_IDS:
            assert fid in card.known_failures, f"测向交会卡未吸收 {fid}"
        # 可行性优先与三档语义须进入验证清单
        assert any("可行集" in v for v in card.validation)
        assert any("区间参数" in v for v in card.validation)


# ---------------------------------------------------------------- 门禁活性

class TestGateIsAlive:
    """证明门禁能抓到问题（不是恒绿的空壳）。"""

    def test_detects_broken_reverse_reference(self, tmp_path, monkeypatch):
        _mini_knowledge(tmp_path, card_has_fm=False)
        monkeypatch.setattr(cc, "KNOWLEDGE_ROOT", tmp_path)
        problems = cc.check_knowledge_cards()
        rev = [p for p in problems if "反向引用未闭合" in p]
        assert len(rev) == 1, f"应报 1 条反向断裂，实际: {problems}"
        assert "fm-demo-a" in rev[0] and "mc-demo" in rev[0]

    def test_closed_library_has_no_reverse_problem(self, tmp_path, monkeypatch):
        _mini_knowledge(tmp_path, card_has_fm=True)
        monkeypatch.setattr(cc, "KNOWLEDGE_ROOT", tmp_path)
        problems = cc.check_knowledge_cards()
        rev = [p for p in problems if "反向引用未闭合" in p]
        assert not rev, f"已闭合却仍报错: {rev}"


# ---------------------------------------------------------------- 降级可见性

class TestDegradationVisibility:
    """软依赖缺失时不得静默——必须进 warnings 并可被 --strict 升级为失败。"""

    def test_missing_jsonschema_warns_instead_of_silent_ok(self, monkeypatch):
        _block_jsonschema(monkeypatch)
        warnings: list[str] = []
        problems = cc.check_knowledge_cards(warnings)
        assert not any("反向引用未闭合" in p for p in problems)
        assert len(warnings) == 1, f"应恰好 1 条降级警告，实际: {warnings}"
        assert "jsonschema" in warnings[0]
        assert "schema" in warnings[0]

    def test_degradation_is_not_a_problem_by_default(self, monkeypatch):
        """ADR-0004 软依赖语义：缺包不应让默认 CI 失败。"""
        _block_jsonschema(monkeypatch)
        assert cc.check_knowledge_cards([]) == []

    def test_strict_promotes_warning_to_failure(self, monkeypatch, capsys):
        _block_jsonschema(monkeypatch)
        monkeypatch.setattr(sys, "argv", ["catalog_check", "--strict"])
        rc = cc.main()
        assert rc == 1, "--strict 下降级必须导致 EXIT 1"
        out = capsys.readouterr().out
        assert "FAIL" in out

    def test_default_mode_still_exits_zero_with_warning(self, monkeypatch, capsys):
        _block_jsonschema(monkeypatch)
        monkeypatch.setattr(sys, "argv", ["catalog_check"])
        rc = cc.main()
        assert rc == 0, "默认模式不得因缺包失败"
        out = capsys.readouterr().out
        assert "WARN" in out, "降级警告必须被打印，不得静默"

    def test_warnings_absent_when_schema_layer_runs(self):
        """有 jsonschema 时 schema 层真跑过，不应有降级警告。"""
        pytest.importorskip("jsonschema")
        warnings: list[str] = []
        cc.check_knowledge_cards(warnings)
        assert not warnings, f"schema 层已执行却仍报降级: {warnings}"
