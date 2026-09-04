"""core/env/loader.py —— 参数配置层加载器（单一真源 + 三层合并 + 官方锁定）。

分层语义：
    OFFICIAL  官方硬约束（来自组委会规范条文），config.yaml 的 overrides **不可覆盖**
    DERIVED   派生值（由 OFFICIAL 推算），可微调但会被一致性验算检查
    TUNABLE   经验软目标（无官方规定），用户可自由调整

合并优先级（后者覆盖前者）：
    schema.yaml 的 value  <  profiles/<竞赛>.yaml  <  config.yaml 的 overrides

设计原则：
    1. 零外部依赖：仅用标准库，自带极简 YAML 解析器（支持多级缩进、行内列表）。
    2. 单一真源：所有参数的默认值、类型、范围、依据只写在 schema.yaml，
       本文件不再内置任何业务阈值（已彻底删除 DEFAULT_CONFIG）。
    3. 官方锁定：overrides 覆盖 OFFICIAL 层参数会被拒绝并打印 ERROR，绝不静默接受。
    4. 缺失即报错：require(key) 对缺失参数抛异常，避免 `_env_get(k, 25)` 这类
       硬编码兜底在配置读取失败时悄悄回退到错误数值。
    5. 一致性验算：合并后自动检查参数之间是否自相矛盾。

接口：
    load_config() -> dict                 展开后的纯值配置（向后兼容）
    get(key, default=None) -> Any         点号路径读取，如 get("paper.max_pages")
    require(key) -> Any                   缺失即抛 EnvConfigError
    layer_of(key) -> str                  返回 OFFICIAL / DERIVED / TUNABLE
    doctor_report() -> dict               参数生效值 + 来源 + 一致性问题（供 env_doctor.py）
    available_profiles() -> list          可用竞赛 profile 名
"""

import os
import sys
import copy

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCHEMA_PATH = os.path.join(_HERE, "schema.yaml")
_CONFIG_PATH = os.path.join(_HERE, "config.yaml")
_PROFILES_DIR = os.path.join(_HERE, "profiles")

LAYER_OFFICIAL = "OFFICIAL"
LAYER_DERIVED = "DERIVED"
LAYER_TUNABLE = "TUNABLE"
_VALID_LAYERS = (LAYER_OFFICIAL, LAYER_DERIVED, LAYER_TUNABLE)


class EnvConfigError(Exception):
    """参数缺失或非法时抛出。"""


# ---------------------------------------------------------------------------
# 极简 YAML 解析
# ---------------------------------------------------------------------------

def _parse_scalar(s):
    """解析 YAML 标量为 Python 类型：int / float / bool / None / list / str。"""
    s = s.strip()
    if s == "":
        return ""
    if (s.startswith('"') and s.endswith('"') and len(s) >= 2) or \
       (s.startswith("'") and s.endswith("'") and len(s) >= 2):
        return s[1:-1]
    # 行内列表 [a, b, c]
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(x) for x in inner.split(",")]
    # 行内空映射 {}
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


def _strip_inline_comment(line):
    """剥离行内 `#` 注释，保留引号内的 #。"""
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            if i == 0 or line[i - 1] in (" ", "\t"):
                return line[:i]
    return line


def _tokenize(text):
    """把文本切成 (indent, content) 列表，丢弃空行与纯注释行。"""
    tokens = []
    for raw in text.splitlines():
        line = _strip_inline_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" \t"))
        tokens.append((indent, line.strip()))
    return tokens


def _build(tokens, pos, indent):
    """在给定缩进层级上构建 dict，返回 (dict, 下一个 token 位置)。"""
    result = {}
    while pos < len(tokens):
        cur_indent, content = tokens[pos]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            pos += 1
            continue
        if content.startswith("- "):
            # 列表项：仅当本层尚未收集任何 key 时才作为 list 返回
            if not result:
                items = []
                while pos < len(tokens) and tokens[pos][0] == cur_indent \
                        and tokens[pos][1].startswith("- "):
                    items.append(_parse_scalar(tokens[pos][1][2:]))
                    pos += 1
                return items, pos
            pos += 1
            continue
        if ":" not in content:
            pos += 1
            continue
        key, _, val = content.partition(":")
        key = key.strip()
        val = val.strip()
        nxt = pos + 1
        if nxt < len(tokens) and tokens[nxt][0] > cur_indent:
            sub, pos = _build(tokens, nxt, tokens[nxt][0])
            if isinstance(sub, dict):
                result[key] = sub
            else:
                result[key] = sub
        elif val == "":
            result[key] = {}
            pos = nxt
        else:
            result[key] = _parse_scalar(val)
            pos = nxt
    return result, pos


