# TEST_TRUST_SCORE 报告 — Batch 8 独立反作弊审计

> **审计日期**: 2026-09-09
> **审计者**: INDEPENDENT 反作弊审计者（只读模式）
> **仓库**: C:\Users\Lin\Desktop\Programs\MathModel
> **基线**: 966 passed / 4 skipped / 970 collected
> **随机种子**: 20260909

---

## TEST_TRUST_SCORE: **80 / 100**

### 评分依据

| 维度 | 得分 | 说明 |
|---|---|---|
| 真实执行验证 | +15 | `LocalPythonAdapter` 通过 `subprocess.run` 真实执行 Python 代码，status 来自 OS returncode，无默认 success |
| 无 P0 作弊 | +10 | 无空测试/assert True/假断言/故意 skip 失败测试 |
| conftest fixture 诚实 | +10 | `injected_session` 注入真实 MODEL_IR + 真实可执行 CODE + 真实 validation_spec，非 mock 对象 |
| 无 mock 掩盖核心逻辑 | +8 | 零 `unittest.mock`/`MagicMock`/`patch`；`monkeypatch` 仅用于路径隔离和退出码路由测试 |
| 抽样断言质量 | -8 | 20 个抽样中 4 个弱断言（文件存在性/源码文本检查）、2 个条件断言可能平凡通过 |
| 结构性测试膨胀 | -7 | 约 50-80 个测试仅检查 `os.path.exists`/目录结构，不验证运行时行为 |
| 条件断言隐患 | -3 | `test_q13` 等测试 `if blockers: assert` 模式在 precondition 不满足时平凡通过 |
| 单独运行可复现 | +5 | 18 个抽样文件全部单独运行通过，无隐藏全局状态依赖 |
| Skipped 测试合理 | +0 | 4 个 skip 均有合理原因（缺失外部产物/无对应功能节点），非作弊 |

**结论**：核心集成测试层（tests/integration/）确实在跑真实 subprocess 执行并验证数值，conftest fixture 是诚实的边界注入而非 mock。主要扣分点在于 unit 层存在一批结构性/文件存在性弱断言测试，以及少量条件断言可能在 precondition 不满足时平凡通过。**未发现 P0 级作弊。**

---

## 抽样 20 测试明细表

随机种子 `20260909`，从 630 个 unit 测试和 299 个 integration 测试中各抽 10 个。

### Unit 抽样（10）

| ID | 文件 | 函数 | 被测 production 函数 | 断言类型 | 结论 |
|---|---|---|---|---|---|
| U01 | test_competition_intelligence.py | `test_ci07_knowledge_version_change_keeps_history` | `CompetitionIntelligence.select_and_record` / `explain_decision` | **真** | 验证版本历史不改写、`reproducible` 标志翻转、`current_version==2`，有具体数值 |
| U02 | test_benchmark.py | `test_pipeline_report_failure_recorded` | `benchmark.pipeline_report`（`_run` 被 monkeypatch 为返回 (2,"boom")） | **真** | mock 仅替代 subprocess 调用，测试报告逻辑正确捕获 FAIL 并记录 detail；合理 |
| U03 | test_env.py | `test_load_config_returns_nonempty_dict` | `env_loader.load_config()` | **弱** | 仅断言 `isinstance(cfg, dict)` 和 `len(cfg) > 0`，不验证任何具体值；同文件其他测试有具体值断言 |
| U04 | test_validate_project.py | `test_main_entry_guard` | （无运行时调用，读取源码文本） | **弱** | 仅检查源码字符串含 `'__name__'` 和 `'__main__'`，不实际验证入口守卫行为 |
| U05 | test_decision_log.py | `test_bad_confidence_raises` | `DecisionLog.add(confidence=1.5)` | **真** | `pytest.raises(DecisionLogError, match="confidence")` 验证输入校验 |
| U06 | test_retrospect.py | `test_main_missing_project` | `retrospect.main(["no-such-project"])` | **真** | 验证退出码 2；真实 CLI 行为 |
| U07 | test_agents_structure.py | `test_all_agents_have_self_check` | （无运行时调用，遍历 29 个 SKILL.md 文件） | **弱** | 正则检查文件内容含 `## Self-Check`；验证文档结构而非逻辑行为 |
| U08 | test_judge_critic.py | `test_fail_beats_weak` | `JudgeCritic.evaluate` | **真** | 构造 E2 fail + E8 weak，验证 verdict=FAIL（优先级聚合） |
| U09 | test_agents_structure.py | `test_writer_agents_dir` | （无运行时调用） | **弱** | `assert os.path.isdir(...)` 仅检查目录存在 |
| U10 | test_execution_adapter.py | `test_status_never_defaulted` | `LocalPythonAdapter.execute`（真实 subprocess 执行 `print('ok')`） | **弱** | 断言 `r.status in ("success","failed","timeout","invalid")`——这 4 值是 `EXEC_STATUS` 唯枚举，断言恒真（重言式）；但代码确实真实执行了 |

