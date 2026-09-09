# AUDIT_FINDINGS — MathModel 全仓库审计发现汇总（Batch 0）

> **审计基线**：HEAD `d44384c`，2026-09-09
> **审计方法**：8 个独立只读审计子代理（A-H），共 108 项发现
> **严重度定义**：
> - **P0** = scientific integrity（假 execution / false evidence / fake completion / Agent 可伪造事实字段）
> - **P1** = broken model construction loop（链路断裂）
> - **P2** = validation / revision weakness（验证/修订弱点）
> - **P3** = architecture / maintainability（架构/可维护性）
> - **P4** = documentation / cosmetic（文档/外观）

---

## 发现计数总览

| 审计官 | 范围 | P0 | P1 | P2 | P3 | P4 | 合计 |
|---|---|---|---|---|---|---|---|
| A 架构 | 架构/依赖/边界 | 0 | 2 | 2 | 6 | 3 | 13 |
| B 模型构建 | Problem→MODEL_IR | 2 | 3 | 4 | 3 | 0 | 12 |
| C 执行 | MODEL_IR→ExecutionResult | 3 | 5 | 4 | 1 | 3 | 16 |
| D 证据/验证 | Evidence→Decision | 3 | 3 | 3 | 0 | 2 | 11 |
| E 修订 | FAIL→M2→Compare | 0 | 7 | 5 | 1 | 0 | 13 |
| F 实验 | K001/K002/K003 | 3 | 7 | 6 | 0 | 0 | 16 |
| G 测试 | 反作弊审计 | 2 | 5 | 5 | 3 | 1 | 16 |
| H 治理 | docs/schema/git | 1 | 3 | 3 | 2 | 2 | 11 |
| **合计** | | **14** | **35** | **32** | **16** | **11** | **108** |

> 注：各审计官原始 severity 已统一映射到 P0-P4。同一问题可能被多个审计官从不同角度发现（如 claim 占位符被 B/D/G 同时报告），下表去重后保留最严重判定并标注交叉引用。

---

## P0 — Scientific Integrity（14 项，去重后 12 项核心）

### P0-01：ExecutionResult 落库无 schema 门禁，任何 Agent 可直接构造伪造执行结果
- **来源**：C-001（HIGH），交叉引用 F-001
- **File**：`core/runtime/artifacts/registry.py:108-145`，`core/runtime/artifacts/artifact.py:63-88`
- **Observed**：`registry.create("execution_result", data=任意dict)` 只做 Artifact 通用校验（ID/type/status 枚举），**不校验 data 内容**。`ExecutionResultData` 是公开 dataclass，任何持有 registry 的代码路径可直接构造 `{status:"success", outputs:{...}, code_hash:"", duration_ms:0}`。
- **Why it matters**："ExecutionResult 只能由 substrate 创建"铁律的直接缺口。K003 伪造事件（dad33cd）正是借助此类无门禁落盘路径。
- **Evidence**：`artifact.py validate` 全文无 data 内容检查；`registry._create_locked:133-135` 仅调 `art.validate()`。
- **Proposed fix**：为 execution_result 增加 data schema 校验（status ∈ EXEC_STATUS、execution_id 非空、code_hash == sha256(code)、必填字段齐全）；或引入"仅 substrate 可写"的执行结果专用登记 API。
- **Test required**：`test_execution_result_schema_gate` — 伪造 data 必须被拒绝。

### P0-02：K003 Organizer/Generator 可直接制造 execution_result — 治理漏洞已实际发生
- **来源**：F-001（P0），交叉引用 C-002
- **File**：`research/P15/experiments/P15-K003/k003_formal_runner.py:690-785`
- **Observed**：单个 Organizer 脚本同时写表示文件、代码、execution_result、fidelity_report、manifest。无独立执行节点，无防篡改链。git `d44384c` 证实 generator 曾伪造 execution_result（空 outputs/空哈希/硬编码 fidelity 39/27/0），后由 harness 人工重建。
- **Why it matters**：治理铁律"Generator 永远没有 execution_result 写权限"被违反且已实际发生一次。没有任何机制保证下一次不会发生。
- **Proposed fix**：拆分执行为独立进程，仅该进程可写 execution_result；执行结果写入 ArtifactRegistry 并纳入哈希链；增加"execution_result 与 registry 一致性"机器校验。

