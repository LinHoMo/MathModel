# Changelog

本文件记录 MathModel Harness 的版本级变更。状态单一真源为 `docs/STATUS.md`（机器实测数字 + commit hash）。

## v3.1.0-rc2（2026-09-07，Release Candidate 收尾）

### RC Smoke（真实负载验证，全部收口）

- **RC-S1 PASS**（真实 CUMCM 2024A 题面，16 波真实认知执行，`projects/rcs1-2024a`）：
  - RuntimeSession 16/16 节点完成、0 阻塞 0 失败；registry 16 artifacts、evidence graph 12 relations。
  - 五链验证全 PASS：State Truth（reconcile OK）/ Replay（run `22a4bf4ad576` 确定性口径全匹配）/ RunRecord（verify 全字段匹配）/ Provider boundary（全程本地）/ Artifact-Evidence chain（registry 内联单源 + graph 连贯）。
  - 记录：`research/RC-SMOKE/S1_SMOKE_RECORD.md`。
- **RC-S3 PASS**（provider boundary 审计，`research/RC-SMOKE/S3_PROVIDER_AUDIT.md`）：外部执行入口（`adapters/openai.yaml` + `core/runtime/adapters/` 桥接层）声明与实测一致；cloud_sandbox 默认关、本地回退行为符合文档。
- **RC-S2 BLOCKED**：等待真实科研建模问题输入；不人为造题。

### P14 Pilot（研究能力第一轮，全部 PASS）

- **P14.1**：执行契约冻结（`research/P14/RUNBOOK_P14_1.md` + schema + `p14_integrity_gate.py`，selftest 覆盖 9 类注入缺陷）。
- **P14.2**：6 ExperimentSpec / 21 实验一次通过 G0–G7。
- **P14.3**：21/21 本地沙箱执行、**21/21 replay match**、21 Evidence + 9 Claims（5 supported / 4 refuted）、全图 G0–G7 PASS。
- **P14.4**：正式判定 **PASS**——Harness 具备"冻结模型 → 可执行实验 → 可审计证据 → Claim 判定（含驳回与反向定位）"能力。报告：`research/P14/PILOT_REPORT.md`。
- **协议增补（v1.1）**：Claim 新增 `UNRESOLVED` 状态（RUNBOOK §5 规则 5 + schema + gate；"证据不足 ≠ 反证"）。

### P13-3D（研究结论正式关闭）

- **定性：Negative but informative**——显式 MODEL_PAPER_MAP 在真实 Writer、冻结模型内容下无结构传输/质量增益（H13/H14/H15/H17 FAIL），不增加未授权变异（H16 PASS，271→263），核心保持两单元越界（H18 FAIL）。
- 关键洞察：论文质量方差由构件质量（arm）主导 → Model Construction 是主要质量杠杆。
- R3.1 instrument hardening：corpus gate v1.1 新增配对唯一性检查（四类阻断，零回归）。
- 证据：`research/P13-3D-R3/real_evaluation/` + `R3_2_FINAL_REPORT.md`。

### Fixed（core/tools，bug-fix-only）

- **replay CLI KeyError 崩溃（RC-S1 A 类）**：`core/tools/runtime/replay.py` verify 失败路径裸取 `rep["reconcile"]` 导致崩溃，改为 `.get` 兜底。
- **replay CLI 项目名归一化（B 类）**：裸项目名现在按 `projects/` 解析（与 state.py 契约对齐）。
- **verify 分诊报错（B 类）**：路径不存在 / 无 RunRecord / 非 v3 三种情形分别给出可行动提示，取代误导性的"非 v3 项目"。
- **state.py status 双视图展示（B 类）**：新增 `v3 视图` 进度行（questions/claims/graph version），消除 V2 0/29 与 V3 完成态的展示割裂。
- **orchestrator 计数口径（C 类）**："处理波次 N（含重试/子波）· 节点完成 X/Y"，消除 20 波 vs 16 节点的口径混淆。

### Known Items（不阻塞，已分级记录）

- `validate.py` 56/57：唯一失败为 [L6] 论文结构——RC-S1 smoke 实例按设计止步于"论文投影就绪"（Writer 渲染未执行），.tex 缺失为阶段预期（C 类）；harness 本体全部校验绿。
- RC-S1 B 类遗留：2024A 内容深度（2 假设/1 实验，真实题面需更重建模）归 skill/workflow 层迭代。
- 工作区存在未跟踪编辑器元数据 `.trae/`、`.zcode/`（未处理）。

### Baseline

- pytest：**781 passed / 11 skipped**（与 v3.1.0-rc1 基线一致）
- catalog_check：OK（v3 双视图三方一致）
- 五轴 non-regression：15 passed（P5 契约）

## v3.1.0-rc1（2026-09-07）

- P0–P6 硬化计划完成（Architecture Freeze → Contract Freeze → State Truth → Deterministic Replay + Run Provenance → Legacy Isolation → Regression Gate → Release Candidate）。
- 九条终验收全证据：781 passed / 11 skipped（0 failed）、validate 57/57、catalog_check OK、五轴 non-regression 15 passed、legacy 冒烟、replay verify、reconcile 通过。
- 详见 `docs/STATUS.md` 与 `docs/architecture/HARDENING_PROGRAM.md`。
