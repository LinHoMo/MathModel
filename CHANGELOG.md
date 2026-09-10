# Changelog

本文件记录 MathModel Harness 的版本级变更。状态单一真源为 `docs/STATUS.md`（机器实测数字 + commit hash）。

## 2026-09-10 — Agent Protocol v1.0 冻结（非版本条目）

### 变更
- **AGENTS.md 冻结为 v1.0**：完成七处修正（六要素任务卡 / 去硬编码数字 / §5 机器校验约束 /
  §7 CI 门禁 / §7.1 文档更新纪律）。冻结后修改 AGENTS.md 须走 ADR（docs/decisions/）
  且不得破坏 validate.py 章节校验。
- **阶段五 V2 残留收口**：顶层 9 个 V2 schema 归档 `core/schemas/legacy/`；
  `core/knowledge/paper-cases` → `cases`（T-CONF-004）；删除 `sample_paper_project`
  （T-CONF-005）；P15 **保留主树**（T-CONF-001，撤销移出决策）；
  修复 CAPABILITY_ROADMAP 断裂引用 ×3（e2e_metrics/benchmark/catalog_check）。
- **版本收口**：`pyproject.toml` version 1.0.0 → 3.2.2（T-CONF-002）；新增 `docs/RELEASE.md`。

### 测试
- 四件套全绿：validate 45/0/0、catalog OK、terminology OK、pytest 595 passed。

## v3.2.2（2026-09-10，V2 论文链/历史债务彻底清除）

### 变更
- **删除论文链工具链（9 个）**：tex_to_docx / docx_post_processor / writing_check /
  citation_check / text_cleanup / distill_empirical / render_ai_usage /
  check_matlab_env / bench_mmbench；补删 validate_project.py（V2 论文校验器）。
- **删除 V2 资产**：core/templates/latex（27 LaTeX 模板）、core/env/profiles（9 竞赛
  论文规格 profile）、core/schemas 4 个 V2 json（paper_spec/code_deliverables/
  literature_evidence/citation）、core/skills/syslab（10 子技能 101 文件，未接入死资产）、
  8 个旧项目实例（rcs1-2024a/v3-real-2024a/g7/g8 test）、docs/architecture 25 份历史报告、
  docs/architecture/diagrams（6 个 V2 图）、docs/integration/harness-compat.md（V2 兼容约定）。
- **env 全面 V3 化**：schema.yaml 删 official/deliverables 块（六组：code/modeling/review/
  runtime/checkpoint/cloud_sandbox）、loader.py 默认 profile 置空且 paper 一致性检查全删、
  config.yaml 重写为纯 overrides、env_doctor.py 去 paper 校验。
- **new_project.py 重写**：纯 V3 布局（inputs/state/state/runs/artifacts/{data,code,results}/model），
  产出 MODEL_IR JSON + 模型描述 MD；删除 time_budget/handoff 等 V2 模板。
- **引用对齐**：benchmark.py 去 bench_mmbench 调用与 help；catalog_check 去 REPOSITORY_AUDIT；
  doctor.py 去 render_ai_usage；gen_runtime_manifest 去 empirical；domain legacy 注记更新；
  validate.py env 字段清单/禁用词注释更新；knowledge/workflows 文档引用去 latex/profiles。

### 测试
- pytest **595 passed / 0 skipped / 0 failed**（删除 test_validate_project/test_tex_to_docx_quick 等，
  重写 test_env/test_doctor 对齐 V3）；validate.py **45/0/0**；catalog_check --check / --check-terminology OK。

### 定位
- 彻底删除而非废弃标记：V2 论文链、旧研究、LaTeX 链、四手残留全部移除；
  全仓仅保留 V3 定位（问题输入 → MODEL_IR JSON + 模型描述 MD/Mermaid）。

## v3.2.1（2026-09-10，移除流程级人工审批）

