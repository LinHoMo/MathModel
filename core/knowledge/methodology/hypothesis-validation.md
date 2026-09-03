# 假设量化验证框架

> 本文档提供假设合理性的量化评估方法，确保建模假设的科学性和可靠性。

---

## 一、假设分类体系

### 1.1 按影响程度分类

| 假设类型 | 定义 | 验证要求 | 示例 |
|---------|------|---------|------|
| **关键假设** | 直接影响模型结构 | 必须严格验证 | 物理定律选择、变量关系 |
| **次要假设** | 影响参数估计 | 需要验证 | 参数分布、测量误差 |
| **简化假设** | 降低计算复杂度 | 说明合理性 | 忽略次要因素 |

### 1.2 按验证方法分类

| 假设类型 | 验证方法 | 数据需求 |
|---------|---------|---------|
| **统计检验型** | 假设检验 | 实验数据 |
| **理论推导型** | 数学证明 | 理论依据 |
| **经验判断型** | 专家评估 | 领域知识 |

### 1.3 按数学性质分类

| 假设类型 | 典型内容 | 验证方法 |
|---------|---------|---------|
| 线性假设 | 变量间线性关系 | 散点图、相关系数 |
| 正态假设 | 误差服从正态分布 | Shapiro-Wilk检验 |
| 独立假设 | 样本相互独立 | Durbin-Watson检验 |
| 同方差假设 | 方差恒定 | Levene检验 |

---

## 二、量化验证方法

### 2.1 统计检验方法

#### 2.1.1 正态性检验

**Shapiro-Wilk检验**：

```python
from scipy import stats

# H0: 数据服从正态分布
# H1: 数据不服从正态分布
statistic, p_value = stats.shapiro(data)

if p_value > 0.05:
    print("不能拒绝正态性假设")
else:
    print("拒绝正态性假设")
```

**判断标准**：
- p > 0.05：不能拒绝正态性假设
- p ≤ 0.05：拒绝正态性假设

#### 2.1.2 独立性检验

**Durbin-Watson检验**：

```python
from statsmodels.stats.stattools import durbin_watson

# DW ≈ 2：无自相关
# DW < 1.5：正自相关
# DW > 2.5：负自相关
dw = durbin_watson(residuals)
```

**判断标准**：
- 1.5 < DW < 2.5：假设成立
- DW ≤ 1.5 或 DW ≥ 2.5：假设不成立

#### 2.1.3 同方差性检验

**Levene检验**：

```python
from scipy import stats

# H0: 各组方差相等
# H1: 各组方差不相等
statistic, p_value = stats.levene(group1, group2, group3)

if p_value > 0.05:
    print("不能拒绝同方差假设")
else:
    print("拒绝同方差假设")
```

#### 2.1.4 线性关系检验

**F检验**：

```python
from scipy import stats

# H0: 线性关系不显著
# H1: 线性关系显著
f_stat, p_value = stats.f_oneway(group1, group2, group3)

if p_value < 0.05:
    print("线性关系显著")
else:
    print("线性关系不显著")
```

### 2.2 灵敏度分析方法

#### 2.2.1 单参数扰动

**方法**：对单个参数进行±10%、±20%的扰动，观察结果变化。

```python
import numpy as np

def sensitivity_analysis(model, params, param_name, perturbations=[0.1, 0.2]):
    results = []
    base_result = model(params)
    
    for p in perturbations:
        # 正向扰动
        params_plus = params.copy()
        params_plus[param_name] *= (1 + p)
        result_plus = model(params_plus)
        
        # 负向扰动
        params_minus = params.copy()
        params_minus[param_name] *= (1 - p)
        result_minus = model(params_minus)
        
        # 计算灵敏度
        sensitivity = (result_plus - result_minus) / (2 * p * params[param_name])
        results.append(sensitivity)
    
    return results
```

**判断标准**：
- 灵敏度 < 0.1：参数不敏感
- 0.1 ≤ 灵敏度 < 0.5：参数中等敏感
- 灵敏度 ≥ 0.5：参数高度敏感

#### 2.2.2 多参数联合扰动

**蒙特卡洛模拟**：

```python
import numpy as np

def monte_carlo_sensitivity(model, param_ranges, n_samples=1000):
    results = []
    
    for _ in range(n_samples):
        # 随机采样参数
        params = {}
        for param, (low, high) in param_ranges.items():
            params[param] = np.random.uniform(low, high)
        
        # 计算结果
        result = model(params)
        results.append(result)
    
    # 统计分析
    mean = np.mean(results)
    std = np.std(results)
    cv = std / mean  # 变异系数
    
    return mean, std, cv
```

**判断标准**：
- 变异系数 < 0.1：模型稳健
- 0.1 ≤ 变异系数 < 0.2：模型较稳健
- 变异系数 ≥ 0.2：模型不稳定

### 2.3 退化测试方法

**原理**：令某参数为0或极端值，检查模型是否退化为已知情况。

**示例**：

```python
def degradation_test(model, params):
    # 测试1：令质量为0
    params_zero_mass = params.copy()
    params_zero_mass['mass'] = 0
    result_zero_mass = model(params_zero_mass)
    
    # 测试2：令阻尼为0
    params_zero_damping = params.copy()
    params_zero_damping['damping'] = 0
    result_zero_damping = model(params_zero_damping)
    
    # 测试3：令刚度为0
    params_zero_stiffness = params.copy()
    params_zero_stiffness['stiffness'] = 0
    result_zero_stiffness = model(params_zero_stiffness)
    
    return {
        'zero_mass': result_zero_mass,
        'zero_damping': result_zero_damping,
        'zero_stiffness': result_zero_stiffness
    }
```

