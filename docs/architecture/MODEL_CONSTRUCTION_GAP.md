# MODEL_CONSTRUCTION_GAP — 模型构造差距分析
> Version: v1.0 | Status: Frozen | Updated: 2026-09-10

> 日期：2026-09-10 ｜ 状态：**ANALYSIS COMPLETE**

---

## 1. 五级正确性框架（L0-L4）

| 级 | 回答 | 含义 | 当前状态 |
|---|---|---|---|
| L0 Syntax | Artifact 合法吗？ | schema/结构校验 | ✅ 已实现 |
| L1 Execution | 代码跑了吗？ | execution_result.status | ✅ 已实现 |
| **L2 Fidelity** | 跑的是声明的模型吗？ | MODEL_IR 声明 ↔ 代码语义 | ⚠️ 已实现但未集成 |
| L3 Mathematical Validity | 数学推导正确吗？ | 推导/量纲/边界/一致性 | ⚠️ 部分（run_numeric_validation）|
| L4 Empirical Adequacy | 数据支持它吗？ | 数据拟合/预测/可验证性 | ⚠️ 依赖盲评 |

## 2. 模块差距分析

### 2.1 已实现但未接入生产

| 模块 | 功能 | 生产调用 | 差距 |
|---|---|---|---|
| `fidelity.py` | L2 Fidelity 检查 | ❌ 只在 CLI | **关键缺口** |
| `diagnosis.py` | 失败诊断 | ❌ 零调用 | 未接入 revision flow |
| `comparison.py` | M1/M2 比较 | ❌ 零调用 | 未接入 model selection |
| `knowledge_guided.py` | 知识引导义务 | ❌ 零调用 | 未接入 candidate generation |
| `revision.py` | 修订草案 | ❌ 零调用 | 未接入 revision flow |

### 2.2 L2 Fidelity 具体差距

**当前状态**：
- `fidelity.py:check_fidelity` 实现了 MODEL_IR → output_key_exists 检查
- `fidelity.py:verify_fidelity` 是端到端函数
- `codegen.py:run_code_pipeline` 调用了 verify_fidelity
- **但** `handlers.py` 的 `do_model_execution` 从未调用 fidelity

**缺失的集成**：
```python
# handlers.py do_model_execution 中应该有：
vr = verify_fidelity(
    self.project_dir,
    model_ir_data,
    exec_artifact_id,
    output_mapping=code_data.get("output_mapping"),
)
if vr["fidelity_status"] == "misaligned":
    return NodeResult(FAIL, f"L2 Fidelity misaligned: {vr}")
```

### 2.3 L3 Mathematical Validity 差距

**当前状态**：
- `run_numeric_validation` 可以检查 constraint/objective/domain
- 但需要外部注入 `validation_spec`（具体数值规格）
- 对于无参考解的题目，L3 只能做结构检查

**缺失的能力**：
- 量纲分析（dimensional analysis）
- 边界条件检查（boundary condition verification）
- 推导一致性检查（derivation consistency）
- 这些需要更深层的数学理解，可能需要 LLM 参与

### 2.4 L4 Empirical Adequacy 差距

**当前状态**：
- 依赖盲评（LLM evaluator）
- κ 值持续低于 0.6 阈值
- K003 证明 L4 正效应来自结构化验证计划的字段填充

**缺失的能力**：
- 真实数据拟合检验（对有参考解的问题）
- 预测能力验证（out-of-sample prediction）
- 灵敏度分析的机械验证（不是 Agent 声称）

## 3. 构造循环完整性评估

### 完整循环路径

```
Problem → Problem Repr → Candidates → Selection → MODEL_IR
→ Code → ExecutionPlan → Execution → ExecutionResult
→ Fidelity (L2) → Validation (L3) → Evidence → Gate
→ Failure → Diagnosis → Revision → New MODEL_IR → Re-execution
```

### 各环节状态

