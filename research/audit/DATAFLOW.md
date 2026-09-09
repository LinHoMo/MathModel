# MathModel 真实 Dataflow 地图（Batch 0 审计产物）

> **审计基线**：HEAD `d44384c`，2026-09-09
> **方法**：8 个独立只读审计子代理（A-H）逐环节追踪，全部结论附磁盘证据
> **判定标准**：REAL = 有真实代码路径且被生产链调用；GAP = 代码存在但未接线/不完整；FAKE = 占位符/硬编码/伪造

---

## 完整链路状态总览

```
Problem ──▶ Representation ──▶ Candidate Gen ──▶ Candidate Eval ──▶ Selection ──▶ MODEL_IR
  GAP          GAP               REAL(有条件)       FAKE(默认)        FAKE(默认)    REAL(结构)/GAP(实例化)

MODEL_IR ──▶ Model Artifact ──▶ Code Gen ──▶ ExecutionPlan ──▶ Adapter ──▶ subprocess
 GAP            GAP               GAP           REAL            REAL         REAL

subprocess ──▶ ExecutionResult ──▶ Fidelity ──▶ Evidence ──▶ Validation ──▶ Gate ──▶ Decision
   REAL          GAP(门禁)         REAL          PARTIAL       REAL*(部分)   STRUCTURAL   REAL(候选模式)

Decision ──▶ FAIL ──▶ Diagnosis ──▶ Revision ──▶ M2 ──▶ Re-execution ──▶ Compare ──▶ Accept/Reject
  REAL        REAL       GAP          GAP       REAL(部分)     REAL            GAP          GAP
```

---

## 逐箭头 12 问审计

对每一条箭头回答：①谁调用谁 ②输入 ③输出 ④schema ⑤是否真执行 ⑥是否有测试 ⑦测试走不走 production path ⑧失败如何传播 ⑨provenance 在哪 ⑩Git 可追溯 ⑪是否有 fallback ⑫Agent 可伪造字段

---

### 箭头 1：Problem → Problem Representation

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `orchestrator.py:349-392` 加载 `problem_features.json` → `handlers.py:778-788` `do_problem_analysis` 创建 Question artifact |
| 2 | 输入 | 题面文本（字符串）、可选 `problem_features.json` |
| 3 | 输出 | `features` dict（6 键粗画像：problem_types/has_data/sample_size/problem_title/...）+ Question artifact（title=纯标签） |
| 4 | schema | V2 `question_spec.schema.json`（146 行完整契约）存在但 **V3 从不读取**；V3 无 representation schema |
| 5 | 是否真执行 | **GAP** — V3 运行时只建粗画像 + 纯标题 Question，**从不读题面内容**；结构化表示仅在 legacy V2 路径 |
| 6 | 是否有测试 | 无针对 V3 representation 的测试 |
| 7 | 测试走 production path | N/A |
| 8 | 失败如何传播 | 缺失 features 时回退 `_LEGACY` 默认画像并打 `_features_source=legacy_default` 标记（`handlers.py:83-85`），**不报错** |
| 9 | provenance | Question artifact 无 provenance；features 来源标记仅在 handler 内存 |
| 10 | Git 可追溯 | 是（代码在 git 中） |
| 11 | 是否有 fallback | **是** — `_LEGACY` 默认画像 fallback，掩盖题面缺失 |
| 12 | Agent 可伪造字段 | `problem_features.json` 可被任意写入，features 全字段可伪造 |

**判定：GAP** — 问题本体从未进入 V3 认知管线。

---

