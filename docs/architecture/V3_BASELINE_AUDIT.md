# V3 Baseline Audit — V2 仓库基线审计

> 生成日期：2026-09-04
> 审计性质：**只读审计，本轮未修改任何生产代码**
> 审计方法：全量文档阅读 + 目录遍历 + 交叉引用搜索 + 测试套件实跑
> 用途：作为 V2 → V3.1 迁移的事实基线（Baseline of Record）

---

## 0. 一句话结论

V2 是一个**工程化程度很高但认知模型扁平**的系统：29 个 agent / 13 个 schema / 36 个工具 / 276 个知识文件在"状态外置 + 契约传递 + 脚本门禁"的骨架上严格串联，仓库卫生与门禁可信度在此前的"四波重构"后已大幅修复（测试 240 passed / 1 failed）；但其核心抽象仍是**29 步线性流水线**，State、Artifact、Evidence、Workflow 四个概念混在 `work/state.json` + 固定文件路径中，Paper 被当作终点 Artifact 而非投影，Knowledge 是文档库而非决策知识。这与 V3.1 的目标（Artifact Layer + Evidence Graph + Workflow DAG + 决策知识库）存在结构性差距，需要分层迁移而非推倒重写。

---

## 1. 仓库身份与 Git 基线

| 项 | 值 |
|---|---|
| 分支 | `main` @ `59641d0`（docs: 更新文档一致性 + 清理 node_modules） |
| 工作区 | 干净，仅 `.opencode/`（V3 Plan 草稿）未跟踪 |
| 版本 | 2.0.0（README 声明），技术栈 LaTeX 单主线 |
| 运行时 | Python 3.12（系统，含 pytest 9.1.1）；核心工具零第三方依赖 |

---

## 2. V2 架构实况

### 2.1 核心数据流

```
赛题文件 → Modeler(8) → MODEL_SPEC.md → Programmer(6) → CODE_DELIVERABLES.md + figures/all_results.json
        → Writer(7) → PAPER_SPEC.md + paper/main.pdf → Reviewer(8) → work/revision_plan.json
```

### 2.2 状态与门禁机制（V2 的骨架，V3 必须继承）

- **`core/tools/state.py`（762 行）**：单一事实源 `projects/<p>/work/state.json` + 人类可读镜像 `work/STATE.md` 双写。29 步以 `PIPELINE` 列表硬编码 `(hand, agent, stage)` 三元组；`current` 永远由 `completed[]` 推导（杜绝过期）；`advance` **已强制跑门禁**（fail-closed，rc=2/3 拒绝推进，含 `--no-gate` 逃生口）；`init` 可从产物反推进度（中断恢复）；另有 `q_states`（Per-Qi 雏形）与 `ai_usage_ledger`。
- **`core/tools/gate.py`（803 行）+ gatelib.py（703 行）**：每个 (hand, agent) 一组 lambda 断言，HARD/WARN 分级，退出码契约 0/1/2/3；后置检查复用 validate_project.py 的 42 项。
- **`catalog.yaml`（schema_version 4）**：29 agent 的单一真源（name/gate/artifact/path/stage/utg_layer），派生 `adapters/openai.yaml`（gen_runtime_manifest.py 生成，勿手编）。
- **UTG 六层**：L1 形式化规约 → L6 哈希审计，映射到 29 agent 无空缺。

### 2.3 已验证修复的 V2 历史断点（来自 REFACTOR_PLAN.md 体检，commit 395c0f7 已修）

| 历史断点 | 现状 |
|---|---|
| gate 与 advance 未耦合 | ✅ 已修复：advance 强制跑门禁，fail-closed |
| 国赛参数基线错误（25/30 页） | ✅ 已修复：对齐 17/20 页、13000 字，真源 `core/env/schema.yaml` + `profiles/*.yaml` |
| guardrails_report 契约覆盖冲突 | ✅ 已修复：拆为 `guardrails_report_programmer.json` / `_writer.json` |
| 追溯率口径分裂 | ✅ 已统一（README 口径说明） |
| 参数三处重复 | ✅ 收敛至 env 层（config.yaml + schema.yaml + 9 个 profiles） |

**结论：V2 的"执行链未接通"问题已基本解决，本轮 V3 迁移的起点是健康的。**

---

## 3. 资产盘点

### 3.1 Agents：29 个（catalog ↔ 目录 ↔ openai.yaml 三方严格一致，无缺失/重复）