---

## 三、假设合理性评估标准

### 3.1 量化评分体系

| 维度 | 评分标准 | 权重 |
|------|---------|------|
| 物理合理性 | 0-10分 | 30% |
| 数学一致性 | 0-10分 | 25% |
| 数据支撑度 | 0-10分 | 25% |
| 影响程度 | 0-10分 | 20% |

### 3.2 各维度评分细则

#### 物理合理性（30%）

| 分数 | 标准 |
|------|------|
| 9-10 | 完全符合物理定律，有经典文献支持 |
| 7-8 | 基本符合物理定律，有合理解释 |
| 5-6 | 部分符合物理定律，需要说明局限性 |
| 3-4 | 不太符合物理定律，需要重新考虑 |
| 1-2 | 严重违背物理定律，必须修改 |

#### 数学一致性（25%）

| 分数 | 标准 |
|------|------|
| 9-10 | 数学推导完整，无逻辑漏洞 |
| 7-8 | 数学推导基本完整，有小问题 |
| 5-6 | 数学推导有跳步，需要补充 |
| 3-4 | 数学推导有明显错误 |
| 1-2 | 数学推导严重错误 |

#### 数据支撑度（25%）

| 分数 | 标准 |
|------|------|
| 9-10 | 有充分的实验/统计数据支持 |
| 7-8 | 有较好的数据支持 |
| 5-6 | 数据支持有限，需要说明 |
| 3-4 | 数据支持不足，需要补充 |
| 1-2 | 缺乏数据支持 |

#### 影响程度（20%）

| 分数 | 标准 |
|------|------|
| 9-10 | 假设对结果影响很小 |
| 7-8 | 假设对结果影响较小 |
| 5-6 | 假设对结果有一定影响 |
| 3-4 | 假设对结果影响较大 |
| 1-2 | 假设对结果影响很大 |

### 3.3 综合评分计算

```
综合评分 = 物理合理性 × 0.3 + 数学一致性 × 0.25 + 数据支撑度 × 0.25 + 影响程度 × 0.2
```

### 3.4 评估结论

| 综合评分 | 评估结论 | 处理建议 |
|---------|---------|---------|
| ≥ 8分 | 假设合理 | 无需修改 |
| 6-7分 | 假设基本合理 | 需要说明局限性 |
| 4-5分 | 假设存疑 | 需要重新考虑 |
| < 4分 | 假设不合理 | 必须修改 |

---

## 四、假设验证报告模板

### 4.1 报告结构

```markdown
# 假设验证报告

## 一、假设列表

| 编号 | 假设内容 | 类型 | 验证方法 |
|------|---------|------|---------|
| H1 | [内容] | 关键假设 | 统计检验 |
| H2 | [内容] | 次要假设 | 理论推导 |

## 二、验证结果

### 2.1 H1验证
- 验证方法：[方法]
- 检验统计量：[值]
- p值：[值]
- 结论：[通过/不通过]

### 2.2 H2验证
- 验证方法：[方法]
- 理论依据：[来源]
- 结论：[通过/不通过]

## 三、灵敏度分析

### 3.1 单参数扰动
- 参数：[名称]
- 扰动范围：±10%, ±20%
- 结果变化：[百分比]
- 结论：[敏感/不敏感]

### 3.2 多参数联合扰动
- 方法：蒙特卡洛模拟
- 样本数：1000
- 变异系数：[值]
- 结论：[稳健/不稳健]

## 四、综合评估

| 维度 | 评分 | 说明 |
|------|------|------|
| 物理合理性 | [分数] | [说明] |
| 数学一致性 | [分数] | [说明] |
| 数据支撑度 | [分数] | [说明] |
| 影响程度 | [分数] | [说明] |
| **综合评分** | **[分数]** | **[结论]** |

## 五、结论与建议

1. 假设合理性结论：[合理/基本合理/存疑/不合理]
2. 主要发现：[发现]
3. 改进建议：[建议]
```

---

## 五、常见假设验证示例

### 5.1 物理建模假设

| 假设 | 验证方法 | 判断标准 |
|------|---------|---------|
| 忽略空气阻力 | 比较阻力与重力量级 | 阻力/重力 < 0.01 |
| 均匀温度场 | 温度测量数据方差 | 方差 < 阈值 |
| 线性弹性 | 应力-应变曲线 | 相关系数 > 0.99 |

### 5.2 统计模型假设

| 假设 | 验证方法 | 判断标准 |
|------|---------|---------|
| 正态分布 | Shapiro-Wilk检验 | p > 0.05 |
| 独立性 | Durbin-Watson检验 | 1.5 < DW < 2.5 |
| 同方差 | Levene检验 | p > 0.05 |

### 5.3 机器学习假设

| 假设 | 验证方法 | 判断标准 |
|------|---------|---------|
| 特征独立 | 相关系数矩阵 | |r| < 0.8 |
| 数据平衡 | 类别比例 | 比例 > 0.5 |
| 无过拟合 | 交叉验证 | 训练/测试差距 < 0.1 |

---

## 六、参考资源

### 6.1 统计检验参考

- 《统计学》（贾俊平）
- 《概率论与数理统计》（浙大版）
- SciPy.stats文档

### 6.2 灵敏度分析参考

- 《灵敏度分析导论》（Saltelli等）
- SALib Python库

### 6.3 检查清单

- [ ] 所有假设都有明确说明
- [ ] 关键假设都经过验证
- [ ] 验证方法选择恰当
- [ ] 判断标准明确
- [ ] 综合评分计算正确
- [ ] 结论与建议合理
