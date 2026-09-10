# ARCHITECTURE_FINAL — 最终架构设计

> 日期：2026-09-10 ｜ 状态：**ARCHITECTURE FROZEN**
> 基于 8 代理审计 + 三轮自我反驳 + 真实执行验证

---

## 1. 架构全景

```text
┌─────────────────────────────────────────────────────────────┐
│                    External Constructors                     │
│  (MathModelAgent / Claude Code / OpenAI Agent / Human)      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    Constructor Protocol
                    (MODEL_IR + Code + Intent + Mapping)
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   LinHoMo Runtime                            │
│                                                              │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Knowledge    │  │ MODEL_IR     │  │ Candidate Arena  │   │
│  │ Retriever    │  │ Builder      │  │ (evidence-based) │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                │                    │              │
│  ┌──────▼────────────────▼────────────────────▼──────────┐  │
│  │              WorkflowEngine (DAG Scheduler)             │  │
│  │  retry / feedback loop / blocked / partial rerun       │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────▼────────────────────────────┐  │
│  │              DefaultNodeExecutor                        │  │
│  │  15 nodes: problem_analysis → model_selection →        │  │
│  │  model_construction → code_generation →                │  │
│  │  model_execution → model_validation → evidence_build → │  │
│  │  evidence_gate → ...（paper_projection 已随 v3.2.2 删除）│
│  └──────────────────────────┬────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────▼────────────────────────────┐  │
│  │              Execution Substrate                        │  │
│  │  LocalPythonAdapter (subprocess, zero-dep)              │  │
│  │  → ExecutionResult (status only from returncode)        │  │
│  │  → E2B / Docker / Syslab (pluggable)                   │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────▼────────────────────────────┐  │
│  │              Fidelity Layer (L2)                        │  │
│  │  check_fidelity: MODEL_IR declarations ↔ code outputs  │  │
│  │  → output_key_exists / output_numeric / output_range   │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────▼────────────────────────────┐  │
│  │              Validation Layer                           │  │
│  │  run_numeric_validation: constraint/objective/domain    │  │
│  │  validate_execution: VR artifact + verified_by edge     │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────▼────────────────────────────┐  │
│  │              Evidence Graph                             │  │
│  │  supports / verified_by / executed_by / produced_by     │  │
│  │  → Evidence Gate (E1-E9)                                │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────▼────────────────────────────┐  │
│  │              Failure Diagnosis + Revision               │  │
│  │  diagnose_failure → build_revision_draft → re-execution │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────▼────────────────────────────┐  │
│  │              Artifact Registry                          │  │
│  │  lifecycle management + hash chain + schema validation  │  │
│  └──────────────────────────┬────────────────────────────┘  │
│                             │                                │
│  ┌──────────────────────────▼────────────────────────────┐  │
│  │              State Machine                              │  │
│  │  status.json (derived from Registry + Graph)            │  │
│  │  refresh_from() / reconcile()                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 2. 核心不变量

### INV-1: Agent Claim ≠ System Fact

只有机械 Runtime 能推进状态机。Agent 的文字输出是"输入"，不是"状态"。

### INV-2: Execution Status Only From Subprocess

`ExecutionResult.status` 只来自 `proc.returncode`。禁止 handler 默认生成
success，禁止 Agent 声称执行完成。

### INV-3: Evidence Not Written By Agent

Evidence relations 由 handler 在节点 PASS 后写入。Agent 不能直接写
`supports`/`verified_by` 边。

### INV-4: State Derived, Not Written

`status.json` 由 `refresh_from(registry, graph)` 派生。禁止手工编辑
或 Agent 直接写入。

### INV-5: Fidelity Is Structural, Not Semantic

Fidelity 检查是确定性的 output_key_exists/output_numeric/output_range。
不做"看起来像"的 LLM 判断。

### INV-6: Knowledge Constrains, Not Dictates

方法卡是 Constraint/Prior，不是答案库。LLM 可以提出 catalog 外的新模型。

### INV-7: No Provenance → No Score

经验常数必须标注来源。无 provenance 的数字不得进入确定性评分。

## 3. 数据流

### 3.1 正常流

```
External Constructor
  → MODEL_IR dict + code string + output_mapping
    → register_code (CODE artifact)
      → execute_code (EXEC artifact, status from subprocess)
        → check_fidelity (VR artifact, L2 fidelity)
          → run_numeric_validation (VR artifact, constraint/objective)
            → synthesize_claim (Claim artifact)
              → evidence_gate (E1-E9 mechanical checks)
                → model_status = validated (auto from supports edge)
