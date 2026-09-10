# core/runtime — V3 Runtime 子域导航

> 语义契约真源：`docs/architecture/RUNTIME_CONTRACTS.md`（与 `core/runtime/contracts.py` 代码真源对齐）。
> 状态真源：`docs/architecture/STATE_TRUTH.md`；本目录按子域组织，各子域职责如下。

## 子域 / Subdomains

| 子域 | 职责 | 入口文件 |
|---|---|---|
| `artifacts/` | 内容对象：稳定 ID + 生命周期 + 注册表（Artifact Registry） | `artifact.py` / `ids.py` / `lifecycle.py` / `registry.py` |
| `state/` | 派生状态：依赖、关系、对账（reconcile 是唯一写入口） | `reconcile.py` / `model.py` / `relations.py` |
| `graph/` | Evidence Graph：节点/边/失效传播 | `evidence_graph.py` |
| `execution/` | 执行引擎：适配器、代码生成、组合器 | `composer.py` / `codegen.py` / `claim_synthesis.py` |
| `modeling/` | 建模工作流节点：候选、比较、诊断、知识引导 | `candidates.py` / `comparison.py` / `knowledge_guided.py` |
| `knowledge/` | 知识服务：方法卡、情报、知识包、检索 | `cards.py` / `retriever.py` / `packs.py` |
| `constructors/` | 外部 Constructor 协议与注册 | `protocol.py` / `registry.py` |
| `adapters/` | 运行时入口适配（含 gen_runtime_manifest 生成物） | `__init__.py` |
| `decisions/` | 决策日志（decision log） | `log.py` |
| `domain/` | 纯定义层：canonical 概念（零行为） | `__init__.py` |
| `evaluation/` | 确定性度量 | `deterministic_metrics.py` |
| `synthesis/` | 合成上下文（expression 层输入） | `context.py` |

## 边界

- `core/runtime/` 业务逻辑**冻结**（ADR-0001）：普通任务不得修改，改动须经契约授权。
- 状态只由确定性机制推进（ADR-0003）：Agent / LLM 只是 Executor。
