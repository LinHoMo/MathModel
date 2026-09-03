# env —— 环境变量配置层

`core/env/` 是 MathModelSkills 项目根目录下的**用户可调环境变量配置层**，让用户在不修改 skill 逻辑的前提下调整交付规格与运行阈值。它是 UTG 多 Agent 架构演进的第一步落地：各 agent 不再硬编码阈值，而是统一通过 `core/env/loader.py` 读取本目录的 `config.yaml`。

## 目录内容

| 文件 | 作用 |
| --- | --- |
| `config.yaml` | 五组可调参数（含默认值与中文注释），用户直接编辑此文件即可调整规格 |
| `loader.py` | 零外部依赖的加载器，提供 `load_config()` / `get(key)` 接口，缺失时回退默认值 |
| `README.md` | 本说明文档 |

## 五组参数

> 下列默认值均对标参考系统 `mmagent-codex-main`。

### 1. paper（论文规格）

| 参数名 | 含义 | 默认值 | 影响范围（读取方 agent） | 对标说明 |
| --- | --- | --- | --- | --- |
| `min_pages` | 最低页数 | `25` | Writer：`final-validator`、`section-writer` | 国赛 25-30 页，est_pages ≥ max_pages×0.8=24 |
| `min_words` | 最低字数 | `18000` | Writer：`section-writer`、`final-validator` | 国赛 18000-25000 字 |
| `min_figures` | 最低图数 | `6` | Writer：`figure-generator`、`final-validator` | 3-4 子问题×每问≥1-2 图+灵敏度≥1 图 |
| `min_tables` | 最低表数 | `4` | Writer：`section-writer`、`final-validator` | 符号说明表+每问结果表+对比表 |
| `min_equations` | 最低公式数 | `15` | Writer：`section-writer`、`final-validator` | 华为杯每子问题 8-15 式逐式编号 |
| `min_references` | 最低参考文献数 | `10` | Writer：`reference-curator`、`final-validator` | 国赛参考文献 ≥10 |
| `max_pages` | 最高页数上限 | `30` | Writer：`final-validator`、`section-writer` | _COMP_RULES.cumcm MAX_PAGES=30 |
| `abstract_min_words` | 中文摘要最少字数 | `400` | Writer：`section-writer` | writing_rules.md：400-600 字 |
| `abstract_max_words` | 中文摘要最多字数 | `600` | Writer：`section-writer` | writing_rules.md：400-600 字 |
| `chars_per_page` | 每页中文字数基准 | `800` | Writer：`structure-planner` | workflow_engine.py `_check_paper_body_pages` |
| `page_fill_ratio` | 正文填充比例下限 | `0.8` | Writer：`structure-planner` | est_pages < max_pages×80% 即 FAIL |
| `pdf_min_bytes` | PDF 最小字节数 | `102400` | Writer：`final-validator` | auto-review-loop PDF>100KB gate |
| `recent_ref_ratio` | 近 3 年文献占比下限 | `0.6` | Writer：`reference-curator` | quality-check：近 3 年文献 ≥60% |
| `figure_min_width` | 图最小宽度（按 `\textwidth`） | `0.85` | Writer：`figure-generator` | comp-paper-zh 第629-630行 |
| `table_max_rows_inline` | 正文表格最大行数 | `12` | Writer：`section-writer` | 正文禁 >12 行表格（comp-paper-zh 第590行） |
| `table_longtable_threshold` | 结果表转 longtable 行数阈值 | `15` | Writer：`section-writer` | >15 行结果表截断转 longtable 放附录 |

### 2. code（代码规格）

