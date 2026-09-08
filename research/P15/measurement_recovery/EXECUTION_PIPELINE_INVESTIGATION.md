# Execution Pipeline Investigation — V3 零 LLM 根因与真实执行路径设计

> **版本**: 1.0
> **日期**: 2026-09-08
> **调查人**: Execution Pipeline Investigator
> **工作目录**: `C:\Users\Lin\Desktop\Programs\MathModel`
> **前置审计**: B0 审计（`EXECUTION_AUTHENTICITY_PROTOCOL.md`）已确认 DefaultNodeExecutor 零 LLM
> **目标**: 找到真实 LLM 执行路径（如存在），或设计 minimal patch 使 `orchestrator --execute` 触发真实 LLM 执行

---

## ⚠️ 架构纠偏（2026-09-08，优先级高于本文档结论）

**Harness ≠ Agent。本项目不做 Agent，只做 Harness。**

1. **"整个 core 零 LLM 调用"不是缺陷，是设计要求。** `core/runtime` 永远不应该 import openai/anthropic 或内嵌 LLM 执行器。真正的认知工作（读题/建模/求解/写结论）由外部 Agent（Doubao/GPT/Claude/人）在这个 harness 之下完成。

2. **本文档中"方案 A（LLMNodeExecutor 进 core）"已撤销。** 不在 core/runtime 里造一个会思考的执行器，不加 `--llm` 标志，不加 LLM provider/api_key 配置。

3. **真正的缺陷不是"core 不调 LLM"**，而是：`orchestrator --execute` 的确定性 `DefaultNodeExecutor`（模板/演练桩，产出空壳）被误当成一次真实 Agent 运行并进入了能力评分。要修的是"执行类型的区分与外部产物的准入"。

4. **正确方向：External-Agent Execution Interface**（见 `EXTERNAL_AGENT_EXECUTION_INTERFACE.md`）：
   - 区分 `dry_run`/`synthetic`（DefaultNodeExecutor，永远不进入能力结论）与 `external_agent`（外部 Agent 真实产物）
   - ExternalArtifactManifest 契约（agent_identity / input_sha256 绑定 / latency > 0 / payload 非空）
   - `register_external_artifact.py` 提交入口（外部 Agent 逐节点登记，不得直接手写 registry.json）
   - Execution Authenticity Gate 判据更新（synthetic 一律标注 SYNTHETIC，capability scoring 自动 INVALID）

5. **DefaultNodeExecutor 是 dry-run/synthetic 演练器，不是 Agent，其产物不代表任何建模能力。**

本文档的调查事实（三条路径零 LLM、唯一可插拔点从未被调用、测量仪器 7/7 PASS）仍然有效；但"推荐方案 A+D"的结论已被上述纠偏取代。

---

## 0. 执行摘要

| 维度 | 结论 |
|------|------|
| **V3 管线是否有 LLM 调用？** | **否。** 全代码库零 LLM API 客户端导入（`openai`/`anthropic`/`requests.post` 到 chat API 均为 0 匹配） |
| **V2 legacy 管线是否有 LLM 调用？** | **否。** `_execute_step` 只读 SKILL.md 文本、跑门禁、推进状态，从不将指令发送给 LLM |
| **RC-S1 是否真实触发 LLM？** | **否。** RunRecord `model_provider=null`, latency=0.07s, 16 nodes — 与 B0 完全相同的零 LLM 确定性执行 |
| **唯一 LLM 可插拔点** | `core/runtime/writing/paragraphs.py:403-425` 的 `ControlledRenderer`（`llm_fn` callable 注入），但从未被任何执行路径调用 |
| **adapters/openai.yaml 是什么** | 从 catalog.yaml 自动生成的 **OpenAI Agents SDK 兼容配置文件**（工具定义 + 29 agent pipeline 描述），不是 LLM 客户端，不发起任何 API 调用 |
| **env/config.yaml 是否有 LLM 配置** | **否。** 仅 `profile: cumcm-2025` + 空 overrides，无任何 provider/api_key/model 配置 |
| **推荐方案** | **方案 A + D 组合**：research-layer 先建 mock LLM executor（方案 D）验证测量仪器，同时设计 core minimal patch（方案 A）使 `DefaultNodeExecutor` 可配置地切换到 LLM 执行器 |

---

## 1. V3 执行路径全量调查

### 1.1 调用链还原