| Hand | 数量 | Agents（stage 顺序） |
|---|---|---|
| Modeler | 8 | problem-parser(1) → literature-searcher(1.5) → type-classifier(2) → method-matcher(3) → model-builder(4) → dag-builder(4.5) → assumption-validator(5) → spec-auditor(6) |
| Programmer | 6 | template-selector → code-implementer → test-runner → result-verifier → guardrails-checker → hash-auditor |
| Writer | 7 | structure-planner → section-writer → figure-generator → reference-curator → consistency-checker → guardrails-checker → final-validator |
| Reviewer | 8 | scorer-academic / scorer-engineering / scorer-judge / scorer-reader / scorer-adversarial（并行评审团）→ weakness-hunter → revision-planner → revision-executor |

Agent SKILL.md 通用模板：frontmatter（name/hand/utg_layer/stage/inputs/outputs）+ 执行卡片 + Procedure + Self-Check（复选框断言，可被 gate.py 转译）+ Iteration（回退规则，最多 3 轮）。scorer 系为精简变体（~73 行）。

**V3 问题确认**：Reviewer 的 5 个 scorer 全部是"Rubric 表 + Output Schema + Self-Check"的 Skill+Validator 形态，被人为提升为 Agent——与 V3 诊断一致，应降级/合并为 critic 层。revision-planner / revision-executor 承担的回退逻辑在 V3 中由 DAG 引擎承担。

### 3.2 Schemas：13 个（core/schemas/）

`question_spec / model_spec / code_deliverables / checkpoint / literature_evidence / model_dag / decision_log / reproducibility / score_card / bench_rubric / bench_result / citation / paper_spec`

- **可复用为 V3 基础**：`decision_log.schema.json`（字段相当完整：decision_type/question/options/choice/rationale/confidence/alternatives_considered——只缺 reversible/invalidated_by/consequences）、`model_dag.schema.json`（DAG 雏形）。
- **缺口**：无 artifact contract、无 stable ID 体系、无 evidence graph、无 workflow DAG、无 lifecycle schema、无 method card / failure memory schema。
- **定位问题**：13 个 schema 全部是"agent 输出格式"，不是"研究对象契约"——这是 V2 "Paper 是终点"思维的直接体现。

### 3.3 Tools：36 个脚本（core/tools/）

按职责分布：

| 职责 | 脚本 | V3 去向建议 |
|---|---|---|
| 状态管理 | state.py | → runtime/state |
| 门禁 | gate.py, gatelib.py, validate.py, validate_project.py, writing_check.py, citation_check.py | → validators |
| 编排 | orchestrator.py | → runtime/execution（DAG 引擎消费） |
| 评分 | score_compute.py, aggregate_scores.py, score_artifact.py, weight_profiles.py | → evaluation/scoring |
| 脚手架 | new_project.py | → runtime（生成 V3 workspace） |
| 文档转换 | tex_to_docx.py, docx_post_processor.py | → tools（纯 utility） |
| 检索 | scholar_fetch.py | → tools |
| 图表 | diagram_gen.py | → tools |
| 数值治理 | freeze_numbers.py | → validators/evidence |
| 合规 | render_ai_usage.py, repro_checklist.py | → validators/competition |
| 环境检查 | doctor.py, env_doctor.py, check_matlab_env.py | → tools |
| 基准 | benchmark.py, bench_mmbench.py | → evaluation/benchmark |
| 度量 | metrics.py | → evaluation |
| 知识蒸馏 | distill_empirical.py, reflection_bank.py, retrospect.py | → knowledge 运营 |
| 沙箱 | cloud_sandbox.py | → runtime/adapters |
| 运行时生成 | gen_runtime_manifest.py, test_runtime_compat.py | → runtime/adapters |
| 修正 | text_cleanup.py | → validators/paper（配套） |
| 测试残留 | test_runtime_compat.py（在 tools 下，位置不当） | → tests |

### 3.4 Knowledge：276 文件（core/knowledge/，12 个子目录）

| 目录 | 文件数 | 性质 |
|---|---|---|
| methodology/ | 54 | 方法论文档（含 **METHOD-DECISION-TREE.json**——结构化决策知识雏形已存在！）+ INDEX.md |
| paper-cases/ | 117 | 获奖论文拆解 |
| validation/ | 42 | 验证模块（Python，含 guardrails.py / hash_chain.py / consistency_checker.py 等——**这是 V3 validators 层的现成种子**） |
| bench/ | 22 | MMBench 题库 |
| playbooks/ | 13 | 赛事打法 |
| _negative/ | 8 | 反模式与失败案例（Failure Memory 的原料） |
| cookbooks/ | 8 | 代码 cookbook（历史断链已修复） |
| problems/ | 5 | 赛题索引 |
| pitfalls/ | 3 | 反模式 |
| review/ | 2 | 评分细则 |
| data-sources/ | 1 | 数据源目录 |
| empirical/ | 1 | 经验统计 |

