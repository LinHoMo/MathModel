---
name: problem-parser
description: '解析赛题文件为结构化 question_spec.json，消除题意歧义。数学建模流程的第一步，任何赛题开工时先用它。'
hand: modeler
utg_layer: L1
stage: 1
inputs:
  - inputs/赛题文件 (PDF/Word/TXT)
outputs:
  - work/question_spec.json
  - work/ambiguity_prescreen.md
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> modeler problem-parser`
- **输入**：赛题文件 inputs/
- **输出**：`work/question_spec.json`
- **核心步骤**：1. 读赛题 → 2. 抽取子问题/变量/约束 → 3. 标出歧义处并给出 ≥2 种解释 → 4. 写 question_spec.json
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Problem Parser

## Role

赛题结构化解析：把自然语言赛题转译为结构化规约，从源头消除输入语义歧义。

## UTG Layer

L1 形式化规约层。本层目标是在建模之前消除三类输入风险：
- **语义歧义**：题面模糊表述（如"合理""适当"）必须显式化为可量化约束。
- **隐含矛盾**：题面多处要求之间潜在的冲突必须在规约中标注。
- **信息缺失**：未给出的参数、边界、单位必须显式列为"需假设/需反演"项，不得静默跳过。

本 agent 的输出 `question_spec.json` 是后续所有 agent 的唯一事实源。

## Contract

- **输入**：项目根 `inputs/` 目录下的赛题文件（PDF/Word/TXT）。PDF 用 `Read` 工具直接读取；扫描版 PDF 需 OCR 或图片描述。
- **输出**：`work/question_spec.json`，必须符合 `core/schemas/question_spec.schema.json`。
- **必填顶层字段**：`metadata` / `background` / `problems` / `constraints` / `data` / `delivery`。

## Procedure

### Step 1: 读取赛题原文

- 读取 `inputs/` 下赛题文件，提取题目背景、问题要求、数据说明、提交要求。
- 确认赛题来源可靠（CUMCM/MCM/ICM 等官方渠道）。

### Step 2: 结构化解析

- 调用 `core/knowledge/validation/problem_spec_parser.py` 的 `ProblemSpecParser.parse(text)` 生成六段式 spec。
- 子问题只认题面明确编号的顶层问题（"问题一/问题二"或"Question 1"），不臆造细分。

### Step 3: 消除歧义与补缺

- 每个输入/输出变量必须给出 `name/type/unit/range`，单位缺失则标 `"dimensionless"` 并记入待假设项。
- 隐含约束（物理守恒、几何边界、速度上限等）从题面抽取后写入 `constraints.global_constraints`。
- 题面模糊词（"合理""适当""尽量"）转译为可量化表达式，无法量化则标注待假设。
- 歧义处必须列出 **≥2 种候选解释**，并用快速验算 / 逻辑递进裁决最终采用项（铁律 M8 前置）：记录模糊表述、两种解释、验算过程、最终解释。

### Step 3.5: 假设敏感性预检（Hypothesis Sensitivity Pre-check）

> 借鉴 MathModelAgent-main `2analysis-modeling/SKILL.md` Step 2 流程，消除「拿到题就直接定模型」的风险。

对每个影响建模方向的歧义，执行以下**四步裁决**流程：

1. **列出模糊表述**：找出题面中所有可能影响建模方向的模糊表述（"不超过""合理范围内""尽可能""根据实际情况"等）。
2. **给出至少两种解释**：每个模糊表述至少给出 2 种数学上可行的解释。
3. **快速验算与递进性检查**：
   - 对每种解释做量级估算（数量级是否合理？）
   - **关键检验**：如果后续问题新增资源/约束/场景，当前解释下新增条件是否会产生边际效应？如果某解释让后续新增条件几乎无效，则需重新审视该解释。
4. **最终裁决**：选择一种解释作为建模基础，记录裁决理由；同时将被否决的解释及其风险写入 `question_spec.json` 的 `ambiguities_rejected` 字段。

预检结果写为 `work/ambiguity_prescreen.md`（供 type-classifier / method-matcher 消费），格式：

```markdown
## 假设敏感性预检

### 模糊表述 1：[题面原文]

#### 解释 A：[说明]
- 快速验算：[量级估算或逻辑推导]
- 递进性检查：[如果后续 q2/q3 新增 XX，此解释下 YY 会怎样]

#### 解释 B：[说明]
- 快速验算：[量级估算或逻辑推导]
- 递进性检查：[...]

#### 最终采用：解释 [A/B]
- 裁决理由：[为什么选这个]

### 绘制的图像和对比表格
- [如有辅助理解的简图或变量关系矩阵，在此说明]
```

**递归验证**：如果某个假设会让后续问题的新增条件在数学上几乎无影响（新增资源 → 目标值不变），**必须回头调整解释**，不得跳过。

### Step 4: 一致性自校

- 调用 `ProblemSpecParser.validate(spec)` 检查必填字段、子问题数量、背景长度、关键词数量。
- 确保 `metadata.topic_type` 暂以初判值填入（最终判定由 type-classifier 给出）。

### Step 5: 导出

- 用 `ProblemSpecParser.to_json(spec, path="work/question_spec.json")` 写出，确保 JSON 可被 schema 校验通过。

## Self-Check

- [ ] `work/question_spec.json` 符合 `core/schemas/question_spec.schema.json` 全部 required 字段
- [ ] `metadata` 含 contest/year/topic_id/topic_type/language 五项
- [ ] 每个子问题含 description(>=10字)/input_variables/output_variables/constraints/dependencies
- [ ] `background.domain_keywords` 至少 3 个，`background.context` >=20 字
- [ ] `sub_problem_count`（隐含于 problems 数组长度）与实际识别的子问题数一致
- [ ] 隐含约束已显式化（守恒律、边界、上限等不再埋在自然语言里）
- [ ] 歧义处已列出 ≥2 种候选解释，并用验算/逻辑裁决最终采用项（铁律 M8 前置）
- [ ] 歧义处至少给出 `get("modeling.ambiguity_min_interpretations", default=2)` 种解释（从 env 读取，默认 2）
- [ ] 每种解释含验算裁决方案：明确验算步骤、判定标准、裁决结论
- [ ] 单位缺失项已标注，未静默跳过
- [ ] 假设敏感性预检（Step 3.5）已执行：`work/ambiguity_prescreen.md` 已生成，覆盖所有影响建模方向的模糊表述
- [ ] 每个模糊表述的「递进性检查」已验证：新增后续条件不会无效化
- [ ] 被否决的解释已写入 `question_spec.json` 的 `ambiguities_rejected` 字段

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "modeler",
  "stage": 1,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "problem-parser",
      "stage": 1,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/knowledge/validation/problem_spec_parser.py` —— 解析与校验实现
- `core/schemas/question_spec.schema.json` —— 输出结构契约

## Iteration

当 `validate()` 返回 issues 时：
1. 背景过短 → 扩充题面摘录至 >=20 字。
2. 关键词不足 3 个 → 补充领域术语。
3. 子问题描述过短 → 补全输入/输出/约束。
4. 修正后重新 `parse()` + `validate()`，直至 `valid == True` 再导出。

## External Skills

本 agent 可使用以下外部 skill：

- **pdf-parser**: 解析赛题 PDF 文件
  - 类型: python
  - 必需: false
  - 降级策略: 使用 PyPDF2 内置解析，或使用用户提供的文本版本
