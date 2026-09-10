"""workflow YAML 子集解析器（零第三方依赖，仓库惯例）。

支持的最小语法（覆盖 workflows/*.yaml 的全部需求）:
    * 注释（# 开头，含行内尾注释）
    * 多级缩进映射（key: value / key:）
    * 块列表（- 标量）与块列表项为映射（- key: value 后续同缩进续行）
    * 行内列表 [a, b, c]
    * 标量: str / int / float / bool / null / 引号字符串

刻意不支持: 锚点 / 多文档 / flow mapping / 多行字符串。
解析失败抛 YamlSyntaxError（fail-closed，不允许 workflow 半懂不懂地跑）。
"""

from __future__ import annotations

import re


class YamlSyntaxError(ValueError):
    """YAML 子集语法错误。"""


def _parse_scalar(s: str):
    s = s.strip()
    if s == "":
        return ""
    if (s.startswith('"') and s.endswith('"') and len(s) >= 2) or \
       (s.startswith("'") and s.endswith("'") and len(s) >= 2):
        return s[1:-1]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(x) for x in _split_inline(inner)]
    if s == "{}":
        return {}
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "none", "~"):
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _split_inline(inner: str) -> list[str]:
    """按逗号切分，尊重引号与方括号嵌套。"""
    parts, buf, depth, quote = [], "", 0, None
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            buf += ch
        elif ch == "[":
            depth += 1
            buf += ch
        elif ch == "]":
            depth -= 1
            buf += ch
        elif ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return parts


def _strip_comment(line: str) -> str:
    """去掉 # 尾注释（引号内的 # 保留）。"""
    out, quote = "", None
    for ch in line:
        if quote:
            out += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out += ch
        elif ch == "#":
            break
        else:
            out += ch
    return out.rstrip()


_KEY_RE = re.compile(r"^([A-Za-z_][\w.-]*)\s*:\s*(.*)$")


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def loads(text: str):
    """解析 YAML 子集文本 → Python 对象（顶层必须是映射）。"""
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        if line.strip() in ("---", "..."):
            continue
        if "\t" in line:
            raise YamlSyntaxError(f"不允许使用 Tab 缩进: {raw!r}")
        lines.append((_indent_of(line), line))
    if not lines:
        return {}
    if lines[0][0] != 0:
        raise YamlSyntaxError("顶层缩进必须为 0")
    value, idx = _parse_block(lines, 0, lines[0][0])
    if idx != len(lines):
        raise YamlSyntaxError(f"第 {idx + 1} 行附近存在无法归位的行: {lines[idx][1]!r}")
    return value


def _parse_block(lines, idx, indent):
    """解析从 idx 开始、缩进为 indent 的块。返回 (value, next_idx)。"""
    if lines[idx][1].lstrip().startswith("- "):
        return _parse_list(lines, idx, indent)
    return _parse_map(lines, idx, indent)


def _parse_map(lines, idx, indent):
    result = {}
    while idx < len(lines):
        cur_indent, line = lines[idx]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise YamlSyntaxError(f"意外的缩进层级: {line!r}")
        m = _KEY_RE.match(line.strip())
        if not m:
            raise YamlSyntaxError(f"期望 'key: value' 形式: {line!r}")
        key, rest = m.group(1), m.group(2)
        if rest:
            result[key] = _parse_scalar(rest)
            idx += 1
        else:
            # 子块：下一行缩进更大
            if idx + 1 < len(lines) and lines[idx + 1][0] > indent:
                value, idx = _parse_block(lines, idx + 1, lines[idx + 1][0])
                result[key] = value
            elif idx + 1 < len(lines) and lines[idx + 1][0] == indent \
                    and lines[idx + 1][1].lstrip().startswith("- "):
                # 空值后跟同缩进列表（宽松：把列表当作该 key 的值）
                value, idx = _parse_list(lines, idx + 1, indent)
                result[key] = value
            else:
                result[key] = None
                idx += 1
    return result, idx


def _parse_list(lines, idx, indent):
    result = []
    while idx < len(lines):
        cur_indent, line = lines[idx]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise YamlSyntaxError(f"列表项内缩进不一致: {line!r}")
        stripped = line.lstrip()
        if not stripped.startswith("- "):
            break
        item_rest = stripped[2:].strip()
        if not item_rest:
            # 纯占位
            result.append(None)
            idx += 1
            continue
        m = _KEY_RE.match(item_rest)
        if m:
            # 列表项是映射: "- key: value"，可能带续行
            item_indent = cur_indent + 2
            item_map = {}
            key, rest = m.group(1), m.group(2)
            if rest:
                item_map[key] = _parse_scalar(rest)
                idx += 1
            else:
                if idx + 1 < len(lines) and lines[idx + 1][0] > item_indent:
                    value, idx = _parse_block(lines, idx + 1, lines[idx + 1][0])
                    item_map[key] = value
                else:
                    item_map[key] = None
                    idx += 1
            # 续行（同 item_indent 的 key: value）
            while idx < len(lines) and lines[idx][0] == item_indent:
                m2 = _KEY_RE.match(lines[idx][1].strip())
                if not m2:
                    break
                k2, r2 = m2.group(1), m2.group(2)
                if r2:
                    item_map[k2] = _parse_scalar(r2)
                    idx += 1
                else:
                    if idx + 1 < len(lines) and lines[idx + 1][0] > item_indent:
                        value, idx = _parse_block(lines, idx + 1, lines[idx + 1][0])
                        item_map[k2] = value
                    else:
                        item_map[k2] = None
                        idx += 1
            result.append(item_map)
        else:
            result.append(_parse_scalar(item_rest))
            idx += 1
    return result, idx


def load_file(path) -> dict:
    from pathlib import Path
    return loads(Path(path).read_text(encoding="utf-8"))