另：四手私有 knowledge（Modeler/domain 等、Programmer/code-templates 等）。

### 3.5 Templates：core/templates/{latex, figures}

latex 下 9 个竞赛包（cumcm/mcm/diangong/huashu/huawei/apmcm/mathorcup/renzhengbei/shuweibei），包内含 config.yaml（与 env/profiles 呼应）。

### 3.6 Tests：240 passed / 1 failed / 10 skipped（实跑基线，2026-09-04）

- unit 24 个（state/new_project/gate/aggregate/weight/validate_project/doctor/benchmark/…，含 `test_openai_manifest` 断言 total_agents==29、`test_evals_and_runtime` 断言 29 个 evals 文件）
- integration 2 个（test_references 路径引用真实性 / test_structure 顶层结构，**依赖 projects/testproj 存在**）
- e2e 1 个（test_pipeline）
- **唯一失败**：`test_delivery_gates.py::TestDeliveryGateAIDisclosure::test_ai_disclosure_in_body_passes`（既有失败，非本轮引入）
- README 中"228/16"为过时数字，需更新

### 3.7 Projects / Archives

- `projects/cumcm2024anew/`：11/29 完成态（current=programmer/result-verifier），work/ 干净，无 output/figures 产物
- `projects/testproj/`：脚手架测试残留（被 tests/integration/test_structure.py 引用）→ 应迁移为 tests/fixtures
- `archives/`：4 个文件，全部是**幽灵脚手架**（pc-diangong 零完成、pc-dtest_done），无真实历史产出 → 证实"archive 与 fixture 混杂、且实际没有历史资产"

### 3.8 外部技能与生成物

- `.claude/skills/`：10 个 syslab 系列 skill（MWORKS Syslab 外部能力包），与 core/ 无复制关系，由 catalog external_skills 声明 → 语义上是 host adapter 下的外部技能，V3 应明确其位置
- `adapters/openai.yaml`：catalog 的自动派生物（263 行）→ V3 的 agent manifest 雏形
- `archify-skill/`：**空目录**，无任何内容 → 删除或补充说明

---

## 4. 根目录与卫生问题清单

| 项 | 现状 | 处置建议 |
|---|---|---|
| `_v.txt` | 6.7KB GBK 乱码的 validate 输出重定向 | 删除（垃圾） |
| `texput.log` | 705B XeTeX 失败日志 | 删除（垃圾） |
| `problem_cumcm2024A.txt` | 2024A 赛题原文 | 迁移至 examples/ 或 projects/cumcm2024anew 已有副本则删除 |
| `REFACTOR_PLAN.md` | 37.7KB 历史体检文档（已完成的诊断） | 迁移 docs/decisions/ 或 archive/ |
| `references/harness_compat.md` | 跨 harness 行为约定 | 迁移 docs/integration/harness-compat.md |
| `archify-skill/` | 空目录 | 删除 |
| `__pycache__` ×51 / tests 下 .pyc | 字节码垃圾 | .gitignore + 清理 |
| `node_modules/` + package-lock.json | 前一轮清理后残留 | 确认用途后处置 |

---

## 5. V3 关键概念的 V2 现状对照

