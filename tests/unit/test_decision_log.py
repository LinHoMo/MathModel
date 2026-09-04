"""P2 Decision Log 测试：登记校验 / 自动 ID / 失效与降权 / 检索 / 持久化。

运行: python -m pytest tests/unit/test_decision_log.py -q
覆盖任务书 Decision Log 升级要求:
reversible / invalidated_by / consequences / criteria / evidence_ids + 检索降权。
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.decisions.log import Decision, DecisionLog, DecisionLogError


@pytest.fixture
def log(tmp_path):
    return DecisionLog(tmp_path / "decisions.json")


def _add(dlog, **kw):
    params = dict(
        question="Q001 评价方法选型",
        chosen="mc-topsis + mc-entropy-weight",
        alternatives=["mc-fuzzy-evaluation（指标边界不模糊，弃）"],
        criteria=["数据可得性", "可解释性", "评委接受度"],
        reasoning="有客观指标矩阵，指标边界清晰，熵权+TOPSIS 管线成熟",
        confidence=0.8,
        reversible=True,
        created_by="model_selection",
        evidence_ids=["M001", "DATA001"],
        question_type="evaluation",
    )
    params.update(kw)
    return dlog.add(**params)


class TestAdd:
    def test_auto_ids_sequential(self, log):
        assert _add(log).decision_id == "D001"
        assert _add(log).decision_id == "D002"

    def test_missing_required_field_raises(self, log):
        with pytest.raises(DecisionLogError, match="reasoning"):
            _add(log, reasoning="")

    def test_bad_confidence_raises(self, log):
        with pytest.raises(DecisionLogError, match="confidence"):
            _add(log, confidence=1.5)

    def test_bad_alternatives_raises(self, log):
        with pytest.raises(DecisionLogError, match="alternatives"):
            _add(log, alternatives=[])

    def test_reversible_required(self, log):
        with pytest.raises(DecisionLogError, match="reversible"):
            _add(log, reversible="yes")

    def test_duplicate_id_rejected(self, log):
        _add(log, decision_id="D001")
        with pytest.raises(DecisionLogError, match="已存在"):
            _add(log, decision_id="D001")

    def test_bad_decision_id_format(self, log):
        with pytest.raises(DecisionLogError, match="D"):
            _add(log, decision_id="decision-1")


class TestInvalidate:
    def test_invalidate_active(self, log):
        _add(log, decision_id="D001")
        _add(log, question="Q001 重新选型", chosen="mc-fuzzy-evaluation",
             decision_id="D002")
        log.invalidate("D001", "D002", "指标实测边界模糊，模糊评价更合适")
        assert log.get("D001").status == "invalidated"
        assert log.get("D001").invalidated_by == "D002"

    def test_invalidate_dangling_target_rejected(self, log):
        _add(log)
        with pytest.raises(DecisionLogError, match="不存在"):
            log.invalidate("D001", "D999", "reason")

    def test_double_invalidate_rejected(self, log):
        _add(log)
        log.invalidate("D001", "invalidation-event-07", "数据集修订")
        with pytest.raises(DecisionLogError, match="不可再推翻"):
            log.invalidate("D001", "D002", "again")

    def test_empty_reason_rejected(self, log):
        _add(log, decision_id="D001")
        _add(log, question="Q001 重选", decision_id="D002")
        with pytest.raises(DecisionLogError, match="reason"):
            log.invalidate("D001", "D002", "  ")

    def test_invalidate_unknown_id(self, log):
        with pytest.raises(DecisionLogError, match="不存在"):
            log.invalidate("D404", "D001", "x")


class TestQuery:
    def test_query_by_question_type(self, log):
        _add(log, question_type="evaluation")
        _add(log, question="Q002 路径优化", chosen="mc-ga",
             question_type="optimization")
        rows = log.query(question_type="optimization")
        assert len(rows) == 1
        assert rows[0]["chosen"] == "mc-ga"

    def test_query_by_method_substring(self, log):
        _add(log)
        _add(log, question="Q002", chosen="mc-ga")
        assert len(log.query(method="topsis")) == 1
        assert len(log.query(method="ga")) == 1

    def test_query_by_text(self, log):
        _add(log, reasoning="因为指标矩阵完整")
        _add(log, question="Q002", reasoning="因为解空间非凸")
        assert len(log.query(text="非凸")) == 1

    def test_active_only_and_downweight(self, log):
        _add(log, decision_id="D001")
        _add(log, question="Q001 重选", chosen="mc-ahp", decision_id="D002")
        log.invalidate("D001", "D002", "权重主观来源被质疑")
        active = log.query(active_only=True)
        assert [r["decision_id"] for r in active] == ["D002"]
        all_rows = {r["decision_id"]: r for r in log.query(active_only=False)}
        assert "superseded_note" in all_rows["D001"]
        assert "被 D002 推翻" in all_rows["D001"]["superseded_note"]

    def test_consequences_append_only(self, log):
        dec = _add(log)
        log.record_consequence("D001", "带动后续验证节点补双权重敏感性")
        log.record_consequence("D001", "评审关注点集中在权重来源")
        got = log.get("D001")
        assert len(got.consequences) == 2
        assert got.consequences[0].startswith("带动")

    def test_consequence_empty_rejected(self, log):
        _add(log)
        with pytest.raises(DecisionLogError, match="不能为空"):
            log.record_consequence("D001", " ")


class TestPersistence:
    def test_save_load_roundtrip(self, tmp_path):
        p = tmp_path / "state" / "decisions.json"
        log = DecisionLog(p)
        _add(log)
        _add(log, question="Q002", chosen="mc-ga", decision_id="D005")
        log.invalidate("D001", "D005", "重选")
        log.record_consequence("D001", "上游修订")
        log.save()

        log2 = DecisionLog(p)
        assert set(log2.decisions) == {"D001", "D005"}
        assert log2.get("D001").status == "invalidated"
        assert log2.get("D001").consequences == ["上游修订"]
        assert log2.get("D005").confidence == 0.8
        # 新 log 在已载入历史上继续编号（不复用、不冲突）
        assert log2.next_id() == "D006"

    def test_load_version_mismatch(self, tmp_path):
        p = tmp_path / "decisions.json"
        p.write_text(json.dumps({"schema_version": 1, "decisions": []}),
                     encoding="utf-8")
        with pytest.raises(DecisionLogError, match="版本"):
            DecisionLog(p)

    def test_atomic_write_no_tmp_leftover(self, tmp_path):
        p = tmp_path / "decisions.json"
        log = DecisionLog(p)
        _add(log)
        log.save()
        assert p.is_file()
        assert list(p.parent.glob("*.tmp")) == []


class TestFromDict:
    def test_full_roundtrip_via_from_dict(self, log):
        dec = _add(log)
        clone = Decision.from_dict(dec.as_dict())
        assert clone == dec

    def test_status_default_active(self, log):
        dec = _add(log)
        assert dec.status == "active"
        assert dec.active
