# Agent G — 测试体系反作弊审计报告（Test Integrity Audit）

- 审计官：Agent G（独立测试完整性审计官，只读审计）
- 审计日期：2026-09-09
- 审计范围：`C:\Users\Lin\Desktop\Programs\MathModel\tests\`（81 个测试文件，915 个收集测试）
- 审计方法：完整套件实跑 + 全量 mock/skip 扫描 + 24 个核心测试手工追踪（test → function → production → side effect）+ 单文件独立运行验证 + 已知问题覆盖核实
- 审计原则：**测试只检查字段存在而不验证真实性，等于没测；mock 了核心执行路径，测试通过不代表系统工作。**

---

## 0. 实际测试运行结果（与 AGENTS.md 声称基线对比）

| 项目 | AGENTS.md 声称 | 本次实跑 | 差异 |
|---|---|---|---|
| 总通过 | 758 passed | **911 passed** | +153 |
| 跳过 | 11 skipped | **4 skipped** | -7 |
| 测试文件数 | （未声明） | 81（hint 声称 217，不实） | — |
| 收集总数 | — | 915 | — |

- 命令：`py -3.12 -m pytest tests -q --tb=short -p no:cacheprovider` → **911 passed, 4 skipped in 65.97s**（复跑 `-rs` 确认 68.03s，结果一致）
- 仓库自身 commit `6af11fa` 明确写 "911 tests"，证实 758/11 为**过期基线**，AGENTS.md 未同步。
- 实际 skip 明细（4 个，全部为条件性 skip）：
  1. `tests/e2e/test_pipeline.py:44` — Modeler 产物 MODEL_SPEC.md 不存在 → 跳过
  2. `tests/e2e/test_pipeline.py:56` — Programmer 产物 CODE_DELIVERABLES.md 不存在 → 跳过
  3. `tests/e2e/test_pipeline.py:68` — Writer 产物 PAPER_SPEC.md 不存在 → 跳过
  4. `tests/integration/test_workflow_execution.py:112` — 当前 workflow 无人工审批节点 → 跳过

---

## 1. 发现计数（按 severity）

| Severity | 数量 | 编号 |
|---|---|---|
| **HIGH** | 5 | G-001, G-002, G-003, G-004, G-006 |
| **MEDIUM** | 8 | G-005, G-007, G-008, G-009, G-011, G-012, G-013, G-015 |
| **LOW** | 3 | G-010, G-014, G-016 |
| **合计** | 16 | |

---

## 2. TEST_TRUST_SCORE（测试信任分）

**69.2 / 100**

基于 24 个随机抽取核心测试的信任评级加权（FAKE=0.0，LOW=0.3，MEDIUM=0.6，HIGH=1.0）：

```
Score = (3×FAKE×0.0 + 4×LOW×0.3 + 4×MEDIUM×0.6 + 13×HIGH×1.0) / 24 × 100
      = (0 + 1.2 + 2.4 + 13.0) / 24 × 100
      = 69.2
