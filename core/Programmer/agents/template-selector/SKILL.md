---
name: template-selector
description: '根据 MODEL_SPEC 选择代码模板并规划实现路径，产出 template_plan.json。编程手的起始步骤。'
hand: programmer
utg_layer: L1
stage: 1
inputs:
  - MODEL_SPEC.md
outputs:
  - work/template_plan.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> programmer template-selector`
- **输入**：output/MODEL_SPEC.md
- **输出**：`work/template_plan.json`
- **核心步骤**：1. 解析模型规格 → 2. 匹配代码模板 → 3. 规划实现路径 → 4. 写 template_plan.json
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Template Selector Agent

## Role

模板选择器：读取 MODEL_SPEC.md，按建模方法分类匹配 Programmer 知识库中的代码模板，输出结构化 template_plan.json 供下游 code-implementer 直接消费。

## UTG Layer

**L1 结构化输出层**：把上游建模手的非结构化建模意图（自然语言方法描述、公式、约束）固化为机器可校验的结构化计划文件 `work/template_plan.json`。本层拦截目标：
- 零字段缺失（每个子问题必须有 method / template_path / functions / dependencies）
- 零路径歧义（template_path 必须指向 `core/Programmer/knowledge/code-templates/` 下真实存在的文件）
- 模板与题型一一对应，不允许"未分类 → 凭空选一个"
- template_plan.json 字段对齐 `core/schemas/code_deliverables.schema.json` 中 environment / files 的前置需求

## Contract

- **输入**：`MODEL_SPEC.md`（按优先级查找：当前目录 → `../Modeler/output/MODEL_SPEC.md`）
- **输出**：`work/template_plan.json`
- **schema（建议字段）**：
  ```json
  {
    "spec_source": "MODEL_SPEC.md 路径",
    "problem_type": "题型总分类",
    "random_seed": 42,
    "target_platform": "python",
    "delivery_branches": [],
    "subproblems": [
      {
        "id": "problem_1",
        "method": "遗传算法",
        "template_path": "core/Programmer/knowledge/code-templates/optimization/genetic_algorithm.py",
        "platform": "python",
        "methodology_ref": "core/knowledge/methodology/optimization.md",
        "functions": [{"name": "solve_problem_1", "description": "...", "inputs": "...", "outputs": "..."}],
        "dependencies": ["numpy", "scipy"],
        "notes": "需要适配的参数/目标函数说明"
      }
    ],
    "file_plan": [
      {"path": "code/main.py", "purpose": "主入口按序调用子问题"},
      {"path": "code/model.py", "purpose": "核心模型实现"}
    ]
  }
  ```

## Procedure

### Step 1: 定位并解析 MODEL_SPEC.md

按优先级查找 MODEL_SPEC.md：当前目录 `MODEL_SPEC.md` → `../Modeler/output/MODEL_SPEC.md`。若均不存在，停止并报告错误。

必须提取的信息清单：
- [ ] 子问题数量和描述
- [ ] 每个子问题的数学方法（公式、算法）
- [ ] 输入数据格式（文件类型、字段、编码）
- [ ] 输出结果格式（JSON/PNG/XLSX）
- [ ] 预期结果范围（用于验证）
- [ ] 必须实现的函数/模块列表
- [ ] 约束条件

### Step 2: 按决策树匹配代码模板

根据 MODEL_SPEC 中的方法选择模板（搬自原 Programmer 手流程，完整保留）：

```
根据 MODEL_SPEC 中的方法选择模板：
├── 优化问题
│   ├── 连续优化 → core/Programmer/knowledge/code-templates/optimization/genetic_algorithm.py
│   ├── 离散优化 → core/Programmer/knowledge/code-templates/optimization/genetic_algorithm.py
│   ├── 组合优化 → core/Programmer/knowledge/code-templates/optimization/simulated_annealing.py
│   ├── 多目标优化 → core/Programmer/knowledge/code-templates/optimization/genetic_algorithm.py
│   ├── GA/DE/PSO统一框架 → core/Programmer/knowledge/code-templates/optimization/ga_de_pso.py
│   ├── 整数规划/0-1规划 → core/Programmer/knowledge/code-templates/optimization/integer_programming.py
│   ├── 蚁群算法 → core/Programmer/knowledge/code-templates/optimization/ant_colony.py
│   └── 差分进化 → core/Programmer/knowledge/code-templates/optimization/differential_evolution.py
├── 回归问题
│   ├── 线性关系 → core/Programmer/knowledge/code-templates/regression/multiple_regression.py
│   ├── 多重共线性 → core/Programmer/knowledge/code-templates/regression/ridge_lasso.py
│   └── 非线性关系 → core/Programmer/knowledge/code-templates/regression/multiple_regression.py
├── 分类问题
│   ├── 二分类 → core/Programmer/knowledge/code-templates/machine-learning/random_forest.py
│   ├── 高精度 → core/Programmer/knowledge/code-templates/machine-learning/xgboost_model.py
│   ├── SVM → core/Programmer/knowledge/code-templates/machine-learning/svm_model.py
│   ├── 神经网络 → core/Programmer/knowledge/code-templates/machine-learning/neural_network_sklearn.py
│   └── 分类算法套件 → core/Programmer/knowledge/code-templates/classification/classification_suite.py
├── 聚类问题
│   ├── K-Means → core/Programmer/knowledge/code-templates/clustering/clustering_suite.py
│   └── 聚类算法套件 → core/Programmer/knowledge/code-templates/clustering/clustering_suite.py
├── 时序问题
│   ├── 平稳序列 → core/Programmer/knowledge/code-templates/time-series/arima_model.py
│   ├── 指数平滑 → core/Programmer/knowledge/code-templates/time-series/exponential_smoothing.py
│   └── LSTM → core/Programmer/knowledge/code-templates/time-series/lstm_model.py
├── 评价问题
│   ├── AHP → core/Programmer/knowledge/code-templates/evaluation/ahp.py
│   ├── 熵权法 → core/Programmer/knowledge/code-templates/evaluation/entropy_weight.py
│   ├── DEA → core/Programmer/knowledge/code-templates/evaluation/dea.py
│   └── 灰色关联 → core/Programmer/knowledge/code-templates/evaluation/grey_relational.py
├── 排队论 → core/Programmer/knowledge/code-templates/queueing/mm1_model.py
├── 图论
│   ├── 最短路径 → core/Programmer/knowledge/code-templates/graph/dijkstra.py
│   └── 网络流 → core/Programmer/knowledge/code-templates/graph/network_flow.py
├── 微分方程 → core/Programmer/knowledge/code-templates/numerical/runge_kutta.py
├── 有限差分/热传导PDE → core/Programmer/knowledge/code-templates/numerical/finite_difference.py
├── Thomas算法(三对角) → core/Programmer/knowledge/code-templates/numerical/thomas_algorithm.py
├── 插值 → core/Programmer/knowledge/code-templates/interpolation/spline.py
├── 蒙特卡洛仿真 → core/Programmer/knowledge/code-templates/simulation/monte_carlo.py
├── 图像处理 → core/Programmer/knowledge/code-templates/image/edge_detection.py
├── 灵敏度分析 → core/Programmer/knowledge/code-templates/utils/sensitivity_analysis.py
└── 未分类问题 → 参考 core/knowledge/methodology/ 中的方法论文档，从头编写
```

`core/Programmer/knowledge/code-templates/` 共 15 个子目录：classification / clustering / deep-learning / evaluation / graph / image / interpolation / machine-learning / numerical / optimization / queueing / regression / simulation / time-series / utils。

### Step 3: 关联方法论文档

对每个子问题，从 `core/knowledge/methodology/`（12 篇）补一份方法论引用：
optimization.md / regression.md / time-series.md / machine-learning.md / numerical-methods.md / ode-pde.md / interpolation-fitting.md / monte-carlo.md / dynamic-programming.md / markov-chain.md / multi-objective.md / response-surface.md。

### Step 4: 规划文件结构与函数清单

按 P3 规划 `code/` 目录结构：`main.py`（主入口，按序调用 solve_problem_N）、`model.py`（核心模型）、`utils.py`（数据/可视化）、必要时 `problem_N.py` 拆分。每个子问题必须有 `solve_problem_N(params: dict) -> dict` 标准签名（与 core/schemas/code_deliverables.schema.json 的 `results.problem_N` 对齐）。

### Step 5: 写出 template_plan.json

将以上决策固化为 `work/template_plan.json`，字段见 Contract。随机种子与平台字段从 env 读取：
```python
from core.env.loader import get
seed = get("code.random_seed", 42)              # 默认 42
platform = get("code.target_platform", "python") # python / matlab / beitian，默认 python
```

平台与交付分支规则（详细对照见 `core/Programmer/knowledge/platform-guide.md`，如 numpy→MATLAB 矩阵、scipy→fmincon、`np.random.seed(42)`→`rng(42)`）：
- `target_platform` 写入 `platform` 字段，默认 `python`；方案里的 `template_path` 恒指向 Python 模板（主线不变）。
- `target_platform` 为 `matlab` 或 `beitian` 时，`delivery_branches` 追加该平台值，下游 code-implementer 据此刻画出 `code/main.m` / `code/main.btm` 交付分支（分支不产出 `all_results.json`，数值以 Python 主线为准）。
- 默认 `python` 时 `delivery_branches` 保持 `[]`，不产出分支。

## Self-Check

- [ ] MODEL_SPEC.md 已定位并完整解析，子问题数量明确
- [ ] 每个子问题都有 template_path，且路径指向 `core/Programmer/knowledge/code-templates/` 下真实存在的文件
- [ ] 未分类子问题已显式标注"从头编写"并附 methodology_ref，未凭空选模板
- [ ] 每个子问题规划了 `solve_problem_N(params: dict) -> dict` 标准函数签名
- [ ] file_plan 中所有 path 以 `code/` 开头（符合 P3 与 schema `^code/` 约束）
- [ ] template_plan.json 为有效 JSON，字段无缺失（id/method/template_path/functions/dependencies）
- [ ] 随机种子字段已写入（默认 42，与 P1 对齐）
- [ ] `target_platform` 已从 `get("code.target_platform", "python")` 写入且取值 ∈ {python, matlab, beitian}；`delivery_branches` 与之一致（非 python 时追加该平台，python 时保持 `[]`）
- [ ] 每个子问题附 methodology_ref（指向 `core/knowledge/methodology/` 真实文档）

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "programmer",
  "stage": 1,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "template-selector",
      "stage": 1,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/Programmer/knowledge/code-templates/`（15 个子目录代码模板）
- `core/Programmer/knowledge/platform-guide.md`（多平台代码分支与求解器外挂指南：单主线 python + matlab/beitian 交付分支）
- `core/knowledge/methodology/`（12 篇方法论文档）
- `core/schemas/code_deliverables.schema.json`（结构化输出 Schema，定义 files/results_ledger 字段约束）
- `core/env/loader.py`：`get("code.random_seed", 42)` 读取随机种子
- `core/Programmer/laws/rules.md`（铁律 P1/P2/P3/P9 与本层相关）

## Iteration

当模板匹配出现以下情况时回退修正：
1. **无匹配模板**：先用 methodology 文档补全方法描述，再退回"从头编写"分支并在 notes 标注需自实现的算法骨架。
2. **多模板候选**：按题型子类（连续/离散/多目标）二次判定，记录被淘汰模板及理由。
3. **schema 不符**：template_plan.json 字段缺失或 path 不以 `code/` 开头时，回到 Step 4 修正后重写。
4. **MODEL_SPEC 缺字段**：停止执行并报告上游 Modeler，不臆测方法。
