# MathModel — Scientific / Mathematical Modeling Harness

**面向数学模型构建、验证与模型—论文传输的可信 Harness（Verification-centered
Modeling Research Harness）。** 把一道赛题（或一个研究问题）变成一条可追溯、
可失效传播、可重放、可审计的研究证据链；论文是这条链的**投影**而非终点。

```text
Problem → Research State → Workflow DAG → Artifact + Evidence Graph
        → Research Quality（七维） → Paper Projection
```

> **Source of truth = Artifact Registry + Evidence Graph + Research State。**
> Agent / LLM 只是 **Executor**——GPT / Claude / DeepSeek / MathModelAgent /
> 人工建模者都可以作为可插拔执行器接入，不反过来定义系统。

核心组件：Artifact Registry（稳定 ID + 生命周期）· Typed Evidence Graph（14 种关系 +
失效传播）· Workflow DAG（15 节点，反馈环，Per-Question 展开）· Wave Execution
（波次并行）· Research Quality（七维质量层）· Runtime Contract（冻结语义）·
Deterministic Replay（重放审计）。

> 架构真源：[docs/architecture/V3.1_ARCHITECTURE.md](docs/architecture/V3.1_ARCHITECTURE.md)
> ｜ 运行时契约：[RUNTIME_CONTRACTS.md](docs/architecture/RUNTIME_CONTRACTS.md)
> ｜ 硬化计划：[HARDENING_PROGRAM.md](docs/architecture/HARDENING_PROGRAM.md)
> ｜ 状态真源：[docs/STATUS.md](docs/STATUS.md)

**当前版本**：3.0.0-dev（System Hardening，P0–P6 收口中）｜ V2 legacy 四手流水线
保留为**兼容层**（`core/legacy/hands/`），由 `state.py` / `gate.py` legacy 模式驱动，
见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。**技术选型**：LaTeX（单一主线，
竞赛差异用 template pack 表达）。

---

## 它解决什么问题

数学建模论文的失败，很少是因为"缺少一个更聪明的回答"。更常见的是：

- 模型换了，摘要没更新；第二问重新求解后，第三问还在引用旧结果
- 论文里的数字没有任何脚本真正产出，或无法回答"这个数字是哪次运行得到的"
- 关键假设只存在于聊天记录里，上下文一断就没了
- 同一个概念存在多套 schema / 多套状态文件，系统"当前是什么状态"出现了多个答案

本项目的应对方式不是写一个更大的 Prompt，而是**把这些隐含依赖显式化**：产物落
Registry（稳定 ID + 生命周期），依赖进 Evidence Graph（上游变化自动使下游失效），
状态由事件日志投影、可对账可重放，门禁由脚本判定。

---

## 架构（V3 主视图）

```
               ┌──────────────────────────────────┐
               │    Workflow Runtime（唯一执行真源）   │
               │  State · Artifact · Evidence · Gate │
               └──────────────┬───────────────────┘
            ┌─────────────────┼──────────────────┐
            ↓                 ↓                  ↓
         Skills             Tools            Executors
      modeling skill       solver          GPT / Claude /
      verification         parser          MathModelAgent /
      paper mapping        validator       Human（可插拔）
```

五层分工：

| 层 | 位置 | 生命周期 |
|---|---|---|
| product（引擎） | `core/` | 长期维护，架构已冻结 |
| legacy（兼容层） | `core/legacy/hands/` | 只读兼容，不新增 |
| benchmark（能力测量） | `core/tools/evaluation/`（能力层 8 件） | 长期；语料在仓库外（`MMBENCH_ROOT`） |
| research（研究实验） | `research/` | 实验生命周期，收尾可归档 |
| instance（用户实例） | `projects/` | 仅 `new_project.py` 创建的运行实例 |

### V2 legacy 兼容层（四手 29 agent）

V2 的 Modeler（8）/ Programmer（6）/ Writer（7）/ Reviewer（8）共 29 个 agent
流水线整体保留在 `core/legacy/hands/`，作为兼容层（被 V3 roles/DAG 取代）。
`catalog.yaml` 双视图（hands + v3）是结构单一真源，`catalog_check.py --check`
强制三方一致。legacy 执行协议见根 [AGENTS.md](AGENTS.md)「兼容模式」章节。

### env 配置层

所有阈值集中在 `core/env/config.yaml`，由零依赖的 `core/env/loader.py` 注入：

| 组 | 关键参数 |
|---|---|
| `paper` | min_pages 17 / min_words 13000 / min_figures 6 / min_tables 4 / min_equations 15 / min_references 10 |
| `code` | random_seed 42 / multi_run_count 5 / cv_threshold 0.10 / max_fix_rounds 3 / sensitivity_range 0.20 |
| `modeling` | min_candidate_models 2 / assumption_score_threshold 6.0 / ambiguity_min_interpretations 2 |
| `review` | max_rounds 4 / pass_score 6 / figure_as_subject_max 3 |
| `runtime` | language zh / template cumcm-zh / strict_mode true / traceability_min_ratio 0.90 |

