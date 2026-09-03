# 建筑方案综合评价知识库

> 本文件提供数学建模竞赛中建筑方案综合评价相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 多准则建筑设计方案评价
- 方案比选与排序
- 利益相关者偏好分析
- 建筑功能与美观平衡
- 成本效益综合评估

### 1.2 常见约束条件
- 功能约束：面积、层数、用途
- 经济约束：造价、运营成本
- 美学约束：风格、协调性
- 安全约束：结构安全、消防
- 环境约束：节能、采光、通风

### 1.3 数据特点
- 定性指标：美观度、舒适度、协调性
- 定量指标：面积、造价、能耗
- 评分数据：专家打分、用户满意度
- 权重数据：各指标相对重要性

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 层次分析法(AHP) | 多准则决策 | 结构清晰、可解释性强 | 主观性较强 |
| 模糊综合评价 | 模糊指标评价 | 处理不确定性 | 隶属函数确定困难 |
| TOPSIS | 方案排序 | 客观、计算简单 | 需要标准化数据 |
| 熵权法 | 客观赋权 | 无需主观判断 | 忽略专家经验 |
| 数据包络分析(DEA) | 效率评价 | 无需预设权重 | 对数据要求高 |
| 灰色关联分析 | 方案优选 | 适合小样本 | 分辨系数选取主观 |

---

## 3. 数学基础

### 3.1 层次分析法(AHP)

**判断矩阵构建**：
```
A = [aᵢⱼ]ₙₓₙ
aᵢⱼ = 1/aⱼᵢ, aᵢᵢ = 1
```

1-9标度含义：
- 1: 同等重要
- 3: 稍微重要
- 5: 明显重要
- 7: 强烈重要
- 9: 极端重要

**权重计算（特征向量法）**：
```
Aw = λ_max · w
```

**一致性检验**：
```
CI = (λ_max - n) / (n - 1)
CR = CI / RI
```

RI值（平均随机一致性指标）：
| n | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| RI | 0 | 0 | 0.58 | 0.90 | 1.12 | 1.24 | 1.32 | 1.41 | 1.45 |

**判断标准**：CR < 0.1 则判断矩阵通过一致性检验。

### 3.2 模糊综合评价

**因素集**：U = {u₁, u₂, ..., uₙ}
**评语集**：V = {v₁, v₂, ..., vₘ}

**模糊关系矩阵**：
```
R = [rᵢⱼ]ₙₓₘ
rᵢⱼ = μ(uᵢ, vⱼ)
```

**综合评价向量**：
```
B = W · R
```

其中W为权重向量，B为评价结果向量。

### 3.3 TOPSIS法

**标准化矩阵**：
```
rᵢⱼ = xᵢⱼ / √(Σᵢ xᵢⱼ²)
```

**加权标准化矩阵**：
```
vᵢⱼ = wⱼ · rᵢⱼ
```

**理想解**：
```
A⁺ = {max(v₁ⱼ), max(v₂ⱼ), ...} (效益型)
A⁻ = {min(v₁ⱼ), min(v₂ⱼ), ...} (成本型)
```

**距离计算**：
```
D⁺ᵢ = √(Σⱼ (vᵢⱼ - v⁺ⱼ)²)
D⁻ᵢ = √(Σⱼ (vᵢⱼ - v⁻ⱼ)²)
```

**相对贴近度**：
```
Cᵢ = D⁻ᵢ / (D⁺ᵢ + D⁻ᵢ)
```

### 3.4 熵权法

**信息熵**：
```
eⱼ = -k · Σᵢ pᵢⱼ · ln(pᵢⱼ)
```

其中k = 1/ln(n)，pᵢⱼ = xᵢⱼ / Σᵢ xᵢⱼ

**差异系数**：
```
dⱼ = 1 - eⱼ
```

**熵权**：
```
wⱼ = dⱼ / Σⱼ dⱼ
```

---

## 4. 代码实现

### 4.1 层次分析法(AHP)

