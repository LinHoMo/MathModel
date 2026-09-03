"""
29 个 agent 的 evals.json 与 openai.yaml 结构测试

测试对象：四手 29 个 agent 各自的 evals/evals.json 与 openai.yaml。
本轮为补门禁质量新增的运行时配置与评测用例。

约束：
  - 不依赖 PyYAML（openai.yaml 用正则提取字段）
  - 测试从项目根目录运行（pytest 根目录为项目根）

evals.json 结构契约：
  {
    "skill_name": "<agent-name>",
    "evals": [
      {
        "id": <int>,
        "prompt": "<str>",
        "expected_output": "<str>",
        "assertions": ["<str>", ...]  # 非空字符串数组
      }
    ]
  }

openai.yaml 结构契约（正则提取）：
  interface:
    display_name: "..."
    short_description: "..."
    default_prompt: "..."
  runtime:
    utg_layer: L?
"""
import json
import os
import re

import pytest


# ---------------------------------------------------------------------------
# 29 个 agent 的 (hand, agent_name) 清单
# ---------------------------------------------------------------------------
AGENTS = [
    # Modeler（8）
    ("Modeler", "problem-parser"),
    ("Modeler", "type-classifier"),
    ("Modeler", "literature-searcher"),
    ("Modeler", "method-matcher"),
    ("Modeler", "model-builder"),
    ("Modeler", "dag-builder"),
    ("Modeler", "assumption-validator"),
    ("Modeler", "spec-auditor"),
    # Programmer（6）
    ("Programmer", "template-selector"),
    ("Programmer", "code-implementer"),
    ("Programmer", "test-runner"),
    ("Programmer", "result-verifier"),
    ("Programmer", "guardrails-checker"),
    ("Programmer", "hash-auditor"),
    # Writer（7）
    ("Writer", "structure-planner"),
    ("Writer", "section-writer"),
    ("Writer", "figure-generator"),
    ("Writer", "reference-curator"),
    ("Writer", "consistency-checker"),
    ("Writer", "guardrails-checker"),
    ("Writer", "final-validator"),
    # Reviewer（8）
    ("Reviewer", "scorer-academic"),
    ("Reviewer", "scorer-engineering"),
    ("Reviewer", "scorer-judge"),
    ("Reviewer", "scorer-reader"),
    ("Reviewer", "scorer-adversarial"),
    ("Reviewer", "weakness-hunter"),
    ("Reviewer", "revision-planner"),
    ("Reviewer", "revision-executor"),
]


def _evals_path(hand, agent_name):
    """返回 agent 的 evals/evals.json 相对路径。"""
    return os.path.join("core", hand, "agents", agent_name, "evals", "evals.json")


def _openai_yaml_path(hand, agent_name):
    """返回 agent 的 openai.yaml 相对路径。"""
    return os.path.join("core", hand, "agents", agent_name, "openai.yaml")