| 环节 | 状态 | 接通生产? |
|---|---|---|
| Problem → Problem Repr | REAL | ✅ |
| Problem Repr → Candidates | REAL | ✅ |
| Candidates → Selection | REAL | ✅ |
| Selection → MODEL_IR | REAL | ✅ |
| MODEL_IR → Code | REAL（外部注入）| ✅ |
| Code → ExecutionPlan | REAL | ✅ |
| ExecutionPlan → Execution | REAL | ✅ |
| Execution → ExecutionResult | REAL | ✅ |
| ExecutionResult → **Fidelity** | **NOT INTEGRATED** | ❌ |
| ExecutionResult → Validation | REAL | ✅ |
| Validation → Evidence | REAL | ✅ |
| Evidence → Gate | REAL | ✅ |
| Gate → Failure Diagnosis | **NOT INTEGRATED** | ❌ |
| Failure → Revision Draft | **NOT INTEGRATED** | ❌ |
| Revision → New MODEL_IR | REAL（外部注入）| ✅ |
| New MODEL_IR → Re-execution | REAL | ✅ |
| Model Comparison | **NOT INTEGRATED** | ❌ |

### 接通率

- **已接通生产**：11/16 = 69%
- **未接通生产**：5/16 = 31%（Fidelity, Diagnosis, Revision Draft, Comparison, Knowledge Guided）

## 4. 构造能力评估

### 4.1 表示层（L1 Representation）

**能力**：MODEL_IR Builder 强制 18 字段 + L2 数学公式检查 + schema validation。
**证据**：K002 S 臂 coverage gate 36/36 = 100%。
**评价**：表示层能力强，但 K002/K003 证明纯表示不产生建模价值。

### 4.2 构造层（L2 Construction）

**能力**：Candidate Arena 生成 3-4 候选，Method Arena 机械选型。
**证据**：K003 L2 层 structured arm 显著低于 F 臂（Δ=−0.41）。
**评价**：结构化构造流程可能限制了 LLM 的自由建模能力。

### 4.3 执行层（L3 Execution）

**能力**：LocalPythonAdapter 真实 subprocess 执行。
**证据**：K003 exec_success_rate = 1.0（66/66）。
**评价**：执行层可靠，但 Fidelity Layer 未集成，无法验证"执行的是否是声明的模型"。

### 4.4 验证层（L4 Validation）

**能力**：run_numeric_validation + Evidence Gate E1-E9。
**证据**：K003 SV−F VAL = +39.92（巨大正效应）。
**评价**：验证层是最强的层。但 κ=0.260 表明盲评工具不可靠。

### 4.5 修订层（L5 Revision）

**能力**：diagnosis → revision_draft → supersede → re-execution。
**证据**：VS-001 M1 FAIL → M2 PASS 闭环已验证。
**评价**：修订循环机制存在但 diagnosis/comparison/revision 未接入生产。

## 5. 关键结论

1. **L2 Fidelity 是最大缺口**：它是 LinHoMo 独有指标，已实现但未接入
2. **31% 的构造循环未接通**：5 个模块是死代码
3. **验证层最强但测量工具最弱**：E1-E9 机械检查强，但盲评 κ 不达标
4. **表示层能力≠建模能力**：K002/K003 已证明
5. **执行层可靠但不完整**：能跑但不知道跑的对不对（缺 Fidelity）


---

## 附录：引用文件路径映射（审计可追溯性）

本文档中的模块引用使用简写（handlers.py:837 表示 837 行）。完整真实路径如下（已逐行核对）：

| 简写 | 真实路径 | 核对结果 |
|---|---|---|
| handlers.py | core/runtime/execution/handlers.py（1737 行） | L817/837/843/876/1423 全部吻合 |
| engine.py | core/runtime/execution/engine.py（417 行） | L96/281/349 吻合（L281/L349 重复 unblock 属实） |
| session.py | core/runtime/execution/session.py（298 行） | L96 吻合 |
| idelity.py | core/runtime/execution/fidelity.py（227 行） | 存在 |
| codegen.py | core/runtime/execution/codegen.py | 存在 |
| integrity_gate.py | core/validators/modules/integrity_gate.py（428 行） | L118/161/172/255/345 全部吻合 |
| indings.py | core/runtime/writing/findings.py（212 行） | L121/147/157 吻合 |
| selection.py | core/runtime/modeling/selection.py（141 行） | L60/80/108/120 吻合（chosen=recs[0] 属实） |
| comparison.py | core/runtime/modeling/comparison.py | L22 吻合 |
| knowledge_guided.py / diagnosis.py / 
evision.py / candidates.py / model_ir.py | core/runtime/modeling/ | 存在（生产零调用见正文） |
