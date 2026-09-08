# MathModel 项目交接文档（HANDOFF）

> **交接时间**：2026-09-08
> **交接人**：MainAgent（Doubao）+ OrganizerAgent o_0001tZGvuba
> **接收人**：下一个执行 Agent
> **仓库路径**：`C:\Users\Lin\Desktop\Programs\MathModel`
> **Python 运行时**：`py -3.12`（默认 py 3.14/3.13 损坏，统一用此）

---

## 一、项目定位（已锁定，不可偏离）

### 一句话定位

> MathModel 是一个面向数学建模的 **LLM-free、可复现、可审计**的建模过程实验基础设施，核心目标是将数学建模过程**结构化、标准化、可视化并可验证**。它让**外部 Agent**（Doubao/GPT/Claude/人）负责实际认知与模型构造，由 **Harness** 负责冻结问题、记录建模过程、建立模型与证据的可追溯关系、验证执行真实性并进行能力测量。第一阶段以数学建模竞赛为受控实验场，最终将同一套 Model Representation 与 Measurement Infrastructure 扩展到科研论文中的具体数学建模问题。

### 锁死的核心信念

> 不是让 AI 写出一篇数学建模论文，而是把"现实问题→数学模型→计算→验证→结论"这一过程本身变成可观察、可结构化、可验证、可比较的对象。LLM-free Harness 保证：看到的"模型能力"真的是 Agent 的，而不是 Harness 替它做的，也不是坏尺子测出来的。

### 三个核心名词（全仓库口径一致）

| 名词 | 含义 | 回答的问题 |
|---|---|---|
| **Model Construction** | 核心能力对象（What） | Agent 能不能把现实问题构造成正确、完整、自洽、可求解、可验证的数学模型？ |
| **Model Representation** | 核心标准化对象（How） | 一个数学模型如何被机器和人结构化表达？产物形态：Model IR / Model Graph / Model Card / Model Trace |
| **Harness** | 核心可信度对象（How do we know） | 怎么证明模型确由 Agent 构造、测量未被伪造、如何复现与定位失败？ |

### 不可违反的铁律

