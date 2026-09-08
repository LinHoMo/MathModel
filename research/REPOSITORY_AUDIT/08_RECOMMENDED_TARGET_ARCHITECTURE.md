# 08 — Recommended Target Architecture（推荐目标架构）

> 审计日期：2026-09-08 | 基线 commit：`af1bbd5`
> 基于：01–07 七份审计报告的综合证据
> 原则：不破坏 v3.1.0 已冻结核心架构，所有变更由真实 failure mode 驱动

---

## ⚠️ 战略定位更新（2026-09-08，优先级高于本文档其余内容）

### 核心对象收束：Model Construction + Model Representation

**MathModel 核心价值 = Model Construction（What）+ Model Representation（How）**，Harness（How do we know）降级为保证可信的底座。

- **Model Construction = What**：Agent 能不能把现实问题构造成正确、完整、自洽、可求解、可验证的数学模型？（真正价值层）
- **Model Representation = How**：一个数学模型如何被机器和人结构化表达？产物形态 Model IR / Model Graph / Model Card / Model Trace / Model Diff（核心标准化对象）
- **Harness = How do we know**：怎么证明模型确由 Agent 构造、测量未被伪造、如何复现与定位失败？（只是底座）

### 架构边界：Harness ≠ Agent，core 永久 LLM-free

- `core/runtime` 永远不应该 import openai/anthropic 或内嵌 LLM 执行器。"整个 core 零 LLM 调用"不是缺陷，是设计要求。
- 真正的认知工作由外部 Agent（Doubao/GPT/Claude/人）完成，通过 **External-Agent Execution Interface** 提交产物（executor_type 区分 + ExternalArtifactManifest 契约 + register_external_artifact.py 提交入口 + gate 判据更新）。
- `DefaultNodeExecutor` 是 dry-run/synthetic 演练器，不是 Agent，其产物不代表任何建模能力，永不进入能力结论。

### Model IR / Model Graph 规范（已交付，最高优先级）

`research/P15/model_representation/`：
- `MODEL_IR_SPEC.md`（66KB）— 完整设计规范（13 字段组 + Model Graph 14节点15边 + 15项 deterministic checks + Model Diff + Modeling Trace + 2024_A 完整实例）
- `model_ir.schema.json`（20KB）— JSON Schema draft 2020-12
- `example_2024_A.json`（27.5KB）— 板凳龙完整实例（5假设/12变量/10参数/2目标/6约束/2机制/5方程/16图节点）
- Schema 校验 PASS，10/11 deterministic checks PASS

### 三层结构（更新目标架构总览）

```
┌─────────────────────────────────────────────────────────┐
│           Modeling System（真正价值 = Model Construction） │
│  Problem→Variables→Assumptions→Mechanism→Objective→     │
│  Constraints→Equations→Solver→Validation→Claims         │
│  表达层：Model IR / Model Graph / Model Trace / Model Diff│
├─────────────────────────────────────────────────────────┤
│           Measurement Harness（底座 = How do we know）    │
│  Freeze Input / Execution / Artifact / Evidence /         │
│  Provenance / Replay / Evaluator / Adjudication          │
│  External-Agent Execution Interface（外部 Agent 提交入口）  │
├─────────────────────────────────────────────────────────┤
│           Competition Profile（CUMCM 受控实验场）           │
│  CUMCM Bench / Problem Cards / Competition Validation     │
├─────────────────────────────────────────────────────────┤
│           Research Profile（科研迁移，同一套 IR + Graph）    │
│  Research Problems / Domain-independent Capability Core   │
└─────────────────────────────────────────────────────────┘
```

CUMCM 只是第一阶段最适合做能力工程的受控实验场，不是最终目的。Competition Profile 与 Research Profile 共享 **Same Model IR + Same Model Graph + Same Evidence Model + Same Harness**。

---

## 1. 目标架构总览

```
                    MathModel Harness
                           │
          ┌────────────────┴────────────────┐
          │                                 │
 Competition Profile                  Research Profile
          │                                 │
      CUMCM Bench                    Research Problems
          │                                 │
          └──────────────┬──────────────────┘
                         │
                  Capability Core
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   Alignment       Construction      Consistency
        │                │                │
        ├──────────── Solving ────────────┤
        │                │                │
    Validation       Evidence        Communication
                         │
                    Verification
                         │
                  Reproducibility
```

