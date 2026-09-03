"""
env 配置层测试

测试 core/env/config.yaml / core/env/loader.py / core/env/README.md 三件套结构、
loader 接口（load_config / get）与四组配置字段完整性。

用 importlib 动态加载 core/env/loader.py，避免包路径 / PYTHONPATH 依赖。
测试从项目根目录运行（pytest 根目录为项目根）。
"""
import os
import importlib.util

import pytest


# ---------------------------------------------------------------------------
# 动态加载 core/env/loader.py 为独立模块
# ---------------------------------------------------------------------------
def _load_env_loader():
    """用 importlib 动态加载 core/env/loader.py，返回模块对象。"""
    loader_path = os.path.join("core", "env", "loader.py")
    assert os.path.exists(loader_path), f"{loader_path} 不存在"
    spec = importlib.util.spec_from_file_location("env_loader", loader_path)
    assert spec is not None and spec.loader is not None, "无法创建 loader spec"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def env_loader():
    """模块级 fixture：所有测试复用同一份加载结果。"""
    return _load_env_loader()


class TestEnvStructure:
    """env 目录三件套结构检查"""

    def test_config_yaml_exists(self):
        """core/env/config.yaml 存在"""
        assert os.path.exists("core/env/config.yaml")

    def test_loader_py_exists(self):
        """core/env/loader.py 存在"""
        assert os.path.exists("core/env/loader.py")

    def test_readme_md_exists(self):
        """core/env/README.md 存在"""
        assert os.path.exists("core/env/README.md")


class TestEnvLoader:
    """core/env/loader.py 接口测试"""

    def test_load_config_returns_nonempty_dict(self, env_loader):
        """load_config() 返回非空 dict"""
        cfg = env_loader.load_config()
        assert isinstance(cfg, dict)
        assert len(cfg) > 0

    def test_load_config_has_four_groups(self, env_loader):
        """load_config() 返回的 dict 含四组 key"""
        cfg = env_loader.load_config()
        for group in ("paper", "code", "modeling", "runtime"):
            assert group in cfg, f"缺少配置组: {group}"

    def test_get_paper_min_pages(self, env_loader):
        """get('paper.min_pages') 返回 25（对标 mmagent-codex-main：国赛 25-30 页）"""
        assert env_loader.get("paper.min_pages") == 25

    def test_get_code_random_seed(self, env_loader):
        """get('code.random_seed') 返回 42"""
        assert env_loader.get("code.random_seed") == 42

    def test_get_missing_with_default(self, env_loader):
        """get('not.exist', default='fb') 返回 'fb'"""
        assert env_loader.get("not.exist", default="fb") == "fb"

    def test_get_missing_returns_none(self, env_loader):
        """get('not.exist') 返回 None"""
        assert env_loader.get("not.exist") is None

    def test_load_config_and_get_callable(self, env_loader):
        """load_config 与 get 可调用"""
        assert callable(env_loader.load_config)
        assert callable(env_loader.get)


class TestEnvConfig:
    """env 配置四组字段完整性测试"""

    def test_paper_fields(self, env_loader):
        """paper 组含 6 个字段"""
        cfg = env_loader.load_config()
        paper = cfg["paper"]
        for field in ("min_pages", "min_words", "min_figures",
                      "min_tables", "min_equations", "min_references"):
            assert field in paper, f"paper 缺字段: {field}"

    def test_code_fields(self, env_loader):
        """code 组含 2 个字段"""
        cfg = env_loader.load_config()
        code = cfg["code"]
        for field in ("random_seed", "multi_run_count"):
            assert field in code, f"code 缺字段: {field}"

    def test_modeling_fields(self, env_loader):
        """modeling 组含 2 个字段"""
        cfg = env_loader.load_config()
        modeling = cfg["modeling"]
        for field in ("min_candidate_models", "assumption_score_threshold"):
            assert field in modeling, f"modeling 缺字段: {field}"

    def test_runtime_fields(self, env_loader):
        """runtime 组含 3 个字段"""
        cfg = env_loader.load_config()
        runtime = cfg["runtime"]
        for field in ("language", "template", "strict_mode"):
            assert field in runtime, f"runtime 缺字段: {field}"

    def test_all_four_groups_present(self, env_loader):
        """四组配置组齐全"""
        cfg = env_loader.load_config()
        assert set(cfg.keys()) >= {"paper", "code", "modeling", "runtime"}
