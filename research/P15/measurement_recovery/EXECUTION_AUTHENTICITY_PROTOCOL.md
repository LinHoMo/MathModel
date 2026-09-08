# Execution Authenticity Protocol — P15 Measurement Recovery

> **版本**: 1.0
> **日期**: 2026-09-08
> **审计对象**: 2024_A B0 run (`projects/p151-2024a/`, run_id `5c98cd9911bc`)
> **审计范围**: orchestrator V3 执行管线 → RuntimeSession → DefaultNodeExecutor → RunRecord
> **核心结论**: B0 "运行"是**确定性零 LLM 模板初始化**，不是真实研究执行。16/16 节点"完成"但产出 16 个空壳 artifact。

---

## 1. 2024_A B0 执行过程还原

### 1.1 调用链（命令行 → 执行引擎）

```
py -3.12 core/tools/orchestrator.py p151-2024a --execute
  └─ core/tools/orchestrator.py (shim)
       └─ core/tools/runtime/orchestrator.py::main()
            └─ _run_v3(base, dry_run=False, competition=None)
                 └─ _execute_v3(project_dir, questions=["Q001"])
                      └─ RuntimeSession(project_dir, ["Q001"], max_workers=1)
                           ├─ DefaultNodeExecutor(registry, graph, state, decisions, ...)
                           ├─ WorkflowEngine(dag, executor, state, on_success)
                           └─ WaveExecutor(dag, executor, max_workers=1)
                                └─ session.run()
                                     ├─ waves.run()  → 16 节点依次执行
                                     ├─ engine.save_progress()
                                     ├─ checkpoint()  → registry/graph/state/decision_log 落盘
                                     └─ _emit_run_record() → state/runs/5c98cd9911bc.json
```

**关键证据**:
- `core/tools/runtime/orchestrator.py:500` — `dry_run=not args.execute`，传入 `--execute` 时 `dry_run=False`
- `core/tools/runtime/orchestrator.py:350-382` — `_execute_v3` 创建 `RuntimeSession` 并调用 `session.run()`
- `core/runtime/execution/session.py:68` — `self.executor_impl = DefaultNodeExecutor(...)`

### 1.2 16 个 DAG 节点执行清单

DAG 由 `base.yaml` + 5 个 stage 文件组合，按 Q001 展开 per_question 节点：

| # | 节点 ID | stage | handler | 产出 artifact | payload 状态 |
|---|---------|-------|---------|--------------|-------------|
| 1 | `problem_analysis` | problem-analysis | `do_problem_analysis` | P001 (problem) | `[]` 空 |
| 2 | `literature_search` | problem-analysis | `do_literature_search` | D001 (decision) | `["mc-topsis","mc-ahp","mc-pca"]` 方法卡ID |
| 3 | `model_selection` | modeling | `do_model_selection` | M001 (model) | `[]` 空（data 含 card_id） |
| 4 | `model_construction` | modeling | `do_model_construction` | A001,A002 (assumption) | `[]` 空 |
| 5 | `model_critique` | modeling | `do_model_critique` | （无 artifact，纯检查） | — |
| 6 | `assumption_check` | modeling | `do_assumption_check` | （无 artifact，纯检查） | — |
| 7 | `experiment_design` | experiment | `do_experiment_design` | D002 (decision) | `["mc-topsis","mc-ahp"]` 方法卡ID |
| 8 | `experiment@Q001` | experiment | `do_experiment` | E001,R001,F001 | `[]` 空（data 含 plan_ref） |
| 9 | `experiment_critique@Q001` | experiment | `do_experiment_critique` | （无 artifact，纯检查） | — |
| 10 | `evidence_build` | evidence | `do_evidence_build` | C001 (claim) | `[]` 空（data 含 statement） |
| 11 | `evidence_gate` | evidence | `do_evidence_gate` | （无 artifact，纯检查） | — |
| 12 | `quality_evaluation` | evidence | `do_quality_evaluation` | （无 artifact，纯检查） | — |
| 13 | `research_direction` | paper | `do_research_direction` | （无 artifact，纯叙事） | — |
| 14 | `paper_projection` | paper | `do_paper_projection` | （无 artifact，纯投影） | — |
| 15 | `paper_sections@Q001` | paper | `do_paper_sections` | S001-S005 (paper_section) | `["问题重述与分析"]` 等单字符串 |
| 16 | `paper_review` | paper | `do_paper_review` | （无 artifact，纯判审） | — |