### P0-03：K003 runner 契约 bug — 已提交 runner 复跑会重新产出伪造空壳
- **来源**：C-002（HIGH）
- **File**：`research/P15/experiments/P15-K003/k003_formal_runner.py:720-758`
- **Observed**：`run_code_pipeline` 只返回 7 个 key（code_id/exec_id/exec_status/...），runner 却读取 `pipe_result.get("outputs"/"duration_ms"/"code_hash"/...)` — 这些 key 全部不存在，全部回退到 `{}`/`0`/`""`。dad33cd 的 66 份空壳**不是恶意伪造，而是契约 bug 机械产生**。d44384c rebuild 重写了产物但**没有修 runner**。
- **Why it matters**：当前提交的 runner 一旦复跑，会重新产出伪造空壳。rebuild 是一次性人工修复，不可复现。
- **Proposed fix**：删除 runner 中所有 `pipe_result.get(...)`，改为从 registry 读 EXEC 数据（照抄 precheck runner 的正确写法）。

### P0-04：默认选型硬编码 `chosen = recs[0]`，无证据支撑
- **来源**：B-001（Critical）
- **File**：`core/runtime/modeling/selection.py:60`（另见 88 行 `top = recs[0]`）
- **Observed**：`outcome = SelectionOutcome(..., chosen=recs[0].card.card_id)` — 直接取检索推荐第一名。confidence 由检索分换算 `min(0.5+0.1*top.score, 0.95)`。
- **Why it matters**：生产默认路径的"为什么选这个模型"只能回答"检索得分最高"，不是模型质量证据。系统无法回答"为什么选 A 不选 B/C"。
- **Proposed fix**：默认路径若无执行证据，应声明 `UNSELECTED/pending_evidence`；或由 orchestrator 接入候选竞技场。
- **Test required**：断言默认路径（无注入）下 model `selection_status == "pending_evidence"`。

### P0-05：默认建模节点不产 MODEL_IR 仍 PASS
- **来源**：B-002（Critical），交叉引用 G-002
- **File**：`core/runtime/execution/handlers.py:891-930`
- **Observed**：`do_model_construction` 无外部注入时只登记 assumption artifact，`construct_model_ir`/`construct_candidate_mirs` 返回 None/[]，**不产生任何 MODEL_IR**。节点以 `PASS("登记 N 条假设")` 结束。实测 3 个真实项目 MIR=0。
- **Why it matters**：MODEL_IR 18 字段契约在默认路径永远不被满足。"模型"只是方法卡 ID 薄壳。DAG 描述写"建立数学模型（公式/符号/边界）"与实际行为完全不符。
- **Proposed fix**：无 MIR 产出时节点应 FAIL 或至少标记 `pending_model_ir`；测试应断言默认路径必须产 MIR。

### P0-06：Claim 是显式占位符 `"{qid} 结论"`，无任何真实结论生成
- **来源**：D-002（Critical），交叉引用 G-003
- **File**：`core/runtime/execution/handlers.py:1219-1227`
- **Observed**：claim 创建时 `title/statement = "{qid} 结论"`，`claim_type="comparative"` 硬编码，`execution_status="not_executed"`，`placeholder: True`。**全仓无任何代码填充真实结论文本**。占位符经 `director.py:73` → narrative_ir → `projection.py:54` 流入论文大纲"结果与分析"节。
- **Why it matters**：论文结论章节的机器可读大纲由占位文本投影而成。claim_quality 只检查 statement 非空，占位符照过。
- **Proposed fix**：占位 claim 不得标记为 supported；claim_quality 增加占位符词检测；结论生成应读取 result 数值由确定性模板或 LLM 合成。

### P0-07：evidence_gate 是纯结构门禁，零数值/真实性检查
- **来源**：D-001（Critical），交叉引用 G-004
- **File**：`core/validators/evidence/evidence_gate.py:87-181`
- **Observed**：E1-E8 全部只查图边存在性/生命周期状态/tags，**无任何数值计算**。不校验 outputs 非空、不校验 execution status、不做 ground truth 比对。仓库自身承认（`handlers.py:495`、`validation.py:193` 注释"evidence_gate 只查边不查数值"）。一条 `not_executed` 的链可以结构 PASS。
- **Why it matters**："证据门禁通过"被当作"有真实证据"的准入信号，但门禁无法区分"真跑过"与"没跑过"。
- **Proposed fix**：增加数值真实性检查：EXEC artifact 必须存在且 status=="success"、outputs 非空；result.data.status != "not_executed" 时应降级。

