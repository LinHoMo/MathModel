# 终审报告（audit Batch 10）

> 日期：2026-09-09 ｜ 依据：Batch 0–9 全部证据 + 全量回归实测
> 基线：**966 passed / 4 skipped / 0 failed**；validate 58/0；catalog/terminology OK
> 立场：**18 项验收按"是否有机械证据"逐项判定**；无证据即 NOT-ESTABLISHED，
> 不用"应该有/设计了"代替。

## 一、18 项验收矩阵

### A. Construction

| # | 验收 | 判定 | 证据 |
|---|---|---|---|
| A1 | Problem → Representation | ✅ REAL | `problem_repr.py`（question_spec/problem_txt → ProblemRepresentation）；Problem artifact 登记 + motivates 边（handlers.do_problem_analysis）；无题面时 source="none" 如实标记（治理 commit） |
| A2 | Representation → Candidates | ✅ REAL | `core/runtime/modeling/candidates.py` + m3 竞技场（M3 候选 A/B 证据化比较）；FIX-2.2 无证据不选型 |
| A3 | Candidates → Selection | ✅ REAL | `selection.py` FIX-2.2：SelectionOutcome.selection_status、无证据→UNSELECTED/pending_evidence；`MethodArena.select(evidence=...)`；决策 artifact + selects 边 |
| A4 | Selection → MODEL_IR | ✅ REAL | model_ir.schema.json jsonschema 实例校验（registry.create 强制，Batch 5）；18 顶层 required；skeleton 不编造空规格（FIX-2.1） |

### B. Execution

| # | 验收 | 判定 | 证据 |
|---|---|---|---|
| B1 | MODEL_IR → Code | ✅ REAL | FIX-3.1 `_check_ir_code_mapping`：implementation_ref 必须与真实执行 code 一致，断裂抛 HandlerError（不静默）；test_ir_code_mapping 3 测试 |
| B2 | Code → ExecutionPlan | ✅ REAL | ExecutionPlan 生成（handlers.do_model_execution 委托 adapter） |
| B3 | ExecutionPlan → subprocess | ✅ REAL | LocalPythonAdapter 真实 subprocess（vs001 8 测试实测 1.925/1.65 数值） |
| B4 | subprocess → ExecutionResult | ✅ REAL | execution_result.schema.json 实例校验 + status 枚举 + code_hash 强制（Batch 1 FIX）；status 只来自 returncode |
| B5 | failure 正确传播 | ✅ REAL | handlers `_results_of(include_failed=False)` + do_model_execution 任一失败→节点 FAIL 含 stderr（Batch 1）；execution_failed→验证 invalid（validation.py precondition 分支） |

### C. Evidence

| # | 验收 | 判定 | 证据 |
|---|---|---|---|
| C1 | ExecutionResult 产生 evidence | ✅ REAL | do_evidence_build 合成 claim 只基于 EXEC outputs（claim_synthesis.py，无输出→placeholder 禁 supports 边）；supports 边带 exec_ref（FIX-4.1 边级 provenance） |
| C2 | Evidence 支持 claim | ✅ REAL | evidence_gate E9：边级 exec_ref 优先，缺失→weak→fail（Batch 4） |
| C3 | provenance 完整 | ✅ REAL | evidence_graph.add_relation exec_ref 参数 + registry 元数据注入 |
| C4 | hashes 完整 | ✅ REAL | code_hash（≥16，与 code 一致校验）+ 冻结 manifest sha256（K001-K003 冻结校验 PASS） |
| C5 | replay 可能 | ✅ REAL | `core/runtime/execution/replay.py`；vs001 test_07 重放 RUN1/RUN2 outputs_match=True |

### D. Validation

| # | 验收 | 判定 | 证据 |
|---|---|---|---|
| D1 | structural validation | ✅ REAL | validate_model_ir 18 顶层 + 各节 required（jsonschema） |
| D2 | mathematical validation | ✅ REAL | FIX-5.3 formula_checker 接线（括号配对/LaTeX/常见错误）→ L2 Mathematical |
| D3 | computational validation | ✅ REAL | run_numeric_validation 真实数值（constraint_violation_max/objective/domain）；derive_checks_from_mir（FIX-5.2 不自动回退） |
| D4 | empirical validation | ✅ REAL | 通用检查集（output_range/equals/numeric 确定性判定）+ VS-001 数值 FAIL 实测 |
| D5 | validation 影响决策 | ✅ REAL | model_validation 节点 FAIL→do_model_selection_decision 不登记选择（Batch 2）；revision_acceptance 决策基于 VR（Batch 6） |

### E. Revision

