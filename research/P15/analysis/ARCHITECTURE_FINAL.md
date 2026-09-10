# ARCHITECTURE FINAL — LinHoMo V3 最终架构设计

> **基于 5 路独立代码审计的证据重构**，不是"设计应该是什么"，而是"当前实际是什么 + 应该变成什么"。
> 审计基线：HEAD `022d457`，2026-09-10。

---

## 1. 当前实际架构（As-Is）

### 1.1 真实调用图（生产路径 orchestrator --execute）

```
orchestrator.py:391 _execute_v3
  └─ RuntimeSession(project, questions, features)  ← 不传 execution_adapter / validation_specs / external_*
       └─ WaveExecutor.engine (state=None, validators={})
            └─ DefaultNodeExecutor (handlers.py:68)
                 ├─ problem_analysis → P001 + Q001 + motivates 边        [REAL]
                 ├─ literature_search → decision artifact + based_on 边   [REAL]
                 ├─ model_selection → MethodArena.select → recs[0]       [REAL, 但选型=取第一]
                 ├─ model_construction → FAIL "no_model_ir" (无注入)     [BLOCKED]
                 ├─ (下游 17 节点全部被阻塞)
```

**实测结果**：临时项目 `orchestrator --execute` → 3/20 节点完成，model_construction BLOCKED，EXEC=0，VR=0，claims=0。

### 1.2 注入后链路（测试/实验脚本路径）

```
外部注入 external_model_irs + external_code + validation_specs
  └─ model_construction → MIR001 (登记)
       └─ code_generation → CODE001 (sha256)
            └─ model_execution → LocalPythonAdapter → subprocess.run
                 └─ EXEC001 (rc=0, status=success) → R001
                      └─ model_validation → validate_execution → VR001 + verified_by
                           └─ (FAIL → retries 耗尽 → blocked; 无自动 revision)
```

**此链路真实接通**（Runtime 审计实测：EXEC001 rc=0，VR001 failed 如实传播），但**仅在测试注入和独立脚本（vs001_driver.py / k003_formal_runner.py）中存在**，V3 主 DAG 生产路径从不注入。

### 1.3 断裂的链路（设计存在但生产未接通）

| 链路环节 | 代码存在 | 生产接通 | 判定 |
|---|---|---|---|
| Fidelity（Model→Code 保真） | `fidelity.py` 真实 | ❌ 仅 codegen.py:155 / CLI 调用 | TEST-ONLY |
| Revision（M1→M2 闭环） | `revision.py` + `diagnosis.py` 真实 | ❌ 仅 tests + vs001_driver.py | TEST-ONLY |
| Engine validators（6 个声明 gate） | `engine.py:181` hook 真实 | ❌ session.py 不传 validators，实测 {} | DEAD |
| Candidate Generation | `candidates.py` 真实 | ❌ CompetitionIntelligence 0 非测试调用方 | TEST-ONLY |
| Knowledge-guided Construction | `knowledge_guided.py` 真实 | ❌ 仅 tests + research/m4_run | TEST-ONLY |
| Candidate Comparison/Arena | `comparison.py` 真实 | ❌ 仅 vs001_driver + tests | TEST-ONLY |
| V3 Roles（5 个） | `roles.py` + `core/roles/*.yaml` | ❌ 仅 DAG 校验引用，handler 不读 | DEAD-in-prod |
| Critic Skills（4 个） | `core/skills/critics/*.yaml` | ❌ engine 不执行，Agent 手动驱动时可写 mark_validated | DEAD + 权限违规 |
| legacy 29 agents | `core/legacy/hands/` | ❌ V3 运行时零读取 | DEAD-in-prod |

### 1.4 信任边界漏洞（当前实际）

```
Agent 可写：
  ✅ problem interpretation / candidates / MODEL_IR / code / experiment_plan  (通过 external_* 注入)
  ❌ execution_result  (registry.create 无来源鉴别，实测伪造可通过)  ← 漏洞
  ❌ validation PASS   (critic SKILL.md 指令 mark_validated，registry 无门禁)  ← 漏洞
  ❌ evidence supports (add_relation 开放 API，无身份绑定)  ← 设计缺口

机械 Harness 写：
  ✅ ExecutionResult (adapter.execute → subprocess)
  ✅ Fidelity (fidelity.py 确定性)
  ✅ VR (validation.py run_checks)
  ✅ Evidence 边 (handlers 机械写入)
  ❌ 但零执行/零验证时返回 PASS (handlers.py:753, 776-781)  ← 语义漏洞
```

---

## 2. 最终架构（To-Be）

