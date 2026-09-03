#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABOUTME: 从 catalog.yaml 单一真源生成 agents/openai.yaml（Codex 运行时入口）
ABOUTME: --check 模式检测漂移，供 doctor.py 调用

用法：
    python core/tools/gen_runtime_manifest.py            # 生成/覆盖 agents/openai.yaml
    python core/tools/gen_runtime_manifest.py --check    # 漂移检测，drift 即 EXIT 1
    python core/tools/gen_runtime_manifest.py --verify   # 校验 29 agent/8 reviewer 等
"""

import argparse
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "catalog.yaml"
OPENAI_PATH = ROOT / "agents" / "openai.yaml"


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


def load_catalog():
    text = CATALOG_PATH.read_text(encoding="utf-8")
    return _parse_yaml_text(text)


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
    hands_raw = catalog.get("hands", [])
    # build lookup by stage_order / name
    by_name = {h["name"]: h for h in hands_raw}

    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds") + "Z"
    header_lines = [
        "# OpenAI Agents SDK 兼容配置",
        "# 用于在 OpenAI Agents SDK 中加载 MathModelSkills 技能",
        "# *** 本文件由 core/tools/gen_runtime_manifest.py 自动生成 ***",
        "# *** 请勿手工编辑 —— 以 catalog.yaml 为单一真源 ***",
        f"# 最近生成时间: {timestamp}",
        "",
        f"# {len(hands_raw)} 手 {sum(len(h.get('agents', [])) for h in hands_raw)} agent（自动生成）",
        'name: "mathmodeling-skills"',
        'version: "2.0.0"',
        'description: "数学建模竞赛全流程 AI 技能包"',
        "",
        'instructions_file: "core/AGENTS.md"',
        "",
        "tools:",
    ]

    # tools block (static, preserve)
    tools_block = [
        ('state_init', '初始化/恢复项目状态', 'python core/tools/state.py {project} init'),
        ('state_status', '查看当前执行进度', 'python core/tools/state.py {project} status'),
        ('state_advance', '推进到下一步', 'python core/tools/state.py {project} advance {hand} {agent} --output {output}'),
        ('gate_check', '运行单步/全链路门禁', 'python core/tools/gate.py {project} {hand} {agent}'),
        ('validate_project', '项目级完整性校验', 'python core/tools/validate_project.py {project}'),
    ]

    tool_lines = []
    for name, desc, fn in tools_block:
        tool_lines += [
            f'  - name: "{name}"',
            f'    description: "{desc}"',
            f'    function: "{fn}"',
            '',
        ]

    tail_lines = [
        "# 环境配置",
        "env:",
        '  config_file: "core/env/config.yaml"',
        '  loader: "core/env/loader.py"',
        "",
        "# 友好模式配置",
        "friendly_mode:",
        "  enabled: true",
        '  description: "关键决策以编号选项呈现，用户输入数字即可推进"',
        '  fallback_prompt: "让我决定 (推荐 X)"',
        "",
        "# 执行流水线定义",
        "pipeline:",
    ]

    agent_block_lines = []
    for h in sorted(hands_raw, key=lambda x: x.get("stage_order", 0)):
        h_name = h["name"]
        h_desc = h.get("description", "")
        agents = h.get("agents", [])
        agent_block_lines += [
            f'  - hand: "{h_name}"',
            f'    description: "{h_desc}"',
            "    agents:",
        ]
        for a in agents:
            e = _agent_entry(a)
            agent_block_lines += [
                f'      - name: "{e["name"]}"',
                f'        stage: {e["stage"]}',
                f'        utg_layer: "{e["utg_layer"]}"',
                f'        description: "{e["description"]}"',
                f'        artifact: "{e["artifact"]}"',
                "",
            ]

    footer = [
        "",
        "# 契约文件（手间接口）",
        "contracts:",
        '  modeler_output: "output/MODEL_SPEC.md"',
        '  programmer_output: "output/CODE_DELIVERABLES.md"',
        '  writer_output: "output/PAPER_SPEC.md"',
        "",
        "# 知识库引用",
        "knowledge_base:",
        '  methodology: "core/knowledge/methodology/"',
        '  cookbooks: "core/knowledge/cookbooks/"',
        '  playbooks: "core/knowledge/playbooks/"',
        '  paper_cases: "core/knowledge/paper-cases/"',
        '  empirical: "core/knowledge/empirical/"',
        '  validation: "core/knowledge/validation/"',
        '  writing: "core/Writer/knowledge/writing/"',
        '  templates: "core/Writer/knowledge/templates/"',
        "",
        "# 验证脚本",
        "validation_scripts:",
        '  gate: "core/tools/gate.py"',
        '  score: "core/tools/score_artifact.py"',
        '  freeze: "core/tools/freeze_numbers.py"',
        '  validate: "core/tools/validate.py"',
        '  doctor: "core/tools/doctor.py"',
        '  retrospect: "core/tools/retrospect.py"',
        '  render_ai_usage: "core/tools/render_ai_usage.py"',
        '  manifest: "core/tools/gen_runtime_manifest.py"',
    ]

    all_lines = (
        header_lines + [""] + tool_lines + tail_lines
        + agent_block_lines + footer
    )

    out = "\n".join(all_lines)
    if not out.endswith("\n"):
        out += "\n"
    return out


# ---------------------------------------------------------------------------
# --check: 漂移检测
# ---------------------------------------------------------------------------

def check_drift(generated_text):
    if not OPENAI_PATH.exists():
        return False, ["agents/openai.yaml 不存在，无法比对漂移"]
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
    errors = []
    hands = catalog.get("hands", [])
    total_agents = sum(len(h.get("agents", [])) for h in hands)
    if total_agents != 29:
        errors.append(f"agent 总数应为 29，实际 {total_agents}")

    reviewer = next((h for h in hands if h["name"] == "reviewer"), None)
    if not reviewer:
        errors.append("reviewer 手缺失")
    else:
        r_agents = reviewer.get("agents", [])
        names = {a["name"] for a in r_agents}
        if "judge-scorer" in names:
            errors.append("reviewer 包含不存在的 'judge-scorer'（应是 5 个 scorer-*）")
        expected_scorers = {"scorer-academic", "scorer-engineering", "scorer-judge", "scorer-reader", "scorer-adversarial"}
        missing = expected_scorers - names
        if missing:
            errors.append(f"reviewer 缺少 scorer: {missing}")
        if len(r_agents) != 8:
            errors.append(f"reviewer 应有 8 个 agent，实际 {len(r_agents)}")

    # 校验每个 agent path 在文件系统存在
    for h in hands:
        for a in h.get("agents", []):
            p = a.get("path", "")
            if p and not (ROOT / p).exists():
                errors.append(f"agent 路径不存在: {p}")
    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="从 catalog.yaml 生成 agents/openai.yaml（Codex 运行时入口）")
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
            print("[check] agents/openai.yaml 与 catalog.yaml 一致，无漂移")
            return 0
        print(f"[check] 检测到 {len(diffs)} 处漂移（应重新生成）:")
        for d in diffs:
            print(d)
        return 1

    # 写文件
    OPENAI_PATH.parent.mkdir(parents=True, exist_ok=True)
    OPENAI_PATH.write_text(generated, encoding="utf-8")
    hands = catalog.get("hands", [])
    total = sum(len(h.get("agents", [])) for h in hands)
    total_hands = len(hands)
    print(f"[gen] agents/openai.yaml 已生成：{total_hands} 手 {total} agent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
