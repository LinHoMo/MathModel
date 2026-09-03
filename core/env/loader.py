"""core/env/loader.py —— 环境变量配置层加载器（UTG 多 Agent 架构第一步）。

用途：
    在不修改 skill 逻辑的前提下，从 core/env/config.yaml 读取用户可调的交付规格与运行阈值，
    供 Modeler / Programmer / Writer 各 agent 通过 get(key) 接口统一读取。

设计原则：
    1. 零外部依赖：仅用 Python 标准库，不依赖 PyYAML。
    2. 内置极简 YAML 解析器：仅支持 `key: value`、缩进层级、`#` 注释（满足 config.yaml 结构）。
    3. 缺失回退：config.yaml 不存在或解析失败时，返回内置 DEFAULT_CONFIG 并打印警告到 stderr，不抛异常、不阻塞流程。
    4. 结果缓存：load_config() 首次加载后缓存，避免重复读文件。

接口：
    load_config() -> dict       返回完整 config dict（含五组参数）
    get(key, default=None) -> Any   支持点号路径，如 get("paper.min_pages")
"""

import os
import sys
import copy

# ---------------------------------------------------------------------------
# 内置默认配置：与 core/env/config.yaml 默认值保持一致
# 缺失或解析失败时回退到此配置，保证流程不阻塞
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "paper": {
        "min_pages": 25,           # 最低页数（国赛 25-30 页，est_pages ≥ max_pages×0.8=24）。对标 mmagent-codex-main
        "min_words": 18000,        # 最低字数（国赛 18000-25000 字）。对标 mmagent-codex-main
        "min_figures": 6,          # 最低图数（3-4 子问题×每问≥1-2 图+灵敏度≥1 图）。对标 mmagent-codex-main
        "min_tables": 4,           # 最低表数（符号说明表+每问结果表+对比表）。对标 mmagent-codex-main
        "min_equations": 15,       # 最低公式数（华为杯每子问题 8-15 式逐式编号）。对标 mmagent-codex-main
        "min_references": 10,      # 最低参考文献数（国赛参考文献 ≥10）。对标 mmagent-codex-main
        "max_pages": 30,           # 最高页数上限（_COMP_RULES.cumcm MAX_PAGES=30）。对标 mmagent-codex-main
        "abstract_min_words": 400, # 中文摘要最少字数（writing_rules.md：400-600 字）。对标 mmagent-codex-main
        "abstract_max_words": 600, # 中文摘要最多字数（writing_rules.md：400-600 字）。对标 mmagent-codex-main
        "chars_per_page": 800,     # 每页中文字数基准（workflow_engine.py）。对标 mmagent-codex-main
        "page_fill_ratio": 0.8,    # 正文填充比例下限（est_pages < max_pages×80% 即 FAIL）。对标 mmagent-codex-main
        "pdf_min_bytes": 102400,   # PDF 最小字节数（100KB gate，auto-review-loop）。对标 mmagent-codex-main
        "recent_ref_ratio": 0.6,   # 近 3 年文献占比下限（quality-check：≥60%）。对标 mmagent-codex-main
        "figure_min_width": 0.85,  # 图最小宽度（单位 \textwidth，下限 0.8）。对标 mmagent-codex-main
        "table_max_rows_inline": 12,  # 正文表格最大行数（>12 行禁放正文）。对标 mmagent-codex-main
        "table_longtable_threshold": 15,  # 结果表转 longtable 的行数阈值（>15 行放附录）。对标 mmagent-codex-main
    },
    "code": {
        "random_seed": 42,         # 随机种子（保证可复现，comp-code 第432行）。对标 mmagent-codex-main
        "multi_run_count": 5,      # 启发式算法多次运行次数（≥5 次）。对标 mmagent-codex-main
        "cv_threshold": 0.10,      # 交叉验证/稳定性阈值（10%，P6 显式化入配置层）。对标 mmagent-codex-main
        "solver_timeout_small": 300,    # 求解器超时（<100 变量，秒）。对标 mmagent-codex-main
        "solver_timeout_medium": 600,   # 求解器超时（100-1000 变量，秒）。对标 mmagent-codex-main
        "solver_timeout_large": 1200,   # 求解器超时（>1000 变量，秒）。对标 mmagent-codex-main
        "max_fix_rounds": 3,       # 单子问题自检修复轮数上限（3 轮不过回退 Modeler）。对标 mmagent-codex-main
        "sensitivity_range": 0.20, # 灵敏度扰动范围（±20% 内扫描）。对标 mmagent-codex-main
        "sensitivity_steps": 10,   # 灵敏度扫描步数（10 步）。对标 mmagent-codex-main
        "min_main_py_bytes": 500,  # main.py 最少字节（comp-code 完成铁律）。对标 mmagent-codex-main
        "min_deliverables_bytes": 1024,  # CODE_DELIVERABLES 最少字节（≥1KB）。对标 mmagent-codex-main
        "target_platform": "python",  # 主线代码平台：python/matlab/beitian（北太天元），默认 python 不产出分支
    },
    "modeling": {
        "min_candidate_models": 2,          # 候选模型最少数量（铁律 M1 ≥2）。对标 mmagent-codex-main
        "assumption_score_threshold": 6.0,  # 假设综合评分通过阈值（保留四维评分）。对标 mmagent-codex-main
        "ambiguity_min_interpretations": 2, # 歧义至少两种解释 + 验算裁决。对标 mmagent-codex-main
        "multi_start_check": True,          # 非凸/启发式必做多起点或多种子稳定性检查。对标 mmagent-codex-main
    },
    "review": {
        "max_rounds": 4,             # 评审最大轮数（auto-review-loop MAX_ROUNDS=4）。对标 mmagent-codex-main
        "improvement_max_rounds": 2, # 论文改进最大轮数（auto-paper-improvement-loop MAX_ROUNDS=2）。对标 mmagent-codex-main
        "pass_score": 6,             # 评审通过分（满分 10）。对标 mmagent-codex-main
        "figure_as_subject_max": 3,  # 图表做主语句式最大次数（≥3 次记 MAJOR）。对标 mmagent-codex-main
    },
    "runtime": {
        "language": "zh",          # 语言 zh/en
        "template": "cumcm-zh",    # 论文模板 cumcm-zh/mcm-en/generic
        "strict_mode": True,       # 严格模式（阈值不达则退回修正）
        "traceability_min_ratio": 0.90,  # 数值可追溯比例下限（≥90%）。对标 mmagent-codex-main
        "numeric_tolerance_rel": 0.005,  # 数值相对容差上限（rel ≤0.5%）。对标 mmagent-codex-main
        "numeric_tolerance_abs": 0.01,   # 数值绝对容差上限（abs ≤0.01）。对标 mmagent-codex-main
        "compile_pdf": "auto",
        "profile": "standard",     # 能力分层：standard=完整流程+全门禁 / lite=弱模型，放宽软性门禁
        "latex_engine": "xelatex", # LaTeX 引擎（编译链 xelatex→bibtex→xelatex→xelatex）
        "deliver_docx": "never",   # DOCX 交付策略：never/auto/always，默认 never 不产出 Word
    },
    "checkpoint": {
        "enabled": False,
        "path": "output/checkpoint.json",
        "save_interval": 1,
    },
}

