# -*- coding: utf-8 -*-
"""P0-5（终审 ROADMAP）：mark_validated 门禁验收。

验收标准：
1. 非白名单调用方调 registry.mark_validated → PermissionError；
2. 白名单调用方（模拟 runtime 验证管线帧）+ 有效 run_record → 通过；
3. run_record 缺失/缺 run_id/hash/validator 不一致 → RegistryError；
4. critic SKILL.md 不含 mark_validated 字符串；
5. 全仓 mark_validated( 仅 registry/artifact 定义 + validator + 测试。
"""

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "core"))

import pytest  # noqa: E402

from runtime.artifacts.registry import (  # noqa: E402
    ArtifactRegistry, RegistryError, VALIDATION_CALLER_ALLOWED_SUBSTR)


@pytest.fixture()
def reg(tmp_path):
    return ArtifactRegistry(path=tmp_path / "reg")


@pytest.fixture()
def model(reg):
    reg.create("question", title="Q", activate=True)  # Q001
    return reg.create("model", title="M", question="Q001", activate=True)


def _run_record(validator="model-critic", **kw):
    d = {"validator": validator, "run_id": "run-001", "hash": "abc123"}
    d.update(kw)
    return d


def test_non_whitelisted_caller_rejected(reg, model):
    """测试模块（非白名单）调用 → PermissionError（Agent 等价路径）。"""
    with pytest.raises(PermissionError):
        reg.mark_validated(model.artifact_id, "model-critic",
                           run_record=_run_record())


def test_missing_run_record_rejected(reg, model):
    with pytest.raises(RegistryError, match="run_record"):
        reg.mark_validated(model.artifact_id, "model-critic")


def test_run_record_missing_trace_rejected(reg, model):
    with pytest.raises(RegistryError, match="run_id"):
        reg.mark_validated(model.artifact_id, "model-critic",
                           run_record={"validator": "model-critic"})


def test_run_record_validator_mismatch_rejected(reg, model):
    with pytest.raises(RegistryError, match="不一致"):
        reg.mark_validated(model.artifact_id, "model-critic",
                           run_record=_run_record(validator="experiment-critic"))


def test_whitelisted_caller_accepted():
    """白名单调用：用 compile 把调用帧路径伪装为 validators.py（模拟
    Runtime 验证管线帧），+ 有效 run_record → 通过。"""
    reg = ArtifactRegistry(path=Path(os.environ.get("TEMP", ".")) / "_p05_reg")
    try:
        reg.create("question", title="Q", activate=True)  # Q001
        m = reg.create("model", title="M", question="Q001", activate=True)
        code = compile(
            "REG.mark_validated(AID, 'model-critic', "
            "run_record={'validator': 'model-critic', 'run_id': 'run-001', "
            "'hash': 'abc123'})",
            str(REPO / "core" / "runtime" / "execution" / "validators.py"),
            "exec")
        exec(code, {"REG": reg, "AID": m.artifact_id})
        art = reg.get(m.artifact_id)
        assert art.status == "validated"
        assert art.validation["passed"] is True
        assert "model-critic" in art.validation["validators"]
    finally:
        import shutil
        shutil.rmtree(str(Path(os.environ.get("TEMP", ".")) / "_p05_reg"),
                      ignore_errors=True)


def test_whitelist_config():
    """白名单仅含 runtime 验证管线（不信任显式 caller 参数）。"""
    assert VALIDATION_CALLER_ALLOWED_SUBSTR == (
        "core/runtime/execution/validators.py",
        "core/runtime/execution/handlers.py",
    )


def test_critic_skills_no_mark_validated():
    """critic SKILL.md 不含 mark_validated 指令。"""
    for rel in ("core/skills/critics/model-critic/SKILL.md",
                "core/skills/critics/experiment-critic/SKILL.md"):
        text = (REPO / rel).read_text(encoding="utf-8")
        assert "mark_validated" not in text, rel


def test_repo_grep_only_whitelisted():
    """全仓 mark_validated( 仅 registry/artifact 定义 + validator/白名单 + 测试。"""
    out = subprocess.run(
        ["rg", "-l", r"mark_validated\(", "core", "tests", "research"],
        cwd=str(REPO), capture_output=True, text=True).stdout
    files = [f for f in out.splitlines() if f.strip()]
    # .md 文档是描述性文本（门禁设计说明），不是代码调用点；
    # 路径统一正斜杠再比前缀（Windows rg 输出为反斜杠）
    norm = [os.path.normpath(f).replace("\\", "/") for f in files]
    bad = [f for f, n in zip(files, norm)
           if not f.endswith(".md")
           and not n.startswith(("core/runtime/artifacts/",
                                 "tests/", "research/P15/analysis/"))]
    assert bad == [], f"mark_validated 出现在非白名单文件: {bad}"
