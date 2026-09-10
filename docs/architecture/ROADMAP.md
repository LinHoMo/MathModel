# ROADMAP — 最终执行路线图

> 日期：2026-09-10 ｜ 状态：**ROADMAP FROZEN**
> 基于 8 代理审计 + 三轮自我反驳 + 真实执行验证

---

## P0（立即执行，1-2 周）

### P0-1: 集成 Fidelity Layer 到生产 DAG

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