**核心定位不变**：Harness ≠ 完整数模 Agent。Harness 是**能力测量与提升基础设施**，不是"自动做题机器"。

---

## 2. 三层 Profile 边界（硬化）

### 2.1 Runtime（core/）— 绝对稳定层

**职责（仅限）**：
- execution（DAG 运行时、orchestrator）
- state（status.json 单一真源、reconcile）
- workflow（DAG 定义、5 Role 调度）
- tools（CLI 入口、shim 转发）
- skills loading（critic skills、外部 skill 注册）
- verification（L1–L6 门禁、validators）
- provider boundary（adapter 隔离、manifest 生成）
- artifact/evidence mechanics（Registry、Evidence Graph、hash chain）

**本次审计发现的越界（需修正）**：
| 越界项 | 证据 | 修正动作 | Tier |
|---|---|---|---|
| `core/knowledge/bench/` 136 文件 benchmark 语料驻留 runtime | 03 审计 §2.2 | MOVE 到 `research/benchmarks/corpus/`，core/knowledge 保留检索接口 | Tier 1 |
| `core/tools/run_p13_3d.py` 破损 shim | 01 审计 DEBT-002，Test-Path=False | DELETE（目标文件不存在） | Tier 0 |
| `core/tools/fidelity_gate.py` 破损 shim | 03 审计 §中严重度 | DELETE 或修复目标 | Tier 0 |
| MMBench 外部路径硬编码 `../_mm_analysis/...` | 03 审计 §中严重度 | 移入 env/config.yaml，core 不硬编码外部路径 | Tier 1 |
| `adapters/openai.yaml` 含 V2 术语和错误路径 | 01 审计 DEBT-011 | REGENERATE（修复生成器模板） | Tier 1 |

**绝对不能动**（v3.1.0 冻结组件）：
- Artifact Registry（`core/runtime/artifacts/`）
- Evidence Graph（`core/runtime/graph/`）
- Research State（`core/runtime/state/` + `projects/*/state/status.json`）
- Workflow DAG（`core/workflows/` + `core/runtime/execution/`）
- 验证门禁 L1–L6（`core/validators/` + `core/tools/validation/`）
- Hash chain（`core/runtime/` 内 hash_chain）
- Provider boundary（`core/runtime/adapters/`）

### 2.2 Competition Profile（CUMCM 特定）

**当前位置**：分散在 `core/env/`（竞赛 profile）、`core/templates/`（LaTeX 模板）、`core/knowledge/`（方法卡）、`research/P15/`（benchmark）

**目标位置**：
- CUMCM problem handling → `core/env/profiles/cumcm.yaml`（已存在，保持）
- CUMCM benchmark → `research/P15/`（已存在，保持）
- CUMCM-specific validation → `core/validators/modules/` 中标记 `competition=cumcm`
- CUMCM templates → `core/templates/cumcm/`（已存在，保持）

**关键修正**：
- Benchmark 数据（`core/knowledge/bench/`）迁出 runtime，见 §2.1
- `examples/problems/cumcm2024A.txt` **内容错误**（防空导弹 ≠ 板凳龙），必须修复（Tier 0，见 §5）

### 2.3 Research Profile（研究实验）

**当前位置**：`research/`（P13-3D/R2/R3、P14、P15、RC-SMOKE、bench-m4*）

**目标结构**：
```
research/
├── P13-3D/          # 已关闭实验（保留，negative but informative）
├── P13-3D-R2/       # 已关闭复现（保留）
├── P13-3D-R3/       # 已关闭对照（保留，删除 _tmp_*.txt）
├── P14/              # 已通过 pilot（保留）
├── P15/              # 进行中 benchmark（保持）
├── RC-SMOKE/         # 冒烟记录（保留）
├── benchmarks/       # 新增：benchmark 语料统一存放
│   └── corpus/       # 从 core/knowledge/bench/ 迁入
├── archives/         # 新增：历史实验归档
│   └── bench-m4-2000c-variants/  # 6 个无引用变体目录迁入
└── REPOSITORY_AUDIT/ # 本次审计（保留）
```