| # | 验收 | 判定 | 证据 |
|---|---|---|---|
| E1 | failure 产生 diagnosis | ✅ REAL | FIX-6.1 diagnosis.py 机械归因（failed checks/constraint_violation/execution）；VR status=failed 才可诊断；diagnosis artifact + diagnosed_by 边 |
| E2 | diagnosis 产生 revision | ✅ REAL | FIX-6.2 revision.py build_revision_draft（changed_components 映射 + modeling_trace revision_draft 步骤；**不编造新数值**——M2 数值由外部 Model Constructor 提供） |
| E3 | M2 linked to M1 | ✅ REAL | revision_of 边 + supersede 方向统一（FIX-6.3：M2 supersedes M1；registry.supersede(M1, replacement=M2)；M1 数据保留、status=superseded） |
| E4 | M2 re-executed | ✅ REAL | vs001 run_m2 修订环（model_construction→…→model_validation 全 PASS）；CODE2→EXEC2→R2 独立链 |
| E5 | M1/M2 compared | ✅ REAL | FIX-6.4 comparison.py 机械比较（valid/checks_passed/robustness/cvm deltas） |
| E6 | acceptance decision 记录 | ✅ REAL | revision_acceptance decision artifact（recommendation/chosen/reasoning/deltas）+ selects 边 |

### F. Integrity

| # | 验收 | 判定 | 证据 |
|---|---|---|---|
| F1 | Generator 不能伪造 execution result | ✅ REAL | execution_writer.py 唯一写入路径（Batch 4）+ registry schema 门禁 + status 枚举 |
| F2 | Agent 不能伪造 evidence | ✅ REAL | supports 边必须指向真实 EXEC outputs（claim_synthesis）；占位 claim 禁 supports |
| F3 | Agent 不能伪造 fidelity | ✅ REAL | execution_result schema 校验 + E9 gate（边级 exec_ref 优先） |
| F4 | Organizer claims 独立验证 | ⏳ 待 Batch 7/8 独立复审回报 | o_00019F2qcEG 运行中 |
| F5 | 无 fake placeholders | ✅ REAL | "{qid} 结论" 占位禁 supports（handlers 1522+）；problem_repr legacy_fallback 已移除 |
| F6 | 无 hidden fallback | ✅ REAL | legacy_fallback 全清除（治理 commit）；derive_checks 不自动回退（FIX-5.2） |
| F7 | 无 legacy 兼容掩盖迁移 | ✅ REAL | production 区术语零残留（terminology check）；legacy 仅 V2 项目导入工具（state.py），不参与 runtime 核心链 |

### G. Reproducibility

| # | 验收 | 判定 | 证据 |
|---|---|---|---|
| G1 | replay works | ✅ REAL | vs001 test_07 + replay.py |
| G2 | environment hash | ✅ REAL | execution_result 环境溯源（session Hardening P3 executor 溯源） |
| G3 | code hash | ✅ REAL | code_hash 强制 + 一致性校验 |
| G4 | input hash | ✅ REAL | problem_sha256（model_ir problem_binding 64hex 强制） |
| G5 | execution provenance | ✅ REAL | executed_by 边 + exec_ref 边级 provenance + RunRecord |

### H. Testing

| # | 验收 | 判定 | 证据 |
|---|---|---|---|
| H1 | unit tests | ✅ | 966/4 全绿（基线实测） |
| H2 | integration tests | ✅ | 298 passed（tests/integration） |
| H3 | failure tests | ✅ | test_ir_code_mapping（断裂抛错）、test_revision_loop（不可诊断拒绝）、execution failure 传播 |
| H4 | E2E test | ✅ | vs001 8 测试（闭环+replay+lineage） |
| H5 | independent audit | ⏳ 待 Batch 7/8 | o_00019F2qcEG |
| H6 | full regression | ✅ | 966/4/0（每批必跑，本次治理后复跑） |

## 二、10 问题终审回答

**1. 当前系统真正能不能完成 Mathematical Model Construction？**
能——最小真实闭环已成立：2024_A 垂直切片从 Problem 走到 MODEL_IR（M1 缺陷模型）
→ 代码 → 真实执行 → 数值 FAIL → 机械诊断 → 修订 M2 → 再执行 → PASS → 机械比较 →
accept 决策 → Replay 可重现。**这是已验证的闭环，不是架构声明。**

**2. 哪些环节是真的，哪些只是 architecture？**
真：执行（subprocess→EXEC→VR）、数值验证、证据边（exec_ref）、选择决策、失败诊断、
修订谱系、比较决策、replay。仍是 architecture 而非生产验证：**K003 的 66 runs 实验**
（构造+执行一体化的表示效应测量）尚未执行完成；多题覆盖仅有 1 题垂直切片。

**3. 哪些地方仍然存在 fake completion 风险？**
- 外部 Model Constructor 注入的 MODEL_IR 本身仍可"形式上合法、数学上错误"
  （L2 数学检查只做公式结构，不做语义等价证明——如实声明为 L2 结构检查）；
- revision proposal 不生成数值（外部修订），存在"外部注入修订值错误"风险
  ——由 M2 再执行 + 验证门兜底，但无独立数学仲裁；