| V3.1 概念 | V2 现状 | 差距 |
|---|---|---|
| **Artifact** | 不存在该抽象；只有"agent 产物路径"（catalog artifact 字段，29 个固定路径） | 无 ID / 无版本 / 无生命周期 / 无 registry |
| **Stable ID** | 无。以文件路径为身份（`work/question_spec.json`） | 文件名即 ID，不可版本化、不可失效传播 |
| **State** | `work/state.json`：completed[]（29 步）+ q_states 雏形 + ai_usage_ledger | 线性步骤为核心；q_states 已有但未被消费为执行单元 |
| **Evidence Graph** | 无。`figures/all_results.json` 是平面键值文件，消费者：writing_check.py（数值一致性）、validate_project.py（#4/#23 检查）、validate.py（追溯率）+ 30+ 处文档契约引用 | 无 typed relations、无 invalidation、无 claim 抽象 |
| **Workflow** | 硬编码 PIPELINE 列表 + orchestrator.py 顺序执行（含每步 3 轮重试、4 大轮） | 无 DAG / 无条件边 / 无并行 / 无 Per-Qi 执行单元 |
| **Knowledge** | 276 文件文档库；METHOD-DECISION-TREE.json 是唯一结构化决策数据 | 无 Method Card / Failure Memory / Innovation Patterns schema 与检索 API |
| **Decision** | decision_log.schema.json 已存在（V2 已有 decision 子命令），字段完整度高 | 缺 reversible / invalidated_by / consequences / criteria；未参与未来决策 |
| **Critic 前置** | 无。所有评审在 paper/main.pdf 之后（Reviewer 手整体后置） | 需新增 model/experiment/narrative/judge critic 并前置 |
| **Paper 定位** | PAPER_SPEC.md + main.pdf 是流水线终点 Artifact | V3 需改为 Research State + Evidence Graph 的投影 |
| **Project Workspace** | new_project.py 脚手架：inputs/ work/ output/ code/ figures/ paper/ deliverables/ _scratch/ | output/ 语义模糊；无 state/ registry；work/ 无 per-Qi 分区；artifacts/ 缺失 |
| **Legacy 兼容** | — | 需要 runtime/legacy 层把 all_results.json / state.json 转换为 V3 Registry+Graph |

---

## 6. V3 迁移的可复用资产（重要：不是从零开始）

1. **状态机骨架**：state.py 的 fail-closed advance / 产物反推 init / current 推导——V3 runtime/state 直接继承此设计哲学
2. **门禁体系**：gate.py + gatelib.py 的断言库 → V3 validators 的执行内核
3. **validation/ 42 个 Python 模块** → validators/ 层的现成种子（guardrails / hash_chain / consistency_checker / cross_model_checker 等）
4. **decision_log.schema.json** → V3 Decision Log 的直接底稿
5. **METHOD-DECISION-TREE.json** → Method Cards 的结构化种子
6. **q_states**（state.py 中已存在）→ Per-Qi 状态的底稿
7. **catalog.yaml → openai.yaml 生成链** → agent manifest 机制保留
8. **env 层**（config.yaml + schema.yaml + 9 profiles）→ 保留，Workflow Composition 消费
9. **四手 laws（M1-M9/P1-P12/W1-W14）** → 拆分归入 skills/roles 的约束声明
10. **test_references.py**（403 处路径引用真实性检查）→ 最终审计工具的底稿

---

## 7. 风险与约束

| 风险 | 说明 | 缓解 |
|---|---|---|
| 29 被测试硬断言 | `test_openai_manifest`（==29）、`test_evals_and_runtime`（29 个 evals 文件）、`test_29_evals_files_exist` | 迁移时同步改写测试，记录 intentional change |
| 30+ 处文档引用 all_results.json | 铁律 W1/P2 的枢纽 | P0 起提供 legacy 适配器，文档逐阶段更新 |
| test_structure 依赖 projects/testproj | fixture 与项目实例耦合 | P5 迁移 tests/fixtures |
| orchestrator.py 是唯一一键入口 | V3 DAG 引擎需提供等价能力并保留命令接口 | runtime/execution 包装，orchestrator 转发 |
| scorer 相关 4 个测试 | aggregate_scores / weight_profiles / score_compute 测试 | 评分能力保留在 evaluation/，Agent 数减少不等于删功能 |

---

## 8. 审计结论

1. **V2 工程骨架健康**（门禁 fail-closed、测试 240/1、三方一致），适合在其上叠加 V3 抽象层，而非重写。
2. **核心差距是认知模型**：缺少 Artifact/ID/Lifecycle/Evidence/Typed Relation/DAG/Per-Qi 执行单元七个基础抽象，且 Paper 是终点而非投影。
3. **可复用资产充足**：validation 模块、decision_log schema、METHOD-DECISION-TREE、q_states、gate 断言库都是 V3 对应层的直接种子。
4. **迁移必须分阶段**：P0（Contract/Registry/Lifecycle，不动 agent）→ P1（State/Evidence/DAG）→ P2（Knowledge）→ P3（Modeling critics）→ P4（Narrative/Projection）→ P5（清理 legacy）。
5. **每阶段必须保持 29-step 兼容层可用**，直到 P5 才删除；测试改动全部记录为 intentional change。

下一步：`docs/architecture/V3.1_ARCHITECTURE.md`（概念层架构评审）。
