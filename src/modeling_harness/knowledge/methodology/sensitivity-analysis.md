# 灵敏度分析方法论

> 本文件提供数学建模竞赛中常用的灵敏度分析知识，包括方法选择、实现要点、防错策略和验证方法。

---

## 1. 方法选择决策树

```
灵敏度分析类型识别：
├── 单因素分析
│   ├── 参数数量少 → 单因素扰动
│   └── 参数数量多 → Morris筛选
├── 全局分析
│   ├── 参数数量适中 → Sobol指数
│   └── 参数数量多 → Sobol+筛选
├── 模型验证
│   ├── 输出不确定性 → 方差分解
│   └── 参数重要性 → Tornado图
└── 鲁棒性评估
    ├── 参数范围已知 → 区间分析
    └── 参数分布已知 → 概率灵敏度
```

---

## 2. 核心方法详解

### 2.1 单因素扰动分析

**方法原理**：
固定其他参数，逐一扰动每个参数，观察输出变化。

**适用场景**：
- 参数数量少
- 快速筛选关键参数
- 初步分析

**代码框架**：
```python
import numpy as np
import matplotlib.pyplot as plt

def single_parameter_perturbation(model, base_params, param_names,
                                   perturbation_range=np.arange(-0.2, 0.21, 0.05)):
    """
    单因素扰动分析
    """
    base_output = model(base_params)
    results = {}
    
    for i, name in enumerate(param_names):
        outputs = []
        for p in perturbation_range:
            perturbed = base_params.copy()
            perturbed[i] *= (1 + p)
            output = model(perturbed)
            outputs.append(output)
        results[name] = outputs
    
    # 计算灵敏度指标
    sensitivities = {}
    for name, outputs in results.items():
        outputs = np.array(outputs)
        sensitivity = (outputs[-1] - outputs[0]) / (2 * perturbation_range[-1])
        sensitivities[name] = sensitivity
    
    # 绘图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    for name, outputs in results.items():
        ax1.plot(perturbation_range * 100, outputs, 'o-', label=name, markersize=3)
    ax1.set_xlabel('参数变化百分比 (%)')
    ax1.set_ylabel('模型输出')
    ax1.set_title('单因素扰动分析')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    names = list(sensitivities.keys())
    values = list(sensitivities.values())
    ax2.barh(names, values)
    ax2.set_xlabel('灵敏度指数')
    ax2.set_title('参数灵敏度排序')
    
    plt.tight_layout()
    
    return results, sensitivities

# 使用示例
def my_model(params):
    return params[0]**2 + 2*params[1] + params[2]*0.5

base_params = [1.0, 2.0, 3.0]
param_names = ['x1', 'x2', 'x3']
results, sensitivities = single_parameter_perturbation(
    my_model, base_params, param_names
)
print("灵敏度指数:", sensitivities)
```

---

### 2.2 Sobol指数分析

**方法原理**：
基于方差分解，量化各参数及其交互作用对输出方差的贡献。

**适用场景**：
- 全局灵敏度分析
- 参数交互作用分析
- 模型验证

**关键指标**：
- 一阶效应指数 Si：参数i的单独贡献
- 全局效应指数 STi：参数i的总贡献（含交互）
- 交互效应：STi - Si

**代码框架**：
```python
import numpy as np
from SALib.sample import saltelli
from SALib.analyze import sobol

def sobol_analysis(model, param_names, param_bounds, n_samples=1024):
    """
    Sobol灵敏度分析
    """
    problem = {
        'num_vars': len(param_names),
        'names': param_names,
        'bounds': param_bounds
    }
    
    # 生成样本
    param_values = saltelli.sample(problem, n_samples, calc_second_order=True)
    
    # 计算模型输出
    Y = np.array([model(p) for p in param_values])
    
    # Sobol分析
    Si = sobol.analyze(problem, Y, calc_second_order=True, print_to_console=False)
    
    # 输出结果
    print("Sobol灵敏度分析结果:")
    print(f"{'参数':<10} {'一阶Si':<15} {'全局STi':<15} {'交互效应':<15}")
    print("-" * 55)
    for i, name in enumerate(param_names):
        print(f"{name:<10} {Si['S1'][i]:<15.4f} {Si['ST'][i]:<15.4f} "
              f"{Si['ST'][i] - Si['S1'][i]:<15.4f}")
    
    return Si

# 使用示例
def sobol_model(params):
    x1, x2, x3 = params
    return np.sin(x1) + 2*x2**2 + 0.5*x3

param_names = ['x1', 'x2', 'x3']
param_bounds = [[0, np.pi], [0, 1], [0, 5]]

Si = sobol_analysis(sobol_model, param_names, param_bounds)
```

---

### 2.3 Morris筛选法

**方法原理**：
通过计算基本效应（Elementary Effect），快速筛选重要参数。

**适用场景**：
- 参数数量多（>20）
- 计算资源有限
- 初步筛选