# 加载结果缓存（避免重复读文件）
_CONFIG_CACHE = None

# config.yaml 路径：与本文件同目录
_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")


def _parse_scalar(value_str):
    """把 YAML 标量字符串解析为 Python 类型（int/float/bool/None/str）。

    极简实现：仅识别整数、浮点数、布尔、null，其余按字符串处理（去掉首尾引号）。
    """
    s = value_str.strip()
    if s == "":
        return ""
    # 去除行内注释（# 前需有空格，避免误伤 URL 或颜色值）
    # 注意：value 部分的 # 注释已在调用前剥离，这里不再处理
    # 去引号
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    low = s.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "none", "~"):
        return None
    # 整数
    try:
        return int(s)
    except ValueError:
        pass
    # 浮点数
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _strip_inline_comment(line):
    """剥离行内 `#` 注释，但保留字符串中的 #。

    极简策略：找到第一个前导空格的 `#` 作为注释起点；
    若 `#` 出现在引号内则不处理（本配置文件无此场景，简化实现）。
    """
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            # # 前需为空白或行首，才算注释
            if i == 0 or line[i - 1] in (" ", "\t"):
                return line[:i]
    return line


def _parse_yaml(text):
    """极简 YAML 解析器：仅支持 `key: value` 与缩进层级（两级：顶层 key + 二级 key）。

    本项目 config.yaml 结构固定为：顶层 5 组 -> 每组若干 `key: value`，
    因此这里实现两级缩进解析即可满足需求，不追求通用性。

    解析失败时抛 ValueError，由上层捕获并回退默认值。
    """
    result = {}
    current_section = None

    for raw_line in text.splitlines():
        # 去行内注释
        line_no_comment = _strip_inline_comment(raw_line)
        # 去首尾空白后判断空行
        stripped = line_no_comment.strip()
        if stripped == "":
            continue

        # 计算缩进（前导空格数，tab 按 1 计，本项目用空格缩进）
        indent = len(line_no_comment) - len(line_no_comment.lstrip(" "))

        if indent == 0:
            # 顶层 key，形如 `paper:`（此层只做分组，不取值）
            if not stripped.endswith(":"):
                raise ValueError("顶层行应为 'section:' 形式，实际: %r" % raw_line)
            section_name = stripped[:-1].strip()
            if section_name == "":
                raise ValueError("空顶层段名: %r" % raw_line)
            current_section = section_name
            result[current_section] = {}
        else:
            # 二级 key: value
            if current_section is None:
                raise ValueError("缩进行出现在任何顶层段之前: %r" % raw_line)
            if ":" not in stripped:
                raise ValueError("二级行缺少 ':' 分隔: %r" % raw_line)
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if key == "":
                raise ValueError("空二级键名: %r" % raw_line)
            result[current_section][key] = _parse_scalar(value)

    return result


