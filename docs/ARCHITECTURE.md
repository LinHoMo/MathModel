# Architecture

> **⚠️ 权威声明（V3 Documentation Authority Cutover）**
> 本文件描述的「四手 29 agent」线性流水线自 V3 起降级为 **legacy 视图**。
> 当前架构真源是 **V3.1 Cognitive Workflow Runtime**：
> **[docs/architecture/V3.1_ARCHITECTURE.md](architecture/V3.1_ARCHITECTURE.md)**
> （Artifact Registry + Typed Evidence Graph + Workflow DAG + 5 Role + 6 Validator + Knowledge 层）。
> 迁移映射见 [V3_MIGRATION_MAP.md](architecture/V3_MIGRATION_MAP.md)，最终审计见 [V3_FINAL_AUDIT.md](architecture/V3_FINAL_AUDIT.md)。
> `catalog.yaml`（schema_version 5）是双视图（legacy hands / v3）的单一真源；
> `core/tools/` 脚本已按职责归入六类子包（runtime / validation / evaluation /
> knowledge / devtools / rendering），根目录保留兼容 shim，AGENTS.md 协议命令不变。
> 下文 legacy 描述仅在维护 `state.py` legacy 流水线时参考。

MathModelSkills 采用角色化架构，把「一道赛题 → 一篇论文」拆成四个独立角色（四手），
每手内部多 agent 按 UTG 六层防御串联，最终交付可追溯、可复现、无 AI 痕迹的论文。

## 分层定位

仓库分四层，职责边界清晰：

| 层 | 目录 | 内容 | 谁维护 |
|---|---|---|---|
| **引擎** | `core/` | 四手的 SKILL.md / agents / laws / knowledge / templates，共享知识库 `core/knowledge/`，验证模块 `core/validators/modules/`，`core/env/` 配置层，`core/schemas/` 输出 Schema，`core/tools/` 工具脚本 | 开发者 |
| **入口** | 根目录 | `AGENTS.md`（唯一权威入口）+ 各 runtime 转发文件（`CLAUDE.md` / `.cursorrules` / `.trae/rules/` 等）+ `catalog.yaml`（agent 元数据索引）+ 安装脚本 | 开发者 |
| **实例** | `projects/<项目>/` | 一个赛题的完整运行时产物：`inputs/` 赛题、`work/` 状态、`output/` 契约、`code/` 代码、`figures/` 结果、`paper/` 论文 | 每次跑题生成 |
| **基础设施** | `docs/` / `tests/` / `.github/` | 架构与状态文档、unit/integration/e2e 测试、CI 入口 | 开发者 |

引擎层新增工具文件：

| 文件路径 | 作用 |
|---|---|
| `core/tools/validation/citation_check.py` | 引用可信度静态扫描（占位符/格式/闭合/承诺兑现） |
| `core/tools/evaluation/benchmark.py bench *` | 国赛复盘基准（rubric 列表/模板/重算/报告） |
| `core/tools/evaluation/bench_mmbench.py` | LLM-MM-Agent MMBench 题库导入适配器 |
| `core/knowledge/bench/cumcm/` | 22 年 CUMCM 评分细则 rubric |

核心原则：**引擎（`core/`）是唯一可复用资产**，实例（`projects/`）是引擎在校验下跑出来的结果；
两者分离，改引擎不动实例，换实例不伤引擎。

## 核心设计

### 1. 角色分离

每个角色（Modeler、Programmer、Writer、Reviewer）是独立单元，位于 `core/<Hand>/`：
- `SKILL.md` - 手级编排器
- `agents/<name>/SKILL.md` - 手内多 agent
- `laws/rules.md` - 铁律
- `knowledge/` - 手私有知识库
- `templates/` - 契约模板

### 2. 契约协作

角色间通过标准化契约文件传递信息，契约是角色间唯一接口，实现松耦合：

- Modeler → `MODEL_SPEC.md` → Programmer
- Programmer → `CODE_DELIVERABLES.md` → Writer
- Writer → `PAPER_SPEC.md` → Reviewer
- Reviewer → `work/execution_report.json` → 最终交付

### 3. 知识库分层共享

知识库分两层：**共享层 `core/knowledge/`（四手共用）** + 私有层 `core/<Hand>/knowledge/`（单手私有）。

