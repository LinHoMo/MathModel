"""测试 agents/openai.yaml 与 catalog.yaml 一致（gen_runtime_manifest.py）。"""

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
        total = sum(len(h.get("agents", [])) for h in self.hands)
        self.assertEqual(total, 29, f"agent 总数应为 29，实际 {total}")

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


if __name__ == "__main__":
    unittest.main()
