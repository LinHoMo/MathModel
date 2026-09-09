# Knowledge-guided Construction — 正式契约

> 版本：v1.0 ｜ 日期：2026-09-10 ｜ 状态：正式（core/runtime/modeling/knowledge_guided.py）
> 上位原则：Modeling Knowledge Governance v1.1（docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md）
> 前身：P1-M4 演示（research/P15/m4_run/）→ 本契约 + 正式模块（固化）

## 1. 三类接入点

知识卡 → MODEL_IR 的**三类义务接入**，全部可溯源（`source_card` + `knowledge_refs`）：

| 接入点 | 知识来源字段 | MODEL_IR 目标 | 契约要求 |
|---|---|---|---|
| **候选** | `compatible_methods` / `family` / `good_for` | 候选模型提议（family + rationale + knowledge_refs） | 由外部 Model Constructor 在候选生成时引用；本模块不代生成候选 |
| **假设** | `required_conditions` + `prerequisites` | `assumptions[]` | `assumption_id` + `source_card`；type 由文本推断 |
| **义务（验证）** | `validation` | `validations[]` | `validation_id` + `source_card` + `status=required`；type 按关键词推断（sensitivity/convergence/limit/reproducibility/constraint） |
| **风险** | `risks` | `risks[]` | 结构化（level/title/source_card） |
| **依赖** | `requires` | `dependencies[]` | `from_type=knowledge_card` + `from_id` + `relation=requires` |
| **论文投影义务** | `validation`（含 摘要/图表/论文/评审 关键词） | `claim_obligations[]`（不进模型验证义务） | 评审知识归口，不冒充可执行验证 |

## 2. 机械映射（LLM-free）

`map_card_obligations_v2(card)` → 分类义务；`apply_knowledge_obligations(model_ir, cards)`
→ 嵌入 MODEL_IR（合并不覆盖建模者已有声明；补契约 id；追加 dependencies；
写 `knowledge_refs`）。`obligation_provenance(model_ir)` → 可审计清单
（哪些项来自哪张卡）。

## 3. 铁律

1. **知识 = Constraint / Prior，不是答案库**：只产生候选/假设/义务，**不判 PASS、
   不生成数值、不指定"必须用 X"**；最终由执行/验证裁决。
2. **无知识不自动判错**：out_of_catalog / 无引导候选是合法的建模者选择。
3. **knowledge coverage 约束 evaluation，不约束 creativity**：知识卡缺失不阻断构造。
4. **义务是候选声明**：嵌入的义务 `status=required`（待执行），非 `passed`；
   是否满足由 Execution/Validation 产出证据裁决。
5. **全部可审计**：任何声称"知识引导"的 MODEL_IR 必须能通过
   `obligation_provenance` 逐条追溯来源卡。

## 4. 卡接入现状（BZD 5 张全接入）

| 卡 | 主要义务目标 |
|---|---|
| mc-bzd-model-fit | assumptions（适用前提）+ validations（适用性自查）+ risks |
| mc-bzd-validation-obligations | validations（敏感性/误差收敛）+ assumptions（mechanism_known） |
| mc-bzd-failure-modes | validations（量纲/约束逐条）+ risks（量纲错误/遗漏约束） |
| mc-bzd-sensitivity | validations（±10% 扰动/敏感性排序） |
| mc-bzd-judging-criteria | claim_obligations（摘要/图表——论文投影，不进验证义务） |

## 5. 测试与验证

- `tests/unit/test_knowledge_guided.py`：映射正确性 / provenance 完整 /
  边界（无卡、judging-criteria 归口 claim、不覆盖建模者声明）。
- P1-M4 e2e（m4_run）作为集成验证：GUIDED vs UNGUIDED 闭环执行+验证对比。

## 6. 与后续实验的关系

- K003 的 SV 臂 validation_plan 强制义务来自实验设计（非知识卡）；
  知识引导是建模阶段的 Prior 注入，与实验臂正交——**不混用**（避免
  "知识卡义务"与"实验要求义务"confound）。
- Capability Validation（Δscore）中，knowledge-guided 能力以
  `obligation_provenance` 覆盖度与执行后验证义务满足率衡量。
