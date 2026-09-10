#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABOUTME: 从 catalog/v3.yaml 单一真源生成 src/modeling_harness/runtime/adapters/openai.yaml（V3 运行时入口）
ABOUTME: --check 模式检测漂移，供 doctor.py 调用

用法：
    python src/modeling_harness/cli/gen_runtime_manifest.py            # 生成/覆盖 src/modeling_harness/runtime/adapters/openai.yaml
    python src/modeling_harness/cli/gen_runtime_manifest.py --check    # 漂移检测，drift 即 EXIT 1
    python src/modeling_harness/cli/gen_runtime_manifest.py --verify   # 校验 V3 角色/validator/工具路径
"""

import argparse
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
CATALOG_PATH = ROOT / "catalog.yaml"
OPENAI_PATH = ROOT / "src" / "modeling_harness" / "runtime" / "adapters" / "openai.yaml"


# ---------------------------------------------------------------------------
# 极简 YAML 解析器（扩展 env/loader.py 的两级解析为 N 级，支持列表 / 嵌套）
# ---------------------------------------------------------------------------

def _strip_comment(line):
    in_s = in_d = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_d: in_s = not in_s
        elif ch == '"' and not in_s: in_d = not in_d
        elif ch == "#" and not in_s and not in_d:
            if i == 0 or line[i - 1] in (" ", "\t"):
                return line[:i]
    return line


def _parse_yaml_text(text):
    """递归下降 YAML 解析器。支持: 标量、list（- item）、嵌套 dict、注释。
    基于缩进层级（spaces-only，与 catalog.yaml 一致）。"""

    lines = text.splitlines()

    def parse(block_lines, base_indent):
        """解析一个 block（共享 base_indent 的连续行），返回 (result, lines_consumed) 或内联返回。"""
        result = []
        i = 0
        while i < len(block_lines):
            raw = block_lines[i]
            stripped_comment = _strip_comment(raw).rstrip()
            if not stripped_comment.strip():
                i += 1
                continue

            # count indent
            indent = len(raw) - len(raw.lstrip(" "))
            if indent < base_indent:
                break
            if indent > base_indent:
                # should not happen at top of parse; break back to caller
                break

            content = stripped_comment
            i += 1

            # list item "- ..."
            if content.lstrip().startswith("- "):
                item_text = content.lstrip()[2:].strip()
                # collect nested lines for this item (indent > current)
                nested = []
                while i < len(block_lines):
                    r = block_lines[i]
                    sc = _strip_comment(r).rstrip()
                    if not sc.strip():
                        nested.append(r)
                        i += 1
                        continue
                    ind = len(r) - len(r.lstrip(" "))
                    if ind > indent:
                        nested.append(r)
                        i += 1
                    else:
                        break

                if ": " in item_text or item_text.endswith(":"):
                    # dict item in list
                    sub_lines = [" " * (indent + 2) + item_text] + nested
                    item = parse(sub_lines, indent + 2)
                    if isinstance(item, list) and len(item) == 1:
                        item = item[0]
                    result.append(item)
                elif nested:
                    # composite list item with nested
                    sub_lines = [" " * (indent + 2) + item_text] + nested
                    item = parse(sub_lines, indent + 2)
                    if isinstance(item, list) and len(item) == 1:
                        item = item[0]
                    result.append(item)
                else:
                    result.append(_coerce_scalar(item_text))
            elif ":" in content:
                key, _, val = content.partition(":")
                key = key.strip()
                val = val.strip()

                # collect nested lines
                nested = []
                while i < len(block_lines):
                    r = block_lines[i]
                    sc = _strip_comment(r).rstrip()
                    if not sc.strip():
                        nested.append(r)
                        i += 1
                        continue
                    ind = len(r) - len(r.lstrip(" "))
                    if ind > indent:
                        nested.append(r)
                        i += 1
                    else:
                        break

                # ensure result is a dict
                if not result or not isinstance(result[-1], dict):
                    result.append({})
                target = result[-1]

                if val:
                    target[key] = _coerce_scalar(val)
                elif nested:
                    sub_lines = nested
                    nested_result = parse(sub_lines, indent + 2)
                    # nested_result might be list or dict
                    target[key] = nested_result
                else:
                    target[key] = None
            else:
                result.append(_coerce_scalar(content.strip()))
        return result

    parsed = parse(lines, 0)
    if isinstance(parsed, list) and len(parsed) == 1:
        return parsed[0]
    return parsed


def _coerce_scalar(s):
    s = s.strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    if s.lower() in ("true", "yes", "on"): return True
    if s.lower() in ("false", "no", "off"): return False
    if s.lower() in ("null", "none", "~", ""): return None
    try: return int(s)
    except ValueError: pass
    try: return float(s)
    except ValueError: pass
    return s


REGISTRY_DIR = ROOT / "catalog"
# registry 文件名 -> 合并进主 catalog 的键名（protocol_tools.yaml 历史键名为 tools）
REGISTRY_FILES = {"v3": "v3", "external_skills": "external_skills",
                  "protocol_tools": "tools"}


def merge_registries(catalog):
    """把 catalog/*.yaml 注册表合并进主 catalog（键不存在时才合并，主文件可覆盖）。"""
    if not REGISTRY_DIR.is_dir():
        return catalog
    for fname, key in REGISTRY_FILES.items():
        f = REGISTRY_DIR / (fname + ".yaml")
        if key not in catalog and f.exists():
            data = _parse_yaml_text(f.read_text(encoding="utf-8"))
            # 注册表文件保留原始顶层键（如 v3:），剥掉；解析器可能把深层
            # list-of-dict 包成单元素 list，一并解包
            if isinstance(data, dict) and list(data.keys()) == [fname]:
                data = data[fname]
            if isinstance(data, list) and len(data) == 1 \
                    and isinstance(data[0], dict):
                data = data[0]
            catalog[key] = data
    return catalog


def load_catalog():
    text = CATALOG_PATH.read_text(encoding="utf-8")
    return merge_registries(_parse_yaml_text(text))


# ---------------------------------------------------------------------------
# 生成 openai.yaml
# ---------------------------------------------------------------------------

def _agent_entry(a):
    """把 catalog.yaml 里的 agent dict 映射为 openai.yaml pipeline dict。"""
    return {
        "name": a["name"],
        "stage": a.get("stage"),
        "utg_layer": a.get("utg_layer", ""),
        "description": a.get("description", ""),
        "artifact": a.get("artifact", ""),
    }


def generate_openai_yaml(catalog):
    """V3：从 catalog/v3.yaml 视图生成 OpenAI Agents SDK 兼容配置。

    产出：MODEL_IR(JSON) + 模型描述文档(MD/Mermaid)；无论文生成、无 V2 兼容。
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds") + "Z"
    lines = [
        "# OpenAI Agents SDK 兼容配置",
        "# 用于在 OpenAI Agents SDK 中加载 Modeling-Harness 技能",
        "# *** 本文件由 src/modeling_harness/cli/gen_runtime_manifest.py 自动生成 ***",
        "# *** 请勿手工编辑 —— 以 catalog/v3.yaml 为单一真源 ***",
        f"# 最近生成时间: {timestamp}",
        "",
        'name: "modeling-harness-skills"',
        'version: "3.0.0"',
        'description: "数学建模认知工作流运行时（V3）"',
        "",
        'instructions_file: "AGENTS.md"',
        "",
        "tools:",
        '  - name: "validate"',
        '    description: "项目级完整性校验"',
        '    function: "python src/modeling_harness/cli/validate.py {project}"',
        "",
        '  - name: "catalog_check"',
        '    description: "catalog 三方一致性检查"',
        '    function: "python src/modeling_harness/cli/catalog_check.py --check"',
        "",
        '  - name: "new_project"',
        '    description: "创建新项目脚手架"',
        '    function: "python src/modeling_harness/cli/new_project.py {project_name} --competition {competition}"',
        "",
        '  - name: "knowledge"',
        '    description: "方法卡检索"',
        '    function: "python src/modeling_harness/cli/knowledge.py recommend --types {types}"',
        "",
        '  - name: "doctor"',
        '    description: "环境预检"',
        '    function: "python src/modeling_harness/cli/doctor.py"',
        "",
        "env:",
        '  config_file: "core/env/config.yaml"',
        '  loader: "core/env/loader.py"',
        "",
        "knowledge_base:",
        '  methodology: "src/modeling_harness/knowledge/methodology/"',
        '  cookbooks: "src/modeling_harness/knowledge/cookbooks/"',
        '  playbooks: "src/modeling_harness/knowledge/playbooks/"',
        '  validation: "src/modeling_harness/validators/modules/"',
        "",
        "validation_scripts:",
        '  validate: "src/modeling_harness/cli/validate.py"',
        '  doctor: "src/modeling_harness/cli/doctor.py"',
        "",
    ]
    return "\n".join(lines)


def check_drift(generated_text):
    if not OPENAI_PATH.exists():
        return False, ["src/modeling_harness/runtime/adapters/openai.yaml 不存在，无法比对漂移"]
    current = OPENAI_PATH.read_text(encoding="utf-8")
    # 去掉自动生成头部时间戳行再比
    import re
    clean_generated = re.sub(r"# 最近生成时间:.*\n", "", generated_text)
    clean_current = re.sub(r"# 最近生成时间:.*\n", "", current)
    if clean_generated != clean_current:
        diffs = []
        gen_lines = clean_generated.splitlines()
        cur_lines = clean_current.splitlines()
        import difflib
        for line in difflib.unified_diff(cur_lines, gen_lines, lineterm="", n=1):
            if line.startswith("+") and not line.startswith("+++"):
                diffs.append(f"  + {line[1:].strip()}")
            elif line.startswith("-") and not line.startswith("---"):
                diffs.append(f"  - {line[1:].strip()}")
        if not diffs:
            # 只是空白/timestamp 差异
            return True, []
        return False, diffs[:20]
    return True, []


# ---------------------------------------------------------------------------
# 验证
# ---------------------------------------------------------------------------

def verify(catalog):
    """V3 一致性校验：角色/validator/核心工具路径存在。"""
    errors = []
    v3 = catalog.get("v3", {}) or {}
    for role in v3.get("roles", []):
        p = role.get("path", "")
        if p and not (ROOT / p).exists():
            errors.append(f"角色路径不存在: {p}")
    for val in v3.get("validators", []):
        p = val.get("path", "")
        if p and not (ROOT / p).exists():
            errors.append(f"validator 路径不存在: {p}")
    for tool in ("validate.py", "catalog_check.py", "new_project.py",
                 "knowledge.py", "doctor.py", "benchmark.py",
                 "diagram_gen.py", "scholar_fetch.py"):
        if not (ROOT / "src" / "modeling_harness" / "cli" / tool).exists():
            errors.append(f"工具缺失: src/modeling_harness/cli/{tool}")
    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="从 catalog.yaml 生成 src/modeling_harness/runtime/adapters/openai.yaml（Codex 运行时入口）")
    ap.add_argument("--check", action="store_true", help="漂移检测，drift 即 EXIT 1")
    ap.add_argument("--verify", action="store_true", help="验证 catalog 内在一致性")
    args = ap.parse_args()

    catalog = load_catalog()
    generated = generate_openai_yaml(catalog)

    errs = verify(catalog)
    if errs:
        for e in errs:
            print(f"[verify][FAIL] {e}")
        if args.verify:
            return 1

    if args.check:
        ok, diffs = check_drift(generated)
        if ok:
            print("[check] src/modeling_harness/runtime/adapters/openai.yaml 与 catalog.yaml 一致，无漂移")
            return 0
        print(f"[check] 检测到 {len(diffs)} 处漂移（应重新生成）:")
        for d in diffs:
            print(d)
        return 1

    # 写文件
    OPENAI_PATH.parent.mkdir(parents=True, exist_ok=True)
    OPENAI_PATH.write_text(generated, encoding="utf-8")
    v3 = catalog.get("v3", {}) or {}
    n_roles = len(v3.get("roles", []))
    n_nodes = len(v3.get("nodes", []))
    print(f"[gen] src/modeling_harness/runtime/adapters/openai.yaml 已生成：V3 {n_roles} 角色 {n_nodes} 节点")
    return 0


if __name__ == "__main__":
    sys.exit(main())
