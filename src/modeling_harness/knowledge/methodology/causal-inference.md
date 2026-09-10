# 因果推断方法

> 从相关性到因果性，掌握因果推断的核心方法。

---

## 一、因果推断基础

### 1.1 相关性 vs 因果性

| 概念 | 定义 | 示例 |
|------|------|------|
| 相关性 | 两个变量同时变化 | 冰淇淋销量↑ 溺水事故↑ |
| 因果性 | 一个变量导致另一个变化 | 天气热 → 冰淇淋销量↑ |
| 混淆变量 | 同时影响两个变量 | 天气温 → 两者都↑ |

### 1.2 因果推断目标

```
Y do(X): 做干预X对Y的因果效应
P(Y|do(X)): 干预X后的结果分布
E[Y|do(X)]: 干预X后的期望结果
```

### 1.3 因果推断假设

- **SUTVA**: 稳定单元处理值假设
- **可忽略性**: 处理分配与潜在结果独立
- **正性**: 每个单元都有非零概率接受处理
- **一致性**: 实际结果等于潜在结果

---

## 二、因果推断方法

### 2.1 随机实验（RCT）

```python
def randomized_experiment(treatment, outcome):
    """
    随机实验因果推断
    """
    # 随机分配处理
    np.random.shuffle(treatment)
    
    # 计算平均处理效应
    ATE = np.mean(outcome[treatment == 1]) - np.mean(outcome[treatment == 0])
    
    return ATE
```

**优点**: 因果推断的金标准
**缺点**: 成本高、伦理限制

### 2.2 倾向得分匹配（PSM）

```python
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors

def propensity_score_matching(X, treatment, outcome):
    """
    倾向得分匹配
    """
    # 估计倾向得分
    ps_model = LogisticRegression()
    ps_model.fit(X, treatment)
    propensity_scores = ps_model.predict_proba(X)[:, 1]
    
    # 匹配
    treated_idx = np.where(treatment == 1)[0]
    control_idx = np.where(treatment == 0)[0]
    
    matched_outcomes = []
    for t_idx in treated_idx:
        # 找最近的对照
        distances = np.abs(propensity_scores[control_idx] - propensity_scores[t_idx])
        nearest = control_idx[np.argmin(distances)]
        
        # 计算配对效应
        effect = outcome[t_idx] - outcome[nearest]
        matched_outcomes.append(effect)
    
    ATE = np.mean(matched_outcomes)
    return ATE
```

### 2.3 双重差分法（DID）

```python
def difference_in_differences(pre_treatment, post_treatment, 
                              treatment_group, control_group):
    """
    双重差分法
    """
    # 处理组变化
    treatment_diff = post_treatment[treatment_group].mean() - \
                    pre_treatment[treatment_group].mean()
    
    # 对照组变化
    control_diff = post_treatment[control_group].mean() - \
                  pre_treatment[control_group].mean()
    
    # DID估计量
    ATE = treatment_diff - control_diff
    
    return ATE
```

### 2.4 断点回归（RDD）

```python
def regression_discontinuity(X, outcome, threshold):
    """
    断点回归
    """
    # 分组
    below = X < threshold
    above = X >= threshold
    
    # 局部线性回归
    from sklearn.linear_model import LinearRegression
    
    # 阈值以下
    model_below = LinearRegression()
    model_below.fit(X[below].reshape(-1, 1), outcome[below])
    
    # 阈值以上
    model_above = LinearRegression()
    model_above.fit(X[above].reshape(-1, 1), outcome[above])
    
    # 断点处的跳跃
    pred_below = model_below.predict([[threshold]])[0]
    pred_above = model_above.predict([[threshold]])[0]
    
    ATE = pred_above - pred_below
    return ATE
```

### 2.5 工具变量法（IV）

```python
def instrumental_variable(X, Z, outcome):
    """
    工具变量法
    """
    from sklearn.linear_model import LinearRegression
    
    # 第一阶段：X对Z回归
    stage1 = LinearRegression()
    stage1.fit(Z.reshape(-1, 1), X)
    X_hat = stage1.predict(Z.reshape(-1, 1))
    
    # 第二阶段：outcome对X_hat回归
    stage2 = LinearRegression()
    stage2.fit(X_hat.reshape(-1, 1), outcome)
    
    ATE = stage2.coef_[0]
    return ATE
```

---

## 三、因果发现

### 3.1 PC算法

```python
def pc_algorithm(data, alpha=0.05):
    """
    PC算法：因果发现
    """
    from scipy.stats import pearsonr
    
    n_vars = data.shape[1]
    adj_matrix = np.ones((n_vars, n_vars), dtype=bool)
    
    # 阶段1：条件独立性测试
    for i in range(n_vars):
        for j in range(i+1, n_vars):
            # 计算偏相关
            corr, p_value = pearsonr(data[:, i], data[:, j])
            if p_value > alpha:
                adj_matrix[i, j] = False
                adj_matrix[j, i] = False
    
    # 阶段2：定向边
    # ...
    
    return adj_matrix
```

### 3.2 因果图可视化

```python
def visualize_causal_graph(adj_matrix, var_names):
    """
    可视化因果图
    """
    import matplotlib.pyplot as plt
    import networkx as nx
    
    G = nx.DiGraph()
    
    for i in range(len(var_names)):
        for j in range(len(var_names)):
            if adj_matrix[i, j]:
                G.add_edge(var_names[i], var_names[j])
    
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=2000, font_size=10, arrows=True)
    
    plt.title("Causal Graph")
    plt.savefig('figures/causal_graph.png', dpi=150, bbox_inches='tight')
    plt.show()
```

---

## 四、论文写作要点

### 4.1 问题分析框架
1. **因果问题定义**: 明确干预和结果
2. **识别策略**: 选择合适的因果推断方法
3. **假设验证**: 检验关键假设
4. **稳健性检验**: 多种方法对比

### 4.2 图表规范
- **因果图**: 节点+有向边
- **平行趋势图**: DID假设验证
- **断点图**: RDD可视化
- **匹配平衡表**: PSM效果

### 4.3 LaTeX代码
```latex
\begin{equation}
ATE = E[Y|do(X=1)] - E[Y|do(X=0)]
\label{eq:ate}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{causal_graph.pdf}
\caption{因果图}
\label{fig:causal}
\end{figure}
```

---

## 五、参考文献

1. Pearl J. Causality. Cambridge University Press, 2009.
2. Imbens G W. Causal Inference for Statistics. Cambridge University Press, 2015.
3. Rubin D B. Causal Inference Using Potential Outcomes. JASA, 2005.
4. Angrist J D. Mostly Harmless Econometrics. Princeton University Press, 2009.
