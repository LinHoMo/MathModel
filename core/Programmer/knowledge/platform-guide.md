# 代码平台分支指南（platform-guide.md）

> 来源：对标 MathModeling-skills 的 Python/MATLAB/北太天元分支 + JuMP/PyOptInterface 求解器外挂。
> 定位：定义编程手「多平台交付」的唯一正确姿势——**单主线、可交付分支**，避免重蹈竞品「双主线内容漂移」的覆辙。

---

## 一、铁则：单主线，分支仅交付

1. **Python 是唯一「真值主线」**：只有 `code/*.py` 会实际执行并产出 `figures/all_results.json`，这是论文全部数值的冻结来源（铁律 P2、W1）。任何分支代码都不允许改写 `all_results.json`。
2. **MATLAB / 北太天元 是「交付分支」**：面向国赛（CUMCM）评审环境——近两年国赛主推国产平台**北太天元**（语法兼容 MATLAB），部分赛区提交要求 `.m`。分支代码与 Python 主线**数值等价**，但只作交付件，不参与门禁的数值判定。
3. **何时产出分支**：由 `code.target_platform` 配置决定（默认 `python`）。设为 `matlab` 或 `beitian` 时，code-implementer 在交付 Python 主线外，额外产出对应平台的等价代码；默认 `python` 时不产出分支，零额外成本。

## 二、平台等价物对照表（迁移查表用）

| 能力 | Python（主线） | MATLAB | 北太天元 |
|---|---|---|---|
| 数组/矩阵 | `numpy` | 原生矩阵 | 兼容 MATLAB 矩阵 |
| 线性规划 | `scipy.optimize.linprog` | `linprog` | `linprog`（同 MATLAB） |
| 非线性优化 | `scipy.optimize.minimize` | `fmincon` | `fmincon`（同 MATLAB） |
| 遗传/启发式 | 自研模板（ga_de_pso 等） | `ga`（Global Opt. Toolbox） | 自研（无 ga 工具箱则重写） |
| 绘图 | `matplotlib` | `plot` / `surf` | `plot` / `surf`（同 MATLAB） |
| 随机种子 | `np.random.seed(42)` | `rng(42)` | `rng(42)` |
| 数值积分 | `scipy.integrate` | `integral` | `integral`（同 MATLAB） |
| ODE/PDE | `solve_ivp` / 自研 rk | `ode45` | `ode45`（同 MATLAB） |

> 北太天元以 MATLAB 语法为基准，迁移时优先按「把 MATLAB 代码原样跑通」处理，仅需注意其工具箱覆盖可能少于 MATLAB。

## 三、求解器外挂（可选，不硬依赖）

主线不强制要求安装第三方求解器，但进阶题目（大规模整数规划 / 混合整数）可外挂：

- **Python**：`scipy.optimize`（零依赖，默认）→ 进阶 `OR-Tools` / `PyOptInterface` / `pulp`（需显式安装，缺失时回退 scipy 并标注「未用外部求解器」）。
- **MATLAB / 北太天元**：直接用 Optimization Toolbox 的 `linprog` / `intlinprog` / `fmincon`。

外挂求解器**不允许**改变 `all_results.json` 的口径：若外挂求解器结果与主线 scipy 结果不一致，以主线 `all_results.json` 为准，并对差异在 `CODE_DELIVERABLES.md` 的 `results_ledger` 中记录归因。

## 四、template_plan.json 里的平台声明

`template-selector` 在 template_plan.json 中写入平台信息（字段必须在 `code_deliverables.schema.json` 允许范围内，缺省补默认值）：

```json
{
  "target_platform": "python",
  "delivery_branches": [],
  "subproblems": [
    {
      "id": "problem_1",
      "method": "遗传算法",
      "template_path": "core/Programmer/knowledge/code-templates/optimization/genetic_algorithm.py",
      "platform": "python",
      "functions": [],
      "dependencies": ["numpy", "scipy"]
    }
  ]
}
```

- `target_platform`：主线平台，取自 `get("code.target_platform", "python")`，取值 `python` / `matlab` / `beitian`。
- `delivery_branches`：交付分支列表（如 `["matlab"]` / `["beitian"]`），默认 `[]`。
- 当 `target_platform` 非 `python` 时，`template_path` 仍指向 Python 模板（主线不变），`delivery_branches` 追加该平台。

## 五、随机种子与可复现（跨平台一致口径）

- Python 主线：`np.random.seed(42)` + `random.seed(42)`（铁律 P1）。
- MATLAB / 北太天元分支：`rng(42)`，且启发式多次运行（≥5 次）报告均值与标准差（铁律 P6）——跨平台时以 Python 主线的均值/标准差为准写入 `all_results.json`。

## 六、交付清单

- `code/main.py`（主线，可执行，产出 `figures/all_results.json`）
- `code/model.py`（核心模型）
- `code/utils.py`（数据/可视化）
- 分支可选：`code/main.m`（MATLAB）或 `code/main.btm`（北太天元），文件头注释 `% 交付分支：与 main.py 数值等价，不产出 all_results.json`。