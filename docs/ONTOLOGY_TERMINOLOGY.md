# ONTOLOGY & TERMINOLOGY — 知识体系术语与本体权威定义（Freeze v1.0）

> 生效日期：2026-09-08 ｜ 状态：**FREEZE**（术语变更需走 RFC）
> 核心命题：**The LLM constructs models. Knowledge constrains and informs construction. Evidence decides whether the construction survives.**
> 本文件是全仓库术语的单一权威来源（single source of truth for vocabulary）。

---

## 1. 三层知识体系（Ontology）

```
Modeling Ontology           — 世界中有哪些可建模结构？What structure is?
        │ identifies structure
        ▼
Model Construction Knowledge — 从这种结构如何构造数学模型？How can it be modeled?
        │ guides construction
        ▼
Case / Experience           — 过去真实问题是怎么使用这种结构的？How was it instantiated?
        │ demonstrates prior instantiation
        ▼
Current Model → Experiment → Evidence → Validation → survive / reject
```

### Layer 1：Modeling Ontology（建模本体）

回答"世界中有哪些可建模结构"。描述的是 **problem structure / mathematical regime**，不是算法。

示例结构（非穷举）：

| structure_id | 中文 | 示例题 |
|---|---|---|
| discrete_sequential_decision | 离散序贯决策 | 2020_B |
| continuous_field | 连续时空场 | 2018_A |
| stochastic_service_system | 随机服务系统 | 2019_C |
| geometric_motion | 几何运动 | 2024_A |
| network_interaction | 网络交互 | — |
| resource_allocation | 资源分配 | — |

### Layer 2：Model Construction Knowledge（模型构造知识）

回答"从这种结构如何构造数学模型"。结构 → state/decision/transition/objective/constraints → 数学表述 → 计算策略。

承载物：**Model Construction Knowledge Unit**（下称 Knowledge Unit，标识 `mck-*`），即原"方法卡"的正式语义。

### Layer 3：Case / Experience（案例/经验）

回答"过去真实问题怎么实例化这种结构"。是 **Knowledge Unit 在具体问题上的实例化证据**，不是知识本身，更不是 gold standard。

---

## 2. Canonical Terms（权威术语表）

以下为本仓库唯一允许的规范术语。旧术语仅在 research history / migration 文档中允许出现。

| # | Canonical Term | 中文 | 定义 | 旧说法（deprecated） |
|---|---|---|---|---|
| 1 | **Model Construction Knowledge Unit**（`mck-*`） | 模型构造知识单元 | 面向"现实问题→数学模型"的建模知识：机理、结构、适用条件、构造模式、验证、失败记忆。不是算法说明书 | Method Card / algorithm card |
| 2 | **Model Construction Knowledge Base** | 模型构造知识库 | Knowledge Unit 的集合 | method card library |
| 3 | **Modeling Structure / Model Regime** | 建模结构 / 模型范式 | 问题在数学上的结构类别（Layer 1 结构） | method family / method type |
| 4 | **Model Construction Strategy Selection** | 模型构造策略选择 | Agent 识别问题结构并选择构造策略的过程。**不是"从算法目录里选一个方法"** | method selection |
| 5 | **Solver / Computational Strategy Selection** | 求解器 / 计算策略选择 | 在已构造模型下选择计算手段（子环节，不是能力主指标） | algorithm selection |
| 6 | **allowed_modeling_structures** | 允许的建模结构 | benchmark 中该题允许的 modeling structure 列表（评分依据，多解原则） | allowed_model_families |
| 7 | **Structure Coverage** | 结构覆盖 | 覆盖了多少建模结构族（知识体系 KPI，不是算法数量） | method coverage |
| 8 | **Construction Appropriateness** | 构造恰当性 | 模型构造是否匹配问题结构（正确性问题） | method correctness |
| 9 | **Structure Alignment** | 结构对齐 | Agent 识别的问题结构是否与题目的 gold structure 对齐 | method match |
| 10 | **Construction Guidance** | 构造引导 | Knowledge Unit 对构造的引导作用（检索输出，非强制） | method recommendation |
| 11 | **Construction Failure / Applicability Failure** | 构造失败 / 适用性失败 | 建模失败模式：结构误判、约束遗漏、机理错误等 | method failure |
| 12 | **Modeling Knowledge** | 建模知识 | Layer 2 知识的总称 | method knowledge |
| 13 | **Case / Instantiated Modeling Case** | 案例 / 实例化建模案例 | 知识在真实问题上的实例化证据 | paper case |
| 14 | **Failure Memory** | 失败记忆 | 可复用的失败模式（定义/检测/避免） | method failure memory |

### 删除词汇（禁止在任何新产出中出现）

