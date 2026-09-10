# Architecture

> 现行 V3 架构文档。历史 V2 架构文档已删除（不向后兼容）。
> 补充细节见 [docs/architecture/V3.1_ARCHITECTURE.md](architecture/V3.1_ARCHITECTURE.md)。

## 定位

**问题输入 → 数学建模产出（MD/Mermaid 文本）**

产出物为 MODEL_IR（JSON）+ 模型描述文档（MD/Mermaid）。
不包含论文生成（LaTeX/PDF），不向后兼容 V2。

> **Source of truth = Artifact Registry + Evidence Graph。**
> Agent / LLM 只是 Executor。

## 分层定位

| 层 | 位置 | 说明 |
|---|---|---|
| 引擎（Harness） | `core/` | 唯一可复用资产：runtime / roles / workflows / validators / schemas / tools / skills / knowledge / env |
| 研究 | `research/` | 研究实验与基准测试（P15 等） |
| 实例 | `projects/` | 仅 `new_project.py` 创建的用户运行实例 |

引擎是 LLM-free 的可信底座：schema、registry、artifact lifecycle、execution、
evidence、validation、provenance、revision、state transition、deterministic checks
全部由引擎负责；认知工作（problem interpretation、hypothesis、model construction、
candidate generation、code generation、reasoning）由外部 Agent 在 harness 下完成。

## 核心设计

### 1. 角色分离

4 角色（`core/roles/`，V3 唯一）：

- analyst —— 问题理解 / 特征提取
- modeler —— 模型构造 / MODEL_IR 生成
- experimenter —— 实验设计 / 执行 / 验证
- critic —— 评审 / 模型批评

Role 是 capability composition；节点引用 capability，由 runtime executor 执行。
无独立 writer 角色（无论文生成）。

### 2. 契约协作

- Artifact Registry：稳定 ID + 生命周期（problem / question / assumption / model /
  code / experiment / result / claim / decision ...）
- Evidence Graph：typed edges + 失效传播 + Revision lineage
- Workflow DAG：节点是认知步骤，不是 Agent
- 验证门禁：evidence-gate / research-quality / model-critic / assumption-checker

### 3. 知识库分层共享

`core/knowledge/`（方法论 / 方法卡 / 陷阱记忆）+ `catalog.yaml`（双视图单一真源）。
知识卡 = Constraint / Prior，不是答案库。

## 数据流

```
Problem → Question → Model Candidates → Selection Decision → MODEL_IR
       → Implementation → Execution → Validation → Evidence
       → Model Evaluation → Revision → Model Rev.2 → … → Model Documentation
```

ExecutionResult 是一等 Artifact，六态 status（not_executed / running / success /
failed / timeout / invalid）只能来自真实执行；`Execution success ≠ Model correct`
是铁律。

## 铁律体系

1. The Agent Is Not The State
2. infra 不冒充 capability
3. Execution success ≠ Model correct（execution / model / evidence 三级状态分离）
4. Knowledge claim ≠ empirical fact（formalized false authority 禁令）
5. Artifact 是真源；状态可对账、可重放、可审计
6. 随机种子固定 42；多种子运行 ≥5 次报告均值与标准差

## 验证机制

`core/tools/validate.py` —— 项目级 45 项校验（V3 schema / MODEL_IR / 模型描述文档 /
角色 / 知识库 / 数值追溯 / 哈希链 / env 配置等）。

`core/tools/catalog_check.py --check` —— catalog 双视图三方一致。
`core/tools/doctor.py` —— 环境预检。

## 修改后必做

```bash
python core/tools/validate.py                          # 45 项校验
python core/tools/catalog_check.py --check             # 双视图一致
python -m pytest tests -q                              # 基线测试
```
