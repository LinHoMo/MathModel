# 机器学习方法论

> 本文件提供数学建模竞赛中常用的机器学习知识，包括模型选择、特征工程、防错策略和验证方法。

---

## 1. 模型选择决策树

```
机器学习任务类型识别：
├── 分类任务（预测类别）
│   ├── 二分类
│   │   ├── 线性可分 → 逻辑回归/SVM
│   │   ├── 非线性 → 随机森林/XGBoost
│   │   └── 不平衡数据 → SMOTE+集成学习
│   └── 多分类
│       ├── 类别数少 → 随机森林/XGBoost
│       └── 类别数多 → 深度学习
├── 回归任务（预测数值）
│   ├── 线性关系 → 线性回归
│   ├── 非线性 → 随机森林/XGBoost
│   └── 时序数据 → LSTM/时序模型
├── 聚类任务（无标签分组）
│   ├── 数据量小 → K-Means
│   ├── 数据量大 → Mini-Batch K-Means
│   ├── 形状复杂 → DBSCAN
│   └── 层次结构 → 层次聚类
└── 降维任务
    ├── 线性降维 → PCA
    └── 非线性降维 → t-SNE/UMAP
```

---

## 2. 核心算法详解

### 2.1 随机森林 (Random Forest)

**适用场景**：分类/回归，特征重要性分析，非线性关系

**优点**：
- 不易过拟合
- 可处理高维数据
- 提供特征重要性
- 对缺失值和异常值鲁棒

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| n_estimators | 100-500 | 树的数量，越大越稳定 |
| max_depth | 5-20 | 树深度，控制过拟合 |
| min_samples_split | 2-10 | 内部节点分裂所需最小样本数 |
| min_samples_leaf | 1-5 | 叶节点最小样本数 |

**代码框架**：
```python
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, mean_squared_error
import numpy as np

def random_forest_model(X, y, task='classification', random_state=42):
    """
    随机森林模型
    task: 'classification' 或 'regression'
    """
    # 划分训练集/测试集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    # 选择模型
    if task == 'classification':
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=random_state,
            n_jobs=-1
        )
    else:
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=random_state,
            n_jobs=-1
        )
    
    # 交叉验证
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy' if task == 'classification' else 'r2')
    print(f"交叉验证分数: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    
    # 训练模型
    model.fit(X_train, y_train)
    
    # 测试集评估
    y_pred = model.predict(X_test)
    if task == 'classification':
        print("\n分类报告:")
        print(classification_report(y_test, y_pred))
    else:
        mse = mean_squared_error(y_test, y_pred)
        print(f"\n测试集MSE: {mse:.4f}")
        print(f"测试集RMSE: {np.sqrt(mse):.4f}")
    
    # 特征重要性
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        print("\n特征重要性:")
        for i in range(min(10, len(importances))):
            print(f"  特征{indices[i]}: {importances[indices[i]]:.4f}")
    
    return model, X_train, X_test, y_train, y_test
```

### 2.2 XGBoost

**适用场景**：分类/回归，Kaggle竞赛常用，高精度预测

**优点**：
- 精度高
- 内置正则化
- 可处理缺失值
- 支持自定义目标函数

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
from sklearn.metrics import accuracy_score, mean_squared_error
import numpy as np

