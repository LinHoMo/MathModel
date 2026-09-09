# MathModel — Scientific / Mathematical Modeling Harness

**面向数学模型构建、验证与模型—论文传输的可信 Harness（Verification-centered
Modeling Research Harness）。** 把一道赛题（或一个研究问题）变成一条可追溯、
可失效传播、可重放、可审计的研究证据链；论文是这条链的**投影**而非终点。

```text
Problem → Model Construction → Model Artifact → Execution → Validation
        → Evidence Graph → Revision → Research State → Paper Projection
```

> **Source of truth = Artifact Registry + Evidence Graph + Research State。**
> Agent / LLM 只是 **Executor**——GPT / Claude / DeepSeek / MathModelAgent /
> 人工建模者都可以作为可插拔执行器接入，不反过来定义系统
> （**The Agent Is Not The State**）。

核心组件：Artifact Registry（稳定 ID + 生命周期）· Typed Evidence Graph（19 种
关系 + 失效传播 + Revision lineage）· Workflow DAG（15 节点，反馈环，Per-Question
展开）· Wave Execution（波次并行）· Research Quality（七维质量层）· Runtime
Contract（冻结语义）· Deterministic Replay（重放审计）。

> 架构真源：[docs/architecture/V3.1_ARCHITECTURE.md](docs/architecture/V3.1_ARCHITECTURE.md)
> ｜ 运行时契约：[RUNTIME_CONTRACTS.md](docs/architecture/RUNTIME_CONTRACTS.md)
> ｜ 硬化计划：[HARDENING_PROGRAM.md](docs/architecture/HARDENING_PROGRAM.md)
> ｜ 三层架构：[THREE_LAYER_ARCHITECTURE.md](docs/architecture/THREE_LAYER_ARCHITECTURE.md)
> ｜ 状态真源：[docs/STATUS.md](docs/STATUS.md)（机器实测数字 + commit hash，唯一口径）
> ｜ 治理：[MODELING_KNOWLEDGE_GOVERNANCE.md](docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md)

**当前版本**：V3.1（架构已冻结，P0–P6 硬化收口）｜ 研究阶段：**P15**
（K001 已 CLOSED · **K002 正式实验已 CLOSED**（RQ1 S−F(MCQ)=−4.85 CI[−7.98,−2.22] NEGATIVE，不进 P15.2）· **P1 Model Construction Loop 三里程碑完成**（VS-001 闭环 7/7 + M3 候选竞技场 + M4 知识引导））。
**技术选型**：LaTeX（单一主线，竞赛差异用 template pack 表达）。

> P15 实验报告：K001 → `research/P15/analysis/reports/P15-K001-REPORT.md` ｜
> K002 → `research/P15/analysis/reports/P15-K002-REPORT.md` ｜
> P1 → `research/P15/analysis/P1_{VS001,M3,M4}_REPORT.md` ｜
> 状态数字唯一口径：`docs/STATUS.md`

---

## 它解决什么问题

数学建模论文的失败，很少是因为"缺少一个更聪明的回答"。更常见的是：

- 模型换了，摘要没更新；第二问重新求解后，第三问还在引用旧结果
- 论文里的数字没有任何脚本真正产出，或无法回答"这个数字是哪次运行得到的"
- 关键假设只存在于聊天记录里，上下文一断就没了
- 同一个概念存在多套 schema / 多套状态文件，系统"当前是什么状态"出现了多个答案
- 模型被"描述"了，但没有被"执行"——`execution_status=success` 不能推出
  `model_status=correct`

本项目的应对方式不是写一个更大的 Prompt，而是**把这些隐含依赖显式化**：产物落
Registry（稳定 ID + 生命周期），依赖进 Evidence Graph（上游变化自动使下游失效），
模型是**可执行、可验证、可失败、可修正、可重放**的一等对象，状态由事件日志投影、
可对账可重放，门禁由脚本判定（而非自评打勾）。

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

### 模型生命周期（核心对象）

Model Construction 不是"生成一段模型描述"，而是一条完整生命周期：

```
Problem → Question → Model Candidates → Selection Decision → MODEL_IR
       → Implementation → Execution → Validation → Evidence
       → Model Evaluation → Revision → Model Rev.2 → … → Paper Projection
```