### 箭头 2：Representation → Candidate Generation

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `handlers.py` `do_model_construction` → `CandidateArena.generate_candidates`（`candidates.py:177-302`） |
| 2 | 输入 | features dict + 方法卡检索结果（`MethodRec` 列表） |
| 3 | 输出 | 最多 4 个候选（baseline/improved/hybrid/innovation），composition 有实质差异 |
| 4 | schema | 候选结构为 dataclass（`candidates.py`），无 JSON schema |
| 5 | 是否真执行 | **REAL（有条件）** — `generate_candidates` 真实生成 2-4 个组合有差异的候选；但**生产路径生成后即弃**（仅 top-1 用于实验规划） |
| 6 | 是否有测试 | `tests/integration/test_p1_m3_competition.py` 覆盖候选竞技场（20 passed） |
| 7 | 测试走 production path | **否** — 测试通过外部 fixture 注入 `external_candidates`，生产 orchestrator 零接线 |
| 8 | 失败如何传播 | 候选生成失败不阻断；候选分数是启发式常量（非评估结果） |
| 9 | provenance | 候选的 `score` 来自检索分派生 + 硬编码增量，**不是模型执行/评估的结果** |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 无候选时返回空列表，下游取 `cands[0]` 可能 IndexError（未审计到防护） |
| 12 | Agent 可伪造字段 | `external_candidates` 注入键可被任意 Agent 写入，候选全字段可伪造 |

**判定：REAL（有条件）/ FAKE（默认路径无评估）**

---

### 箭头 3：Candidate Generation → Candidate Evaluation

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | 候选模式：`handlers.py:376-441` `execute_code` → `LocalPythonAdapter` → `_register_vr`（`handlers.py:457-489`）→ `run_numeric_validation` |
| 2 | 输入 | 候选 MODEL_IR + 代码（需外部注入） |
| 3 | 输出 | EXEC artifact（真实 subprocess 结果）+ VR artifact（数值验证结果） |
| 4 | schema | EXEC/VR 为 registry artifact，无 data schema 门禁 |
| 5 | 是否真执行 | **FAKE（默认）/ REAL（候选模式）** — 默认路径无任何评估（无 code/exec/VR）；候选模式有真实数值验证 |
| 6 | 是否有测试 | 候选模式测试真实（`test_p1_m3_competition.py:135-148` 断言坏候选 VR 判 failed） |
| 7 | 测试走 production path | 否 — 需外部注入 |
| 8 | 失败如何传播 | 候选模式：VR failed 真实记录；默认路径：无评估 = 无失败 |
| 9 | provenance | VR artifact 含 `verified_by` 边指向 EXEC；默认路径无 provenance |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 默认路径"不评估"本身就是最大的 fallback |
| 12 | Agent 可伪造字段 | `external_model_irs` 注入可伪造候选；VR data 无 schema 门禁可伪造 |

**判定：FAKE（默认生产链）**

---

### 箭头 4：Candidate Evaluation → Selection

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | 默认：`handlers.py:848-849` → `MethodArena.select`（`selection.py:46-121`）；候选模式：`do_model_selection_decision`（`handlers.py:639-740`） |
| 2 | 输入 | 默认：检索推荐列表 `recs`；候选模式：候选 VR 指标表 |
| 3 | 输出 | 默认：`SelectionOutcome(chosen=recs[0].card.card_id)`；候选模式：decision artifact（含 reasoning/evidence_ids/ranked） |
| 4 | schema | decision artifact 无 schema 门禁 |
| 5 | 是否真执行 | **FAKE（默认）** — `selection.py:60` `chosen=recs[0]` **硬编码**，confidence 由检索分换算；候选模式 REAL（基于 VR 机械排序） |
| 6 | 是否有测试 | `test_model_selection.py::test_select_returns_shortlist` — 但**只断言格式，不断言 chosen 是否最优**（G-006） |
| 7 | 测试走 production path | 是（默认路径），但断言不捕捉硬编码 |
| 8 | 失败如何传播 | 无失败概念 — `recs[0]` 永远有值 |
| 9 | provenance | 默认：无 evidence 支撑；候选模式：decision.data.reasoning 引用真实 VR id |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | `recs[0]` 本身就是 fallback（取第一个而非评估最优） |
| 12 | Agent 可伪造字段 | 检索结果可被 knowledge 层操纵；候选模式 `external_candidates` 可伪造 |

