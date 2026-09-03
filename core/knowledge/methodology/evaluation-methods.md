# 综合评价方法论

> 本文档提供综合评价的完整方法论，包括AHP、熵权法、DEA、灰色关联分析等核心方法。

---

## 一、方法选择决策树

```
综合评价问题
├── 权重确定方式？
│   ├── 主观赋权 → AHP层次分析法
│   │   ├── 专家经验丰富 → AHP
│   │   └── 指标较少(<10) → AHP
│   ├── 客观赋权 → 熵权法
│   │   ├── 指标可量化 → 熵权法
│   │   └── 数据完整 → 熵权法
│   └── 组合赋权 → AHP + 熵权法
├── 评价对象数量？
│   ├── 少量(≤30) → TOPSIS / 灰色关联
│   ├── 大量(>30) → DEA数据包络分析
│   └── 不确定 → 模糊综合评价
└── 指标类型？
    ├── 定量指标 → TOPSIS / DEA
    └── 定性+定量 → AHP + 模糊综合评价
```

---

## 二、AHP层次分析法

### 2.1 模型原理

**AHP（Analytic Hierarchy Process）**：将复杂问题分解为目标、准则、方案等层次，通过两两比较确定权重。

**一致性检验**：CR = CI/RI < 0.1 时，判断矩阵具有满意一致性。

### 2.2 标度含义

| 标度 | 含义 |
|------|------|
| 1 | 两因素同样重要 |
| 3 | 前者比后者稍微重要 |
| 5 | 前者比后者明显重要 |
| 7 | 前者比后者强烈重要 |
| 9 | 前者比后者极端重要 |
| 2,4,6,8 | 相邻判断的中间值 |

### 2.3 完整代码框架

```python
import numpy as np
import pandas as pd

class AHP:
    def __init__(self, criteria, alternatives=None):
        self.criteria = criteria
        self.alternatives = alternatives
        self.criteria_matrix = None
        self.criteria_weights = None
        self.alternative_matrices = {}
        self.alternative_weights = {}
    
    def set_criteria_matrix(self, matrix):
        self.criteria_matrix = np.array(matrix)
        self.criteria_weights = self.calculate_weights(self.criteria_matrix)
    
    def set_alternative_matrix(self, criterion, matrix):
        self.alternative_matrices[criterion] = np.array(matrix)
        self.alternative_weights[criterion] = self.calculate_weights(
            self.alternative_matrices[criterion]
        )
    
    def calculate_weights(self, matrix):
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        max_idx = np.argmax(eigenvalues.real)
        max_eigenvalue = eigenvalues[max_idx].real
        weights = eigenvectors[:, max_idx].real
        weights = weights / weights.sum()
        
        # 一致性检验
        n = matrix.shape[0]
        CI = (max_eigenvalue - n) / (n - 1)
        RI_table = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 
                    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
        RI = RI_table.get(n, 1.49)
        CR = CI / RI if RI > 0 else 0
        
        return {
            'weights': weights,
            'max_eigenvalue': max_eigenvalue,
            'CI': CI,
            'RI': RI,
            'CR': CR,
            'consistent': CR < 0.1
        }
    
    def calculate_final_weights(self):
        if self.criteria_weights is None:
            raise ValueError("请先设置准则层判断矩阵")
        
        final_weights = np.zeros(len(self.alternatives))
        
        for i, criterion in enumerate(self.criteria):
            if criterion in self.alternative_weights:
                alt_weights = self.alternative_weights[criterion]['weights']
                final_weights += self.criteria_weights['weights'][i] * alt_weights
        
        return final_weights / final_weights.sum()
    
    def get_results(self):
        results = {
            'criteria_weights': self.criteria_weights,
            'alternative_weights': self.alternative_weights,
            'final_weights': self.calculate_final_weights()
        }
        return results
```

### 2.4 使用示例