`MODEL_IR` 是**三层可执行模型规格**（Semantic → Mathematical → Computational），
不是方法卡标签；`ExecutionResult` 是一等 Artifact（六态 status 只能来自真实执行，
禁止 handler 默认生成）；`Execution success ≠ Model correct` 是铁律。
P1-VS-001 已首次跑通完整闭环：M1（缺陷模型）→ 真实执行 → 数值校验 FAIL →
修订 M2 → 再执行 → PASS → Replay 可重现（见
`research/P15/experiments/p1-vs001/P1-VS001-REPORT.md`）。

### 四层分工

| 层 | 位置 | 生命周期 |
|---|---|---|
| product（引擎） | `core/` | 长期维护，架构已冻结（P0–P6 授权例外） |
| benchmark（能力测量） | `core/tools/`（benchmark.py / e2e_metrics.py / bench_mmbench.py） | 长期；语料在仓库外（`MMBENCH_ROOT`）；能力进步以 Δscore 度量 |
| research（研究实验） | `research/` | 实验生命周期（P15：K001/K002/P1） |
| instance（用户实例） | `projects/` | 仅 `new_project.py` 创建的运行实例 |

---

## 研究现状（P15）

| 实验 | 状态 | 结论 |
|---|---|---|
| **P15-K001**（2×2×rep 预注册：Knowledge × Case + Sham） | ✅ CLOSED（55 runs，盲评，DATA FREEZE，配对分析） | Δ_K = +2.14 CI[+0.00, +6.41] → **negative result**；Sham > K 提示"更多上下文"与"建模知识"须分离；RQ5 词表错位为 tertiary measurement limitation |
| **P15-K002**（Model Representation Efficacy：F / S / S+V 三臂） | 🔒 **FROZEN**（38 文件哈希锁定，rubric v1.1，五 Gate 全 PASS） | 预检 6 题区分度验证；v1.1 重评证实 L2 区分度恢复（E4 候选对比为唯一区分要素）；正式实验在 P1 闭环之后执行 |
| **P1**（Model Construction Loop） | ✅ **闭环**（VS-001 7/7 验收 PASS） | Gap Audit（11 环节）→ P1 计划第 2 版（C1–C10）→ 垂直切片 M1 FAIL → M2 PASS → Replay 可重现；C1（MODEL_IR 升入 core）已完成，C5–C10 按计划推进 |

- 协议/工具链：`research/P15/protocol/`（预注册、冻结规格、rubric、prompt 模板）
  · `research/P15/scripts/k001_*.py / k002_*.py`（状态机/冻结/登记/盲评/分析）
- 深度归因：`research/P15/analysis/reports/P15-K001-ATTRIBUTION.md`（negative result
  四层归因：信息增益 ceiling / 测量粒度 / 剂量 / 功效）
- 三仓库审计：`research/P15/analysis/MODEL_CONSTRUCTION_GAP_AUDIT.md`（BZD =
  评审知识 / MathModelAgent = 执行基质 / LinHoMo = 认知架构·实验室——三者非竞争，
  各缺 execution 证据 / model semantics / computational execution）

---

## 快速开始

```bash
# Windows 本机统一用 py -3.12（系统默认 py 3.14/3.13 安装损坏）
py -3.12 core/tools/new_project.py my-problem          # 创建 V3 workspace（projects/my-problem）
py -3.12 core/tools/orchestrator.py my-problem         # V3 DAG 干跑计划
py -3.12 core/tools/orchestrator.py my-problem --execute   # 真实执行（登记 Artifact/Evidence/State）

# 验证产物完整性（交付前必跑）
py -3.12 core/tools/validate.py                        # 项目级 57 项校验
py -3.12 core/tools/catalog_check.py --check           # 双视图三方一致性
py -3.12 -m pytest tests -q                            # 单元/集成/端到端（以 STATUS.md 实测为准）
```

---

## 目录结构

