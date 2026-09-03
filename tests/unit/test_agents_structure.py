"""
agent 结构完整性测试

测试四手（Modeler / Programmer / Writer / Reviewer）agents 目录结构、agent 数量与名称、
SKILL.md frontmatter 字段、Self-Check 章节、catalog.yaml 与 AGENTS.md 完整性。

UTG 多 Agent 架构收尾验证：29 个 agent 按 UTG L1–L6 串联。
测试从项目根目录运行（pytest 根目录为项目根）。
"""
import os
import re

import pytest


# ---------------------------------------------------------------------------
# 四手预期 agent 名称与 UTG 层映射（与各 SKILL.md frontmatter 一致）
# ---------------------------------------------------------------------------
EXPECTED_AGENTS = {
    "Modeler": {
        "problem-parser": "L1",
        "type-classifier": "L1",
        "literature-searcher": "L2",
        "method-matcher": "L2",
        "model-builder": "L3",
        "dag-builder": "L4",
        "assumption-validator": "L4",
        "spec-auditor": "L5+L6",
    },
    "Programmer": {
        "template-selector": "L1",
        "code-implementer": "L2",
        "test-runner": "L3",
        "result-verifier": "L4",
        "guardrails-checker": "L5",
        "hash-auditor": "L6",
    },
    "Writer": {
        "structure-planner": "L1",
        "section-writer": "L2",
        "figure-generator": "L2",
        "reference-curator": "L3",
        "consistency-checker": "L4",
        "guardrails-checker": "L5",
        "final-validator": "L6",
    },
    "Reviewer": {
        "scorer-academic": "L4",
        "scorer-engineering": "L4",
        "scorer-judge": "L4",
        "scorer-reader": "L4",
        "scorer-adversarial": "L4",
        "weakness-hunter": "L4",
        "revision-planner": "L5",
        "revision-executor": "L6",
    },
}

VALID_UTG_LAYERS = {"L1", "L2", "L3", "L4", "L5", "L6", "L5+L6"}

FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)


def _all_expected_agent_names():
    """返回 29 个 agent name 的列表。"""
    names = []
    for hand_agents in EXPECTED_AGENTS.values():
        names.extend(hand_agents.keys())
    return names


def _iter_skill_paths():
    """yield (hand, agent_name, skill_path)，路径不保证存在。"""
    for hand, agents in EXPECTED_AGENTS.items():
        for agent_name in agents:
            yield hand, agent_name, os.path.join("core", hand, "agents", agent_name, "SKILL.md")


class TestAgentsDirectories:
    """四手 agents 目录存在"""

    def test_modeler_agents_dir(self):
        assert os.path.isdir("core/Modeler/agents")

    def test_programmer_agents_dir(self):
        assert os.path.isdir("core/Programmer/agents")

    def test_writer_agents_dir(self):
        assert os.path.isdir("core/Writer/agents")

    def test_reviewer_agents_dir(self):
        assert os.path.isdir("core/Reviewer/agents")


class TestAgentsCount:
    """四手 agent 数量与名称正确（8/6/7/8 = 29）"""

    def test_modeler_agents_count(self):
        names = _subdirs_with_skill("core/Modeler/agents")
        assert len(names) == 8
        for n in EXPECTED_AGENTS["Modeler"]:
            assert n in names, f"Modeler 缺 agent: {n}"

    def test_programmer_agents_count(self):
        names = _subdirs_with_skill("core/Programmer/agents")
        assert len(names) == 6
        for n in EXPECTED_AGENTS["Programmer"]:
            assert n in names, f"Programmer 缺 agent: {n}"

    def test_writer_agents_count(self):
        names = _subdirs_with_skill("core/Writer/agents")
        assert len(names) == 7
        for n in EXPECTED_AGENTS["Writer"]:
            assert n in names, f"Writer 缺 agent: {n}"

    def test_reviewer_agents_count(self):
        names = _subdirs_with_skill("core/Reviewer/agents")
        assert len(names) == 8
        for n in EXPECTED_AGENTS["Reviewer"]:
            assert n in names, f"Reviewer 缺 agent: {n}"

    def test_total_agents_count(self):
        total = sum(len(agents) for agents in EXPECTED_AGENTS.values())
        assert total == 29


def _subdirs_with_skill(agents_dir):
    """返回 agents 目录下含 SKILL.md 的子目录名列表。"""
    names = []
    for sub in sorted(os.listdir(agents_dir)):
        sub_path = os.path.join(agents_dir, sub)
        if os.path.isdir(sub_path) and os.path.exists(os.path.join(sub_path, "SKILL.md")):
            names.append(sub)
    return names