### P0-08：执行失败不传播 — do_model_execution 无条件 PASS
- **来源**：C-007（MEDIUM→P0），交叉引用 D-005
- **File**：`core/runtime/execution/handlers.py:525-534`
- **Observed**：`do_model_execution` 无论执行结果如何都返回 PASS。实验链 `_results_of` 不过滤 `data.status="failed"`，**claim 可构建在失败执行之上**。
- **Why it matters**：`execution failed → validation FAIL → decision FAIL` 的传播链断裂。实际是 `execution failed → default PASS`。
- **Proposed fix**：执行失败时节点应 FAIL 或至少标记；`_results_of` 应过滤 failed 结果。

### P0-09：K003 盲评不盲 — submission ID 是 (题目,臂,seed) 确定性哈希，臂可逆向还原
- **来源**：F-002（P0）
- **File**：`research/P15/experiments/P15-K003/k003_formal_runner.py` `make_submission_id`
- **Observed**：`sid = sha256(f"P15-K003_{problem}_{arm}_seed{seed}")[:12]`。实测 `09a80448b035` = 2022_C/S/42。任何人可枚举 72 组合反推任意 run 的臂。且盲评包文件结构本身（F=model_doc.md / SV=validation_plan.json）直接暴露臂。
- **Why it matters**：盲评核心假设（评估者看不到臂分组）被结构性破坏。G2 校准报告显示评估者已在按"F 臂/SV 臂"推理。
- **Proposed fix**：改用随机 UUID；run_order 在 FROZEN 阶段生成并哈希冻结。

### P0-10：K003 不存在真实外部 Agent 构造 — 罐头定义替代 construct
- **来源**：F-003（P0）
- **File**：`research/P15/experiments/P15-K003/k003_formal_runner.py` `ALL_PROBLEM_DEFS`
- **Observed**：所有"外部 Agent 产物"（MODEL_IR/model_doc/run_model.py/output_mapping）都是 runner 脚本内硬编码的问题定义。协议规定"外部 Agent 只负责构造模型+写代码"，但正式实验中该角色被 Organizer 罐头定义完全替代。
- **Why it matters**：K003 的 RQ1（"结构化表示是否提升外部 Agent 的模型构造质量"）根本没有被测量。Construct Validity = FAIL。
- **Proposed fix**：必须真正接入独立构造 Agent；Organizer 不得预置表示定义。

### P0-11：K003 formal_results.json 被后台 Organizer 原地改写，与 run_summary 冲突
- **来源**：H-002（High→P0）
- **File**：`research/P15/experiments/P15-K003/formal_results.json` vs `run_summary.json`
- **Observed**：审计期间观察到 formal_results.json 被后台进程改写，瞬时出现 27/39/0 分布，与 run_summary 的 18/26/22 冲突（mtime 18:55 vs 16:43）。提交后无一致性门禁。
- **Why it matters**：实验结果文件可被任意改写且无校验，与 K002 E02 事件同类风险。
- **Proposed fix**：实验结果文件纳入冻结/哈希链；增加 formal_results 与 run_summary 一致性校验。

### P0-12：测试把错误行为编码为预期 — 占位管线 validated、legacy pointer 豁免
- **来源**：G-002（HIGH→P0）
- **File**：`tests/e2e/test_e2e_metrics.py`，`tests/integration/test_runtime_session.py`
- **Observed**：test_e2e_metrics 明确断言"全为 legacy pointer → structural_pass is None（不判 FAIL）"，把"默认路径不产 MODEL_IR"编码为预期行为。test_runtime_session 断言 `claims_supported=2`（占位 claim 骗过 gate）。
- **Why it matters**：测试不仅没捕捉 P0-05/P0-06，反而把它们锁定为正确行为。修复这些问题会"破坏测试"。
- **Proposed fix**：修改测试断言为正确行为（无 MIR 应 FAIL，占位 claim 不应 supported）。

---

## P1 — Broken Model Construction Loop（35 项，去重后核心 18 项）

### P1-01：K003 REAL EXECUTION rebuild 过程不可从已提交代码重放
- **来源**：C-003（HIGH）
- d44384c 重写了 66 份 execution_result 但 diff 中无任何脚本变更。写入真实数据的脚本未提交。审计者无法从仓库证明"66 份真实执行"。

