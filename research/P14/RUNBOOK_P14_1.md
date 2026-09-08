# P14.1 Runbook — 执行契约（Machine-Checkable Freeze）

- Status: **FROZEN v1 (2026-09-07)** · v1.1 增补见 §5 末
- 上游: `PRE_REGISTRATION.md`（v1 FROZEN）——本文件将 PREREG §5 的 5 条待冻结项**全部冻结**，冻结后按本契约执行，禁止事后调参。
- 配套: `schemas/p14_entities.schema.json`（规范镜像，draft-07）+ `scripts/p14_integrity_gate.py`（原生校验器 + 五项 integrity 门禁 + `--selftest`）。
- 环境: `py -3.12`，无 jsonschema（门禁内置等价结构校验，由 selftest 证明与 schema 镜像一致）。

## 1. 冻结输入（Frozen Artifacts）

选臂规则（已在 PREREG 冻结）：优先盲评 PQ（主证据），噪声内（ΔPQ < 1 分）以 coverage_fidelity tie-break。

| question | arm | artifact 文件 | sha256 | bytes |
|---|---|---|---|---|
| 2020_B | **MMA** | `research/P13-3D-R2/output/artifacts/2020_B_MMA.json` | `3da8d82ee6708d4339becefa3790f93c5f5cff0e168e88eb298a84f2a25571fa` | 2755 |
| 2024_B | **B1-F** | `research/P13-3D-R2/output/artifacts/2024_B_B1_F.json` | `a808a0f7edece952e69205c06c7647e40ba29fbe92e078a5e13234419c388e6d` | 3312 |
| 2022_C | **B1-F** | `research/P13-3D-R2/output/artifacts/2022_C_B1_F.json` | `c15924bee329867701c502d768b338b6c8782f22cbc1bb5ce37b66ccf5468012` | 3252 |

选臂依据（可审计）：2024_B 盲评 B1-F 82.65 ≫ MMA 66.7 / B0 64.25；2022_C B1-F 92.6 ≫ MMA 89.6 / B0 86.1；2020_B MMA 88.1 ≈ B1-F 87.75（Δ<1，tie-break）且 MMA coverage_fidelity 73.3% ≫ B1-F 44.8%。

## 2. 条件定义（C0 / C1）与治理边界

- **C0**：仅 MODEL_ARTIFACT 生成 ExperimentSpec。`verification_questions == []`。
- **C1**：MODEL_ARTIFACT + verification-question checklist scaffold。checklist 只回答"需要验证什么、检查什么"，以问题列表组织实验设计。

> **治理边界（FROZEN）**：C1 的 checklist 只能改变"验证什么、检查什么"的**组织方式**，不能替 MODEL_ARTIFACT 新增模型变量、参数、约束、机制或结论。P14 不得变成第二个 P13-3C。

机器守卫（门禁 G6，两条）：

1. **禁增词表**：checklist 不得出现 `新增/添加/增加 + 变量|参数|约束|机制|结论`、`修改假设|替换假设|引入新结论` 等模式（frozen regex 列表在门禁内）。
2. **锚定要求**：checklist 每一条必须锚定至少一个 artifact 元素——包含 artifact 的变量/参数符号、元素 id，或 assumptions/mechanisms/objective/constraints 文本中的任一 4-gram。无法锚定的条目 = 违规。

另设 G7（claim origin）：每条 Claim 的 `model_origin.anchor` 必须能在冻结 artifact 文本中找到（子串或元素 id），保证结论只能溯源自模型。

## 3. 目录布局与命名

```text
research/P14/
  PRE_REGISTRATION.md / RUNBOOK_P14_1.md / schemas/ / scripts/
  runs/<run_id>/                      # 一次 pilot 运行一个目录
    manifest.json                     # run 元数据 + frozen_artifacts + replays[]
    specs/      P14-SPEC001.json ...  # 每题 × 每条件一份（6 份）
    executions/ P14-EXE001.json ...
    results/    P14-RES001.json ...
    evidences/  P14-EVI001.json ...
    claims/     P14-CLM001.json ...
```

run_id：`P14-<date>-<seq>`（如 `P14-20260907-01`）。种子 42；多轮执行 runs≥1 时每次 seed = 42 + i。

## 4. 六实体契约

所有实体共用 envelope：`entity_type` / `entity_id` / `schema_version="p14.v1"` / `run_id` / `created_at` / `content_sha256` / `parent_ref{entity_type, entity_id, content_sha256}`。

**hash 约定（FROZEN）**：`content_sha256 = sha256( json.dumps(entity 去掉 content_sha256 字段, ensure_ascii=False, sort_keys=True, separators=(",", ":")) )`。门禁按同法重算。