class TestAgentsFrontmatter:
    """每个 agent SKILL.md 的 frontmatter 字段与 UTG 层合法性"""

    REQUIRED_FIELDS = ["name", "utg_layer", "inputs", "outputs", "stage"]

    def test_all_agents_have_frontmatter(self):
        """每个 agent SKILL.md 含 YAML frontmatter"""
        missing = []
        for hand, agent_name, skill_path in _iter_skill_paths():
            assert os.path.exists(skill_path), f"{skill_path} 不存在"
            content = _read(skill_path)
            if not FRONTMATTER_PATTERN.match(content):
                missing.append(f"{hand}/{agent_name}")
        assert missing == [], f"缺少 frontmatter: {missing}"

    def test_frontmatter_required_fields(self):
        """frontmatter 含 name/utg_layer/inputs/outputs/stage"""
        issues = []
        for hand, agent_name, skill_path in _iter_skill_paths():
            content = _read(skill_path)
            m = FRONTMATTER_PATTERN.match(content)
            assert m is not None, f"{hand}/{agent_name} 无 frontmatter"
            fm = m.group(1)
            for field in self.REQUIRED_FIELDS:
                if not re.search(r"^%s\s*:" % re.escape(field), fm, re.MULTILINE):
                    issues.append(f"{hand}/{agent_name} 缺 {field}")
        assert issues == [], f"frontmatter 缺字段: {issues}"

    def test_utg_layer_values_valid(self):
        """每个 agent utg_layer 取值合法"""
        invalid = []
        for hand, agent_name, skill_path in _iter_skill_paths():
            content = _read(skill_path)
            m = FRONTMATTER_PATTERN.match(content)
            assert m is not None
            fm = m.group(1)
            layer_m = re.search(r"^utg_layer\s*:\s*(\S+)", fm, re.MULTILINE)
            assert layer_m is not None, f"{hand}/{agent_name} 缺 utg_layer"
            val = layer_m.group(1).strip().strip('"\'')
            if val not in VALID_UTG_LAYERS:
                invalid.append(f"{hand}/{agent_name}={val}")
        assert invalid == [], f"非法 utg_layer: {invalid}"

    def test_utg_layer_matches_expected_mapping(self):
        """UTG 层映射与预期一致"""
        mismatches = []
        for hand, agents in EXPECTED_AGENTS.items():
            for agent_name, expected_layer in agents.items():
                skill_path = os.path.join("core", hand, "agents", agent_name, "SKILL.md")
                content = _read(skill_path)
                m = FRONTMATTER_PATTERN.match(content)
                assert m is not None
                fm = m.group(1)
                layer_m = re.search(r"^utg_layer\s*:\s*(\S+)", fm, re.MULTILINE)
                assert layer_m is not None
                actual = layer_m.group(1).strip().strip('"\'')
                if actual != expected_layer:
                    mismatches.append(
                        f"{hand}/{agent_name}: 期望 {expected_layer}, 实际 {actual}"
                    )
        assert mismatches == [], f"UTG 层映射不符: {mismatches}"


class TestAgentsSelfCheck:
    """每个 agent SKILL.md 含 ## Self-Check 章节"""

    def test_all_agents_have_self_check(self):
        missing = []
        for hand, agent_name, skill_path in _iter_skill_paths():
            content = _read(skill_path)
            if not re.search(r"^##\s*Self-Check\s*$", content, re.MULTILINE):
                missing.append(f"{hand}/{agent_name}")
        assert missing == [], f"缺少 Self-Check: {missing}"


class TestCatalogYaml:
    """catalog.yaml 含全部 29 个 agent name"""

    def test_catalog_exists(self):
        assert os.path.exists("catalog.yaml")

    def test_catalog_contains_all_agents(self):
        with open("catalog.yaml", "r", encoding="utf-8") as f:
            content = f.read()
        names = re.findall(r"^\s+- name: (\S+)", content, re.MULTILINE)
        name_set = set(names)
        missing = [n for n in _all_expected_agent_names() if n not in name_set]
        assert missing == [], f"catalog.yaml 缺 agent: {missing}"


class TestAgentsMd:
    """AGENTS.md 含关键章节"""

    def test_agents_md_exists(self):
        assert os.path.exists("AGENTS.md")

    def test_agents_md_has_agent_index(self):
        with open("AGENTS.md", "r", encoding="utf-8") as f:
            content = f.read()
        assert "## Agent 索引" in content

    def test_agents_md_has_env_entry(self):
        with open("AGENTS.md", "r", encoding="utf-8") as f:
            content = f.read()
        assert "## env 配置入口" in content


def _read(path):
    """读取文件文本（UTF-8）。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