**registry 计数器**: problem=1, question=1, decision=2, model=1, assumption=2, experiment=1, result=1, figure=1, claim=1, paper_section=5 → **总计 16 个 artifact**（与 16 节点不一一对应，部分节点产出多个，部分不产出）。

### 1.3 Run Manifest 异常指标

| 字段 | B0 实测值 | 正常期望值 | 异常判定 |
|------|----------|-----------|---------|
| `latency.seconds` | 0.06 | > 10（含 LLM 调用） | **INVALID** — 模板初始化速度 |
| `model_provider` | `null` | `"openai"` / `"anthropic"` / 本地模型名 | **INVALID** — 零 LLM |
| `model_version` | `null` | `"gpt-4o-2024-05-13"` 等 | **INVALID** — 零 LLM |
| `skill_version` | `e3b0c44...b7852b855` | 非空 SHA256 | **INVALID** — 空字符串 SHA256 |
| `token_cost` | `null` | > 0 数值 | **INVALID** — 零 LLM |
| `prompt_hash` | = `workflow_version` | 独立 prompt 哈希 | **SUSPECT** — 设计上等同 |
| `engine.completed_nodes` | 16 | 16 | 表面正常，但空壳 |
| `engine.failures` | `[]` | `[]` | 表面正常 |
| `decision` | `null` | 决策摘要 | **INVALID** — 无决策记录 |

**skill_version 空哈希根因**: `core/runtime/state/runs.py:75-77` 的 `skill_version()` 调用 `hash_globs(["core/skills"], REPO)`，该函数只 glob `*.yaml` 文件。`core/skills/` 目录下仅有 `critics/` 子目录且无 `.yaml` 文件 → 文件列表为空 → `hashlib.sha256(b"").hexdigest()` = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。

### 1.4 "TOPSIS 选择"来源追踪

**不是 agent 决策，是方法卡推荐系统的模板默认值。** 证据链：

1. `DefaultNodeExecutor.__init__` (handlers.py:75-79) 设置默认 features:
   ```python
   self.features = dict(features or {
       "problem_types": ["evaluation"],
       "has_data": True,
       "sample_size": "medium",
   })
   ```
2. `do_literature_search` (handlers.py:187) 调用 `self.retriever.recommend(self.features, top_k=3)`
   - 输入 features 硬编码为 `problem_types=["evaluation"]`
   - 返回 top-3: mc-topsis(76), mc-ahp(73), mc-pca(63)
3. `do_model_selection` (handlers.py:209) 调用 `self.arena.select(qid, qf, ...)`
   - MethodArena 选择得分最高的 mc-topsis
   - decision_log D001 记录 `chosen: "mc-topsis"`, `confidence: 0.95`, `created_by: "model_selection"`
4. **关键**: 整个过程从未读取赛题文本 `examples/problems/cumcm2024A.txt` 的内容。features 是硬编码默认值，不是从题面提取的。2024_A 实际是**物理/运动学问题**（龙形螺线、龙头把手坐标、碰撞检测），与"evaluation"题型完全不符。

**decision_log D001 的 `evidence_ids: []`** — 决策无任何证据支撑，进一步确认是模板默认值。

### 1.5 V2 状态 0/29 的含义

V2 状态文件 (`work/state.json`, `work/STATE.md`) 显示:
- `completed: []`
- `current: {hand: "modeler", agent: "problem-parser", stage: 1}`
- 进度 0/29

**原因**: V3 执行路径 (`RuntimeSession`) 与 V2 状态系统 (`work/state.json`) 是**两套独立的状态存储**。V3 写入 `state/status.json`、`state/registry.json` 等，从不触碰 `work/state.json`。V3 的 16/16 节点完成与 V2 的 0/29 步完成之间没有任何同步机制。