### 变更
- **删除 human_approval 机制**：engine.py 删除 WAITING 常量、waiting 集合、
  needs_approval/approve 函数与审批分支；dag.py 删除 human_approval 字段；
  wave_executor.py 删除审批分组与审批节点 step（并行层直接执行 ready）；
  state/model.py 删除 workflow_waiting/workflow_approve/waiting_approval；
  两个 schema（dag/status）同步删字段；session.py/contracts.py 清理 waiting 引用。
- **定位**：审核发生在**产物交付后**（MODEL_IR + 模型描述文档给人评审），
  DAG 内不设流程级人工审批节点（V3 全自动 harness）。
- **测试**：删除 3 个审批测试（engine gate / integration / state），
  保留 blocked/retry/反馈环语义测试。

### 验证
- `validate.py`：**45 通过 / 0 失败 / 0 警告**
- `catalog_check --check`：**OK**
- `pytest`：**610 passed / 0 skipped / 0 failed**

## v3.2.0（2026-09-10，V2 彻底清除 + V3 新定位固化）

### V2 彻底删除（不向后兼容）

- **历史文档删除**：14 个过渡期过程文档（V3_ARCHITECTURE_PLAN / V3_BASELINE_AUDIT /
  V3_FINAL_AUDIT / V3_MIGRATION_MAP / V3_IMPLEMENTATION_REPORT / IMPROVEMENT_PLAN /
  RELEASE_CANDIDATE / COMPETITION_INTELLIGENCE_AUDIT / CROSS_QUESTION_SYNTHESIS_CONTRACT /
  COMPATIBILITY_POLICY / HARDENING_PROGRAM / CAPABILITY_ROADMAP_P13_P17 /
  RESEARCH_QUALITY_AUDIT / refactor-plan-v2）删除。
- **旧研究目录删除**：P13-3D / P13-3D-R2 / P13-3D-R3 / P14 / RC-SMOKE / audit /
  bench-m4-2000c 系列 / bench-p132-2023c（研究历史数据，仅保留 P15 现行实验）。
- **LaTeX 链彻底移除**：`env/schema.yaml` 删除 paper 规格块（20 字段）、
  compile_pdf / latex_engine / deliver_docx、LaTeX template 块、paper_name；
  profiles 同步清理；`doctor.py` 删除 check_latex / check_competition_pack /
  ENGINE_BY_COMPETITION；`test_doctor.py` 删除 V2 引擎映射与竞赛包测试。
- **ARCHITECTURE.md 重写**：V2 四手架构描述 → V3 现行架构（4 角色 / MODEL_IR+MD 产出 /
  Artifact Registry + Evidence Graph + DAG）。
- **README/AGENTS/STATUS/TEAM_GUIDE/STATE_TRUTH/RUN_PROVENANCE/harness-compat/V3.1**：
  统一更新为新定位（45 项校验、4 角色、无 LaTeX/论文、无 V2 兼容层）。

### 验证

- `validate.py`：**45 通过 / 0 失败 / 0 警告**
- `catalog_check --check` / `--check-terminology`：**OK**
- `doctor.py`：**就绪 17 / 警告 0 / 阻塞 0**
- `pytest`：**613 passed / 0 skipped**（human_approval integration 测试消除条件 skip，改为真实注入审批节点验证）



## v3.1.1（2026-09-08，仓库清理 + P15 研究基础设施 + core/tools 统一）

### core/tools 统一（4 commits，`7f29443`…`9199f03`，non-regression 774/11）