**判定：FAKE（默认）— 系统无法回答"为什么选这个模型而不是另外两个"**

---

### 箭头 5：Selection → MODEL_IR

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `handlers.py:891-930` `do_model_construction` → `construct_model_ir` / `construct_candidate_mirs` |
| 2 | 输入 | 选中方法卡 ID + 可选 `external_model_irs` 注入 |
| 3 | 输出 | 默认：**无 MODEL_IR**（只登记 assumption artifact）；注入模式：MIR artifact（18 字段三层结构） |
| 4 | schema | `ModelIR` dataclass（`model_ir.py:70-99`）18 required 字段 + `model_ir.schema.json`（嵌套契约完整）；**但 `validate_model_ir` 注释自曝"历史：register 从不校验"** |
| 5 | 是否真执行 | **REAL（结构）/ GAP（实例化）** — 结构完整含 equations/mechanisms/solvers/validations；但**默认生产路径从不实例化**（实测 3 个真实项目 MIR=0） |
| 6 | 是否有测试 | MODEL_IR schema 测试真实（HIGH 信任）；但无"默认路径必须产 MIR"的测试 |
| 7 | 测试走 production path | schema 测试走；实例化测试需注入 |
| 8 | 失败如何传播 | **不传播** — 无注入时 `construct_model_ir` 返回 None，节点仍以 `PASS("登记 N 条假设")` 结束（B-002） |
| 9 | provenance | MIR artifact provenance 默认为 `{}`/`None`（实测）；无 `code_mapping` 字段（全仓 0 匹配） |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | **是** — 无注入时 fallback 到"只登记假设"，节点 PASS |
| 12 | Agent 可伪造字段 | `external_model_irs` 注入可伪造完整 MIR；registry.create 无 data schema 门禁 |

**判定：GAP — MODEL_IR 结构足以生成可执行模型，但生产链从不生成它**

---

### 箭头 6：MODEL_IR → Model Artifact

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `handlers.py:865-872` 创建 model artifact |
| 2 | 输入 | 选中方法卡 ID + shortlist |
| 3 | 输出 | V3 model artifact = `{card_id, family, shortlist}` **薄壳** |
| 4 | schema | V2 `model_artifact.schema.json` 存在（要求 candidate_models minItems=2, selection_reason minLength=30）但**全仓无强制执行点** |
| 5 | 是否真执行 | **GAP** — model artifact 是方法卡 ID 薄壳，provenance 空，不含 equations/mechanism/solver |
| 6 | 是否有测试 | 无针对 model artifact 完整性的测试 |
| 7 | 测试走 production path | N/A |
| 8 | 失败如何传播 | 无失败 |
| 9 | provenance | 实测 `M001 provenance={}`；谱系只能沿 graph 边隐式重建 |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 薄壳本身就是 fallback |
| 12 | Agent 可伪造字段 | card_id/family/shortlist 全可伪造 |

**判定：GAP**

---

### 箭头 7：Model Artifact → Code Generation

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `codegen.py` — 但**明确声明"core 永久 LLM-free：本模块不生成代码"**（`codegen.py:4-5`） |
| 2 | 输入 | 外部 Agent 交付的代码 + `model_id/solver_id/output_mapping` |
| 3 | 输出 | 登记 CODE artifact + 可选执行 |
| 4 | schema | CODE artifact 无 data schema 门禁 |
| 5 | 是否真执行 | **GAP** — harness 内不存在 MODEL_IR→code 的机械生成路径；代码由外部 Agent 交付后经 `register_code` 登记 |
| 6 | 是否有测试 | codegen 测试真实（测试 register→execute→fidelity 管线） |
| 7 | 测试走 production path | **否** — codegen.py+fidelity.py 是平行管线，仅测试/CLI 可达，不在 runtime 生产链上（A-005） |
| 8 | 失败如何传播 | 无代码时 `generate_code` 返回 `[]`，下游 no-op |
| 9 | provenance | CODE artifact 含 code_hash（真实 sha256）；但无"从 MODEL_IR 派生"的校验 |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 无代码 = no-op，不报错 |
| 12 | Agent 可伪造字段 | code 文本可任意写入；output_mapping 可伪造（影响 fidelity） |