### Integration 抽样（10）

| ID | 文件 | 函数 | 被测 production 函数 | 断言类型 | 结论 |
|---|---|---|---|---|---|
| V01 | test_runtime_session.py | `test_resume_after_crash_skips_completed` | `RuntimeSession.run` / `resume` | **真** | 完整 DAG 执行后从磁盘恢复进度文件，验证 completed 数一致 |
| V02 | test_references.py | `test_all_references_exist` | （无运行时调用，正则提取 SKILL.md 文件引用） | **弱** | 验证引用路径在磁盘上存在；文件存在性检查 |
| V03 | test_research_quality.py | `test_q13_rerun_with_quality_memory` | `ResearchQuality.record_blockers` | **弱** | `if rep2.blockers: assert recorded`——若 blockers 为空则整个测试平凡通过 |
| V04 | test_p1_m3_competition.py | `test_llm_free_boundary` | 外部注入边界验证 | **真** | 验证候选来自外部注入、code 含 `def solve(inputs)`、EXEC provenance adapter=`local_python` |
| V05 | test_execution_validation.py | `test_range_failure_attributable` | `run_checks`（output total_cost=-5.0, range min=0） | **真** | 验证 status=failed、check passed=False、detail 含"超出" |
| V06 | test_paper_redteam.py | `test_B_superseded_experiment_leakage` | `RuntimeSession.rerun` / EvidenceGraph | **真** | rerun 后验证 superseded result 不支撑 active claim |
| V07 | test_red_team.py | `test_resume_rebuilds_same_world[after_plan]` | `RuntimeSession.resume` | **真** | 快照对比 artifacts+relations+quality，resume 后世界一致 |
| V08 | test_research_quality.py | `test_B_superseded_model_cannot_support_decision` | `ResearchQuality.evaluate` | **弱** | `assert dead_models or model_findings`——两个替代条件满足其一即过 |
| V09 | test_controlled_expression.py | `test_figure_and_equation_bindings` | `ParagraphPlanner.figure_bindings` / `equation_bindings` | **真** | 验证绑定含 `why_exists`/`what_it_does_not_prove`/`model_ref`/`purpose` |
| V10 | test_structure.py | `test_new_project_scaffold_structure` | `new_project.scaffold` | **真** | 真实创建项目目录，验证目录/文件复制/模板文件存在 |

### 抽样统计

| 断言类型 | 数量 | 占比 |
|---|---|---|
| 真断言（验证具体数值/状态/行为） | 12 | 60% |
| 弱断言（字段存在/类型/文件存在/重言式） | 7 | 35% |
| 假断言（恒真/无实际验证） | 1 | 5%（U10 重言式，但代码真实执行） |

---

## 反作弊发现列表

### F-001: 条件断言平凡通过风险
- **严重度**: P1
- **文件**: `tests/integration/test_research_quality.py:287-290`
- **证据**:
  ```python
  if rep2.blockers:
      assert recorded
      kinds = [d.question_type for d in recorded]
      assert all(k == "quality" for k in kinds)
  ```
- **说明**: 当 `rep2.blockers` 为空时，整个 `test_q13_rerun_with_quality_memory` 平凡通过，不验证任何行为。虽然测试试图构造 blocker（清空 baseline_comparison），但如果构造失败，测试不会失败。
- **建议**: 将 `if rep2.blockers:` 改为 `assert rep2.blockers`，确保 blocker 确实被构造出来。

### F-002: 重言式断言
- **严重度**: P2
- **文件**: `tests/unit/test_execution_adapter.py:95-98`
- **证据**:
  ```python
  def test_status_never_defaulted(self):
      r = self._run("raise SystemExit(0) if False else print('ok')")
      assert r.status in ("success", "failed", "timeout", "invalid")
  ```