### 2.1 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Constructors（可替换）                │
│  MathModelAgent │ Pi │ OpenAI │ Claude │ Local(自研最小)          │
└────────────────────────┬────────────────────────────────────────┘
                         │ Constructor Protocol
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              core/runtime/constructors/（新增）                    │
│  protocol.py · adapter.py · registry.py · adapters/{local,openai,│
│  claude,mathmodel_agent,pi}.py                                   │
│  输出：ConstructionBundle（interpretation/candidates/MIR/code/    │
│  experiment_plan/reasoning_metadata/revision_request/raw_output） │
│  信任规则：bundle 内 execution_result/fidelity/validation 一律丢弃  │
└────────────────────────┬────────────────────────────────────────┘
                         │ ConstructionBundle（声明级）
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LinHoMo Runtime（核心，机械，LLM-free）          │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐    │
│  │ MODEL_IR 校验 │──▶│ Code 复跑     │──▶│ ExecutionResult  │    │
│  │ (schema gate) │   │ (adapter)    │   │ (subprocess,hash)│    │
│  └──────────────┘   └──────────────┘   └────────┬─────────┘    │
│                                                │              │
│  ┌──────────────┐   ┌──────────────┐            ▼              │
│  │ Revision     │◀──│ Failure      │◀──┐   Fidelity 检查      │
│  │ (supersede)  │   │ Diagnosis    │   │   (model↔code)      │
│  └──────┬───────┘   └──────────────┘   │   └────────┬─────────┘│
│         │                             │            │          │
│         ▼                             │            ▼          │
│  ┌──────────────┐                     │   ┌──────────────┐    │
│  │ New Model    │──re-execution───────┘   │ Mechanical   │    │
│  │ Version      │                         │ Validation   │    │
│  └──────────────┘                         │ (VR, checks) │    │
│                                           └──────┬───────┘    │
│                                                  │            │
│  ┌───────────────────────────────────────────────▼─────────┐  │
│  │              Evidence Graph（typed, fail-closed）         │  │
│  │  problem→question→model→code→exec→VR→claim→revision     │  │
│  └───────────────────────┬──────────────────────────────────┘  │
│                          │                                     │
│  ┌───────────────────────▼──────────────────────────────────┐  │
│  │         Artifact Registry + Lifecycle State Machine       │  │
│  │  draft→active→validated→published; terminal 不可复用      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Evaluation Layer（测量层）                       │
│  Constructor-independent Benchmark（2×2 析因，L6 主终点）          │
│  + Mechanical L6 判定（GT 数值对照）+ Blind Eval（L1/L2 辅助）     │
│  + BZD 评审知识资产（rubric/failure memory，经验常数禁入评分）      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心设计原则

1. **Constructor 可替换**：外部 Agent 通过 Constructor Protocol 接入，LinHoMo 不自研强大 Constructor
2. **Runtime 不信任 Constructor 的任何已验证声明**：bundle 内 execution_result/fidelity/validation 一律丢弃，代码由 Runtime 复跑
3. **ExecutionResult 仅由机械 subprocess 写入**：registry.create("execution_result") 必须携带 adapter 签发的不可伪造字段
4. **零执行 ≠ PASS，零验证 ≠ PASS**：model_execution 无代码 → blocked；model_validation 无 spec → blocked
5. **Validation PASS 仅由 Validator 写入**：mark_validated 增加调用方白名单 + 验证器运行记录要求
6. **Revision 是主 DAG 节点**：model_validation FAIL → diagnose → revision_draft → new_model_version → re-execution
7. **Fidelity 是主路径门**：code_generation 后自动跑 fidelity，misaligned → FAIL
8. **Engine validators 必须挂载**：session 构造 engine 时传入 validators，catalog 声明的 gate 真实执行
9. **The Agent Is Not The State**：状态仅由 filesystem/artifact/hash/validator 推进
10. **infra 不冒充 capability**：每个新模块必须回答"它改变了哪个可测量的 Model Construction 行为"

### 2.3 状态机（最终）

```
Constructor 输出 ConstructionBundle（声明级，trust=not_verified）
    │
    ▼
MODEL_IR schema 校验 ──fail──▶ C0 降级（保留 raw_output，标记 unresolved）
    │ pass
    ▼
Code 注册（sha256）→ Fidelity 检查 ──misaligned──▶ FAIL → Revision
    │ aligned
    ▼
ExecutionAdapter（subprocess）→ ExecutionResult（机械，带 provenance）
    │
    ▼
Mechanical Validation（run_checks，VR artifact）
    ├── pass → model status = validated
    ├── fail → Failure Diagnosis → Revision Proposal（Agent）
    │         → New Model Version（supersede 旧）→ Re-execution
    └── no spec → blocked（非 PASS）
    │
    ▼
Evidence Graph 写入（executed_by / verified_by / supports / revision_of）
    │
    ▼
Evidence Gate（E1-E9，要求 VR 存在 + exec_ref + 非占位）
    │
    ▼
Final Model State（validated / published / superseded / invalidated）
```