```
py -3.12 core/tools/orchestrator.py <项目> --execute
  └─ core/tools/orchestrator.py (22行 shim) → exec core/tools/runtime/orchestrator.py
       └─ main() → _run_v3(base, dry_run=False, competition=None)
            └─ _execute_v3(project_dir, questions)
                 └─ RuntimeSession(project_dir, questions, max_workers=1)
                      ├─ __init__:
                      │    ├─ ArtifactRegistry(state/registry.json)
                      │    ├─ EvidenceGraph(state/evidence_graph.json)
                      │    ├─ ProjectState(state/status.json)
                      │    ├─ DecisionLog(state/decision_log.json)
                      │    ├─ WorkflowComposer → compose_executable(questions) → DAG
                      │    └─ DefaultNodeExecutor(registry, graph, state, decisions, ...)  ← 零 LLM
                      └─ session.run():
                           ├─ WaveExecutor.run() → 16 节点依次执行 DefaultNodeExecutor
                           ├─ engine.save_progress()
                           ├─ checkpoint() → registry/graph/state/decision_log 落盘
                           └─ _emit_run_record() → state/runs/<run_id>.json
```

### 1.2 DefaultNodeExecutor 16 节点行为清单

| # | 节点 | handler 方法 | 实际行为 | LLM 调用? |
|---|------|-------------|---------|-----------|
| 1 | `problem_analysis` | `do_problem_analysis` | 登记 problem artifact + motivates 证据 | 否 |
| 2 | `literature_search` | `do_literature_search` | `KnowledgeRetriever.recommend(features, top_k=3)` — 本地知识库关键词匹配 | 否 |
| 3 | `model_selection` | `do_model_selection` | `MethodArena.select(qid, qf)` — 基于方法卡得分的确定性排序 | 否 |
| 4 | `model_construction` | `do_model_construction` | 从方法卡 `card.risks` 提取前 2 条作为假设，登记 assumption artifact | 否 |
| 5 | `model_critique` | `do_model_critique` | 纯检查：每问题有 model 且 ≥1 条假设 | 否 |
| 6 | `assumption_check` | `do_assumption_check` | 纯检查：每问题 ≥1 模型 | 否 |
| 7 | `experiment_design` | `do_experiment_design` | `ExperimentPlanner.plan()` — 从方法卡元数据生成结构化计划 | 否 |
| 8 | `experiment@Q001` | `do_experiment` | **登记空壳 E/R/F artifact**（payload=[], data 仅含 card_id/plan_ref），不执行任何代码 | 否 |
| 9 | `experiment_critique@Q001` | `do_experiment_critique` | 纯检查：result 存在且非终态 | 否 |
| 10 | `evidence_build` | `do_evidence_build` | 登记 claim artifact（data.statement="Q001 结论" 模板文本） | 否 |
| 11 | `evidence_gate` | `do_evidence_gate` | `evidence_gate_evaluate()` — 确定性 coverage 计算 | 否 |
| 12 | `quality_evaluation` | `do_quality_evaluation` | `ResearchQuality.evaluate()` — 七维确定性规则检查 | 否 |
| 13 | `research_direction` | `do_research_direction` | `ResearchDirector.build()` — 从 claims 闭包确定性构建 story arcs | 否 |
| 14 | `paper_projection` | `do_paper_projection` | `PaperProjection.project()` — 纯函数大纲投影 | 否 |
| 15 | `paper_sections@Q001` | `do_paper_sections` | 登记 paper_section artifact（payload=["问题重述与分析"] 等单字符串） | 否 |
| 16 | `paper_review` | `do_paper_review` | `JudgeCritic.evaluate()` — 确定性判审规则 | 否 |

**关键证据** (`handlers.py:13-15`):
```
本实现是**确定性认知管线**（零 LLM）：文献检索/方法竞技场/实验规划器/研究叙事/
论文投影/批判器全部复用 core/runtime 下的真实模块，产出可追溯到
Artifact Registry + Evidence Graph 的研究状态。LLM 节点后续按同一协议接入。
```

### 1.3 全代码库 LLM 调用点搜索

执行 `rg -i 'openai|anthropic|llm|chat\.completions|api_key|gpt|claude' core/**/*.py`，93 个匹配全部归类如下：

| 类别 | 数量 | 说明 |
|------|------|------|
| 注释/文档声明"零 LLM" | ~15 | handlers.py, contracts.py, context.py, quality/contract.py, e2e_metrics.py 等 |
| `model_provider`/`model_version` 字段 | ~10 | runs.py, session.py, replay.py — 仅为 RunRecord 元数据字段，默认 null |
| `ControlledRenderer` LLM 可插拔接口 | ~8 | paragraphs.py:403-425 — `llm_fn` callable 注入，**从未被调用** |
| `LLM_MAY_CHANGE`/`LLM_MAY_NOT_CHANGE` 常量 | ~5 | expression.py — 表达层权限边界定义，非调用 |
| `gen_runtime_manifest.py` / `openai.yaml` | ~10 | 生成 OpenAI Agents SDK 兼容配置，非 LLM 客户端 |
| `scholar_fetch.py` AMINER API | ~8 | 学术文献检索 API（`AMINER_API_KEY`），**不是 LLM** |
| `cloud_sandbox.py` E2B/Daytona | ~5 | 云代码执行沙箱 API key，**不是 LLM** |
| `guardrails.py` 占位符检测 | ~3 | 检测 LLM 输出中的占位符（如 CLAUDE.md），非调用 |
| `score_compute.py` AI 关键词检测 | ~2 | 检测论文中是否提到 "AI"/"ChatGPT"/"GPT"，非调用 |
| `render_ai_usage.py` | ~2 | AI 使用量渲染工具（CLI 参数 `--tool "Claude Opus"`），非调用 |