```python
# 准则层
criteria = ['成本', '质量', '服务']
criteria_matrix = [
    [1, 1/3, 3],
    [3, 1, 5],
    [1/3, 1/5, 1]
]

# 方案层（对每个准则）
alternatives = ['方案A', '方案B', '方案C']

# 对成本的判断矩阵
cost_matrix = [
    [1, 1/2, 1/3],
    [2, 1, 1/2],
    [3, 2, 1]
]

# 对质量的判断矩阵
quality_matrix = [
    [1, 3, 5],
    [1/3, 1, 3],
    [1/5, 1/3, 1]
]

# 对服务的判断矩阵
service_matrix = [
    [1, 1/3, 1/5],
    [3, 1, 1/3],
    [5, 3, 1]
]

# 计算
ahp = AHP(criteria, alternatives)
ahp.set_criteria_matrix(criteria_matrix)
ahp.set_alternative_matrix('成本', cost_matrix)
ahp.set_alternative_matrix('质量', quality_matrix)
ahp.set_alternative_matrix('服务', service_matrix)

results = ahp.get_results()
print("最终权重:", results['final_weights'])
```

---

## 三、熵权法

### 3.1 模型原理

**熵权法**：根据指标变异程度确定权重，变异越大，权重越大。

**信息熵**：Hⱼ = -k×Σpᵢⱼ×ln(pᵢⱼ)，其中 k = 1/ln(n)

**差异系数**：dⱼ = 1 - Hⱼ

**权重**：wⱼ = dⱼ / Σdⱼ

### 3.2 完整代码框架

```python
import numpy as np
import pandas as pd

class EntropyWeight:
    def __init__(self, data):
        """
        data: DataFrame或ndarray，行为样本，列为指标
        """
        self.data = np.array(data, dtype=float)
        self.n_samples, self.n_indicators = self.data.shape
        self.weights = None
        self.entropy = None
    
    def normalize(self, method='positive'):
        """标准化（正向指标）"""
        min_vals = self.data.min(axis=0)
        max_vals = self.data.max(axis=0)
        
        # 避免除零
        range_vals = max_vals - min_vals
        range_vals[range_vals == 0] = 1
        
        if method == 'positive':
            normalized = (self.data - min_vals) / range_vals
        else:  # negative
            normalized = (max_vals - self.data) / range_vals
        
        # 处理零值（避免ln(0)）
        normalized = normalized + 1e-10
        
        return normalized
    
    def calculate_entropy(self):
        """计算信息熵"""
        normalized = self.normalize()
        
        # 计算比重
        p = normalized / normalized.sum(axis=0)
        
        # 计算信息熵
        k = 1 / np.log(self.n_samples)
        self.entropy = -k * (p * np.log(p)).sum(axis=0)
        
        return self.entropy
    
    def calculate_weights(self):
        """计算权重"""
        if self.entropy is None:
            self.calculate_entropy()
        
        # 差异系数
        d = 1 - self.entropy
        
        # 权重
        self.weights = d / d.sum()
        
        return self.weights
    
    def get_results(self):
        if self.weights is None:
            self.calculate_weights()
        
        return {
            'entropy': self.entropy,
            'weights': self.weights,
            'diversity': 1 - self.entropy
        }
```

### 3.3 使用示例

```python
import pandas as pd

# 示例数据：学生综合评价
data = pd.DataFrame({
    '成绩': [85, 92, 78, 95, 88],
    '出勤': [90, 85, 95, 88, 92],
    '作业': [88, 90, 82, 96, 85],
    '竞赛': [75, 88, 70, 92, 80]
})

# 计算权重
ew = EntropyWeight(data)
results = ew.get_results()

print("各指标权重:")
for i, col in enumerate(data.columns):
    print(f"  {col}: {results['weights'][i]:.4f}")
```

---

## 四、TOPSIS逼近理想解排序法

### 4.1 模型原理

**TOPSIS**：通过计算各方案与正理想解和负理想解的距离进行排序。