def _read_text(path):
    """读取文件文本（UTF-8）。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ===========================================================================
# evals.json 结构测试
# ===========================================================================
class TestEvalsStructure:
    """29 个 evals/evals.json 结构完整性"""

    def test_29_evals_files_exist(self):
        """29 个 evals.json 文件全部存在"""
        missing = []
        for hand, agent_name in AGENTS:
            p = _evals_path(hand, agent_name)
            if not os.path.exists(p):
                missing.append(p)
        assert missing == [], f"evals.json 缺失: {missing}"
        assert len(AGENTS) == 29, f"agent 总数应为 29，实际 {len(AGENTS)}"

    def test_all_evals_valid_json(self):
        """每个 evals.json 是合法 JSON"""
        for hand, agent_name in AGENTS:
            p = _evals_path(hand, agent_name)
            assert os.path.exists(p), f"{p} 不存在"
            try:
                data = json.loads(_read_text(p))
            except json.JSONDecodeError as e:
                pytest.fail(f"{p} JSON 解析失败: {e}")

    def test_all_evals_have_skill_name(self):
        """每个 evals.json 含 skill_name 字段（字符串）"""
        for hand, agent_name in AGENTS:
            p = _evals_path(hand, agent_name)
            data = json.loads(_read_text(p))
            assert "skill_name" in data, f"{p} 缺 skill_name"
            assert isinstance(data["skill_name"], str), \
                f"{p}: skill_name 不是字符串"
            assert data["skill_name"].strip() != "", \
                f"{p}: skill_name 为空"

    def test_all_evals_have_evals_array(self):
        """每个 evals.json 含 evals 数组"""
        for hand, agent_name in AGENTS:
            p = _evals_path(hand, agent_name)
            data = json.loads(_read_text(p))
            assert "evals" in data, f"{p} 缺 evals 字段"
            assert isinstance(data["evals"], list), \
                f"{p}: evals 不是数组"
            assert len(data["evals"]) >= 1, \
                f"{p}: evals 数组为空"

    def test_each_eval_has_required_fields(self):
        """每个 eval 含 id/prompt/expected_output/assertions"""
        for hand, agent_name in AGENTS:
            p = _evals_path(hand, agent_name)
            data = json.loads(_read_text(p))
            for i, ev in enumerate(data["evals"]):
                assert isinstance(ev, dict), \
                    f"{p}: evals[{i}] 不是 dict"
                # id
                assert "id" in ev, f"{p}: evals[{i}] 缺 id"
                # prompt
                assert "prompt" in ev, f"{p}: evals[{i}] 缺 prompt"
                assert isinstance(ev["prompt"], str) and ev["prompt"].strip(), \
                    f"{p}: evals[{i}] prompt 非字符串或空"
                # expected_output
                assert "expected_output" in ev, \
                    f"{p}: evals[{i}] 缺 expected_output"
                assert isinstance(ev["expected_output"], str) \
                    and ev["expected_output"].strip(), \
                    f"{p}: evals[{i}] expected_output 非字符串或空"
                # assertions
                assert "assertions" in ev, \
                    f"{p}: evals[{i}] 缺 assertions"
                assert isinstance(ev["assertions"], list), \
                    f"{p}: evals[{i}] assertions 不是数组"
                assert len(ev["assertions"]) >= 1, \
                    f"{p}: evals[{i}] assertions 数组为空"

    def test_assertions_are_non_empty_strings(self):
        """assertions 是非空字符串数组"""
        for hand, agent_name in AGENTS:
            p = _evals_path(hand, agent_name)
            data = json.loads(_read_text(p))
            for i, ev in enumerate(data["evals"]):
                for j, a in enumerate(ev["assertions"]):
                    assert isinstance(a, str), \
                        f"{p}: evals[{i}].assertions[{j}] 不是字符串"
                    assert a.strip() != "", \
                        f"{p}: evals[{i}].assertions[{j}] 为空字符串"

    def test_skill_name_matches_agent_name(self):
        """evals.json 的 skill_name 与 agent 目录名一致"""
        for hand, agent_name in AGENTS:
            p = _evals_path(hand, agent_name)
            data = json.loads(_read_text(p))
            assert data["skill_name"] == agent_name, \
                f"{p}: skill_name={data['skill_name']} != {agent_name}"


# ===========================================================================
# openai.yaml 结构测试（正则提取，不依赖 PyYAML）
# ===========================================================================
class TestOpenaiYaml:
    """29 个 openai.yaml 结构完整性"""

    def test_29_openai_yaml_files_exist(self):
        """29 个 openai.yaml 文件全部存在"""
        missing = []
        for hand, agent_name in AGENTS:
            p = _openai_yaml_path(hand, agent_name)
            if not os.path.exists(p):
                missing.append(p)
        assert missing == [], f"openai.yaml 缺失: {missing}"

    def test_all_yaml_have_display_name(self):
        """每个 openai.yaml 含 display_name 字段"""
        # YAML 字段缩进在 interface: 段下，允许前导空白
        pat = re.compile(r"^\s*display_name\s*:\s*(.+)$", re.MULTILINE)
        missing = []
        for hand, agent_name in AGENTS:
            p = _openai_yaml_path(hand, agent_name)
            content = _read_text(p)
            m = pat.search(content)
            if m is None:
                missing.append(p)
            else:
                val = m.group(1).strip().strip('"\'')
                assert val, f"{p}: display_name 为空"
        assert missing == [], f"缺 display_name: {missing}"

    def test_all_yaml_have_short_description(self):
        """每个 openai.yaml 含 short_description 字段"""
        pat = re.compile(r"^\s*short_description\s*:\s*(.+)$", re.MULTILINE)
        missing = []
        for hand, agent_name in AGENTS:
            p = _openai_yaml_path(hand, agent_name)
            content = _read_text(p)
            m = pat.search(content)
            if m is None:
                missing.append(p)
            else:
                val = m.group(1).strip().strip('"\'')
                assert val, f"{p}: short_description 为空"
        assert missing == [], f"缺 short_description: {missing}"

    def test_all_yaml_have_default_prompt(self):
        """每个 openai.yaml 含 default_prompt 字段"""
        pat = re.compile(r"^\s*default_prompt\s*:\s*(.+)$", re.MULTILINE)
        missing = []
        for hand, agent_name in AGENTS:
            p = _openai_yaml_path(hand, agent_name)
            content = _read_text(p)
            m = pat.search(content)
            if m is None:
                missing.append(p)
            else:
                val = m.group(1).strip().strip('"\'')
                assert val, f"{p}: default_prompt 为空"
        assert missing == [], f"缺 default_prompt: {missing}"

    def test_all_yaml_have_utg_layer(self):
        """每个 openai.yaml 含 utg_layer 字段且取值合法"""
        valid_layers = {"L1", "L2", "L3", "L4", "L5", "L6", "L5+L6"}
        # utg_layer 缩进在 runtime: 段下，允许前导空白
        pat = re.compile(r"^\s*utg_layer\s*:\s*(\S+)", re.MULTILINE)
        issues = []
        for hand, agent_name in AGENTS:
            p = _openai_yaml_path(hand, agent_name)
            content = _read_text(p)
            m = pat.search(content)
            if m is None:
                issues.append(f"{p}: 缺 utg_layer")
                continue
            val = m.group(1).strip().strip('"\'')
            if val not in valid_layers:
                issues.append(f"{p}: utg_layer={val} 非法")
        assert issues == [], f"utg_layer 问题: {issues}"

    def test_all_yaml_have_runtime_section(self):
        """每个 openai.yaml 含 runtime: 段"""
        for hand, agent_name in AGENTS:
            p = _openai_yaml_path(hand, agent_name)
            content = _read_text(p)
            assert re.search(r"^runtime\s*:", content, re.MULTILINE), \
                f"{p}: 缺 runtime 段"

    def test_all_yaml_have_interface_section(self):
        """每个 openai.yaml 含 interface: 段"""
        for hand, agent_name in AGENTS:
            p = _openai_yaml_path(hand, agent_name)
            content = _read_text(p)
            assert re.search(r"^interface\s*:", content, re.MULTILINE), \
                f"{p}: 缺 interface 段"

    def test_default_prompt_references_skill_name(self):
        """default_prompt 含 $<agent_name> 引用（如 $spec-auditor）"""
        for hand, agent_name in AGENTS:
            p = _openai_yaml_path(hand, agent_name)
            content = _read_text(p)
            m = re.search(r"^\s*default_prompt\s*:\s*(.+)$", content, re.MULTILINE)
            assert m is not None, f"{p}: 缺 default_prompt"
            val = m.group(1).strip()
            # 应含 $agent_name 或 Use $ 字样
            assert f"${agent_name}" in val or "Use $" in val, \
                f"{p}: default_prompt 未引用 ${agent_name}"
