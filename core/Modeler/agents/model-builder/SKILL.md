---
name: model-builder
description: '建立数学模型：从基本定律推导公式、定义符号与量纲、列出边界条件，产出 model_draft.md。'
hand: modeler
utg_layer: L3
stage: 4
inputs:
  - work/method_candidates.json
outputs:
  - work/model_draft.md
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> modeler model-builder`
- **输入**：work/method_candidates.json
- **输出**：`work/model_draft.md`
- **核心步骤**：1. 从基本定律推导 → 2. 定义符号与量纲 → 3. 列边界条件 → 4. 写 model_draft.md
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Model Builder

## Role

建立数学模型：为每个子问题写出公式、符号定义与边界条件，输出结构对齐 MODEL_SPEC 的草稿。

## UTG Layer

L3 过程验证层。本层确保推导链路完整且每步有依据，对应铁律 M3/M4/M5：
- 推导链路：基本定律 → 数学模型 → 边界条件 → 求解方法 → 验证，不得跳步。
- 符号一致性：一个符号只表示一个物理量，全文统一含单位。
- 边界条件必须明确列出（初始/约束/边界）。

> **借鉴 MM-Agent（NeurIPS 2025）Actor-Critic 机制**：model-builder 采用「Actor 推导 → Critic 批判 → Improvement 改进」的迭代循环，默认 1 轮（env `modeling.problem_modeling_round`），最多 3 轮。每轮后产出更严谨的推导。

## Contract

- **输入**：`work/method_candidates.json`。
- **输出**：`work/model_draft.md`（主产物）+ `work/model_draft_critique.md`（Critic 审计记录）。
- **草稿结构**对齐 `core/schemas/model_spec.schema.json` 的 `assumptions` / `symbols` / `models` / `sub_problems` / `verification` 字段（草稿形态，可含未评分假设，待 assumption-validator 补分）。
- 每个子问题必须有 `formulas`（>=1）、`boundary_conditions`、`solution_approach`。
- **Actor-Critic 轮次**：默认 1 轮（env `modeling.problem_modeling_round`），最多 3 轮。

## Procedure

### Step 1: 确定选中模型

- 读 `work/method_candidates.json`，对每个子问题从候选中选定方法（取 `fivedim_score` 最高分者，`selected=true`）。
- 若多个候选同分差距 <0.5，则全部进入本步起草对比，最终由 spec-auditor 选定。

### Step 2-6: Actor 推导（首轮）

> 本步骤执行一轮完整推导，产出 work/model_draft.md

- **Step 2：写假设与必要性** — 为每个子问题列出模型假设，每个假设必须有 `necessity`（>=10 字），编号统一 `H1, H2...` 格式。
- **Step 3：写公式与推导** — 参考 `core/knowledge/methodology/mathematical-derivation.md`，从基本定律推导到最终模型，每步注明依据。每个子问题至少 1 个公式。
- **Step 4：注册符号** — 用 `core/knowledge/validation/symbol_registry.py` 注册全部符号，调用 `check_consistency()` 确认无冲突。
- **Step 5：校验公式语法** — 用 `core/knowledge/validation/formula_checker.py` 逐条校验公式括号、LaTeX 命令完整性。
- **Step 6：列边界条件** — 明确 `boundary_conditions`（初始/约束/边界），给出 `solution_approach`。

### Step 3: Critic 批判（Actor-Critic 环，借鉴 MM-Agent 的 ProblemUnderstanding.modeling_critic）

> 借鉴 MM-Agent 的「建模批判」机制，对首轮推导做**纯批判**——只挑缺陷，不给建议。

对每个子问题的推导执行以下检查，产出 `work/model_draft_critique.md`：

1. **推导深度检验**：推导是否从基本定律出发？有无跳步？简略步骤是否影响可复现性？
2. **公式正确性**：方程两边量纲是否守恒？初始/边界条件的数学表达是否完整？
3. **假设合理性**：每个假设是否必要？有无遗漏关键限制？假设与题面约束是否一致？
4. **符号一致性**：一个符号是否只表一个物理量？国际单位是否统一？符号表与正文是否一致？
5. **国赛评分对齐**：对照 `core/knowledge/review/scoring-criteria.md`，是否存在已被明确标注的扣分项？（如「物理/反演问题须有可靠性验证」）

批判输出格式（写入 `work/model_draft_critique.md`）：
```
## 子问题 N 批判