### 2.4 模块边界最终划分

| 层 | 模块 | 职责 | Owner |
|---|---|---|---|
| Constructor | `core/runtime/constructors/` | 外部 Agent 适配，输出 ConstructionBundle | External |
| Runtime-Execution | `core/runtime/execution/` | subprocess 执行、ExecutionResult、Fidelity、Replay | Harness（机械） |
| Runtime-Evidence | `core/runtime/graph/` + `artifacts/` | Evidence Graph、Registry、lifecycle | Harness（机械） |
| Runtime-Modeling | `core/runtime/modeling/` | MODEL_IR 校验、selection、revision、diagnosis | Harness（机械）+ Agent（revision proposal） |
| Runtime-State | `core/runtime/state/` | 状态投影、reconcile | Harness（机械） |
| Runtime-Knowledge | `core/runtime/knowledge/` + `core/knowledge/` | 方法卡检索、知识供给 | Harness（机械） |
| Guardrails | `core/validators/` + `core/tools/validate.py` | 项目级校验、evidence gate、quality | Validator（机械） |
| Projection | `core/runtime/writing/`（精简） | 论文投影（非核心） | Harness |
| Evaluation | `benchmark/` + `research/P15/` | Constructor-independent benchmark | Research |
| Legacy | `core/legacy/hands/` | V2 兼容（只读，冻结） | — |

---

## 3. 从 As-Is 到 To-Be 的关键变更

### 3.1 必须新增

| 变更 | 文件 | 理由 |
|---|---|---|
| Constructor Protocol 层 | `core/runtime/constructors/{protocol,adapter,registry}.py` + `adapters/` | 外部 Agent 接入的唯一通道 |
| ExecutionResult 来源鉴别 | `core/runtime/artifacts/artifact.py` + `registry.py` | EXEC 必须携带 adapter 签发字段，防伪造 |
| Revision DAG 节点 | `catalog/v3.yaml` + `handlers.py` | diagnosis/revision 接入主路径 |
| Fidelity DAG 节点 | `catalog/v3.yaml` + `handlers.py` | code_generation 后自动 fidelity 检查 |
| Engine validators 挂载 | `core/runtime/execution/session.py` + `wave_executor.py` | 6 个声明 gate 真实执行 |
| mark_validated 门禁 | `core/runtime/artifacts/registry.py` | 调用方白名单 + 验证器运行记录 |
| L6 数值判定层 | `core/runtime/execution/validation.py` 扩展 | GT 数值断言机械比对 |
| Constructor-independent benchmark | `research/P15/benchmark/constructor_independent/` | 2×2 析因实验框架 |

### 3.2 必须修改

| 变更 | 文件 | 当前问题 | 修复 |
|---|---|---|---|
| orchestrator 注入通道 | `core/tools/orchestrator.py:322-326,391` | 从不传 external_*/adapter/specs | 支持从项目目录加载 Constructor 产物 |
| 零执行=PASS | `handlers.py:753` | 0 个模型执行也 PASS | 无代码 → blocked |
| 零验证=PASS | `handlers.py:776-781` | 无 spec → 0/0 PASS | 无 spec → blocked |
| E9 不要求 VR | `evidence_gate.py:208-215` | 有执行无验证的 claim 可通过 | E9 增加 VR 存在性要求 |
| selection recs[0] | `selection.py:80` | evidence 存在仍取第一 | evidence 参与排序，或明确声明"检索排序选型" |
| K003 残余直写 | `k003_formal_runner.py:829` | 绕过 execution_writer | 删除 fallback，改写 error log |
| critic SKILL mark_validated | `core/skills/critics/*/SKILL.md:63,52` | Agent 直接写 validation PASS | 改为"提交 review report，由 runtime 登记" |
| V2 路径损坏 | `orchestrator.py:58-59` | _skill_path 指向不存在路径 | 修正为 core/legacy/hands/ 或废弃 --legacy |
| model_ir schema 双副本 | `research/P15/model_representation/model_ir.schema.json` | 与 core/schemas/v3 漂移 | research 侧改为引用 core |
| AGENTS.md 数字过期 | `AGENTS.md` | 57/758 vs 实测 58/989 | 更新 |

### 3.3 必须删除/冻结

