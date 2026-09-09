# 战略裁决记录：P1 Model Construction Runtime（2026-09-09）

> 来源：用户对 GitHub main 实际代码/架构复核后的指令（含三仓库审计结论延续）
> 状态：**已批准为当前最高优先级** · K002 冻结**暂缓**

## 一、核心判断

LinHoMo = Research Runtime + Modeling Semantics + Evaluation Infrastructure，
还不是 Mathematical Modeling Engine。缺的中间段：

```
Model Construction → Implementation → Execution → Validation → Revision
```

## 二、用户明确否定的方向（红线）

- ❌ 新 Agent（现有 analyst/modeler/experimenter/critic/writer 足够）
- ❌ 新顶层架构 / 新 Workflow 层
- ❌ 新大批 Skills / 更多 Paper Intelligence / 更多 schema
- ❌ 为了"看起来完整"增加功能

## 三、用户明确要求的方向

1. **Model Lifecycle 作为核心对象**（不是 Agent Workflow）：
   Problem → Question → Problem Representation → Model Candidates → Model Selection
   → Model Artifact → Implementation → Execution → Validation → Evidence
   → Model Evaluation → Model Revision → Model v2 → … → Claim → Paper
2. **Model Construction Protocol**：每一步产出什么 Artifact（Q001/A001/M001/CODE001/E001/EXEC001/R001/C001），进入 Evidence Graph。
3. **Model-to-Code Fidelity 第一优先级**：Execution Success ≠ Implementation Correctness ≠ Model Validity；先做结构保真检查（objective/variables/constraints/solver 的 declared vs implemented）。
4. **四层验证**：L0 Schema / L1 Execution / L2 Model Fidelity / L3 Mathematical Validity / L4 Empirical Adequacy。
5. **自动修模闭环**：M1→E1→V1 FAIL→M2→E2→V2 PASS，Evidence Graph 记录谱系。
6. **Candidate Model Set + Decision Artifact**：ModelSet[M001,M002,M003] + Decision(alternatives/criteria/evidence/chosen/confidence)。
7. **Method Selection → Model Instantiation 是当前最核心能力缺口**：Problem Features → Candidate Methods → Structural Compatibility → Candidate Models → Model Instantiation → MODEL_IR。

## 四、K002 处置（暂缓，非取消）

- 预检已完成（G2 PASS、区分度 6/6、格式不对称发现）——**冻结暂缓**
- K002 应升级为 **Model Construction 实验**：F vs S 比较扩展到
  Model Construction Quality / Model-Code Fidelity / Execution Success / Validation Success / Revision Count / Final Model Quality
- 冻结前置：P1 Model Construction Runtime 打通后 + 盲评呈现层统一后

## 五、既定路线（6 阶段，用户重排）

| 阶段 | 内容 | 状态 |
|---|---|---|
| P0-E | Executable Runtime（MODEL_IR→Code→Execution→Result→Evidence） | ✅ 已完成（ad917d2 起） |
| P0-E2 | Execution Integrity（Replay/Recovery/Env Manifest/RunRecord/Failure Injection） | 待做 |
| **P1** | **Model Construction Runtime（Candidate Model → Decision → MODEL_IR）** | **当前** |
| P2 | Model-to-Code Fidelity（结构保真 → 语义/数学保真） | 待做 |
| P3 | Model Validation Runtime（Validation Suite → Evidence Graph） | 待做 |
| P4 | Model Revision Loop（FAILURE→Diagnosis→Revision→Re-execution→Validation） | 待做 |
| P5 | K002（Representation → Model Construction Capability） | 暂缓至 P1-P4 后 |

## 六、下一步动作（已批准）

1. **Model Construction Gap Audit**（代码级、逐函数追踪 10 环节 × 10 问）→ 已委派 Organizer
2. 产出 **P1 Model Construction Runtime Implementation Plan**（按真实文件+类+函数+测试+commit 顺序）
3. 按计划打通 Model Construction Loop

## 七、持续有效的工程哲学

- **The Agent Is Not The State**：Artifact + Evidence + Event + State Projection = research state；Agent/LLM/Handler 只是 Executor，永不是事实来源。
- Evidence 是 execution substrate 产生的，不是 Agent 写出来的。
- infra 不冒充 capability：每个新基础设施必须回答"它改变了哪个可测量的 Model Construction behavior"。