**state/status.json 的 `run.phase: "init"`** — 即使 V3 跑完了 16 节点，status.json 仍标记为 init 阶段，因为 `RuntimeSession` 没有更新 `run.phase` 字段。

---

## 2. Root-Cause 分析

### 2.1 根本原因：DefaultNodeExecutor 是确定性零 LLM 管线

**直接证据** (`core/runtime/execution/handlers.py:13-15`):
```
本实现是**确定性认知管线**（零 LLM）：文献检索/方法竞技场/实验规划器/研究叙事/
论文投影/批判器全部复用 core/runtime 下的真实模块，产出可追溯到
Artifact Registry + Evidence Graph 的研究状态。LLM 节点后续按同一协议接入。
```

这是**设计意图**，不是 bug。V3 执行引擎在 P6 阶段实现了确定性骨架，LLM 节点标注为"后续按同一协议接入"。但问题在于：

1. **orchestrator `--execute` 标志的语义误导**: 用户期望 `--execute` 触发"真实研究执行"，实际触发的是"确定性模板初始化"。没有任何警告或配置项告知用户当前是零 LLM 模式。
2. **RunRecord 不区分执行模式**: `model_provider=null` 被注释为"诚实缺省，不臆造"（runs.py:11），但 RunRecord 的 `status: "completed"` 和 `engine.completed_nodes: 16` 给人"执行成功"的错觉。
3. **空 payload artifact 被标记为 "active"**: registry 中所有 artifact 的 `lifecycle_history` 都包含 `"reason": "registered with payload"`，即使 `payload=[]`。这是误导性的状态消息。

### 2.2 缺陷分类

| # | 缺陷 | 类型 | 严重度 | 位置 |
|---|------|------|--------|------|
| D1 | `--execute` 触发零 LLM 确定性管线，无模式标识 | core 设计缺陷 | P0 | orchestrator.py:350-382 |
| D2 | RunRecord 无 `execution_mode` 字段区分 deterministic/llm | core schema 缺陷 | P0 | runs.py:119-149 |
| D3 | 空 payload artifact 被标记为 "registered with payload" | core 逻辑缺陷 | P1 | registry create 逻辑 |
| D4 | `skill_version` 返回空字符串 SHA256 时无警告 | core 边界缺陷 | P2 | runs.py:75-77 |
| D5 | `prompt_hash` 等于 `workflow_version`，不哈希实际 prompt | core 设计缺陷 | P2 | runs.py:131 |
| D6 | V3/V2 状态无同步，16/16 与 0/29 并存 | core 架构缺陷 | P1 | session.py / state.py |
| D7 | features 硬编码默认值，不读取题面文本 | core 逻辑缺陷 | P0 | handlers.py:75-79 |
| D8 | artifact `provenance={}` / `validation={}` 全空，无执行溯源 | core schema 缺陷 | P1 | handlers.py 所有 create 调用 |

### 2.3 哪些是 core bug，哪些是 research-layer 配置

**需要 core minimal patch 的（不修改 v3.1.x architecture）**:
- D2: 在 RunRecord schema 中增加 `execution_mode` 字段（`"deterministic"` / `"llm"` / `"hybrid"`），`DefaultNodeExecutor` 运行时标记为 `"deterministic"`
- D3: registry create 时若 `payload=[]` 且 `data={}`，lifecycle reason 应为 `"registered (empty)"` 而非 `"registered with payload"`
- D4: `skill_version()` 若返回空哈希，应在 RunRecord 中标记 `skill_version_warning: "no skill yaml files found"`
- D1: 在 `_execute_v3` 入口打印明确警告：`[V3][EXEC] 当前为确定性零 LLM 模式（execution_mode=deterministic），LLM 节点未接入`

**属于 research-layer 配置/新增的（不修改 core）**:
- Execution Authenticity Gate（本协议定义）
- Artifact Non-Emptiness Gate（本协议定义）
- benchmark 运行前的 pre-flight 检查
- 真实 LLM executor 的接入配置（需要外部 LLM provider 配置，属于 P+ 阶段工作）