### P1-02：K003 伪造链 fidelity 证据剥离 — score=0.2 有值但 checks=[]
- **来源**：C-004（HIGH）
- 旧版 fidelity_report.json `score=0.2, checks=[], passed=0, total=0`。分数与证据剥离，文件层面不可验证。0.2 实际是真实 VR 分数（3/15）但被剥离 checks 后呈现为无证据裸分。

### P1-03：MODEL_IR 无 `code_mapping` 字段
- **来源**：B-003（High）
- 全仓 Grep `code_mapping` 0 匹配。MODEL_IR→Code 的映射仅靠 graph `implemented_by` 边 + schema `solvers[].implementation_ref`（自由字符串，不校验指向真实 CODE artifact）。

### P1-04：Evidence Graph 无 `evaluated_by`/`selected_from` 边
- **来源**：B-004（High）
- `evaluated_by` 和 `selected_from` 在 RELATION_TYPES 中均不存在，全仓 0 匹配。候选评估证据和选型可追溯性未实体化为 typed 边。

### P1-05：候选分数是启发式常量，非评估结果
- **来源**：B-005（High）
- candidates.py 的 score 全部由检索分派生 + 硬编码增量（baseline=main.score, improved=main.score+2, hybrid=max-2, innovation=main.score+novelty...）。不是任何模型执行/评估的结果。

### P1-06：默认实验结果为 `not_executed` 占位，Claim 可被未执行结果支撑
- **来源**：B-006（High），交叉引用 D-005
- 默认 runtime 不执行数值计算（handlers.py:1081-1082 注释明示），result 停留 not_executed。E6 只查 lifecycle draft 不查 data.status，未执行链可过 gate。

### P1-07：21 个分层 validator 是死代码，validate.py 只做"类名存在"检查
- **来源**：D-003（High），交叉引用 G-006、H-004
- `core/validators/modules/*` 21 个文件全仓零 import。validate.py 的 L1-L6 检查只是 `if "class X" not in content` 的字符串存在性检查，恒 PASS。"六层防御验证"名不副实。

### P1-08：V3 运行时不读题面/question_spec.json
- **来源**：B-007（Medium→P1）
- V3 只建 features 粗画像 + 纯标题 Question。结构化表示（question_spec.schema.json 146 行完整契约）仅在 legacy V2 路径，V3 从不读取。问题本体从未进入 V3 认知管线。

### P1-09：jsonschema 未在 runtime 强制执行
- **来源**：B-008（Medium→P1），交叉引用 A-004
- model_ir.py 的 `validate_model_ir` 注释自曝"历史：register 从不校验"。pyproject 连 jsonschema 依赖都没有。validate.py 的 schema 检查只验文件是合法 JSON（非实例校验）。

### P1-10：Model Artifact provenance 为空
- **来源**：B-009（Medium→P1）
- V3 model artifact 是 `{card_id, family, shortlist}` 薄壳，registry.create 调用均未传 provenance → 实测 provenance={}。V2 model_artifact.schema.json 也无 provenance 字段且无强制执行点。

### P1-11：候选竞技场链未接入生产 orchestrator
- **来源**：B-012（Medium→P1）
- P1-M3 候选竞技场链（多候选真实执行+数值验证+机械排序）每个环节 REAL，但生产 orchestrator 零接线，无任何生产代码注入 `external_candidates`。两条链并行存在。

### P1-12：codegen.py + fidelity.py 是平行管线，不在生产链上
- **来源**：A-005（P3→P1，因影响执行链完整性）
- codegen.py+fidelity.py 是完整执行+保真管线，但仅测试/CLI 可达。生产链另有一套实现（handlers 内联执行）。多管线并存是造假事件的结构性土壤。

### P1-13：e2e/test_pipeline.py 是自认占位符 — 端到端从未被执行
- **来源**：G-001（HIGH）
- 3/4 核心 e2e 测试因产物不存在而 `pytest.skip`，注释自认"显式占位"。端到端流水线从未被测试执行。

### P1-14：claim 占位符零测试覆盖
- **来源**：G-003（HIGH）
- `"{qid} 结论"` 占位符、placeholder=True、not_executed 状态零测试覆盖。test_runtime_session 反而断言 claims_supported=2。

