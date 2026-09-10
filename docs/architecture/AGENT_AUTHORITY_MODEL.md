# AGENT_AUTHORITY_MODEL — Agent 权限矩阵

> 日期：2026-09-10 ｜ 状态：**DESIGN FROZEN**
> 核心原则：**Agent Claim ≠ System Fact**

---

## 1. 权限矩阵

### 1.1 Artifact 写入权限

| Artifact | Agent 可写 | Runtime/Harness 可写 | 原因 |
|---|---|---|---|
| Problem Interpretation | **YES** | - | 外部输入 |
| MODEL_IR | **YES** | - | 外部构造 |
| Code | **YES** | - | 外部构造 |
| Experiment Plan | **YES** | - | 外部构造 |
| Hypothesis | **YES** | - | 外部构造 |
| Revision Proposal | **YES** | - | 外部构造 |
| ExecutionPlan | - | **YES** | 从 MODEL_IR 派生 |
| ExecutionResult | **NO** | **YES** | 只来自真实 subprocess |
| VerificationResult | **NO** | **YES** | 只来自确定性验证 |
| Fidelity Report | **NO** | **YES** | 只来自 Fidelity Layer |
| Evidence Relations | **NO** | **YES** | 只在节点 PASS 后写入 |
| PASS/FAIL Decision | **NO** | **YES** | 只来自 Validator |
| Registry State | **NO** | **YES** | 只通过 Registry API |
| State Machine | **NO** | **YES** | 只通过 refresh_from() |
| Provenance | - | **YES** | 系统级追踪 |
| Claim (synthesized) | **NO** | **YES** | 只从 EXEC/VR 数据合成 |
| Model Status | **NO** | **YES** | 只从 supports edge 推导 |

### 1.2 状态推进权限

| 状态变更 | Agent 可触发 | Runtime 触发 | 条件 |
|---|---|---|---|
| 问题解析完成 | 间接 | YES | problem_analysis 节点 PASS |
| 方法选型 | 间接 | YES | model_selection 节点 PASS + 有 evidence |
| 模型构造完成 | 间接 | YES | model_construction 节点 PASS + 有效 MODEL_IR |
| 代码生成完成 | 间接 | YES | code_generation 节点 PASS + 有效代码 |
| 执行完成 | **NO** | YES | 只来自 subprocess 真实状态 |
| 验证完成 | **NO** | YES | 只来自 VR artifact |
| 证据充分 | **NO** | YES | 只来自 Evidence Gate E1-E9 |
| 模型验证通过 | **NO** | YES | 只从 supports edge 自动推导 |
| ~~论文投影完成~~ | — | — | `paper_projection` 节点已随 v3.2.2 论文链删除，不再适用 |

### 1.3 间接写入通道

Agent 可以通过以下方式间接影响系统：

1. **注入外部产物**：通过 `external_model_irs`/`external_code` dict 注入
2. **Constructor Adapter**：通过 `construct()` 返回 `ConstructionBundle`
3. **Human-in-the-loop**：通过 `approve()` 放行审批节点

**但**：所有注入产物都经过 Runtime 的确定性处理（注册、执行、验证）后
才成为系统状态。Agent 的原始输出永远不直接等于系统状态。

## 2. 违反模式与修复

### 2.1 已确认的违反

| 违反 | 位置 | 严重度 | 修复方案 |
|---|---|---|---|
| `_decision_confidence` 硬编码常数 | handlers.py:837-857 | Medium | 标注 provenance 或移除 |
| `_rank_candidates` 隐含价值判断 | handlers.py:817-835 | Low | 文档化假设 |
| findings.py 硬编码置信度 | findings.py:121/147/157 | Medium | 标注 provenance |
| integrity_gate 经验阈值 | integrity_gate.py:118/161/172/255/345 | Medium | 标注来源或移除 |
| selection.py 公式系数 | selection.py:120 | Low | 标注 provenance |
| Node PASS 基于计数 | handlers.py:725/753/1206 | Low | 增加验证检查 |

### 2.2 "formalized false authority" 清单

以下硬编码常数被确定性脚本包装后产生"客观测量"外观：

| 常数 | 位置 | 声称含义 | 实际来源 |
|---|---|---|---|
| 0.25 | handlers.py:837 | 低置信度 | 无 |
| 0.7 | handlers.py:848 | 单候选置信度 | 无 |
| 0.95 | handlers.py:850 | 高置信度 | 无 |
| 0.8/0.6 | handlers.py:857 | 间距置信度 | 无 |
| 0.8/0.5 | findings.py:121 | 鲁棒性置信度 | 无 |
| 0.15 | integrity_gate.py:118 | 文本相似度 | "经验阈值" |
| 20 | integrity_gate.py:161 | Benford χ² | "经验阈值" |
| 0.999 | integrity_gate.py:172 | R² 过拟合 | 无 |
| 0.30 | integrity_gate.py:255 | AI 写作比例 | 无 |
| 0.10 | integrity_gate.py:345 | 数值可追溯性 | 无 |
| 0.5+0.1*score | selection.py:120 | 选型置信度 | 无 |

**治理原则**：这些常数要么标注明确来源（paper/calibration/data），
要么从确定性评分中移除，要么降级为 advisory（不参与 PASS/FAIL 判定）。

## 3. Agent Authority Invariant（写死）

```
INV-AG1: Agent 的文字输出 ≠ 系统状态
INV-AG2: ExecutionResult.status 只来自 subprocess
INV-AG3: VR.status 只来自 run_checks/run_numeric_validation
INV-AG4: Evidence relations 只在节点 PASS 后写入
INV-AG5: Model status 只从 supports edge 自动推导
INV-AG6: State 只从 Registry + Graph 派生
INV-AG7: 无 provenance 的数字不参与 PASS/FAIL 判定
```


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