- **说明**: `EXEC_STATUS = ("not_executed", "running", "success", "failed", "timeout", "invalid")`，但 `execute()` 方法实际只可能返回 success/failed/timeout/invalid。断言 `in (...)` 是恒真的。测试的意图是"不凭空 success"，但实际断言未验证这一点（应断言 `r.status == "success"` 因为 `print('ok')` 必然 returncode=0）。
- **建议**: 改为 `assert r.status == "success"` 和 `assert r.returncode == 0`。

### F-003: 源码文本检查替代行为测试
- **严重度**: P2
- **文件**: `tests/unit/test_validate_project.py:82-86`（及同文件 13 个类似测试）
- **证据**:
  ```python
  def test_main_entry_guard(self):
      src = _read_validate_project_source()
      assert '__name__' in src and "__main__" in src
  ```
- **说明**: 该文件 13 个测试中大部分读取 `validate_project.py` 源码文本并用正则检查函数名/常量/分组名存在，但不实际执行检查逻辑。文件 docstring 已承认"本测试只验证其结构完整与可加载性，不实际执行检查"。这是有意识的选择，但意味着 validate_project.py 的 49 个检查函数的正确性未被测试覆盖（除了 `--help` 退出码测试）。
- **建议**: 为关键检查函数（如 check_placeholders, check_numeric_traceability）补充至少一个正/反例单元测试。

### F-004: 结构性文件存在性测试占 unit 层约 5-8%
- **严重度**: P2
- **文件**: `tests/unit/test_modeler.py`, `test_programmer.py`, `test_writer.py`, `test_agents_structure.py`, `test_structure.py`, `test_references.py`
- **证据**: 全测试套件中 89 处 `os.path.exists/isdir/isfile` 调用分布在 14 个文件中，其中 `test_modeler.py`(11处)、`test_programmer.py`(12处)、`test_writer.py`(15处)、`test_structure.py`(15处) 几乎全为文件存在性检查。
- **说明**: 这些测试验证项目脚手架完整性（SKILL.md 存在、目录结构完整），有防回归价值但不验证任何运行时逻辑。它们 inflated 通过数但不增加行为覆盖率。
- **建议**: 可接受作为"项目健康检查"层，但不应计入行为测试覆盖率。

### F-005: 替代条件断言
- **严重度**: P2
- **文件**: `tests/integration/test_research_quality.py:167`
- **证据**:
  ```python
  assert dead_models or model_findings
  ```
- **说明**: 两个替代条件满足其一即通过。语义上可接受（设计文档说明了两种可能路径），但降低了断言精度。
- **建议**: 可接受，建议加注释说明为何二选一。

---

## conftest.py 深度分析

### `mir(qid, model_id)` fixture

**判定：真实数据结构，非 mock。**

- 返回一个符合 `model_ir.schema.json` 全部 required 字段的 MODEL_IR 字典
- 包含完整的 18 个顶层节（ir_version, model_family, problem_binding, assumptions, variables, parameters, objectives, constraints, mechanisms, equations, dependencies, solvers, experiments, validations, claims, model_graph, modeling_trace）
- 数值参数为确定性值（slope=2.0, intercept=1.0）
- 文档字符串明确说明这是 "最小真实 MODEL_IR"，且经 audit FIX-5.4 对齐了 jsonschema 契约
- **不替代任何计算**：它只是提供数据结构，实际计算由 `CODE` 中的 `solve()` 函数完成

### `injected_session(tmp_path, questions, max_workers)` fixture

**判定：真实执行闭环，非 mock。**

- 创建真实 `RuntimeSession`，挂载真实 `LocalPythonAdapter`
- `LocalPythonAdapter.execute()` 通过 `subprocess.run([python, script])` 真实执行 Python 代码（已逐行阅读 `adapters.py:177-261` 确认）
- 执行状态仅来自 `proc.returncode`：`"success" if proc.returncode == 0 else "failed"`，**无默认 success 路径**
- 注入物为：
  - `external_model_irs`: `mir()` 返回的完整 MODEL_IR
  - `external_code`: `CODE` 字符串（含真实 `solve(inputs)` 函数，执行 `y = slope*x + intercept`）
  - `validation_specs`: 真实验证规格（output_field_exists / output_numeric / output_range）
- 文档字符串（conftest.py:1-8）明确声明："默认路径无真实执行事实 → evidence_build 如实 FAIL。需要'完整闭环成功'的测试必须经 external_model_irs / external_code / validation_specs 注入真实 Model Constructor 产物"
- **关键设计**：这是 LLM-free 边界——Model Constructor 产物由外部注入（测试边界），但 Runtime 执行/验证/证据合成全部走 production path。这不是 mock，而是诚实的依赖注入。