**结论：`core/` 目录下零 LLM API 客户端导入（`import openai` / `from openai` / `import anthropic` / `client.chat.completions` 均为 0 匹配）。**

### 1.4 LLM 应该在哪里发生？—— 设计意图分析

从代码结构和注释中可推断 V3 的 LLM 接入设计意图：

1. **Node Executor 协议** (`handlers.py:5-11`):
   ```
   executor(node_id, engine_ctx) -> NodeResult
   NodeResult.outputs 可选键:
       artifacts: list[dict]  产出 Artifact
       evidence:  list[dict]  证据关系
       metrics:   dict        节点指标（latency_ms 等）
   ```
   协议设计为可替换的 executor。`DefaultNodeExecutor` 是确定性实现，注释明确说"LLM 节点后续按同一协议接入"。

2. **ControlledRenderer** (`paragraphs.py:403-425`):
   - 设计为 `llm_fn(ExpressionInput) -> str` callable 注入
   - 有后验校验（数字/引用/claim ⊆ 允许集）
   - 但 `RuntimeSession` 和 `DefaultNodeExecutor` 从未实例化或调用它
   - 这是 **P11 论文渲染层**的 LLM 接入点，不是认知管线层的

3. **RunRecord 的 `run_meta`** (`session.py:56-58`):
   ```python
   # Hardening P3：外部 executor 溯源（model_provider/model_version/
   # token_cost/decision）；additive，None 时记录为 null
   self.run_meta = run_meta or {}
   ```
   设计为外部 executor 通过 `run_meta` 注入 LLM 元数据，但 `_execute_v3` 调用 `RuntimeSession` 时从未传入 `run_meta`。

4. **adapters/openai.yaml**:
   - 从 catalog.yaml 生成的 OpenAI Agents SDK 兼容配置
   - 定义了 29 个 agent 的工具调用（state_init/gate_check/validate_project 等）
   - 设计意图是：**在 OpenAI Agents SDK（或 Codex CLI）中加载此配置，由外部 LLM agent 驱动 29 步流水线**
   - 但 MathModel 仓库本身不包含 OpenAI Agents SDK 的运行时，`orchestrator --legacy` 也不调用它

**设计上 LLM 调用应该发生的位置：**
- **认知管线层**：`DefaultNodeExecutor` 的替代实现（如 `LLMNodeExecutor`），在 `problem_analysis`/`model_construction`/`experiment` 等节点调用 LLM 生成实际内容
- **论文渲染层**：`ControlledRenderer` 的 `llm_fn` 注入点，在 `paper_sections` 之后的段落渲染阶段调用 LLM
- **外部驱动层**：通过 `adapters/openai.yaml` 在 OpenAI Agents SDK/Codex CLI 中由外部 LLM agent 驱动 V2 29 步流水线

---

## 2. V2 Legacy 管线调查

### 2.1 `orchestrator --legacy` 执行路径

```
py -3.12 core/tools/orchestrator.py <项目> --legacy
  └─ _run_pipeline(project, max_rounds, dry_run)
       └─ 遍历 S.PIPELINE (29 步):
            └─ _retry_step(project, hand, agent, 3)
                 └─ _execute_step(project, hand, agent):
                      ├─ _parse_skill(skill_path) → 读取 SKILL.md 文本，提取 Procedure/Contract/Iteration
                      ├─ [Reviewer 特殊] _run_score_compute(project) → 确定性评分
                      ├─ _run_gate(project, hand, agent, "artifact") → 确定性门禁检查
                      └─ _advance_state(project, hand, agent, artifact) → 状态推进
```

### 2.2 关键发现：V2 同样零 LLM

`_execute_step` (`core/tools/runtime/orchestrator.py:137-235`) 的行为：

1. **读取 SKILL.md** (`_parse_skill`, L63-77): 仅解析 markdown 标题结构，提取 `## Procedure`/`## Contract`/`## Iteration` 等节文本，**存储在 `skill` dict 中但从未使用**
2. **跑门禁** (`_run_gate`, L80-92): 调用 `gate.py` 做确定性 artifact 检查
3. **推进状态** (`_advance_state`, L95-102): 调用 `state.py advance`
4. **Reviewer 特殊处理** (L159-187): 调用 `score_compute.py` 做确定性评分

**`skill` 变量在 `_execute_step` 中被解析后完全未被使用。** 29 个 agent 的 SKILL.md 是写给**人类或外部 LLM agent** 的指令文本，orchestrator 本身从不执行这些指令。

### 2.3 V2 状态确认