```

### 3.2 失败流

```
execution failed / validation failed
  → diagnose_failure (FailureDiagnosis artifact)
    → build_revision_draft (Revision Draft, no new values)
      → External Constructor provides M2
        → supersede M1 (M1 status → superseded)
          → re-execute M2
            → compare_models (M1 vs M2, mechanical)
              → accept M2 or keep M1
```

### 3.3 Invalidation 流

```
Artifact invalidated
  → Graph propagation (fixed-point)
    → Engine reset (partial rerun)
      → Cross-question propagation (evidential only)
        → Rebuild from affected node
```

## 4. 架构边界

### 4.1 Runtime 与 Constructor 的边界

```
Runtime 管:
  - 产物注册 (ArtifactRegistry)
  - 执行调度 (WorkflowEngine)
  - 真实执行 (ExecutionAdapter)
  - Fidelity 校验 (check_fidelity)
  - 验证 (run_numeric_validation)
  - 证据管理 (EvidenceGraph)
  - 状态机 (ProjectState)
  - 重放 (replay)
  - 对账 (reconcile)

Constructor 管:
  - 问题理解 (Problem Interpretation)
  - 模型构造 (Model Construction)
  - 代码生成 (Code Generation)
  - 实验设计 (Experiment Design)
  - 修订建议 (Revision Proposal)
```

### 4.2 Runtime 与 Evaluation 的边界

```
Runtime 管:
  - 执行 + 验证 + 证据 + 状态

Evaluation 管:
  - 盲评 (Blind Evaluation)
  - Benchmark (八项指标)
  - Rubric (评分标准)
  - 评审 (Review)
```

### 4.3 Knowledge 的边界

```
Knowledge 管:
  - 方法卡 (Constraint/Prior)
  - 失败记忆 (Failure Memory)
  - 创新模式 (Innovation Patterns)
  - 竞赛情报 (Competition Intelligence)

Knowledge 不管:
  - 模型构造 (由 Constructor 做)
  - 执行 (由 Runtime 做)
  - 判定 (由 Validator 做)
```

## 5. 最终目录结构

```
MathModel/
├── core/
│   ├── env/                    # 配置 + loader
│   ├── runtime/                # V3 认知工作流引擎
│   │   ├── artifacts/          # Artifact Registry
│   │   ├── execution/          # Execution Substrate + Fidelity + Validation
│   │   ├── graph/              # Evidence Graph
│   │   ├── modeling/           # MODEL_IR + Candidates + Selection + Diagnosis + Revision
│   │   ├── knowledge/          # Knowledge Retriever + Cards + Packs
│   │   ├── state/              # State Machine + Reconcile + Runs
│   │   ├── decisions/          # Decision Log
│   │   ├── writing/            # Paper Projection
│   │   ├── synthesis/          # Cross-question Context
│   │   ├── constructors/       # 【NEW】Constructor Adapter Protocol
│   │   └── roles.py            # V3 Role Definitions
│   ├── roles/                  # V3 Role YAMLs
│   ├── workflows/              # DAG Definitions
│   ├── validators/             # Evidence Gate + Quality Validators
│   ├── knowledge/              # Method Cards + Failure Memory + Patterns
│   ├── schemas/                # JSON Schemas (consolidated)
│   ├── skills/                 # Critics + Syslab
│   ├── templates/              # （LaTeX 模板已随 v3.2.2 删除）
│   ├── tools/                  # CLI Tools (cleaned)
│   ├── legacy/                 # V2 Compatibility (frozen)
│   └── evaluation/             # Scoring + Benchmark (fixed ghost dirs)
├── tests/                      # 96 test files
├── projects/                   # Project instances
├── research/                   # Experiments (reorganized)
├── docs/
│   ├── architecture/           # Active contracts only (pruned)
│   ├── decisions/              # ADRs
│   └── integration/            # Compatibility docs
├── catalog.yaml                # Single source of truth
└── pyproject.toml              # Minimal, zero-dep
```

## 6. Constructor Protocol（新增）

```python
# core/runtime/constructors/protocol.py

