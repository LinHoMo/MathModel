# 分类算法方法论

> 本文件提供数学建模竞赛中常用的分类算法知识，包括算法选择、特征工程、防错策略和验证方法。

---

## 1. 算法选择决策树

```
分类问题类型识别：
├── 二分类
│   ├── 线性可分 → 逻辑回归/SVM
│   ├── 非线性 → 随机森林/XGBoost
│   └── 不平衡数据 → SMOTE+集成学习
├── 多分类
│   ├── 类别数少(k≤10) → 随机森林/XGBoost
│   └── 类别数多(k>10) → 深度学习
├── 高维稀疏 → SVM/逻辑回归
├── 可解释性要求高 → 决策树/逻辑回归
└── 精度要求高 → XGBoost/Stacking
```

---

## 2. 核心算法详解

### 2.1 逻辑回归 (Logistic Regression)

**方法原理**：
通过Sigmoid函数将线性组合映射到[0,1]概率空间，用于二分类问题。

**模型形式**：
```
P(y=1|x) = 1 / (1 + exp(-(β₀ + β₁x₁ + ... + βₖxₖ)))
```

**适用场景**：
- 二分类问题
- 需要概率输出
- 特征重要性分析
- 线性可分数据

**代码框架**：
```python
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler
import numpy as np

def logistic_regression_model(X, y, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = LogisticRegression(
        penalty='l2', C=1.0, max_iter=1000, random_state=random_state
    )
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    
    print("分类报告:")
    print(classification_report(y_test, y_pred))
    print(f"AUC: {roc_auc_score(y_test, y_prob):.4f}")
    
    # 特征重要性（系数）
    coef = model.coef_[0]
    feature_importance = np.abs(coef) / np.sum(np.abs(coef))
    print("\n特征重要性:")
    for i, imp in enumerate(feature_importance):
        print(f"  特征{i}: {imp:.4f}")
    
    return model, scaler
```

---

### 2.2 决策树 (Decision Tree)

**方法原理**：
递归地将数据划分到子节点，基于信息增益或基尼系数选择最优划分特征。

**适用场景**：
- 可解释性要求高
- 需要可视化决策过程
- 特征类型混合（数值+分类）

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| max_depth | 3-15 | 控制树深度，防止过拟合 |
| min_samples_split | 2-20 | 内部节点分裂最小样本数 |
| min_samples_leaf | 1-10 | 叶节点最小样本数 |
| criterion | gini/entropy | 划分标准 |

**代码框架**：
```python
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

def decision_tree_model(X, y, feature_names=None, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    model = DecisionTreeClassifier(
        max_depth=5, min_samples_split=10, random_state=random_state
    )
    model.fit(X_train, y_train)
    
    print(f"训练准确率: {model.score(X_train, y_train):.4f}")
    print(f"测试准确率: {model.score(X_test, y_test):.4f}")
    
    # 可视化
    plt.figure(figsize=(20, 10))
    plot_tree(model, feature_names=feature_names, filled=True, rounded=True)
    plt.tight_layout()
    
    return model
```

---

### 2.3 随机森林 (Random Forest)

**方法原理**：
基于Bagging思想，训练多棵决策树并综合预测结果，降低过拟合风险。

**适用场景**：
- 分类/回归通用
- 特征重要性分析
- 对噪声和异常值鲁棒
- 无需特征缩放

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| n_estimators | 100-500 | 树的数量 |
| max_depth | 5-20 | 树深度 |
| min_samples_split | 2-10 | 内部节点分裂最小样本数 |
| min_samples_leaf | 1-5 | 叶节点最小样本数 |

**代码框架**：
```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report
import numpy as np

def random_forest_model(X, y, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    model = RandomForestClassifier(
        n_estimators=100, max_depth=10, random_state=random_state, n_jobs=-1
    )
    
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
    print(f"交叉验证: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    print("\n分类报告:")
    print(classification_report(y_test, y_pred))
    
    # 特征重要性
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    print("\n特征重要性:")
    for i in range(min(10, len(importances))):
        print(f"  特征{indices[i]}: {importances[indices[i]]:.4f}")
    
    return model
```

---

### 2.4 支持向量机 (SVM)

**方法原理**：
寻找最大间隔超平面分离不同类别，通过核函数处理非线性问题。

**适用场景**：
- 高维数据
- 样本量适中
- 二分类问题
- 非线性可分（使用核技巧）

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| C | 0.1-100 | 正则化参数 |
| kernel | rbf/linear/poly | 核函数类型 |
| gamma | scale/auto | RBF核宽度 |