| 参数名 | 含义 | 默认值 | 影响范围（读取方 agent） | 对标说明 |
| --- | --- | --- | --- | --- |
| `random_seed` | 随机种子（保证可复现） | `42` | Programmer：`code-implementer`、`test-runner`、`result-verifier` | comp-code 第432行，一致 |
| `multi_run_count` | 启发式算法多次运行次数 | `5` | Programmer：`code-implementer`、`result-verifier` | norms 第272行 ≥5 次，一致 |
| `cv_threshold` | 交叉验证/稳定性阈值 | `0.10` | Programmer：`result-verifier` | 原 P6 硬编码显式化入配置层 |
| `solver_timeout_small` | 求解器超时（<100 变量，秒） | `300` | Programmer：`code-implementer`、`result-verifier` | comp-code 第409-413行 |
| `solver_timeout_medium` | 求解器超时（100-1000 变量，秒） | `600` | Programmer：`code-implementer`、`result-verifier` | comp-code 第409-413行 |
| `solver_timeout_large` | 求解器超时（>1000 变量，秒） | `1200` | Programmer：`code-implementer`、`result-verifier` | comp-code 第409-413行 |
| `max_fix_rounds` | 单子问题自检修复轮数上限 | `3` | Programmer：`test-runner` | 3 轮不过回退 Modeler（comp-code 第288行） |
| `sensitivity_range` | 灵敏度扰动范围 | `0.20` | Programmer：`result-verifier` | ±20% 内扫描（comp-code 第314行） |
| `sensitivity_steps` | 灵敏度扫描步数 | `10` | Programmer：`result-verifier` | 10 步，兼容 ±10% 采样点 |
| `min_main_py_bytes` | `main.py` 最少字节 | `500` | Programmer：`code-implementer` | comp-code 完成铁律 |
| `min_deliverables_bytes` | `CODE_DELIVERABLES` 最少字节 | `1024` | Programmer：`hash-auditor` | CODE_DELIVERABLES.md ≥1KB |

### 3. modeling（建模规格）

| 参数名 | 含义 | 默认值 | 影响范围（读取方 agent） | 对标说明 |
| --- | --- | --- | --- | --- |
| `min_candidate_models` | 候选模型最少数量 | `2` | Modeler：`method-matcher`、`model-builder` | 铁律 M1 ≥2，一致 |
| `assumption_score_threshold` | 假设综合评分通过阈值 | `6.0` | Modeler：`assumption-validator`、`spec-auditor` | 保留四维评分 |
| `ambiguity_min_interpretations` | 歧义至少给出的解释数 | `2` | Modeler：`problem-parser`、`assumption-validator` | 2analysis-modeling 假设敏感性预检 |
| `multi_start_check` | 多起点/多种子稳定性检查 | `true` | Modeler：`model-builder`、`assumption-validator` | norms 第52行 |

### 4. review（评审规格，新增组）

| 参数名 | 含义 | 默认值 | 影响范围（读取方 agent） | 对标说明 |
| --- | --- | --- | --- | --- |
| `max_rounds` | 评审最大轮数 | `4` | Writer：`final-validator`（评审循环） | auto-review-loop MAX_ROUNDS=4 |
| `improvement_max_rounds` | 论文改进最大轮数 | `2` | Writer：`final-validator`（改进循环） | auto-paper-improvement-loop MAX_ROUNDS=2 |
| `pass_score` | 评审通过分（满分 10） | `6` | Writer：`final-validator` | POSITIVE_THRESHOLD score≥6/10 |
| `figure_as_subject_max` | 图表做主语句式最大次数 | `3` | Writer：`guardrails-checker` | ≥3 次记 MAJOR（improvement-loop 第62行） |

### 5. runtime（运行时）