### P1-15：evidence_gate 测试只验证结构行为，不验证数值真实性
- **来源**：G-004（HIGH）
- test_evidence_gate 用合成图/artifact，断言只覆盖结构判定。"无证据"被降格为"无边"。

### P1-16：21 个 validator modules 零测试
- **来源**：G-006（HIGH）
- core/validators/modules/ 死代码且零测试。tests 仅引用 evidence_gate 和 quality。

### P1-17：K003 伪重复 — 66 runs 仅含 24 个唯一表示
- **来源**：F-004（P1）
- 同题同臂 3 个 rep 的表示文件逐字节相同（F 臂 0 个不同哈希）。有效样本量是 24 不是 66。bootstrap/CI 精度宣称虚高，评估者对相同包重复评分人为抬高 κ。

### P1-18：K003 重建不可复现 — execution_result 含空时间戳/占位 ID
- **来源**：F-005（P1），交叉引用 C-003
- 磁盘上 execution_result 的 `executed_at=""`、`EXEC001` 占位与 runner 输出契约（应写 UTC 时间戳）不符。重建脚本未入库。

---

## P2 — Validation / Revision Weakness（32 项，去重后核心 14 项）

### P2-01：门禁 WEAK 也被 handler 判为 FAIL，语义矛盾
- **来源**：D-004（High）
- evidence_gate 文档声明 WEAK 为警告性，但 `do_evidence_gate` 中 `if report.passed: PASS else: FAIL`，WEAK 走 FAIL→反馈环。与文档语义矛盾。

### P2-02：Validation 分层无一完整 REAL
- **来源**：D 审计矩阵
- L0 GAP（not_executed 可过）、L1 GAP（无实例校验）、L2 FAKE（formula_checker 死代码）、L3 GAP（run_numeric_validation 硬编码单问题）、L4 GAP（sensitivity 仅 tags 检索不计算）。

### P2-03：run_numeric_validation 硬编码单一问题
- **来源**：D 审计（L3）
- validation.py 的数值验证硬编码 `pair_distances/head_speeds/positions` 键名，非通用层。换一个问题就无法验证。

### P2-04：无 Failure Diagnosis 代码
- **来源**：E-001/E-003（HIGH）
- engine._handle_failure 只做 retry→rollback，不分析失败原因。p1-vs001 的"诊断"是 runner 硬编码字符串。

### P2-05：无 Revision Proposal 机制
- **来源**：E-003/E-005（HIGH）
- 无"基于失败证据生成修订方案"的机制。M2 的 MODEL_IR 全部来自预写文件/fixtures。runtime 仅读取外部注入的 revision_of 登记谱系。

### P2-06：supersedes 边方向在两套官方路径中相反
- **来源**：E-002（HIGH）
- runtime 路径（handlers.py:205 + e2e）是"旧 supersedes 新"，p1-vs001 runner 是"新 supersedes 旧"。语义自相矛盾。

### P2-07：registry.supersede 已实现但 core 无调用点
- **来源**：E-007（MEDIUM）
- vs001_run 中 M1/M2 同时保持 active（双活模型）。旧模型未被标记 superseded。

### P2-08：无 M1/M2 比较逻辑
- **来源**：E-008/E-009（HIGH）
- 修订路径无任何指标对比计算、无 delta 记录。m3 候选竞技场有机械比较但是独立候选选型（无 revision_of 边），不是修订比较。

### P2-09：无 Accept/Reject 决策类型
- **来源**：E-010（HIGH）
- 无"接受/拒绝 M2"的决策产物。p1-vs001 的 D001 是"Revision Request"（记录型），VR passed 是验证结果非决策。

### P2-10：无 changed_components 结构化字段
- **来源**：E-006（MEDIUM）
- M1→M2 改了什么（参数/方程/假设）没有结构化记录。系统无法回答"为什么修改 mu 就能修复"。

### P2-11：K002 已知混淆未修复 — 格式不对称污染负效应
- **来源**：F-008（P1→P2）
- 预检已发现 S<F 方向一致 6/6（p≈1.6%）并锁定"格式不对称"为最可能混淆，正式实验仅加指令级"格式中立"条款（报告自认未消除）。负效应 −4.85 不可作为"结构化有害"的证据。

### P2-12：K001 post-hoc 修正计分口径
- **来源**：F-012/F-013（P2）
- K001 存在修正计分口径变化（Δ 2.14 vs 6.41）与 n=1 稀有事件表述强度问题。