共享层（`core/knowledge/`）：
- `methodology/` - 50 篇方法论文档 + METHOD-DECISION-TREE + INDEX（method-matcher / model-builder 消费）
- `cookbooks/` - 8 大类算法手册（优化/ML/评价/机理/统计/网络/聚类/博弈，method-matcher 消费）
- `playbooks/` - 12 个端到端例题（国赛 9 + 美赛 3，含拆题→代码→论文全流程）
- `paper-cases/` - 论文案例拆解 + METHOD-MAPPING.md + INNOVATION-TAGS.md
- `empirical/` - 获奖论文实测分位锚定（cumcm-empirical.json，117 篇蒸馏 p25/p50/p75）
- `data-sources/` - 数据源清单 + 文献检索脚本（DATA-SOURCES.md / scholar_fetch.py）
- `problems/` - 历年赛题库（INDEX.md + MCM-ICM.md）
- `review/` - 评审视角洞察（judge-insights 等）
- `validation/` - 20 个验证模块（guardrails / hash_chain / stage_gate / consistency_checker 等，跨手调用）
- `pitfalls/` - 反模式库 + 数值边界 bug 库
- `_negative/` - 反例库（真实翻车案例，供 weakness-hunter / 反思银行消费）
- `templates/mathmodel/` - 论文模板

私有层：
- `core/Modeler/knowledge/` - domain（43 个领域知识）+ problem-types（5 个题型专项）+ paper-bridge.md
- `core/Programmer/knowledge/` - code-templates（优化 / 时序 / 图 / 聚类 / 仿真等代码模板）+ platform-guide.md
- `core/Writer/knowledge/` - writing（写作规范）+ profiles（竞赛与题型画像）+ reference（图表规范）+ templates

### 4. 迭代优化

每个角色内部支持迭代修正：
- Modeler：假设验证不通过时返回修正
- Programmer：测试不通过时返回修正
- Writer：校验不通过时返回修正

## 数据流

```
┌─────────────────────────────────────────────────────────────┐
│                        输入层                                │
│  projects/<项目>/inputs/                                     │
│  └── 赛题文件（PDF/Word/TXT）                                │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Modeler（建模手）                         │
│  读取题目 → 问题分解 → 题型识别 → 方法匹配 → 模型建立        │
│  输出：output/MODEL_SPEC.md                                  │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Programmer（编程手）                        │
│  读取 MODEL_SPEC → 选择模板 → 实现代码 → 测试 → 结果验证    │
│  输出：output/CODE_DELIVERABLES.md + figures/all_results.json│
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Writer（论文手）                         │
│  读取 CODE_DELIVERABLES → 撰写论文 → 图表 → 文献 → 校验     │
│  输出：output/PAPER_SPEC.md + paper/main.pdf                 │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Reviewer（评审手）                         │
│  打分 → 挑缺陷 → 出修改清单 → 执行局部回修                   │
│  输出：work/execution_report.json                            │
└─────────────────────────────────────────────────────────────┘
```

数据流：`inputs/` → Modeler → `MODEL_SPEC.md` → Programmer → `CODE_DELIVERABLES.md` → Writer → `paper/main.pdf`。

## 铁律体系

每个角色有自己的铁律，不可违反（共 35 条：M1–M9 / P1–P12 / W1–W14）：

### Modeler 铁律 (M1-M9)
- M1: 模型选择必须比较至少 2 个候选方法
- M2: 每个假设必须有量化验证
- M3: 数学推导必须从基本定律到最终模型
- M4: 符号定义必须完整，含量纲
- M5: 边界条件必须明确列出
- M6: 启发式算法不能直接宣称全局最优
- M7: MODEL_SPEC.md 必须包含所有子问题的完整建模方案
- M8: 假设敏感性预检：赛题歧义处至少 2 种解释并裁决，关键假设可参数化
- M9: 防数据泄露：预测类禁未来信息训练，多目标先量纲归一化

### Programmer 铁律 (P1-P12)
- P1: 代码必须设置随机种子（`np.random.seed(42)`），保证可复现
- P2: 所有数值必须可追溯到 all_results.json
- P3: 代码文件必须放在 code/ 目录
- P4: 每个代码文件必须有 docstring
- P5: 必须处理异常情况
- P6: 启发式算法必须多次运行（≥5 次）报告均值与标准差
- P7: 优化问题必须先保证可行解
- P8: 数据读取后必须检查
- P9: CODE_DELIVERABLES.md 必须包含运行说明
- P10: 约束重验证：最优解重新代入所有约束检查可行性
- P11: 求解器超时分级：按变量数分级（300/600/1200s），定期输出当前最优
- P12: 修复轮数上限：每子问题最多 3 轮，超限回退 Modeler

### Writer 铁律 (W1-W14)
- W1: 论文中每个数值必须能追溯到 all_results.json
- W2: 摘要必须包含具体数值结果
- W3: 每个假设必须有必要性说明
- W4: 每张图表前后必须有分析文字
- W5: 参考文献必须真实存在
- W6: 禁止使用 AI 痕迹词汇
- W7: 禁止出现内部文件名
- W8: 禁止有占位符残留
- W9: 灵敏度分析必须存在
- W10: 模型评价必须诚实讨论缺点
- W11: 正文禁列表：摘要与正文禁 itemize/enumerate，附录豁免
- W12: 图表引用句式：禁图表做主语，用括号旁注，每图后 ≥3-5 句分析
- W13: 摘要规格：400-600 字，含每子问题方法 + 具体数值
- W14: 版面规格：图宽 ≥0.85\textwidth，正文表 ≤12 行，超 15 行转 longtable

