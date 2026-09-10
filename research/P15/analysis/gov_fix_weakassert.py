# -*- coding: utf-8 -*-
"""audit Batch8：强化 3 个弱断言样本（U10/V08/U03）。"""
from pathlib import Path

REPO = Path(r"C:\Users\Lin\Desktop\Programs\MathModel")

# U10: test_status_never_defaulted 重言式 → 验证真实执行内容
p1 = REPO / "tests" / "unit" / "test_execution_adapter.py"
s1 = p1.read_text(encoding="utf-8")
old1 = '''        r = self._run("raise SystemExit(0) if False else print('ok')")
        assert r.status in ("success", "failed", "timeout", "invalid")'''
new1 = '''        r = self._run("raise SystemExit(0) if False else print('ok')")
        # audit Batch8：原断言 status in 全枚举恒真（重言式）——强化为
        # 验证真实执行内容：success 且 stdout 含输出
        assert r.status == "success", f"真实执行应 success，实际 {r.status}"
        assert "ok" in (r.stdout or ""), f"stdout 应含真实输出，实际 {r.stdout!r}"'''
assert old1 in s1, "U10 pattern not found"
p1.write_text(s1.replace(old1, new1, 1), encoding="utf-8")
print("U10 fixed")

# V08: test_B_superseded_model_cannot_support_decision 双条件其一 → 前置+真实验证
p2 = REPO / "tests" / "integration" / "test_research_quality.py"
s2 = p2.read_text(encoding="utf-8")
old2 = '''        model_findings = rep.dimensions["model"].findings
        dead_models = [a for a in s.registry.list_by_type("model")
                       if a.status == "superseded"]
        assert dead_models or model_findings'''
new2 = '''        model_findings = rep.dimensions["model"].findings
        dead_models = [a for a in s.registry.list_by_type("model")
                       if a.status == "superseded"]
        # audit Batch8：原断言双条件其一（可能平凡通过）——强化为
        # 前置（superseded 必须存在）+ 质量层必须真实发现
        assert dead_models, "前置：模型必须处于 superseded 状态"
        assert model_findings, "Quality 层必须发现 superseded 模型（D4 规则）"'''
assert old2 in s2, "V08 pattern not found"
p2.write_text(s2.replace(old2, new2, 1), encoding="utf-8")
print("V08 fixed")

# U03: test_load_config_returns_nonempty_dict 仅断言非空 → 断言关键组键
p3 = REPO / "tests" / "unit" / "test_env.py"
s3 = p3.read_text(encoding="utf-8")
old3 = '''    def test_load_config_returns_nonempty_dict(self, env_loader):
        """load_config() 返回非空 dict"""
        cfg = env_loader.load_config()
        assert isinstance(cfg, dict)
        assert len(cfg) > 0'''
new3 = '''    def test_load_config_returns_nonempty_dict(self, env_loader):
        """load_config() 返回非空 dict 且含核心配置组"""
        cfg = env_loader.load_config()
        assert isinstance(cfg, dict)
        assert len(cfg) > 0
        # audit Batch8：强化——关键配置组必须存在（否则 load_config 无意义）
        for group in ("paper", "code", "modeling", "review", "runtime"):
            assert group in cfg, f"配置组 {group} 缺失"'''
assert old3 in s3, "U03 pattern not found"
p3.write_text(s3.replace(old3, new3, 1), encoding="utf-8")
print("U03 fixed")
