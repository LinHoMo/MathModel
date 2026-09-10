# ROADMAP — 最终执行路线图

> 日期：2026-09-10 ｜ 状态：**ROADMAP FROZEN**
> 基于 8 代理审计 + 三轮自我反驳 + 真实执行验证

---

## P0（立即执行，1-2 周）

### P0-1: 集成 Fidelity Layer 到生产 DAG

> ✅ **DONE 2026-09-10**（commit `2e6662a` + `80741df`）：
> - handlers `do_model_execution` 对成功 EXEC 调 `verify_fidelity`，misaligned → 节点 FAIL，失败名前 5 个进 reason
> - `verify_fidelity` 生产 DAG 内 `register_vr=False`（只写报告，不注册 VR/verified_by——防 C8 `_active_vr_of` 幂等复用跳过真实数值验证）
> - `check_fidelity` 容器/向量输出（positions 数组）F5 范围检查如实跳过（skipped），只对可机械判定的标量下结论
> - `_register_code` 记录 `output_mapping` 契约，`execute_code` 透传 EXEC provenance（对齐 codegen 契约）
> - 验收：`test_fidelity_integration.py` 5/5 + VS-001 e2e 8/8；全量 994 passed / 4 skipped；validate 58/0；catalog OK

**目标**：L2 Fidelity（MODEL_IR↔Code）在生产路径中执行

**为什么做**：Fidelity 是 LinHoMo 独有指标，已实现但未接入。当前生产路径
执行代码但不知道执行的是否是声明的模型。

**不做的风险**：真执行+假模型无法检测（代码跑通但不实现声明的模型）

**具体改动**：
- `core/runtime/execution/handlers.py` `do_model_execution` 方法
- 在 `execute_code` 后调用 `verify_fidelity`
- Fidelity misaligned → FAIL

**测试**：
- 单测：test_fidelity_integration.py
- 集成：VS-001 重跑包含 fidelity 检查

**验收标准**：
- `verify_fidelity` 从 handlers 被调用
- Fidelity misaligned 时节点返回 FAIL
- pytest 全绿

**预计依赖**：无新依赖

---

### P0-2: 接入 Failure Diagnosis 到 Revision Flow

> ✅ **DONE 2026-09-10**（commit `311a863`）：
> - `do_model_validation` 无存活候选 FAIL → `_diagnose_and_draft`：沿 verified_by 边对每个 failed VR 调 `diagnose_failure`（机械证据），注册 diagnosis artifact + `(MIR, diagnosed_by, DIAG)` 边（幂等）
> - `build_revision_draft` 生成 M2 草案（`*-REV1`，modeling_trace 追加 revision_draft 步骤 + changed_components），放入 `shared["revision_packages"][qid]` 供外部 Model Constructor 消费
> - `finalize_revision` 去重：已有 diagnosed_by 边则跳过（全闭环仅 1 DIAG）
> - 验收：`test_diagnosis_integration.py` 5/5（三要素/机械根因/草案继承/单 DIAG/LLM-free）；全量 999 passed / 4 skipped；validate 58/0；catalog OK

**目标**：失败后自动诊断，生成修订草案

**为什么做**：diagnosis.py 已实现但零调用。Revision loop 的"失败→诊断"环节断裂。

**不做的风险**：失败后无法机械归因，只能靠人工或 LLM 猜测

**具体改动**：
- `core/runtime/execution/handlers.py` 在 validation FAIL 时调用 `diagnose_failure`
- `core/runtime/modeling/revision.py` `build_revision_draft` 生成 M2 草案
- 将诊断和草案传递给外部 Constructor

**测试**：
- 单测：test_diagnosis_integration.py
- 集成：VS-001 M1 FAIL → diagnosis → revision draft

**验收标准**：
- Validation FAIL 后自动生成 FailureDiagnosis artifact
- FailureDiagnosis 包含 failed_components/root_cause/suggested_fixes
- build_revision_draft 生成 M2 草案

**预计依赖**：无新依赖

---

### P0-3: 修复 Engine Validators 未使用问题

