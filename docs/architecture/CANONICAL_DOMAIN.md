# Canonical Domain Model —— 概念与 Schema 的唯一真源

> 建立：2026-09-07（System Hardening P1 / Contract Freeze）
> 代码真源：`core/runtime/domain/__init__.py`（纯定义层，零行为）
> 规则：**一个概念 = 一个 canonical 名 = 一个 schema 归属；任何新增 schema / 字段 /
> 文件不得发明 canonical 之外的近义词。** 本文件是语义归户的权威文档。

## 1. 要解决的问题

历史上同一个概念存在多套定义并存，是未来接科研项目后 Semantic Drift 的源头。
典型三类（Hardening P0 审计确认）：

| 概念 | 曾并存的称呼（废止） | Canonical |
|---|---|---|
| 模型 | `MODEL_SPEC.md` / `MODEL_ARTIFACT` / V3 Model Artifact / `ResearchState.models` / model_output / formal_model | **Model** |
| 论文 | `PAPER_SPEC` / Paper Projection / `paper/main.pdf` / Writer output | **PaperProjection** |
| 证据 | Evidence Graph / experiment result / validator report | **Evidence** |

## 2. 12 个规范实体与 Schema 归户

| Canonical 实体 | v3 subtype（artifact type enum） | canonical schema 归属 | legacy 投影（只读兼容） |
|---|---|---|---|
| Problem | problem | 无独立 schema（inputs/ 原始题面为真源） | `question_spec.schema.json` |
| Question | question | 无独立 schema（DAG per_question + Research State questions 维度） | `question_spec.schema.json`、V2 `q_states` |
| Model | model | M artifact；内容在 payload 文件 | `model_spec.schema.json`、`model_artifact.schema.json`、`model_dag.schema.json`、`MODEL_SPEC.md` |
| Artifact | —（统一契约本体，15 子类型） | `v3/artifact/artifact.schema.json` + `registry.schema.json` | V2 各契约文件 |
| Experiment | experiment | E artifact | `code_deliverables.schema.json`、`CODE_DELIVERABLES.md` |
| Result | result | R artifact | `figures/all_results.json`（legacy 数值出口） |
| Evidence | —（graph 为主体） | `v3/evidence/graph.schema.json` | `literature_evidence.schema.json` |
| Claim | claim | C artifact（P10 Finding Graph 前身研究） | 无 |
| Decision | decision | `v3/decision/decision.schema.json` | `decision_log.schema.json`（已升级扩展） |
| PaperProjection | deliverable（+ narrative / paper_section） | deliverable artifact | `paper_spec.schema.json`、`PAPER_SPEC.md`、`paper/main.tex/pdf` |
| Failure | —（知识层，非 artifact） | `v3/knowledge/failure.schema.json` | `pitfalls/` + `_negative/` markdown |
| Run | —（运行记录层，P3 创建） | `v3/run/run_record.schema.json`（预注册） | `reproducibility.schema.json`、`state/status.json` 的 run 段 |

### 2.1 全部 V2 schema 归户登记（15 个逐一闭合）

不在 12 实体主映射中的 6 个 V2 schema 归户如下：

| V2 schema | 归属 | 说明 |
|---|---|---|
| `bench_result.schema.json` | evaluation 层 | 评测资产，非 domain 实体；能力测量口径见 BASELINE_REPORT |
| `bench_rubric.schema.json` | evaluation 层 | 同上（评委 rubric） |
| `checkpoint.schema.json` | Run（legacy 会话快照） | session checkpoint 的 legacy 视图，P2 后由事件投影取代 |
| `citation.schema.json` | PaperProjection（子结构） | 论文投影的引用子结构，validators/paper 消费 |
| `model_paper_map.schema.json` | Model → PaperProjection 传输映射 | P13-3D 传输研究的映射表；canonical 视角是 M→deliverable 的 appears_in 边投影 |
| `score_card.schema.json` | evaluation 层 | 五维评分链输出 |

## 3. 视图规则

- **Canonical 视图**：`core/schemas/v3/`（artifact / decision / evidence / knowledge /
  state / workflow 六域 + P3 新增 run 域）。新增 runtime 功能一律落此层。
- **Legacy 视图**：`core/schemas/*.json` 15 个 V2 schema，全部冻结只读，仅作为 V2
  兼容层的校验器使用；任何新代码不得把新语义写进这些 schema。
- **状态视图**：`v3/state/status.schema.json` 明确声明自身是「派生视图，不存储研究
  内容」——流程状态投影（见 STATE_TRUTH.md），不是新的内容真源。
- **投影规则**：Artifact 是真源，Evidence / Experiment / Paper / Evaluation 都是投影；
  投影只能从 Registry / Graph / 事件重建，禁止反向手写（同 STATE_TRUTH 的单一真源语义）。

## 4. 命名禁令与执行

1. 任何新增 schema / 字段 / 文件名必须先查 `core/runtime/domain/__init__.py` 的
   `CANONICAL_ENTITIES` 与 `ENTIT_ALIASES`（同义词回收表）；命中旧称呼即违规。
2. V2/legacy 文档中历史称呼保留不改（证据不改写原则），但在新文档中必须用 canonical 名。
3. 执行方式：文档规约 + 评审抽查（Hardening P5 回归测试含命名抽查用例）；
   `catalog_check.py` 行为不变。

## 5. 变更流程

实体增删或 schema 归属变更 = 架构级变更：须更新本文件 + `core/runtime/domain/__init__.py`
+ `THREE_LAYER_ARCHITECTURE.md` 例外登记，三条缺一不可提交。