```

**解读**：测试套件的"硬核"部分（执行运行时、fidelity、MODEL_IR schema、P1 注入式 e2e、DAG/图引擎）确实是真实执行 + 真实数值断言（HIGH 占 54%）；但**默认建模路径、证据内容真实性、端到端流水线**三个关键交付面被占位符/字段存在/结构性断言覆盖（FAKE+LOW 占 29%），把分数从"可信"区间拉低。**911 绿不代表系统工作——绿的是运行时机制，不是建模与证据内容。**

分域信任概览：

| 领域 | 信任级别 | 关键证据 |
|---|---|---|
| execution（subprocess 真实执行） | HIGH | LocalPythonAdapter 真 subprocess；test_execution_runtime/fidelity/codegen 断言真实数值 |
| validation（validator 真实计算） | HIGH | fidelity VR、DAG 校验、DecisionLog 校验均为真实逻辑 |
| modeling（选型/规划） | MEDIUM | 真实 retriever 评分 + 真实 planner，但选型硬编码 recs[0] 无测试捕捉 |
| evidence（证据门禁） | MEDIUM | 真函数但零数值计算；测试只验证结构行为，不验证内容真实性 |
| 默认确定性管线 | LOW | 产 not_executed 结果 + 占位 claim，测试把"validated"断言为正确 |
| e2e 流水线 | FAKE | 3/4 核心断言因产物不存在而跳过，注释自认"显式占位" |
| P1 注入式 e2e | HIGH | 外部 fixture 注入后全链路真实执行（不覆盖 LLM 建模侧） |

---

## 3. 抽取测试信任评级明细表（24 项）

| # | 测试（文件::test） | 信任级别 | 理由（test→function→side effect 追踪） |
|---|---|---|---|
| 1 | e2e/test_pipeline.py::test_modeler_can_output | **FAKE** | 产物不存在即 `pytest.skip`；注释自认"此 skip 为显式占位"。从未执行任何流水线 |
| 2 | e2e/test_pipeline.py::test_programmer_can_output | **FAKE** | 同上，CODE_DELIVERABLES.md / all_results.json 不存在即跳过 |
| 3 | e2e/test_pipeline.py::test_writer_can_output | **FAKE** | 同上，PAPER_SPEC.md / main.tex 不存在即跳过 |
| 4 | unit/test_aggregate_scores.py::test_verify_mode_exit_0 | MEDIUM | 真 subprocess 跑 aggregate_scores.py --verify，但依赖静态 fixture score_card.json；存在即断言，不存在即 skip |
| 5 | unit/test_evidence_gate.py::test_pass_when_all_good | MEDIUM | 真调用 evidence_gate.evaluate，但图/artifact 全为测试合成；断言只覆盖结构判定，无数值真实性维度 |
| 6 | unit/test_model_selection.py::test_select_returns_shortlist | MEDIUM | 真 retriever+arena；断言 chosen 格式/alternatives/criteria，**不验证 chosen 是否最优**（recs[0] 硬编码可轻松通过） |
| 7 | integration/test_execution_runtime.py::test_adapter_with_code_executes_and_updates_status | HIGH | 真 LocalPythonAdapter subprocess 执行注入代码，断言 status=success 与 value=={"answer":42} |
| 8 | integration/test_execution_runtime.py::test_adapter_failed_code_yields_failed_status | HIGH | 真执行 raise 代码，断言 failed + stderr 含真实报错 |
| 9 | integration/test_workflow_execution.py::test_retry_then_pass_completes | HIGH | 真 WorkflowComposer+Engine；executor 为测试桩但引擎重试/反馈环是真实逻辑 |
| 10 | runtime/test_model_ir.py::test_example_2024_A_passes | HIGH | golden 样本真实存在（research/P15/...），验证真实 18 字段契约 |
| 11 | unit/test_evals_and_runtime.py::test_each_eval_has_required_fields | LOW | 只查 evals.json 字段存在/非空；**从不运行任何 eval**，断言真实性为零 |
| 12 | unit/test_gate_paper_thresholds.py::test_gate_all_exit_nonzero | HIGH | 真 subprocess 跑 gate.py --level all；副作用：tearDown 删除 fixture 产物 |
| 13 | integration/test_p1_vs001_e2e.py::test_04_execution_result_has_real_numeric_outputs | HIGH | 真 subprocess + 真数值断言（pair_distances≈2.86/1.925，head_speeds≈1.0） |
| 14 | integration/test_p1_vs001_e2e.py::test_05_validation_fails_on_real_numbers | HIGH | 断言 constraint_violation_max≈0.275，数值判 FAIL，非伪造 |
| 15 | integration/test_p1_vs001_e2e.py::test_07_replay_reproduces_runs | HIGH | replay 真实重跑代码，断言输出一致 + 数值级差异 |
| 16 | integration/test_execution_codegen.py::test_execute_from_artifact_success | HIGH | 真 subprocess；断言 outputs=={"total_cost":42.0}、code_hash 与 CODE 一致 |
| 17 | integration/test_execution_codegen.py::test_registers_with_sha256 | LOW | 断言被 `[:0] or None` 中和为恒真——硬编码 hash 失效，实际只查 isinstance(str) |
| 18 | integration/test_p1_m3_competition.py::test_02_decision_fields_and_ranking | HIGH | 真 subprocess 双候选 + VR 数值排序断言（cv 0.275 vs 0.0）；chosen==min(cv) |
| 19 | integration/test_runtime_session.py::test_artifacts_and_evidence_registered | LOW | 默认管线跑通，但只查 artifact **类型在场**；model_ir 不在断言集内，占位 claim/not_executed 结果照样绿 |
| 20 | integration/test_runtime_session.py::test_state_derived_questions_validated | LOW | 直接断言占位管线状态="validated"、claims_supported=2——**把假内容编码为正确行为** |
| 21 | integration/test_execution_fidelity.py::test_mapping_lie_detected | HIGH | 真 fidelity 计算；断言 mapping 谎报被如实判 misaligned |
| 22 | integration/test_red_team.py::test_R4_rerun_creates_new_lineage | MEDIUM | 真引擎 rerun 语义，但运行对象是占位 claim/not_executed 结果——机制真、内容假 |
| 23 | integration/test_replay_execution.py::test_replay_identical_outputs | HIGH | 真 subprocess + 真 replay 输出比对 |
| 24 | unit/test_decision_log.py::test_invalidate_active | HIGH | 真 DecisionLog 校验（生命周期/幂等/审计），断言语义完整 |

**抽样统计**：HIGH 13 / MEDIUM 4 / LOW 4 / FAKE 3。

---

## 4. 逐项审计结果

| 审计项 | 结论 |
|---|---|
| 1. fixture 替代真实执行？ | 部分。fixtures/ 为静态产物快照（score_card.json 等），aggregate/gate 测试基于静态产物而非重算；e2e 用"目录存在"当 fixture，产物缺失即跳过 |
| 2. mock 掩盖真实 runtime？ | 否。**0 个 mock.patch / MagicMock / Mock(；84 处 monkeypatch 均为合法隔离用途**（env 删除、config 替换、fs stub）。无核心路径 mock |
| 3. 依赖其他 test 的 import side effect？ | 否。单文件独立运行 3 个关键文件均通过（见 §7）。但**全体依赖 conftest 全局 chdir 副作用** |
| 4. assertion 验证数值？ | 分裂。execution/fidelity/P1 系列断言真实数值；runtime_session/e2e_metrics/evals 只查字段/类型在场 |
| 5. 空测试？ | 无。多行扫描 0 个 pass-only / docstring-only 测试 |
| 6. skip 合理？ | 不合理（3 个 e2e 占位 skip + 1 个审批节点环境 skip，见 G-009） |
| 7. integration 进入 production path？ | 执行类进入（真 subprocess）；建模/证据类只进结构层；e2e 类**不进**（占位） |
| 8. hardcoded expected output？ | 有：P1-M3 chosen=="MIR002"、non_regression anchor（method_selection=0 等）、codegen sha256 死值 |
| 9. 只检查字段存在？ | 有：test_evals_and_runtime（29 agent evals 从不运行）、test_runtime_session 类型在场、e2e 文件存在性 |
| 10. process-level side effects？ | 有：conftest 全局 chdir；gate 测试 tearDown 删除 fixture 文件；monkeypatch.delenv 环境变量 |

---

## 5. 完整发现清单

---

### G-001 [HIGH] e2e 流水线测试是自认的占位符，端到端从未被执行

- **File**: `tests/e2e/test_pipeline.py`
- **Function-Symbol**: `TestEndToEndPipeline.test_modeler_can_output` / `test_programmer_can_output` / `test_writer_can_output`
- **Line**: 36-69（skip 于 44 / 56 / 68）
- **Observed behavior**: 三个名义上的"端到端管道测试"在产物不存在时 `pytest.skip`。本次实跑 3 个全部跳过（见 §0）。line 40-41 注释自认："[legacy 冻结] V2 流水线产物不再重建，此 skip 为显式占位（非覆盖空洞）；V3 主线产物由 Artifact Registry 管理，对应断言见 tests/integration/test_*_runtime.py"
- **Expected behavior**: e2e 测试应真实构造/运行一条 Modeler→Programmer→Writer 流水线并断言产物；至少应 FAIL 而非 SKIP（"没有产物"本身就是交付缺陷）。
- **Why it matters**: 仓库最显眼的 "端到端管道测试" 实际什么都没测。`test_modeler_can_output` 在样本中被评为 FAKE。全绿结果里 3 个绿点来自 skip，非执行。
- **Evidence**: 实跑 `SKIPPED [3] tests\e2e\test_pipeline.py:44/56/68`；fixture 项目 `output/`、`figures/`、`paper/` 为空目录。
- **Reproduction**: `py -3.12 -m pytest tests/e2e/test_pipeline.py -q -rs` → 3 skipped。
- **Proposed fix**: 要么让 e2e 真实跑 V3 RuntimeSession 并断言 registry/graph/state 落盘产物；要么删除该文件并明确声明 V3 的 e2e 载体是 `tests/integration/test_p1_*_e2e.py`。**占位 skip 必须移除。**
- **Regression risk**: 若改为真实执行，需保证测试可离线确定性复现（固定种子 42）。
- **Test required**: 新增一条不依赖任何前置产物的真实 e2e（RuntimeSession 默认管线 → registry 落盘 → 关键 artifact 数值断言）。

---

### G-002 [HIGH] "默认路径建模节点不产 MODEL_IR 仍 PASS" 被测试显式编码为预期行为

- **File**: `tests/integration/test_e2e_metrics.py`（+ `tests/integration/test_runtime_session.py`）
- **Function-Symbol**: `TestE2EMetrics.test_model_structural_check_modelir_contract`（line 80-120）；`DefaultNodeExecutor.do_model_selection`（handlers.py:808-849）
- **Line**: test_e2e_metrics.py:117-120；handlers.py:848-849（只建 `model` artifact，data 为 card_id/family/shortlist，无 MODEL_IR）
- **Observed behavior**: 
  1. 默认管线 `do_model_selection` 创建的是方法族容器 `model` artifact（`card_id`/`family`/`shortlist`），**从不创建 `model_ir` artifact**。
  2. `test_model_structural_check_modelir_contract` 显式断言"全为 legacy pointer → `structural_pass is None`（不判 FAIL）"、`legacy_pointer_skipped == 1`。
  3. `test_runtime_session.py::test_artifacts_and_evidence_registered` 断言的类型集合为 `{problem, question, model, assumption, experiment, result, figure, claim, paper_section}` —— **model_ir 不在其中**，且全套测试中仅 test_p1_vs001_core.py 直接 `create("model_ir", ...)`（手工构造），没有任何测试断言默认 RuntimeSession 产出 MODEL_IR。
- **Expected behavior**: 若"MODEL_IR 是建模节点必交付物"（P1-VS-001 C1 契约），默认路径不产 MODEL_IR 应使结构检查 FAIL 或至少 WEAK，测试应捕捉这一缺失。
- **Why it matters**: 这是已知问题中影响最大的一条：**结构评分机制为 legacy pointer 开豁免**，等于给"不产 MODEL_IR"发免死金牌。测试不仅没抓，还把它固化为预期输出（`structural_pass is None` 被 assert）。benchmark 的 model_correctness / method_selection 指标因此永远测不到默认管线。
- **Evidence**: `Select-String 'list_by_type("model_ir")|create("model_ir"'` 全测试仅命中 test_p1_vs001_core.py（手工构造）；e2e_metrics.py 的 `_model_structural_check` 只对 MODEL_IR 计数（`models_checked==1`），legacy pointer 全部 skip。
- **Reproduction**: 运行默认 `RuntimeSession(["Q001"]).run()` 后 `registry.list_by_type("model_ir")` 为空，但 `test_runtime_session.py` 全绿。
- **Proposed fix**: 删除/收紧 legacy pointer 豁免（可降级为 WEAK 而非 None）；新增断言"默认管线必须产出 ≥1 个 model_ir"。
- **Regression risk**: 高——将直接打红一批默认管线测试（test_runtime_session / red_team / research_runs），暴露真实缺口。
- **Test required**: `test_default_pipeline_produces_model_ir`（断言类型在场 + 三层结构 + 与 model artifact 的 instantiates 边）。

---

### G-003 [HIGH] claim 占位符（"{qid} 结论"，placeholder=True）无任何测试覆盖，且被断言为通过

- **File**: `core/runtime/execution/handlers.py` / 全 tests/
- **Function-Symbol**: `DefaultNodeExecutor.do_evidence_build`
- **Line**: handlers.py:1219-1227
- **Observed behavior**: 默认证据构建生成 `claim(title=f"{qid} 结论", data={statement: f"{qid} 结论", claim_type: "comparative", execution_status: "not_executed", placeholder: True})`，并**自动补一条 result→claim 的 supports 边**。随后 `do_evidence_gate` 因"claim 有 supports 边"而 PASS。全测试中 **0 处**断言 claim 非占位；`test_runtime_session::test_state_derived_questions_validated` 反而断言 `claims_supported == 2`（占位 claim 全部"被支撑"）。
- **Expected behavior**: 存在测试断言默认管线产出的 claim 具备真实语句内容（非 "{qid} 结论"）、非 placeholder、execution_status 非 not_executed（或明确标注该路径为 demo 并禁止进入论文投影）。
- **Why it matters**: 占位 claim 自带 supports 边 → evidence gate 结构上必然通过 → 默认管线对"无真实结论"完全免疫。这与 evidence 语义（"Evidence 不是 Agent 写出来的，而是 execution substrate 产生的"）直接矛盾。
- **Evidence**: 全测试 grep "placeholder" 仅命中 check_placeholders（validate_project 工具名），无断言 claim.data.placeholder 为假；实跑 911 绿中 `do_evidence_build` 占位路径全绿。
- **Reproduction**: `py -3.12 -m pytest tests/integration/test_runtime_session.py -q` → 9 passed，断言 claims_supported=2。
- **Proposed fix**: 新增测试断言默认管线 claim 的 `data.placeholder is False` 或 `statement` 非模板串；占位路径应被证据门禁判 WEAK/FAIL。
- **Regression risk**: 中——会打红默认管线全链（evidence gate 将 FAIL，feedback loop 暴露）。
- **Test required**: `test_default_pipeline_claims_not_placeholder`。

---

### G-004 [HIGH] evidence_gate 零数值计算，测试只验证结构行为——"无证据"被降格为"无边"

- **File**: `core/validators/evidence/evidence_gate.py` / `tests/unit/test_evidence_gate.py`
- **Function-Symbol**: `evaluate()`
- **Line**: evidence_gate.py:87-181
- **Observed behavior**: gate 全部检查项 = 边存在性（E1/E2/E4/E5）+ 生命周期状态（E3/E6）+ 标签存在（E8）+ 覆盖率比值（E7，来自 `graph.coverage()`，仍是边计数）。**对 result 的数值内容零检查**——一个 value 被伪造/占位的 result 若挂着正确的边，gate 照常 PASS。测试（test_evidence_gate.py 全部 15 项）构造合成图，断言 verdict/code 字符串，忠实于浅实现但从未验证"结果数值为真"这一要求。
- **Expected behavior**: 证据门禁至少应校验 result 携带真实数值（非 not_executed、非空 outputs、与 execution_result 一致），并有测试断言伪造数值会被拦截。
- **Why it matters**: 系统宣称"无证据不得进入论文投影"，实际只是"无边不得进入"。"evidence 是否真实生成"这一审计核心问题，测试没有回答。
- **Evidence**: 已知背景独立核实成立：evidence_gate.py 全文无任何数值运算；test_evidence_gate.py 全部合成数据 + 结构断言。
- **Reproduction**: 构造一个 result(data={"value": None, "status": "not_executed"}) 并挂 supports 边 → gate PASS，无测试拦截。
- **Proposed fix**: 新增 E9 检查（result 数值真实性：status==executed 且 outputs 非空或 value 非占位）；配套测试断言 not_executed/空值 result 触发 FAIL/WEAK。
- **Regression risk**: 高——默认管线 not_executed 结果将无法通过 gate（这正是要暴露的问题）。
- **Test required**: `test_gate_fails_on_not_executed_result_with_supports_edge`。

---

### G-005 [MEDIUM] selection.py:60 硬编码 `chosen=recs[0]` 无测试捕捉，选型能力被锚定为 0

- **File**: `core/runtime/modeling/selection.py` / `tests/unit/test_model_selection.py`
- **Function-Symbol**: `MethodArena.select`
- **Line**: selection.py:60
- **Observed behavior**: `chosen=recs[0].card.card_id` —— "选型"恒取检索排序第一名，无独立竞争逻辑。`test_select_returns_shortlist` 只断言 `chosen.startswith("mc-")`、shortlist≥2、decision 记录存在，**从不断言 chosen 是最高分/最优**。
- **Expected behavior**: 应有测试验证 chosen 对应最高分候选（如构造两个候选使 recs[0] 非最优场景，断言 chosen 跟随最优）。
- **Why it matters**: "MethodArena（方法选型竞技场）"名不副实；更严重的是 `test_non_regression_contract::test_quality_axis` 把 `method_selection: 0` 写进硬编码 anchor 且 `if v is None: continue`——**benchmark 自己承认方法选型能力为 0，回归测试还把它锁死为可接受基线**。
- **Evidence**: selection.py:60 直读；test_model_selection.py 全文件无 score 排序断言；test_non_regression_contract.py:41-49 anchor。
- **Reproduction**: `py -3.12 -m pytest tests/unit/test_model_selection.py -q` → 8 passed，均不涉及 chosen 最优性。
- **Proposed fix**: 新增测试断言 chosen.score == max(shortlist scores)（当前实现恰好满足，但至少锁住语义）；评估是否引入真竞争逻辑。
- **Regression risk**: 低（当前实现满足断言）。
- **Test required**: `test_chosen_is_highest_scored_candidate`。

---

### G-006 [HIGH] core/validators/modules/ 下 21 个 validator 是死代码，且零测试覆盖、零死代码检测

- **File**: `core/validators/modules/*.py`（21 个）/ 全 tests/
- **Function-Symbol**: assumption_validator / formula_checker / symbolic_verifier / hash_chain / integrity_gate / stage_gate / type_system 等 21 个模块
- **Line**: 整个目录
- **Observed behavior**: 生产代码 `from validators.modules...` 命中 **0** 次；测试引用 `validators.` 仅 `validators.quality` 与 `validators.evidence`。21 个模块既不被调用也不被测试。这些模块声称提供 symbolic_verifier / formula_checker / hash_chain 等关键能力，实际是**无人使用、无人验证的僵尸代码**。
- **Expected behavior**: 存在测试断言所有 core/validators/** 模块至少被 import 或声明为待接入；被移除或标注 dead code。
- **Why it matters**: 仓库宣称的验证能力（公式检查、符号验证、哈希链、完整性门禁）实际挂在死代码上。审计"validator 是否真实计算"时，答案是一半的 validator 根本不参与。
- **Evidence**: `Select-String 'from validators\.modules|import validators\.modules' core -r` → 0；测试同查 0。
- **Reproduction**: `py -3.12 -m pytest tests -q` 全绿，但上述 21 个模块从未被 import。
- **Proposed fix**: 新增 import-cover 测试（收集 core/validators/modules 全部模块并断言存在至少一个引用点），或正式删除/归档死代码。
- **Regression risk**: 低。
- **Test required**: `test_all_validator_modules_are_imported`（或等价死代码检测）。

---

### G-007 [MEDIUM] conftest.py 收集期全局 `os.chdir(ROOT)` 是进程级副作用，全体相对路径断言依赖它

- **File**: `tests/conftest.py`
- **Function-Symbol**: 模块顶层 `os.chdir(ROOT)`
- **Line**: 17
- **Observed behavior**: pytest 收集阶段无条件改变进程 cwd 到仓库根，使数百个 `os.path.isdir("core/...")` 相对断言成立。文档注释承认这是为"换个目录跑就全挂"打的补丁。
- **Expected behavior**: 相对路径断言应基于显式 ROOT 派生（如 `ROOT / "core" / ...`），而非依赖全局 cwd。
- **Why it matters**: 全局副作用让"测试是否真的在仓库根运行"不可见；任何直接 `python tests/xxx.py` 或嵌入式调用都会失败；多项目并发 pytest 会互相污染 cwd。
- **Evidence**: conftest.py:15-17；单文件运行验证（见 §7）依赖 conftest 才通过。
- **Reproduction**: 在非仓库根 cwd 运行任意含相对路径断言的测试 → 依赖 conftest 被加载才通过。
- **Proposed fix**: 逐步把相对路径断言改为 `repo_path(...)` 绝对路径；conftest 的 chdir 仅作兼容。
- **Regression risk**: 中（涉及大量测试文件）。
- **Test required**: 抽取 3-5 个文件改为绝对路径后从任意 cwd 运行通过。

---

### G-008 [MEDIUM] AGENTS.md 测试基线过期（758/11 vs 实际 911/4）

- **File**: `AGENTS.md`
- **Line**: "修改后必做"节 `py -3.12 -m pytest tests -q # 758 passed / 11 skipped（基线）`
- **Observed behavior**: 实跑 911 passed / 4 skipped；仓库 commit 6af11fa 亦写 "911 tests"。AGENTS.md 的 758/11 与当前状态相差 +153/-7。
- **Expected behavior**: 基线应同步为 911 passed / 4 skipped（或标注生成日期与 commit）。
- **Why it matters**: 维护者按 AGENTS.md 判断"回退"会得到错误信号（例如 800 个通过被误判为回退，或 758 个通过被误判为进步）。
- **Evidence**: 本次两次独立实跑均为 911/4；git log 6af11fa。
- **Reproduction**: `py -3.12 -m pytest tests -q`。
- **Proposed fix**: 更新基线数字并注明 commit。
- **Regression risk**: 无。
- **Test required**: 无（文档维护）。

---

### G-009 [MEDIUM] 4 个 skip 中 3 个是"测试对象不存在"的静默占位，1 个是特性未被环境启用

- **File**: `tests/e2e/test_pipeline.py`（44/56/68）、`tests/integration/test_workflow_execution.py`（112）
- **Function-Symbol**: 见 G-001；`TestHumanApproval.test_waiting_approval_and_approve`
- **Line**: 见上
- **Observed behavior**: e2e 三个 skip = 产物不存在即跳过（等同于"没测"）；workflow 审批测试因当前 DAG 无 human_approval 节点而跳过（**人工审批特性当前零覆盖**）。
- **Expected behavior**: "产物不存在"应 FAIL（交付缺陷）或真实生成；审批特性应 fixture 一个含审批节点的 DAG 来测。
- **Why it matters**: skip 把缺陷伪装成绿点。AGENTS.md 声称 11 skipped，实际只有 4 个且均为条件性跳过。
- **Evidence**: `-rs` 输出见 §0。
- **Reproduction**: 已实跑复现。
- **Proposed fix**: e2e skip 移除（见 G-001）；审批测试用 `core/workflows` 中带审批节点的配置或手工构造 DAG。
- **Regression risk**: 中。
- **Test required**: `test_human_approval_with_approval_node`（不再 skip）。

---

### G-010 [LOW] test_execution_codegen.py 的 sha256 断言被 `[:0] or None` 中和为恒真

- **File**: `tests/integration/test_execution_codegen.py`
- **Function-Symbol**: `TestRegisterCode.test_registers_with_sha256`
- **Line**: 45-47
- **Observed behavior**: `assert sha256 == ("9d0a...e5e6"[:0] or None) or isinstance(sha256, str)` —— `"..."[:0]` 为空串，`"" or None` 为 None，故恒等式退化为 `sha256 == None or isinstance(sha256, str)`。硬编码的期望 hash 被截断为 0 长度后丢弃，实际只断言"是字符串"。
- **Expected behavior**: 要么断言与已知 CODE_OK 的真实 sha256 相等，要么删除死值、只保留长度 64 断言。
- **Why it matters**: 断言外观上像"校验硬编码值"，实际无校验力；是"看起来在测、实际没测"的微缩样本。
- **Evidence**: 直读 line 45-47。
- **Reproduction**: 无需复现，静态可证。
- **Proposed fix**: 计算 `CODE_OK` 真实 sha256 并断言相等。
- **Regression risk**: 低（真实值稳定）。
- **Test required**: 本测试修正即可。

---

### G-011 [MEDIUM] test_gate_paper_thresholds.py 运行期删除共享 fixture 文件（进程级副作用）

- **File**: `tests/unit/test_gate_paper_thresholds.py`
- **Function-Symbol**: `TestGatePaperThresholds.tearDownClass`
- **Line**: 20-26
- **Observed behavior**: gate.py --level all 运行会生成 `paper/main.pdf` 与 `work/inputs_baseline.json`，tearDownClass 无条件 `unlink` 这两个文件以"保持 fixture 静态入库"。测试即产生又销毁仓库内文件。
- **Expected behavior**: 测试应在 tmp_path 副本上运行 gate.py，不触碰仓库 fixture。
- **Why it matters**: 若测试中途崩溃/并行运行，会留下或删除半成品状态，污染共享 fixture；审计"process-level side effects"命中。
- **Evidence**: line 20-26；实跑后 fixture 目录被清理（当前无残留）。
- **Reproduction**: `py -3.12 -m pytest tests/unit/test_gate_paper_thresholds.py -q` 后检查 fixtures/sample_paper_project/paper/main.pdf 不存在。
- **Proposed fix**: 复制 fixture 到 tmp_path 再运行 gate。
- **Regression risk**: 低。
- **Test required**: 无（重构现有测试）。

---

### G-012 [MEDIUM] 测试静默跳过依赖"仓库静态 fixture 在场"——fixture 缺失时绿变 skip 而非红

- **File**: `tests/unit/test_aggregate_scores.py`（31/36/43/50/57/65 六处 skipTest）、`tests/unit/test_gate_paper_thresholds.py`（36/48）、`tests/e2e/test_pipeline.py`
- **Function-Symbol**: 各 setUpClass / has_proj 守卫
- **Line**: 见上
- **Observed behavior**: 多个测试用"项目/文件存在"做前置，不存在即 `skipTest`。本次因 fixture 在场未触发，但**fixture 一删，这些测试静默变 skip，套件仍全绿**。
- **Expected behavior**: 测试数据缺失应报 ERROR/FAIL（setup 失败），不得以 skip 掩盖。
- **Why it matters**: 静默 skip 模式让 CI 可以在"测试对象不存在"时仍绿，是 FAKE 测试的温床。
- **Evidence**: 全测试 grep "skipTest|pytest.skip" 命中 15 处，其中 12 处为"对象不存在"型。
- **Reproduction**: 临时重命名 fixtures/sample_incomplete_project → 套件仍绿（6+ 测试变 skip）。
- **Proposed fix**: 将"对象不存在"改为 `pytest.fail` 或在 conftest 统一 fixture 生成。
- **Regression risk**: 中。
- **Test required**: fixture 完整性自检测试。

---

### G-013 [MEDIUM] P1 系列"真实 e2e"依赖外部手写 fixture 注入，LLM/agent 建模侧从未被测

- **File**: `tests/integration/test_p1_vs001_e2e.py`、`test_p1_m3_competition.py`、`test_p1_m4_guided_vs_unguided.py`
- **Function-Symbol**: 各 `make_session` / `inject_candidates` / `vs001_fixtures` / `m3_fixtures`
- **Line**: 各文件头部 docstring（如 test_p1_vs001_e2e.py:17-19 "LLM-free：M1/M2 MODEL_IR 与 C1/C2 代码由外部 Model Constructor 手写注入"）
- **Observed behavior**: 这些 HIGH 信任 e2e 的输入（MODEL_IR/code）全部来自 `research/P15/*/vs001_fixtures.py`、`m3_fixtures.py` 的**手写常量**。测试验证的是 runtime 回路（登记/执行/验证/选型/replay）在已知正确输入下的行为；**LLM 建模（从赛题到 MODEL_IR）这一真实生产环节零覆盖**——生产管线中的 model-builder agent 产出的 MODEL_IR 质量、正确性没有任何测试。
- **Expected behavior**: 至少应有针对建模 agent 输出契约的验证测试（MODEL_IR schema + 语义合理性），或明确声明建模侧由人工评审兜底。
- **Why it matters**: "系统真的能建模吗"这一最终问题，测试没有回答——只回答了"给对了模型，runtime 能跑对吗"。
- **Evidence**: 三个文件 docstring 均声明 LLM-free 注入；`vs001_fixtures.py` 为手写常量。
- **Reproduction**: 删除 fixtures 后 P1 测试 FAIL（依赖外部路径），而建模 agent 输出无对应测试。
- **Proposed fix**: 增加对 model-builder 产物（真实或 golden）的 MODEL_IR 契约 + 数值一致性测试。
- **Regression risk**: 中。
- **Test required**: `test_model_builder_output_valid_model_ir`（针对建模 agent 的产出）。

---

### G-014 [LOW] 套件无 mock.patch/MagicMock，monkeypatch 84 处均属合理隔离——mock 维度健康

- **File**: 全 tests/
- **Function-Symbol**: —
- **Line**: —
- **Observed behavior**: 0 处 mock.patch / MagicMock / Mock(；84 处 monkeypatch 集中在 env 删除（`monkeypatch.delenv`）、config 替换（`_load_config`）、文件系统 stub（fake_root）。核心执行路径无 mock。
- **Expected behavior**: 维持现状。
- **Why it matters**: 反作弊审计中"mock 掩盖真实 runtime"这一项**干净通过**——这是套件最大的优点，值得记录。
- **Evidence**: 全量正则扫描 0/0/0/84。
- **Reproduction**: 静态扫描即可。
- **Proposed fix**: 无。
- **Regression risk**: 无。
- **Test required**: 无。

---

### G-015 [MEDIUM] 五轴回归测试用硬编码锚点且允许缺失指标静默跳过——method_selection/innovation 锚定 0

- **File**: `tests/regression/test_non_regression_contract.py`
- **Function-Symbol**: `TestNonRegressionContract.test_quality_axis`
- **Line**: 37-49（anchor 字典）、50-52（`if v is None: continue`）
- **Observed behavior**: anchor = `{decomposition:100, method_selection:0, model_correctness:70, experiment_validity:100, validation_reliability:100, innovation:0, end_to_end:71}`；指标缺失时 `continue`（不扣分）。method_selection 与 innovation 两轴被锚定为 **0** 且作为可接受基线。
- **Expected behavior**: 锚点应来自已验证的实测基线而非拍脑袋；缺失指标应 FAIL 而非跳过；0 分能力轴应在报告中显式标记为"能力缺失"。
- **Why it matters**: 回归门禁把"方法选型=0、创新=0"锁死为合法状态，与 G-005（recs[0] 硬编码）互相印证：**系统知道这两项能力为 0，且用测试把它固化**。
- **Evidence**: 直读 line 37-52；本次运行未 skip（research/bench-m4-2000c/work/e2e_metrics.json 存在）。
- **Reproduction**: `py -3.12 -m pytest tests/regression/test_non_regression_contract.py::TestNonRegressionContract::test_quality_axis -q` → passed。
- **Proposed fix**: 0 分轴改为 FAIL 或显式豁免登记；缺失指标改 FAIL。
- **Regression risk**: 高（会暴露真实能力缺口，但这是正确的方向）。
- **Test required**: anchor 真实性审计 + 缺失指标 FAIL 测试。

---

### G-016 [LOW] 并行/串行等价性与崩溃恢复有真实测试，机制层覆盖良好

- **File**: `tests/integration/test_runtime_session.py::test_parallel_session_same_result`、`test_resume_after_crash_skips_completed`；`tests/unit/test_crash_consistency.py`
- **Function-Symbol**: RuntimeSession / engine_progress 原子写
- **Line**: test_runtime_session.py:70-75, 108-122
- **Observed behavior**: 并行 max_workers=4 与串行结果等价断言；崩溃后 resume 从进度文件恢复断言；engine_progress 原子写断言。均为真实机制测试。
- **Expected behavior**: 维持。
- **Why it matters**: 记录套件的机制层信任度，避免报告显得全盘否定——**问题集中在内容真实性层，不在机制层**。
- **Evidence**: 直读 + 实跑通过。
- **Reproduction**: 无需。
- **Proposed fix**: 无。
- **Regression risk**: 无。
- **Test required**: 无。

---

## 6. 核心结论

1. **套件机制层可信，内容层不可信。** execution/validation/engine 的机制测试（约 54% 抽样）真实执行、真实断言数值；但建模产出、证据真实性、claim 内容、默认管线交付物四个内容层全部被占位/结构/存在性断言覆盖。
2. **最危险的三个测试不是"没测"，而是"把错误行为断言为正确"**：test_runtime_session 断言占位管线 validated；test_e2e_metrics 断言 legacy pointer 豁免（structural_pass=None）；test_non_regression_contract 把 method_selection=0 锚定为基线。这三处让 911 绿成为"系统按预期不工作"的证明。
3. **e2e 目录名不副实。** 名义端到端测试 3/4 核心断言是占位 skip；真正的 e2e 能力集中在 P1 注入式测试，但那不覆盖建模侧。
4. **AGENTS.md 的 758/11 基线与实际 911/4 不符**，且仓库自身 commit 已确认 911。
5. **mock 维度干净**（0 mock.patch），这是套件的真实优点，但与"测试信任分 69.2"不矛盾——信任缺口来自占位与浅断言，而非 mock。

**一句话审计结论**：这套测试能证明"运行时机制在受控输入下工作"，**不能**证明"默认建模-证据-论文管线产出真实可信的结果"——而后者恰是数学建模竞赛交付的核心。

---

## 7. 附录：单文件独立运行验证（import side effect）

| 文件 | 独立运行结果 | 结论 |
|---|---|---|
| tests/integration/test_runtime_session.py | 9 passed in 1.96s | 无跨文件依赖 |
| tests/unit/test_aggregate_scores.py | 6 passed in 0.15s | 无跨文件依赖 |
| tests/unit/test_gate_paper_thresholds.py | 2 passed in 6.90s | 无跨文件依赖，但有 fixture 副作用 |

结论：未发现"依赖其他 test 的 import side effect"的测试；但全部测试依赖 conftest 全局 chdir（G-007）。

## 8. 附录：审计执行记录

- 完整套件实跑 2 次：`py -3.12 -m pytest tests -q`（65.97s）与 `-rs`（68.03s），结果一致：911 passed / 4 skipped。
- 全量静态扫描：mock.patch=0，MagicMock=0，Mock(=0，monkeypatch=84，skip 标记=15 处（12 处"对象不存在"型 + 3 处 e2e 占位）。
- 已知问题核实：selection.py:60（确认）、evidence_gate 零数值（确认）、21 validator 死代码（确认，0 import）、claim 占位符（确认，0 测试覆盖）、默认路径不产 MODEL_IR（确认，且被测试编码为豁免）。
- 24 个测试逐一追踪 test→function→production→side effect（见 §3）。
- 未修改任何测试或代码文件（只读审计；仅创建本报告）。