---

## 快速开始

```bash
# V3 模式（认知工作流运行时）
python core/tools/new_project.py my-problem          # 创建 V3 workspace（projects/my-problem）
python core/tools/orchestrator.py my-problem         # V3 DAG 干跑计划
python core/tools/orchestrator.py my-problem --execute   # 真实执行（登记 Artifact/Evidence/State）

# V2 兼容模式（四手 29 步流水线）
python core/tools/state.py my-problem init           # 从产物反推进度
python core/tools/state.py my-problem status         # 显示下一步
python core/tools/orchestrator.py my-problem --legacy

# 验证产物完整性
python core/tools/validate.py                        # 项目级校验
python core/tools/catalog_check.py --check           # 双视图三方一致性
```

## 目录结构

```
MathModel/
├── core/                            # 引擎（唯一可复用资产，架构冻结）
│   ├── runtime/                     # V3 认知运行时：artifacts / state / graph / execution / knowledge / legacy / adapters
│   ├── roles/  workflows/           # 5 角色 / Workflow DAG（YAML 定义）
│   ├── validators/                  # evidence / quality / modules（42 模块 L1–L6）
│   ├── schemas/                     # v3/ 六域 canonical schema + V2 兼容 schema（legacy 视图）
│   ├── evaluation/                  # 评分链 / benchmark / 能力指标（e2e_metrics 八项）
│   ├── tools/                       # runtime/validation/evaluation/knowledge/devtools/rendering 子包 + 根 shim（命令兼容）
│   ├── legacy/hands/                # V2 兼容层：Modeler / Programmer / Writer / Reviewer 四手
│   ├── skills/  knowledge/  env/  templates/
│   └── adapters/                    # 运行时适配 manifest
├── research/                        # 研究实验（P13-3D 系列 / bench 运行）——带实验专属脚本
├── projects/                        # 用户运行实例（仅 new_project.py 创建）
├── archives/                        # 历史样例归档（只读，不计入实时校验）
├── examples/                        # 少量可运行示例（problems/cumcm2024A.txt）
├── docs/                            # 架构与状态文档（architecture/ 为真源）
├── tests/                           # unit / integration / e2e / regression / compat
├── AGENTS.md                        # agent 活动入口（唯一权威协议）
├── catalog.yaml + catalog/          # 双视图元数据索引（单一真源）
└── pyproject.toml                   # pytest marker 注册等工程配置
```

## 当前状态

状态唯一真源是 [docs/STATUS.md](docs/STATUS.md)：所有数字来自机器命令实测
并记录 commit hash（System Hardening P0 起执行）。**历史文档中的旧数字
（228/574/751 等）一律作废，以 STATUS.md 当前口径为准。**

## 设计原则

1. **Artifact 是真源**：所有下游表示（Evidence / Experiment / Paper / Evaluation）都是投影
2. **状态可对账**：Event Log → Projection → status.json，禁止多个状态真源并存
3. **可重放可审计**：每次运行留 RunRecord（版本/哈希/模型/输入），可 deterministic replay
4. **可验证**：阈值集中在 env，判定交给脚本，不靠人工自觉
5. **引擎与实例分离**：`core/` 是唯一可复用引擎，`projects/<项目>/` 是校验下的运行实例；
   `research/` 实验与 `projects/` 实例生命周期分离

## 许可与边界

本仓库是协作与质量控制工具，不是自动获奖系统。AI 生成的公式、代码、事实和引用必须人工复核；竞赛规则（页数、匿名、AI 使用披露）变化频繁，提交前须以当届官方通知为准。

---

## 命令速查

```text
python core/tools/state.py <项目> {init,status,advance,fail,reset,reconcile}
python core/tools/gate.py <项目> <hand> <agent>        # 单步门禁
python core/tools/gate.py <项目> all                   # 全链路门禁
python core/tools/orchestrator.py <项目> [--execute|--legacy]
python core/tools/validate.py / validate_project.py <项目>
python core/tools/catalog_check.py --check
python core/tools/citation_check.py project <项目> / bib <file>
python core/tools/benchmark.py bench {list,run,score,report}
python core/tools/bench_mmbench.py {list,export,path}
python core/tools/replay.py <项目> [<run_id> [diff <run_id>]]
python core/tools/knowledge.py recommend --types <题型>
python core/tools/score_compute.py <项目>
```

> Windows 本机：`py` 默认解释器（3.14/3.13）安装损坏，请用 `py -3.12 ...`。