def xgboost_model(X, y, task='classification', random_state=42):
    """
    XGBoost模型
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    if task == 'classification':
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )
    else:
        model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state
        )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    if task == 'classification':
        accuracy = accuracy_score(y_test, y_pred)
        print(f"测试集准确率: {accuracy:.4f}")
    else:
        mse = mean_squared_error(y_test, y_pred)
        print(f"测试集RMSE: {np.sqrt(mse):.4f}")
    
    return model, X_train, X_test, y_train, y_test

def xgboost_hyperparameter_tuning(X, y, task='classification'):
    """
    XGBoost超参数调优
    """
    param_grid = {
        'max_depth': [3, 5, 7, 9],
        'learning_rate': [0.01, 0.05, 0.1, 0.2],
        'n_estimators': [100, 200, 300],
        'subsample': [0.7, 0.8, 0.9],
        'colsample_bytree': [0.7, 0.8, 0.9]
    }
    
    if task == 'classification':
        model = xgb.XGBClassifier(use_label_encoder=False, eval_metric='mlogloss')
        scoring = 'accuracy'
    else:
        model = xgb.XGBRegressor()
        scoring = 'r2'
    
    grid_search = GridSearchCV(
        model, param_grid, cv=5, scoring=scoring, n_jobs=-1, verbose=1
    )
    grid_search.fit(X, y)
    
    print(f"最佳参数: {grid_search.best_params_}")
    print(f"最佳分数: {grid_search.best_score_:.4f}")
    
    return grid_search.best_estimator_
```

### 2.3 K-Means聚类

**适用场景**：无监督聚类，客户分群，数据降维

**优点**：
- 简单快速
- 可扩展性好
- 结果易解释

**关键参数**：
| 参数 | 典型范围 | 影响 |
|------|---------|------|
| n_clusters | 2-10 | 聚类数（需预设） |
| max_iter | 100-300 | 最大迭代次数 |
| n_init | 10-20 | 不同初始化次数 |

**选择聚类数的方法**：
- 肘部法则（Elbow Method）
- 轮廓系数（Silhouette Score）
- Gap Statistic

**代码框架**：
```python
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import matplotlib.pyplot as plt
import numpy as np

def kmeans_clustering(X, max_k=10, random_state=42):
    """
    K-Means聚类分析
    """
    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 肘部法则选择K
    inertias = []
    silhouette_scores = []
    K_range = range(2, max_k + 1)
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
        silhouette_scores.append(silhouette_score(X_scaled, kmeans.labels_))
    
    # 绘制肘部图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    ax1.plot(K_range, inertias, 'bo-')
    ax1.set_xlabel('Number of Clusters (K)')
    ax1.set_ylabel('Inertia')
    ax1.set_title('Elbow Method')
    
    ax2.plot(K_range, silhouette_scores, 'ro-')
    ax2.set_xlabel('Number of Clusters (K)')
    ax2.set_ylabel('Silhouette Score')
    ax2.set_title('Silhouette Analysis')
    
    plt.tight_layout()
    
    # 选择最佳K（轮廓系数最大）
    best_k = K_range[np.argmax(silhouette_scores)]
    print(f"最佳聚类数: {best_k}")
    print(f"最大轮廓系数: {max(silhouette_scores):.4f}")
    
    # 使用最佳K拟合
    kmeans = KMeans(n_clusters=best_k, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(X_scaled)
    
    # 评估指标
    print(f"\n聚类评估:")
    print(f"  轮廓系数: {silhouette_score(X_scaled, labels):.4f}")
    print(f"  Calinski-Harabasz指数: {calinski_harabasz_score(X_scaled, labels):.4f}")
    
    return kmeans, labels, scaler, best_k
```

### 2.4 决策树

**适用场景**：分类/回归，可解释性要求高

**优点**：
- 模型可解释性强
- 不需要特征缩放
- 可处理分类和数值特征

**缺点**：
- 容易过拟合
- 对数据敏感

**代码框架**：
```python
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor, plot_tree
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

def decision_tree_model(X, y, feature_names=None, task='classification', random_state=42):
    """
    决策树模型
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state
    )
    
    if task == 'classification':
        model = DecisionTreeClassifier(max_depth=5, random_state=random_state)
    else:
        model = DecisionTreeRegressor(max_depth=5, random_state=random_state)
    
    model.fit(X_train, y_train)
    
    # 可视化决策树
    plt.figure(figsize=(20, 10))
    plot_tree(model, feature_names=feature_names, filled=True, rounded=True)
    plt.title("Decision Tree Visualization")
    plt.tight_layout()
    
    return model, X_train, X_test, y_train, y_test
```

---

## 3. 特征工程

### 3.1 数据预处理

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder

def data_preprocessing(df, target_col, task='classification'):
    """
    数据预处理流程
    """
    # 1. 分离特征和目标
    X = df.drop(columns=[target_col])
    y = df[target_col]
    
    # 2. 处理缺失值
    # 数值型：中位数填充
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())
    
    # 分类型：众数填充
    categorical_cols = X.select_dtypes(include=['object', 'category']).columns
    for col in categorical_cols:
        X[col] = X[col].fillna(X[col].mode()[0])
    
    # 3. 编码分类变量
    le = LabelEncoder()
    for col in categorical_cols:
        X[col] = le.fit_transform(X[col].astype(str))
    
    # 4. 标准化
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(
        scaler.fit_transform(X), 
        columns=X.columns, 
        index=X.index
    )
    
    return X_scaled, y, scaler
```

### 3.2 特征选择

```python
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from sklearn.ensemble import RandomForestClassifier
import numpy as np

def feature_selection(X, y, method='importance', k=10, task='classification'):
    """
    特征选择
    """
    if method == 'importance':
        # 基于模型的特征重要性
        if task == 'classification':
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        
        model.fit(X, y)
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:k]
        
        selected_features = X.columns[indices].tolist()
        print(f"选择的特征 (Top {k}):")
        for i, idx in enumerate(indices):
            print(f"  {i+1}. {X.columns[idx]}: {importances[idx]:.4f}")
    
    elif method == 'statistical':
        # 统计检验选择
        if task == 'classification':
            selector = SelectKBest(f_classif, k=k)
        else:
            selector = SelectKBest(f_regression, k=k)
        
        selector.fit(X, y)
        selected_mask = selector.get_support()
        selected_features = X.columns[selected_mask].tolist()
        
        print(f"选择的特征 (Top {k}):")
        scores = selector.scores_[selected_mask]
        for i, (feat, score) in enumerate(zip(selected_features, scores)):
            print(f"  {i+1}. {feat}: {score:.4f}")
    
    return selected_features
```

### 3.3 特征构造