| 模块 | 处置 | 理由 |
|---|---|---|
| `core/validators/modules/` 20 个死模块 | 删除 | 全仓 0 导入 |
| `core/runtime/writing/` 6 个仅测试模块 | 删除 | paragraphs/fact_check/patterns/expression/redundancy/narrative_critic |
| `core/runtime/domain/` | 删除 | DEAD EVERYWHERE |
| `core/runtime/adapters/`（注意：不是 execution/adapters.py） | 删除 | 仅 openai.yaml，DEAD EVERYWHERE |
| `core/runtime/contracts.py` | 合并入 runtime 或删除 | 仅测试引用 |
| `core/tools/` 6 个空壳子目录 | 删除 | devtools/friendly/rendering/validation/runtime/knowledge |
| `core/skills/syslab/` | 移出仓库 | 与 MathModel 无关的 MWORKS 技能包 |
| `core/schemas/` 顶层旧 12 个 schema | 归档删除 | 与 v3/ 双真源 |
| `bench_mmbench.py` 空壳 | 实现或删除 | accuracy 恒 0 |
| `_maybe_execute_experiment` | 删除 | handlers.py:1423，0 调用点 |
| legacy 29 agent | 冻结为只读参考 | V3 运行时零读取 |
| V3 roles 行为驱动 | 降级为元数据 | handler 不读 roles |

---

## 4. 最终目录结构（推荐）

```
MathModel/
├─ runtime/                      # Research Runtime（核心，机械，LLM-free）
│  ├─ constructors/              #   NEW: Constructor Protocol 层
│  │  ├─ protocol.py             #     ConstructorAdapter ABC + ConstructionBundle
│  │  ├─ adapter.py              #     BaseConstructorAdapter
│  │  ├─ registry.py             #     ConstructorRegistry
│  │  └─ adapters/               #     local / openai / claude / mathmodel_agent / pi
│  ├─ execution/                 #   substrate + handlers + engine + fidelity + replay
│  ├─ artifacts/                 #   Registry + lifecycle + ids
│  ├─ graph/                     #   Evidence Graph
│  ├─ state/                     #   状态投影 + reconcile
│  ├─ modeling/                  #   MODEL_IR / selection / revision / diagnosis
│  ├─ knowledge/                 #   检索代码（retriever / cards / intelligence）
│  └─ projection/                #   论文投影（精简：director/projection/findings/judge_critic）
├─ guardrails/                   # 验证层（Validator 唯一属主）
│  ├─ gates/                     #   evidence_gate / quality / engine validators
│  └─ schemas/                   #   v3 唯一真源
├─ brain/                        # Agent Brain（Agent 可写，研发主战场）
│  ├─ roles/                     #   元数据标签（不驱动行为）
│  ├─ skills/                    #   critic 技能（改为提交 report，不直接 mark_validated）
│  └─ knowledge/                 #   知识数据语料
├─ cli/                          # 薄壳命令（state/gate/validate/orchestrator/replay）
├─ benchmark/                    # 评分链 + Constructor-independent benchmark
│  ├─ arena/                     #   Candidate Arena（benchmark 工具）
│  └─ constructor_independent/   #   NEW: 2×2 析因实验框架
├─ projects/                     # 运行实例
├─ legacy/                       # V2 兼容（只读冻结）
├─ research/                     # 实验归档（禁止被 production 导入）
└─ tests/                        # 与 runtime/guardrails 一一对应
```

---

## 5. 架构不变量（写死，不可违反）

1. **core/runtime 永久 LLM-free**：不引入任何 LLM 执行器
2. **ExecutionResult 仅由 subprocess 基底写入**：Agent 不可直接写 EXEC
3. **Validation PASS 仅由 Validator 写入**：Agent 提交 review report，由 runtime 登记
4. **零执行 ≠ PASS，零验证 ≠ PASS**："没做"和"做了且通过"必须区分
5. **Evidence 边必须带 exec_ref**：claim 的 supports 边必须指向真实 ExecutionResult
6. **FROZEN 后不改冻结项**：改 = new revision，旧版作废
7. **状态单一真源**：status.json 由 artifact 重建，禁止多份状态文件
8. **经验常数禁入确定性评分**：BZD 的 6.81% 等必须打 provenance 标签且不进入 score_compute
9. **Constructor 可替换**：Runtime 不绑定任何特定 Constructor
10. **infra 不冒充 capability**：新模块必须回答"改变了哪个可测量行为"

---

*本架构基于 5 路独立审计的代码证据重构。所有 As-Is 判定附 file:line，见各审计子报告与 `MODEL_CONSTRUCTION_GAP.md`。*
