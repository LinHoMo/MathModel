"""
3 个 laws/rules.md 的反例与速查表测试

测试对象：三手的 laws/rules.md：
  - core/Modeler/laws/rules.md（铁律 M1-M7，每条含"典型反例"）
  - core/Programmer/laws/rules.md（铁律 P1-P9，每条含"典型反例"）
  - core/Writer/laws/rules.md（铁律 W1-W10，每条含"典型反例"）

本轮补门禁质量内容：
  - 每条铁律配 1 个"典型反例"（说明违反后的具体后果）
  - 末尾新增"防错速查表"章节（一页纸速查）

测试从项目根目录运行（pytest 根目录为项目根）。
"""
import os
import re

import pytest


# ---------------------------------------------------------------------------
# 3 个 laws 文件相对路径
# ---------------------------------------------------------------------------
LAWS_FILES = {
    "Modeler": os.path.join("core", "Modeler", "laws", "rules.md"),
    "Programmer": os.path.join("core", "Programmer", "laws", "rules.md"),
    "Writer": os.path.join("core", "Writer", "laws", "rules.md"),
}

# 每条铁律数量（M1-M7 = 7，P1-P9 = 9，W1-W10 = 10）
EXPECTED_ANTIEXAMPLE_COUNT = {
    "Modeler": 7,
    "Programmer": 9,
    "Writer": 10,
}


def _read(path):
    """读取文件文本（UTF-8）。"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


class TestLawsAntiPatterns:
    """3 个 laws/rules.md 含"典型反例"且每条铁律各配反例"""

    def test_all_laws_files_exist(self):
        """3 个 laws/rules.md 文件全部存在"""
        missing = [p for p in LAWS_FILES.values() if not os.path.exists(p)]
        assert missing == [], f"laws 文件缺失: {missing}"

    def test_modeler_has_at_least_7_antiexamples(self):
        """core/Modeler/laws/rules.md 含 >=7 处'典型反例'（M1-M7 每条一个）"""
        content = _read(LAWS_FILES["Modeler"])
        n = len(re.findall(r"典型反例", content))
        assert n >= EXPECTED_ANTIEXAMPLE_COUNT["Modeler"], \
            f"Modeler laws 典型反例数 {n} < {EXPECTED_ANTIEXAMPLE_COUNT['Modeler']}"

    def test_programmer_has_at_least_9_antiexamples(self):
        """core/Programmer/laws/rules.md 含 >=9 处'典型反例'（P1-P9 每条一个）"""
        content = _read(LAWS_FILES["Programmer"])
        n = len(re.findall(r"典型反例", content))
        assert n >= EXPECTED_ANTIEXAMPLE_COUNT["Programmer"], \
            f"Programmer laws 典型反例数 {n} < {EXPECTED_ANTIEXAMPLE_COUNT['Programmer']}"

    def test_writer_has_at_least_10_antiexamples(self):
        """core/Writer/laws/rules.md 含 >=10 处'典型反例'（W1-W10 每条一个）"""
        content = _read(LAWS_FILES["Writer"])
        n = len(re.findall(r"典型反例", content))
        assert n >= EXPECTED_ANTIEXAMPLE_COUNT["Writer"], \
            f"Writer laws 典型反例数 {n} < {EXPECTED_ANTIEXAMPLE_COUNT['Writer']}"

    def test_modeler_rules_m1_to_m7_present(self):
        """Modeler laws 含 M1-M7 全部铁律编号"""
        content = _read(LAWS_FILES["Modeler"])
        for i in range(1, 8):
            assert re.search(r"\bM%d\b" % i, content), \
                f"Modeler laws 缺 M{i}"

    def test_programmer_rules_p1_to_p9_present(self):
        """Programmer laws 含 P1-P9 全部铁律编号"""
        content = _read(LAWS_FILES["Programmer"])
        for i in range(1, 10):
            assert re.search(r"\bP%d\b" % i, content), \
                f"Programmer laws 缺 P{i}"

    def test_writer_rules_w1_to_w10_present(self):
        """Writer laws 含 W1-W10 全部铁律编号"""
        content = _read(LAWS_FILES["Writer"])
        for i in range(1, 11):
            assert re.search(r"\bW%d\b" % i, content), \
                f"Writer laws 缺 W{i}"


class TestLawsCheatSheet:
    """3 个 laws/rules.md 含'防错速查表'章节"""

    def test_modeler_has_cheat_sheet(self):
        """core/Modeler/laws/rules.md 含'防错速查表'章节"""
        content = _read(LAWS_FILES["Modeler"])
        assert "防错速查表" in content, \
            "Modeler laws 缺'防错速查表'章节"
        # 应作为标题出现（# 或 ## 或 ### 防错速查表）
        assert re.search(r"^#+\s*.*防错速查表", content, re.MULTILINE), \
            "Modeler laws '防错速查表' 未作为标题"

    def test_programmer_has_cheat_sheet(self):
        """core/Programmer/laws/rules.md 含'防错速查表'章节"""
        content = _read(LAWS_FILES["Programmer"])
        assert "防错速查表" in content, \
            "Programmer laws 缺'防错速查表'章节"
        assert re.search(r"^#+\s*.*防错速查表", content, re.MULTILINE), \
            "Programmer laws '防错速查表' 未作为标题"

    def test_writer_has_cheat_sheet(self):
        """core/Writer/laws/rules.md 含'防错速查表'章节"""
        content = _read(LAWS_FILES["Writer"])
        assert "防错速查表" in content, \
            "Writer laws 缺'防错速查表'章节"
        assert re.search(r"^#+\s*.*防错速查表", content, re.MULTILINE), \
            "Writer laws '防错速查表' 未作为标题"

    def test_cheat_sheet_has_content(self):
        """'防错速查表'章节非空（标题后有实质内容）"""
        for hand, path in LAWS_FILES.items():
            content = _read(path)
            # 找到"防错速查表"标题位置
            m = re.search(r"^(#+\s*.*防错速查表.*)$", content, re.MULTILINE)
            assert m is not None, f"{hand} laws 缺'防错速查表'标题"
            # 标题后的内容（到下一个同级或更高级标题，或文件末尾）
            start = m.end()
            # 取到下一个 # 标题前的内容
            rest = content[start:]
            # 截到下一个标题
            next_heading = re.search(r"^#{1,6}\s", rest, re.MULTILINE)
            if next_heading:
                section_body = rest[:next_heading.start()]
            else:
                section_body = rest
            # 去除空白行后应有实质内容（>= 50 字符）
            stripped = section_body.strip()
            assert len(stripped) >= 50, \
                f"{hand} laws '防错速查表'章节内容过少 ({len(stripped)} 字符)"
