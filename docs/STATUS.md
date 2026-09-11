# 项目状态

> 更新：2026-09-11（标准层 v1.2：**used_in 显式引用契约**（46 参数全显式化）+
> **双级门禁**（显式破损硬 FAIL / 启发式未命中降 WARN）+ G4 evidence_refs 对象形态 +
> **门禁金标准**（46 参数真值，FP=FN=0）；判据升 v1.2，失败卡 22→23。
> 同日早些（v1.1）：G4 证据义务矩阵（EV1–EV5）/ G5 复杂度预算 /
> R4 创新声明契约 / R3 结构距离工具接入 validate.py 与 cli/innovation_metrics.py；
> 三实例合规声明并反向验收；修复 G5 真实误报（2026b P13/P14 字符串值+浮点格式）并
> 固化为回归测试；判据文档升 v1.1，审查文档登记 §9 遗留优化项。前序基线见下：
> 2026-09-10（V2 彻底清除：历史文档/旧研究/LaTeX 链/四手残留删除，
> 全仓采用 V3 新定位；**P15-K002 → P1 全程闭环 → 实例反馈审计**：ADR-0008
> 问题理解层 + 实例状态契约门禁 + 投影写出唯一入口；cumcm2024a/2026a/2026b
> 三实例可读、可对账、可度量，分解覆盖 20.0→100.0）。架构见
> `docs/architecture/V3.1_ARCHITECTURE.md`。
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