- `algorithm_card` — 不存在该概念
- `reference_method` — 参考方法匹配评分（已废弃）
- `core_methods` — 唯一答案方法（已废弃；历史数据仅以 `historical_core_methods` 追溯）
- `method_selection`（作为能力主指标语义）— 诱导"题目→选方法→套方法"

### 允许保留的兼容标识符（仅限代码运行时契约，须注释标注 legacy）

- e2e_metrics 输出 JSON 键 `method_selection`（历史 e2e_metrics_report.json 兼容）
- manifest node_id `method_selection`（B0 历史 manifest 数据契约）
- 方法卡 YAML `family` 字段名（中性词；语义 = Modeling Structure）
- 目录 `core/knowledge/methods/cards/`（路径契约，语义 = Knowledge Unit 库）

---

## 3. 术语分层规则（Zero-residue Gate）

| 区域 | 旧术语允许？ | 说明 |
|---|---|---|
| **production**（`core/`、`AGENTS.md`、`docs/architecture/` 现行文档、`docs/ONTOLOGY_TERMINOLOGY.md`） | ❌ 零残留 | schema / benchmark / evaluator / governance / CLI 必须用 canonical terms |
| **research history**（`research/` 已产出报告、`projects/*-b0/` 历史观测、`b0_manifests/`、`runs/`） | ✅ 允许 | 历史数据与观测记录不可改写（可追溯性优先） |
| **migration / history 文档**（本文件、MODELING_KNOWLEDGE_GOVERNANCE 历史更正记录、docs/decisions） | ✅ 允许 | 新旧映射本身需要旧词 |
| **代码运行时兼容层** | ✅ 允许（须注释 `# legacy compat`） | 读取历史 manifest / report 的键名 |

门禁命令：

```powershell
py -3.12 core/tools/catalog_check.py --check-terminology
```

扫描范围 = production；失败即不通过交付门禁。research / history / migration 排除。

---

## 4. 语义映射：旧概念 → 新概念

| 旧概念（危险语义） | 新概念（正确语义） |
|---|---|
| 题目 → 分类 → 选方法卡 → 套模型 | 题目 → 识别 problem structure → 建模结构假设 → LLM 构造模型 → 数学表述 → 计算策略 → 实验 → 证据 |
| "这道题允许哪些方法" | "这道题的 gold structure 是什么"（多解：primary / secondary） |
| 检索命中 → 必须使用 | 检索 → LLM 评估适用性 → USE / ADAPT / REJECT |
| 覆盖了多少算法 | 覆盖了多少建模结构 + 每结构的构造知识质量 |
| 方法正确性 | 构造恰当性（structure alignment + math correctness + constraint completeness） |

---

## 5. Knowledge Unit 结构（mck-* 最小知识维度）

每个 Knowledge Unit 应能表达：

1. mechanism — 现实机制（为什么这种结构成立）
2. structure — 结构识别条件（什么信号表明该结构存在）
3. assumptions — 假设
4. math object — 数学对象（state/decision/transition/objective/constraints）
5. formulation — 数学表述
6. construction pattern — 构造模式
7. solver / computational strategy — 计算策略
8. validation — 验证方式
9. failure modes — 失败模式（链接 Failure Memory）
10. composition — 可组合结构

> 现阶段文件格式仍为 `core/knowledge/methods/cards/mc-*.yaml`（路径契约），
> 但语义上它们是 Model Construction Knowledge Unit；后续如有 RFC 批准，可迁移为 `mck-*` 命名。

---

## 6. KPI：结构覆盖（替代"算法覆盖率"）

| 指标 | 含义 |
|---|---|
| Structure Coverage | 覆盖多少建模结构族（Layer 1） |
| Construction Coverage | 每结构是否有足够构造知识（variables/params/constraints/objective/dynamics/boundary/assumptions） |
| Applicability Precision | 会不会乱用（能识别"结构不匹配"而拒绝） |
| Validation Utility | 知识是否真正帮助构造→实验→验证→失败诊断 |

结构覆盖表（目标形态）：

| Structure | Knowledge Unit | Validation | Cases |
|---|---|---|---|
| discrete_sequential_decision | ✅ mck | ✅ | 2020_B |
| continuous_field | ✅ mck | ✅ | 2018_A |
| stochastic_service_system | ✅ mck | ✅ | 2019_C |
| geometric_motion | 🟡 | ❌ | 2024_A |
| network_interaction | 🟡 | ❌ | — |
| resource_allocation | 🟡 | ❌ | — |

---

## 7. 与既有文档的关系

- `docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md` — 治理规范（引用本文件的 canonical terms）
- `AGENTS.md` — 方向锁定段落（引用本文件）
- `catalog_check.py --check-terminology` — 强制执行本文件 §3 分层规则