def _deep_merge(base, override):
    """用 override 递归合并到 base 上（base 已是默认值的拷贝）。

    仅对 dict 递归合并；非 dict 类型直接用 override 覆盖。
    这样即使 config.yaml 只写了部分字段，缺失字段仍保留默认值。
    """
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config():
    """加载完整 config dict。

    流程：
        1. 若已缓存则直接返回缓存（深拷贝，防止调用方误改）。
        2. 读取 core/env/config.yaml；不存在则回退 DEFAULT_CONFIG 并打印警告。
        3. 用极简解析器解析；解析失败则回退 DEFAULT_CONFIG 并打印警告。
        4. 用解析结果递归合并到 DEFAULT_CONFIG 拷贝上（缺失字段补默认值）。
        5. 缓存并返回（深拷贝）。
    """
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return copy.deepcopy(_CONFIG_CACHE)

    # 配置文件不存在：回退默认值
    if not os.path.isfile(_CONFIG_PATH):
        sys.stderr.write(
            "[env/loader] 警告：config.yaml 不存在(%s)，回退到 DEFAULT_CONFIG。\n" % _CONFIG_PATH
        )
        _CONFIG_CACHE = copy.deepcopy(DEFAULT_CONFIG)
        return copy.deepcopy(_CONFIG_CACHE)

    # 读取文件
    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        sys.stderr.write(
            "[env/loader] 警告：读取 config.yaml 失败(%s)，回退到 DEFAULT_CONFIG。错误：%s\n"
            % (_CONFIG_PATH, e)
        )
        _CONFIG_CACHE = copy.deepcopy(DEFAULT_CONFIG)
        return copy.deepcopy(_CONFIG_CACHE)

    # 解析 YAML
    try:
        parsed = _parse_yaml(text)
    except ValueError as e:
        sys.stderr.write(
            "[env/loader] 警告：config.yaml 解析失败，回退到 DEFAULT_CONFIG。错误：%s\n" % e
        )
        _CONFIG_CACHE = copy.deepcopy(DEFAULT_CONFIG)
        return copy.deepcopy(_CONFIG_CACHE)

    # 递归合并：parsed 覆盖到 DEFAULT_CONFIG 拷贝上，缺失字段补默认值
    merged = copy.deepcopy(DEFAULT_CONFIG)
    _deep_merge(merged, parsed)
    _CONFIG_CACHE = merged
    return copy.deepcopy(_CONFIG_CACHE)


def get(key, default=None):
    """按点号路径读取配置项。

    示例：
        get("paper.min_pages")         -> 10
        get("code.random_seed")        -> 42
        get("runtime.language")        -> "zh"
        get("not.exist", default="x")  -> "x"

    Args:
        key: 点号分隔的路径，如 "paper.min_pages"。
        default: 路径任意一段不存在时返回的默认值。

    Returns:
        命中则返回对应值；否则返回 default。
    """
    if not key or not isinstance(key, str):
        return default

    cfg = load_config()
    cur = cfg
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def _reload():
    """清除缓存并重新加载（仅供调试/测试使用，对外不暴露语义）。"""
    global _CONFIG_CACHE
    _CONFIG_CACHE = None
    return load_config()


if __name__ == "__main__":
    # 调试入口：打印加载结果，便于 `py core\env\loader.py` 验证
    print("=" * 60)
    print("core/env/loader.py 调试输出")
    print("config.yaml 路径:", _CONFIG_PATH)
    print("config.yaml 存在:", os.path.isfile(_CONFIG_PATH))
    print("=" * 60)

    cfg = load_config()
    print("\n[load_config()] 完整配置：")
    for section, items in cfg.items():
        print("  %s:" % section)
        for k, v in items.items():
            print("    %s: %r" % (k, v))

    print("\n[get(key)] 点号路径示例：")
    for k in (
        "paper.min_pages",
        "paper.min_words",
        "paper.min_figures",
        "paper.min_tables",
        "paper.min_equations",
        "paper.min_references",
        "code.random_seed",
        "code.multi_run_count",
        "modeling.min_candidate_models",
        "modeling.assumption_score_threshold",
        "runtime.language",
        "runtime.template",
        "runtime.strict_mode",
        "not.exist.key",
    ):
        print("  get(%r) = %r" % (k, get(k)))

    print("\n[get(key, default)] 带默认值示例：")
    print("  get('not.exist', default='fallback') =", get("not.exist", default="fallback"))

    print("\n加载完成，无报错。")