- **Harness 引擎**（`src/modeling_harness/`：runtime / roles / workflows / validators / schemas）——唯一可复用资产；
- **Research Runtime**（`src/modeling_harness/runtime/`）——冻结（架构冻结，治理例外经
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
| 标准层 v1.1（T-THEORY-02~06） | G4 证据义务矩阵（EV1–EV5）/ G5 复杂度预算 / R4 创新声明契约 / R3 结构距离工具；三实例合规声明 + 反向验收；修复 G5 真实误报并固化回归 | ✅ | 见 TASKS.md |
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
| **治理三大待办** | **Candidate Arena 固化 benchmark**（全池 8 题 44 候选机械选型 + 6 集成测试）→ **Knowledge-guided 正式化**（`src/modeling_harness/runtime/modeling/knowledge_guided.py` 机械映射 BZD 5 卡 + 契约 v1.0 + 8 单测）→ **Capability Validation Δscore**（八项指标 + P1 执行级指标双口径，诚实局限声明） | ✅ 完成 | `benchmark/arena/`、`protocol/KNOWLEDGE_GUIDED_CONSTRUCTION.md`、`analysis/CAPABILITY_DELTA_REPORT.md` |
| **P2-4 修复** | V2 兼容层路径真迁移：`orchestrator.py _skill_path` → `src/modeling_harness/legacy/hands/<Hand>/agents/<agent>/SKILL.md`（四手 29 agent 全解析）+ `state.py` 提示同步 + `tests/unit/test_legacy_paths.py`（2 用例） | ✔ 完成 | 本轮 |
| **P3-2（K004）** | L5 Revision 度量实验：预注册（18 单元 = 6 变体 × 3 种子，M/M/c 模板 + 错误注入 service_rate→ρ>1→L6 FAIL，修订→PASS）+ 真实 subprocess runner + 配对差分 bootstrap CI。**Δ_L6=+1.0000 CI[+1.0000,+1.0000] H1 SUPPORTED**；M1 失败真实性 18/18、M2 通过 18/18、Replay 18/18、修正轮数均值 1.0；报告 `experiments/P15-K004/K004_REPORT.md`（范围如实：单题模板、测 Revision 执行/验证层） | ✅ 完成 | 本轮 |
| **P2-2/P3-3** | 外部 Constructor 适配器：`src/modeling_harness/adapters/`——`MathModelAgentAdapter`（MMA 产物目录加载，未配置抛 ConstructorNotConfigured 禁伪造）、`PiAdapter`（同目录模式）、`ReferenceConstructor`（内置最小参考）；`tests/unit/test_constructor_adapters.py` 7 用例；边界：Worker/External Solver/Baseline，不触碰 Runtime 信任核心 | ✅ 完成 | 本轮 |
| **P3-1（K005）** | Constructor×Runtime 2×2 析因 benchmark：预注册协议（C1 裸 Doubao × C2 MMA × R0/R1，6 题 × 5 rep = 120 runs，配对差分 + bootstrap CI + 析因分解）+ runner 框架（`benchmark/constructor_independent/runner.py`，消费 adapter 产物目录）。**正式 runs 数据收集 BLOCKED（如实）**——需外部 Constructor 会话逐题生成，禁止伪造/回填 | ✅ 框架+预注册（数据待外部收集） | 本轮 |
| **P3-4** | BZD 知识导入：试点 5 卡（M4 已落地，Prior 知识 + source_type/confidence/status 标注）；经验常数禁令验证（src/modeling_harness/ 零引用 6.81% 等）。**目录重组：2026-09-10 执行完成**——`domains/`（Canonical Domain Model 由 runtime/domain 上提）与 `adapters/`（外部 Constructor 适配器由 constructors/adapters 上提）落地顶层；`runtime/execution/adapters/`（执行适配器，不同语义）保留原址；见 ADR-0006 | ✅ 完成 | 本轮 |
| **v3.2.2 V2 残留彻底清除** | 删除论文链工具 9 个 + validate_project.py + LaTeX 模板 27 + 竞赛 profile 9 + V2 schema 4 + syslab 技能 101 + 旧实例 8 + docs 25+6（diagrams）+ harness-compat；env 全面 V3 化（schema 六组、loader 无 profile、config 无 paper）；new_project 重写纯 V3 布局（inputs/state/artifacts/model）；知识/文档引用全部对齐 | ✅ 600 passed，validate 45/0/0，catalog OK | 本轮 |
| **2026 A/B 全问建模交付** | 用 harness 完成 CUMCM 2026 A 题（药材烘干：径向耦合传热传质 PDE + Landau 移动边界）与 B 题（干扰源交会定位 + 同心环覆盖清除）全问建模：各产出 `model_ir.json` + `model.md` + `all_results.json` + `result*.xlsx` + `state/`（registry/evidence_graph/decision_log/status）；A 题烘干时长 Q3 57.4222 h / Q4 64.7806 h（含收缩，终半径 1.2721 cm）；B 题 30 组演练清除比例 1.0000（Q3 7150.10 s / Q4 15088.79 s），覆盖漏检率全向 0.0000 / 含定向 0.00025；**反向修复 harness 4 处**（validate.py Mermaid 闭合误判、new_project.py README 内部路径泄漏、两题 README 路径泄漏）；新增知识卡 3 张 + 失败卡 5 条 + playbook 2 篇 | ✅ 600 passed，validate 45/0/0，catalog OK，术语 OK | 本轮 |
| **实例反馈闭环（ADR-0008）** | 三个交付实例可读、可对账、可度量：registry 子问题由 1/1/1 → 5/4/4（每问独立 artifact），`MH-MODEL_IR-0001` 内联 MODEL_IR 契约字段，narrative → deliverable，payload 路径全解析，状态投影由 `ProjectState.refresh_from` 派生（唯一入口，`scripts/state_projection.py`）。**前置**：ADR-0008 问题理解层（题面 → 子问题 + 类型 + 检索特征确定性派生，移除 _LEGACY 硬编码）。**新增 harness 门禁**「实例状态契约」（validate 46/0/0，覆盖扁平投影 / 非法维度值 / 退役类型 / 路径悬空）；**schema 对齐**（narrative/paper 从必填降为历史容忍维度）。**修复前后**：2024_A 分解覆盖 20.0→100.0，模型结构检查 legacy_pointer→PASS，三实例 reconcile ok=True。报告 `docs/PROJECTS_FEEDBACK_AUDIT.md`；仍如实登记未闭合项（方法结构对齐词表缺口 / 2026 真值卡缺失） | ✅ 628 passed，validate 46/0/0，catalog OK，术语 OK | 本轮 |
| **2026_A 精细适配 + harness 溯源改进** | ① 原始赛题材料（A/B 题 PDF + 附件）归位 `inputs/`；② **A 题 v1.1 数据驱动边界**：附件1 实测温湿度序列（241 行，0–14400 s 插值）替代指数趋近+阶跃近似，附件2 实测半径（145 行，2.000→1.198 cm）替代 Landau 自算，产出实测/守恒双解对照。**数值**：Q1 末表面 36.7863 °C（v1.0 44.59），Q3 烘干 57.1722 h（v1.0 57.4222，差 0.25），Q4 附件2 驱动 52.3111 h vs Landau 64.5667 h（差 12.26 h，终半径 1.200 vs 1.2721 cm）；空间/时间收敛 + 温度敏感性（参数化 T_air）实测入台账。③ **harness 溯源改进**：`check_numeric_traceability` 增加题面输入 `inputs/problem.txt` 为合法溯源目标（结果→台账、题面常数→题面），消除物理常数误报（物理常数不再压低追溯比例），附 3 单测锁定语义 | ✅ 631 passed，validate 46/0/0，catalog OK，术语 OK | 本轮 |
| **2026_B 真实模拟器协议构建** | 按《B 题附件2·模拟器通信接口说明及编程指南》构建协议忠实客户端（`SimulatorHTTP`：4 指令、`arena_id`/`position`/`measure_result`/`svd_deg`/`clear_result`，虚拟时间服务端计算）+ 规范忠实本地 Mock（含 1 s 频道切换耗时）。**关键**：真实 API 不返回信号强度 → 策略弃用强度估距，改为纯示向度交会 + 越界检测归航（失联回退最近可测点处理定向盲区）。Mock 演练各 5 组（seed 42..46）：Q3/Q4 清除比例均 1.0000（Q3 虚拟 12918.09 s / 定位清除 8269.47 s；Q4 22592.91 s / 17514.37 s）。**未接官方评测机**（GUI 登录 + 联网 + 测试窗口），如实声明 | ✅ 631 passed，validate 46/0/0，catalog OK，术语 OK | 本轮 |
| **参数来源门禁（治理加固）** | 新增 L4 门禁 `check_parameter_provenance`：声称 `problem_given` 的**数值参数**，其值必须能在 `inputs/problem.txt` 原文匹配（仅允许 ×10^k 单位换算，k∈[-9,9]）；需经 ÷2 等推导得到的值应标 `derived`。堵住输入侧诚信漏洞（把自建常数标成题面给定）。首跑即揪出 `cumcm2024a:P15`（调头空间半径 4.5 m 实为直径 9 m 的 ÷2 推导，已改标 `derived` 并补 definition）；参数 `source` 词表受控化（6 项）。附 `tests/unit/test_parameter_provenance.py` 5 单测锁定语义 | ✅ 636 passed，validate 47/0/0，catalog OK，术语 OK | 本轮 |
| **模型质量判据（标准层）+ G3 校准参数门禁** | 判据升 FROZEN（`docs/architecture/MODEL_QUALITY_CRITERIA.md`）：合格线 Gate G1 数值溯源 / G2 参数来源 / **G3 校准参数**（新增）+ 排序线 Rank R1/R2（无真值，标"不可算"不阻塞）。**G3**：`source ∉ {problem_given, derived, convention}` 的数值参数须 (a) `calibration_anchor_ref` 指向 `calibration_anchor` 假设，(b) 台账含 `calibration_sensitivity[pid]`（varied 轴≥2）。TDD 6 单测；**真实数据 RED**：上线即拦 `cumcm2026a:P08/P12`。**实例合规**：A 题 P08→A04、P12→A03 补锚定；`solve_a` 时间常数参数化 + τ 扫描（300/450/600 s → 58.0944/58.1000/58.1111 h）产出 `calibration_sensitivity`。**反向验收**：移除 P08 锚定 → validate FAIL 指名 → 字节级还原后 48/0/0 | ✅ 642 passed，validate 48/0/0，catalog OK，术语 OK | 本轮 |
| **标准层 v1.2：显式引用契约 + 双级门禁 + 金标准** | 根治「门禁漏检而非真死」（2026b P13/P14 事件）：① `parameters[].used_in=[{type,ref}]` 七类引用硬校验（组件 id 可解析 / code 文件存在且禁越界）；② `check_parsimony_budget` 只对破损显式声明硬 FAIL，新增 `check_dead_param_scan` 为 WARN 级（WARN_CHECKS），启发式不再单独决定硬失败；③ G4 义务支持 `{layer,evidence_refs}` 对象形态；④ 三实例 46 参数机器扫描生成 used_in（每参数 2–12 个真实引用，zero-hit=[]，人工抽审）；⑤ 金标准 `tests/fixtures/param_usage_gold.json` 度量启发式 FP=FN=0。TDD 17 新单测 | ✅ 700 passed，validate 52/0/0，catalog OK，术语 OK，金标准 FP=FN=0 | 本轮 |
| **能力层：结构可识别性 + 词表修订 r1** | 新增工具 `cli/structure_coverage.py`（只读词表）把「方法结构对齐」从散文变数字：修订前实例结构解析率 **10/19 = 52.6%**（2026a 3/6、2026b 1/7），9 项落 `out_of_catalog`——即 `PROJECTS_FEEDBACK_AUDIT §4` 自承的「词表无交集」。按词表自带 **Architecture Gate**（定义清晰/层级明确/跨来源/可映射真实题/不与现有重叠）逐条复核后修订（ADR-0010）：`mass_transfer`/`moving_boundary`→`numerical_pde.mechanism`，`effective_property_correlation`→method，新增 families `computational_geometry`、`coverage_path_planning`。修订后 **19/19 = 100%**（同命令可复现）。**方法卡登记**：给 2026 相关族挂卡（numerical_pde←mc-moving-boundary-pde、computational_geometry←mc-bearing-triangulation、coverage_path_planning←mc-coverage-search）；2026 A/B 实例在 `model_family.cards` 登记选型，**方法卡登记率 0/3 → 2/3 = 66.7%**（2024a 未登记，如实暴露）。附 9 单测 | ✅ 651 passed，validate 48/0/0，catalog OK，术语 OK | 本轮 |
| **标准层 §9.3/§9.4/§9.7 优化收口（T-THEORY-08 遗留项）** | 创新短板专项：① **§9.3 R3 连续结构距离**：`innovation_metrics.py` 建结构本体图 O（节点=建模结构族，边=组合/父子），`d_structure = 1 − max sim`（同源=1、邻居=0.5^L、不连通=0），新增 `canonicalize_token`/`family_similarity`/`continuous_structure_distance`/`build_ontology`；**声明审计**比对声明值与机械计算值，偏差>阈值→WARN（防虚报创新），`innovation_report` 输出 computed/delta/audit；新增 `--json` 供流水线消费。② **§9.4 G4 子问题粒度**：证据检查下钻到 `sub_question_binding`；**显式 opt-in**（`evidence_obligations_subquestion_scope: true`）避免误伤按实例级 G4 撰写的历史合规实例；新增证据独立性提示（同一 evidence_ref 支撑多层义务→非阻塞 WARN）。③ **§9.7 工具打磨**：G5 死参数 FAIL/WARN 消息自解释（逐参数列出 id/symbol/name/value 已尝试信号）；`artifacts/data/*.csv` 纳入使用语料（金标准 46 参数全 used → FP/FN 仍为 0，噪声由该表锁基线）。**全绿**：715 passed，validate 52/0/0，catalog OK，术语 OK，金标准 FP=FN=0；三实例反向验收（注入子问题作用域缺陷→FAIL→还原→PASS） | ✅ 715 passed，validate 52/0/0，catalog OK，术语 OK，金标准 FP=FN=0 | 本轮 |