`projects/rcs1-2024a/work/state.json`:
```json
{
  "current": {"hand": "modeler", "agent": "problem-parser", "stage": 1},
  "completed": [],
  "q_states": {}
}
```
V2 状态 0/29，与 V3 的 16/16 节点完成完全独立，无同步机制。

---

## 3. RC-S1 真实执行调查

### 3.1 RunRecord 分析

`projects/rcs1-2024a/state/runs/22a4bf4ad576.json`:

| 字段 | 值 | 判定 |
|------|-----|------|
| `run_id` | `22a4bf4ad576` | 正常 |
| `status` | `completed` | 表面正常 |
| `model_provider` | `null` | **零 LLM** |
| `model_version` | `null` | **零 LLM** |
| `token_cost` | `null` | **零 LLM** |
| `latency.seconds` | `0.07` | **模板初始化速度**（真实 LLM 通常 >10s） |
| `skill_version` | `e3b0c44...b7852b855` | **空字符串 SHA256**（core/skills/ 无 .yaml） |
| `engine.completed_nodes` | 16 | 与 V3 DAG 节点数一致 |
| `engine.failures` | `[]` | 表面正常 |
| `decision` | `null` | 无决策记录 |

### 3.2 RC-SMOKE 报告的自我描述

`research/RC-SMOKE/S1_SMOKE_RECORD.md` 明确写道：
> 执行方式：`orchestrator.py rcs1-2024a --execute`（RuntimeSession，**全程本地，无外部 provider 调用**）

> Provider boundary: 全程本地；adapters/openai.yaml 未启用（未走外部 runtime），边界无违反

RC-S1 的"16 波真实认知执行"是指 **RuntimeSession 的 16 个 DAG 节点全部执行完成**，而非"16 次 LLM 调用"。报告本身诚实标注了"无外部 provider 调用"。

### 3.3 结论

**RC-S1 与 B0 是完全相同的零 LLM 确定性执行。** 区别仅在于：
- RC-S1 使用了真实的 CUMCM 2024A 题面文件（`inputs/problem_cumcm2024A.txt`）
- 但 `DefaultNodeExecutor` 的 `features` 仍是硬编码默认值 `{"problem_types": ["evaluation"], ...}`，**从未读取题面文本**
- `input_hash` 非空（因为 inputs/ 有文件），但执行逻辑不依赖输入内容

---

## 4. 四种方案可行性分析

### 方案 A：在 DefaultNodeExecutor 中增加 LLM 调用点

**描述**: 实现 `LLMNodeExecutor`（或扩展 `DefaultNodeExecutor`），在关键节点（problem_analysis, model_construction, experiment, evidence_build, paper_sections）调用 LLM 生成实际内容。

**需要的改动**:

| 改动 | 文件 | 行 | 说明 |
|------|------|-----|------|
| A1 | `core/env/config.yaml` | 新增 | 增加 `runtime.llm: {provider, model, api_key_env, base_url}` 配置 |
| A2 | `core/env/schema.yaml` | 新增 | 增加 LLM 配置的 schema 定义 |
| A3 | `core/runtime/execution/llm_executor.py` | 新增文件 | `LLMNodeExecutor` 类，实现 `executor(node_id, ctx) -> NodeResult` 协议 |
| A4 | `core/runtime/execution/session.py` | L68 | `RuntimeSession.__init__` 根据配置选择 `DefaultNodeExecutor` 或 `LLMNodeExecutor` |
| A5 | `core/tools/runtime/orchestrator.py` | L362 | `_execute_v3` 传入 `run_meta={"model_provider": ..., "model_version": ...}` |

**LLM 调用点设计**:

| 节点 | LLM 任务 | 输入 | 输出 |
|------|---------|------|------|
| `problem_analysis` | 题面解析 + 问题分解 | 题面文本 | problem artifact payload（结构化问题描述）+ sub_questions |
| `literature_search` | 文献检索策略生成 | 问题描述 | 检索关键词 + 方法卡选择理由 |
| `model_selection` | 模型选型推理 | 问题描述 + 候选方法卡 | 选型决策 + reasoning + evidence_ids |
| `model_construction` | 数学模型构建 | 问题描述 + 选型结果 | model payload（objective/constraints/variables/equations） |
| `experiment` | 实验代码生成 + 执行 | 模型 + 实验计划 | 实际代码执行结果（数值） |
| `evidence_build` | 结论生成 | 实验结果 | claim payload（有意义的结论文本） |
| `paper_sections` | 论文章节撰写 | 大纲 + claim + 结果 | paper_section payload（≥200 字的实际内容） |

**可行性**: ⭐⭐⭐⭐（高）
- Node Executor 协议已设计为可替换
- `run_meta` 机制已存在，只需传入
- LLM 调用逻辑可封装在独立模块中，不侵入现有确定性节点
- **风险**: 需要 LLM API key 和网络访问；实验节点需要代码执行沙箱（cloud_sandbox.py 已有 E2B/Daytona 集成但默认关闭）

