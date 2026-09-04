"""测试 agents/openai.yaml 与 catalog.yaml 一致（gen_runtime_manifest.py）+ catalog v5 双视图。"""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "core" / "tools"))

import gen_runtime_manifest as GRM
import state as S


class TestOpenAiManifest(unittest.TestCase):
    """agents/openai.yaml 必须与 catalog.yaml 单一真源一致。"""

    def setUp(self):
        self.catalog = GRM.load_catalog()
        self.hands = self.catalog.get("hands", [])

    def test_total_agents_is_29(self):
        """legacy hands 视图（V2 线性流水线）保持 29 agent 不变。"""
        total = sum(len(h.get("agents", [])) for h in self.hands)
        self.assertEqual(total, 29, f"legacy agent 总数应为 29，实际 {total}")

    def test_reviewer_hand_has_8_agents(self):
        reviewer = next((h for h in self.hands if h["name"] == "reviewer"), None)
        self.assertIsNotNone(reviewer, "reviewer 手缺失")
        self.assertEqual(len(reviewer.get("agents", [])), 8, "reviewer 应有 8 个 agent")

    def test_all_5_scorers_present(self):
        reviewer = next((h for h in self.hands if h["name"] == "reviewer"), None)
        names = {a["name"] for a in reviewer.get("agents", [])}
        expected = {"scorer-academic", "scorer-engineering",
                    "scorer-judge", "scorer-reader", "scorer-adversarial"}
        missing = expected - names
        self.assertFalse(missing, f"reviewer 缺少 scorer: {missing}")

    def test_no_judge_scorer(self):
        """旧设计 judge-scorer 已废弃，不应出现在 catalog 中。"""
        all_names = {a["name"] for h in self.hands for a in h.get("agents", [])}
        self.assertNotIn("judge-scorer", all_names)

    def test_agent_set_equals_state_pipeline(self):
        """catalog agent 集合应等于 state.PIPELINE 的 (hand, agent) 对。"""
        catalog_pairs = {(h["name"], a["name"]) for h in self.hands for a in h.get("agents", [])}
        state_pairs = {(h, a) for h, a, _ in S.PIPELINE}
        self.assertEqual(catalog_pairs, state_pairs)

    def test_every_agent_path_exists(self):
        """每个 agent 的 path 字段对应真实目录。"""
        for h in self.hands:
            for a in h.get("agents", []):
                p = a.get("path", "")
                if p:
                    self.assertTrue(
                        (ROOT / p).exists(),
                        f"agent 路径不存在: {p}（{h['name']}/{a['name']}）"
                    )


    def test_hand_agent_pairs_unique(self):
        """(hand, agent) 二元组必须唯一（存在同名 guardrails-checker 跨手）。"""
        pairs = [(h["name"], a["name"]) for h in self.hands for a in h.get("agents", [])]
        self.assertEqual(len(pairs), len(set(pairs)), "存在重复 (hand, agent) 对")

    def test_generate_no_drift(self):
        """生成器输出不应与磁盘文件漂移。"""
        generated = GRM.generate_openai_yaml(self.catalog)
        ok, diffs = GRM.check_drift(generated)
        self.assertTrue(ok, f"检测到漂移: {diffs[:5]}")

    def test_check_mode_exit_code(self):
        """--check 模式应返回 0（无漂移）。"""
        import subprocess
        r = subprocess.run(
            [sys.executable, str(ROOT / "core" / "tools" / "gen_runtime_manifest.py"), "--check"],
            cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"--check EXIT {r.returncode}: {r.stdout}{r.stderr}")


class TestCatalogV3View(unittest.TestCase):
    """catalog v5 双视图：v3 节（roles/nodes/validators）与运行时实体一致。

    深度三方校验由 core/tools/catalog_check.py 承担（见
    tests/unit/test_catalog_check.py）；此处做 manifest 侧的结构性断言。
    """

    def setUp(self):
        self.catalog = GRM.load_catalog()
        # GRM 解析器会把 v3 块包成单元素 list，统一解包
        v3 = self.catalog.get("v3")
        if isinstance(v3, list) and len(v3) == 1 and isinstance(v3[0], dict):
            v3 = v3[0]
        self.v3 = v3 or {}

    def test_schema_version_5(self):
        self.assertEqual(self.catalog.get("schema_version"), 5,
                         "v3 双视图要求 schema_version 5")

    def test_v3_view_present(self):
        for key in ("roles", "nodes", "validators"):
            self.assertIn(key, self.v3, f"v3 视图缺少 {key}")

    def test_v3_roles_are_5(self):
        names = {r["name"] for r in self.v3.get("roles", [])}
        self.assertEqual(
            names, {"analyst", "modeler", "experimenter", "critic", "writer"},
            f"v3.roles 应为 5 角色，实际 {sorted(names)}")

    def test_v3_nodes_are_15(self):
        nodes = self.v3.get("nodes", [])
        self.assertEqual(len(nodes), 15, f"v3.nodes 应为 15 节点，实际 {len(nodes)}")

    def test_v3_validators_paths_exist(self):
        for v in self.v3.get("validators", []):
            path = ROOT / v.get("path", "")
            self.assertTrue(path.is_file(),
                            f"v3.validators[{v.get('name')}] 路径不存在: {v.get('path')}")

    def test_v3_nodes_roles_all_declared(self):
        role_names = {r["name"] for r in self.v3.get("roles", [])}
        for n in self.v3.get("nodes", []):
            self.assertIn(n.get("role"), role_names,
                          f"v3.nodes[{n.get('name')}] 引用未声明角色: {n.get('role')}")

    def test_manifest_generation_ignores_v3(self):
        """openai.yaml 生成只消费 hands（legacy 视图），v3 追加不产生漂移。"""
        generated = GRM.generate_openai_yaml(self.catalog)
        ok, diffs = GRM.check_drift(generated)
        self.assertTrue(ok, f"v3 追加导致 manifest 漂移: {diffs[:5]}")


class TestCatalogCheck(unittest.TestCase):
    """catalog_check.py --check：v3 双视图三方一致性（roles/DAG/validators）。"""

    def test_check_exit_zero(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, str(ROOT / "core" / "tools" / "catalog_check.py"), "--check"],
            cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0,
                         f"catalog_check EXIT {r.returncode}: {r.stdout}{r.stderr}")

    def test_json_mode_reports_ok(self):
        import subprocess
        r = subprocess.run(
            [sys.executable, str(ROOT / "core" / "tools" / "catalog_check.py"), "--json"],
            cwd=str(ROOT), capture_output=True, text=True)
        payload = json.loads(r.stdout)
        self.assertTrue(payload["ok"], f"catalog_check 发现问题: {payload['problems']}")


if __name__ == "__main__":
    unittest.main()