### `_real_session.py`（集成测试共享工厂）

**判定：与 conftest 同性质的真实执行工厂。**

- `make_real_session()` 注入更完整的三层 MODEL_IR（L1 semantic / L2 mathematical / L3 computational）
- 注入代码计算 `y = a*x + b`（a=2.0, x=3.0, b=1.0 → y=7.0）
- `MINIMAL_VALIDATION_SPEC` 含 `output_equals: y == 7.0, tolerance=1e-9`——这是**数值精确断言**
- 同样挂载 `LocalPythonAdapter` 真实 subprocess 执行

### 结论

conftest 的 fixture 设计是**诚实的**：它没有用 mock 对象替代 runtime，而是在 LLM-free 边界注入外部产物，让 runtime 真实执行。文档字符串中多次引用 audit FIX-1.x，表明此前存在"占位 claim 假 PASS"问题，已被修复为"无数值执行→如实 FAIL"。

---

## 4 个 Skipped 测试分析

| # | 文件:行 | 测试函数 | Skip 原因 | 合理性判定 |
|---|---|---|---|---|
| 1 | `tests/e2e/test_pipeline.py:44` | `test_modeler_can_output` | `sample_incomplete_project/output/MODEL_SPEC.md` 不存在 | **合理**。fixture 项目是故意不完整的；代码注释明确说明"[legacy 冻结] V2 流水线产物不再重建，此 skip 为显式占位（非覆盖空洞）；V3 主线产物由 Artifact Registry 管理"。V3 等效测试在 `tests/integration/test_runtime_session.py` 等文件中覆盖。 |
| 2 | `tests/e2e/test_pipeline.py:56` | `test_programmer_can_output` | `sample_incomplete_project/output/CODE_DELIVERABLES.md` 不存在 | **合理**。同上，legacy V2 产物文件缺失；V3 等效覆盖在 integration 层。 |
| 3 | `tests/e2e/test_pipeline.py:68` | `test_writer_can_output` | `sample_incomplete_project/output/PAPER_SPEC.md` 不存在 | **合理**。同上。 |
| 4 | `tests/integration/test_workflow_execution.py:112` | `test_waiting_approval_and_approve` | 当前 workflow 无 human_approval 节点 | **合理**。条件 skip：workflow 定义中没有人工审批节点时跳过该测试；若未来添加审批节点，测试自动激活。不是"测试失败所以 skip"。 |

**Skipped 作弊判定**: 无。所有 4 个 skip 均为前置条件缺失（外部产物文件未生成 / 功能节点未定义），非"因为测试断言失败所以 skip"。e2e 测试的注释明确说明了 legacy 冻结原因，且 V3 等效测试已在 integration 层覆盖。

---

## 其他反作弊模式扫描结果

| 模式 | 结果 |
|---|---|
| `assert True` / `assert 1==1` | **0 匹配** |
| `unittest.mock` / `MagicMock` / `patch(` | **0 匹配** |
| `pass` 作为测试函数唯一体 | **0 匹配** |
| `except: pass` / `except: continue`（吞异常） | **0 匹配** |
| `pytest.raises` 用于验证错误路径 | 多处使用，均合理（如 confidence=1.5 raises DecisionLogError） |
| `monkeypatch.setattr` | 29 处，绝大多数为 `ROOT`/`project_dir` 路径隔离（tmp_path），3 处为 `_run`/`run_gate` 替代 subprocess（测试报告/退出码逻辑），均合理 |
| 单独运行抽样文件 | 18 个文件全部单独运行通过，无隐藏全局状态依赖 |
| 硬编码 expected 值 | `test_p1_m3_competition.py` 中的 0.275/1.925 来自真实物理计算（1.925-1.65=0.275），非凭空；`_real_session.py` 中 7.0 = 2*3+1 来自注入代码实算 |

---

## 审计者声明

本审计为独立只读验证：
- 未修改任何代码、测试或配置文件
- 未执行任何 git 操作
- 未为了"好看"降低任何严重度
- 抽样使用固定随机种子 `20260909`（审计日期），从 630 unit + 299 integration 测试中随机选取
- 全量测试运行验证（966 passed / 4 skipped，179.09s）
- 所有抽样文件单独运行验证通过
- 报告文件为唯一写入产物