@dataclass
class ConstructionBundle:
    """External Constructor → LinHoMo Runtime 的标准输出。"""
    problem_interpretation: dict       # 问题理解
    model_candidates: list[dict]       # 候选模型列表
    selected_model: str                # 选中模型 ID
    model_ir: dict                     # MODEL_IR JSON
    code: str                          # 可执行代码
    output_mapping: dict               # 声明名 → 代码输出 key
    experiment_plan: dict              # 实验计划
    reasoning_metadata: dict           # 推理元数据（可选）
    revision_request: dict | None      # 修订请求（revision 时）

class ConstructorAdapter(ABC):
    """External Constructor 统一接口。"""

    @abstractmethod
    def construct(self, problem, context) -> ConstructionBundle:
        """从问题构造模型。"""

    @abstractmethod
    def revise(self, diagnosis, context) -> ConstructionBundle:
        """基于失败诊断修订模型。"""
```

### Capability Levels

```
C0 = text only (free-form model description)
C1 = model description (structured but not MACHINE-readable)
C2 = MODEL_IR (structured, schema-validated)
C3 = MODEL_IR + code (executable)
C4 = MODEL_IR + code + output_mapping (fidelity-verifiable)
C5 = revision-capable (can consume diagnosis → produce M2)
```

LinHoMo Runtime 至少需要 C4 才能执行完整闭环。
C5 是可选的（支持自动 revision）。

## 7. 模块状态清单

| 模块 | 状态 | 行动 |
|---|---|---|
| Artifact Registry | REAL, PRODUCTION | 冻结 |
| Evidence Graph | REAL, PRODUCTION | 冻结 |
| WorkflowEngine | REAL, PRODUCTION | 冻结（修复 unblock 重复定义）|
| WaveExecutor | REAL, PRODUCTION | 冻结 |
| ProjectState | REAL, PRODUCTION | 冻结 |
| LocalPythonAdapter | REAL, PRODUCTION | 冻结 |
| DefaultNodeExecutor | REAL, PRODUCTION | 重构（接入 fidelity + 4 dead modules）|
| RuntimeSession | REAL, PRODUCTION | 冻结（启用 engine validators）|
| MODEL_IR Builder | REAL, PRODUCTION | 冻结 |
| Candidate Arena | REAL, PRODUCTION | 冻结 |
| Method Arena | REAL, PRODUCTION | 冻结 |
| Experiment Planner | REAL, PRODUCTION | 冻结 |
| Replay | REAL, RESEARCH | 保留 |
| Fidelity | REAL, NOT INTEGRATED | **接入生产 DAG** |
| Knowledge Guided | REAL, NOT INTEGRATED | **接入 production** |
| Failure Diagnosis | REAL, NOT INTEGRATED | **接入 revision flow** |
| Model Comparison | REAL, NOT INTEGRATED | **接入 model selection** |
| Revision Draft | REAL, NOT INTEGRATED | **接入 revision flow** |
| claim_synthesis | REAL, PRODUCTION | 冻结 |
| Engine Validators | WIRED, NOT USED | **启用或删除** |
| `_maybe_execute_experiment` | DEAD | **删除** |
| `codegen.py` standalone | DUPLICATE | **统一到 handlers** |


---

## 附录：引用文件路径映射（审计可追溯性）

本文档中的模块引用使用简写（handlers.py:837 表示 837 行）。完整真实路径如下（已逐行核对）：

| 简写 | 真实路径 | 核对结果 |
|---|---|---|
| handlers.py | core/runtime/execution/handlers.py（1737 行） | L817/837/843/876/1423 全部吻合 |
| engine.py | core/runtime/execution/engine.py（417 行） | L96/281/349 吻合（L281/L349 重复 unblock 属实） |
| session.py | core/runtime/execution/session.py（298 行） | L96 吻合 |
| idelity.py | core/runtime/execution/fidelity.py（227 行） | 存在 |
| codegen.py | core/runtime/execution/codegen.py | 存在 |
| integrity_gate.py | core/validators/modules/integrity_gate.py（428 行） | L118/161/172/255/345 全部吻合 |
| indings.py | core/runtime/writing/findings.py（212 行） | L121/147/157 吻合 |
| selection.py | core/runtime/modeling/selection.py（141 行） | L60/80/108/120 吻合（chosen=recs[0] 属实） |
| comparison.py | core/runtime/modeling/comparison.py | L22 吻合 |
| knowledge_guided.py / diagnosis.py / 
evision.py / candidates.py / model_ir.py | core/runtime/modeling/ | 存在（生产零调用见正文） |