---

## 3. Execution Authenticity Gate 规格

### 3.1 设计原则

- **deterministic first**: 所有检查项必须可由代码确定性判定，不依赖 LLM
- **fail-closed**: 任何一项 INVALID → 整体 INVALID，不允许"部分通过"
- **三层语义**: 区分 `non-empty`（有东西）/ `structurally valid`（结构对）/ `semantically populated`（内容有意义）
- **可追溯**: 每项检查输出具体检查值和判定依据，不允许只输出 PASS/FAIL

### 3.2 检查项清单（13 项）

#### EAG-01: model_provider 非空
- **检查**: `run_record.model_provider is not None and isinstance(str) and len > 0`
- **通过标准**: 非空字符串，如 `"openai"`, `"anthropic"`, `"local-ollama"`
- **失败处理**: INVALID — 零 LLM 执行
- **B0 实测**: `null` → **FAIL**

#### EAG-02: model_version 非空
- **检查**: `run_record.model_version is not None and isinstance(str) and len > 0`
- **通过标准**: 非空字符串，如 `"gpt-4o-2024-05-13"`, `"claude-3-5-sonnet-20240620"`
- **失败处理**: INVALID
- **B0 实测**: `null` → **FAIL**

#### EAG-03: skill_version 非空哈希
- **检查**: `run_record.skill_version != SHA256_EMPTY and len == 64 and all(c in "0123456789abcdef" for c in skill_version)`
- **通过标准**: 64 位十六进制，且不等于空字符串 SHA256 (`e3b0c44...`)
- **失败处理**: INVALID — 无技能指令包
- **B0 实测**: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` → **FAIL**

#### EAG-04: execution timestamp 合理
- **检查**: `run_record.started_at` 可解析为 ISO 8601；`finished_at - started_at > 0`；时间不在未来（允许 60s 时钟偏差）
- **通过标准**: 起止时间合理，duration > 0
- **失败处理**: FAIL（时间异常可能是时钟问题，不直接 INVALID）
- **B0 实测**: `started_at = finished_at = 2026-09-08T00:35:58Z` → duration=0 → **FAIL**

#### EAG-05: latency > 阈值
- **检查**: `run_record.latency.seconds >= MIN_LATENCY_THRESHOLD`（默认 1.0 秒）
- **通过标准**: ≥ 1.0s（真实 LLM 调用通常 > 10s；1s 是绝对下限，排除纯内存操作）
- **失败处理**: INVALID — 模板初始化速度
- **B0 实测**: 0.06s → **FAIL**

#### EAG-06: input_hash 与 manifest 一致
- **检查**: 重新计算 `inputs/` 目录 SHA256，与 `run_record.input_hash` 对比
- **通过标准**: 哈希一致（证明输入未被篡改）
- **失败处理**: FAIL（输入不一致，可能是重放攻击或数据损坏）
- **B0 实测**: `inputs/` 为空目录 → `input_hash = SHA256("<empty-inputs>")` → 与 manifest 一致 → **PASS**（但空输入本身是问题）

#### EAG-07: workflow_hash 与 DAG 定义一致
- **检查**: 重新计算 `core/roles/` + `core/workflows/` 的 YAML 组合哈希，与 `run_record.workflow_version` 对比
- **通过标准**: 哈希一致
- **失败处理**: FAIL
- **B0 实测**: 一致 → **PASS**

#### EAG-08: tool invocation 记录存在
- **检查**: 检查项目目录下是否存在真实执行痕迹：`code/` 目录有 .py 文件、`output/` 目录有结果文件、`artifacts/` 有非空产物
- **通过标准**: 至少存在一种真实执行产物（代码/输出/图表）
- **失败处理**: INVALID — 无执行痕迹
- **B0 实测**: `projects/p151-2024a/` 下无 `code/`、无 `output/`、无 `artifacts/` → **FAIL**

#### EAG-09: artifact count > 0
- **检查**: `len(registry.artifacts) > 0`
- **通过标准**: ≥ 1
- **失败处理**: INVALID
- **B0 实测**: 16 → **PASS**（但见 EAG-10）

#### EAG-10: artifact payload non-empty（调用 Artifact Integrity Gate Layer 1）
- **检查**: 对每个 artifact 运行 Artifact Non-Emptiness Gate Layer 1，统计通过率
- **通过标准**: ≥ 80% 的 artifact 通过 Layer 1 non-empty 检查（允许 paper_section 等轻量 artifact）
- **失败处理**: INVALID — 空壳 artifact
- **B0 实测**: 10/16 payload=[]，仅 6/16 有非空 payload（2 decision + 5 paper_section，但 paper_section 是单字符串）→ **FAIL**

#### EAG-11: decision_log 非空
- **检查**: `decision_log.decisions` 列表非空，且每个 decision 有 `evidence_ids` 非空或 `reasoning` 非模板默认值
- **通过标准**: ≥ 1 条决策，且决策有证据支撑
- **失败处理**: FAIL（无决策可能是简单问题，但 evidence_ids 为空是 INVALID）
- **B0 实测**: 1 条决策 (D001)，但 `evidence_ids=[]` → **FAIL**

#### EAG-12: execution-result binding（artifact 可追溯到具体执行）
- **检查**: 每个 artifact 的 `provenance` 字段非空，包含 `run_id` / `node_id` / `executor` 信息；或 `created_by` 指向具体节点处理器
- **通过标准**: ≥ 90% 的 artifact 有可追溯的执行来源
- **失败处理**: INVALID — artifact 来源不明
- **B0 实测**: 所有 artifact `provenance={}` → **FAIL**

#### EAG-13: execution_mode 标识
- **检查**: RunRecord 中存在 `execution_mode` 字段，值为 `"llm"` 或 `"hybrid"`（`"deterministic"` 视为模板初始化）
- **通过标准**: `execution_mode in ("llm", "hybrid")`
- **失败处理**: INVALID — 确定性模板初始化
- **B0 实测**: 字段不存在（core schema 缺陷 D2）→ **FAIL**

### 3.3 Gate 输出格式

```json
{
  "gate": "execution_authenticity",
  "version": "1.0",
  "project": "p151-2024a",
  "run_id": "5c98cd9911bc",
  "timestamp": "2026-09-08T00:35:58Z",
  "overall_verdict": "INVALID",
  "summary": {
    "pass": 3,
    "fail": 6,
    "invalid": 4,
    "total": 13
  },
  "checks": [
    {
      "id": "EAG-01",
      "name": "model_provider_non_empty",
      "verdict": "INVALID",
      "expected": "non-empty string",
      "actual": null,
      "message": "model_provider is null — zero-LLM execution"
    },
    ...
  ],
  "root_causes": [
    "DefaultNodeExecutor is deterministic zero-LLM pipeline",
    "orchestrator --execute triggers template initialization, not real execution",
    "10/16 artifacts have empty payload"
  ],
  "recommendations": [
    "Do not count this run as real execution in benchmark",
    "Require LLM executor configuration before re-running",
    "Apply Artifact Non-Emptiness Gate to all downstream consumers"
  ]
}
```

### 3.4 判定矩阵

| overall_verdict | 条件 |
|-----------------|------|
| `PASS` | 所有 13 项 PASS |
| `FAIL` | 无 INVALID，但有 ≥1 项 FAIL（可修复的配置/时间问题） |
| `INVALID` | ≥1 项 INVALID（空执行 / 零 LLM / 空壳 artifact） |

**铁律**: INVALID 的 run **不得**计入 benchmark 成功运行，不得作为论文数值来源，不得触发 state advance。

---

## 4. 修复建议

### 4.1 Core minimal patch（不修改 v3.1.x architecture）

| Patch | 文件 | 改动 | 风险 |
|-------|------|------|------|
| P1 | `core/runtime/state/runs.py` | RunRecord 增加 `execution_mode` 字段；`emit_run_record` 接受 `execution_mode` 参数，默认 `"deterministic"` | 低 — additive 字段 |
| P2 | `core/runtime/execution/session.py` | `_emit_run_record` 调用时传入 `execution_mode="deterministic"`（当使用 DefaultNodeExecutor 时） | 低 |
| P3 | `core/tools/runtime/orchestrator.py` | `_execute_v3` 入口打印警告：`[V3][EXEC] execution_mode=deterministic (zero-LLM). Real LLM execution requires external executor.` | 低 |
| P4 | `core/runtime/artifacts/registry.py` | create 时若 `payload=[]` 且 `data={}`，lifecycle reason 改为 `"registered (empty)"` | 低 — 仅消息文本 |
| P5 | `core/runtime/state/runs.py` | `skill_version()` 返回空哈希时，在 RunRecord 增加 `_warnings: ["skill_version: empty hash (no .yaml in core/skills)"]` | 低 |

### 4.2 Research-layer 新增（本审计产出）

| 项 | 文件 | 说明 |
|----|------|------|
| R1 | `research/P15/measurement_recovery/EXECUTION_AUTHENTICITY_PROTOCOL.md` | 本文件 |
| R2 | `research/P15/measurement_recovery/ARTIFACT_INTEGRITY_PROTOCOL.md` | Artifact 三层完整性门 |
| R3 | `research/P15/measurement_recovery/execution_gate.py` | deterministic gate 实现 |
| R4 | benchmark 运行前 pre-flight: 调用 `execution_gate.py` 验证上一轮 run，INVALID 则拒绝进入评分 |

### 4.3 长期架构建议（不在本次修复范围）

1. **LLM Executor 接入**: 实现 `LLMNodeExecutor` 类，遵循与 `DefaultNodeExecutor` 相同的 `executor(node_id, ctx) -> NodeResult` 协议，在 `RuntimeSession.__init__` 中根据配置选择 executor
2. **execution_mode 配置**: 在 `core/env/config.yaml` 增加 `runtime.execution_mode: "deterministic" | "llm" | "hybrid"` 配置项
3. **V3/V2 状态桥接**: 实现 V3 完成 → V2 状态反推进度的同步器，消除 16/16 与 0/29 的矛盾
4. **artifact provenance 强制**: registry create 时强制要求 `provenance` 字段包含 `run_id` 和 `node_id`，空则拒绝创建

---

## 5. 证据索引

| 证据 | 路径 | 关键行 |
|------|------|--------|
| Run manifest | `projects/p151-2024a/state/runs/5c98cd9911bc.json` | 全文 |
| Benchmark manifest | `research/P15/benchmark/manifests/p151-2024a-run.json` | 全文 |
| Registry (16 artifacts) | `projects/p151-2024a/state/registry.json` | 全文 |
| V3 status | `projects/p151-2024a/state/status.json` | `run.phase: "init"` |
| V2 status | `projects/p151-2024a/work/state.json` | `completed: []` |
| Decision log | `projects/p151-2024a/state/decision_log.json` | `evidence_ids: []` |
| Orchestrator shim | `core/tools/orchestrator.py` | 全文 (22行) |
| Orchestrator impl | `core/tools/runtime/orchestrator.py` | L350-382 `_execute_v3` |
| RuntimeSession | `core/runtime/execution/session.py` | L68 `DefaultNodeExecutor`, L97-129 `run()` |
| DefaultNodeExecutor | `core/runtime/execution/handlers.py` | L13-15 零LLM声明, L75-79 默认features |
| WaveExecutor | `core/runtime/execution/wave_executor.py` | L64-95 `run()` |
| WorkflowEngine | `core/runtime/execution/engine.py` | L111-167 `step()` / `_post_execute()` |
| RunRecord emitter | `core/runtime/state/runs.py` | L107-151 `emit_run_record`, L75-77 `skill_version` |
| DAG composer | `core/runtime/execution/composer.py` | L138-142 `compose_executable` |
| Stage defs | `core/workflows/stages/*.yaml` | 5 个文件 |