**关键修正**：
- `research/P13-3D-R3/prompts/_tmp_*.txt`（12 文件，零引用）→ DELETE（Tier 0）
- `research/P13-3D/inputs/`（空目录）→ DELETE（Tier 0）
- `research/bench-m4-2000c-p131-b/c`、`bench-m4-2000c-p132-a/b/c`、`bench-p132-2023c`（6 目录，无外部引用）→ MOVE 到 `research/archives/`（Tier 1，保留 registry/evidence_graph 研究证据）
- `research/bench-m4-2000c/work/mc_scorecard_v2.json` → DELETE（v2 重复，Tier 0）

---

## 3. Capability Core（七项不可约简能力）

基于 04 审计的结论，Capability Core = 7 项：

| # | 能力 | 当前测量状态 | 目标 | 科研迁移 |
|---|---|---|---|---|
| 1 | **Problem Alignment** | 有 evaluator 但不可靠（05 审计：string matching） | 重设计为 deterministic + semantic | ✅ 完全通用 |
| 2 | **Model Construction** | 有 P13 证据但无独立 evaluator | 最高优先级：新建 11 层审计管线 | ✅ 完全通用 |
| 3 | **Formal Consistency** | P13-3B 证明可干预（math 55→95） | 拆 dimension/symbol/unit/equation checks | ✅ 完全通用 |
| 4 | **Solving** | 有 code execution 但无 solving strategy 测量 | 增加 solvability check | ✅ 完全通用 |
| 5 | **Validation** | 有 validators 但偏格式而非模型 | 增加 model validation evaluator | ✅ 完全通用 |
| 6 | **Evidence** | P14 建立完整链（21/21 replay match） | 保持，扩展到 benchmark evidence | ✅ 完全通用 |
| 7 | **Communication** | 有 paper generation 但 P13-3D 证明非瓶颈 | 保持现状，不优先投入 | ⚠️ 需从比赛口径泛化 |

**比赛特有能力（不入 Core）**：
- C2 Subproblem Decomposition（比赛题面特有子问题编号）
- C7 Model-family Selection（比赛常用方法库）
- C15 Model→Paper Transmission（20 页论文格式）
- 子问题 count-ratio 测量

**完全无测量的关键能力（需补）**：
- C2 Subproblem Decomposition — 但 2024_A B0 证明这是首要根因
- C8 Cross-question Model Interface
- Security（permission_guard / trust_domain / incremental_checker）

---

## 4. Benchmark 目标架构（三层 + Model Card）

### 4.1 三层评估

| 层 | 名称 | 输入 | 输出 | Evaluator | 通过标准 |
|---|---|---|---|---|---|
| L1 | Problem Understanding | 题面 + 附件 | sub_questions, variables, constraints, assumptions | deterministic: count/coverage; semantic: alignment | sub_questions ≥ gold 80%, key_variables 全覆盖 |
| L2 | Model Construction | L1 输出 + 题面 | model_spec (objective/constraints/mechanism/equations) | 8 deterministic + 5 semantic checks（见 05 审计 §7） | structural ≥ 80, math ≥ 70, alignment ≥ 60 |
| L3 | End-to-End | 题面 + 附件 | 完整论文 + 代码 + 结果 | L1+L2 + paper quality + result validation | 三层均通过 + 结果可复现 |

**当前状态**：无分层，直接 L3（题目→完整论文），导致无法定位失败。

### 4.2 Model Card（每个 benchmark problem 必备）

字段：problem_id, source, source_sha256, family, sub_questions, allowed_model_families, required_problem_elements, required_relationships, known_valid_model_patterns, known_invalid_model_patterns, validation_requirements, sensitivity_requirements, common_human_errors, common_llm_errors, evidence_sources。

2024_A 的 Model Card 示例见 05 审计 §5。

### 4.3 多解模型原则

