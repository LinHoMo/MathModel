# 项目状态

> 更新：2026-09-09（audit Batch 6：Revision Loop 真实化）。治理见
> `docs/architecture/THREE_LAYER_ARCHITECTURE.md`，硬化总纲见
> `docs/architecture/HARDENING_PROGRAM.md`。
> **本文件是状态数字的唯一出处：所有数字来自机器命令实测并绑定 commit hash，
> 禁止人工转述其他来源的数字。**

## 当前定位

**Scientific / Mathematical Modeling Harness**：面向数学模型构建、验证与
模型—论文传输的可信 Harness。给一道赛题（或研究问题）→ Model Construction →
Model Artifact → Execution → Validation → Evidence Graph → Revision →
Research State → 论文投影。**Source of truth = Artifact Registry + Evidence
Graph + Research State；Agent / LLM 只是 Executor（GPT / Claude / DeepSeek /
MathModelAgent / 人工均可插拔，The Agent Is Not The State）。**

资产归位三层，自 2026-09-07 起**架构冻结**（不再接受架构革命）：

- **Agent Brain**（角色指令 + 知识层）——研发主战场；
- **Research Runtime**（`core/runtime/`）——冻结（System Hardening 例外经
  `HARDENING_PROGRAM.md` P0–P3 授权）；
- **Guardrails**（validators + gates + 评分链）——冻结（同受硬化计划授权）。

能力进步以基线 Δscore 度量（八项指标，`bench e2e`），不以"新增契约/测试数量"度量。
**infra 不冒充 capability**：新基础设施必须回答"它改变了哪个可测量的 Model
Construction 行为？"。

## 阶段历史

| 阶段 | 内容 | 状态 | 锚点 |
|---|---|---|---|
| V2 P0–P5 | 诚信基线 / rubric / 引用 / 图表 / 知识层 / 定位 | ✅ | `5967940`… |
| V3.1 迁移 | Artifact / Evidence Graph / DAG / Knowledge / Modeling / Writing | ✅ | `1140e96`…`4487cd8` |
| P6–P12 | Runtime Execution / Integrity / Competition Intelligence / Research Quality / Paper Intelligence / Scientific Writing / Cross-Question | ✅ | `938227c`…`0302228` |
| P13-3 | Model Construction（3C）→ Model→Paper Transmission | ✅ | `82eb4fc`/`0036338`/`efc22df` |
| Hardening P0–P6 | Architecture/Contract Freeze + State Truth + Replay + Legacy Isolation + Regression Gate + Release Candidate | ✅ | `9d98e86`…`v3.1.0（RC）` |
| P15.0/P15.1 | CUMCM Benchmark Freeze + B0 Alignment Baseline | ✅ | `8751c45`（tag `p15.0-benchmark-freeze`）/ `af1bbd5`（tag `p15.1-b0-baseline`） |
| **P15-K001** | 2×2×rep 预注册（Knowledge × Case + Sham），55 runs，盲评 + DATA FREEZE + 配对分析 | ✅ CLOSED | Δ_K=+2.14 CI[+0.00,+6.41] → **negative result**；`de15d96` |
| **P15-K002** | Model Representation Efficacy（F/S/S+V 三臂）：契约统一（schema 迁 core、register 真 jsonschema、40 文件冻结）→ 108/108 生成 → 3 evaluator 盲评（锚定澄清，κ=0.4345）→ 配对分析 | ✅ **CLOSED** | RQ1 S−F(MCQ) Δ=−4.85 CI[−7.98,−2.22] **NEGATIVE**（不进 P15.2）；SV−F(VAL) +4.81 **POSITIVE**；报告 `analysis/reports/P15-K002-REPORT.md` |
| **P1** | Model Construction Loop：Gap Audit（11 环节）→ P1 计划 v2（C1–C10）→ **VS-001 垂直切片 7/7 PASS（2024_A，M1 FAIL → M2 PASS 闭环 + Replay）** → **M3 候选竞技场（evidence-based 选型，D002 selects 边真写入）** → **M4 知识引导（BZD 试点卡 5 张 + 义务映射）** | ✅ **全部完成**（C1–C10 + M3/M4） | 报告 `analysis/P1_{VS001,M3,M4}_REPORT.md` |
| **P0-1 修复** | Fidelity Layer 接入生产 DAG（handlers 调 verify_fidelity；misaligned→FAIL；不注册 VR 防 C8 幂等复用；容器输出如实跳过；m3/m4 透传 OUTPUT_MAPPING 契约） | ✔ 完成 | `80741df` |
| **P15-K003** | Model Representation Efficacy under Executed Construction（F/S/SV 三臂，构造+执行一体化）：五 Gate 全 PASS（G1 映射 v1.2 / G2 κ=0.712 / G3 词表 / G4 exec 1.00 / G5 功效）→ FROZEN（36 文件冻结，root `94b14d4f`）→ 66/66 真实 subprocess 执行（rc=0，含 hash/provenance）→ 3 evaluator 独立盲评（66 匿名 bundle，198 评分文件 + 对拍一致）→ 配对分析（bootstrap 10000，主检验 18 blocks） | ✅ **CLOSED** | 主终点 S−F(MCQ)=+3.76 CI[+2.13,+5.44] **POSITIVE**；SV−F(VAL)=+39.92 CI[+37.24,+42.60] **POSITIVE**；L4 为唯一正效应来源（S−F +1.58, SV−F +3.59）、L2 显著负（−0.41/−0.50）→ **"验证义务+执行闭环 > 表示格式"实证**；κ=0.260（<0.6，如实披露）；报告 `analysis/reports/P15-K003-REPORT.md` |
| **audit 修复（Batch 1–6）** | 证据级全系统审计：P0×12/P1×18/P2×14 修复循环。执行真实化（EXEC 只由 substrate 写、失败真实传播、占位 claim 禁 supports）、选型证据化（无证据不选型）、契约统一（schema 迁 core + register 真 jsonschema 实例校验）、L2 数学检查、**Batch 6 Revision Loop**（机械诊断 diagnosis + 修订草案 + supersede 方向统一 + M1/M2 机械比较 accept 决策） | ✅ 全绿 | 计划 `research/audit/IMPLEMENTATION_PLAN.md`；Batch 6 提交见 git log |
| **audit Batch 7–10** | 独立复审：E2E loop reviewer **REAL 判定**（M1 FAIL=真实数值违反 0.275>1e-6、execution status 仅来自真实 subprocess、replay 真实重跑）+ TEST_TRUST_SCORE=**80/100**（无 P0 作弊，零 mock，核心集成层真实执行）+ 实验体系审计 + 终审 18 项验收（F4/H5 回填 REAL）。P2×2 已修复（supersedes 方向单一真源、死代码分支删除） | ✅ 完成 | `research/audit/batch7_e2e_review/VERDICT.md`、`batch8_test_trust/TEST_TRUST_SCORE.md`、`batch10_final/FINAL_VERDICT.md` |
| **治理三大待办** | **Candidate Arena 固化 benchmark**（全池 8 题 44 候选机械选型 + 6 集成测试）→ **Knowledge-guided 正式化**（`core/runtime/modeling/knowledge_guided.py` 机械映射 BZD 5 卡 + 契约 v1.0 + 8 单测）→ **Capability Validation Δscore**（八项指标 + P1 执行级指标双口径，诚实局限声明） | ✅ 完成 | `benchmark/arena/`、`protocol/KNOWLEDGE_GUIDED_CONSTRUCTION.md`、`analysis/CAPABILITY_DELTA_REPORT.md` |

