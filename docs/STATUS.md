# 项目状态

> 更新：2026-09-10（V2 彻底清除：历史文档/旧研究/LaTeX 链/四手残留删除，
> 全仓采用 V3 新定位）。架构见 `docs/architecture/V3.1_ARCHITECTURE.md`。
> **本文件是状态数字的唯一出处：所有数字来自机器命令实测并绑定 commit hash，
> 禁止人工转述其他来源的数字。**

## 当前定位

**Scientific / Mathematical Modeling Harness**：面向数学模型构建与验证的
可信 Harness。给一道赛题（或研究问题）→ Model Construction → Model Artifact →
Execution → Validation → Evidence Graph → Revision → Research State →
**MODEL_IR（JSON）+ 模型描述文档（MD/Mermaid）**。不包含论文生成（LaTeX/PDF）、
不向后兼容 V2。**Source of truth = Artifact Registry + Evidence Graph +
Research State；Agent / LLM 只是 Executor（GPT / Claude / DeepSeek /
MathModelAgent / 人工均可插拔，The Agent Is Not The State）。**

资产归位三层，自 2026-09-07 起**架构冻结**（不再接受架构革命）：

- **Harness 引擎**（`core/`：runtime / roles / workflows / validators / schemas）——唯一可复用资产；
- **Research Runtime**（`core/runtime/`）——冻结（架构冻结，治理例外经
  `docs/architecture/RUNTIME_CONTRACTS.md` 授权）；