**步骤**：
1. 标准化决策矩阵
2. 计算加权标准化矩阵
3. 确定正理想解和负理想解
4. 计算各方案到正负理想解的距离
5. 计算相对贴近度并排序

### 4.2 完整代码框架

```python
import numpy as np
import pandas as pd

class TOPSIS:
    def __init__(self, data, weights):
        """
        data: 决策矩阵（行为方案，列为指标）
        weights: 指标权重
        """
        self.data = np.array(data, dtype=float)
        self.weights = np.array(weights)
        self.n_samples, self.n_indicators = self.data.shape
    
    def normalize(self):
        """向量标准化"""
        norm = np.sqrt((self.data ** 2).sum(axis=0))
        return self.data / norm
    
    def calculate_weighted(self):
        """加权标准化矩阵"""
        normalized = self.normalize()
        return normalized * self.weights
    
    def calculate_ideal(self):
        """正负理想解"""
        weighted = self.calculate_weighted()
        
        # 正理想解（效益型指标取最大，成本型取最小）
        positive_ideal = weighted.max(axis=0)
        # 负理想解
        negative_ideal = weighted.min(axis=0)
        
        return positive_ideal, negative_ideal
    
    def calculate_distance(self):
        """到正负理想解的欧氏距离"""
        weighted = self.calculate_weighted()
        positive_ideal, negative_ideal = self.calculate_ideal()
        
        d_positive = np.sqrt(((weighted - positive_ideal) ** 2).sum(axis=1))
        d_negative = np.sqrt(((weighted - negative_ideal) ** 2).sum(axis=1))
        
        return d_positive, d_negative
    
    def calculate_closeness(self):
        """相对贴近度"""
        d_positive, d_negative = self.calculate_distance()
        
        closeness = d_negative / (d_positive + d_negative)
        return closeness
    
    def rank(self):
        """排序"""
        closeness = self.calculate_closeness()
        rank_idx = np.argsort(-closeness)
        return rank_idx, closeness
```

### 4.3 使用示例

```python
# 决策矩阵：行为方案，列为指标
data = [
    [85, 90, 88, 75],  # 方案A
    [92, 85, 90, 88],  # 方案B
    [78, 95, 82, 70],  # 方案C
    [95, 88, 96, 92],  # 方案D
]

# 权重（来自AHP或熵权法）
weights = [0.3, 0.25, 0.25, 0.2]

# TOPSIS计算
topsis = TOPSIS(data, weights)
rank_idx, closeness = topsis.rank()

print("排序结果:")
for i, idx in enumerate(rank_idx):
    print(f"  第{i+1}名: 方案{chr(65+idx)}, 贴近度={closeness[idx]:.4f}")
```

---

## 五、DEA数据包络分析

### 5.1 模型原理

**DEA（Data Envelopment Analysis）**：评价多输入多输出决策单元（DMU）的相对效率。

**CCR模型**（规模报酬不变）：

```
max Σuᵣyᵣ₀
s.t. Σvᵢxᵢ₀ = 1
     Σuᵣyᵣⱼ - Σvᵢxᵢⱼ ≤ 0, ∀j
     uᵣ, vᵢ ≥ 0
```

### 5.2 完整代码框架

