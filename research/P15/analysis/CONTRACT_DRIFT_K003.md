# CONTRACT DRIFT — K003 实验 register 契约 vs runtime registry 契约

> 日期：2026-09-10 ｜ 诊断者：MainAgent（audit 遗留治理项）
> 状态：已诊断 + 机制层治理完成（历史数据不动，如实披露）

## 1. 事实（机器实测）

- **runtime MODEL_IR schema**：`research/P15/model_representation/model_ir.schema.json`
  （v1.0 契约重建版，K002 起为模板对齐契约）：
  - 顶层 required 18 字段（含 model_graph；K002 register 侧为 18 含 modeling_trace——两版并存见 §4）
  - `model_family` required=[primary, description]
  - `problem_binding` required=[problem_id, sub_question_id, problem_sha256]
    （problem_sha256 pattern `^[0-9a-f]{64}$`）
  - `validations[].method` 必填
- **K003 正式 run**（`research/P15/experiments/P15-K003/runs/`，66 run）：
  - 44 份有 model_ir.json（S/SV 臂；F 臂 22 份用 model_doc.md，无 model_ir 属设计）
  - **仅 8/44 通过 runtime schema 全量约束**；36/44 缺至少一类字段：
    | 缺失 | 份数 |
    |---|---|
    | `model_family.description` | 36 |
    | `problem_binding.sub_question_id`（部分用 `sub_questions` 数组） | 36 |
    | `problem_binding.problem_sha256`（`"pending"` 占位） | 36 |
    | `dependencies` 为空 | 36 |
    | `validations[].method` 为 None | 36 |

## 2. 根因（代码级）

- `research/P15/experiments/P15-K003/k003_formal_runner.py` **无任何 schema 校验**
  （零 jsonschema 引用），model_ir 直接 `write_json` 落盘——register 无契约 gate。
- 生成侧两种模板形态并存：2022_C 型（description/sub_question_id/dependencies/
  validations.method 齐全，仅 problem_sha256=pending）与 2018_A 型（旧模板：
  无 description、用 `sub_questions` 数组、dependencies 空、validations.method=None）。
  两套模板来自不同 Model Constructor 会话，runner 未归一。

## 3. 影响评估

- **盲评/评分不受影响**：K003 rubric（L1-L4）评分对象是盲评包中的
  model_ir/model_doc + run_model.py + execution_result + fidelity_report；
  runtime schema 合规性不是 rubric 维度。缺字段不改变评分依据。
- **DAG 注入路径会 ContractError**（audit 期间已实测）：K003 run 若注入
  runtime DAG 会因 model_ir 不合规抛错——**arena 已走轻量 run_code_pipeline
  绕过 DAG 注入**，无运行影响。
- **problem_sha256=pending 是数据质量局限**：run 的 problem_binding 未回填
  冻结题面 hash；配对分析用 condition_map（problem_id）绑定，不受影响，
  但 run 级 provenance 不完整——如实披露为 K003 测量局限。

## 4. 治理动作（机制层统一，历史数据不动）

1. **诊断记录**（本文档）：36/44 不合规事实、根因、影响。
2. **register schema gate**：`k003_formal_runner.py` 增加 jsonschema 校验
   （Draft 202012，runtime schema），未来生成不合规 MODEL_IR 即 FAIL——
   杜绝再次产生两套契约。已生成 66 runs **不回溯修改**（实验数据诚信：
   FROZEN 后产物与生成时刻一致）。
3. **契约条款**：`P15-EXPERIMENT-CONTRACT-v2.md` 追加 register 硬性条款
   （实验 run 的 MODEL_IR 必须过 runtime schema；problem_sha256 必须回填
   真实冻结题面 hash，禁止 `"pending"` 占位）。
4. **K003 报告披露**：P15-K003-REPORT.md 局限节引用本文档。

## 5. 遗留观察

- runtime schema 顶层 required 18 项含 model_graph，K002 register
  （k002_register.py REQUIRED_TOP）含 modeling_trace——两版顶层字段清单
  在历史演进中未完全对齐（K002 契约重建时已核对模板承诺 18 字段；
  schema 的 model_graph 与 register 的 modeling_trace 并存差异待下次
  契约版本收敛时统一）。已记录，不阻塞。