```python
import numpy as np

class AHP:
    """
    层次分析法
    """
    def __init__(self, criteria, alternatives=None):
        """
        Parameters
        ----------
        criteria : list
            准则层名称
        alternatives : list
            方案层名称
        """
        self.criteria = criteria
        self.n_criteria = len(criteria)
        self.alternatives = alternatives
    
    def create_comparison_matrix(self, comparisons):
        """
        创建判断矩阵
        
        Parameters
        ----------
        comparisons : list of tuples
            比较结果 [(i, j, value), ...]
        """
        n = self.n_criteria
        matrix = np.eye(n)
        
        for i, j, value in comparisons:
            matrix[i, j] = value
            matrix[j, i] = 1 / value
        
        return matrix
    
    def calculate_weights(self, matrix):
        """
        计算权重（特征向量法）
        
        Returns
        -------
        weights : array
            权重向量
        lambda_max : float
            最大特征值
        CI : float
            一致性指标
        CR : float
            一致性比率
        """
        n = matrix.shape[0]
        
        # 计算特征值和特征向量
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        
        # 最大特征值
        max_idx = np.argmax(eigenvalues.real)
        lambda_max = eigenvalues[max_idx].real
        
        # 特征向量
        eigenvector = eigenvectors[:, max_idx].real
        weights = eigenvector / np.sum(eigenvector)
        
        # 一致性检验
        CI = (lambda_max - n) / (n - 1)
        
        # RI值
        RI_table = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 
                    6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}
        RI = RI_table.get(n, 1.45)
        
        CR = CI / RI if RI > 0 else 0
        
        return weights, lambda_max, CI, CR
    
    def consistency_check(self, matrix, threshold=0.1):
        """
        一致性检验
        """
        weights, lambda_max, CI, CR = self.calculate_weights(matrix)
        
        print(f"最大特征值 λ_max = {lambda_max:.4f}")
        print(f"一致性指标 CI = {CI:.4f}")
        print(f"一致性比率 CR = {CR:.4f}")
        
        if CR < threshold:
            print("✓ 通过一致性检验")
            return True, weights
        else:
            print("✗ 未通过一致性检验，请调整判断矩阵")
            return False, weights
    
    def calculate_sub_criteria_weights(self, main_matrix, sub_matrices):
        """
        计算子准则层权重
        """
        main_weights, _, _, _ = self.calculate_weights(main_matrix)
        
        sub_weights = []
        for sub_matrix in sub_matrices:
            weights, _, _, _ = self.calculate_weights(sub_matrix)
            sub_weights.append(weights)
        
        # 综合权重
        total_weights = np.zeros(sum(m.shape[0] for m in sub_matrices))
        idx = 0
        for i, sub_weight in enumerate(sub_weights):
            n = len(sub_weight)
            total_weights[idx:idx+n] = main_weights[i] * sub_weight
            idx += n
        
        return total_weights
```

### 4.2 模糊综合评价

```python
import numpy as np

class FuzzyComprehensiveEvaluation:
    """
    模糊综合评价
    """
    def __init__(self, factors, comments):
        """
        Parameters
        ----------
        factors : list
            因素集
        comments : list
            评语集
        """
        self.factors = factors
        self.comments = comments
        self.n_factors = len(factors)
        self.n_comments = len(comments)
    
    def create_membership_matrix(self, data):
        """
        创建隶属度矩阵
        
        Parameters
        ----------
        data : array
            评价数据 (n_factors, n_samples)
        
        Returns
        -------
        R : array
            隶属度矩阵 (n_factors, n_comments)
        """
        R = np.zeros((self.n_factors, self.n_comments))
        
        for i in range(self.n_factors):
            # 使用模糊统计法计算隶属度
            counts = np.zeros(self.n_comments)
            for value in data[i]:
                # 根据值的大小分配隶属度
                if value <= 0.2:
                    counts[0] += 1
                elif value <= 0.4:
                    counts[1] += 1
                elif value <= 0.6:
                    counts[2] += 1
                elif value <= 0.8:
                    counts[3] += 1
                else:
                    counts[4] += 1
            
            R[i] = counts / np.sum(counts)
        
        return R
    
    def trapezoidal_membership(self, x, a, b, c, d):
        """
        梯形隶属函数
        
        Parameters
        ----------
        x : float
            输入值
        a, b, c, d : float
            梯形参数
        """
        if x <= a or x >= d:
            return 0
        elif a < x <= b:
            return (x - a) / (b - a) if b != a else 1
        elif b < x <= c:
            return 1
        else:
            return (d - x) / (d - c) if d != c else 1
    
    def triangular_membership(self, x, a, b, c):
        """
        三角形隶属函数
        """
        if x <= a or x >= c:
            return 0
        elif a < x <= b:
            return (x - a) / (b - a) if b != a else 1
        else:
            return (c - x) / (c - b) if c != b else 1
    
    def comprehensive_evaluation(self, weights, R, method='weighted_average'):
        """
        综合评价
        
        Parameters
        ----------
        weights : array
            权重向量
        R : array
            隶属度矩阵
        method : str
            评价方法
        
        Returns
        -------
        B : array
            评价结果向量
        """
        if method == 'weighted_average':
            # 加权平均型
            B = np.dot(weights, R)
        elif method == 'max_min':
            # 主因素决定型
            B = np.zeros(self.n_comments)
            for j in range(self.n_comments):
                B[j] = np.max(np.minimum(weights, R[:, j]))
        elif method == 'max_product':
            # 主因素突出型
            B = np.zeros(self.n_comments)
            for j in range(self.n_comments):
                B[j] = np.max(weights * R[:, j])
        
        return B
    
    def defuzzification(self, B, method='centroid'):
        """
        去模糊化
        
        Parameters
        ----------
        B : array
            评价结果向量
        method : str
            去模糊化方法
        """
        if method == 'centroid':
            # 重心法
            x = np.linspace(0, 1, self.n_comments)
            return np.sum(x * B) / np.sum(B)
        elif method == 'max_membership':
            # 最大隶属度法
            return np.argmax(B)
        elif method == 'weighted_average':
            # 加权平均法
            x = np.linspace(0, 1, self.n_comments)
            return np.sum(x * B)
    
    def classify_result(self, B):
        """
        评价结果分级
        """
        max_idx = np.argmax(B)
        grade = self.comments[max_idx]
        
        # 计算置信度
        confidence = B[max_idx]
        
        return grade, confidence
```

