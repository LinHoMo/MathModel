# P15-K002 生成侧共享规范（Generator Spec v1.0）

> 本文件是 6 个生成子代理的唯一操作规范。严格按此执行，不得自行发挥。
> 核心铁律：**反解盲**（产物中不出现臂标识）、**冻结项只读**、**不碰 core/**、**每 run 独立构造**。

---

## 一、每 run 工作流（严格按序）

```
1. 读 manifest:  research/P15/experiments/P15-K002/runs/<sid>/manifest.json
   → 获取 arm, problem_id, statement_sha256, seed, rep, batch
2. 读 bundle:    research/P15/experiments/P15-K002/bundles/<sid>.md
   → 获取题面全文 + 输出要求 + 受控词表（model_family.primary 必须从词表选）
3. 构造产物（按臂，见下文）
4. 写产物到 runs/<sid>/
5. 运行 k002_register.py 登记
6. 若登记 FAIL → 读错误信息 → 修正产物 → 重跑 register（最多 3 轮）
7. 记录结果（sid / arm / status / latency / 修复次数）
```

---

## 二、S 臂产物：model_ir.json

写入 `runs/<sid>/model_ir.json`。必须通过 `core/schemas/v3/model/model_ir.schema.json` jsonschema 校验。

### 18 个顶层字段（全部必填，不得留空/null/"见上文"）

| # | 字段 | 结构要求 |
|---|---|---|
| 1 | `ir_version` | 固定字符串 `"1.0"` |
| 2 | `model_id` | `"M-<sid 前 8 位>"`，如 `M-04fc6d82` |
| 3 | `model_family` | 对象：`{"primary": "<受控词表选一>", "secondary": [], "description": "<一句话>", "candidates": [{"family": "...", "rationale": "..."}, ...]}`。**candidates ≥ 2**，每个有选择/排除依据。primary 必须从 bundle 末尾的"建模结构词表"中选，不得自造。 |
| 4 | `problem_binding` | `{"problem_id": "<manifest.problem_id>", "sub_question_id": "<覆盖全部子问题的逗号分隔或列表>", "problem_sha256": "<manifest.statement_sha256 逐字符复制>"}`。**problem_sha256 必须与 manifest 完全一致**（register 会校验）。 |
| 5 | `assumptions` | 数组，每条：`{"assumption_id": "A1", "text": "...", "type": "projection|calibration|mechanism|simplification|mechanism_assumption", "rationale": "..."}`。≥3 条，覆盖建模所需。 |
| 6 | `variables` | 数组，每条：`{"variable_id": "V1", "name": "...", "symbol": "<LaTeX>", "definition": "...", "unit": "...", "type": "state|decision|observation|constant|derived|parameter", "sub_question_binding": "Q1" 或 ["Q1","Q2"]}`。题面涉及的全部关键量必须声明，方程中出现的符号必须能在此找到。 |
| 7 | `parameters` | 数组，每条：`{"parameter_id": "P1", "name": "...", "symbol": "...", "value": <数值或字符串>, "source": "题目|校准|文献|假设|推导"}`。题面给出的数值参数全部列出。 |
| 8 | `objectives` | 数组，每条：`{"objective_id": "O1", "type": "minimize|maximize|estimate|satisfy|simulate|find", "expression": "<数学表达式>", "variables_refs": ["V1",...], "sub_question_binding": "Q1"}`。**每个子问题至少一个 objective**。 |
| 9 | `constraints` | 数组，每条：`{"constraint_id": "C1", "type": "...", "expression": "...", "variables_refs": [...], "source": "题面|物理限制|模型假设", "sub_question_binding": "Q1"}`。影响可行性的约束不漏。 |
| 10 | `mechanisms` | 数组，每条：`{"mechanism_id": "M1", "description": "<为什么适用这种数学结构>", "related_equations": ["E1"], "sub_question_binding": "Q1"}`。 |
| 11 | `equations` | 数组，每条：`{"equation_id": "E1", "latex": "<LaTeX 公式>", "type": "微分|差分|代数|递推|逻辑", "variables_refs": [...], "derivation_trace": "...", "sub_question_binding": "Q1"}`。注明边界/初始/终止条件。 |
| 12 | `dependencies` | 数组，记录模型内部依赖关系（如 `{"from": "E1", "to": "O1", "type": "derives"}`）。 |
| 13 | `solvers` | 数组，每条：`{"solver_id": "S1", "method": "...", "implementation_ref": "pseudocode 或算法名", "sub_question_binding": "Q1"}`。 |
| 14 | `experiments` | 数组，每条：`{"experiment_id": "X1", "type": "...", "inputs": {...}, "expected_outputs": {...}, "sub_question_binding": "Q1"}`。 |
| 15 | `validations` | 数组，每条：`{"validation_id": "V1", "type": "baseline|sensitivity|limit|reproducibility|convergence|uncertainty", "method": "...", "targets_refs": ["O1"], "sub_question_binding": "Q1"}`。≥2 条不同 type。 |
| 16 | `claims` | 数组，每条：`{"claim_id": "C1", "text": "...", "type": "...", "evidence_refs": ["X1","V1"], "model_refs": ["M1"], "sub_question_binding": "Q1", "status": "hypothesis|supported|refuted"}`。**每个子问题至少一个 claim**，evidence_refs 必须引用已声明的 experiments/validations id。 |
| 17 | `model_graph` | 对象：`{"nodes": [{"id": "M1", "label": "..."}], "edges": [{"from": "M1", "to": "E1", "relation": "..."}]}`。 |
| 18 | `modeling_trace` | 字符串：简要溯源记录（读了什么、如何选择模型族、关键决策点）。 |

### 子问题覆盖（coverage gate）

register.py 会检查 `problem_binding.sub_question_id` + 所有 objectives/claims/validations/mechanisms 的 `sub_question_binding` 是否覆盖该题全部子问题。**每个子问题必须至少被一个 objective/claim/validation/mechanism 引用**。

各题子问题清单（从 gt.json 读取，register 也会校验）：
- 2020_B: Q1,Q2,Q3
- 2018_A: Q1,Q2,Q3
- 2019_C: Q1,Q2,Q3,Q4
- 2018_B: Q1,Q2,Q3,Q4
- 2017_B: Q1,Q2,Q3,Q4
- 2011_B: Q1,Q2,Q3,Q4,Q5
- 2022_C: Q1,Q2,Q3,Q4
- 2024_A: Q1,Q2,Q3,Q4,Q5

---

## 三、SV 臂产物：model_ir.json + validation_plan.json

### model_ir.json
与 S 臂完全相同（18 字段，同上）。**不要把 validation_plan 写进 model_ir.json**（schema 不包含此字段，会导致 jsonschema 失败）。

### validation_plan.json（独立文件，5 字段全部必填且非空）

写入 `runs/<sid>/validation_plan.json`：

```json
{
  "limit_tests": [
    {"test_id": "LT1", "description": "<边界/极限检验描述>", "parameter": "...", "limit": "...", "expected_behavior": "..."}
  ],
  "multi_seed": {
    "n_runs": 5,
    "seeds": [42, 123, 456, 789, 1024],
    "aggregation": "mean_std",
    "description": "多种子运行取均值标准差"
  },
  "sensitivity": [
    {"param_id": "P1", "range": "±20%", "method": "one_at_a_time", "target": "O1"}
  ],
  "ambiguity_handling": [
    {"source": "<题面歧义点>", "interpretations": ["<解释1>", "<解释2>"], "adopted": "<采纳的解释>", "justification": "<理由>"}
  ],
  "claim_evidence_map": [
    {"claim": "C1", "evidence_ref": "V1", "status": "supported"},
    {"claim": "C2", "evidence_ref": "X1", "status": "supported"}
  ]
}
```

**字段最小非空要求（register 机械校验）：**
- `limit_tests`: list 且 len ≥ 1
- `multi_seed`: dict 且 `n_runs` ≥ 3
- `sensitivity`: list 且 len ≥ 1
- `ambiguity_handling`: list 且 len ≥ 1
- `claim_evidence_map`: list 且 len ≥ 1，每条必须有 `evidence_ref` 非空

---

## 四、F 臂产物：model_doc.md

写入 `runs/<sid>/model_doc.md`。自由文本 Markdown，必须包含以下 9 个部分（每部分有实质内容，禁止模板化空话）：

1. **问题理解**：题面核心矛盾、关键实体、子问题分解
2. **假设**：每条假设含类型（projection/calibration/mechanism/simplification）+ 合理性说明 + 误差影响
3. **变量**：全部关键变量声明（名称/符号/定义/单位/类型/所属子问题）
4. **参数**：全部参数声明（名称/符号/取值/来源）
5. **目标**：每个子问题分别给出目标（类型/数学表达式/所属子问题）
6. **约束**：全部关键约束（表达式/方向/来源/所属子问题）
7. **机理**：为什么适用这种数学结构 + **候选模型对比**（≥2 个候选，各自优劣与选择依据）
8. **方程**：控制方程/递推关系（LaTeX/类型/变量引用/推导依据/边界条件）
9. **求解与验证**：求解策略（方法选择/复杂度）+ 可复现性（随机种子/多 seed）+ 验证方案（基线/灵敏度/极限/多 seed 稳定性）+ 结果合理性预期

**整体要求**：九部分全部围绕本题真实展开；方程/符号/变量自洽；子问题多的题按子问题组织内容，确保每个子问题被实质覆盖。

---

## 五、登记命令

### S 臂
```powershell
py -3.12 research/P15/scripts/k002_register.py --submission-id <sid> --latency <秒> --agent-identity doubao --model-version "doubao-1.5-pro" --provider doubao --model-ir research/P15/experiments/P15-K002/runs/<sid>/model_ir.json
```

### SV 臂
```powershell
py -3.12 research/P15/scripts/k002_register.py --submission-id <sid> --latency <秒> --agent-identity doubao --model-version "doubao-1.5-pro" --provider doubao --model-ir research/P15/experiments/P15-K002/runs/<sid>/model_ir.json --validation-plan research/P15/experiments/P15-K002/runs/<sid>/validation_plan.json
```

### F 臂
```powershell
py -3.12 research/P15/scripts/k002_register.py --submission-id <sid> --latency <秒> --agent-identity doubao --model-version "doubao-1.5-pro" --provider doubao
```

**latency**：填一个合理的正数（如 45-180 秒，根据构造复杂度估计）。必须 > 0。

**退出码**：0 = REGISTERED 成功；2 = COVERAGE_FAIL（需补子问题覆盖）；1 = 校验失败（需修产物）。

---

## 六、反解盲铁律（违反则盲评包泄漏自检 FAIL）

产物中**严禁**出现以下任何内容：
- 臂标识：F / S / SV / free / structured / representation / validation_plan 臂名
- 实验标识：P15-K002 / K002 / submission_id / batch / rep / seed
- 格式暗示："按 MODEL_IR 结构化输出" / "自由文本" / "本臂要求"
- 任何能让评分者推断出所属臂的文字

`model_id` 用 `M-<sid 前 8 位>`（这是允许的，因为 sid 本身是盲的）。

---

## 七、冻结项只读（严禁修改）

- `research/P15/protocol/frozen_specs_k002/`（prompt_templates / hashes.json / run_order.json）
- 题面 / gt.json / card.yaml / rubric / DRAFT / GATES
- `core/schemas/v3/model/model_ir.schema.json`
- `core/model_families.yaml` / catalog
- `research/P15/scripts/k002_*.py`（register/state/freeze/blind_pack/gen_bundles/common）
- `research/P15/experiments/P15-K002/key/`（盲评映射，严禁出现在产物中）

---

## 八、每 run 独立构造

- 同一题不同 rep/seed 必须独立构造，**禁止批量复制粘贴**
- 不同 rep 之间模型选择、假设、参数取值、方程形式应有合理差异
- 但所有产物必须满足同一套质量标准（18 字段全实质填充 / 子问题全覆盖 / 反解盲）

---

## 九、失败修复循环

register 失败时：
1. 读错误信息（缺字段 / schema 不通过 / sha256 不匹配 / coverage 缺失 / SV 五字段不满足）
2. 精准修正对应产物
3. 重跑 register
4. 最多 3 轮；3 轮仍失败则记录 sid 和错误信息，继续下一个 run（最后汇总报告）

---

## 十、完成回报

每个子代理完成后回报：
- 本批 submission_id 列表 + 各自 arm + status（REGISTERED / COVERAGE_FAIL / FAILED）
- 修复记录（哪些 run 修了几轮、修了什么）
- 总耗时估计