**代码框架**：
```python
import numpy as np
from SALib.sample import morris as morris_sample
from SALib.analyze import morris as morris_analyze

def morris_screening(model, param_names, param_bounds, n_trajectories=10):
    """
    Morris筛选分析
    """
    problem = {
        'num_vars': len(param_names),
        'names': param_names,
        'bounds': param_bounds
    }
    
    # 生成样本
    param_values = morris_sample.sample(problem, n_trajectories)
    
    # 计算模型输出
    Y = np.array([model(p) for p in param_values])
    
    # Morris分析
    Si = morris_analyze.analyze(problem, param_values, Y, 
                                 conf_level=0.95, print_to_console=False)
    
    # 输出结果
    print("Morris筛选结果:")
    print(f"{'参数':<10} {'均值μ*':<15} {'标准差σ':<15} {'重要性':<10}")
    print("-" * 50)
    for i, name in enumerate(param_names):
        importance = "重要" if Si['mu_star'][i] > np.mean(Si['mu_star']) else "次要"
        print(f"{name:<10} {Si['mu_star'][i]:<15.4f} {Si['sigma'][i]:<15.4f} "
              f"{importance:<10}")
    
    return Si

# 使用示例
def morris_model(params):
    return sum(p**2 for p in params)

param_names = [f'x{i}' for i in range(10)]
param_bounds = [[-1, 1]] * 10

Si = morris_screening(morris_model, param_names, param_bounds)
```

---

### 2.4 Tornado图

**方法原理**：
可视化各参数对输出的影响程度，按影响大小排序。

**代码框架**：
```python
import matplotlib.pyplot as plt
import numpy as np

def tornado_plot(param_names, low_values, high_values, base_value):
    """
    绘制Tornado图
    """
    n_params = len(param_names)
    
    # 计算影响范围
    low_impact = [base_value - low for low in low_values]
    high_impact = [high - base_value for high in high_values]
    
    # 按影响范围排序
    total_impact = [abs(l) + abs(h) for l, h in zip(low_impact, high_impact)]
    sorted_indices = np.argsort(total_impact)[::-1]
    
    param_names = [param_names[i] for i in sorted_indices]
    low_impact = [low_impact[i] for i in sorted_indices]
    high_impact = [high_impact[i] for i in sorted_indices]
    
    # 绘图
    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(n_params)
    
    ax.barh(y_pos, low_impact, height=0.4, label='Low (-20%)', color='blue', alpha=0.6)
    ax.barh([y + 0.4 for y in y_pos], high_impact, height=0.4, 
            label='High (+20%)', color='red', alpha=0.6)
    
    ax.set_yticks([y + 0.2 for y in y_pos])
    ax.set_yticklabels(param_names)
    ax.axvline(x=0, color='black', linestyle='--')
    ax.set_xlabel('模型输出变化')
    ax.set_title('Tornado图 - 参数灵敏度排序')
    ax.legend()
    plt.tight_layout()
    
    return fig

# 使用示例
param_names = ['温度', '压力', '催化剂', '时间', '浓度']
base_value = 100
low_values = [95, 98, 90, 97, 96]
high_values = [105, 102, 112, 103, 104]

tornado_plot(param_names, low_values, high_values, base_value)
```

---

## 3. 鲁棒性评估

### 3.1 区间分析

```python
def interval_analysis(model, param_bounds, n_samples=10000):
    """
    区间分析：评估参数在给定范围内的输出范围
    """
    n_params = len(param_bounds)
    samples = np.random.uniform(
        [b[0] for b in param_bounds],
        [b[1] for b in param_bounds],
        (n_samples, n_params)
    )
    
    outputs = np.array([model(s) for s in samples])
    
    result = {
        'mean': np.mean(outputs),
        'std': np.std(outputs),
        'min': np.min(outputs),
        'max': np.max(outputs),
        'percentile_5': np.percentile(outputs, 5),
        'percentile_95': np.percentile(outputs, 95)
    }
    
    print(f"输出范围: [{result['min']:.4f}, {result['max']:.4f}]")
    print(f"90%置信区间: [{result['percentile_5']:.4f}, {result['percentile_95']:.4f}]")
    
    return result
```

### 3.2 概率灵敏度

```python
def probabilistic_sensitivity(model, param_distributions, n_samples=10000):
    """
    概率灵敏度分析：考虑参数的概率分布
    """
    samples = []
    for dist in param_distributions:
        if dist['type'] == 'normal':
            samples.append(np.random.normal(dist['mean'], dist['std'], n_samples))
        elif dist['type'] == 'uniform':
            samples.append(np.random.uniform(dist['low'], dist['high'], n_samples))
    
    samples = np.array(samples).T
    outputs = np.array([model(s) for s in samples])
    
    result = {
        'mean': np.mean(outputs),
        'std': np.std(outputs),
        'pdf_x': np.linspace(np.min(outputs), np.max(outputs), 100)
    }
    
    return result
```

---

## 4. 常见陷阱与最佳实践

### 4.1 常见陷阱

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| 扰动范围选择不当 | 灵敏度估计偏差 | 参考物理范围/经验范围 |
| 交互效应忽略 | 低估参数重要性 | 使用全局分析方法 |
| 样本量不足 | 结果不稳定 | 增加样本量/收敛性分析 |
| 参数相关性忽略 | 结果不准确 | 处理相关参数 |
| 单一指标 | 评估片面 | 多指标综合评估 |

### 4.2 最佳实践

- **多方法对比**：单因素+全局分析
- **收敛性分析**：监控结果随样本量的变化
- **可视化展示**：Tornado图、散点图
- **参数相关性**：分析参数间的相互作用
- **结果解释**：结合业务逻辑解释灵敏度

---

## 5. 验证清单

- [ ] 扰动范围合理（基于物理/经验范围）
- [ ] 样本量足够（收敛性验证）
- [ ] 交互效应已分析（全局方法）
- [ ] 参数相关性已考虑
- [ ] 灵敏度排序合理（与业务逻辑一致）
- [ ] 可视化展示完整（Tornado图等）
- [ ] 结果可解释（结合业务逻辑）
- [ ] 鲁棒性评估已执行