**Non-regression 验证**:
- `py -3.12 core/tools/validate.py` 57 项全绿
- `py -3.12 -m pytest tests -q` 758 passed / 11 skipped
- `py -3.12 core/tools/catalog_check.py --check` 双视图一致
- 默认配置（无 LLM provider）时行为不变，仍走 `DefaultNodeExecutor`

---

### 方案 B：找到正确的 LLM 执行入口

**描述**: V3 是确定性管线，LLM 执行在别处（如外部 OpenAI Agents SDK / Codex CLI）。

**调查结果**:
- `adapters/openai.yaml` 是 OpenAI Agents SDK 兼容配置，定义了 29 agent 的工具调用
- 但 MathModel 仓库**不包含** OpenAI Agents SDK 的运行时或启动脚本
- 没有任何文档说明如何在 OpenAI Agents SDK 中加载此配置并驱动流水线
- `core/tools/runtime/gen_runtime_manifest.py` 仅生成/校验此文件，不执行

**可行性**: ⭐⭐（低）
- 需要用户自行安装 OpenAI Agents SDK / Codex CLI
- 需要编写外部启动脚本（仓库中不存在）
- 29 agent 的 SKILL.md 指令是为人类/通用 LLM agent 设计的，不是为 OpenAI Agents SDK 的 tool-calling 模式优化的
- **不推荐作为 B0-R2 的执行路径**

---

### 方案 C：V2 legacy 管线触发 LLM

**描述**: `orchestrator --legacy` 的 29-agent 管线调用 LLM 执行 SKILL.md 指令。

**调查结果**:
- `_execute_step` 解析 SKILL.md 但**从不将指令发送给 LLM**
- 29 个 agent 的 SKILL.md 是指令文本，设计为由**人类或外部 LLM agent** 逐步执行
- orchestrator 本身只做门禁检查和状态推进，不做内容生成
- V2 legacy 模式与 V3 一样是零 LLM

**可行性**: ⭐（极低）
- 需要重写 `_execute_step` 以在每步调用 LLM 执行 SKILL.md 的 Procedure
- 29 步 × LLM 调用 = 高延迟和高成本
- SKILL.md 的指令粒度不统一（有的是具体步骤，有的是高层指导），LLM 执行质量不可控
- **不推荐**

---

### 方案 D：research-layer mock LLM executor

**描述**: 在 research 层实现一个 mock LLM executor，用确定性规则模拟 LLM 输出（非空 payload、有意义的文本、数值结果），用于验证评估器和 gate 是否正确工作。

**设计**:
- 实现 `MockLLMNodeExecutor`，遵循与 `DefaultNodeExecutor` 相同的协议
- 每个节点用模板 + 随机化生成非空 artifact payload
- `model_construction`: 生成包含 objective/constraints/variables/equations 的 model payload
- `experiment`: 生成包含数值结果的 result payload（如 `{"values": {"collision_time": 3.42}}`）
- `paper_sections`: 生成 ≥200 字的章节内容
- `run_meta`: 传入 `{"model_provider": "mock-llm", "model_version": "mock-v1", "token_cost": 0.0}`

**可行性**: ⭐⭐⭐⭐⭐（最高）
- 零外部依赖，零 API key，零网络
- 可验证 gate（Execution Authenticity Gate + Artifact Integrity Gate）对非空 artifact 的判定
- 可验证 evaluator（score_compute）对有内容论文的评分
- 可验证全链路"输入→执行→artifact→gate→evaluator"
- **不是真实能力测量，但可以验证测量仪器是否工作**

**局限性**:
- mock 输出的质量不代表真实 LLM 的能力
- 不能用于 benchmark 评分（测量的是 mock 的能力，不是系统的能力）
- 仅用于 B0-R2 的"测量仪器验证"阶段

---

## 5. 推荐方案：A + D 组合

### 5.1 分阶段策略

| 阶段 | 方案 | 目标 | 产出 |
|------|------|------|------|
| **B0-R2 立即** | D (mock LLM executor) | 验证测量仪器（gate + evaluator）对非空 artifact 的判定正确性 | `research/P15/measurement_recovery/mock_llm_executor.py` + 测试报告 |
| **B0-R3 短期** | A (core minimal patch) | 使 `orchestrator --execute` 可配置地切换到真实 LLM 执行 | `core/runtime/execution/llm_executor.py` + env 配置 + non-regression 验证 |
| **B0-R4 中期** | A 深化 | 实验节点接入代码执行沙箱（cloud_sandbox E2B/Daytona），实现真实数值结果 | 实验执行后端 + 结果验证 |

### 5.2 为什么不单独用方案 A

- 方案 A 需要 LLM API key 和网络，在当前环境可能不可用
- 即使有 LLM，第一次接入需要调试 prompt 和输出格式，测量仪器本身可能有 bug
- 先用方案 D 验证测量仪器，再用方案 A 接入真实 LLM，可以区分"测量仪器 bug"和"LLM 输出质量问题"

