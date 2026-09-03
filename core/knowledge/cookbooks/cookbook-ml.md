# Cookbook: 机器学习类模型

> 适用场景：数据驱动、特征→目标映射、预测/分类/聚类/降维。CUMCM C题、MCM C题高频。

---

## 1. 树模型集成 (XGBoost / LightGBM / CatBoost / Random Forest)

| 项目 | 内容 |
|------|------|
| **适用场景** | 表格数据、特征工程丰富、非线性强、解释性要求中等；回归/分类/排序 |
| **核心优势** | 开箱即用强、处理缺失值自带、特征重要性直观、并行训练快 |
| **关键超参数** | `n_estimators`(100-2000), `max_depth`(3-12), `learning_rate`(0.01-0.3), `subsample`(0.6-1.0), `colsample_bytree`(0.6-1.0), `reg_alpha/lambda`(L1/L2) |
| **代码模板** | `core/Programmer/knowledge/code-templates/ml/xgboost_template.py`, `lgbm_template.py`, `rf_template.py` |
| **调优策略** | Optuna/BayesSearchCV → 先调学习率+树数 → 再调深度+正则 → 最后调采样 |
| **常见坑** | 1) 过拟合 → 降深度/增正则/早停<br>2) 类别不平衡 → `scale_pos_weight`/分层采样/阈值调整<br>3) 类别特征 → CatBoost 原生/Target Encoding/One-hot<br>4) 时间序列泄露 → 严格时间序列 CV (Expanding/Sliding Window) |
| **验证清单** | ✅ CV 分数稳定 (CV≤5%) ✅ 训练/验证差距小 ✅ 特征重要性合理 ✅ 残差无模式 ✅ SHAP 解释自洽 |
| **文献支撑示例** | [1] CUMCM2023C 国一：XGBoost + 滞后特征 + 滚动预测<br>[2] MCM2024C O奖：LightGBM + 时序特征工程 + 集成 |

---

## 2. 深度学习 (MLP / CNN / RNN-LSTM-GRU / Transformer / Temporal Fusion Transformer)

| 架构 | 适用场景 | 关键设计 | 代码模板 |
|------|----------|----------|----------|
| **MLP** | 定长特征向量、非线性回归/分类 | 层数2-5、宽度64-512、Dropout/BN、残差 | `mlp_template.py` |
| **CNN** | 局部相关性强 (图像/一维信号/时序局部模式) | 1D Conv、核3/5/7、池化、扩张卷积 | `cnn1d_template.py` |
| **LSTM/GRU** | 变长序列、长程依赖、单向/双向 | 隐层64-256、层数1-3、Dropout、Attention可选 | `lstm_template.py`, `gru_template.py` |
| **Transformer** | 长序列、并行训练、多头自注意力 | d_model 64-512、heads 4-8、层数2-6、位置编码 | `transformer_template.py` |
| **TFT** | 多变量时序、可解释、静态/动态协变量 | 变量选择门控、时间注意力、分位数回归 | `tft_template.py` (PyTorch Forecasting) |

**通用关键超参数**：`batch_size`(32-256), `lr`(1e-4-1e-2), `weight_decay`(1e-5-1e-3), `early_stopping`(patience 10-30), `gradient_clip`(1.0)

**常见坑**：
1. 样本量小 → 迁移学习/预训练/数据增强/简化模型
2. 梯度消失/爆炸 → 梯度裁剪/层归一化/残差/更好初始化
3. 过拟合 → Dropout/Weight Decay/Label Smoothing/Early Stopping/数据增强
4. 时间序列 CV 必须 **Expanding Window** 或 **Sliding Window**，严禁随机 K-Fold

**验证清单**：✅ 训练/验证曲线收敛 ✅ 多种子稳定 (CV≤10%) ✅ 测试集泛化 ✅ 预测区间校准 (若输出分位数) ✅ 计算资源可控

---

## 3. 经典机器学习 (SVM / KNN / 朴素贝叶斯 / 逻辑回归 / 线性判别)

| 算法 | 适用场景 | 关键参数 | 代码模板 |
|------|----------|----------|----------|
| **SVM/SVR** | 中小样本、高维、核技巧 | `C`(0.1-100), `kernel`(rbf/linear/poly), `gamma`(scale/auto) | `svm_template.py` |
| **KNN** | 基线、局部模式、可解释 | `n_neighbors`(3-20), `weights`(uniform/distance), `metric` | `knn_template.py` |
| **Logistic/Linear** | 基线、可解释、概率校准 | `C`, `penalty`(l1/l2/elasticnet), `solver` | `linear_template.py` |

**常见坑**：SVM 标度敏感 → 必须 StandardScaler；KNN 维度灾难 → PCA/特征选择。

---

## 4. 无监督 / 自监督 (K-Means / DBSCAN / GMM / 层次聚类 / 谱聚类 / 密度峰值 / 对比学习)

