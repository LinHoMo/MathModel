"""P3 Role 层测试：加载契约 / DAG 角色校验 / 与真实 workflow 的一致性。

运行: python -m pytest tests/unit/test_roles.py -q
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))

import pytest

from runtime.execution.composer import WorkflowComposer
from runtime.roles import RoleError, load_roles, validate_dag_roles

ROLES_ROOT = REPO / "core" / "roles"


class TestRoleLibrary:
    def test_five_roles_load(self):
        roles = load_roles(ROLES_ROOT)
        assert set(roles) == {"analyst", "modeler", "experimenter", "critic", "writer"}

    def test_capabilities_non_empty(self):
        for r in load_roles(ROLES_ROOT).values():
            assert r.capabilities, f"{r.role} 无 capabilities"
            assert all(isinstance(c, str) and c for c in r.capabilities)

    def test_critic_has_critique_capabilities(self):
        roles = load_roles(ROLES_ROOT)
        caps = set(roles["critic"].capabilities)
        assert {"model-critique", "experiment-critique", "evidence-gating"} <= caps

    def test_modeler_consumes_knowledge(self):
        roles = load_roles(ROLES_ROOT)
        assert "model-selection" in roles["modeler"].capabilities

    def test_bad_role_id_rejected(self, tmp_path):
        (tmp_path / "x.yaml").write_text(
            "role: hacker\ncapabilities: [x]\n", encoding="utf-8")
        with pytest.raises(RoleError, match="role 非法"):
            load_roles(tmp_path)

    def test_missing_role_file_rejected(self, tmp_path):
        (tmp_path / "analyst.yaml").write_text(
            "role: analyst\ncapabilities: [x]\n", encoding="utf-8")
        with pytest.raises(RoleError, match="缺少"):
            load_roles(tmp_path)

    def test_empty_capabilities_rejected(self, tmp_path):
        (tmp_path / "analyst.yaml").write_text(
            "role: analyst\ncapabilities: []\n", encoding="utf-8")
        with pytest.raises(RoleError, match="capabilities"):
            load_roles(tmp_path)


class TestDagRoleValidation:
    def test_composed_workflow_roles_all_valid(self):
        """真实 base workflow 组合后，所有节点 role 引用合法且在 executes 内。"""
        composer = WorkflowComposer(REPO / "core" / "workflows")
        dag = composer.compose()
        roles = load_roles(ROLES_ROOT)
        problems = validate_dag_roles(dag, roles)
        assert problems == []

    def test_expanded_workflow_roles_valid(self):
        composer = WorkflowComposer(REPO / "core" / "workflows")
        dag = composer.compose_executable(["Q001", "Q002"])
        roles = load_roles(ROLES_ROOT)
        assert validate_dag_roles(dag, roles) == []

    def test_unknown_role_detected(self):
        from runtime.execution.dag import Node, WorkflowDAG
        dag = WorkflowDAG(nodes={"n1": Node("n1", role="ghost")})
        problems = validate_dag_roles(dag, {"modeler": load_roles(ROLES_ROOT)["modeler"]})
        assert any("ghost" in p for p in problems)

    def test_node_outside_executes_detected(self):
        from runtime.execution.dag import Node, WorkflowDAG
        roles = load_roles(ROLES_ROOT)
        # writer role 不执行 model_selection
        dag = WorkflowDAG(nodes={
            "model_selection": Node("model_selection", role="writer")})
        problems = validate_dag_roles(dag, roles)
        assert any("executes" in p for p in problems)