### 4.3 TOPSIS法

```python
import numpy as np

class TOPSIS:
    """
    TOPSIS法（逼近理想解排序法）
    """
    def __init__(self, decision_matrix, weights, criteria_types):
        """
        Parameters
        ----------
        decision_matrix : array
            决策矩阵 (n_alternatives, n_criteria)
        weights : array
            权重向量
        criteria_types : list
            准则类型 ('benefit' or 'cost')
        """
        self.matrix = np.array(decision_matrix)
        self.weights = np.array(weights)
        self.types = criteria_types
        
        self.n_alternatives, self.n_criteria = self.matrix.shape
    
    def normalize(self):
        """
        标准化矩阵
        """
        norm_matrix = np.zeros_like(self.matrix, dtype=float)
        
        for j in range(self.n_criteria):
            col = self.matrix[:, j]
            norm_matrix[:, j] = col / np.sqrt(np.sum(col**2))
        
        return norm_matrix
    
    def weight_normalize(self):
        """
        加权标准化矩阵
        """
        norm_matrix = self.normalize()
        weighted_matrix = norm_matrix * self.weights
        
        return weighted_matrix
    
    def ideal_solutions(self):
        """
        计算正负理想解
        """
        weighted_matrix = self.weight_normalize()
        
        ideal_pos = np.zeros(self.n_criteria)
        ideal_neg = np.zeros(self.n_criteria)
        
        for j in range(self.n_criteria):
            if self.types[j] == 'benefit':
                ideal_pos[j] = np.max(weighted_matrix[:, j])
                ideal_neg[j] = np.min(weighted_matrix[:, j])
            else:
                ideal_pos[j] = np.min(weighted_matrix[:, j])
                ideal_neg[j] = np.max(weighted_matrix[:, j])
        
        return ideal_pos, ideal_neg
    
    def distance_calculation(self):
        """
        计算各方案到正负理想解的距离
        """
        weighted_matrix = self.weight_normalize()
        ideal_pos, ideal_neg = self.ideal_solutions()
        
        dist_pos = np.sqrt(np.sum((weighted_matrix - ideal_pos)**2, axis=1))
        dist_neg = np.sqrt(np.sum((weighted_matrix - ideal_neg)**2, axis=1))
        
        return dist_pos, dist_neg
    
    def relative_closeness(self):
        """
        计算相对贴近度
        """
        dist_pos, dist_neg = self.distance_calculation()
        
        closeness = dist_neg / (dist_pos + dist_neg)
        
        return closeness
    
    def ranking(self):
        """
        方案排序
        """
        closeness = self.relative_closeness()
        ranking = np.argsort(closeness)[::-1]
        
        return ranking, closeness
    
    def get_results(self):
        """
        获取完整结果
        """
        ranking, closeness = self.ranking()
        
        results = []
        for rank, idx in enumerate(ranking):
            results.append({
                'rank': rank + 1,
                'alternative': idx,
                'closeness': closeness[idx]
            })
        
        return results
```

### 4.4 综合评价示例