| 算法 | 适用场景 | 关键参数 | 代码模板 |
|------|----------|----------|----------|
| **K-Means** | 球状簇、K已知、大规模 | `n_clusters`, `n_init`(10+), `k-means++` 初始化 | `kmeans_template.py` |
| **DBSCAN** | 任意形状、噪声鲁棒、密度可分 | `eps`, `min_samples`(≥维度+1) | `dbscan_template.py` |
| **GMM** | 概率簇、椭球形状、软分配 | `n_components`, `covariance_type`(full/tied/diag/spherical) | `gmm_template.py` |
| **层次聚类** | 树形结构、无需预设K、可视化 | `linkage`(ward/complete/average), `distance_threshold` | `hierarchical_template.py` |
| **谱聚类** | 非凸簇、流形结构 | `n_clusters`, `affinity`(rbf/nearest_neighbors), `n_neighbors` | `spectral_template.py` |

**评价指标**：轮廓系数、Calinski-Harabasz、Davies-Bouldin、ARI/NMI (有真标签时)。

---

## 5. 降维 / 特征工程 (PCA / t-SNE / UMAP / 自编码器 / 因子分析 / 目标编码)

| 方法 | 用途 | 代码模板 |
|------|------|----------|
| **PCA** | 线性降维、去噪、可视化 | `pca_template.py` |
| **t-SNE/UMAP** | 非线性可视化 (仅可视化，不可作特征) | `tsne_template.py`, `umap_template.py` |
| **自编码器** | 非线性压缩、特征学习、异常检测 | `autoencoder_template.py` |
| **Target Encoding** | 高基数类别特征 → 数值 | `target_encoding.py` (平滑/留一法防泄露) |

---

## 6. 模型解释与不确定性量化

| 需求 | 方法 | 代码模板 |
|------|------|----------|
| **全局特征重要性** | SHAP (TreeSHAP/KernelSHAP), Permutation Importance | `shap_analysis.py` |
| **局部解释** | SHAP force/waterfall, LIME, 反事实 | `local_explain.py` |
| **预测区间** | Quantile Regression, Conformal Prediction, MC Dropout, Ensemble 分位数 | `prediction_interval.py` |
| **校准** | Platt Scaling, Isotonic Regression, Temperature Scaling | `calibration.py` |

---

## 7. 代码模板目录映射

```
core/Programmer/knowledge/code-templates/ml/
├── xgboost_template.py
├── lgbm_template.py
├── rf_template.py
├── mlp_template.py
├── cnn1d_template.py
├── lstm_template.py
├── gru_template.py
├── transformer_template.py
├── tft_template.py
├── svm_template.py
├── knn_template.py
├── linear_template.py
├── kmeans_template.py
├── dbscan_template.py
├── gmm_template.py
├── hierarchical_template.py
├── spectral_template.py
├── pca_template.py
├── tsne_template.py
├── umap_template.py
├── autoencoder_template.py
├── target_encoding.py
├── shap_analysis.py
├── local_explain.py
├── prediction_interval.py
└── calibration.py
```

---

## 8. 选型决策树 (ML类)

```
数据类型？
├─ 表格/结构化 → 样本量？
│   ├─ <1000 → 线性/树模型(RF/XGB) → 首选
│   └─ ≥1000 → XGBoost/LightGBM/CatBoost → 首选
├─ 时序/序列 → 预测步长？
│   ├─ 短期(≤30) → LSTM/GRU/Transformer/TFT → 首选
│   └─ 长期/多步 → TFT/Transformer + 递归/直接多步 → 首选
├─ 图像/信号 → CNN/Transformer → 首选
├─ 文本/NLP → Transformer/BERT/预训练 → 首选
└─ 无标签/探索 → 聚类/降维 → 按形状选 K-Means/DBSCAN/GMM
```

**铁律**：
- 时序问题 **严禁随机 K-Fold**，必须 Expanding/Sliding Window CV
- 所有模型 **必须报告多种子稳定性 (CV≤10%)**
- 竞赛论文 **必须给出 SHAP/特征重要性解释**，黑盒不可接受
- 预测问题 **必须给出预测区间**，而非仅点预测

---

## 9. 竞赛实战提示

| 竞赛 | 题型 | 推荐首选 | 避坑指南 |
|------|------|----------|----------|
| CUMCM C | 数据/预测 | XGBoost/LightGBM + 时序CV | 滞后特征防泄露、滚动验证 |
| MCM C | 大数据/预测 | TFT/Transformer + 集成 | 显性化不确定性、分位数回归 |
| 电工杯 | 工程数据 | XGBoost + 物理约束嵌入 | 特征含物理意义、残差分析 |

---

*版本：1.0 | 更新：2026-09-01 | 维护：Modeler 手*