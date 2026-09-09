# P1 前置摸底：Model Construction 链路现状（MainAgent 第一手交叉验证）

> 2026-09-09 · 与 Organizer Gap Audit（o_0001KEhhRew）并行，独立证据
> 结论：**Runtime 核心模块已存在且可运行，缺口在"后半段闭环未接入主路径"**

## 一、已确认存在且可运行（含测试证据）

| 环节 | 模块 | 测试 |
|---|---|---|
| Candidate Model | `core/runtime/modeling/candidates.py`（239 行，CandidateArena，required_evidence 绑定） | 经 handlers 间接覆盖，无直接单测 |
| Model Selection | `core/runtime/modeling/selection.py`（121 行，MethodArena + DecisionLog 历史决策 + shortlist + Decision 登记） | `test_model_selection.py` ✅ |
| Experiment Plan | `core/runtime/modeling/planner.py`（283 行，required_checks/preflight_guards/failure_watchlist/baseline/sensitivity） | 经 test_model_selection 覆盖 |
| Decision Log | `core/runtime/decisions/log.py`（279 行，一等实体、可推翻、持久化 decisions.json） | `test_decision_log.py` ✅ |
| Model→Code Fidelity | `core/runtime/execution/fidelity.py`（227 行，P0-E6，确定性映射检查，LLM-free） | `test_execution_fidelity.py` ✅ |
| Code 登记/执行闭环 | `core/runtime/execution/codegen.py`（193 行，P0-E7：register_code→execute_code→verify_fidelity→run_code_pipeline） | `test_execution_codegen.py` ✅ |

专项验证：4 个测试文件 60 passed（0.99s）。

## 二、调用关系（谁接入了运行时）

- ✅ **已接入 handlers.py / intelligence.py**：candidates / planner / MethodArena / CandidateArena / ExperimentPlanner
  （即：Problem → Candidate → Decision → MODEL_IR → ExperimentPlan 前半段已在 V3 运行时主路径）
- ⚠️ **未接入主路径**：`register_code` / `run_code_pipeline`（codegen.py 闭环目前**只被自身与测试引用**）
  → **P0-E7（Code→Execution→Fidelity）已实现但未接到 orchestrator/handlers 主链**

## 三、核心缺口（P1 主攻方向）

1. **后半段闭环未接线**：MODEL_IR → Code → Execution → Fidelity → Validation → Revision
   的 P0-E7 闭环存在但未进运行时主路径（无端到端入口工具）
2. **Revision 环节**：未见 model 版本化 → 失败诊断 → 新版本的运行时闭环代码（M1→E1→V1 FAIL→M2）
3. **candidates.py / planner.py 无直接单测**（依赖 handlers 间接覆盖，需补）
4. core/runtime/adapters 很薄（openai.yaml 配置 + __init__），符合 LLM-free 定位，无需扩展

## 四、待 Organizer Gap Audit 确认

- 10 环节 × 10 问逐环节证据（是否存在占位/hardcoded）
- 端到端入口（orchestrator DAG 是否真的会触发 candidates→selection→…→codegen）
- P1 Implementation Plan 的具体文件/函数/测试/commit 顺序