## 当前数字（机器实测，Python 3.12.10，截至 2026-09-10）

| 项 | 实测输出 | 生成命令 |
|---|---|---|
| 单元/集成/端到端测试 | **994 passed / 4 skipped / 0 failed（skip 全部分类）** | `py -3.12 -m pytest tests -q` |
| 项目级校验 | **58 通过 / 0 失败 / 0 警告** | `py -3.12 core/tools/validate.py` |
| catalog 三方一致 | **OK** | `py -3.12 core/tools/catalog_check.py --check` |
| 术语零残留 | **OK**（production 零残留，无行内豁免） | `py -3.12 core/tools/catalog_check.py --check-terminology` |
| K001 冻结校验 | **PASS（44 文件）** | `py -3.12 research/P15/scripts/k001_freeze.py --check` |
| K002 冻结校验 | **PASS（40 文件）** | `py -3.12 research/P15/scripts/k002_freeze.py --check` |
| K003 冻结校验 | **PASS（36 文件）** | `py -3.12 research/P15/scripts/k003_freeze.py --check` |

说明：

- **双真源问题档案**：历史文档出现过 228/16、574/11、751/11、774/11、855/4 多套
  测试数字与本表并存。自 Hardening P0 起，全部状态数字以本表口径为准；旧数字
  一律作废（P1 进行期间 pytest 计数随 Organizer 提交演进，以每次 commit 时实测为准）。
- K001 冻结基线于 2026-09-09 因术语治理迁移（旧字段名 →
  `allowed_modeling_structures`，5 题 gt.json，旧名详见 GOVERNANCE_REPORT §7.1）
  重冻——评分数据独立冻结于 DATA
  FREEZE（165 文件）未受影响，漂移原因记录于 `GOVERNANCE_REPORT §7.1`。