### 5.3 为什么不单独用方案 D

- mock LLM 不能测量系统的真实能力
- B0-R2 的最终目标是真实能力测量，mock 只是前置验证
- 方案 A 是实现真实执行的必要条件

### 5.4 B0-R2 执行路径建议

```
B0-R2 执行流程:
1. [已完成] 零 LLM 根因确认（本报告）
2. [已完成] 测量仪器验证（test_measurement_pipeline.py, 7/7 PASS）
3. [下一步] 实现 mock_llm_executor.py（方案 D）
   - 构造非空 artifact（model payload 含 equations, result 含数值, paper_section ≥200字）
   - 跑 Execution Authenticity Gate → 验证 EAG-01/02/05/10/13 通过
   - 跑 Artifact Integrity Gate → 验证 pass_rate ≥ 0.8
   - 跑 score_compute → 验证评分数值合理
4. [下一步] 设计 core minimal patch（方案 A，仅设计不执行）
   - LLMNodeExecutor 类设计
   - env 配置设计
   - RuntimeSession 集成点
   - non-regression 验证计划
5. [B0-R3] 执行 core minimal patch，接入真实 LLM
6. [B0-R3] 用真实 LLM 跑 benchmark，获得真实能力测量
```

---

## 6. Core Minimal Patch 详细设计（方案 A，仅提案不执行）

### 6.1 Patch 清单

| Patch ID | 文件 | 操作 | 行数 | 风险 |
|----------|------|------|------|------|
| P-A1 | `core/env/schema.yaml` | 新增 `runtime.llm` 配置节 | +15 | 低（additive） |
| P-A2 | `core/env/config.yaml` | 新增默认 `runtime.llm.enabled: false` | +5 | 低（additive） |
| P-A3 | `core/runtime/execution/llm_executor.py` | 新增文件：`LLMNodeExecutor` 类 | ~300 | 中（新模块） |
| P-A4 | `core/runtime/execution/session.py` | L47-71: `__init__` 根据配置选择 executor | +10 | 低（条件分支） |
| P-A5 | `core/tools/runtime/orchestrator.py` | L362: 传入 `run_meta` | +5 | 低（additive） |

**总计**: ~335 行新增，15 行修改，无删除。

### 6.2 P-A3: LLMNodeExecutor 核心设计

```python
# core/runtime/execution/llm_executor.py（新增文件，设计稿）

class LLMNodeExecutor:
    """LLM 驱动的节点执行器，遵循 executor(node_id, ctx) -> NodeResult 协议。
    
    与 DefaultNodeExecutor 的区别：
    - problem_analysis: 调用 LLM 解析题面文本，生成结构化问题描述
    - model_construction: 调用 LLM 构建数学模型（objective/constraints/equations）
    - experiment: 调用 LLM 生成实验代码，在沙箱中执行，获得真实数值结果
    - evidence_build: 调用 LLM 基于实验结果生成有意义的结论
    - paper_sections: 调用 LLM 撰写论文章节（≥200 字实际内容）
    
    其余节点（literature_search, model_selection, gates, etc.）复用
    DefaultNodeExecutor 的确定性实现（方法卡检索/竞技场/门禁不需要 LLM）。
    """
    
    def __init__(self, registry, graph, state=None, decisions=None,
                 llm_config: dict = None, **kwargs):
        self.registry = registry
        self.graph = graph
        self.state = state
        self.decisions = decisions
        self.llm_config = llm_config or {}
        # 复用确定性 executor 处理非 LLM 节点
        self._deterministic = DefaultNodeExecutor(
            registry, graph, state=state, decisions=decisions, **kwargs)
        self._client = self._init_llm_client()
    
    def _init_llm_client(self):
        """根据配置初始化 LLM 客户端（openai / anthropic / 本地）。"""
        provider = self.llm_config.get("provider", "openai")
        api_key = os.environ.get(self.llm_config.get("api_key_env", "OPENAI_API_KEY"))
        if not api_key:
            raise HandlerError(f"LLM provider {provider} 需要 API key "
                             f"(env: {self.llm_config.get('api_key_env')})")
        if provider == "openai":
            from openai import OpenAI
            return OpenAI(api_key=api_key,
                         base_url=self.llm_config.get("base_url"))
        # ... 其他 provider
    
    def __call__(self, node_id: str, ctx: dict) -> NodeResult:
        base = node_id.split("@", 1)[0]
        # LLM 节点
        if base in ("problem_analysis", "model_construction", "experiment",
                     "evidence_build", "paper_sections"):
            return getattr(self, f"_llm_{base}")(node_id, ctx)
        # 确定性节点复用 DefaultNodeExecutor
        return self._deterministic(node_id, ctx)
    
    def _llm_problem_analysis(self, node_id, ctx) -> NodeResult:
        """读取题面文本 → LLM 解析 → 非空 problem/question artifact。"""
        problem_text = self._read_problem_text()
        prompt = f"解析以下数学建模赛题，输出结构化问题描述...\n\n{problem_text}"
        response = self._call_llm(prompt, response_format="json")
        # 解析 response，创建非空 artifact
        ...
    
    def _call_llm(self, prompt: str, response_format: str = "text") -> str:
        """调用 LLM API，记录 token 用量。"""
        t0 = time.perf_counter()
        resp = self._client.chat.completions.create(
            model=self.llm_config.get("model", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            temperature=self.llm_config.get("temperature", 0.3),
        )
        self._token_usage += resp.usage.total_tokens
        return resp.choices[0].message.content
```