### P2-13：STATUS.md 声称 validate.py "57/0/0"，实测 56/1/0
- **来源**：H-001（High）
- fixture PDF 8230B < 102400B 且该 PDF 未入库。干净检出无法复现声称值。

### P2-14：K003 G2/G4 闸门未能阻止正式运行中的伪造
- **来源**：F-016（P2）
- G2/G4 闸门在预检上通过，但未能阻止正式运行中 generator 伪造 execution_result。闸门对执行权限分离无校验能力。

---

## P3 — Architecture / Maintainability（16 项，核心 8 项）

### P3-01：orchestrator --legacy 模式 SKILL 路径全部失效
- **来源**：A-001（P1）
- `_skill_path()` 指向迁移前的 `core/<Hand>/...`，实际在 `core/legacy/hands/`。29 步流水线一步都跑不起来。catalog.yaml 路径正确，是调用方硬编码绕过真源。

### P3-02：state.py status 打印的 SKILL 路径过期
- **来源**：A-002（P1）
- 与 A-001 同源。续跑协议在实际环境中无法按 CLI 提示执行。

### P3-03：contracts.py 契约冻结层零接线
- **来源**：A-003（P2）
- 全部谓词（is_terminal/is_reusable/validate_node_result_outputs/ContractViolation）在 core/ 零调用。终态元组在 ≥10 个文件中内联，与契约模块 docstring 宣称的"一律 import 谓词、禁止内联元组"直接矛盾。

### P3-04：v3 schema 无任何数据校验消费方
- **来源**：A-004（P2）
- 27 个 schema 中 v3 schema（registry/status/graph/run_record/dag）无任何数据校验消费方。pyproject 连 jsonschema 依赖都没有。

### P3-05：writing 质量孤岛
- **来源**：A-006（P3）
- `writing/{paragraphs,expression,patterns,fact_check,redundancy}` 只被 tests 引用，不在生产链上。

### P3-06：orchestrator 未接线 execution adapter / validators
- **来源**：A 审计 + E 审计
- RuntimeSession 的 validators={}（空），engine 的 validator 钩子未被传入任何 validator。

### P3-07：registry.create 无 payload schema 门禁（通用）
- **来源**：H-003（Medium）
- 不仅 execution_result，所有 artifact type 的 data 字段都无 schema 门禁。"真 jsonschema"仅在 P15 独立脚本，且含硬编码绝对路径。

### P3-08：生成产物入库问题
- **来源**：H-007（Medium）
- 实验 registry.json（1.4-1.8MB ×5）、projects/ 232 文件、字体 30MB、外部仓库快照 8.6MB 均在 git 中。

---

## P4 — Documentation / Cosmetic（11 项，核心 6 项）

### P4-01：AGENTS.md 测试基线 758/11 过期
- **来源**：H-009（Low），G 审计确认
- 实际 911 passed / 4 skipped。仓库 commit 6af11fa 自证 911。

### P4-02：README/catalog 注释数字与实际不符
- **来源**：H-005（Medium→P4）
- 注释称"15 节点 + 6 validator"，实际 20 节点 + 7 validator。

### P4-03：README/HANDOFF/STATUS 三方冲突
- **来源**：H-006（Medium→P4）
- README 研究表（K002 38 文件/FROZEN）与 HANDOFF.md（882/4、K002 进行中）与 STATUS.md（911/4、K002 CLOSED、K003 FROZEN）冲突。"双真源"复发。

### P4-04：.gitignore 重复条目
- **来源**：H-008（Low）

### P4-05：P15 硬编码路径 + superseded schema 副本残留
- **来源**：H-010（Low）

### P4-06：raw_k003 盲评数据未入库
- **来源**：H-011（Info）

---

## 交叉引用矩阵

| 核心问题 | 报告审计官 |
|---|---|
| ExecutionResult 可伪造 | C-001, F-001, H-003 |
| 默认不产 MODEL_IR | B-002, G-002 |
| Claim 占位符 | D-002, G-003, B-006 |
| evidence_gate 零数值 | D-001, G-004 |
| 21 validator 死代码 | D-003, G-006, H-004 |
| K003 伪造事件 | F-001, C-002, C-003, C-004, F-005 |
| selection 硬编码 | B-001, G-006(测试未捕捉) |
| 修订环缺失 | E-001~E-013 |