**代码框架**：
```python
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

def svm_model(X, y, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    param_grid = {
        'C': [0.1, 1, 10, 100],
        'kernel': ['rbf', 'linear'],
        'gamma': ['scale', 'auto', 0.1, 1]
    }
    
    grid = GridSearchCV(SVC(), param_grid, cv=5, scoring='accuracy', n_jobs=-1)
    grid.fit(X_train_scaled, y_train)
    
    print(f"最佳参数: {grid.best_params_}")
    
    y_pred = grid.predict(X_test_scaled)
    print("\n分类报告:")
    print(classification_report(y_test, y_pred))
    
    return grid.best_estimator_, scaler
```

---

### 2.5 XGBoost

**方法原理**：
梯度提升框架，通过迭代训练弱学习器，每轮拟合之前轮次的残差。

**适用场景**：
- 分类/回归通用
- 精度要求高
- Kaggle竞赛常用
- 特征重要性分析

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| n_estimators | 100-1000 | 树的数量 |
| max_depth | 3-10 | 树深度 |
| learning_rate | 0.01-0.3 | 学习率 |
| subsample | 0.7-0.9 | 行采样比例 |
| colsample_bytree | 0.7-0.9 | 列采样比例 |

**代码框架**：
```python
import xgboost as xgb
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report

def xgboost_model(X, y, random_state=42):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    model = xgb.XGBClassifier(
        n_estimators=100, max_depth=6, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, random_state=random_state,
        use_label_encoder=False, eval_metric='mlogloss'
    )
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    print(f"准确率: {accuracy_score(y_test, y_pred):.4f}")
    print("\n分类报告:")
    print(classification_report(y_test, y_pred))
    
    return model
```

---

## 3. 特征工程

### 3.1 数据预处理

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder

def preprocess_classification_data(df, target_col):
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # 缺失值处理
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())
    
    categorical_cols = X.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        X[col] = X[col].fillna(X[col].mode()[0])
    
    # 编码
    le = LabelEncoder()
    for col in categorical_cols:
        X[col] = le.fit_transform(X[col].astype(str))
    
    # 标准化
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)
    
    return X_scaled, y, scaler
```

### 3.2 类别不平衡处理

```python
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

def handle_imbalance(X, y, method='smote'):
    if method == 'smote':
        sampler = SMOTE(random_state=42)
    elif method == 'undersample':
        sampler = RandomUnderSampler(random_state=42)
    
    X_res, y_res = sampler.fit_resample(X, y)
    return X_res, y_res
```

---

## 4. 模型评估

### 4.1 分类评估指标

```python
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, confusion_matrix,
                             classification_report, roc_curve)
import matplotlib.pyplot as plt

def classification_evaluation(y_true, y_pred, y_prob=None):
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted')
    f1 = f1_score(y_true, y_pred, average='weighted')
    
    print(f"准确率: {accuracy:.4f}")
    print(f"精确率: {precision:.4f}")
    print(f"召回率: {recall:.4f}")
    print(f"F1分数: {f1:.4f}")
    
    if y_prob is not None:
        print(f"AUC: {roc_auc_score(y_true, y_prob):.4f}")
    
    print("\n混淆矩阵:")
    print(confusion_matrix(y_true, y_pred))
```

---

## 5. 常见陷阱与最佳实践

### 5.1 常见陷阱

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| 过拟合 | 训练准确率高，测试低 | 交叉验证/正则化/早停 |
| 类别不平衡 | 少数类预测不准 | SMOTE/加权/调整阈值 |
| 特征选择不当 | 冗余特征影响性能 | 特征重要性/VIF检验 |
| 未标准化 | SVM/逻辑回归效果差 | StandardScaler |
| 数据泄露 | 测试集信息泄露 | 先划分再处理 |

### 5.2 最佳实践

- **数据划分**：使用分层抽样，保持类别比例
- **特征缩放**：SVM、逻辑回归必须标准化
- **交叉验证**：至少5折交叉验证
- **模型对比**：至少对比3种以上算法
- **特征重要性**：分析并报告关键特征

---

## 6. 验证清单

- [ ] 数据划分正确（训练/测试/验证）
- [ ] 标准化仅在训练集上fit
- [ ] 交叉验证分数稳定
- [ ] 过拟合检查（训练/测试差距 < 10%）
- [ ] 类别不平衡已处理（如适用）
- [ ] 混淆矩阵/ROC曲线已绘制
- [ ] 特征重要性已分析
- [ ] 模型可解释性已说明