- **core/tools/ 子目录内联**：7 个子目录（runtime/validation/knowledge/devtools/rendering/evaluation/friendly）的 37 个实现文件内联到 `core/tools/*.py`，删除全部子目录。loose 文件从 shim 变为自包含实现。
- **core/evaluation/ 空壳删除**：3 个 `__init__.py`（零导入，功能由 `core/tools/` 承担）。
- **adapters 迁移**：`adapters/openai.yaml` → `core/runtime/adapters/openai.yaml`；修复 `gen_runtime_manifest.py` 输出路径 + `instructions_file` 路径（`AGENTS.md` → `AGENTS.md`）。
- **AI 工具配置 V2→V3**：`.clinerules` / `.cursorrules` / `.windsurfrules` 更新为 V3 表述；`GEMINI.md` 合并为 `@CLAUDE.md` 指针。
- **文档更新**：`TEAM_GUIDE.md`（V2 四手→V3 五角色）、`harness-compat.md`（V2 契约→V3 Artifact Registry）。
- **测试修正**：`test_validate_project.py` 路径更新；`test_tex_to_docx_quick.py` 转为 pytest 格式并迁入 `tests/unit/`；删除 `test_evaluation_bridge.py`（core/evaluation/ 已删）。
- **空目录清理**：`tests/tests/`、`research/P13-3D/inputs/`、`research/P13-3D-R3/.workbuddy/`、`adapters/`。
- **research/README.md**：新增目录指南。

### 仓库清理（3 commits，`691bdd0`…`b6540e3`，non-regression 781/11 不变）

- **技能迁移**：10 个 syslab 技能包从 `.claude/skills/` → `core/skills/syslab/`（101 files，git mv 历史保留）。
- **归档清理**：`archives/cumcm2024anew/` → `tests/fixtures/sample_incomplete_project/`（7 files，git mv）；删除 `archives/README.md`。
- **V2 残余移除**：`package.json` + `package-lock.json`（node 依赖，V2 遗留）。
- **架构文档迁移**：`.opencode/plans/V3_ARCHITECTURE_PLAN.md` → `docs/architecture/`。
- **P0 测量修复**：`e2e_metrics.py` 空壳过滤 + 方法族匹配 + 结构性检查；`validate.py` 路径引用更新；`cumcm2024A.txt` 输入污染修复。
- **工具清理**：删除 `fidelity_gate.py`、`run_p13_3d.py`、12 个 `_tmp_*.txt`、`mc_scorecard_v2.json`。
- **文档更新**：`STATUS.md`、`METRICS.md`、3 个架构审计文档、5 个测试文件路径修正。

### P15.0 CUMCM Benchmark Freeze（`8751c45`，tag `p15.0-benchmark-freeze`）

- 36 题 × 7 gold fields（problem_source/problem_type/capability_dimensions/model_methods/assumptions/code_language/result_fields）。
- Schemas：`competition_problem.schema.json`（30B schema，含 problem_type=5 enum + 16 capability_dimensions）。
- Catalog：`by_family.json`（8 families）、`by_capability.json`（16 dims）、`by_failure_mode.json`（12 patterns）。
- Validation scripts：`validate_schema.py`（PASS）、`benchmark_completeness.py`（36/36）、`coverage_report.py`、`duplicate_gate.py`。
- Baseline snapshot：5 问题卡（2024_A / 2022_C / 2020_B / 2018_A / 2019_C）+ `content_hashes.json`。
- Pre-registration：`PRE_REGISTRATION.md`（v1 freeze）。

### P15.1 B0 Alignment Baseline（`af1bbd5`，tag `p15.1-b0-baseline`）

- **2024_A B0 首轮**：V3 pipeline 16/16 节点完成；decomposition_coverage = UNRESOLVED（Q001 payload 为空）；method_selection = 0%（TOPSIS chosen for kinematics）；methodology_completeness = 0%；structural_compliance = 15.6%。
- **2024_A B0-R2 改进轮**：Mock execution with real problem text（`p151-2024a-r2/`）。
- **P15 研究基础设施**：measurement_recovery（execution_gate + register_external_artifact + schemas）、Model IR spec（MODEL_IR_SPEC.md + schema + example）、capability ontology（CAPABILITY_MAP + FAILURE_TAXONOMY + MODEL_CONSTRUCTION_RUBRIC）。
- **仓库审计**：10 份审计报告（`research/REPOSITORY_AUDIT/`）。
- **会话交接**：`HANDOFF.md`。

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

- **replay CLI KeyError 崩溃（RC-S1 A 类）**：`core/tools/replay.py` verify 失败路径裸取 `rep["reconcile"]` 导致崩溃，改为 `.get` 兜底。
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