- **Guardrails**（validators + gates）——冻结（同受契约授权）。

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
| **P0-3 完整收口** | ExecutionResult 来源鉴别 execution_token（HMAC 签名/校验，进程级 secret）：LocalPythonAdapter 真实执行后签发，registry.create 强制校验（success EXEC 必须带有效 token 或 legacy_unverified 声明）；Agent/Handler 无 secret 无法伪造 EXEC | ✔ 完成 | `f8f21f1` |
| **P1-1** | Constructor Adapter Protocol：ConstructionBundle（MODEL_IR+code+output_mapping+validation_spec+revision_of）+ ConstructorAdapter ABC + capability C0-C5 + ConstructorRegistry/apply_bundle（外部 Constructor 统一接入） | ✔ 完成
| **P2-1** | L6 数值正确性机械判定层：`validate_against_gt`（feasibility/objective_sane/output_nonnegative/output_range，无断言 unverifiable、不可判定 skipped）+ 8/8 题 `gt.json#l6_assertions` v1.0（数学必然 + 题面客观边界）+ fidelity 升级 F6 约束数值满足 / F7 目标值有限 + arena 接入 L6（全池 44 候选零误伤，报告 l6 列与选型排序） | ✔ 完成 | 见 git log |
| **P1-2** | Knowledge Guided Construction 接入生产路径：_register_mir 应用 apply_knowledge_obligations（默认关闭，source_card 溯源，不覆盖声明）；义务对齐 MODEL_IR 契约 | ✔ 完成 | 见 git log |
| **P1-3** | Model Comparison 接入生产路径：revision 链自动 compare_models → decision artifact + compared_with/based_on 边 | ✔ 完成 | 见 git log |
| **P1-4** | 硬编码经验常数 Provenance：confidence 全标注 advisory 不参与判定；integrity_gate 政策阈值声明来源 | ✔ 完成 | 见 git log |
| **P0-4 修复** | 清理 Dead Code：删除 `_maybe_execute_experiment`（无调用者）/ engine 重复 unblock / comparison 无效循环；codegen 独立路径定位为研究工具链 （K003/K002/arena 消费） | ✔ 完成 | `6466490` |
| **P0-4 补完** | 零执行/零验证 ≠ PASS（blocked）：do_model_execution 无活跃候选/全部无代码 → blocked；do_model_validation 无 EXEC 或 EXEC 无验证规格 → blocked（区分"没做"与"做了且通过"）；**engine BLOCKED 依赖传播**（上游阻塞→下游级联 blocked 不假装完成，run() 状态可见不静默吞 pending）+ unblock 级联恢复；test_05 断言升级（无 decision 伪造） | ✔ 完成 | P2-1 基建 commit |
| **P0-5** | mark_validated 调用方白名单门禁：仅 runtime 验证管线（validators.py/handlers.py）可标记 validated（调用栈真实路径判定，不信任显式 caller）；run_record 必填（run_id/hash 可追溯）；critic SKILL.md 改写为提交 review report 由 runtime 登记（The Agent Is Not The State）；验收 8/8 | ✔ 完成 | 见 git log |
| **P2-3（检索命中率）** | K001 negative 归因：8 题（K003 同题集）特征→recommend(top_k=10) vs ground-truth 卡；修复前 hit@3=5/8=62.5% → 修复后 7/8=87.5%（ols 补 regression / kmeans 补 small 小样本）；2024_A 未命中如实记录 | ✔ 完成 | `analysis/reports/P2-3-RETRIEVAL-HITRATE.md` |
| **P2-2** | Fidelity Measurement Study：44 结构化 runs 分布双峰（36 aligned 0.93 / 8 misaligned 0.2 全在 2022_C+2024_A）；根因=中文变量名 vs 英文 key 的 output_mapping 词汇错位（exec 全 success，非数学错误，与 RQ5 同源）；fidelity vs 盲评 L2 无正相关（Pearson .051/Spearman .254）、L2.6 负相关 -.479 → fidelity 进机械主指标 + output_mapping 契约前置 | ✔ 完成 | 报告 `analysis/reports/P2-2-FIDELITY-STUDY.md` |
| **P2-1 基建** | Constructor-Independent Benchmark（K004）：预注册 v1.0（4 Constructor×2 RT×8 题×2 seeds=64 runs，MCQ_primary+VAL_mech 双主终点，5 判定形态，Measurement Gate 前置）；Reference Constructor（LLM-free C3，M1_DICT 合规基底 + 模板代码对齐变量，真实执行闭环可跑）；MathModelAgent Adapter 契约（未装配抛 ConstructorError）；验收 5/5 | ✔ 完成（基建） | 64 runs 生成+盲评+统计为 P2-1b |
| **P0-3 修复** | 启用 Engine Validator Hook（方案 B）：evidence_consistency_validator——PASS 节点 outputs.artifacts/evidence 必须真实存在于 registry（handler 不能自己说完成）；WorkflowEngine 与 WaveExecutor 同注全 NODE_TYPES | ✔ 完成 | `validators.py` |
| **P0-2 修复** | Failure Diagnosis 接入生产 DAG（validation FAIL 无存活候选 → diagnose_failure 注册 diagnosis + diagnosed_by 边 + build_revision_draft 生成 M2 草案供外部 Constructor；finalize_revision 去重防双 DIAG） | ✔ 完成 | `311a863` |
| **P0-1 修复** | Fidelity Layer 接入生产 DAG（handlers 调 verify_fidelity；misaligned→FAIL；不注册 VR 防 C8 幂等复用；容器输出如实跳过；m3/m4 透传 OUTPUT_MAPPING 契约） | ✔ 完成 | `80741df` |
| **P15-K003** | Model Representation Efficacy under Executed Construction（F/S/SV 三臂，构造+执行一体化）：五 Gate 全 PASS（G1 映射 v1.2 / G2 κ=0.712 / G3 词表 / G4 exec 1.00 / G5 功效）→ FROZEN（36 文件冻结，root `94b14d4f`）→ 66/66 真实 subprocess 执行（rc=0，含 hash/provenance）→ 3 evaluator 独立盲评（66 匿名 bundle，198 评分文件 + 对拍一致）→ 配对分析（bootstrap 10000，主检验 18 blocks） | ✅ **CLOSED** | 主终点 S−F(MCQ)=+3.76 CI[+2.13,+5.44] **POSITIVE**；SV−F(VAL)=+39.92 CI[+37.24,+42.60] **POSITIVE**；L4 为唯一正效应来源（S−F +1.58, SV−F +3.59）、L2 显著负（−0.41/−0.50）→ **"验证义务+执行闭环 > 表示格式"实证**；κ=0.260（<0.6，如实披露）；报告 `analysis/reports/P15-K003-REPORT.md` |
| **audit 修复（Batch 1–6）** | 证据级全系统审计：P0×12/P1×18/P2×14 修复循环。执行真实化（EXEC 只由 substrate 写、失败真实传播、占位 claim 禁 supports）、选型证据化（无证据不选型）、契约统一（schema 迁 core + register 真 jsonschema 实例校验）、L2 数学检查、**Batch 6 Revision Loop**（机械诊断 diagnosis + 修订草案 + supersede 方向统一 + M1/M2 机械比较 accept 决策） | ✅ 全绿 | 计划 `research/audit/IMPLEMENTATION_PLAN.md`；Batch 6 提交见 git log |
| **audit Batch 7–10** | 独立复审：E2E loop reviewer **REAL 判定**（M1 FAIL=真实数值违反 0.275>1e-6、execution status 仅来自真实 subprocess、replay 真实重跑）+ TEST_TRUST_SCORE=**80/100**（无 P0 作弊，零 mock，核心集成层真实执行）+ 实验体系审计 + 终审 18 项验收（F4/H5 回填 REAL）。P2×2 已修复（supersedes 方向单一真源、死代码分支删除） | ✅ 完成 | `research/audit/batch7_e2e_review/VERDICT.md`、`batch8_test_trust/TEST_TRUST_SCORE.md`、`batch10_final/FINAL_VERDICT.md` |
| **治理三大待办** | **Candidate Arena 固化 benchmark**（全池 8 题 44 候选机械选型 + 6 集成测试）→ **Knowledge-guided 正式化**（`core/runtime/modeling/knowledge_guided.py` 机械映射 BZD 5 卡 + 契约 v1.0 + 8 单测）→ **Capability Validation Δscore**（八项指标 + P1 执行级指标双口径，诚实局限声明） | ✅ 完成 | `benchmark/arena/`、`protocol/KNOWLEDGE_GUIDED_CONSTRUCTION.md`、`analysis/CAPABILITY_DELTA_REPORT.md` |
| **P2-4 修复** | V2 兼容层路径真迁移：`orchestrator.py _skill_path` → `core/legacy/hands/<Hand>/agents/<agent>/SKILL.md`（四手 29 agent 全解析）+ `state.py` 提示同步 + `tests/unit/test_legacy_paths.py`（2 用例） | ✔ 完成 | 本轮 |
| **P3-2（K004）** | L5 Revision 度量实验：预注册（18 单元 = 6 变体 × 3 种子，M/M/c 模板 + 错误注入 service_rate→ρ>1→L6 FAIL，修订→PASS）+ 真实 subprocess runner + 配对差分 bootstrap CI。**Δ_L6=+1.0000 CI[+1.0000,+1.0000] H1 SUPPORTED**；M1 失败真实性 18/18、M2 通过 18/18、Replay 18/18、修正轮数均值 1.0；报告 `experiments/P15-K004/K004_REPORT.md`（范围如实：单题模板、测 Revision 执行/验证层） | ✅ 完成 | 本轮 |
| **P2-2/P3-3** | 外部 Constructor 适配器：`core/runtime/constructors/adapters/`——`MathModelAgentAdapter`（MMA 产物目录加载，未配置抛 ConstructorNotConfigured 禁伪造）、`PiAdapter`（同目录模式）、`ReferenceConstructor`（内置最小参考）；`tests/unit/test_constructor_adapters.py` 7 用例；边界：Worker/External Solver/Baseline，不触碰 Runtime 信任核心 | ✅ 完成 | 本轮 |
| **P3-1（K005）** | Constructor×Runtime 2×2 析因 benchmark：预注册协议（C1 裸 Doubao × C2 MMA × R0/R1，6 题 × 5 rep = 120 runs，配对差分 + bootstrap CI + 析因分解）+ runner 框架（`benchmark/constructor_independent/runner.py`，消费 adapter 产物目录）。**正式 runs 数据收集 BLOCKED（如实）**——需外部 Constructor 会话逐题生成，禁止伪造/回填 | ✅ 框架+预注册（数据待外部收集） | 本轮 |
| **P3-4** | BZD 知识导入：试点 5 卡（M4 已落地，Prior 知识 + source_type/confidence/status 标注）；经验常数禁令验证（core/ 零引用 6.81% 等）。**目录重组：评估后暂缓**（顶层大迁移 import 回归风险 > 收益，改渐进式：constructors/adapters 已落地、dead code 已清） | ✅ 知识部分（重组暂缓） | 本轮 |