**判定：GAP — 生成侧真实性完全依赖外部 Agent，harness 无法机械保证"代码执行了 MODEL_IR 声明的模型"**

---

### 箭头 8：Code Generation → ExecutionPlan

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `adapters.py:72-83` `ExecutionPlan` dataclass 构造 |
| 2 | 输入 | model_id/code/inputs/timeout_seconds/workdir/env/adapter/meta |
| 3 | 输出 | ExecutionPlan 对象 |
| 4 | schema | 普通 dataclass，无校验 |
| 5 | 是否真执行 | **REAL** — 结构真实 |
| 6 | 是否有测试 | execution runtime 测试覆盖 |
| 7 | 测试走 production path | 是 |
| 8 | 失败如何传播 | 构造失败抛异常 |
| 9 | provenance | plan 含 model_id 引用 |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 无 |
| 12 | Agent 可伪造字段 | plan 全部字段可任意构造（无校验"从 MODEL_IR 派生"） |

**判定：REAL（但无派生校验）**

---

### 箭头 9：ExecutionPlan → Execution Adapter → subprocess

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `LocalPythonAdapter.execute`（`adapters.py:177-261`）→ `subprocess.run` |
| 2 | 输入 | ExecutionPlan（含 code 文本） |
| 3 | 输出 | 临时 .py 文件 → subprocess → stdout/stderr/returncode |
| 4 | schema | `ExecutionResultData` dataclass（`adapters.py:40-47`）含 execution_id/model_id/status/outputs/stdout/stderr/returncode/duration_ms/code_hash/environment_hash/... |
| 5 | 是否真执行 | **REAL** — 写临时 .py → `subprocess.run([python, script], capture_output=True, timeout=..., cwd=..., env=...)`（L198-202），真 subprocess 非模拟 |
| 6 | 是否有测试 | `test_execution_runtime.py` 真实 subprocess 测试（HIGH 信任：断言 status=success + value=={"answer":42}；失败代码断言 failed + stderr 含真实报错） |
| 7 | 测试走 production path | **是** — 真 LocalPythonAdapter + 真 subprocess |
| 8 | 失败如何传播 | returncode≠0 → status="failed"；timeout → status="timeout"；语法错误 → status="invalid"。**但** `do_model_execution` 无条件 PASS（`handlers.py:525-534`），失败不阻断节点 |
| 9 | provenance | ExecutionResultData 含 code_hash=sha256(code)、environment_hash、started_at/finished_at、duration_ms=perf_counter 差值 |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 异常分支直接构造 status="invalid"（合法）；但 `do_model_execution` 的 PASS 是 fallback 掩盖 |
| 12 | Agent 可伪造字段 | **ExecutionResultData 是公开 dataclass，任何持有 registry 的 Agent 可直接构造**（C-001）；status/outputs/code_hash/duration_ms 全可伪造 |

**判定：REAL（subprocess 执行真实）/ GAP（ExecutionResult 创建无门禁，Agent 可伪造）**

---