```python
import numpy as np
from scipy.optimize import linprog

class DEA:
    def __init__(self, inputs, outputs):
        """
        inputs: 输入矩阵（行为DMU，列为输入指标）
        outputs: 输出矩阵（行为DMU，列为输出指标）
        """
        self.inputs = np.array(inputs, dtype=float)
        self.outputs = np.array(outputs, dtype=float)
        self.n_dmu = self.inputs.shape[0]
        self.n_input = self.inputs.shape[1]
        self.n_output = self.outputs.shape[1]
    
    def ccr_model(self, dmu_idx):
        """CCR模型求解单个DMU效率"""
        # 目标函数：最大化输出加权和
        c = np.zeros(self.n_input + self.n_output)
        c[self.n_input:] = -self.outputs[dmu_idx]  # 负号因为linprog是最小化
        
        # 约束：输入加权和=1
        A_eq = np.zeros((1, self.n_input + self.n_output))
        A_eq[0, :self.n_input] = self.inputs[dmu_idx]
        b_eq = [1]
        
        # 约束：输出加权和 - 输入加权和 <= 0
        A_ub = np.zeros((self.n_dmu, self.n_input + self.n_output))
        for j in range(self.n_dmu):
            A_ub[j, :self.n_input] = -self.inputs[j]
            A_ub[j, self.n_input:] = self.outputs[j]
        b_ub = np.zeros(self.n_dmu)
        
        # 变量边界
        bounds = [(0, None)] * (self.n_input + self.n_output)
        
        # 求解
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, 
                        bounds=bounds, method='highs')
        
        if result.success:
            efficiency = -result.fun  # 还原为正
            weights = result.x
            return efficiency, weights
        else:
            return None, None
    
    def calculate_all(self):
        """计算所有DMU效率"""
        efficiencies = []
        weights_list = []
        
        for i in range(self.n_dmu):
            eff, w = self.ccr_model(i)
            efficiencies.append(eff)
            weights_list.append(w)
        
        return {
            'efficiencies': np.array(efficiencies),
            'weights': weights_list,
            'efficient_dmus': np.where(np.array(efficiencies) >= 0.9999)[0],
            'inefficient_dmus': np.where(np.array(efficiencies) < 0.9999)[0]
        }
    
    def get_benchmarks(self, inefficient_idx):
        """获取无效DMU的标杆"""
        results = self.calculate_all()
        weights = results['weights'][inefficient_idx]
        
        input_weights = weights[:self.n_input]
        output_weights = weights[self.n_input:]
        
        return {
            'input_weights': input_weights,
            'output_weights': output_weights
        }
```

### 5.3 使用示例

```python
# 输入：学生投入（学习时间、课外辅导、资料费用）
inputs = [
    [100, 20, 50],  # 学生A
    [120, 30, 60],  # 学生B
    [80, 15, 40],   # 学生C
    [150, 40, 80],  # 学生D
]

# 输出：学习成果（成绩、证书数、竞赛获奖）
outputs = [
    [85, 2, 1],  # 学生A
    [92, 3, 2],  # 学生B
    [78, 1, 0],  # 学生C
    [95, 4, 3],  # 学生D
]

# DEA计算
dea = DEA(inputs, outputs)
results = dea.calculate_all()

print("效率值:")
for i, eff in enumerate(results['efficiencies']):
    print(f"  DMU{i+1}: {eff:.4f}")
print(f"有效DMU: {results['efficient_dmus']}")
print(f"无效DMU: {results['inefficient_dmus']}")
```

---

## 六、灰色关联分析

### 6.1 模型原理

**灰色关联分析**：通过比较序列的几何形状相似程度判断关联程度。

**关联系数**：ξᵢ(k) = (min min Δ + ρ max max Δ) / (Δ + ρ max max Δ)

**关联度**：rᵢ = (1/n)×Σξᵢ(k)

### 6.2 完整代码框架