- **[推导跳步]**：从 XX 定律直接跳到 YY 解，缺少 ZZ 中间步骤
- **[量纲不一致]**：公式 (3) 左侧为 m/s²，右侧退化后为 kg·m
- **[假设遗漏]**：未考虑题面「XX 不能超过 YYY」的约束
- **[评分风险]**：2025 B 评阅要求「用估计值反算」，当前推导缺少可靠性验证步骤
```

### Step 4: Improvement 改进（Actor-Critic 环）

> 基于 Critic 的批判，**直接改进** model_draft.md。改进时不提及上一版缺陷，只给出修正后的推导。

读取 `work/model_draft_critique.md`，逐条修正 `work/model_draft.md`：
- 推导跳步 → 补充中间步骤与依据
- 量纲不一致 → 修正公式使其守恒
- 假设遗漏 → 追加假设并补充必要性
- 评分风险 → 追加评阅要求的验证步骤

改进后重新跑 Step 4（符号一致性）+ Step 5（公式语法），再写回 `work/model_draft.md`。

### Step 5: 多轮迭代控制

```python
from core.env.loader import get
max_rounds = get("modeling.problem_modeling_round", default=1)  # 默认 1 轮，最多 3
```

- 第 1 轮：Step 2-6 全流程
- 第 2-n 轮：仅 Step 3（Critic）→ Step 4（Improvement）循环
- **提前终止条件**：Step 3 Critic 无新缺陷 → 可跳过剩余轮次
- **强制终止**：完成 max_rounds 轮后必须终止，即使仍有缺陷

### Step 6.5: 编写代码实现任务清单

在 `work/model_draft.md` 末尾（spec-auditor 渲染前提前占位）增加第 10 章「代码实现任务清单」，格式对齐 `core/Modeler/templates/MODEL_SPEC_TEMPLATE.md` ## 10。

每个子问题必须填写：
- **任务**：一句话可执行的求解目标
- **输入**：数据来源（`inputs/` 文件名 + 字段名）、物理参数值与单位
- **输出**：变量名 + 含义 + 单位 + 写入 `figures/all_results.json` 的键路径（如 `results.problem_1.values.xx`）
- **方法**：算法名 + 关键步骤（1-2-3），引用 `core/knowledge/methodology/` 路径
- **校验**：约束检查清单（逐条列出）、预期量级（如 `v ∈ [0.5, 3.0] m/s`）、物理不可为负 / 为零的边界

**工程约束**：若本题为优化类，必须写明每个变量的物理上下界（参考 TYPE-ANTIPATTERNS-CHECKLIST.md O1-O8）。

### Step 6.7: 编码前防错自检（M8 前置）

读取 `core/knowledge/pitfalls/TYPE-ANTIPATTERNS-CHECKLIST.md`，对当前题型做映射检查：
- 优化类 → O1-O8 逐项确认已在第 10 章任务清单中落地（变量上界 / 整数取整策略 / 约束回代）
- 预测类 → S1-S6（训练测试划分方式已明确？防数据泄露？）
- 评价类 → E1-E4（正向/负向指标方向是否已列表？）
- 图论类 → G1-G4（有向/无向？负权？）
- 机理/仿真 → D1-D4（单位、初边值条件、步长收敛？）

发现未覆盖的风险，在 task_list 的"校验"列追加。

### Step 7: 导出草稿

- 写最终版 `work/model_draft.md`，章节对齐 `core/Modeler/templates/MODEL_SPEC_TEMPLATE.md`。
- 第 10 章「代码实现任务清单」已完整填写（每个子问题一张表 + 工程优化铁律通用提示）。
- 附 `work/model_draft_critique.md`（Critic 全过程产物，供 spec-auditor 审计）。

## Self-Check

- [ ] 每个子问题 `formulas` 数组至少 1 个公式
- [ ] 每个假设有 `necessity` 字段且 >=10 字（M2 前置）
- [ ] `symbols` 至少 1 个，含量纲，`SymbolRegistry.check_consistency()` 无冲突（M4）
- [ ] 公式语法通过 `FormulaChecker.check()`（无括号失配、无空参数）
- [ ] 每个子问题 `boundary_conditions` 明确列出（M5）
- [ ] 推导从基本定律到最终模型，每步有依据（M3）
- [ ] 选中模型标注了 `selected` 与选择依据（基于 `fivedim_score` 最高分）
- [ ] 启发式算法未直接宣称全局最优（M6）
- [ ] Actor-Critic 环已执行：`work/model_draft_critique.md` 已生成
- [ ] Critic 发现的缺陷已在 Improvement 中修正或标注不可修正原因
- [ ] 迭已达 `max_rounds` 轮或 Critic 无新缺陷（满足其一即终止）
- [ ] 五维评分最高分候选已被选为主方案（或同分差距<0.5 时多方案进下游）
- [ ] 第 10 章「代码实现任务清单」已生成，每个子问题含任务/输入/输出/方法/校验五列
- [ ] 工程优化铁律已写入第 10 章末尾（优化变量上下界 / 取整策略 / 约束回代 / 求解器成功≠最优）
- [ ] 题型防错速查已按题型（TYPE-ANTIPATTERNS-CHECKLIST.md）过一遍，风险已并入校验列

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "modeler",
  "stage": 4,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "model-builder",
      "stage": 4,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/knowledge/methodology/mathematical-derivation.md` —— 推导规范
- `core/knowledge/methodology/CUMCM-HMML.md` —— 三级方法知识库（HMML 节点含「常见扣分点」，Critic 步骤引用）
- `core/knowledge/review/scoring-criteria.md` —— 评分细则（Critic 步骤引用，对齐评阅扣分点）
- `core/knowledge/validation/symbol_registry.py` —— 符号注册与一致性
- `core/knowledge/validation/formula_checker.py` —— 公式语法检查
- `core/schemas/model_spec.schema.json` —— 草稿结构对齐目标
- `core/Modeler/templates/MODEL_SPEC_TEMPLATE.md` —— 章节模板

## Iteration

当公式语法、符号一致性检查失败或 Critic 发现缺陷时：
1. 公式语法错 → 按 `FormulaChecker` 报错位置修正，重新 `check()`。
2. 符号冲突 → 统一符号命名后重新 `register()` + `check_consistency()`。
3. 推导跳步 → 按 `mathematical-derivation.md` 补全中间步骤。
4. Critic 发现缺陷 → 按 Step 4 (Improvement) 直接改进，然后重跑 Step 4+5。
5. 降档方法被选中（AHP/灰色预测） → 回退 method-matcher 检查避档是否遗漏。
6. 修正后重写 `work/model_draft.md`，再进入 assumption-validator。