### 箭头 10：subprocess → ExecutionResult

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | adapter 返回 `ExecutionResultData` → `registry.create("execution_result", data=...)` |
| 2 | 输入 | adapter 真实输出（stdout JSON 解析、returncode、duration） |
| 3 | 输出 | EXEC artifact（registry 中） |
| 4 | schema | **无 data schema 门禁** — `Artifact.validate` 只查 ID/type/status 枚举，**不校验 data 内容**（C-001） |
| 5 | 是否真执行 | **GAP** — harness 创建点真实（来自 adapter），但**任何 Agent 可绕过 adapter 直接 registry.create** |
| 6 | 是否有测试 | execution runtime 测试覆盖真实路径；但无"伪造 data 必须被拒绝"的测试 |
| 7 | 测试走 production path | 是（真实路径） |
| 8 | 失败如何传播 | EXEC status=failed 真实记录；但 `_results_of` 不过滤 failed（C-008），claim 可构建在失败执行之上 |
| 9 | provenance | EXEC artifact data 含完整字段（当由 adapter 创建时）；伪造时 provenance 可任意写 |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | registry.create 无门禁 = 最大 fallback |
| 12 | Agent 可伪造字段 | **全部 EXEC data 字段可伪造**：status/outputs/stdout/stderr/returncode/duration_ms/code_hash/environment_hash/execution_id（C-001 清单） |

**判定：GAP — "ExecutionResult 只能由 substrate 创建"铁律的直接缺口**

---

### 箭头 11：ExecutionResult → Fidelity

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `fidelity.py:119-157` 从 EXEC outputs + output_mapping 计算 |
| 2 | 输入 | EXEC outputs（dict）+ output_mapping（声明的期望输出） |
| 3 | 输出 | fidelity_report（passed/total/score + checks 数组） |
| 4 | schema | fidelity_report 无 schema 门禁 |
| 5 | 是否真执行 | **REAL** — 基于真实 outputs 机械计算 passed/total，非硬编码 |
| 6 | 是否有测试 | fidelity 测试真实（HIGH 信任） |
| 7 | 测试走 production path | 是 |
| 8 | 失败如何传播 | fidelity misaligned 真实记录；但可被伪造 outputs 间接操纵（C-001 连带） |
| 9 | provenance | fidelity_report 含 checks 数组（每项检查名+通过状态）；K003 旧版曾剥离 checks（C-004） |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 无 output_mapping 时 → unverifiable（合理） |
| 12 | Agent 可伪造字段 | fidelity_score 不能直接伪造（由计算产生），但**可通过伪造 outputs 间接操纵**；output_mapping 可伪造宽松映射 |

**判定：REAL（但可被伪造 outputs 间接操纵）**

---

### 箭头 12：Fidelity → Evidence

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `handlers.py` `do_evidence_build`（L1199-1235）创建 claim + supports 边 |
| 2 | 输入 | experiment results（含 EXEC/VR/fidelity） |
| 3 | 输出 | Claim artifact + Evidence Graph 边（`{from, relation, to, at}`） |
| 4 | schema | 无独立 Evidence 实体；"证据"=Registry artifact + Graph 边；claim 无 schema 门禁 |
| 5 | 是否真执行 | **PARTIAL** — 边真实写入；但 claim statement = `"{qid} 结论"` **显式占位符**（`handlers.py:1219-1227`，`placeholder: True`），全仓无代码填充真实结论 |
| 6 | 是否有测试 | **零测试覆盖 claim 占位符**（G-003）；evidence_gate 测试只验证结构行为 |
| 7 | 测试走 production path | evidence_gate 测试走，但不验证内容真实性 |
| 8 | 失败如何传播 | 占位 claim 自带 supports 边骗过 evidence gate；`test_runtime_session` 断言 `claims_supported=2`（G-003） |
| 9 | provenance | claim 有结构 provenance（supports 边/experiment_refs）但**内容是占位符**；图边不携带 code_hash/output/environment |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 占位符本身就是 fallback |
| 12 | Agent 可伪造字段 | claim statement/claim_type/execution_status 全可伪造；Agent handler 可直接创建证据关系（不强制 execution substrate） |

**判定：PARTIAL / FAKE（claim 内容）— 占位符经 director→narrative_ir→projection 流入论文大纲"结果与分析"节**

---