```
MathModel/
├── core/                            # 引擎（唯一可复用资产，架构冻结）
│   ├── runtime/                     # V3 认知运行时：artifacts / state / graph / execution / modeling / knowledge
│   ├── roles/  workflows/           # 5 角色 / Workflow DAG（YAML 定义）
│   ├── validators/                  # evidence / quality / modules（L1–L6 门禁）
│   ├── schemas/                     # v3/ 六域 canonical schema
│   ├── evaluation/  tools/          # 评分链 / benchmark / 能力指标 / runtime 工具
│   ├── skills/  knowledge/  env/  templates/  adapters/
├── catalog.yaml + catalog/          # 双视图元数据索引（单一真源；model_families.yaml 已 frozen）
├── research/                        # 研究实验（P15：K001/K002/P1；bench 运行）——带实验专属脚本
├── projects/                        # 用户运行实例（仅 new_project.py 创建）
├── docs/                            # 架构与状态文档（architecture/ 为真源，STATUS.md 为状态唯一真源）
├── tests/                           # unit / integration / e2e / regression（含 P1 闭环测试）
├── examples/                        # 少量可运行示例
├── AGENTS.md                        # agent 活动入口（唯一权威协议）
└── pyproject.toml                   # pytest marker 注册等工程配置
```

---

## 当前状态

状态唯一真源是 [docs/STATUS.md](docs/STATUS.md)：所有数字来自机器命令实测并记录
commit hash。**历史文档中的旧数字（228/574/751/774/855 等）一律作废，以
STATUS.md 当前口径为准。**

## 设计原则与治理红线

1. **Artifact 是真源**：所有下游表示（Evidence / Experiment / Paper / Evaluation）都是投影
2. **状态可对账**：Event Log → Projection → status.json，禁止多个状态真源并存
3. **可重放可审计**：每次运行留 RunRecord（版本/哈希/模型/输入），可 deterministic replay
4. **可验证**：阈值集中在 env，判定交给脚本，不靠人工自觉
5. **引擎与实例分离**：`core/` 是唯一可复用引擎，`projects/<项目>/` 是校验下的运行实例
6. **The Agent Is Not The State**：Agent/LLM/Handler 永远不是事实来源
7. **infra 不冒充 capability**：任何新 schema/contract/validator 必须回答
   "它改变了哪个可测量的 Model Construction 行为？"——答不出不得包装成能力提升
8. **Execution success ≠ Model correct**：execution_status / model_status /
   evidence_status 三级分离，禁止越级
9. **Knowledge claim ≠ empirical fact**：经验判断不得经确定性脚本包装成"客观测量
   （formalized false authority 禁令）；知识卡 = Constraint / Prior，不是答案库
10. **Model Construction=What · Model Representation=How · Harness=How do we know**
    （用户锁定三层定位：只做 LLM-free Harness，认知由外部 Agent 完成）

详见：`docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md`、
`research/P15/analysis/STRATEGY_P1_VS001.md`、`STRATEGY_P1_MODEL_CONSTRUCTION.md`。

---

## 命令速查

```text
# V3 运行时
py -3.12 core/tools/orchestrator.py <项目> [--execute]   # DAG 干跑 / 真实执行
py -3.12 core/tools/validate.py                          # 项目级 57 项校验
py -3.12 core/tools/catalog_check.py --check             # catalog 三方一致
py -3.12 core/tools/catalog_check.py --check-terminology # 术语零残留
py -3.12 core/tools/replay.py <项目> [<run_id> [diff <run_id>]]   # 重放 / 差异归因
py -3.12 core/tools/knowledge.py recommend --types <题型>        # 方法卡检索
py -3.12 core/tools/score_compute.py <项目>              # 自动化 5 维评分卡
py -3.12 core/tools/benchmark.py bench {list,run,score,report}

# P15 研究工具链（协议/冻结/状态机/盲评）
py -3.12 research/P15/scripts/k001_state.py show         # K001 状态机
py -3.12 research/P15/scripts/k002_state.py show         # K002 状态机（FROZEN）
py -3.12 research/P15/scripts/k002_freeze.py --check     # K002 冻结漂移校验
```

> Windows 本机：`py` 默认解释器（3.14/3.13）安装损坏，请用 `py -3.12 ...`。

## 许可与边界

本仓库是协作与质量控制工具，不是自动获奖系统。AI 生成的公式、代码、事实和引用
必须人工复核；竞赛规则（页数、匿名、AI 使用披露）变化频繁，提交前须以当届官方
通知为准。