## 当前数字（机器实测，Python 3.12.10，截至 2026-09-10）

| 项 | 实测输出 | 生成命令 |
|---|---|---|
| 单元/集成/端到端测试 | **610 passed / 0 skipped / 0 failed** | `py -3.12 -m pytest tests -q` |
| 项目级校验 | **45 通过 / 0 失败 / 0 警告** | `py -3.12 core/tools/validate.py` |
| catalog 三方一致 | **OK** | `py -3.12 core/tools/catalog_check.py --check` |
| 术语零残留 | **OK**（production 零残留，无行内豁免） | `py -3.12 core/tools/catalog_check.py --check-terminology` |
| K001 冻结校验 | **PASS（44 文件）** | `py -3.12 research/P15/scripts/k001_freeze.py --check` |
| K002 冻结校验 | **PASS（40 文件）** | `py -3.12 research/P15/scripts/k002_freeze.py --check` |
| K003 冻结校验 | **PASS（36 文件，revision v1.1：8 题 gt.json 新增 `l6_assertions` 键，P2-1 治理变更，新 root `347f4534`；已评分数据不受影响）** | `py -3.12 research/P15/scripts/k003_freeze.py --check` |

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
  P1（Model Construction Loop）：C1–C10 全部完成 + VS-001 7/7 + M3/M4
  K002 正式实验：CLOSED（RQ1 NEGATIVE）；K003 正式实验：CLOSED（POSITIVE）
  audit Batch 7–10：独立复审 REAL + TEST_TRUST_SCORE 80/100
  治理三大待办：Candidate Arena 固化 / Knowledge-guided 正式化 / Capability Validation Δscore
  ROADMAP P0–P3 全部项（2026-09-10 收口）：
    P0-1~P0-6 ✅（注入通道/validators 挂载/EXEC 来源鉴别/零执行≠PASS/mark_validated 门禁/K003 直写删除）
    P1-1~P1-5 ✅（fidelity 门/Revision 闭环/Constructor Protocol/MODEL_IR 契约/死代码清理）
    P2-1 ✅ L6 数值正确性机械判定层（validate_against_gt + 8 题 l6_assertions + F6/F7 + arena 接入）
    P2-2 ✅ MMA/Pi/Reference 适配器；P2-3 ✅ 检索命中率 87.5%；P2-4 ✅ V2 兼容层路径真迁移
    P3-1 ✅ K005 2×2 析因 benchmark 框架+预注册（120 runs 设计；正式数据收集 BLOCKED 待外部 Constructor）
    P3-2 ✅ K004 L5 Revision 度量（Δ_L6=+1.0 CI[1,1] H1 SUPPORTED）
    P3-3 ✅ Pi Adapter；P3-3b ✅ paper chain 统一（并行会话）；P3-4 ✅ BZD 知识（目录重组渐进式暂缓）

