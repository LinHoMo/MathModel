"""P1-VS-001 核心改动测试：model_ir artifact 类型 + revision_of/supersedes 边。

每处 core 改动必须有对应测试（最小修改原则的门禁）。
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import json

import pytest

from runtime.artifacts.ids import (
    ARTIFACT_TYPES, PREFIX_TO_TYPE, format_id, id_type, is_valid_id, parse_id,
)
from runtime.artifacts.registry import ArtifactRegistry
from runtime.graph.evidence_graph import (
    RELATION_TYPES, STRONG_RELATIONS, WEAK_RELATIONS, EvidenceGraph, GraphError,
    propagation_tiers,
)


# ============================================================
# 1. model_ir artifact 类型（ids.py）
# ============================================================

class TestModelIRType:
    def test_model_ir_in_artifact_types(self):
        assert "model_ir" in ARTIFACT_TYPES
        assert ARTIFACT_TYPES["model_ir"] == "MIR"

    def test_mir_prefix_reverse_lookup(self):
        assert PREFIX_TO_TYPE["MIR"] == "model_ir"

    def test_mir_id_format(self):
        assert format_id("MIR", 1) == "MIR001"
        assert format_id("MIR", 42) == "MIR042"
        assert format_id("MIR", 1000) == "MIR1000"

    def test_mir_id_valid(self):
        assert is_valid_id("MIR001")
        assert is_valid_id("MIR1000")
        assert not is_valid_id("MIR0")   # 编号必须 >=1
        assert not is_valid_id("MI001")  # 前缀错误

    def test_mir_id_parse(self):
        atype, prefix, num = parse_id("MIR007")
        assert atype == "model_ir"
        assert prefix == "MIR"
        assert num == 7

    def test_mir_not_confused_with_model(self):
        # MIR001 不应被解析为 M 类型
        assert id_type("MIR001") == "model_ir"
        assert id_type("M001") == "model"

    def test_registry_create_model_ir(self, tmp_path):
        from conftest import mir
        reg = ArtifactRegistry(tmp_path / "registry.json")
        reg.create("question", title="Q1", data={"question_id": "Q1"},
                   activate=True)
        art = reg.create("model_ir", title="test MIR",
                         data=mir("Q1", "M-TEST"), activate=True)
        assert art.artifact_id.startswith("MIR")
        assert art.type == "model_ir"
        assert art.status == "active"
        reg.save()
        # 恢复
        reg2 = ArtifactRegistry(tmp_path / "registry.json")
        reg2.load()
        assert reg2.get(art.artifact_id).type == "model_ir"


# ============================================================
# 2. revision_of / supersedes 边（evidence_graph.py）
# ============================================================

class TestRevisionRelations:
    def test_relation_types_exist(self):
        assert "revision_of" in RELATION_TYPES
        assert "supersedes" in RELATION_TYPES

    def test_revision_of_type_constraint(self):
        ft, tt = RELATION_TYPES["revision_of"]
        assert "model" in ft
        assert "model_ir" in ft
        assert "model" in tt
        assert "model_ir" in tt

    def test_supersedes_type_constraint(self):
        ft, tt = RELATION_TYPES["supersedes"]
        assert "model" in ft
        assert "model_ir" in ft
        assert "model" in tt
        assert "model_ir" in tt

    def test_revision_relations_are_weak(self):
        assert "revision_of" in WEAK_RELATIONS
        assert "supersedes" in WEAK_RELATIONS
        assert "revision_of" not in STRONG_RELATIONS
        assert "supersedes" not in STRONG_RELATIONS

    def test_revision_propagation_none(self):
        # 修订谱系是审计边，不传播失效
        assert propagation_tiers("revision_of") == (None, None)
        assert propagation_tiers("supersedes") == (None, None)

    def _make_graph(self, tmp_path):
        reg = ArtifactRegistry(tmp_path / "registry.json")
        # 创建两个 model_ir 和两个 model
        mir1 = reg.create("model_ir", title="MIR v1", activate=True)
        mir2 = reg.create("model_ir", title="MIR v2", activate=True)
        m1 = reg.create("model", title="Model v1", activate=True)
        m2 = reg.create("model", title="Model v2", activate=True)
        g = EvidenceGraph(reg, tmp_path / "evidence_graph.json")
        return reg, g, mir1.artifact_id, mir2.artifact_id, m1.artifact_id, m2.artifact_id

    def test_add_revision_of_edge(self, tmp_path):
        reg, g, mir1, mir2, m1, m2 = self._make_graph(tmp_path)
        edge = g.add_relation(mir2, "revision_of", mir1)
        assert edge["from"] == mir2
        assert edge["relation"] == "revision_of"
        assert edge["to"] == mir1

    def test_add_supersedes_edge(self, tmp_path):
        reg, g, mir1, mir2, m1, m2 = self._make_graph(tmp_path)
        edge = g.add_relation(mir2, "supersedes", mir1)
        assert edge["relation"] == "supersedes"

    def test_revision_between_models(self, tmp_path):
        reg, g, mir1, mir2, m1, m2 = self._make_graph(tmp_path)
        g.add_relation(m2, "revision_of", m1)
        g.add_relation(m2, "supersedes", m1)
        assert len(g.relations) == 2

    def test_revision_rejects_wrong_type(self, tmp_path):
        reg, g, mir1, mir2, m1, m2 = self._make_graph(tmp_path)
        # 创建一个 code artifact
        code = reg.create("code", title="code", data={"code": "x=1"},
                          activate=True)
        with pytest.raises(GraphError):
            g.add_relation(code.artifact_id, "revision_of", mir1)

    def test_revision_no_self_loop(self, tmp_path):
        reg, g, mir1, mir2, m1, m2 = self._make_graph(tmp_path)
        with pytest.raises(GraphError):
            g.add_relation(mir1, "revision_of", mir1)

    def test_revision_no_duplicate(self, tmp_path):
        reg, g, mir1, mir2, m1, m2 = self._make_graph(tmp_path)
        g.add_relation(mir2, "revision_of", mir1)
        with pytest.raises(GraphError):
            g.add_relation(mir2, "revision_of", mir1)

    def test_revision_persist_and_reload(self, tmp_path):
        reg, g, mir1, mir2, m1, m2 = self._make_graph(tmp_path)
        g.add_relation(mir2, "revision_of", mir1)
        g.add_relation(mir2, "supersedes", mir1)
        reg.save()
        g.save()
        # 重新加载
        reg2 = ArtifactRegistry(tmp_path / "registry.json")
        reg2.load()
        g2 = EvidenceGraph(reg2, tmp_path / "evidence_graph.json")
        relations = [(r["from"], r["relation"], r["to"]) for r in g2.relations]
        assert (mir2, "revision_of", mir1) in relations
        assert (mir2, "supersedes", mir1) in relations

    def test_revision_does_not_propagate_invalidation(self, tmp_path):
        """revision_of/supersedes 是审计边，invalidate 不应沿它们传播。"""
        reg, g, mir1, mir2, m1, m2 = self._make_graph(tmp_path)
        g.add_relation(mir2, "revision_of", mir1)
        g.add_relation(mir2, "supersedes", mir1)
        reg.save()
        g.save()
        # invalidate mir1（旧版本被替代）
        report = g.invalidate(mir1, reason="superseded by v2")
        # mir2 不应被波及（修订边不传播）
        assert mir2 not in report["invalidated"]
        assert mir2 not in report["requires_revalidation"]