- Windows 本机 `py` 默认解释器（3.14/3.13）安装损坏，统一用 `py -3.12`。

## 下一步

```text
已完成（2026-09-10）：
  audit Batch 1–6：证据级修复循环全绿
    Batch 1  执行真实化（EXEC 只由 substrate 写 / 失败真实传播 / 占位 claim 禁 supports）
    Batch 2  选型证据化（无证据不选型 / UNSELECTED 如实推进）
    Batch 3  MODEL_IR↔Code 映射保真（implementation_ref 断裂抛错）
    Batch 4  Evidence 边级 provenance（exec_ref）+ K003 execution_writer 唯一写入 + submission_id 去可逆
    Batch 5  契约统一：schema 迁 core + register 真 jsonschema 实例校验（58 项 validate）
             + L2 Mathematical 检查（formula_checker 接线）+ validator 模块冒烟
    Batch 6  Revision Loop 真实化：机械失败诊断（diagnosis artifact + diagnosed_by 边）
             + 修订草案（不编造数值）+ supersede 方向统一（新取代旧，M1 状态 superseded）
             + M1/M2 机械比较（revision_acceptance 决策 + selects 边）
  P1（Model Construction Loop）：C1–C10 全部完成 + VS-001 7/7（2024_A，M1 FAIL→M2 PASS + Replay）
    + M3 候选竞技场（evidence-based 选型）+ M4 知识引导（BZD 试点卡 5 张）
  K002 正式实验：契约统一（40 文件冻结）→ 108/108 生成 → 3 evaluator 盲评（κ=0.4345）
    → 配对分析 → 状态机 CLOSED（RQ1 NEGATIVE，不进 P15.2）
  K003 预注册：五 Gate 全 PASS（G2 κ=0.712、G4 exec 1.00）→ FROZEN（36 文件冻结）
  audit Batch 7–10：独立复审 REAL + TEST_TRUST_SCORE 80/100（无 P0 作弊）+ P2×2 修复
    + 实验体系审计 + 终审 18 项验收 F4/H5 回填 REAL
  治理三大待办（2026-09-10）：
    ① Candidate Arena 固化 benchmark（全池 8 题 44 候选机械选型，6 集成测试）
    ② Knowledge-guided 正式化（core 机械映射模块 + BZD 5 卡 + 契约 v1.0，8 单测）
    ③ Capability Validation Δscore（八项指标 + P1 执行级指标双口径报告）

进行中（MainAgent）：
  ① K003 正式实验：66 runs → 独立盲评（3 evaluator，198 评分 + 对拍一致）→ 配对分析 → P15-K003-REPORT.md → 状态机 CLOSED ✅（已完成）
  ② 战略级终审（Organizer `o_0001kxvAFGc`）：8 审计域（A-H）+ 交叉验证 + 三轮自我反驳 → 6/7 决策文档已落盘
     （STRATEGIC_VERDICT / ARCHITECTURE_FINAL / CONSTRUCTOR_INTEGRATION_PLAN / AGENT_AUTHORITY_MODEL /
       EXPERIMENT_STRATEGY / MODEL_CONSTRUCTION_GAP；ROADMAP 待产出）→ 审计结论与 K003 一致：
       "验证义务+执行闭环是护城河，Constructor 层可替换"
  ③ 终审完成后：与 K001/K002/K003 三实验对比表、P16 决策正式落定
```

## 风险与待办

- **K002 测量局限（已证实）**：RQ1 S−F(MCQ)=−4.85 NEGATIVE 主因 **L3 层格式不对称**（S 臂结构化 JSON 暴露"无执行证据"系统性低分；F 臂自由文本可叙述性声称）。K002 为纯表示实验、产物不含真实执行——**"执行证据声明完备性"≠"真实执行能力"**；下一实验必须构造+执行一体化（执行产物进盲评包）。
- **盲评 κ 边界**：3 evaluator 校准 κ=0.4345（锚定澄清后），低 κ 维度已在敏感性 B 剔除；报告完整披露（`MODEL_CONSTRUCTION_RUBRIC_ANCHOR_K002.md`）。
- **P1 闭环铁律**：`execution_status=success` 不得推出 `model_status=correct`；
  `ExecutionResult.status` 只能来自真实执行状态，禁止 handler 默认生成。
- **E02 残留事件档案**：盲评收尾期预检残留评估者文件被异步写回 scores/（7 份，已恢复+终止污染源）；正式报告数字以 git HEAD 评分版为准（确定性复现）。
- CUMCM 22 份 rubric 中 13 份 `reference_results` 为空——不凭记忆伪造 GT。
- 完整 CUMCM 题面语料未导入（现有仅题名索引 + 已 verified 的 K001/K002 题面）。