进行中（MainAgent）：无 —— ROADMAP 全项已处理完毕
待办：
  ① K005 正式 120 runs 数据收集（需外部 Constructor 会话：裸 Doubao + MathModelAgent 逐题生成，禁止伪造）
  ② P3-4 目录顶层重组（渐进式，待未来冻结点）
  ③ 终审完成后的三实验对比表与 P16 决策正式落定
```

## 风险与待办

- **K002 测量局限（已证实）**：RQ1 S−F(MCQ)=−4.85 NEGATIVE 主因 **L3 层格式不对称**（S 臂结构化 JSON 暴露"无执行证据"系统性低分；F 臂自由文本可叙述性声称）。K002 为纯表示实验、产物不含真实执行——**"执行证据声明完备性"≠"真实执行能力"**；下一实验必须构造+执行一体化（执行产物进盲评包）。
- **盲评 κ 边界**：3 evaluator 校准 κ=0.4345（锚定澄清后），低 κ 维度已在敏感性 B 剔除；报告完整披露（`MODEL_CONSTRUCTION_RUBRIC_ANCHOR_K002.md`）。
- **P1 闭环铁律**：`execution_status=success` 不得推出 `model_status=correct`；
  `ExecutionResult.status` 只能来自真实执行状态，禁止 handler 默认生成。
- **E02 残留事件档案**：盲评收尾期预检残留评估者文件被异步写回 scores/（7 份，已恢复+终止污染源）；正式报告数字以 git HEAD 评分版为准（确定性复现）。
- CUMCM 22 份 rubric 中 13 份 `reference_results` 为空——不凭记忆伪造 GT。
- 完整 CUMCM 题面语料未导入（现有仅题名索引 + 已 verified 的 K001/K002 题面）。
