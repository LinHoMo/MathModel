# EXPERIMENT_STRATEGY — 实验策略
> Version: v1.0 | Status: Frozen | Updated: 2026-09-10

> 日期：2026-09-10 ｜ 状态：**DESIGN FROZEN**

---

## 1. K001/K002/K003 实验总结

### K001: Knowledge Efficacy — NULL

| 指标 | 值 | 解读 |
|---|---|---|
| Δ_K | +2.14 | CI 触 0，p=1.0 |
| Method hit rate | 22% | 知识卡 barely 影响选择 |
| Adoption rate | 66% | 检索到时大多被改造 |
| **结论** | **NULL** | 知识注入无显著建模增益 |

**为什么是 NULL**：
- 知识卡作为 Constraint/Prior 的设计哲学正确
- 但检索→注入→使用的链路有瓶颈
- 可能是检索失败（知识卡未被找到）而非知识无用

### K002: Representation Efficacy — INVALID (Measurement Failure)

| 指标 | 值 | 解读 |
|---|---|---|
| S−F MCQ | −4.85 | 显著负 |
| L3 format asymmetry | S=4.5, F=5.8 | JSON 暴露无执行证据 |
| κ | 0.4345 | < 0.6 |
| **结论** | **INVALID** | 测量结构问题，不是能力发现 |

**为什么是 INVALID**：
- 无执行产物时 L3/L4 不可测量
- S 臂 JSON 的结构化字段被盲评更严格审视
- F 臂自由文本可叙述性声称执行/验证

### K003: Construction+Execution — MIXED

| 指标 | 值 | 解读 |
|---|---|---|
| S−F MCQ | +3.76 | 显著正（但全来自 L4）|
| S−F L2 | −0.41 | 显著负（结构化伤害构造文本）|
| SV−F VAL | +39.92 | 巨大正（验证计划字段填充）|
| κ | 0.260 | < 0.6 |
| **结论** | **MIXED** | L2 负 + L4 正 + κ 不达标 |

**为什么是 MIXED**：
- L4 正效应部分是循环论证（SV 强制字段 → L4 评分字段）
- L2 负效应是真实发现（结构化伤害构造文本质量）
- L2 负 + L4 正 = MCQ composite 为正，但分层看结论不同

## 2. 三实验综合结论

```
"结构化表示本身 ≠ 建模能力" (K002 证明)
"验证义务 + 执行闭环可能比表示格式更重要" (K003 证明)
"Runtime/Evidence 层是 LinHoMo 的真正护城河" (三实验共同指向)
```

## 3. 下一阶段实验策略

### 3.1 Constructor-Independent Benchmark（最重要）

**目标**：区分 Agent 能力 vs LinHoMo Runtime 增益

**设计**：
```
同一批竞赛题（8 题）
× 不同 Constructor（4 种）
× 有/无 LinHoMo Runtime（2 种）
= 64 runs

Constructor:
  A = MathModelAgent (free-text → code)
  B = Claude Code (CLAUDE.md 指令)
  C = Reference Constructor (minimal, LLM-free, 确定性)
  D = Human expert

Runtime 条件：
  With = Constructor + LinHoMo (Execution → Fidelity → Validation → Evidence)
  Without = Constructor 裸输出（盲评直接评）
```

**度量**：
- MCQ composite (L1-L4)
- L2 Fidelity score
- exec_success_rate
- validation_pass_rate
- correction_count (revision rounds)
- Paper quality (blind evaluation)

**预期发现**：
- 裸 Constructor vs Constructor+Runtime 的差值 = LinHoMo 增益
- 不同 Constructor 的差值 = Agent 能力差异
- 交互效应 = Runtime 对不同 Agent 的差异化增益

### 3.2 Fidelity Measurement（关键缺口）

**目标**：测量 MODEL_IR↔Code 的 L2 Fidelity 在真实构造中的分布