### 6.3 P-A4: RuntimeSession 集成点（修改前/后）

**修改前** (`session.py:68-71`):
```python
self.executor_impl = DefaultNodeExecutor(
    self.registry, self.graph, state=self.state,
    decisions=self.decisions, knowledge_root=knowledge_root,
    features=features, min_coverage=min_coverage)
```

**修改后**:
```python
llm_config = self._load_llm_config()
if llm_config.get("enabled"):
    from runtime.execution.llm_executor import LLMNodeExecutor
    self.executor_impl = LLMNodeExecutor(
        self.registry, self.graph, state=self.state,
        decisions=self.decisions, knowledge_root=knowledge_root,
        features=features, min_coverage=min_coverage,
        llm_config=llm_config)
    self.run_meta.update({
        "model_provider": llm_config.get("provider"),
        "model_version": llm_config.get("model"),
    })
else:
    self.executor_impl = DefaultNodeExecutor(
        self.registry, self.graph, state=self.state,
        decisions=self.decisions, knowledge_root=knowledge_root,
        features=features, min_coverage=min_coverage)
```

### 6.4 为什么是 minimal patch

1. **新增为主，修改极少**: ~335 行新增（主要在新文件 `llm_executor.py`），仅 15 行修改（条件分支 + run_meta 传入）
2. **默认行为不变**: `runtime.llm.enabled` 默认为 `false`，不配置时完全走 `DefaultNodeExecutor`，与现有行为 100% 一致
3. **协议兼容**: `LLMNodeExecutor` 遵循与 `DefaultNodeExecutor` 相同的 `executor(node_id, ctx) -> NodeResult` 协议，`WorkflowEngine`/`WaveExecutor` 无需修改
4. **非 LLM 节点复用**: 16 个节点中仅 5 个需要 LLM（problem_analysis, model_construction, experiment, evidence_build, paper_sections），其余 11 个复用确定性实现
5. **可回退**: 任何 LLM 节点失败可降级为确定性实现（`try LLM → except → fallback to DefaultNodeExecutor`）

### 6.5 Non-regression 验证计划

```powershell
# 1. 默认配置（LLM 关闭）下行为不变
py -3.12 core/tools/orchestrator.py rcs1-2024a --execute
# 预期: 与 patch 前完全相同的 16 节点零 LLM 执行，run_id 一致

# 2. 57 项项目级校验
py -3.12 core/tools/validate.py
# 预期: 全绿

# 3. catalog 双视图一致
py -3.12 core/tools/catalog_check.py --check
# 预期: 无漂移

# 4. 单元测试
py -3.12 -m pytest tests -q
# 预期: 758 passed / 11 skipped（基线不变）

# 5. LLM 配置缺失时的优雅降级
# 设置 runtime.llm.enabled: true 但不设 API key
# 预期: 明确报错 "LLM provider needs API key"，不崩溃，不产生半成品 artifact

# 6. Replay 一致性
py -3.12 core/tools/replay.py rcs1-2024a
# 预期: 确定性执行的 run 可重放，hash 全匹配
```

---

## 7. 测量仪器验证结果（test_measurement_pipeline.py）

### 7.1 测试矩阵

| 测试 ID | 描述 | 结果 |
|---------|------|------|
| T1 | 空 artifact 注册表 → Artifact Integrity Gate INVALID | PASS (pass_rate=0.0%) |
| T2 | 非空 model artifact → Layer1 non-empty PASS | PASS (overall=PASS) |
| T3 | 混合注册表（50% 空壳）→ 正确识别空壳比例 | PASS (PASS=2, INVALID=2) |
| T4 | 零 LLM RunRecord → Execution Authenticity Gate INVALID | PASS (10/13 checks FAIL) |
| T5 | 模拟 LLM RunRecord → 关键检查 EAG-01/02/05/13 PASS | PASS |
| T6 | score_compute 对最小论文评分不崩溃 | PASS (academic=4.5, eng=3.9, judge=4.75) |
| T7 | 全链路集成（构造项目→写 registry→跑 gate→断言 verdict） | PASS (AIG pass_rate=100%) |

### 7.2 关键发现

