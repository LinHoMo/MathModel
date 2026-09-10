# P15 实验体系统一契约 v2（P15-EXPERIMENT-CONTRACT）

> 状态：ACTIVE（v1.2 治理升级，2026-09-09）
> 适用范围：P15 全部预注册实验（K001 已冻结的历史数据除外）
> 原则：**新数据一律 v2 标准；历史数据只读保留、不回写不迁移；节点间通信只通过文件契约。**

---

## 0. 契约总则

1. **每个节点只有一个标准**：同一类产物（manifest / deterministic / scores / condition_map）全实验共用一套字段与语义；不存在"两套并存 + 注释兼容"。
2. **字符串只是序列化，不是本体**：建模结构以 `catalog/model_families.yaml` 的 canonical id 为唯一身份；别名（aliases）在词表内解析，不进入运行数据。
3. **历史数据只读**：K001 / B0 / B0-R2 的产物是冻结快照，禁止改写；读取历史数据时按历史格式读取（如 `method_selection` 输出键），新写入一律新键（如 `structure_alignment`）。
4. **扩展走契约**：新题 / 新卡 / 新实验必须走「manifest + 哈希 + 词表校验 + 冻结」四步；不得在数据中引入词表外的新字符串命名。

---

## 1. 输入层标准（problem_cards）

| 文件 | 标准 |
|---|---|
| `problem_statement.txt` | 真实题面全文（sha256 冻结，8 题 verified） |
| `card.yaml` | 题目元信息（canonical 词表，无旧术语） |
| `gt.json` | `allowed_modeling_structures`（**唯一字段名**，v1.2 已全量迁移，无 `allowed_model_families`） |
| `manifests/input_manifest.json` | 8 题 {problem_id, text_sha256, local_path} 全 verified |

**GT 词表规则**：`gt.json.allowed_modeling_structures` 的值必须可解析到 `catalog/model_families.yaml` 的 canonical id 或 aliases（G3 Gate 强制）。

## 2. 词表层标准（catalog/model_families.yaml）

- 18 canonical families（frozen 待 K002 FROZEN 后置 true）。
- 结构：`id / canonical_name / aliases / concepts / mechanisms / methods / solvers / provenance / status`。
- **机制层允许共享**（如 `state_transition` 是 DP + MDP 共享机制原语），**命名层唯一**；族命中只在命名层判定。
- 运行数据（model_ir / deterministic / bundle）中出现的结构名必须是 canonical id 或词表别名。

## 3. Bundle 层标准（bundles/<sid>.md）

- 每 run 唯一输入：题面 + 参考资料段。
- **臂差异只允许出现在 `<!-- BEGIN REFERENCE` 区**；非参考资料段全实验逐字节一致（F/S 模板长度差 <10%，SV 的差值即为验证计划处理量）。
- 冻结后 bundle 内容不可变（哈希纳入 freeze）。

## 4. Run 层标准（runs/<sid>/）

### 4.1 manifest.json（v2）

```json
{
  "submission_id": "m-<题号>-<8位hex>",
  "problem_id": "2020_B",
  "arm": "F|S|SV",
  "rep": 1, "seed": 42, "batch": 0,
  "status": "PENDING|GENERATED|REGISTERED|COVERAGE_FAIL|FAIL",
  "statement_sha256": "<题面哈希>",
  "generator": {"model": "doubao-pro", "identity": "external_agent"},
  "cost": {"latency_s": 0, "input_tokens": 0, "output_tokens": 0},
  "coverage": {"expected": [], "covered": [], "missing": [], "complete": false}
}
```

### 4.2 model_ir.json（S / SV 臂，18 顶层字段）

`ir_version / model_id / model_family / problem_binding / assumptions / variables / parameters / objectives / constraints / mechanisms / equations / dependencies / solvers / experiments / validations / claims / model_graph / modeling_trace`

- `problem_binding.problem_sha256` 必须等于冻结题面哈希。
- SV 臂额外要求 `validations.validation_plan` 5 强制字段：`limit_tests`（非空 list）/ `multi_seed`（n_runs≥3）/ `sensitivity` / `ambiguity_handling` / `claim_evidence_map`（每条有 evidence_ref）。

### 4.3 model_doc.md（F 臂主体，盲评呈现用）

### 4.4 deterministic.json（v2 键）

`coverage / model_family_primary / undeclared_symbol_ratio / …`（全部为确定性可复算指标；无旧键 `method_family_identified` 等）。

## 5. Register 层标准（k002_register.py）