- claim 合成只禁占位，不保证"claim 内容与输出数学一致"（语义层）。

**4. Agent 可以伪造哪些事实？**
不能伪造：execution_result（status/code_hash/outputs）、supports 边（EXEC 产物）、
verification 数值。仍可影响：MODEL_IR 的变量/方程/参数（建模内容本身）、claim 的
文字表述（但无数值事实时禁 supports）。**剩余可伪造面 = 建模者的自由建模内容**，
这是 LLM-free 边界的设计选择，由执行+验证兜底。

**5. Execution 是否完全机械化？**
是——ExecutionResult.status 只来自 LocalPythonAdapter 真实 returncode；execution
写入唯一路径（execution_writer.py）；registry schema 门禁。**无 handler 默认生成。**

**6. Evidence 是否来自真实执行？**
是——supports 边必须带 exec_ref（FIX-4.1），E9 门禁边级校验；claim 只从 EXEC
outputs 合成；无输出→placeholder 禁 supports。

**7. Validation 是否真正影响决策？**
是——model_validation FAIL → model_selection_decision 不登记（Batch 2）；
M1 数值 FAIL → revision_acceptance 决策只基于 VR（Batch 6）。**验证是决策的
前置门，不是装饰。**

**8. Revision 是否真正存在？**
是——机械诊断（diagnosis artifact + diagnosed_by 边）→ 修订草案（不编造数值）→
M2（revision_of + supersedes 谱系，M1 数据保留）→ 再执行 → 机械比较 → accept
决策记录。**M1→FAIL→M2→PASS 真实跑通且可 replay。**

**9. 一个真实数学建模题能否从 Problem 走到 Model V2？**
能——2024_A（2024 国赛 A 题"板凳龙"）已验证完整路径。注意：这是**单题垂直切片**；
跨题泛化（K003 6 题+2 泛化题）是下一验证点。

**10. 公开后最容易被攻击的 10 个点？**
1. **单题验证**：只有 2024_A 一个完整闭环，跨题泛化未证 → "1 个例子不算引擎"；
2. **K003 未完成**：表示实验承诺（执行证据澄清）尚未落地 → "设计比结果多"；
3. **K001/K002 双 negative**：两轮主实验均 negative → "你的抽象没有能力增益"，
   必须靠 K003 + 能力 Δscore 正面回应；
4. **L2 数学检查的边界**：公式结构检查 ≠ 数学等价证明 → "validator PASS 不等于
   模型正确"（README 已声明 execution≠correct，但 L2 语义等价是开放问题）；
5. **revision 数值来自外部**：M2 修订值由外部 Model Constructor 提供，无独立数学
   仲裁 → "修订正确性依赖注入者"；
6. **盲评 κ 边界**（K002 0.4345）：3 evaluator 一致性偏弱 → "评分不稳健"（已用
   敏感性分析+锚定澄清缓解）；
7. **统计功效**（K001 n=11/臂、K003 rep=3）：CI 宽 → "无法区分小效应/噪声"
   （已如实声明）；
8. **候选竞技场未固化 benchmark**：M3 是演示不是正式能力基准 → "证据化选型没有
   系统级验证"；
9. **harmless/边缘：legacy 层存在**：V2 29 agent 兼容层 → "旧架构残留"（已隔离，
   production 零引用，但公众可能误解）；
10. **LLM-free 边界**：建模内容全部来自外部 Agent → "你的系统自己不建模"——
    这恰是定位（Harness），需在 README/报告反复澄清"认知由外部完成、Harness
    保证可信度"。

## 三、SYSTEM VERDICT（终版）

```
REAL CAPABILITY      : 最小 Model Construction Loop（Problem→MODEL_IR→Code→
                       Execution→Evidence→Validation→Diagnosis→Revision→M2→
                       Comparison→Accept）+ Replay —— 单题垂直切片已验证
ARCHITECTURAL CAP    : 完整 Runtime（Registry/Evidence Graph/DAG/Contract/Replay）
                       + 三实验测量体系（K001-K003）+ 候选/选型/修订语义
FAKE / UNVERIFIED    : K003 执行结果（FROZEN 未跑完）；跨题泛化；L2 语义等价；
                       revision 数值独立仲裁；候选竞技场正式 benchmark
MODEL CONSTRUCTION
LOOP STATUS          : REAL（最小闭环）—— 跨题泛化与能力增益待 K003/Δscore 证实
```

## 四、遗留与下一步

- ⏳ Batch 7/8 独立复审（o_00019F2qcEG）——回报后回填 F4/H5 判定与 TEST_TRUST_SCORE；
- K003 66 runs 生成 → 盲评 → 配对分析 → CLOSED（K003 报告 + 三实验对比 + P16 决策）；
- 项目治理后续：候选竞技场固化 benchmark、Knowledge-guided 正式化、Capability
  Validation（Δscore 八项指标）——按 STATUS.md「待用户拍板」三项推进。