| 参数名 | 含义 | 默认值 | 影响范围（读取方 agent） | 对标说明 |
| --- | --- | --- | --- | --- |
| `language` | 语言 `zh`/`en` | `zh` | 所有 agent 共享（决定论文/输出语言） | — |
| `template` | 论文模板 `cumcm-zh`/`mcm-en`/`generic` | `cumcm-zh` | Writer：`structure-planner`、`final-validator`；Modeler：`spec-auditor` | — |
| `strict_mode` | 严格模式（阈值不达则退回修正） | `true` | 所有手的 `*-validator` / `guardrails-checker` | — |
| `traceability_min_ratio` | 数值可追溯比例下限 | `0.90` | 所有手 `*-validator` / `hash-auditor` | norms 第70行"所有引用数值必须可追溯" |
| `numeric_tolerance_rel` | 数值相对容差上限 | `0.005` | Programmer：`result-verifier`；Writer：`consistency-checker` | 统一 consistency-checker 口径（rel ≤0.5%） |
| `numeric_tolerance_abs` | 数值绝对容差上限 | `0.01` | Programmer：`result-verifier`；Writer：`consistency-checker` | 统一 validate_project 口径（abs ≤0.01） |

## loader.py 接口用法

`loader.py` 零外部依赖（仅用 Python 标准库，内置极简 YAML 解析器，不依赖 PyYAML），可直接 `import` 使用：

```python
# 假设从项目根目录运行，或已把 core/env/ 加入 sys.path
from core.env.loader import load_config, get

# 方式一：一次性拿到完整 config dict
cfg = load_config()
print(cfg["paper"]["min_pages"])        # 25
print(cfg["code"]["random_seed"])       # 42
print(cfg["runtime"]["strict_mode"])    # True

# 方式二：按点号路径读取单个值（推荐，agent 内部使用）
get("paper.min_pages")                  # 25
get("code.random_seed")                 # 42
get("modeling.assumption_score_threshold")  # 6.0
get("runtime.template")                 # "cumcm-zh"

# key 不存在时返回 default（不抛异常）
get("not.exist.key", default="fallback")  # "fallback"
```

`load_config()` 内部会缓存加载结果，重复调用不会重复读文件；返回的是深拷贝，调用方修改不会污染缓存。

### 命令行调试

```powershell
py core\env\loader.py
```

会打印加载到的完整配置与若干 `get(key)` 示例结果，便于验证配置是否生效。

## 修改示例

### 示例 1：把最低页数改为 15

编辑 `core/env/config.yaml`：

```yaml
paper:
  min_pages: 15          # 最低页数
```

保存后，Writer 的 `final-validator` 会按 15 页校验，不足则退回 `section-writer` 补写。无需改动任何 skill 代码。

### 示例 2：把随机种子改为 2024、多次运行次数改为 10

```yaml
code:
  random_seed: 2024      # 随机种子
  multi_run_count: 10    # 启发式算法多次运行次数
```

Programmer 的 `code-implementer` 生成代码时使用新种子，`result-verifier` 按 10 次校验稳定性。

### 示例 3：切换为英文 MCM 模板、关闭严格模式

```yaml
runtime:
  language: en
  template: mcm-en
  strict_mode: false
```

所有 agent 共享该运行时配置，论文输出英文、套用 MCM 模板，且阈值不达时不强制退回修正。

## 缺失回退机制

- 若 `core/env/config.yaml` **不存在**：`load_config()` 返回 `loader.py` 内置的 `DEFAULT_CONFIG`（四组默认值与本文件表格一致），并向 stderr 打印警告，**不阻塞流程**。
- 若 `config.yaml` **某字段缺失**：仅该字段回退默认值，其余字段按文件读取（通过递归合并实现）。
- 若 `config.yaml` **解析失败**（格式错误）：整体回退 `DEFAULT_CONFIG` 并打印警告，不抛异常。

这一机制保证：即使配置文件被误删或写错，建模流程仍能以默认规格继续运行，不会因配置问题中断。

## 设计约束

- `loader.py` **零外部依赖**：不依赖 PyYAML，内置极简 YAML 解析器仅支持 `key: value`、两级缩进、`#` 注释（恰好覆盖 `config.yaml` 结构）。
- `config.yaml` 的字段类型由 `loader.py` 自动推断（int / float / bool / string），用户无需加引号。
- 修改 `config.yaml` 后无需重启进程外的任何操作，下次 `load_config()` 首次调用即生效（同一进程内会缓存，如需强制重载可调用内部 `_reload()`）。