## 六层防御体系

在每个角色中嵌入六层防御，从源头到交付层层拦截错误：

| 层 | 机制 | Modeler | Programmer | Writer |
|---|---|---|---|---|
| L1 | 形式化规约（结构化输出 + 消歧） | problem-parser / type-classifier | template-selector | structure-planner |
| L2 | 工具调用与生成（类型制导） | method-matcher | code-implementer | section-writer / figure-generator |
| L3 | 过程验证（推导链 / 契约 / 引用闭合） | model-builder | test-runner | reference-curator |
| L4 | 异构验证（量化评分 / 跨方法对照） | assumption-validator | result-verifier | consistency-checker |
| L5 | 运行时护栏（禁用词 / 占位符 / AI 痕迹 / 权限） | spec-auditor | guardrails-checker | guardrails-checker |
| L6 | 事后哈希审计（篡改检测 + 错误归因） | spec-auditor | hash-auditor | final-validator |

### 验证模块清单（统一位于 `core/validators/modules/`）

| 层 | 模块 | 功能 |
|---|---|---|
| L1 | problem_spec_parser.py / symbol_registry.py / assumption_validator.py | 赛题解析 / 符号注册 / 假设验证 |
| L2 | type_system.py / formula_checker.py / output_validator.py | 类型推导 / 公式检查 / 输出校验 |
| L3 | invariant_tracker.py / contract_checker.py / stage_gate.py / process_verifier.py | 不变式 / 契约 / 阶段门禁 / 过程验证 |
| L4 | symbolic_verifier.py / cross_model_checker.py / consistency_checker.py | 符号验证 / 异构交叉 / 论文代码一致性 |
| L5 | trust_domain.py / permission_guard.py / incremental_checker.py / guardrails.py | 信任域 / 权限守卫 / 增量校验 / 护栏 |
| L6 | hash_chain.py / error_attribution.py / rule_iterator.py | 哈希追溯链 / 错误归因 / 规则迭代 |

## 验证机制

- **单步门禁**：`python core/tools/gate.py <项目> <hand> <agent>`，由脚本判定而非人工勾选
- **全链路门禁**：`python core/tools/gate.py <项目> all`
- **项目级校验**：`python core/tools/validate.py`（57 项，覆盖 L1–L6）
- **单项目校验**：`python core/tools/validate_project.py <项目>`
- **测试套件**：`python -m pytest tests -q`（unit / integration / e2e 三层）

### validate.py 57 项检查分布

| 层 | 项数 | 覆盖内容 |
|---|---|---|
| L1 | 14 | env 配置三件套 + Schema 目录/格式 + 四手 agents 结构 + catalog.yaml + AGENTS.md + 输入规约 Schema + 符号注册表 + 假设验证器 |
| L2 | 3 | 类型系统 + 公式检查器 + 输出验证器 |
| L3 | 6 | 目录结构 + Python 语法 + 知识库 + laws + 不变式跟踪 + 契约校验 / 阶段门禁 |
| L4 | 5 | 符号验证器 + 异构模型 + 一致性校验 + 物理模型 + 数值追溯 |
| L5 | 10 | 信任域 + 权限守卫 + 增量校验 + 禁用词 + 占位符 + AI 痕迹 + 内部路径 + 正文列表 + 图表主语句式 |
| L6 | 19 | 哈希追溯链 + 错误归因 + 规则迭代 + 文档 + 测试 + checkpoint 格式 + 论文结构 + 引用完整性 + 图表引用 + 灵敏度 + 模型评价 + 假设必要性 + 文献年份 + 表格行数 |

**当前状态：56 通过 / 0 失败 / 1 警告**（警告项为文献年份占比 7% < 60%，WARN 级不阻塞，基准为赛题年份 2024）。

### 两处口径说明（易踩坑）

1. **论文字数**：按「跳过导言区 → 去注释 → 去数学环境 → 去 LaTeX 命令 → 统计中文字符 + 正文英文单词」计算。直接统计 LaTeX 源码会把 `\theta`、`\begin`、`\cite` 等命令计入，实测虚高约 2000 字。
2. **文献年份**：近 3 年以**赛题年份**为基准（从 `projects/<项目名>` 推断），非当前年份；同时检测「未来文献」（年份晚于赛题年份）视为引用造假信号。