- `core_methods` 字段改为 `allowed_model_families`（列表，非唯一答案）
- 增加 `acceptable_alternative` 字段
- evaluator 测 `does the model answer the problem?` 而非 `did the agent guess the reference solution?`

---

## 5. 测量仪器修复路线（最高优先级）

**基于 05 审计的 P0 发现，当前 B0 数据完全无效，必须先修尺子再量能力。**

### Phase 0: 紧急修复（Tier 0，立即执行）

| # | 修复项 | 证据 | 验证 |
|---|---|---|---|
| F0-1 | 修复 `examples/problems/cumcm2024A.txt` 内容（防空导弹→板凳龙） | 05 审计 §1：hash 匹配确认输入错误 | sha256 与 gold standard 一致 |
| F0-2 | 实现 artifact non-emptiness gate | 05 审计 §1：16 个空壳 artifact 全 PASS | 空 artifact 必须 FAIL |
| F0-3 | 删除破损 shim `run_p13_3d.py` | 01 DEBT-002：Test-Path=False | import 不报错 |
| F0-4 | 删除破损 shim `fidelity_gate.py`（或修复目标） | 03 审计：目标不存在 | 同上 |
| F0-5 | 删除 12 个 `_tmp_*.txt` | 01 DEBT-001：Grep 零引用 | 文件不存在 |
| F0-6 | 删除 `tests/tests/` 嵌套目录 | 01 DEBT-003：路径错误 | pytest 收集不受影响 |
| F0-7 | 删除空目录 `research/P13-3D/inputs/` | 01 DEBT-007：0 文件 | 目录不存在 |

### Phase 1: 结构整理（Tier 1，无行为变化）

| # | 修复项 | 验证 |
|---|---|---|
| F1-1 | MOVE `core/knowledge/bench/` → `research/benchmarks/corpus/`，保留检索接口 | knowledge.py recommend 仍可工作 |
| F1-2 | MOVE 6 个 bench-m4 变体目录 → `research/archives/` | regression test 仍引用 bench-m4-2000c（不移动） |
| F1-3 | REGENERATE `adapters/openai.yaml`（修复 V2 术语） | gen_runtime_manifest.py 输出正确 |
| F1-4 | MMBench 路径移入 `env/config.yaml` | core/ 无硬编码外部路径 |
| F1-5 | ARCHIVE `docs/IMPROVEMENT_PLAN.md` → `docs/architecture/` | 文档可访问 |
| F1-6 | UPDATE `docs/TEAM_GUIDE.md`（V2→V3） | 引用正确 |
| F1-7 | MERGE 四重复 .clinerules 等 → 统一指向 AGENTS.md | 无重复 |
| F1-8 | `git rm --cached package-lock.json` | .gitignore 生效 |

### Phase 2: Research-layer 修复（Tier 2，不碰 core）

| # | 修复项 | 验证 |
|---|---|---|
| F2-1 | 重设计 Model Construction evaluator（8 deterministic + 5 semantic） | 05 审计 §7 的 spec |
| F2-2 | 为 2024_A 写完整 Model Card | 05 审计 §5 的示例 |
| F2-3 | CUMCM-Bench-v2 schema 升级：core_methods→allowed_model_families | schema validate 通过 |
| F2-4 | 实现 L1 Problem Understanding evaluator | sub_question decomposition 可测量 |
| F2-5 | 3 个 adversarial test case（05 审计 §8） | evaluator 能正确判 FAIL |

### Phase 3: 能力训练（测量仪器修复后）

- P15.1-FIX：修复输入后重跑 2024_A B0
- P15.1-BASELINE：确保真实执行（latency > 0, model_provider ≠ null）
- P15.2a：L1+L2 Pilot，3–5 题
- P15.2b：L3 End-to-End，在 L1+L2 通过后

---

## 6. 测试体系目标