def _parse_yaml(text):
    """解析（多级缩进的）YAML 文本为嵌套 dict。"""
    tokens = _tokenize(text)
    if not tokens:
        return {}
    result, _ = _build(tokens, 0, tokens[0][0])
    return result if isinstance(result, dict) else {}


def _read_yaml(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return _parse_yaml(f.read())
    except OSError as e:
        raise EnvConfigError("无法读取 %s：%s" % (path, e))


# ---------------------------------------------------------------------------
# schema 展开
# ---------------------------------------------------------------------------

def _is_param_node(v):
    """判断 schema 节点是否是参数定义（含 value 且有 layer/type 之一）。"""
    return isinstance(v, dict) and "value" in v and ("layer" in v or "type" in v)


def _flatten_values(node):
    """把 schema 的 {key: {value, layer, ...}} 展开为纯值 {key: value}。"""
    out = {}
    for k, v in node.items():
        if _is_param_node(v):
            out[k] = copy.deepcopy(v["value"])
        elif isinstance(v, dict):
            out[k] = _flatten_values(v)
        else:
            out[k] = v
    return out


def _index_meta(node, prefix="", layers=None, sources=None, types=None):
    """收集 {路径: layer} / {路径: source} / {路径: type}。"""
    layers = {} if layers is None else layers
    sources = {} if sources is None else sources
    types = {} if types is None else types
    for k, v in node.items():
        path = "%s.%s" % (prefix, k) if prefix else k
        if _is_param_node(v):
            layer = str(v.get("layer", LAYER_TUNABLE)).upper()
            if layer not in _VALID_LAYERS:
                layer = LAYER_TUNABLE
            layers[path] = layer
            sources[path] = v.get("source", "")
            types[path] = v.get("type", "")
        elif isinstance(v, dict):
            _index_meta(v, path, layers, sources, types)
    return layers, sources, types


# ---------------------------------------------------------------------------
# 合并
# ---------------------------------------------------------------------------

def _merge_into(base, override, layers, prefix="", strict_official=True,
                track=None, source="override", rejected=None):
    """用 override 递归覆盖 base（均为纯值 dict）。

    track    记录成功应用的覆盖 [(path, value, source)]
    rejected 记录因 OFFICIAL 锁定而被拒绝的覆盖 [(path, 想改的值, 保留的值)]
    """
    if track is None:
        track = []
    if rejected is None:
        rejected = []
    for k, v in override.items():
        path = "%s.%s" % (prefix, k) if prefix else k
        if k not in base:
            base[k] = copy.deepcopy(v)
            track.append((path, v, source))
            continue
        if isinstance(v, dict) and isinstance(base[k], dict):
            _merge_into(base[k], v, layers, path, strict_official, track, source, rejected)
        else:
            if strict_official and layers.get(path) == LAYER_OFFICIAL:
                sys.stderr.write(
                    "[env/loader] ERROR：参数 %s 属于 OFFICIAL 层（官方硬约束），"
                    "不允许在 config.yaml 的 overrides 中覆盖。已忽略该覆盖，"
                    "保留值 %r。若确需修改，请改 schema.yaml 并在注释中写明当届官方依据。\n"
                    % (path, base[k])
                )
                rejected.append((path, v, base[k]))
            else:
                base[k] = copy.deepcopy(v)
                track.append((path, v, source))
    return track, rejected


def _check_consistency(cfg):
    """合并后检查参数是否自相矛盾，返回问题描述列表。"""
    issues = []
    p = cfg.get("paper", {}) or {}

    def num(*keys):
        vals = [p.get(k) for k in keys]
        return vals if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals) else None

    got = num("max_pages", "min_pages")
    if got:
        mx, mn = got
        if mn > mx:
            issues.append("paper.min_pages(%s) > paper.max_pages(%s)：此组合永远无法达标" % (mn, mx))

    got = num("max_pages", "page_fill_ratio", "min_pages")
    if got:
        mx, fill, mn = got
        floor = mx * fill
        if mn > floor:
            issues.append(
                "paper.min_pages(%s) > max_pages x page_fill_ratio(%.1f)：页数下限高于填充率闸门，无法达标"
                % (mn, floor))

    got = num("min_words", "max_words")
    if got:
        mnw, mxw = got
        if mnw > mxw:
            issues.append("paper.min_words(%s) > paper.max_words(%s)" % (mnw, mxw))

    got = num("max_words", "chars_per_page", "max_pages")
    if got:
        mxw, cpp, mxp = got
        need_pages = mxw / cpp if cpp else 0
        if need_pages > mxp:
            issues.append(
                "paper.max_words(%s) 需要约 %.1f 页，超过 paper.max_pages(%s)：字数上限会撑爆页数"
                % (mxw, need_pages, mxp))

    got = num("abstract_min_words", "abstract_max_words")
    if got:
        a, b = got
        if a > b:
            issues.append("paper.abstract_min_words(%s) > abstract_max_words(%s)" % (a, b))

    got = num("pdf_min_bytes", "pdf_max_bytes")
    if got:
        a, b = got
        if a > b:
            issues.append("paper.pdf_min_bytes(%s) > pdf_max_bytes(%s)" % (a, b))

    return issues