1. **Gate 对空壳 artifact 的判定正确**: T1 中 6 个空壳 artifact 的 pass_rate=0.0%，overall=INVALID
2. **Gate 对非空 artifact 的判定正确**: T2 中手工构造的非空 model artifact 通过 Layer1
3. **EAG 对零 LLM 特征的识别正确**: T4 中 `model_provider=null` + `latency=0.06s` 触发 10/13 项 FAIL，overall=INVALID
4. **EAG 对模拟 LLM 特征的识别正确**: T5 中 `model_provider="openai"` + `latency=45.3s` + `execution_mode="llm"` 使 EAG-01/02/05/13 全部 PASS
5. **score_compute 工作正常**: T6 对最小论文给出合理评分（academic=4.5/10, engineering=3.9/10, judge=4.75/10）
6. **全链路可验证**: T7 构造完整项目（非空 artifact + 模拟 LLM run record + 代码文件），AIG pass_rate=100%

### 7.3 测量仪器结论

**Gate 和 evaluator 本身工作正常，能正确区分空壳/非空 artifact 和零 LLM/真实 LLM 执行特征。** B0-R2 的瓶颈不在测量仪器，而在执行管线本身不产生非空 artifact 和真实 LLM 执行。

---

## 8. 证据索引

| 证据 | 路径 | 关键行/内容 |
|------|------|------------|
| V3 orchestrator 实现 | `core/tools/runtime/orchestrator.py` | L350-382 `_execute_v3`, L137-235 `_execute_step` |
| DefaultNodeExecutor 零 LLM 声明 | `core/runtime/execution/handlers.py` | L13-15 |
| DefaultNodeExecutor 默认 features | `core/runtime/execution/handlers.py` | L75-79 |
| RuntimeSession executor 选择 | `core/runtime/execution/session.py` | L68-71 |
| RunRecord model_provider 字段 | `core/runtime/state/runs.py` | L10-11, L129 |
| ControlledRenderer LLM 可插拔接口 | `core/runtime/writing/paragraphs.py` | L403-425 |
| adapters/openai.yaml 生成器 | `core/tools/runtime/gen_runtime_manifest.py` | L191-213 |
| env 配置（无 LLM） | `core/env/config.yaml` | 全文仅 18 行 |
| external_skills 声明 | `catalog/external_skills.yaml` | pdf-parser/latex-compiler/code-executor/syslab（均非 LLM） |
| RC-S1 RunRecord | `projects/rcs1-2024a/state/runs/22a4bf4ad576.json` | model_provider=null, latency=0.07s |
| RC-S1 V2 状态 | `projects/rcs1-2024a/work/state.json` | completed=[], 0/29 |
| RC-SMOKE S1 报告 | `research/RC-SMOKE/S1_SMOKE_RECORD.md` | "全程本地，无外部 provider 调用" |
| RC-SMOKE S3 审计 | `research/RC-SMOKE/S3_PROVIDER_AUDIT.md` | adapters/openai.yaml 未启用 |
| 全代码库 LLM 搜索 | `rg -i 'import openai|from openai|client.chat' core/**/*.py` | 0 匹配 |
| 测量仪器测试 | `research/P15/measurement_recovery/test_measurement_pipeline.py` | 7/7 PASS |

---

## 9. 产出文件清单

| 文件 | 绝对路径 | 说明 |
|------|---------|------|
| 调查报告 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\measurement_recovery\EXECUTION_PIPELINE_INVESTIGATION.md` | 本文件 |
| 测量仪器测试 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\measurement_recovery\test_measurement_pipeline.py` | 7 项端到端测试，7/7 PASS |
| Execution Authenticity 协议 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\measurement_recovery\EXECUTION_AUTHENTICITY_PROTOCOL.md` | 上一轮产出，13 项检查 |
| Artifact Integrity 协议 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\measurement_recovery\ARTIFACT_INTEGRITY_PROTOCOL.md` | 上一轮产出，三层完整性 |
| Gate 实现 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\measurement_recovery\execution_gate.py` | 上一轮产出，deterministic gate |

---

## 10. 关键结论

1. **V3/V2/RC-S1 三条执行路径全部零 LLM**，有代码级证据（零 API 客户端导入 + handlers.py 明确声明 + RunRecord model_provider=null）
2. **唯一的 LLM 可插拔点** (`ControlledRenderer`) 从未被任何执行路径调用
3. **`adapters/openai.yaml` 是配置文件不是客户端**，设计为外部 OpenAI Agents SDK 使用，但仓库无运行时
4. **测量仪器（gate + evaluator）工作正常**，能正确区分空壳/非空和零 LLM/真实 LLM
5. **推荐方案 A + D 组合**：先用 mock LLM executor（方案 D）验证全链路，再设计 core minimal patch（方案 A）接入真实 LLM
6. **Core minimal patch 是可行的**：~335 行新增，15 行修改，默认行为不变，协议兼容，可回退
7. **B0-R2 下一步**：实现 `mock_llm_executor.py`，用非空 artifact 跑通全链路 gate + evaluator，为真实 LLM 接入做准备