### 箭头 13：Evidence → Validation

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | 真实路径：`run_numeric_validation`（`validation.py`）；声称路径：`core/validators/modules/*` 21 个分层 validator |
| 2 | 输入 | EXEC outputs + 模型声明（constraints/domains/objectives） |
| 3 | 输出 | VR artifact（mathematical_valid/constraint_violation_max/objective_value/...） |
| 4 | schema | VR 无 data schema 门禁 |
| 5 | 是否真执行 | **REAL*（仅两条路径）** — `run_numeric_validation` 真算但**硬编码单一问题**（pair_distances/head_speeds/positions 键名）；21 个 modules validator **是死代码**（全仓零 import，validate.py 只做"类名字符串存在性"检查）（D-003） |
| 6 | 是否有测试 | VR 测试真实；modules validator **零测试**（G-006） |
| 7 | 测试走 production path | VR 走；modules 不走（死代码） |
| 8 | 失败如何传播 | VR failed 真实记录；但 modules 死代码意味着 L2 Mathematical 层从未执行 |
| 9 | provenance | VR 含 `verified_by` 边指向 EXEC |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | modules 死代码 = "声称有验证、实际未执行"的 fallback |
| 12 | Agent 可伪造字段 | VR data 无 schema 门禁可伪造 |

**判定：REAL*（仅数值验证，且硬编码单问题）/ FAKE（L2 分层验证未接线）**

---

### 箭头 14：Validation → Gate

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `evidence_gate.py:87-181` `evaluate(registry, graph, min_coverage)` |
| 2 | 输入 | registry + evidence graph |
| 3 | 输出 | GateReport（PASS/WEAK/FAIL + E1-E8 明细） |
| 4 | schema | GateReport 为 dataclass |
| 5 | 是否真执行 | **STRUCTURAL ONLY** — E1-E8 全部只查边存在性/生命周期/tags，**零数值计算**（D-001）；不校验 outputs 非空、不校验 execution status、不做 ground truth 比对 |
| 6 | 是否有测试 | `test_evidence_gate.py` 只验证结构判定，不验证数值真实性（G-004） |
| 7 | 测试走 production path | 是，但断言维度缺失 |
| 8 | 失败如何传播 | WEAK 也被 handler 判 FAIL（D-004，与文档语义矛盾）；not_executed 链可结构 PASS（E6 只查 lifecycle draft，不查 data.status） |
| 9 | provenance | GateReport 含 E1-E8 明细，但都是结构指标 |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | "结构 PASS = 有证据"是概念性 fallback |
| 12 | Agent 可伪造字段 | 边可任意创建（无 substrate 强制），tags 可任意打 |

**判定：STRUCTURAL — "证据门禁通过"不等于"有真实证据"**

---

### 箭头 15：Gate → Decision

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | 候选模式：`do_model_selection_decision`（`handlers.py:639-740`）；默认：无 decision |
| 2 | 输入 | 候选 VR 指标表 + gate 结果 |
| 3 | 输出 | decision artifact（chosen/alternatives/criteria/evidence_ids/reasoning/confidence/ranked） |
| 4 | schema | decision artifact 无 schema 门禁；`DecisionLog`（`decisions/log.py`）结构完整 |
| 5 | 是否真执行 | **REAL（候选模式）** — 基于 VR 指标机械排序（mathematical_valid→constraint_violation_max 升序→...），reasoning 含具体数值；默认模式无 decision |
| 6 | 是否有测试 | m3 competition 测试断言 `chosen == min(cv, key=cv.get)`（真实） |
| 7 | 测试走 production path | 候选模式需注入 |
| 8 | 失败如何传播 | 无 VR 证据时 `chosen="UNSELECTED", confidence=0.0`（合理） |
| 9 | provenance | decision.evidence_ids 指向 VR artifact；reasoning 引用真实 VR id 与数值 |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 默认路径无 decision = fallback |
| 12 | Agent 可伪造字段 | decision data 无 schema 门禁，但 reasoning 需引用存在的 VR id |