# ---------------------------------------------------------------------------
# 对外接口
# ---------------------------------------------------------------------------

_CONFIG_CACHE = None
_META_CACHE = None


def available_profiles():
    """列出 core/env/profiles/ 下可用的竞赛 profile 名（不含扩展名）。"""
    if not os.path.isdir(_PROFILES_DIR):
        return []
    return sorted(
        f[:-5] for f in os.listdir(_PROFILES_DIR)
        if f.endswith(".yaml") and not f.startswith("_")
    )


def _load_all():
    global _CONFIG_CACHE, _META_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE, _META_CACHE

    if not os.path.isfile(_SCHEMA_PATH):
        raise EnvConfigError(
            "参数真源 schema.yaml 不存在：%s。所有阈值都定义在这里，缺失即无法运行。" % _SCHEMA_PATH)

    schema = _read_yaml(_SCHEMA_PATH)
    layers, sources, types = _index_meta(schema)
    values = _flatten_values(schema)

    # 用户配置
    user_cfg = _read_yaml(_CONFIG_PATH) if os.path.isfile(_CONFIG_PATH) else {}
    profile_name = user_cfg.get("profile") or "cumcm-2025"

    applied = []       # [(path, value, source)]  成功应用的覆盖
    rejected = []      # [(path, 想改的值, 保留的值)]  被 OFFICIAL 锁定拒绝的覆盖
    profile_meta = {}

    # 1) 竞赛 profile 差量（profile 代表的是该赛事的官方规则本身，允许声明 OFFICIAL 值）
    prof_path = os.path.join(_PROFILES_DIR, profile_name + ".yaml")
    if os.path.isfile(prof_path):
        prof = _read_yaml(prof_path)
        prof.pop("inherits", None)
        profile_meta = prof.pop("meta", {}) or {}
        _merge_into(values, prof, layers, strict_official=False, track=applied,
                    source="profile:" + profile_name, rejected=rejected)
    else:
        sys.stderr.write(
            "[env/loader] 警告：profile 文件不存在 %s，仅使用 schema.yaml 默认值。\n" % prof_path)

    # 2) 用户 overrides（严格：OFFICIAL 层拒绝覆盖）
    ov = user_cfg.get("overrides") or {}
    if isinstance(ov, dict) and ov:
        _merge_into(values, ov, layers, strict_official=True, track=applied,
                    source="config.yaml overrides", rejected=rejected)

    # 3) 一致性验算
    issues = _check_consistency(values)
    for msg in issues:
        sys.stderr.write("[env/loader] 参数矛盾：%s\n" % msg)

    _CONFIG_CACHE = values
    _META_CACHE = {
        "profile": profile_name,
        "profile_meta": profile_meta,
        "layers": layers,
        "sources": sources,
        "types": types,
        "applied": applied,
        "rejected": rejected,
        "issues": issues,
        "schema_path": _SCHEMA_PATH,
        "config_path": _CONFIG_PATH,
    }
    return _CONFIG_CACHE, _META_CACHE


