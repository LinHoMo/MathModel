---
name: spec-auditor
description: '对 MODEL_SPEC.md 做护栏检查与哈希审计，是建模手交付给编程手前的最后一道门禁。'
hand: modeler
utg_layer: L5+L6
stage: 6
inputs:
  - work/model_draft.md
  - work/assumption_validation.json
outputs:
  - output/MODEL_SPEC.md
  - work/audit_log.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> modeler spec-auditor`
- **输入**：work/model_draft.md + 全部中间产物
- **输出**：`output/MODEL_SPEC.md`
- **核心步骤**：1. 渲染 MODEL_SPEC → 2. 护栏检查 → 3. 哈希审计 → 4. 交付 Programmer
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Spec Auditor

## Role

MODEL_SPEC 护栏检查 + 哈希审计：合并草稿与假设评分，输出最终 MODEL_SPEC，并固化全链审计轨迹。

## UTG Layer

L5 运行时护栏 + L6 事后哈希审计。
- **L5**：输出前实时拦截禁用词、占位符、内部路径、AI 痕迹，对应铁律 M7 的可读性护栏。
- **L6**：用 SHA-256 哈希链把全部中间产物（question_spec → type_classification → method_candidates → model_draft → assumption_validation → MODEL_SPEC）串联固化，支持事后篡改检测。

## Contract

- **输入**：`work/model_draft.md` + `work/assumption_validation.json`（并可读全部前置中间产物）。
- **输出**：
  - `output/MODEL_SPEC.md`：最终模型规格说明书，必须符合 `core/schemas/model_spec.schema.json`。
  - `work/audit_log.json`：哈希链审计日志。

## Procedure

### Step 1: 合并与渲染

- 把 `assumption_validation.json` 的四维评分回填到 `model_draft.md` 的每个假设 `validation` 字段。
- 按 `core/Modeler/templates/MODEL_SPEC_TEMPLATE.md` 渲染最终 `output/MODEL_SPEC.md`，确保 5 个必要章节齐全（问题理解/模型假设/符号说明/模型选型/模型建立）。

### Step 2: Schema 校验

- 校验 MODEL_SPEC 内容符合 `core/schemas/model_spec.schema.json` 的全部 required 字段：
  - `problem_understanding`（contest/topic_type/sub_problem_count/sub_problems）
  - `assumptions`（每个含 id/content/type/necessity/validation，validation 含五项评分）
  - `symbols`（>=1，含 symbol/meaning/unit）
  - `models`（>=2 候选，含 name/pros/cons/applicability/selected）
  - `sub_problems`（每个含 method/formulas/boundary_conditions/solution_approach）
  - `verification`（methods/sensitivity_parameters/expected_ranges）

### Step 3: L5 运行时护栏

- 调用 `core/knowledge/validation/guardrails.py`：
  ```python
  from core.knowledge.validation.guardrails import Guardrails
  g = Guardrails()
  g.validate_output(model_spec_text)
  # 必须 g.has_errors() == False
  ```
- 拦截项：禁用词（统一扩充词表，见 `core/Writer/knowledge/writing/forbidden-words.md`）、占位符（TODO/FIXME/TBD/XXX/待补/待补充/待续写/这里补/待完善）、内部路径（.py 文件名/临时目录/`work/`/`_tmp/`/`MODEL_SPEC.md`/`CODE_DELIVERABLES.md`/`PAPER_SPEC.md`/`all_results.json`/`CLAUDE.md`/`AGENTS.md`）、AI 痕迹（"作为AI"/"由AI生成"）。

### Step 4: L6 哈希链审计

- 调用 `core/knowledge/validation/hash_chain.py`：
  ```python
  from core.knowledge.validation.hash_chain import HashChain
  chain = HashChain()
  chain.add_entry("question_spec", open("work/question_spec.json").read())
  chain.add_entry("type_classification", open("work/type_classification.json").read())
  chain.add_entry("method_candidates", open("work/method_candidates.json").read())
  chain.add_entry("model_draft", open("work/model_draft.md").read())
  chain.add_entry("assumption_validation", open("work/assumption_validation.json").read())
  chain.add_entry("MODEL_SPEC", open("output/MODEL_SPEC.md").read())
  assert chain.verify_chain() is True
  ```
- 导出 `work/audit_log.json`：含 `chain.to_dict()`（每条目的 index/artifact_name/data_hash/previous_hash/chain_hash/timestamp）与 `chain.get_audit_log()`。

### Step 5: 交付

- `output/MODEL_SPEC.md` 移交 Programmer 手。
- `work/audit_log.json` 留档供事后验证。

### Step 6: 运行可执行门禁

运行 `py core/tools/validate_project.py --project <项目路径>`，确认本 agent 对接的 [HARD] 检查全部 PASS。任一 HARD 失败按 ## Iteration 回退修正后重跑。WARN 项记录到 work/audit_log.json 但不阻塞。

## Self-Check

### HARD 项（必须 PASS，任一失败阻塞交付）

- [ ] [HARD] `output/MODEL_SPEC.md` 符合 `core/schemas/model_spec.schema.json` 全部 required 字段 → core/schemas/model_spec.schema.json
- [ ] [HARD] 5 个必要章节齐全（问题理解/模型假设/符号说明/模型选型/模型建立）→ core/schemas/model_spec.schema.json
- [ ] [HARD] `output/MODEL_SPEC.md` 无占位符（TODO/FIXME/TBD/XXX/待补/示例数据/模板数据）→ core/tools/validate_project.py: check_placeholders
- [ ] [HARD] `output/MODEL_SPEC.md` 无禁用词（统一扩充词表（见 core/Writer/knowledge 禁用词文件））→ core/tools/validate_project.py: check_forbidden_words
- [ ] [HARD] `output/MODEL_SPEC.md` 无内部路径/AI 痕迹（"作为AI"/"PaperCritic"/"Prompt"/"token"等）→ core/tools/validate_project.py: check_forbidden_words（含内部路径检测）
- [ ] [HARD] 词表扩充同步：禁用词表与 `core/Writer/knowledge/writing/forbidden-words.md` 保持一致，`Guardrails` 加载的禁用词表必须引用 `core/Writer/knowledge/writing/forbidden-words.md` 最新内容
- [ ] [HARD] 防数据泄露检查（铁律 M9）：赛题原始数据文件路径（如 `inputs/` 下的文件名）不得出现在 `MODEL_SPEC` 中
- [ ] [HARD] 防数据泄露检查（铁律 M9）：赛题敏感数值不得直接写入论文正文（应以模型参数化形式表述，如"δ=0.15"而非"原始数据中 15.2% 的..."）
- [ ] [HARD] `Guardrails.has_errors() == False`（无禁用词/占位符/内部路径/AI 痕迹）→ core/tools/validate_project.py: check_placeholders + check_forbidden_words
- [ ] [HARD] 候选模型 >=2（M1），每个假设 `composite_score >= threshold`（M2）→ core/schemas/model_spec.schema.json
- [ ] [HARD] 假设 `validation` 五项评分已回填（非空）→ core/schemas/model_spec.schema.json
- [ ] [HARD] `HashChain.verify_chain() == True`，链未断裂 → core/knowledge/validation/hash_chain.py
- [ ] [HARD] `work/audit_log.json` 含全部 6 个中间产物的哈希条目 → core/knowledge/validation/hash_chain.py

### WARN 项（记录但不阻塞）

- [ ] [WARN] 题型识别已写入 `work/type_classification.json`（影响下游物理校验分级）→ core/tools/validate_project.py: check_analysis_report_physics（间接）
- [ ] [WARN] 启发式算法未宣称全局最优（M6），子问题建模方案完整（M7）

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "modeler",
  "stage": 6,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "spec-auditor",
      "stage": 6,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/knowledge/validation/guardrails.py` —— L5 运行时护栏引擎
- `core/knowledge/validation/hash_chain.py` —— L6 SHA-256 哈希链
- `core/schemas/model_spec.schema.json` —— 最终输出结构契约
- `core/Modeler/templates/MODEL_SPEC_TEMPLATE.md` —— 渲染模板

## Iteration

当护栏报错或 schema 不符时：
1. 护栏 error（禁用词/占位符/AI 痕迹）→ 回退 model-builder 修正文本后重新 `validate_output()`。
2. schema 缺字段 → 补全对应字段（候选不足补 method-matcher 回退；评分缺失补 assumption-validator 回退）。
3. 哈希链校验失败 → 重新按顺序 `add_entry()` 重建链（通常因中间产物被外部改动）。
4. 全部通过后再交付 `output/MODEL_SPEC.md` 与 `work/audit_log.json`。