```python
import numpy as np
import pandas as pd

class GreyRelational:
    def __init__(self, reference, compare):
        """
        reference: 参考序列（最优方案）
        compare: 比较序列矩阵（行为方案，列为指标）
        """
        self.reference = np.array(reference, dtype=float)
        self.compare = np.array(compare, dtype=float)
        self.n_samples = self.compare.shape[0]
        self.n_indicators = self.compare.shape[1]
    
    def normalize(self):
        """标准化（均值化）"""
        all_data = np.vstack([self.reference, self.compare])
        mean_vals = all_data.mean(axis=0)
        
        # 避免除零
        mean_vals[mean_vals == 0] = 1
        
        ref_norm = self.reference / mean_vals
        comp_norm = self.compare / mean_vals
        
        return ref_norm, comp_norm
    
    def calculate_deltas(self):
        """计算差序列"""
        ref_norm, comp_norm = self.normalize()
        
        deltas = np.abs(comp_norm - ref_norm)
        return deltas
    
    def calculate_coefficients(self, rho=0.5):
        """计算关联系数"""
        deltas = self.calculate_deltas()
        
        min_delta = deltas.min()
        max_delta = deltas.max()
        
        coefficients = (min_delta + rho * max_delta) / (deltas + rho * max_delta)
        return coefficients
    
    def calculate_relational_degree(self, weights=None, rho=0.5):
        """计算关联度"""
        coefficients = self.calculate_coefficients(rho)
        
        if weights is None:
            weights = np.ones(self.n_indicators) / self.n_indicators
        
        degree = (coefficients * weights).sum(axis=1)
        return degree
    
    def rank(self, weights=None, rho=0.5):
        """排序"""
        degree = self.calculate_relational_degree(weights, rho)
        rank_idx = np.argsort(-degree)
        return rank_idx, degree
```

### 6.3 使用示例

```python
import numpy as np

# 参考序列（最优方案）
reference = [95, 90, 88, 92]  # 最高分、最高出勤等

# 比较序列（各学生）
compare = [
    [85, 90, 88, 75],  # 学生A
    [92, 85, 90, 88],  # 学生B
    [78, 95, 82, 70],  # 学生C
    [95, 88, 96, 92],  # 学生D
]

# 灰色关联分析
gra = GreyRelational(reference, compare)
rank_idx, degree = gra.rank()

print("关联度排序:")
for i, idx in enumerate(rank_idx):
    print(f"  第{i+1}名: 学生{chr(65+idx)}, 关联度={degree[idx]:.4f}")
```

---

## 七、组合赋权法

### 7.1 原理

将主观权重（AHP）和客观权重（熵权法）组合，得到综合权重。

**线性组合**：w = α×w_AHP + (1-α)×w_熵

### 7.2 代码实现

```python
def combined_weights(ahp_weights, entropy_weights, alpha=0.5):
    """
    组合权重
    alpha: AHP权重占比（0-1）
    """
    combined = alpha * ahp_weights + (1 - alpha) * entropy_weights
    return combined / combined.sum()  # 归一化
```

---

## 八、竞赛常见场景

### 8.1 评价类问题

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 方案评价 | AHP + TOPSIS | D001, D005 |
| 效率评价 | DEA | D017, D026 |
| 环境质量评价 | 熵权法 + TOPSIS | D034 |
| 经济发展评价 | 灰色关联 + AHP | C142, C227 |
| 服务质量评价 | AHP + 模糊综合 | B007, B050 |

### 8.2 决策类问题

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 投资决策 | AHP + TOPSIS | C305 |
| 供应商选择 | DEA + 灰色关联 | B195, B196 |
| 人才评价 | AHP + 熵权法 | D033 |

---

## 九、常见问题与解决方案

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| AHP一致性不通过 | 专家判断矛盾 | 调整判断矩阵 |
| 熵权法权重为0 | 指标无变异 | 删除该指标 |
| DEA效率全为1 | DMU太少 | 增加DMU或减少指标 |
| 灰色关联度相同 | 序列太相似 | 增加指标或调整ρ |

---

## 十、参考资源

### 10.1 教材推荐

- 《层次分析法》（许树柏）
- 《灰色系统理论》（邓聚龙）
- 《数据包络分析》（魏权龄）

### 10.2 Python库

- pyDecision：AHP、TOPSIS、VIKOR
- dea：DEA数据包络分析
-灰狼优化算法：灰色关联

### 10.3 检查清单

- [ ] AHP一致性检验通过（CR<0.1）
- [ ] 熵权法处理了零值问题
- [ ] TOPSIS正负理想解正确
- [ ] DEA效率值在[0,1]范围内
- [ ] 灰色关联ρ值选择合理
- [ ] 组合权重归一化