**判定：REAL（候选模式，本链最健康环节）/ GAP（默认模式）**

---

### 箭头 16：Decision → FAIL → Failure Diagnosis

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | `engine.py:_handle_failure` → retry → on_fail → reset_to |
| 2 | 输入 | 节点 FAIL 状态 |
| 3 | 输出 | retry / rollback / blocked |
| 4 | schema | 无 diagnosis 数据结构 |
| 5 | 是否真执行 | **REAL（FAIL 检测）/ GAP（诊断）** — FAIL 真实判出（VR failed 4/5 检查）；但**无任何诊断代码**，engine 只做 retry→rollback，不分析失败原因 |
| 6 | 是否有测试 | e2e 测试覆盖 FAIL→retry；无 diagnosis 测试 |
| 7 | 测试走 production path | 是 |
| 8 | 失败如何传播 | retry 耗尽 → blocked；无诊断输出 |
| 9 | provenance | 无 diagnosis artifact |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | retry 本身是 fallback；无诊断 = "失败了但不知道为什么" |
| 12 | Agent 可伪造字段 | N/A（无 diagnosis 字段） |

**判定：GAP — p1-vs001 的"诊断"是 runner 里硬编码字符串，非系统产出**

---

### 箭头 17：Failure Diagnosis → Revision Proposal → M2

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | 无系统机制；实验脚本 `p1_vs001_runner.py` 手工构造 |
| 2 | 输入 | 硬编码 diagnosis + 预写 M2 MODEL_IR 文件 |
| 3 | 输出 | M2 MIR artifact + `revision_of` 边 |
| 4 | schema | MIR schema 完整（同箭头 5）；revision 边为 graph `revision_of`（弱边、不传播） |
| 5 | 是否真执行 | **GAP** — 无"基于失败证据生成修订方案"的机制；M2 全部来自预写 fixtures；`registry.supersede` 已实现但 core 无调用点（E-007） |
| 6 | 是否有测试 | e2e 测试覆盖注入式 M2 执行；无"自动修订"测试 |
| 7 | 测试走 production path | 需外部注入 |
| 8 | 失败如何传播 | 无修订 = 流程结束或 blocked |
| 9 | provenance | `revision_of` 边真实存在（p1-vs001: MIR003→MIR002）；但 `supersedes` 边方向在两套路径中**相反**（E-002）；无 `changed_components` 结构化字段 |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 预写 fixtures = 最大 fallback |
| 12 | Agent 可伪造字段 | `external_model_irs` 注入可伪造 M2 + revision_of 边 |

**判定：GAP — M2 谱系边存在，但修订提案完全由外部人工/脚本驱动**

---

### 箭头 18：M2 → Re-execution

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | 同箭头 9-10（LocalPythonAdapter → subprocess → EXEC） |
| 2 | 输入 | M2 代码（外部注入） |
| 3 | 输出 | 新 EXEC artifact（真实 subprocess） |
| 4 | schema | 同箭头 10（无 data 门禁） |
| 5 | 是否真执行 | **REAL** — M2 经真实 subprocess 重新执行，输出修正后真实数值 |
| 6 | 是否有测试 | e2e `test_06` 断言 2 code + 2 EXEC + 2 VR |
| 7 | 测试走 production path | 需注入 |
| 8 | 失败如何传播 | 同箭头 10 |
| 9 | provenance | 新 EXEC 含 code_hash（与 M1 不同） |
| 10 | Git 可追溯 | 是 |
| 11 | 是否有 fallback | 无 |
| 12 | Agent 可伪造字段 | 同箭头 10（EXEC 全字段可伪造） |

**判定：REAL**

---

