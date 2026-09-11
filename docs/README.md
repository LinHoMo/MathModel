# Documentation Index / 文档索引

> 本文档是 `docs/` 目录的唯一入口索引。所有 Agent 与读者从这里进入对应文档。
> 必读顺序见根 `AGENTS.md` §1。

## 必读入口 / Mandatory Entry Points

| 文档 | 角色 |
|---|---|
| [STATUS.md](STATUS.md) | **状态真源**：所有数字的唯一出处（机器实测 + commit 绑定） |
| [architecture/V3.1_ARCHITECTURE.md](architecture/V3.1_ARCHITECTURE.md) | **架构真源**：V3 认知工作流运行时的概念定义与边界 |
| [ONTOLOGY_TERMINOLOGY.md](ONTOLOGY_TERMINOLOGY.md) | **术语真源**：全仓术语唯一权威定义（Freeze v1.0） |
| [../AGENTS.md](../AGENTS.md) | **工作协议**：Agent 角色、工作流、禁止事项、验收标准 |

## 架构文档清单 / Architecture Docs（docs/architecture/）

| 文档 | 一句话说明 |
|---|---|
| [V3.1_ARCHITECTURE.md](architecture/V3.1_ARCHITECTURE.md) | V3.1 认知工作流运行时架构（18 概念问题 + 目录决策 + 实施门） |
| [ARCHITECTURE_FINAL.md](architecture/ARCHITECTURE_FINAL.md) | 最终架构设计（8 代理审计 + 三轮自我反驳后冻结） |
| [STRATEGIC_VERDICT.md](architecture/STRATEGIC_VERDICT.md) | 最终架构与战略审查裁决（Constructor-Independent Runtime-First） |
| [CANONICAL_DOMAIN.md](architecture/CANONICAL_DOMAIN.md) | 概念与 Schema 的唯一真源（一个概念 = 一个 canonical 名） |
| [AGENT_AUTHORITY_MODEL.md](architecture/AGENT_AUTHORITY_MODEL.md) | Agent 权限矩阵（Agent Claim ≠ System Fact） |
| [ROADMAP.md](architecture/ROADMAP.md) | 最终执行路线图（P0–P3 收口记录） |
| [RUNTIME_CONTRACTS.md](architecture/RUNTIME_CONTRACTS.md) | V3 Runtime 语义契约真源（P7 冻结，与 contracts.py 对齐） |
| [STATE_TRUTH.md](architecture/STATE_TRUTH.md) | 状态单一真源决策表（Hardening P2，reconcile 对账） |
| [RUN_PROVENANCE.md](architecture/RUN_PROVENANCE.md) | 运行溯源与确定性重放（Hardening P3，replay 引擎） |
| [MODELING_KNOWLEDGE_GOVERNANCE.md](architecture/MODELING_KNOWLEDGE_GOVERNANCE.md) | Modeling Knowledge 治理规范（方法卡 = Constraint/Prior/Validation） |
| MODEL_CONSTRUCTION_GAP.md | 模型构造差距分析（ANALYSIS COMPLETE） |
| MODEL_QUALITY_CRITERIA.md | 模型质量判据（FROZEN：合格线 G1–G3 Gate + 排序线 R1–R2 Rank） |
| [CONSTRUCTOR_INTEGRATION_PLAN.md](architecture/CONSTRUCTOR_INTEGRATION_PLAN.md) | 外部 Constructor 集成方案（DESIGN FROZEN） |
| [EXPERIMENT_STRATEGY.md](architecture/EXPERIMENT_STRATEGY.md) | 实验策略（DESIGN FROZEN） |
| [EXPRESSION_CONTRACT.md](architecture/EXPRESSION_CONTRACT.md) | 表达层契约（P11 冻结，expression.py 代码真源） |

## 决策记录 / Decision Records（docs/decisions/）

| 文档 | 说明 |
|---|---|
| [decisions/README.md](decisions/README.md) | ADR 索引与使用说明 |
| [decisions/ADR-0001-architecture-freeze.md](decisions/ADR-0001-architecture-freeze.md) | 架构冻结（V3.1） |
| [decisions/ADR-0002-llm-free-core.md](decisions/ADR-0002-llm-free-core.md) | core LLM-free |
| [decisions/ADR-0003-artifact-registry-as-truth.md](decisions/ADR-0003-artifact-registry-as-truth.md) | Artifact Registry 作为真源 |
| [decisions/ADR-0004-no-third-party-deps.md](decisions/ADR-0004-no-third-party-deps.md) | 运行时零依赖（区分测试依赖） |
| [decisions/ADR-0005-v3-no-backward-compat.md](decisions/ADR-0005-v3-no-backward-compat.md) | V3 不向后兼容 V2 |

## 研究与基线 / Research & Baseline

| 文档 | 说明 |
|---|---|
| [../research/P15/README.md](../research/P15/README.md) | P15 实验入口（K 系列状态、实验地图、报告索引、铁律） |
| [../research/README.md](../research/README.md) | 研究目录总览（ENGINEERING / P15） |

## 顶层文档 / Top-Level Docs

| 文档 | 说明 |
|---|---|
| ARCHITECTURE.md | 现行 V3 架构总览（问题输入 → MODEL_IR + 模型描述文档） |
| diagrams/ | **架构图生成物**（`mh diagram repo` 从 catalog 确定性渲染；勿手改） |
| [BENCHMARK.md](BENCHMARK.md) | 国赛复盘基准（CUMCM Bench）设计 |
| [METRICS.md](METRICS.md) | 项目度量单一真源（由 `src/modeling_harness/cli/metrics.py --write` 自动生成） |
| [HANDOFF.md](HANDOFF.md) | 跨题交接：四件套门禁口径、本轮修复清单、优化 backlog（给下一个 Agent） |
| [PROJECTS_FEEDBACK_AUDIT.md](PROJECTS_FEEDBACK_AUDIT.md) | 实例反馈审计与闭环：三实例缺陷清单 + harness 侧修复 + 实测对照 + 未闭合项 |
| [THEORY_FOUNDATION_REVIEW.md](THEORY_FOUNDATION_REVIEW.md) | 理论基座缺口审查与优化方案（REVIEW：10 维度分析 + 创新空间/合成真值/预测探针提案） |
| [STATUS.md](STATUS.md) | 项目状态与机器实测数字（状态真源） |
| [ONTOLOGY_TERMINOLOGY.md](ONTOLOGY_TERMINOLOGY.md) | 术语与本体权威定义 |
| [../CHANGELOG.md](../CHANGELOG.md) | 版本变更日志 |
| [../README.md](../README.md) | 仓库总览 |

## 约定

- `docs/` 是唯一文档区；新增文档先在本索引登记，避免孤儿文档。
- 决策记录统一走 `docs/decisions/ADR-xxxx`（模板 `ADR-TEMPLATE.md`）。
- 历史归档文档（如有）放 `docs/` 子目录并在此登记为「历史」。
