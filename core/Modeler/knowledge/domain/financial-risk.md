# 信贷决策与风险评估领域知识

## 一、核心概念

### 1.1 信用评分
- **定义**: 量化评估借款人违约风险的数值
- **常用模型**: Logistic回归、决策树、随机森林、XGBoost
- **评估指标**: AUC、KS统计量、Gini系数

### 1.2 违约概率 (PD)
- **定义**: 借款人在未来特定时期内违约的概率
- **计算方法**: 历史违约率、统计模型、机器学习

### 1.3 违约损失率 (LGD)
- **定义**: 违约发生时的损失比例
- **影响因素**: 抵押品价值、回收成本、经济环境

### 1.4 违约敞口 (EAD)
- **定义**: 违约时的敞口金额
- **计算**: 未偿还本金 + 预期提取金额

---

## 二、建模方法

### 2.1 Logistic回归
```
P(default=1) = 1 / (1 + -(β0 + β1*X1 + ... + βn*Xn))
```
**优点**: 可解释性强、系数即 odds ratio
**缺点**: 线性假设、无法处理复杂交互

### 2.2 评分卡模型
```
Score = A - B * ln(odds)
其中:
  A = offset + factor * ln(prior_odds)
  B = factor / ln(odds_ratio)
```

**WOE (Weight of Evidence)**:
```
WOE = ln(Distribution of Events / Distribution of Non-Events)
```

**IV (Information Value)**:
```
IV = Σ(Distribution of Events - Distribution of Non-Events) * WOE
```
- IV < 0.02: 无预测能力
- 0.02 ≤ IV < 0.1: 弱预测能力
- 0.1 ≤ IV < 0.3: 中等预测能力
- IV ≥ 0.3: 强预测能力

### 2.3 XGBoost信用评分
```python
import xgboost as xgb

model = xgb.XGBClassifier(
    objective='binary:logistic',
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    eval_metric='auc'
)
```

### 2.4 集成学习
- **Bagging**: 降低方差
- **Boosting**: 降低偏差
- **Stacking**: 多模型融合

---

## 三、特征工程

### 3.1 常用特征类别

| 类别 | 特征示例 | 说明 |
|------|---------|------|
| 基础信息 | 年龄、收入、教育 | 人口统计学 |
| 信用历史 | 信用记录长度、逾期次数 | 征信数据 |
| 负债情况 | 负债收入比、信用卡使用率 | 还款能力 |
| 行为数据 | 消费习惯、登录频率 | 行为画像 |
| 社交数据 | 社交网络、联系人 | 社交图谱 |

### 3.2 特征处理
```python
# 缺失值处理
df.fillna(df.median(), inplace=True)

# 异常值处理
Q1 = df.quantile(0.25)
Q3 = df.quantile(0.75)
IQR = Q3 - Q1
df = df[(df >= Q1 - 1.5*IQR) & (df <= Q3 + 1.5*IQR)]

# 分箱
pd.cut(df['income'], bins=10, labels=False)

# 标准化
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
```

### 3.3 特征选择
- **过滤法**: 相关系数、卡方检验、互信息
- **包裹法**: 递归特征消除 (RFE)
- **嵌入法**: L1正则化、树模型特征重要性

---

## 四、模型评估

### 4.1 混淆矩阵
```
              预测
              正    负
实际  正    TP    FN
      负    FP    TN
```

### 4.2 评估指标
- **准确率**: (TP + TN) / (TP + TN + FP + FN)
- **精确率**: TP / (TP + FP)
- **召回率**: TP / (TP + FN)
- **F1**: 2 * Precision * Recall / (Precision + Recall)

### 4.3 ROC曲线与AUC
```python
from sklearn.metrics import roc_curve, auc

fpr, tpr, thresholds = roc_curve(y_true, y_scores)
auc_score = auc(fpr, tpr)
```

### 4.4 KS统计量
```
KS = max(|TPR - FPR|)
```
- KS > 0.3: 模型有较好的区分能力
- KS > 0.4: 模型区分能力很好

### 4.5 Gini系数
```
Gini = 2 * AUC - 1
```

---

## 五、风险策略

### 5.1 审批策略
| 风险等级 | 评分范围 | 策略 |
|---------|---------|------|
| 低风险 | > 700 | 自动通过 |
| 中风险 | 600-700 | 人工审核 |
| 高风险 | < 600 | 自动拒绝 |

### 5.2 定价策略
```
利率 = 资金成本 + 运营成本 + 风险溢价 + 利润
```

### 5.3 额度策略
```
额度 = f(收入, 信用评分, 负债率, 历史表现)
```

### 5.4 催收策略
| 逾期天数 | 催收方式 | 优先级 |
|---------|---------|--------|
| 1-7天 | 短信提醒 | 低 |
| 8-30天 | 电话催收 | 中 |
| 31-90天 | 上门催收 | 高 |
| > 90天 | 法律途径 | 最高 |

---

## 六、论文写作要点

### 6.1 问题分析框架
1. **数据理解**: 数据来源、字段含义、缺失情况
2. **探索性分析**: 分布、相关性、异常值
3. **特征工程**: 特征构造、选择、转换
4. **模型选择**: 多模型对比、交叉验证
5. **结果评估**: 指标计算、业务解读
6. **策略建议**: 审批、定价、额度

### 6.2 图表规范
- **ROC曲线**: 标注AUC值、基准线
- **混淆矩阵**: 热力图形式
- **特征重要性**: 水平条形图
- **评分分布**: 分组直方图
- **KS曲线**: 两条曲线+最大差距

### 6.3 LaTeX代码
```latex
% ROC曲线
\begin{figure}[htbp]
\centering
\includegraphics[width=0.6\textwidth]{roc_curve.pdf}
\caption{ROC曲线}
\label{fig:roc}
\end{figure}

% 混淆矩阵
\begin{table}[htbp]
\centering
\caption{混淆矩阵}
\begin{tabular}{c|cc}
\hline
& 预测正 & 预测负 \\
\hline
实际正 & TP & FN \\
实际负 & FP & TN \\
\hline
\end{tabular}
\end{table}
```

---

## 七、常见问题与解决方案

### 7.1 样本不平衡
- **过采样**: SMOTE、ADASYN
- **欠采样**: 随机欠采样、Tomek Links
- **代价敏感学习**: 调整类别权重

### 7.2 特征缺失
- **删除**: 缺失率 > 50%的特征
- **填充**: 均值、中位数、众数、模型预测
- **指示器**: 缺失值本身作为特征

### 7.3 过拟合
- **正则化**: L1、L2
- **交叉验证**: K折交叉验证
- **早停**: 监控验证集性能
- **特征选择**: 减少特征数量

### 7.4 模型解释性
- **SHAP值**: 单样本解释
- **LIME**: 局部可解释模型
- **特征重要性**: 全局解释
- **部分依赖图**: 特征边际效应

---

## 八、参考文献

1. 李航. 统计学习方法. 清华大学出版社, 2012.
2. 周志华. 机器学习. 清华大学出版社, 2016.
3. 托马斯. 信用评分模型技术与应用. 中国金融出版社, 2006.
4. 巴塞尔银行监管委员会. 统一资本计量和资本标准的国际协议, 2004.