| Gate | 规则 | 退出码 |
|---|---|---|
| 哈希绑定 | `problem_binding.problem_sha256 == manifest.statement_sha256` | 1（作废） |
| 覆盖度 | `model_ir.problem_binding.sub_question_id` 覆盖全部子问题（缺任一 → COVERAGE_FAIL，不进主终点，单独报告） | 2 |
| 验证计划（SV） | 5 强制字段全部满足（缺 → 作废） | 1 |
| **MODEL_IR schema（2026-09-10 契约统一，CONTRACT_DRIFT_K003）** | 实验 run 的 model_ir 必须通过 `core/schemas/v3/model/model_ir.schema.json（P1-4 唯一真源）`（Draft 202012 jsonschema 全量校验）：model_family.description 必填、problem_binding 用 sub_question_id（禁止 sub_questions 旧形态）、problem_sha256 必填真实冻结题面 hash（**禁止 `"pending"` 占位**）、dependencies 非空、validations[].method 必填 | 1（拒绝登记） |
| 通过 | 全部满足 | 0（REGISTERED） |

> **CONTRACT_DRIFT 历史事实**：K003 正式 44 份 model_ir 仅 8 份合规（36 份缺
> description/sub_question_id/problem_sha256/dependencies/validations.method，
> 根因：k003_formal_runner 无 schema gate）。已治理：runner 注入
> `_assert_mir_schema` 门禁（拦未来生成），历史数据不回溯修改，局限披露见
> `research/P15/analysis/CONTRACT_DRIFT_K003.md` 与 K003 报告。

## 6. 盲评层标准

- 盲评包：`blind/<sid>.md` = 去标识后 submission + 题面 + 评分表；`model_id` 中性化为 `m-<sha256前8位>`，**禁止任何臂/批次/分组标识**（leak 词表强制拦截）。
- 评分文件：`scores/<sid>.json` = 22 维 {dimension, score, evidence}；`evaluator.model` 记录评估模型；`evaluator ≠ generator`（预注册铁律）。
- 评分框架：`capability/MODEL_CONSTRUCTION_RUBRIC.md` v1.0（L1 9 / L2 15 / L3 9 / L4 9，满分 42；**L2.6 权重 3 满 3 分，禁止再乘权重**）。
- 分组明细只在 `key/condition_map.json`（ANALYSIS 阶段解封；任何报告/产物不得外泄分组）。

## 7. 冻结层标准（k002_freeze.py）

- 冻结目标：8 题（statement/card/gt）+ prompt 模板 F/S/SV + DRAFT + GATES + 词表 + schemas。
- 冻结产出：`hashes.json`（逐文件 sha256）+ `frozen_root_sha256`。
- 校验：`--check` 全文件哈希一致 → PASS；任何漂移 → FAIL（禁止修改冻结规格提分）。

## 8. 分析层标准（k002_analysis.py）

- 主终点：MCQ_primary（L2 composite，与 K001 同 rubric 可比）+ VAL_primary（L4，S+V 臂特有价值）。
- 效应：Δ_FS / Δ_SV / Δ_FSV 配对差分 + cluster bootstrap（95% CI）+ 符号置换。
- 结论形态：预注册 5 种（positive / negative / zero / mixed / insufficient-power），以效应量 + CI 为主，不做仅 p 值判断。
- 题目区分度预检：condition 间差为 0 → 删除该题单列；≥2 题无区分度 → STOP（K001 per-block 教训：2019_C 全臂恒定 87.18 零区分度）。

## 9. 兼容与迁移规则（v1.2 已执行）

| 项 | 动作 | 状态 |
|---|---|---|
| `gt.json` 旧字段 `allowed_model_families` | 迁移为 `allowed_modeling_structures` | ✅ 5 题已迁移 |
| `e2e_metrics.py` 输出键 | `method_selection` → `structure_alignment`（历史读取仍按旧键） | ✅ |
| `e2e_metrics.py` 字符串方法兜底 | 移除 `_method_hit`（结构唯一评分依据；紧凑匹配保留在 `_structure_hit`） | ✅ |
| `catalog_check.py` 术语门禁 | 移除 `# legacy compat` 行内豁免（零注释兼容） | ✅ |
| `k002_gen_bundles.py` 字段回退 | 移除 `or allowed_model_families` | ✅ |
| 历史文档 | 23 份规划/报告加 ARCHIVAL-NOTE；迁移类路径批量修正 | ✅ |

## 10. 扩展指引（后续插入新内容）

1. **新题**：加 statement/card/gt（canonical 词表）→ input_manifest 登记 → sha256 verified → G3 词表校验。
2. **新方法卡**：家族名必须来自词表（或先扩词表 aliases）；卡字段按 method_card.schema v3（含 structure_signals）。
3. **新实验**：复制 K002 工具链模板（k002_*），改实验参数与冻结清单；**不得复制 K001 的旧 manifest/deterministic 结构**。
4. **新指标**：先在 rubric/schema 层定义（dimension + scoring 规则），再进分析脚本；禁止在分析期临时发明指标。
5. **新节点**：必须定义输入/输出文件契约 + 退出码 + 哈希绑定，写进本契约后再实现。