def load_config():
    """返回展开后的完整配置 dict（纯值，向后兼容旧接口）。"""
    cfg, _ = _load_all()
    return copy.deepcopy(cfg)


def get(key, default=None):
    """按点号路径读取配置，如 get("paper.max_pages")。"""
    if not key or not isinstance(key, str):
        return default
    try:
        cfg, _ = _load_all()
    except EnvConfigError as e:
        sys.stderr.write("[env/loader] %s\n" % e)
        return default
    cur = cfg
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def require(key):
    """读取必需参数；缺失或配置层不可用时抛 EnvConfigError。

    用于替代 `_env_get(key, 25)` 这类硬编码兜底——配置读不到就明确失败，
    绝不悄悄回退到一个可能早已过时的数字。
    """
    sentinel = object()
    v = get(key, sentinel)
    if v is sentinel:
        raise EnvConfigError(
            "必需参数缺失：%s（请在 core/env/schema.yaml 中定义，或检查 profile 是否覆盖）" % key)
    return v


def layer_of(key):
    """返回参数的层级：OFFICIAL / DERIVED / TUNABLE；未知返回空字符串。"""
    try:
        _, meta = _load_all()
    except EnvConfigError:
        return ""
    return meta["layers"].get(key, "")


def profile_name():
    """返回当前生效的竞赛 profile 名。"""
    try:
        _, meta = _load_all()
    except EnvConfigError:
        return ""
    return meta.get("profile", "")


def doctor_report():
    """返回参数体检报告 dict，供 core/tools/env_doctor.py 渲染。"""
    cfg, meta = _load_all()
    rows = []

    def walk(node, prefix=""):
        for k, v in sorted(node.items()):
            path = "%s.%s" % (prefix, k) if prefix else k
            if isinstance(v, dict):
                walk(v, path)
            else:
                src = "schema"
                for ap in reversed(meta["applied"]):
                    if ap[0] == path:
                        src = ap[2]
                        break
                rows.append({
                    "path": path,
                    "value": v,
                    "layer": meta["layers"].get(path, "-"),
                    "source": src,
                    "note": meta["sources"].get(path, ""),
                })
    walk(cfg)
    return {
        "profile": meta["profile"],
        "profile_meta": meta["profile_meta"],
        "rows": rows,
        "issues": meta["issues"],
        "rejected": meta["rejected"],
        "available_profiles": available_profiles(),
    }


def _reload():
    """清除缓存重新加载（调试/测试用）。"""
    global _CONFIG_CACHE, _META_CACHE
    _CONFIG_CACHE = None
    _META_CACHE = None
    return load_config()


if __name__ == "__main__":
    print("=" * 66)
    print("core/env/loader.py 调试输出")
    print("schema :", _SCHEMA_PATH, os.path.isfile(_SCHEMA_PATH))
    print("config :", _CONFIG_PATH, os.path.isfile(_CONFIG_PATH))
    print("可用 profile:", ", ".join(available_profiles()))
    print("=" * 66)

    rep = doctor_report()
    print("\n当前 profile: %s" % rep["profile"])
    pm = rep["profile_meta"]
    if pm:
        print("  赛事: %s  verified=%s  来源: %s" % (
            pm.get("name", "?"), pm.get("verified", "?"), pm.get("rules_source", "?")))

    print("\n[关键参数]")
    for r in rep["rows"]:
        if r["path"].startswith(("paper.", "official.")):
            print("  %-38s = %-18s [%s]" % (r["path"], r["value"], r["layer"]))

    if rep["issues"]:
        print("\n[参数矛盾]")
        for i in rep["issues"]:
            print("  !", i)
    else:
        print("\n[参数矛盾] 无")

    if rep["rejected"]:
        print("\n[被拒绝的覆盖]")
        for path, want, keep in rep["rejected"]:
            print("  x %s -> 想改成 %r，已拒绝（OFFICIAL 层锁定）" % (path, want))

    print("\n[get() 兼容性抽样]")
    for k in ("paper.max_pages", "paper.min_pages", "paper.min_words",
              "paper.min_figures", "code.random_seed", "runtime.language",
              "official.ai_support_pdf_name", "not.exist.key"):
        print("  get(%r) = %r" % (k, get(k)))