```python
import numpy as np

def building_evaluation_example():
    """
    建筑方案综合评价示例
    """
    # 定义准则和权重
    criteria = ['功能性', '美观性', '经济性', '安全性', '环保性']
    
    # 判断矩阵
    comparison_data = [
        (0, 1, 2),   # 功能性 vs 美观性
        (0, 2, 3),   # 功能性 vs 经济性
        (0, 3, 1),   # 功能性 vs 安全性
        (0, 4, 2),   # 功能性 vs 环保性
        (1, 2, 2),   # 美观性 vs 经济性
        (1, 3, 1/2), # 美观性 vs 安全性
        (1, 4, 1),   # 美观性 vs 环保性
        (2, 3, 1/3), # 经济性 vs 安全性
        (2, 4, 1/2), # 经济性 vs 环保性
        (3, 4, 2),   # 安全性 vs 环保性
    ]
    
    # 创建AHP实例
    ahp = AHP(criteria)
    matrix = ahp.create_comparison_matrix(comparison_data)
    
    # 一致性检验
    passed, weights = ahp.consistency_check(matrix)
    
    if not passed:
        print("请调整判断矩阵")
        return
    
    # 方案评价数据（3个方案，5个准则）
    alternatives = ['方案A', '方案B', '方案C']
    scores = np.array([
        [0.85, 0.70, 0.90, 0.95, 0.80],  # 方案A
        [0.75, 0.85, 0.80, 0.90, 0.85],  # 方案B
        [0.90, 0.75, 0.70, 0.85, 0.90],  # 方案C
    ])
    
    # TOPSIS评价
    criteria_types = ['benefit'] * 5  # 所有准则都是效益型
    topsis = TOPSIS(scores, weights, criteria_types)
    results = topsis.get_results()
    
    print("\nTOPSIS评价结果：")
    for result in results:
        print(f"第{result['rank']}名: 方案{alternatives[result['alternative']]} "
              f"(贴近度: {result['closeness']:.4f})")
    
    # 模糊综合评价
    fuzzy = FuzzyComprehensiveEvaluation(criteria, ['优', '良', '中', '差', '劣'])
    
    # 创建隶属度矩阵
    R = np.array([
        [0.3, 0.4, 0.2, 0.1, 0.0],  # 功能性
        [0.2, 0.3, 0.3, 0.1, 0.1],  # 美观性
        [0.4, 0.3, 0.2, 0.1, 0.0],  # 经济性
        [0.5, 0.3, 0.1, 0.1, 0.0],  # 安全性
        [0.3, 0.4, 0.2, 0.1, 0.0],  # 环保性
    ])
    
    B = fuzzy.comprehensive_evaluation(weights, R)
    grade, confidence = fuzzy.classify_result(B)
    
    print(f"\n模糊综合评价结果：{grade} (置信度: {confidence:.2%})")
    
    return weights, results, B
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 判断矩阵不一致 | CR > 0.1 | 调整判断值或使用修正算法 |
| 权重归一化错误 | 权重和≠1 | 确保权重向量归一化 |
| 指标类型混淆 | 优劣判断错误 | 明确区分效益型和成本型 |
| 隶属函数选取不当 | 评价结果失真 | 使用多种隶属函数对比 |
| 标准化方法错误 | 结果偏差 | 使用正确的标准化公式 |
| 忽略定性指标 | 评价不全面 | 将定性指标量化处理 |

---

## 6. 验证方法

### 6.1 一致性验证
- AHP判断矩阵CR < 0.1
- 检查矩阵元素是否满足互反性
- 验证特征向量计算正确

### 6.2 结果验证
- 与专家评价结果对比
- 检查排序结果是否合理
- 验证贴近度在[0,1]范围内

### 6.3 敏感性分析
- 改变权重，观察排序变化
- 调整评价标准，检验结果稳定性
- 分析关键影响因素

### 6.4 稳健性分析
- 使用不同评价方法对比
- 改变样本量，检验结果一致性
- 分析极端情况下的表现

---

## 7. 真题案例

### 2010D 宿舍设计评价

**题目概述**：评价不同宿舍设计方案的优劣，考虑功能、美观、经济、安全、环保等多个因素。

**关键信息**：
- 多个设计方案
- 多个评价指标
- 需要综合排序

**解题思路**：
1. 建立评价指标体系
2. 使用AHP确定指标权重
3. 采用TOPSIS或模糊综合评价进行方案排序
4. 进行敏感性分析
5. 提出推荐方案

**参考代码框架**：
```python
# 2010D问题求解框架
# 1. 定义指标体系
criteria = ['面积', '采光', '通风', '造价', '美观']

# 2. 构建判断矩阵
comparison_data = [...]
matrix = create_comparison_matrix(comparison_data)

# 3. AHP权重计算
weights, lambda_max, CI, CR = calculate_weights(matrix)

# 4. 方案评价
scores = np.array([...])  # 方案评分

# 5. TOPSIS排序
topsis = TOPSIS(scores, weights, ['benefit']*5)
results = topsis.get_results()
```

---

## 8. 参考文献

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| 2010D-A01 | AHP+模糊评价 | 主客观结合 |
| 2010D-A02 | TOPSIS+熵权 | 客观赋权 |
| 2010D-A03 | DEA+灰色关联 | 效率分析 |

---

## 9. 验证清单

- [ ] AHP判断矩阵CR < 0.1
- [ ] 权重向量归一化（和为1）
- [ ] 指标类型明确区分
- [ ] 隶属度矩阵每行和为1
- [ ] TOPSIS贴近度在[0,1]范围
- [ ] 评价结果与直觉一致
- [ ] 敏感性分析已执行
- [ ] 不同方法结果对比一致