| **知识卡门禁增强 + 建模经验回灌（T-B/T-E1）** | ① **反向引用闭合（第三层门禁）**：`catalog_check` 补齐 `failure.applies_to → card.known_failures` 反向校验（运行时只校验 card→failure 一个方向，导致「写了失败记忆但检索不到」的死知识可长期存在）；刻意不进运行时加载路径，避免编辑中间态让运行时 fail-closed 崩溃。实测发现并修复 2 处存量断裂（`fm-small-sample-deep-learning→mc-xgboost`、`fm-timeseries-no-backtest→mc-grey-gm11`），现全库双向闭合。② **降级不再静默**：原第二层在缺 `jsonschema` 时直接 return 而输出仍为 OK，使「schema 全绿」名不副实；改为写入 `warnings` 显式打印，新增 `--strict` 将降级提升为硬失败（exit 1），warnings 默认不计退出码以守 ADR-0004。③ **新失败卡 2 张**：`fm-conditional-objective-hides-infeasibility`（条件期望掩盖不可行）、`fm-interval-parameter-direction`（区间参数语义读反），均挂入 `mc-bearing-triangulation` / `mc-prior-robustness-regret` 的 `known_failures`。④ **方法卡回灌**：测向卡补「可行性优先于最优性」「区间参数三档语义」「双准则交叉核验」；后悔值卡补可行集 `F = {x: max P_fail ≤ τ}`、情景集 = 先验 × 区间参数、双准则一致性报告。⑤ **两个 critic 加固**：model-critic 维度 4 扩为「可解性与可观测性」（不可观测量代入具体值 / 区间参数用乐观端当保证端 → FAIL）；experiment-critic 加「失效概率与目标并列」。⑥ 新增 `tests/unit/test_catalog_check.py`（10 项，含门禁活性反证与降级三态）。**全绿**：736 passed，validate 52/0/0，doctor 13/0/0，catalog OK（缺/有 jsonschema 两种环境分别验证） | ✅ 736 passed，validate 52/0/0，doctor 13/0/0，catalog OK | 本轮 |
| **2026_B Q1/Q2 重建 + 知识卡门禁（T-A/T-B/T-D1）** | ① **知识卡门禁落地**：`catalog_check.py` 新增 `check_knowledge_cards()` 两层校验（层 1 运行时契约 fail-closed；层 2 jsonschema Draft7，软依赖缺失则跳过），填补丁「知识卡 schema 零 Python 执行点」这一真实缺口；4 份 schema 的 `source_type` 枚举补 `BZD`（**方向校正**：先是改数据去迁就枚举，反向测试证明测试与数据才是规格、枚举才是陈旧一侧，已回滚）。② **定位方法卡 v2**：`mc-bearing-triangulation` 由 v1 升 v2，剔除「GDOP ∝ 1/sinφ、φ=90° 最优」这一被证伪表述，补完整闭式 `D = (2 sinε/sinχ)·√(R²+L²+|R²+L²−d²|)` 与 L 依赖性，新增 5 条方法卡 / 5 条失败卡。③ **2026_B Q1/Q2 重建**：修正接收半径语义（1000 m 是「保证可接收」上限而非下限）→ 算例与反例改取保证可行；反例改正向模型生成并加 ρ 相似不变性降维扫描定上确界 0.5002942（v1 手搓反例 0.5083 落在可达集外，夸大 28.33×）；Q2 目标由 φ 换 E[D]，场景集扩为「距离先验 × r_rec 假设」6 个，补可行性优先筛选与 (ψ,d) 闭式可行域 ψ ≤ arcsin(r_rec/R_max) = 42.17°；新增独立复核（99 项机器校验全通过，含重跑可复现）与 v1 缺陷审计（ast 解析源码取字面量，不重抄数字）。**全绿**：726 passed，validate 52/0/0，doctor 13/0/0，catalog OK | ✅ 726 passed，validate 52/0/0，doctor 13/0/0，catalog OK | 本轮 |