### 箭头 19：Re-execution → Compare(M1, M2)

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | **无** — 修订路径无任何比较逻辑 |
| 2 | 输入 | N/A |
| 3 | 输出 | N/A |
| 4 | schema | 无 comparison 数据结构 |
| 5 | 是否真执行 | **GAP** — 无指标对比计算、无 delta 记录、无"M2 优于 M1 因为…"的决策产物；m3 候选竞技场有机械比较但那是独立候选选型（无 revision_of 边），不是修订比较 |
| 6 | 是否有测试 | 无 |
| 7 | 测试走 production path | N/A |
| 8 | 失败如何传播 | N/A |
| 9 | provenance | 无 comparison artifact |
| 10 | Git 可追溯 | N/A |
| 11 | 是否有 fallback | 无比较 = "M2 通过了就默认更好" |
| 12 | Agent 可伪造字段 | N/A |

**判定：GAP — 系统无法从自身状态回答"为什么 M2 比 M1 更好"**

---

### 箭头 20：Compare → Accept/Reject

| # | 问题 | 答案 |
|---|---|---|
| 1 | 谁调用谁 | **无** — 无 Accept/Reject 决策类型 |
| 2 | 输入 | N/A |
| 3 | 输出 | N/A |
| 4 | schema | 无 |
| 5 | 是否真执行 | **GAP** — p1-vs001 唯一决策 D001 是"Revision Request"（记录型），VR passed 是验证结果非决策；m3 D002 是 candidate_selection 非 Accept/Reject |
| 6 | 是否有测试 | 无 |
| 7 | 测试走 production path | N/A |
| 8 | 失败如何传播 | N/A |
| 9 | provenance | 无 |
| 10 | Git 可追溯 | N/A |
| 11 | 是否有 fallback | VR passed = 隐式接受（无显式决策） |
| 12 | Agent 可伪造字段 | N/A |

**判定：GAP**

---

## GAP 汇总（答不了 12 问的箭头）

| 箭头 | 核心 GAP | 严重度 |
|---|---|---|
| Problem→Representation | V3 不读题面 | P1 |
| Candidate Eval（默认） | 无评估 | P1 |
| Selection（默认） | recs[0] 硬编码 | P0 |
| MODEL_IR（实例化） | 默认不产 MIR | P0 |
| Code Generation | 无 MODEL_IR→code 机械生成 | P1 |
| ExecutionResult 创建 | 无 schema 门禁，Agent 可伪造 | P0 |
| Evidence/Claim | 占位符 "{qid} 结论" | P0 |
| Validation L2 | 21 个 validator 死代码 | P1 |
| Gate | 零数值计算 | P0 |
| Failure Diagnosis | 无诊断代码 | P1 |
| Revision Proposal | 无自动修订，M2 来自预写 | P1 |
| Compare(M1,M2) | 无比较逻辑 | P1 |
| Accept/Reject | 无决策类型 | P1 |

---

## Agent 可伪造字段总清单

| 字段 | 伪造路径 | 下游信任方 |
|---|---|---|
| EXEC.status / outputs / code_hash / duration_ms | `registry.create("execution_result", data=任意dict)` 无门禁 | validation / claim / fidelity / 报告 |
| Claim.statement / claim_type | `handlers.py:1219-1227` 直接构造 | 论文投影 / narrative |
| Candidate 全字段 | `external_candidates` 注入 | selection / experiment |
| MODEL_IR 全字段 | `external_model_irs` 注入 | 下游全部 |
| VR data | registry.create 无门禁 | decision / gate |
| Evidence Graph 边 | handler 可直接 `graph.add_edge` | evidence_gate / provenance |
| problem_features | JSON 文件可任意写 | 整条建模链 |
| decision.reasoning | decision data 无门禁 | 报告 / 可追溯性 |

> **核心结论**：当前系统中，Agent 可以伪造的事实字段覆盖 ExecutionResult / Evidence / Claim / Fidelity（间接）/ ValidationResult / Decision，**唯一不能直接伪造的是 subprocess returncode 和 fidelity_score（但可被伪造 outputs 间接操纵）**。