> ✅ **DONE 2026-09-10**（方案 B，commit `validators.py`）：
> - 新增 `core/runtime/execution/validators.py`：`evidence_consistency_validator`——PASS 节点机械复核 outputs.artifacts/evidence 真实存在于 registry（防 handler 谎报产物/证据；registry.get 缺失抛异常时安全判定）
> - `session.py`：同一 validators 注册到 WorkflowEngine 与 WaveExecutor（self.engine 最终指向 waves.engine，避免覆盖丢失）
> - 验收：`test_validator_integration.py` 5/5（注册覆盖/假 artifact 否决/假 evidence 端点否决/合法不误杀/全闭环绿）；全量 1009 passed / 4 skipped；validate 58/0；catalog OK

**目标**：要么启用 engine validator hook，要么删除该基础设施

**为什么做**：session.py:96 创建 WorkflowEngine 时未传 validators= 参数。
Engine 的 validator hook 机制从未在生产中使用。

**不做的风险**：死基础设施增加理解成本

**具体改动**：
- 方案 A（推荐）：删除 engine.py 中的 validators 机制（简化代码）
- 方案 B：在 session.py 中注册 validators（启用 hook）

**测试**：
- 如果选 A：删除后 pytest 全绿
- 如果选 B：验证 validator hook 被触发

**验收标准**：
- engine.py 中不再有未使用的 validators 代码（如果选 A）
- 或 validators 在生产路径中被调用（如果选 B）

**预计依赖**：无新依赖

---

### P0-4: 清理 Dead Code

> ✅ **DONE 2026-09-10**（commit `6466490`）：
> - handlers.py：删除 `_maybe_execute_experiment`（-2066 bytes，无调用者；P0-E 已由 do_model_execution.execute_code 路径取代）
> - engine.py：删除第一个 `unblock` 定义（被增强版覆盖，含 rollback cycles 清理）
> - comparison.py：`_vr_metrics` 删除无效循环（for 内仅 continue）
> - codegen.py 独立路径保留：K003/K002/arena/vs001 研究 runner 消费，定位为研究工具链；生产 DAG 走 handlers
> - 验收：全量 1009 passed / 4 skipped（零回归）；validate 58/0；catalog OK

**目标**：删除确认的死代码

**为什么做**：4 个 modeling 模块在生产路径中零调用（诊断已确认），
加上其他 dead code，增加理解成本。

**不做的风险**：新开发者被死代码误导

**具体改动**：
- 删除 `handlers.py:1423` `_maybe_execute_experiment` 方法
- 删除 `engine.py:281` 第一个 `unblock` 定义（被 line 349 覆盖）
- 修复 `comparison.py:22-26` dead loop（删除无效循环）
- 统一 `codegen.py` 独立路径到 `handlers.py`（或保留为 CLI 工具）

**测试**：
- pytest 全绿（删除后）
- catalog_check 通过

**验收标准**：
- grep 确认无调用者
- 测试全绿

**预计依赖**：无新依赖

---

## P1（短期，2-4 周）

### P1-1: Constructor Adapter Protocol

> ✅ **DONE 2026-09-10**（commit 见 STATUS）：`core/runtime/constructors/` （protocol.py ConstructionBundle/ConstructorAdapter/C0-C5 + registry.py ConstructorRegistry/apply_bundle）；验收 5/5（序列化往返/能力分级/ABC/mock 全闭环/无事实写权限）。


**目标**：设计并实现 `core/runtime/constructors/protocol.py`

**为什么做**：支持外部 Constructor（MathModelAgent/Claude Code）通过统一
协议接入 LinHoMo Runtime。

**不做的风险**：无法标准化外部 Agent 集成

**具体改动**：
- 新建 `core/runtime/constructors/__init__.py`
- 新建 `core/runtime/constructors/protocol.py`（ConstructionBundle + ConstructorAdapter）
- 新建 `core/runtime/constructors/registry.py`（Adapter 注册）
- 在 handlers.py 中增加 ConstructorAdapter 接入点

**测试**：
- 单测：test_constructor_protocol.py
- Mock adapter 测试完整闭环