| 实体 | entity_id 前缀 | 特有必填字段 |
|---|---|---|
| ExperimentSpec | `P14-SPEC` | `question_id`, `condition(C0\|C1)`, `model_artifact_ref{question_id, arm, path, model_artifact_hash}`, `verification_questions[str]`, `experiments[{experiment_id, title, purpose, type∈{sensitivity,robustness,ablation,extreme_value,fit,simulation}, procedure, metrics[], seed=42, runs≥1}]`, `generator` |
| Execution | `P14-EXE` | `spec_ref{entity_id, content_sha256}`, `experiment_id`(须存在于该 spec), `runner{backend="python-sandbox", python_version, entrypoint, code_sha256}`, `seed`, `runs`, `status∈{completed,failed,timeout,diverged}`, `log_path`, `env_fingerprint` |
| Result | `P14-RES` | `execution_ref{entity_id, content_sha256}`, `data(object)`, `status∈{valid,stale,invalid}` |
| Evidence | `P14-EVI` | `result_ref{entity_id, content_sha256}`, `interpretation`, `position∈{supports,refutes,characterizes}`, `target_claim_desc`, `status∈{valid,stale,invalid}` |
| Claim | `P14-CLM` | `text`, `model_origin{element_type∈{objective,constraint,mechanism,assumption,parameter,variable}, anchor}`, `supported_by[evidence entity_id]`, `refuted_by[evidence entity_id]`, `status∈{supported,refuted,untested,stale,invalid}` |

manifest.json 必含：`run_id`, `prereg_version="p14.v1"`, `frozen_artifacts`（与 §1 表完全一致）, `replays[{execution_id, replayed_at, result_sha256_original, result_sha256_replay, match}]`, `created_at`。

`frozen_artifacts` 的 JSON 形态（FROZEN）：`{"<qid>/<arm>": {"path": "<相对仓库根路径>", "sha256": "<64hex>"}}`。

id 风格对齐 Evidence Graph v3（类型化编号），后续可导出为 graph relations（`based_on / produces / supports`）。

## 5. 失效传播语义（FROZEN v1）

1. `Execution.status ∈ {failed, timeout, diverged}` ⇒ 其 Result.status 必须为 `invalid`。
2. manifest.replays 中该 Execution 存在 `match=false` ⇒ 其 Result.status 必须为 `stale` 或 `invalid`。
3. Result `invalid` ⇒ 引用它的 Evidence 必须 `invalid`；Result `stale` ⇒ Evidence 必须 `stale|invalid`。
4. Claim：`supported_by` 中任一 Evidence `invalid` ⇒ Claim 不得为 `supported`；全部支持证据 `stale|invalid`（或为空而自称 supported）⇒ Claim 必须 `stale|invalid`；`refuted_by` 中存在有效（链路 valid）Evidence ⇒ Claim 必须 `refuted`；`supported_by` 与 `refuted_by` 均空 ⇒ Claim 只能为 `untested`。
5. **[v1.1 增补，P14.4 收口修订 2026-09-07，仅对未来 run 生效]** Claim 新增 `unresolved`（UNRESOLVED）状态：存在有效关联 Evidence，但谓词既不满足支持条件也不构成反驳 ⇒ `unresolved`；`unresolved` 必须至少绑定 1 条 Evidence（门禁强制）；**禁止把 UNRESOLVED 误用作 REFUTED**——“证据不足”不是“反证”。本轮 run P14-20260907-01 的实体状态不受影响。

## 6. 五项 integrity 门禁 ↔ 机器检查映射

| Gate | 门禁检查 | 错误码 |
|---|---|---|
| Provenance | G1：spec.model_artifact_hash == 冻结表 && 文件实测 hash 一致；manifest.frozen_artifacts == 冻结表 | `G1_PROVENANCE` |
| Determinism | G2：每个 completed Execution 在 manifest.replays 有 ≥1 条 `match=true` | `G2_DETERMINISM` |
| Result binding | G3：Result→Execution 引用存在且 hash 一致；每 Execution ≤1 Result；Execution 实测 hash 与 spec_ref 一致 | `G3_RESULT_BINDING` |
| Evidence binding | G4：Evidence→Result 引用存在且 hash 一致；Claim.supported_by/refuted_by 的 evidence id 存在 | `G4_EVIDENCE_BINDING` |
| Invalidation | G5：§5 全部规则（含传递闭包） | `G5_INVALIDATION` |
| （附加） | G0 结构/schema 校验；G6 C1 containment；G7 claim origin | `G0_SCHEMA` `G6_C1_CONTAINMENT` `G7_CLAIM_ORIGIN` |

## 7. 执行流程与纪律

P14.2 生成 specs（6 份，C0×3 + C1×3）→ P14.3 沙箱执行（entrypoint + seed 42）→ P14.4 落 Result/Evidence/Claim → `p14_integrity_gate.py runs/<run_id>` 全绿 → 报告。任何 gate 红 → 修实体记录，不改门禁语义。

纪律：全程 research/ 轨道；发现 core 缺陷走 failure→experiment→intervention→non-regression；negative results 合格；禁止改门禁语义与冻结表；模拟/试跑数据不得进入正式 runs/（试跑放 `runs/_scratch/`，门禁跳过下划线前缀目录）。

## 8. 自检验收

```text
py -3.12 research/P14/scripts/p14_integrity_gate.py --selftest
```

要求：合成合法图 PASS；对七类注入缺陷（G1 hash 篡改、G2 缺 replay、G3 断链、G4 断链、G5 失效未传播、G6 禁增词/无锚定、G7 claim 无源）逐一 FAIL 且错误码正确。selftest 全绿 = 契约具备机器可判定性。