```python
def feature_engineering(df):
    """
    特征工程：从原始特征构造新特征
    """
    # 1. 交互特征
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for i in range(len(numeric_cols)):
        for j in range(i+1, len(numeric_cols)):
            col1, col2 = numeric_cols[i], numeric_cols[j]
            df[f'{col1}_x_{col2}'] = df[col1] * df[col2]
    
    # 2. 多项式特征
    from sklearn.preprocessing import PolynomialFeatures
    poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=False)
    poly_features = poly.fit_transform(df[numeric_cols])
    poly_feature_names = poly.get_feature_names_out(numeric_cols)
    
    # 3. 统计特征
    df['numeric_mean'] = df[numeric_cols].mean(axis=1)
    df['numeric_std'] = df[numeric_cols].std(axis=1)
    df['numeric_max'] = df[numeric_cols].max(axis=1)
    df['numeric_min'] = df[numeric_cols].min(axis=1)
    
    return df
```

---

## 4. 模型评估

### 4.1 分类评估

```python
from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                             f1_score, roc_auc_score, confusion_matrix, 
                             classification_report, roc_curve)
import matplotlib.pyplot as plt
import numpy as np

def classification_evaluation(y_true, y_pred, y_prob=None, class_names=None):
    """
    分类模型评估
    """
    # 基本指标
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, average='weighted')
    recall = recall_score(y_true, y_pred, average='weighted')
    f1 = f1_score(y_true, y_pred, average='weighted')
    
    print(f"准确率: {accuracy:.4f}")
    print(f"精确率: {precision:.4f}")
    print(f"召回率: {recall:.4f}")
    print(f"F1分数: {f1:.4f}")
    
    # 混淆矩阵
    cm = confusion_matrix(y_true, y_pred)
    print("\n混淆矩阵:")
    print(cm)
    
    # 分类报告
    print("\n分类报告:")
    print(classification_report(y_true, y_pred, target_names=class_names))
    
    # ROC曲线（二分类）
    if y_prob is not None and len(np.unique(y_true)) == 2:
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        auc = roc_auc_score(y_true, y_prob)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, 'b-', label=f'ROC曲线 (AUC = {auc:.4f})')
        plt.plot([0, 1], [0, 1], 'r--', label='随机猜测')
        plt.xlabel('假正率 (FPR)')
        plt.ylabel('真正率 (TPR)')
        plt.title('ROC曲线')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1
    }
```

### 4.2 回归评估

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

def regression_evaluation(y_true, y_pred):
    """
    回归模型评估
    """
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    
    # MAPE
    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    
    print(f"MSE:  {mse:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAE:  {mae:.4f}")
    print(f"R²:   {r2:.4f}")
    print(f"MAPE: {mape:.2f}%")
    
    return {
        'mse': mse,
        'rmse': rmse,
        'mae': mae,
        'r2': r2,
        'mape': mape
    }
```

### 4.3 聚类评估

```python
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

def clustering_evaluation(X, labels):
    """
    聚类模型评估
    """
    sil_score = silhouette_score(X, labels)
    ch_score = calinski_harabasz_score(X, labels)
    db_score = davies_bouldin_score(X, labels)
    
    print(f"轮廓系数: {sil_score:.4f} (越高越好)")
    print(f"Calinski-Harabasz指数: {ch_score:.4f} (越高越好)")
    print(f"Davies-Bouldin指数: {db_score:.4f} (越低越好)")
    
    return {
        'silhouette': sil_score,
        'calinski_harabasz': ch_score,
        'davies_bouldin': db_score
    }
```

---

## 5. 防错速查表

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| 过拟合 | 训练准确率高，测试准确率低 | 交叉验证/正则化/早停 |
| 欠拟合 | 训练和测试准确率都低 | 增加模型复杂度/特征 |
| 数据泄露 | 测试集信息泄露到训练集 | 先划分再标准化 |
| 类别不平衡 | 少数类预测不准 | SMOTE/加权/调整阈值 |
| 未标准化 | 基于距离的算法失效 | 标准化/归一化 |
| 特征冗余 | 多重共线性 | 特征选择/VIF检验 |
| 外推风险 | 预测超出训练范围 | 声明适用范围 |

---

## 6. 参考论文（来自高教杯优秀论文）

| 论文编号 | 机器学习方法 | 应用场景 | 关键创新 |
|---------|-------------|---------|---------|
| C008 | K-Means+决策树 | 会员画像 | RFMS指标+聚类分群 |
| C052 | K-Means+随机森林 | 会员画像 | 多模型对比+特征重要性 |
| C109 | 决策树+梯度下降 | 信贷风险 | 非线性优化+特征工程 |
| C142 | 随机森林 | 信贷决策 | 类别不平衡处理 |
| C227 | XGBoost | 信贷决策 | 超参数调优+交叉验证 |

---

## 7. 验证清单

- [ ] 数据划分正确（训练/测试/验证）
- [ ] 标准化仅在训练集上fit
- [ ] 交叉验证分数稳定
- [ ] 过拟合检查（训练/测试差距 < 10%）
- [ ] 类别不平衡已处理（如适用）
- [ ] 特征重要性已分析
- [ ] 混淆矩阵/ROC曲线已绘制
- [ ] 模型可解释性已说明