**验收标准**：
- ConstructionBundle 可序列化/反序列化
- ConstructorAdapter ABC 定义完整
- 一个 mock adapter 可以完成 construct → execute → validate 闭环

**预计依赖**：无新依赖

---

### P1-2: 接入 Knowledge Guided Construction

> ✅ **DONE 2026-09-10**：handlers._register_mir 接入 apply_knowledge_obligations（shared[knowledge_guide] 配置，默认关闭；merge + source_card 溯源 + knowledge_refs，不覆盖建模者声明）；knowledge_guided 义务对齐 MODEL_IR 契约（method/targets_refs/sub_question_binding/text/rationale）；验收 4/4 + M4 7/7。


**目标**：将 knowledge_guided.py 接入 candidate generation

**为什么做**：knowledge_guided.py 实现了 v2 版本的义务映射
（validation/claim 分离），但从未被生产路径调用。

**不做的风险**：知识引导义务（validations/assumptions/risks）无法嵌入 MODEL_IR

**具体改动**：
- 在 `handlers.py` `do_model_selection` 中调用 `apply_knowledge_obligations`
- 或在 `CandidateArena` 中集成 `map_card_obligations_v2`

**测试**：
- 单测：test_knowledge_guided_integration.py
- 验证 MODEL_IR 包含 knowledge-derived obligations

**验收标准**：
- MODEL_IR.validations 包含 source_card 溯源
- 知识卡义务正确嵌入候选模型

**预计依赖**：无新依赖

---

### P1-3: 接入 Model Comparison

> ✅ **DONE 2026-09-10**：do_model_validation PASS 分支沿 revision_of 边自动 compare_models（VR 机械证据）→ decision artifact + compared_with/based_on 边（evidence_graph 新增 compared_with 弱边）；幂等 + 证据缺失不制造决策；验收 3/3。


**目标**：将 comparison.py 接入 model selection

**为什么做**：M1/M2 比较目前靠盲评。comparison.py 可以从 VR 指标
机械比较两个模型。

**不做的风险**：模型比较只能靠主观盲评

**具体改动**：
- 在 revision flow 中调用 `compare_models`
- 将比较结果传递给 accept/reject 决策

**测试**：
- 单测：test_comparison_integration.py

**验收标准**：
- M1 FAIL → M2 PASS 时自动比较
- 比较结果包含 better_model/recommendation/deltas

**预计依赖**：无新依赖

---

### P1-4: 标注硬编码经验常数的 Provenance

> ✅ **DONE 2026-09-10**：_decision_confidence docstring 声明 advisory（不参与 PASS/FAIL）；findings/selection confidence 标注 advisory；integrity_gate 声明政策阈值来源（env/评审政策，非经验外推）；验收 5/5 + 29 单测无回归。


**目标**：所有确定性评分中的经验常数要么标注来源，要么移除

**为什么做**：13+ 个硬编码常数（0.25/0.7/0.95/0.15/20/0.999 等）
被确定性脚本包装后产生"客观测量"外观。这是 formalized false authority。

**不做的风险**：系统输出的"置信度"和"评分"实际是无溯源的猜测

**具体改动**：
- `handlers.py:837-857` `_decision_confidence`：标注为 advisory，不参与 PASS/FAIL
- `findings.py:121/147/157`：标注为 advisory
- `integrity_gate.py:118/161/172/255/345`：标注来源或移除
- `selection.py:120`：标注为 advisory

**测试**：
- 验证 advisory 常数不参与 PASS/FAIL 判定

**验收标准**：
- grep 确认无未标注的经验常数参与确定性判定
- 所有 confidence 值标注为 advisory

**预计依赖**：无新依赖

---

## P2（中期，1-2 月）