1. **core/runtime 永久 LLM-free**：绝不在 core 内构建 LLM 执行器或把项目做成完整数模 Agent。认知工作由外部 Agent 完成。
2. **synthetic/dry_run 永不进能力结论**：只有 `executor_type=external_agent` 的产物可进入能力评分。
3. **不伪造题面/结果**：所有赛题必须来自真实可追溯来源，带 SHA256 + provenance。
4. **不为了提高分数修改 evaluator**：测量仪器独立于被测量对象。
5. **不修改 .gitignore / .git/**：任何 agent 不得修改版本控制元数据。
6. **不删除 research evidence**：P13/P14/P15 的实验证据即使不被 runtime import 也具有科研价值。
7. **core 修改必须由真实 failure mode 驱动**：经过 minimal patch + non-regression。
8. **标准化的是表达/接口/证据，不是答案**：同一题 ODE/状态空间/递推/PDE 都允许进入同一 Harness。

---

## 二、本次会话完成的工作

### 2.1 深度审计（第一轮，Organizer 完成）

产出 10 份审计报告（~350KB），位于 `research/REPOSITORY_AUDIT/`：

| 文件 | 内容 |
|---|---|
| `EXECUTIVE_SUMMARY.md` | 12 问回答 + 战略定位更新 |
| `FINAL_AUDIT_REPORT.md` | 全过程 + 验证记录 |
| `01_REPOSITORY_INVENTORY.md` | 仓库清单（34KB） |
| `02_DEBT_LEDGER.md` | 债务台账（35KB） |
| `03_ARCHITECTURE_AUDIT.md` | 架构与测试审计（50KB） |
| `04_MODELING_CAPABILITY_AUDIT.md` | 建模能力审计（61KB） |
| `05_BENCHMARK_AUDIT.md` | Benchmark 审计 + B0 失效根因（56KB） |
| `06_COMPETITIVE_LANDSCAPE.md` | 竞争格局（27KB） |
| `07_SOURCE_PROVENANCE.md` | 资料溯源（44KB） |
| `08_RECOMMENDED_TARGET_ARCHITECTURE.md` | 推荐目标架构（三层结构更新版） |

**核心发现**：2024_A B0 测量完全无效——输入题面实际是"防空导弹"（实为 2025_A 被错误标记为 2024_A）；pipeline 未真实执行（latency=0.06s, model_provider=null, 16 个空壳 artifact）；evaluator 放过空壳；4/5 题 BLOCKED。

### 2.2 测量恢复（第二轮，Organizer 完成）

位于 `research/P15/measurement_recovery/` 和 `research/P15/capability/`：

**输入真实性恢复**：
- 5 道 benchmark 题全部找回真实题面（0 BLOCKED），每题 2 来源交叉验证 + SHA256
- 2024_A = "板凳龙闹元宵"，sha256=`9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e`
- 2022_C = 古代玻璃成分分析
- 2020_B = 穿越沙漠
- 2018_A = 高温作业服装设计
- 2019_C = 机场出租车

**P0 测量修复（5 项）**：
- P0-1：题面污染修复（`examples/problems/cumcm2024A.txt` 和 `projects/p151-2024a/inputs/cumcm2024A.txt`）
- P0-2：e2e_metrics 空壳过滤（`core/tools/evaluation/e2e_metrics.py` +287 行）
- P0-3：method_selection 从字符串匹配改为模型族匹配
- P0-4：model_correctness 结构校验
- P0-5：execution_gate 接入评估编排（`research/P15/measurement_recovery/execution_gate.py`，41KB）

**能力本体重建**：
- 11 项能力地图（`research/P15/capability/CAPABILITY_MAP.md`，31KB）
- 25 个可测量 Failure Mode（`FAILURE_TAXONOMY.md`，44KB）
- L1-L4 Model Construction 评分细则（`MODEL_CONSTRUCTION_RUBRIC.md`，18KB）
- 5 张 Problem Card（`research/P15/benchmark/problem_cards/`）

**关键根因确认**：整个 `core/` 零 LLM API 客户端导入，`DefaultNodeExecutor` 是确定性纯内存操作桩——此前没有任何一次运行真正调用过 LLM。**这不是缺陷，是设计要求**（Harness ≠ Agent）。

### 2.3 架构纠偏：External-Agent Execution Interface

撤销了"core 内 LLM 执行器"方向，改为外部 Agent 执行接口：

- `external_artifact_manifest.schema.json`：executor_type 三态 enum（external_agent / dry_run / synthetic）
- `register_external_artifact.py`（616 行）：外部 Agent 唯一合规登记入口
- `mark_executor_type.py`：旧项目 executor_type 标注
- `execution_gate.py` v2.0：增加 executor_type 判据 + EAG-14/15/16
- synthetic/dry_run 项目：gate 判 SKIPPED=13，退出码 2，明确"不适用"

### 2.4 Model IR / Model Graph 规范（最高优先级交付物）

位于 `research/P15/model_representation/`：

| 文件 | 大小 | 内容 |
|---|---|---|
| `MODEL_IR_SPEC.md` | 66.2KB | 13 字段组完整定义 + Model Graph 14节点15边 + 15项 deterministic checks + Model Diff 规范 + Modeling Trace + 2024_A 完整实例 |
| `model_ir.schema.json` | 20.4KB | JSON Schema draft 2020-12，全部字段组 + $defs |
| `example_2024_A.json` | 27.5KB | 板凳龙完整实例：5假设/12变量/10参数/2目标/6约束/2机制/5方程/10依赖/16图节点/13图边 |

**验证**：Schema 校验 PASS；10/11 deterministic checks PASS（DC-006 WARN 为合理中间变量）。

### 2.5 仓库结构清理（MainAgent 直接执行，本轮完成）

| 操作 | 详情 | 验证 |
|---|---|---|
| `.claude/` 删除 | 10 个 syslab 技能包（101 文件）用 `git mv` 迁到 `core/skills/syslab/`，历史保留；更新 catalog/external_skills.yaml 和 V3_BASELINE_AUDIT.md 引用 | git 全部识别为 rename |
| `archives/` 删除 | 有用的不完整项目样例迁到 `tests/fixtures/sample_incomplete_project/`（污染题面替换为干净 generic sample）；更新 test_pipeline.py、test_gate_paper_thresholds.py、metrics.py、validate.py、test_structure.py、README.md、docs/METRICS.md、docs/STATUS.md、projects/README.md、RC-SMOKE RUNBOOK 共 11 处引用 | pytest 781/11 零回归 |
| `package.json` / `package-lock.json` 删除 | V2 残留占位，描述与新定位冲突，无真实依赖 | git rm |
| `node_modules/` 删除 | 本地杂物（gitignored） | 磁盘清理 |
| `.opencode/` 清理 | 唯一文件 V3_ARCHITECTURE_PLAN.md 迁到 `docs/architecture/` | git mv |
| 规则 shims 保留 | CLAUDE.md/GEMINI.md/.clinerules/.cursorrules/.windsurfrules 均为指向 AGENTS.md 的多工具入口指针，是好实践 | 保留 |
| `.trae/.zcode/.workbuddy` 保留 | 均为未跟踪/被忽略的本地工具环境，不污染仓库 | 不动 |

**非回归验证结果**：
- pytest：**781 passed, 11 skipped**（34.09s）——与基线完全一致
- catalog_check --check：**PASS**（v3 双视图三方一致）
- validate.py：53 通过 / 4 失败 / 0 警告——4 个失败全是 `projects/p151-2024a/` 里不完整 synthetic 论文的内容级问题（字数 63/13000、图 1/6、表 1/4、公式 2/15、物理模型检查缺失、数值追溯 25%<90%），是 B0-R2 合成运行的半成品论文被 validate 实际校验到了，**不是本次清理导致的回归**

---

## 三、当前仓库结构（清理后）

```
MathModel/
├── AGENTS.md                    # 权威执行协议（canonical，95 行）
├── CLAUDE.md / GEMINI.md       # 规则 shim → 指向 AGENTS.md
├── .clinerules / .cursorrules / .windsurfrules  # 同上
├── Dockerfile / docker-compose.yml
├── install.ps1 / install.sh    # 多目标安装器（把 core/ 装到外部工具家目录）
├── pyproject.toml
├── catalog.yaml                 # 结构单一真源（hands + v3 双视图）
├── catalog/
│   └── external_skills.yaml     # 外部技能注册表（syslab 等）
├── core/                        # 产品层（冻结架构 v3.1.0）
│   ├── env/                     # 配置（config.yaml + loader.py）
│   ├── evaluation/              # 评估器（e2e_metrics.py 等）
│   ├── knowledge/               # 知识库（含 bench/ 语料——待迁出，见待办）
│   ├── legacy/hands/            # V2 兼容层（29 agent，只读）
│   ├── roles/                   # V3 5 Role（analyst/modeler/experimenter/critic/writer）
│   ├── runtime/                 # 运行时（Artifact Registry + Evidence Graph + Workflow DAG）
│   ├── schemas/                 # JSON Schema
│   ├── skills/                  # 项目技能
│   │   ├── critics/             # 4 个 critic skill
│   │   └── syslab/              # 10 个 MWORKS Syslab 技能包（从 .claude 迁入）
│   ├── templates/               # 模板
│   ├── tools/                   # CLI 工具（state.py/orchestrator.py/gate.py/validate.py 等）
│   ├── validators/              # 验证器
│   └── workflows/               # 工作流定义
├── adapters/                    # 适配器
├── docs/                        # 文档
│   ├── architecture/            # 架构文档（含 V3_ARCHITECTURE_PLAN.md，从 .opencode 迁入）
│   ├── METRICS.md
│   └── STATUS.md
├── examples/
│   └── problems/                # 真实赛题题面（5 道，已验证 SHA256）
├── projects/                    # 用户运行实例
│   ├── p151-2024a/             # P15.1 2024_A 项目（含 B0-R2 synthetic 半成品论文）
│   └── rcs1/                    # RC-S1 smoke 项目
├── research/                    # 研究实验层
│   ├── REPOSITORY_AUDIT/       # 审计报告（10 份 + STRUCTURE_NAMING_PROPOSAL.md）
│   ├── P13-3D/                  # P13 系列实验（CLOSED，negative but informative）
│   ├── P14/                     # P14 能力验证（PASS）
│   ├── P15/                     # P15 Competition Model Construction Program
│   │   ├── measurement_recovery/  # 测量恢复（execution_gate.py, register_external_artifact.py 等）
│   │   ├── capability/            # 能力本体（CAPABILITY_MAP, FAILURE_TAXONOMY, RUBRIC）
│   │   ├── model_representation/  # Model IR 规范（最高优先级交付物）
│   │   ├── benchmark/             # Benchmark（problem_cards/ + manifests/）
│   │   └── reports/               # 报告（MEASUREMENT_RECOVERY_REPORT, CAPABILITY_VALIDATION_ROADMAP）
│   └── RC-SMOKE/                # RC-S1 smoke 实验
├── tests/                       # 测试
│   ├── e2e/                     # 端到端测试（test_pipeline.py → 指向新 fixture）
│   ├── integration/             # 集成测试
│   ├── unit/                    # 单元测试
│   └── fixtures/                # 测试 fixture
│       └── sample_incomplete_project/  # 从 archives 迁入的不完整项目样例
└── HANDOFF.md                   # 本文档
```

---

## 四、P15 路线图（已更名重排）

**P15 = Competition Model Construction Program**（不再是"Competition Modeling Capability Program"）

| 阶段 | 重点 | 状态 |
|---|---|---|
| P15.0 | Modeling Ontology + Benchmark Freeze | ✅ FREEZE |
| P15.1 | Problem → Model Structure（测量恢复 + 真实题面） | ✅ 测量恢复完成，B0 数据已废弃 |
| **P15.2** | **Model Construction（整条链核心）** | ⏸ 暂停，等 Model IR 评审通过 + 尺子验收 |
| P15.3 | Formal Consistency（形式自洽） | 🔲 未开始 |
| P15.4 | Computational Solving（计算求解） | 🔲 未开始 |
| P15.5 | Validation（验证） | 🔲 未开始 |
| P15.6 | Model → Paper Transmission | 🔲 未开始 |
| P15.7 | Competition Model Construction Benchmark | 🔲 未开始 |

**关键决策**：P15.2 不是取消，而是延后到"尺子验收通过"之后。避免再出现"跑了实验、出了漂亮数字、最后发现实验根本没测到 Agent"的情况。

---

## 五、待办事项（按优先级）

### P0 — 立即（测量验收）

1. **用户评审 Model IR 规范**（`research/P15/model_representation/MODEL_IR_SPEC.md` + `model_ir.schema.json` + `example_2024_A.json`）——这是最高优先级交付物，决定可视化/标准化/能力评测/科研迁移四件事能否统一。
2. **external_artifact_manifest payload 对齐 Model IR schema**（6b 最终定型）——当前 external_artifact_manifest 的 payload schema 需要与 model_ir.schema.json 对齐。
3. **6c Real B0-R3**：由**外部 Agent（Doubao）作为执行体**真正做 2024_A"板凳龙"——按 SKILL/role 指令逐节点真实读题、分解子问题、建模、求解、验证，通过 `register_external_artifact.py` 提交真实 artifact，获得第一个真实可信 baseline。run record 里 executor_type=external_agent、agent_identity 如实记录。

### P1 — 近期（结构债务）

4. **core/tools/ 双版本并行处置**（最大结构债务）：35 个 V3 canonical + 37 个 V2 平行实现零导入方。需用户拍板：是删除 V2 平行实现、还是合并、还是标记 deprecated。
5. **core/knowledge/bench/ 迁出 core**（136 文件 benchmark 语料驻留 runtime，违反"Benchmark 属 research"原则）。需验证接口兼容性后迁移到 `research/P15/benchmark/`。
6. **core/evaluation/ 空壳确认**（3 个 `__init__.py`，零导入）——候选 DELETE，需确认无隐藏依赖。
7. **pyproject.toml description 更新**：当前描述可能仍为 V2 旧定位，需更新为 LLM-free Harness + Model Construction 新定位。
8. **projects/p151-2024a 和 rcs1 重复 fixture 处置**：7 个 state 文件大小完全相同，均停留在 init 阶段。需判断是保留为 smoke fixture 还是清理。

### P2 — 中期（能力建设）

9. **L1 Problem Understanding evaluator**（C2 子问题分解可测量——当前完全无测量但正是 2024_A B0 首要根因）
10. **L2 Model Construction evaluator**（8 deterministic + 5 semantic checks，已在 MODEL_CONSTRUCTION_RUBRIC.md 设计，需实现）
11. **Adversarial Modeling Benchmark**（wrong-objective / missing-constraint / wrong-unit / method-name-trap 等）
12. **Human baseline 建立**（Agent vs Human solution 同 rubric 比较，而非 Agent vs answer key）

### P3 — 长期（科研迁移）

13. **Research Profile 设计**：同一套 Model IR + Model Graph + Evidence Model + Harness 迁移到科研论文中的具体数学建模问题
14. **Model Diff 工具实现**（两个外部 Agent 解同一题的结构化对比）
15. **Modeling Trace replay 工具**（建模过程的时序与版本记录，支持 replay）

---

## 六、已知问题与注意事项

### 6.1 validate.py 的 4 个失败

`projects/p151-2024a/paper/main.tex` 是 B0-R2 synthetic 运行产生的半成品论文（63 字、1 图、1 表、2 公式），被 validate.py 实际校验到内容不达标。这**不是回归**，是 synthetic 产物的预期表现。处理方式：
- 选项 A：给 p151-2024a 标记 executor_type=synthetic，让 validate.py 跳过 synthetic 项目的论文内容校验
- 选项 B：删除 p151-2024a 的半成品 paper/，让 validate.py 回到"无活跃论文→跳过"状态
- 选项 C：保留作为已知不达标样例，在 validate.py 输出中明确标注

### 6.2 旧 B0 数据已废弃

`research/P15/reports/P15.1-2024A-B0.md` 中的 UNRESOLVED / 20% / wrong family 三个观测值**全部无效**（输入错误 + 未真实执行 + evaluator 放过空壳）。不得继续用于任何能力结论。新的 baseline 必须等 6c Real B0-R3 完成。

### 6.3 example_external_manifest.json 的小瑕疵

`research/P15/measurement_recovery/example_external_manifest.json` 的 payload 用了 TOPSIS 但 input_sha256 是板凳龙（运动学），存在模型族不匹配。应改为运动学/几何建模示例。

### 6.4 mock_llm_executor.py 命名

`research/P15/measurement_recovery/mock_llm_executor.py`（1151 行）文件名含 "llm" 但实为纯确定性合成执行器，零网络/LLM 调用。在 LLM-free harness 中建议改名为 `synthetic_executor.py` 以名实相符。

### 6.5 CAPABILITY_VALIDATION_ROADMAP.md 旧措辞

核心结论里仍有一句旧措辞"瓶颈是接入真实 LLM 执行"，应改为"由外部 Agent 通过 6b 接口执行"。

### 6.6 论文规范版本

- 2026 修订稿：正文 ≤30 页硬上限
- 2023/2024 版："尽量 20 页内"软目标
- 官方评阅标准：假设合理性 / 建模创造性 / 结果正确性 / 表述清晰性（四项，无论文长度要求）
- 两版本已厘清，`research/P15/benchmark/manifests/input_manifest.json` 中有记录

### 6.7 OrganizerAgent 状态

`o_0001tZGvuba` 已完成任务并进入 idle-resumable standby。对话历史、VM workspace、产物全部保留。如果后续任务与本次审计/测量恢复/Model IR 相关，**优先唤醒该 Organizer 继续**（send_message），不要新建。

---

## 七、如何继续（操作手册）

### 7.1 常用命令

```powershell
# 状态查看
py -3.12 core/tools/state.py <项目> status
py -3.12 core/tools/orchestrator.py <项目>          # DAG 干跑
py -3.12 core/tools/orchestrator.py <项目> --execute # 实际执行（synthetic/dry_run）

# 非回归验证（任何修改后必跑）
py -3.12 -m pytest tests -q                           # 781 passed / 11 skipped 基线
py -3.12 core/tools/catalog_check.py --check          # v3 双视图三方一致
py -3.12 core/tools/validate.py                        # 项目级校验

# 外部 Agent 产物登记（6c Real B0-R3 用）
py -3.12 research/P15/measurement_recovery/register_external_artifact.py \
  --project <项目> --manifest <manifest.json> --input-sha256 <hash> --dry-run

# 执行真实性门禁
py -3.12 research/P15/measurement_recovery/execution_gate.py --project <项目>

# Model IR schema 校验
py -3.12 -c "import json; from jsonschema import validate; \
  schema=json.load(open('research/P15/model_representation/model_ir.schema.json')); \
  instance=json.load(open('research/P15/model_representation/example_2024_A.json')); \
  validate(instance, schema); print('Model IR schema PASS')"
```

### 7.2 唤醒 Organizer 继续

```python
# 如果后续任务与审计/测量/Model IR 相关，优先唤醒 o_0001tZGvuba
send_message(
    target="agent_id",
    target_agent="o_0001tZGvuba",
    message="<你的后续指令>"
)
```

### 7.3 修改纪律

1. **先读状态**：`state.py status` 看当前进度
2. **research 优先**：所有实验性工作进 `research/`，不要直接改 core
3. **core 修改**：必须有真实 failure mode 驱动 → minimal patch → non-regression
4. **git mv 保历史**：目录/文件移动用 `git mv`，不要用文件系统裸 mv
5. **不改 .gitignore**：任何 agent 不得修改版本控制元数据
6. **不删 research evidence**：P13/P14/P15 实验证据具有科研价值
7. **每批修改后必跑非回归**：pytest + catalog_check + validate

### 7.4 赛题真实性验证

```powershell
# 验证题面 SHA256 与 manifest 一致
py -3.12 -c "
import hashlib, json, pathlib
manifest = json.load(open('research/P15/benchmark/manifests/input_manifest.json'))
for prob in manifest['problems']:
    p = pathlib.Path(prob['local_path'])
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    status = 'MATCH' if h == prob['sha256'] else 'MISMATCH'
    print(f\"{prob['id']}: {status} ({h[:16]}...)\")
"
```

---

## 八、四个最终问题（当前答案）

1. **这个仓库现在究竟是什么？**
   以 Harness（tools+skills+workflow+verification/evidence）为核心的数学建模过程结构化/标准化/可视化/可验证基础设施。v3.1.0 内核冻结且健康，测量层已校准（输入真实性恢复 + execution gate + 空壳过滤），Model IR 规范已交付待评审。

2. **它到底测量什么？**
   设计目标：Model Construction 全链路（Problem Understanding → Model Construction → Formal Consistency → Solving → Validation → Evidence → Claim Support → Communication）。实际：11 项能力已定义，25 个 Failure Mode 可测量，L1-L4 评分细则已设计。但当前只有 synthetic 自检数据，**尚无任何真实 external_agent baseline**（旧 B0 已废弃）。

3. **下一步如何证明它真的越来越会数学建模？**
   先评审 Model IR → 对齐 external_manifest payload → 6c Real B0-R3（外部 Agent 真实做 2024_A，通过 register_external_artifact.py 提交）→ 获得第一个真实可信 baseline → 基于真实 failure mode 做 targeted intervention → cross-family validation → generalization test。每步都有 deterministic 测量，不接受 LLM 自评分。

4. **哪些能力可以迁移到科研数学建模？**
   7 项 Capability Core 中 5 项完全通用（Model Construction / Formal Consistency / Solving / Validation / Evidence），2 项需解耦比赛特有部分（Problem Alignment 解耦子问题编号，Communication 解耦论文页数格式）。Evidence 是 V3 相对 V2 的关键差异化能力。Model IR 设计为 domain-independent，同一套 IR 能承载开放科研问题。

---

## 九、关键产物索引

### 最高优先级（待评审）
- `research/P15/model_representation/MODEL_IR_SPEC.md` — Model IR 规范
- `research/P15/model_representation/model_ir.schema.json` — JSON Schema
- `research/P15/model_representation/example_2024_A.json` — 板凳龙完整实例

### 测量恢复
- `research/P15/measurement_recovery/execution_gate.py` — 执行真实性门禁
- `research/P15/measurement_recovery/register_external_artifact.py` — 外部 Agent 登记入口
- `research/P15/measurement_recovery/external_artifact_manifest.schema.json` — 准入契约 schema
- `research/P15/reports/MEASUREMENT_RECOVERY_REPORT.md` — 测量恢复报告
- `research/P15/reports/CAPABILITY_VALIDATION_ROADMAP.md` — 能力验证路线图

### 能力本体
- `research/P15/capability/CAPABILITY_MAP.md` — 11 项能力地图
- `research/P15/capability/FAILURE_TAXONOMY.md` — 25 个可测量 FM
- `research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md` — L1-L4 评分细则

### Benchmark
- `research/P15/benchmark/problem_cards/` — 5 张 Problem Card
- `research/P15/benchmark/manifests/input_manifest.json` — 5 题 SHA256 + 来源

### 审计
- `research/REPOSITORY_AUDIT/EXECUTIVE_SUMMARY.md` — 执行摘要（12 问）
- `research/REPOSITORY_AUDIT/08_RECOMMENDED_TARGET_ARCHITECTURE.md` — 目标架构
- `research/REPOSITORY_AUDIT/STRUCTURE_NAMING_PROPOSAL.md` — 结构命名方案

### 核心修复
- `examples/problems/cumcm2024A.txt` — 已修复为真实板凳龙题面
- `core/tools/evaluation/e2e_metrics.py` — 4 个 bug 修复（空壳过滤/方法族/结构校验/KeyError）
- `core/skills/syslab/` — 从 .claude 迁入的 10 个 Syslab 技能包
- `tests/fixtures/sample_incomplete_project/` — 从 archives 迁入的测试 fixture

---

**交接完毕。下一个 Agent 请从第五节"待办事项"的 P0 开始，优先评审 Model IR 规范，然后推进 6c Real B0-R3。任何疑问可唤醒 Organizer o_0001tZGvuba 继续上下文。**