## 当前数字（机器实测，Python 3.12.10，截至 2026-09-11）
| 项 | 实测输出 | 生成命令 |
|---|---|---|
| 单元/集成/端到端测试 | **792 passed / 0 skipped / 0 failed**（viz 确定性渲染器 + 项目图表门禁接入后复测） | `py -3.12 -m pytest tests -q` |
| 项目级校验 | **53 通过 / 0 失败 / 0 警告**（新增「项目图表」门禁 L6.4） | `py -3.12 src/modeling_harness/cli/validate.py` |
| catalog 三方一致 | **OK** | `py -3.12 src/modeling_harness/cli/catalog_check.py --check` |
| 术语零残留 | **OK**（production 零残留，无行内豁免） | `py -3.12 src/modeling_harness/cli/catalog_check.py --check-terminology` |
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
  2026 A/B 全问建模交付（2026-09-10）：
    projects/cumcm2026a（药材烘干：径向耦合 PDE + Landau 移动边界）✅ 四件套 + state
    projects/cumcm2026b（干扰源交会定位 + 同心环覆盖清除）✅ 四件套 + state
    反向修复 harness 4 处（Mermaid 闭合误判 / README 内部路径泄漏 ×3）
    知识沉淀：方法卡 3 + 失败卡 5 + playbook 2（A/B 各 1）
    交接文档：`docs/HANDOFF.md`（跨题门禁/修复/backlog）+ `projects/cumcm2026a/HANDOFF.md`、`projects/cumcm2026b/HANDOFF.md`；`.rivet/` 入 `.gitignore`

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