> ✅ **DONE 2026-09-10**（commit `P2-1 基建`）：预注册
> `research/P15/protocol/preregistration/P15-K004-v1.0.md`（4 Constructor ×
> 2 Runtime × 8 题 × 2 seeds = 64 runs；MCQ_primary + VAL_mech 双主终点；
> 5 判定形态；Measurement Gate 前置）；`research/P15/k004/reference_constructor.py`
> （LLM-free Reference Constructor C3，M1_DICT 合规基底 + 模板代码与 MODEL_IR
> 变量对齐，fidelity 可测）；`research/P15/k004/mma_adapter.py`（MathModelAgent
> Adapter 契约，未装配抛 ConstructorError 不静默降级）；验收 5/5
> （bundle 合规+往返 / apply_bundle+DAG 真实执行闭环 / registry /
> mma 清晰报错 / 预注册判定规则）。剩余：64 runs 生成 + 盲评 + 统计（P2-1b）。

### P2-1: Constructor-Independent Benchmark

**目标**：区分 Agent 能力 vs Runtime 增益

**为什么做**：这是回答"LinHoMo 是否真正增加建模价值"的唯一方法

**不做的风险**：无法证明 Runtime 的价值

**具体改动**：
- 设计实验协议（预注册）
- 实现 Reference Constructor（minimal, LLM-free）
- 实现 MathModelAgent Adapter
- 跑 64 runs（8 题 × 4 Constructor × 2 Runtime 条件）
- 盲评 + 统计分析

**测试**：
- 实验协议通过 RFC 审批
- 64 runs 全部完成
- 盲评 κ ≥ 0.6

**验收标准**：
- 能区分 Agent 能力 vs Runtime 增益
- 结果可复现

**预计依赖**：可能需要 E2B API key

---

> ✅ **DONE 2026-09-10**（commit `P2-2 fidelity study`）：
> `research/P15/analysis/p2_2_fidelity_study.py` + 报告
> `P2-2-FIDELITY-STUDY.md` + 产物 JSON。44 结构化 runs：fidelity 双峰分布
> （36 aligned 0.8-1.0 / 8 misaligned 全 0.2）；8 个 misaligned 全在
> 2022_C/2024_A，根因=中文语义变量名 vs 英文输出 key 的 output_mapping
> 词汇错位（exec 全 success，非数学错误）——与 K001 RQ5 词表问题同源；
> fidelity vs 盲评 L2 无正相关（Pearson .051/Spearman .254），L2.6 负相关
> -.479——文档结构质量与表示-实现一致性正交。建议：fidelity 进 benchmark
> 机械主指标；output_mapping 契约前置（P1-1 ConstructionBundle 已承载）。

### P2-2: Fidelity Measurement Study

**目标**：测量 L2 Fidelity 在真实构造中的分布

**为什么做**：Fidelity 是 LinHoMo 独有指标，但从未被系统测量

**不做的风险**：不知道 Fidelity 作为质量指标的有效性

**具体改动**：
- 对 K003 的 66 runs 计算 fidelity_score
- 分析 fidelity 与盲评 L2 score 的相关性
- 识别 misaligned 案例

**测试**：
- 分析脚本可复现
- 结果可解释

**验收标准**：
- Fidelity 分布报告
- Fidelity vs 盲评 L2 的相关性分析

**预计依赖**：K003 数据已存在

---

> ✅ **DONE 2026-09-10**（commit `dc8dca1`+`bb10f6b`）：
> 检索命中率判别（检索失败 vs 知识无用）——8 题 ground-truth 卡 hit@3
> 修复前 62.5%（5/8）→ 修复后 **87.5%（7/8，全 rank=1）**。修复 2 处
> 检索缺陷：mc-ols 补 `regression`（题目标签与卡词表错位）；mc-kmeans
> 补 `small`（聚类适用小样本，原标注过滤整卡）。2024_A 未命中=卡池
> 覆盖缺口（无运动学/ODE 卡，P1 工程项）。判定：检索基本可靠 →
> K001 negative 非检索失败 → 指向效用/剂量/测量维度（与 ATTRIBUTION
> 一致）。P2-3 实验（直接注入 vs 检索后注入，18 runs）见 P2-3b。

### P2-3: Knowledge Efficacy v2

**目标**：验证知识卡在改进检索后是否有效

**为什么做**：K001 NULL 可能是检索失败而非知识无用

**不做的风险**：放弃一个可能有效的方向

**具体改动**：
- 设计实验（直接注入 vs 检索后注入）
- 跑 18 runs
- 盲评 + 统计分析

