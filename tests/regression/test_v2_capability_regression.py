"""V2 能力回归测试 — P5 验收基线。

目的: V3 P0-P5 重构期间，V2 29 步流水线的核心能力必须始终可用
（迁移映射 §5: "29-step PIPELINE 保留为 legacy 模式"）。

覆盖:
    R1  new_project 脚手架（含 V3 workspace 目录）
    R2  state init / status / advance / fail（legacy 状态机）
    R3  gate CLI 可调用（gatelib 门禁库加载）
    R4  catalog v5 双视图 --check 通过
    R5  adapters/openai.yaml 与 catalog 无漂移
    R6  orchestrator 默认 V3 DAG 干跑 + --legacy 干跑
    R7  validate.py 项目级校验入口可用
    R8  doctor.py 环境预检通过

运行: python -m pytest tests/regression/test_v2_capability_regression.py -q
"""

import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable


def _run(args, timeout=120):
    return subprocess.run([PY] + args, cwd=str(ROOT),
                          capture_output=True, text=True, timeout=timeout)


@pytest.fixture(scope="module")
def reg_project():
    """创建一次性 legacy 项目，全部回归用例共用，模块级清理。"""
    name = f"regtest{uuid.uuid4().hex[:8]}"
    problem = ROOT / "tests" / "fixtures" / "sample_problem.txt"
    problem.parent.mkdir(parents=True, exist_ok=True)
    problem.write_text("回归测试赛题：某物理系统的数学建模。", encoding="utf-8")
    r = _run(["core/tools/new_project.py", name,
              "--competition", "cumcm", "--problem", str(problem)])
    assert r.returncode == 0, f"new_project 失败: {r.stdout}{r.stderr}"
    yield name
    shutil.rmtree(ROOT / "projects" / name, ignore_errors=True)


# ------------------------------------------------------------- R1 脚手架

class TestScaffold:
    def test_r1_scaffold_dirs(self, reg_project):
        base = ROOT / "projects" / reg_project
        for sub in ("inputs", "work", "output", "code", "figures", "paper",
                    "state", "artifacts"):
            assert (base / sub).is_dir(), f"脚手架缺目录: {sub}"
        # 赛题已导入
        assert (base / "inputs" / "sample_problem.txt").is_file()
        # legacy 契约文件
        assert (base / "work" / "handoff.md").is_file()
        assert (base / "work" / "time_budget.yaml").is_file()


# ------------------------------------------------------------- R2 状态机

class TestLegacyState:
    def test_r2_init_and_status(self, reg_project):
        r = _run(["core/tools/state.py", reg_project, "init"])
        assert r.returncode == 0, r.stdout + r.stderr
        r = _run(["core/tools/state.py", reg_project, "status"])
        assert r.returncode == 0, r.stdout + r.stderr
        # 29 步流水线起点
        assert "problem-parser" in r.stdout or "modeler" in r.stdout.lower()

    def test_r2_advance_and_fail(self, reg_project):
        # advance 需要 gate 产物；用 fail 登记验证写路径
        r = _run(["core/tools/state.py", reg_project, "fail",
                  "modeler", "problem-parser", "--reason", "回归测试登记"])
        assert r.returncode == 0, r.stdout + r.stderr
        # fail 不推进进度（进度仍 0/29），但记录必须落入 state.json
        state_file = ROOT / "projects" / reg_project / "work" / "state.json"
        assert state_file.is_file()
        content = state_file.read_text(encoding="utf-8")
        assert "回归测试登记" in content
        r = _run(["core/tools/state.py", reg_project, "status"])
        assert r.returncode == 0
        assert "0/29" in r.stdout   # fail 登记不等于完成


# ------------------------------------------------------------- R3/R4/R5

class TestGatesAndCatalog:
    def test_r3_gate_cli_loadable(self, reg_project):
        """gate CLI 可执行（无产物时报错方式必须是门禁 FAIL 而非崩溃）。"""
        r = _run(["core/tools/gate.py", reg_project, "modeler",
                  "problem-parser"], timeout=60)
        assert r.returncode in (0, 1), \
            f"gate 异常退出: {r.returncode}\n{r.stdout}{r.stderr}"

    def test_r4_catalog_check(self):
        r = _run(["core/tools/catalog_check.py", "--check"])
        assert r.returncode == 0, r.stdout + r.stderr

    def test_r5_manifest_no_drift(self):
        r = _run(["core/tools/gen_runtime_manifest.py", "--check"])
        assert r.returncode == 0, r.stdout + r.stderr


# ------------------------------------------------------------- R6 编排器

class TestOrchestrator:
    def test_r6_default_is_v3_dry_run(self, reg_project):
        r = _run(["core/tools/orchestrator.py", reg_project], timeout=120)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "[V3]" in r.stdout
        assert "Wave" in r.stdout

    def test_r6_legacy_mode(self, reg_project):
        """legacy 模式可启动：空项目上第 1 步门禁必然拦截（EXIT 1 是正确
        行为——门禁拒绝了空产物），关键是不崩溃、输出流水线头部。"""
        r = _run(["core/tools/orchestrator.py", reg_project,
                  "--legacy", "--dry-run"], timeout=180)
        assert r.returncode in (0, 1), \
            f"legacy 模式异常退出: {r.returncode}\n{r.stdout}{r.stderr}"
        assert "自动化流水线" in r.stdout
        assert "Traceback" not in r.stderr


# ------------------------------------------------------------- R7/R8

class TestValidationEntries:
    def test_r7_validate_project_entry(self, reg_project):
        """validate_project 对新建项目必须可执行（空项目产物不全时
        EXIT 0/1 均为合法判定，但不得 traceback / EXIT 2 路径错）。"""
        proj_path = ROOT / "projects" / reg_project
        r = _run(["core/tools/validate_project.py", "--project", str(proj_path)],
                 timeout=180)
        assert r.returncode in (0, 1), \
            f"validate_project 异常: {r.returncode}\n{r.stdout[-800:]}{r.stderr[-800:]}"
        assert "Traceback" not in r.stderr
        assert "not a directory" not in r.stdout

    def test_r8_doctor(self):
        r = _run(["core/tools/doctor.py", "--skip-tools"], timeout=120)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "阻塞 0" in r.stdout