**设计**：
```
K003 的 66 runs
× 对每个 S/SV run 计算 fidelity_score
× 对 F arm 计算 "unverifiable"（无结构化声明）
× 与盲评 L2 score 比较
```

**预期发现**：
- Fidelity score 与盲评 L2 score 的相关性
- 是否存在"execution success but fidelity misaligned"的案例
- Fidelity 作为自动质量指标的可行性

### 3.3 Knowledge Efficacy v2（重试 K001）

**目标**：验证知识卡在改进检索后是否有效

**设计**：
```
K001 的 3 题
× 2 条件：直接注入（无检索） vs 检索后注入
× 3 rep
= 18 runs

直接注入 = 把知识卡内容直接放入 prompt（绕过检索）
检索后注入 = 当前 KnowledgeRetriever 流程
```

**预期发现**：
- 如果直接注入有效但检索后无效 → 检索是瓶颈
- 如果两者都无效 → 知识卡内容需要改进
- 如果两者都有效 → 当前检索机制有问题

## 4. 测量工具改进

### 4.1 盲评 κ 提升

**目标**：κ ≥ 0.6

**方法**：
1. 扩充校准集（当前 5 份 → 15 份）
2. 增加评分维度显式化（每个维度给出具体判定规则）
3. 增加 evaluator 数量（3 → 5）
4. 考虑用确定性检查替代主观维度（L4.1/L4.5 可以从 execution_result 自动计算）

### 4.2 确定性指标替代盲评

对于可以机械判定的维度，用确定性检查替代盲评：

| 维度 | 盲评 | 确定性替代 |
|---|---|---|
| L4.1 Baseline comparison | evaluator 判断 | execution_result 数值比较 |
| L4.5 Claim-evidence map | evaluator 判断 | Evidence Graph 机械遍历 |
| L1.3 Code executable | evaluator 判断 | subprocess 真实执行 |
| L2.7 Mechanism correctness | evaluator 判断 | MODEL_IR 结构检查 |

## 5. 实验伦理

### 诚实原则

1. 实验结果是什么就报什么，不为了"好看"而调参
2. κ < 0.6 必须在报告中明确声明测量限制
3. L4 正效应如果是循环论证，必须说清楚
4. 负结果（K001 NULL, K002 INVALID）和正结果（K003）同等重要

### 预注册原则

1. 所有实验必须预注册（终点/对比/统计方法/决策门）
2. 预注册后不修改（除非有 RFC 审批）
3. 敏感性分析必须预先指定


---

## 附录：引用文件路径映射（审计可追溯性）

本文档中的模块引用使用简写（handlers.py:837 表示 837 行）。完整真实路径如下（已逐行核对）：

| 简写 | 真实路径 | 核对结果 |
|---|---|---|
| handlers.py | src/modeling_harness/runtime/execution/handlers.py（1737 行） | L817/837/843/876/1423 全部吻合 |
| engine.py | src/modeling_harness/runtime/execution/engine.py（417 行） | L96/281/349 吻合（L281/L349 重复 unblock 属实） |
| session.py | src/modeling_harness/runtime/execution/session.py（298 行） | L96 吻合 |
| idelity.py | src/modeling_harness/runtime/execution/fidelity.py（227 行） | 存在 |
| codegen.py | src/modeling_harness/runtime/execution/codegen.py | 存在 |
| integrity_gate.py | src/modeling_harness/validators/modules/integrity_gate.py（428 行） | L118/161/172/255/345 全部吻合 |
| indings.py | src/modeling_harness/runtime/writing/findings.py（212 行） | L121/147/157 吻合 |
| selection.py | src/modeling_harness/runtime/modeling/selection.py（141 行） | L60/80/108/120 吻合（chosen=recs[0] 属实） |
| comparison.py | src/modeling_harness/runtime/modeling/comparison.py | L22 吻合 |
| knowledge_guided.py / diagnosis.py / 
evision.py / candidates.py / model_ir.py | src/modeling_harness/runtime/modeling/ | 存在（生产零调用见正文） |