**测试**：
- 实验协议通过 RFC 审批
- 18 runs 全部完成

**验收标准**：
- 能区分"检索失败"和"知识无用"

**预计依赖**：无新依赖

---

## P3（长期，3+ 月）

### P3-1: E2B Execution Backend

**目标**：支持 E2B 沙箱执行

**为什么做**：LocalPythonAdapter 安全性有限，E2B 提供隔离沙箱

**不做的风险**：安全限制

**具体改动**：
- `core/runtime/execution/adapters.py` 新增 `E2BAdapter`
- 实现 `ExecutionAdapter` 接口

**测试**：
- E2B 可用时自动切换
- 不可用时回退 LocalPythonAdapter

**验收标准**：
- E2B adapter 可执行代码
- 输出格式与 LocalPythonAdapter 一致

**预计依赖**：E2B API key

---

### P3-2: 确定性指标替代盲评

> ✅ **DONE 2026-09-10**（commit `8681041`）：
> `core/runtime/evaluation/deterministic_metrics.py`（LLM-free）：
> - `claim_evidence_coverage(graph)`：Evidence Graph 机械遍历——每个 claim
>   是否被真实证据终端支撑（supports 边 + execution_result 带
>   execution_token / verification_result 带数值 / result 带 outputs），
>   缺失如实报告，绝不默认通过（The Agent Is Not The State）。
> - `baseline_comparison(outputs_a, outputs_b, keys, tolerance)`：纯数值
>   确定性比较（相对差异/tie/different/incomparable，缺失 key 列出）。
> 验收 7/7（真实证据 supported / 假证据 unsupported / 空图 / tie /
> different / incomparable / 逐位确定性）。L1.3 subprocess 真实执行
> 已有（P0-3），故 ≥3 个维度已有确定性替代（L1.3/L4.1/L4.5）。


**目标**：用确定性检查替代部分盲评维度

**为什么做**：κ 值持续低于 0.6，盲评工具不可靠

**不做的风险**：测量工具本身不可靠

**具体改动**：
- L4.1 Baseline comparison → execution_result 数值比较
- L4.5 Claim-evidence map → Evidence Graph 机械遍历
- L1.3 Code executable → subprocess 真实执行（已有）

**测试**：
- 确定性指标与盲评指标的相关性

**验收标准**：
- 至少 3 个维度有确定性替代
- 确定性指标可复现

**预计依赖**：无新依赖

---

### P3-3: Paper Quality End-to-End Test

**目标**：完整 pipeline 在真实竞赛题上的表现

**为什么做**：所有 P15 实验都是组件级，没有测试端到端

**不做的风险**：不知道整体 pipeline 是否产生好的论文

**具体改动**：
- 选择 2 道竞赛题
- 完整 pipeline：Knowledge → Construction → Execution → Validation → Paper
- 盲评论文质量

**测试**：
- 论文通过 LLM reviewer
- 论文包含真实执行结果

**验收标准**：
- 论文包含 ≥ 6 figures, ≥ 4 tables, ≥ 15 equations, ≥ 10 references
- 无 placeholder / AI 痕迹

**预计依赖**：需要 LaTeX 编译环境

---

## 执行顺序

```
P0-1 (Fidelity) → P0-2 (Diagnosis) → P0-3 (Engine Validators) → P0-4 (Dead Code)
                                                                      ↓
P1-1 (Constructor Protocol) ← P0 完成
    ↓
P1-2 (Knowledge Guided) + P1-3 (Comparison) + P1-4 (Provenance)
    ↓
P2-1 (Constructor-Independent Benchmark) ← P1 完成
    ↓
P2-2 (Fidelity Measurement) + P2-3 (Knowledge v2)
    ↓
P3-1 (E2B) + P3-2 (Deterministic Metrics) + P3-3 (E2E Test)
```

## 每项验收命令

```powershell
# 每项完成后必须运行：
py -3.12 -m pytest tests -q                    # 全绿
py -3.12 core/tools/validate.py                # 58 通过
py -3.12 core/tools/catalog_check.py --check   # OK
```