| 能力 | 当前 | 目标 | 动作 |
|---|---|---|---|
| Architecture | 充分 | 保持 | — |
| State | 充分 | 保持 | — |
| Workflow | 充分 | 保持 | — |
| Provider boundary | 充分 | 保持 | — |
| Replay | 充分 | 保持 | — |
| Determinism | 充分 | 保持 | — |
| Artifact integrity | 充分 | 保持 | — |
| Evidence integrity | 充分 | 保持 | — |
| Schema | 部分 | 充分 | 增加 benchmark schema 测试 |
| Security | **零** | 部分 | 新增 permission_guard / trust_domain 测试（Tier 2） |
| Failure recovery | 部分 | 充分 | 增加 crash recovery 测试 |
| Real problem execution | 部分 | 充分 | 增加 non-emptiness gate 测试 |
| Mathematical modeling capability | 部分 | 充分 | L1/L2 evaluator 测试（Tier 2） |

**清理**：~72 个纯 `os.path.exists` fixture-existence 测试应标记或合并，不删除但降低权重。

---

## 7. 科研迁移路径

| 能力 | 比赛特有部分 | 通用部分 | 迁移动作 |
|---|---|---|---|
| Problem Alignment | 子问题编号、A/B/C 题分类 | 问题→抽象→变量→约束 | 解耦 competition profile |
| Model Construction | 比赛常用方法库（TOPSIS 等） | 11 层认知管线 | 方法库可插拔 |
| Formal Consistency | 无 | dimension/symbol/unit/equation | 直接通用 |
| Solving | 比赛时间限制 | solvability / computational reliability | 解耦时间约束 |
| Validation | 比赛评阅标准 | model validation / sensitivity | 评阅标准可配置 |
| Evidence | 无 | hash chain / provenance / replay | 直接通用 |
| Communication | 20 页论文格式 | 结果→主张→证据映射 | 格式模板可插拔 |

**结论**：7 项 Core 能力中 5 项完全通用，2 项（Alignment, Communication）需解耦比赛特有部分。这证明 Harness 路线可从 CUMCM 迁移到科研数学建模。

---

## 8. 与竞争性项目的差异化定位

基于 06 审计对 10 个公开项目的比较：

| 维度 | 我们 | 典型竞品 | 差异化 |
|---|---|---|---|
| 定位 | Harness（测量基础设施） | 完整 Agent（自动做题） | 我们不追求自动做题 |
| 能力测量 | Evidence-based + deterministic | LLM self-score / marketing claim | 我们有真实 B0 观测 |
| 失败归因 | F0–F11 十一层 | 无（"Agent 不行"） | 我们能定位到具体层 |
| 可复现性 | hash chain + replay + 781 tests | 无 | 我们有 P14 21/21 replay match |
| 论文生成 | 有但非瓶颈（P13-3D 证明） | 核心卖点 | 我们优先 Model Construction |
| Benchmark | CUMCM-Bench-v2（需修复） | 无独立 benchmark | 我们有 benchmark 基础设施 |

**不复制**：多 Agent 堆砌、算法库膨胀、论文长度优化、自评分体系。
**吸收**：题面/附件→EDA 链路的完整性（RC-S1 已验证）、Run Ledger 概念（已在 state/ 中实现）。

---

## 9. 实施优先级总览

```
立即（Tier 0）          本周（Tier 1）           下周（Tier 2）
┌──────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│ 修复 2024A 题面 │    │ bench 语料迁出 core  │    │ Model Construction     │
│ non-emptiness  │    │ bench-m4 变体归档    │    │   evaluator 重设计     │
│ 删除破损 shim   │    │ adapters 重新生成     │    │ L1 Problem Understanding│
│ 删除 _tmp_*.txt│    │ MMBench 路径配置化    │    │   evaluator            │
│ 删除嵌套目录    │    │ 文档更新/归档         │    │ 2024A Model Card       │
│ 删除空目录      │    │ 重复配置合并          │    │ Benchmark schema 升级  │
└──────────────┘    └──────────────────┘    │ 3 个 adversarial test  │
                                             └──────────────────────┘
验证：pytest + catalog + validate + replay 全绿（781 passed / 11 skipped 不下降）
```

**Tier 3/4（Skill/workflow 改进、Core 架构变更）**：除非发现真实 core failure，否则本次审计不执行。

---

*报告生成时间：2026-09-08 | 综合自 01–07 审计报告 | 下一份：EXECUTIVE_SUMMARY.md*
