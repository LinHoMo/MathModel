#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
支持向量机(SVM)模型模板
功能：核函数选择、参数优化、决策边界可视化
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.svm import SVC, SVR
from sklearn.model_selection import train_test_split, GridSearchCV, learning_curve
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, classification_report, 
                             confusion_matrix, mean_squared_error, r2_score)
from sklearn.datasets import make_classification, make_moons, make_circles
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class SVMClassifier:
    """SVM分类器封装类"""
    
    def __init__(self, kernel='rbf', C=1.0, gamma='scale', random_state=42):
        """
        初始化SVM分类器
        参数：
            kernel: 核函数 ('linear', 'rbf', 'poly', 'sigmoid')
            C: 正则化参数
            gamma: 核函数系数
            random_state: 随机种子
        """
        self.kernel = kernel
        self.C = C
        self.gamma = gamma
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = None
        self.param_grid = None
    
    def preprocess(self, X_train, X_test):
        """数据标准化预处理"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        return X_train_scaled, X_test_scaled
    
    def train(self, X_train, y_train, optimize_params=False):
        """
        训练模型
        参数：
            X_train: 训练特征
            y_train: 训练标签
            optimize_params: 是否进行参数优化
        """
        if optimize_params:
            # 定义参数网格
            self.param_grid = {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.1, 0.01, 0.001],
                'kernel': ['rbf', 'linear', 'poly']
            }
            
            # 网格搜索
            print("执行参数网格搜索...")
            grid_search = GridSearchCV(
                SVC(random_state=self.random_state),
                self.param_grid,
                cv=5,
                scoring='accuracy',
                n_jobs=-1,
                verbose=0
            )
            
            grid_search.fit(X_train, y_train)
            
            # 使用最佳参数
            self.model = grid_search.best_estimator_
            print(f"最佳参数: {grid_search.best_params_}")
            print(f"最佳交叉验证准确率: {grid_search.best_score_:.4f}")
        else:
            # 直接使用给定参数训练
            self.model = SVC(
                kernel=self.kernel,
                C=self.C,
                gamma=self.gamma,
                random_state=self.random_state,
                probability=True
            )
            self.model.fit(X_train, y_train)
    
    def evaluate(self, X_test, y_test):
        """模型评估"""
        y_pred = self.model.predict(X_test)
        
        results = {
            'accuracy': accuracy_score(y_test, y_pred),
            'classification_report': classification_report(y_test, y_pred),
            'confusion_matrix': confusion_matrix(y_test, y_pred),
            'predictions': y_pred,
            'support_vectors': self.model.support_vectors_,
            'n_support': self.model.n_support_
        }
        
        print(f"测试集准确率: {results['accuracy']:.4f}")
        print(f"支持向量数量: {len(results['support_vectors'])}")
        print("\n分类报告:")
        print(results['classification_report'])
        
        return results
    
    def plot_decision_boundary(self, X, y, title="SVM决策边界"):
        """绘制决策边界"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 对于高维数据，只使用前两个特征
        X_plot = X[:, :2] if X.shape[1] > 2 else X
        
        # 创建网格
        h = 0.02
        x_min, x_max = X_plot[:, 0].min() - 1, X_plot[:, 0].max() + 1
        y_min, y_max = X_plot[:, 1].min() - 1, X_plot[:, 1].max() + 1
        xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                             np.arange(y_min, y_max, h))
        
        # 预测网格点
        Z = self.model.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)
        
        # 绘制决策边界
        axes[0].contourf(xx, yy, Z, alpha=0.3, cmap=plt.cm.coolwarm)
        axes[0].contour(xx, yy, Z, colors='k', linewidths=0.5)
        
        # 绘制数据点
        scatter = axes[0].scatter(X_plot[:, 0], X_plot[:, 1], c=y, 
                                 cmap=plt.cm.coolwarm, edgecolors='k', s=50)
        
        # 绘制支持向量
        sv = self.model.support_vectors_[:, :2] if self.model.support_vectors_.shape[1] > 2 else self.model.support_vectors_
        axes[0].scatter(sv[:, 0], sv[:, 1], s=200, facecolors='none', 
                       edgecolors='black', linewidths=2, label='支持向量')
        
        axes[0].set_title(title)
        axes[0].set_xlabel('特征1')
        axes[0].set_ylabel('特征2')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # 绘制概率分布
        if hasattr(self.model, 'predict_proba'):
            Z_proba = self.model.predict_proba(np.c_[xx.ravel(), yy.ravel()])
            Z_proba = Z_proba[:, 1].reshape(xx.shape)
            
            im = axes[1].contourf(xx, yy, Z_proba, alpha=0.7, cmap=plt.cm.RdYlBu)
            plt.colorbar(im, ax=axes[1])
            
            axes[1].scatter(X_plot[:, 0], X_plot[:, 1], c=y, 
                          cmap=plt.cm.RdYlBu, edgecolors='k', s=50)
            axes[1].set_title('概率分布')
            axes[1].set_xlabel('特征1')
            axes[1].set_ylabel('特征2')
            axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_kernel_comparison(self, X, y):
        """比较不同核函数的决策边界"""
        kernels = ['linear', 'rbf', 'poly', 'sigmoid']
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axes = axes.ravel()
        
        for i, kernel in enumerate(kernels):
            # 创建模型
            svm = SVC(kernel=kernel, C=1.0, gamma='scale', random_state=42)
            svm.fit(X[:, :2], y)
            
            # 创建网格
            h = 0.02
            x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
            y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
            xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                                 np.arange(y_min, y_max, h))
            
            # 预测
            Z = svm.predict(np.c_[xx.ravel(), yy.ravel()])
            Z = Z.reshape(xx.shape)
            
            # 绘制
            axes[i].contourf(xx, yy, Z, alpha=0.3, cmap=plt.cm.coolwarm)
            axes[i].contour(xx, yy, Z, colors='k', linewidths=0.5)
            axes[i].scatter(X[:, 0], X[:, 1], c=y, cmap=plt.cm.coolwarm, 
                          edgecolors='k', s=50)
            
            # 绘制支持向量
            sv = svm.support_vectors_
            axes[i].scatter(sv[:, 0], sv[:, 1], s=200, facecolors='none', 
                          edgecolors='black', linewidths=2)
            
            axes[i].set_title(f'{kernel}核函数')
            axes[i].set_xlabel('特征1')
            axes[i].set_ylabel('特征2')
            axes[i].grid(True, alpha=0.3)
        
        plt.suptitle('不同核函数的SVM决策边界比较', fontsize=14)
        plt.tight_layout()
        plt.show()


class SVMRegressor:
    """SVM回归器封装类"""
    
    def __init__(self, kernel='rbf', C=1.0, gamma='scale', epsilon=0.1):
        """
        初始化SVM回归器
        参数：
            kernel: 核函数
            C: 正则化参数
            gamma: 核函数系数
            epsilon: epsilon-SVR的epsilon参数
        """
        self.kernel = kernel
        self.C = C
        self.gamma = gamma
        self.epsilon = epsilon
        self.scaler = StandardScaler()
        self.model = None
    
    def preprocess(self, X_train, X_test):
        """数据标准化预处理"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        return X_train_scaled, X_test_scaled
    
    def train(self, X_train, y_train, optimize_params=False):
        """训练模型"""
        if optimize_params:
            param_grid = {
                'C': [0.1, 1, 10, 100],
                'gamma': ['scale', 'auto', 0.1, 0.01],
                'epsilon': [0.01, 0.1, 0.2, 0.5],
                'kernel': ['rbf', 'linear']
            }
            
            grid_search = GridSearchCV(
                SVR(),
                param_grid,
                cv=5,
                scoring='neg_mean_squared_error',
                n_jobs=-1
            )
            
            grid_search.fit(X_train, y_train)
            self.model = grid_search.best_estimator_
            
            print(f"最佳参数: {grid_search.best_params_}")
            print(f"最佳MSE: {-grid_search.best_score_:.4f}")
        else:
            self.model = SVR(
                kernel=self.kernel,
                C=self.C,
                gamma=self.gamma,
                epsilon=self.epsilon
            )
            self.model.fit(X_train, y_train)
    
    def evaluate(self, X_test, y_test):
        """模型评估"""
        y_pred = self.model.predict(X_test)
        
        results = {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred),
            'predictions': y_pred,
            'support_vectors': self.model.support_vectors_,
            'n_support': self.model.n_support_
        }
        
        print(f"均方误差 (MSE): {results['mse']:.4f}")
        print(f"均方根误差 (RMSE): {results['rmse']:.4f}")
        print(f"R² 分数: {results['r2']:.4f}")
        print(f"支持向量数量: {len(results['support_vectors'])}")
        
        return results
    
    def plot_results(self, X_test, y_test, results):
        """可视化结果"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. 预测值 vs 真实值
        y_pred = results['predictions']
        axes[0, 0].scatter(y_test, y_pred, alpha=0.6, edgecolors='k', linewidth=0.5)
        min_val = min(y_test.min(), y_pred.min())
        max_val = max(y_test.max(), y_pred.max())
        axes[0, 0].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2)
        axes[0, 0].set_title('预测值 vs 真实值')
        axes[0, 0].set_xlabel('真实值')
        axes[0, 0].set_ylabel('预测值')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 残差分布
        residuals = y_test - y_pred
        axes[0, 1].hist(residuals, bins=30, edgecolor='black', alpha=0.7)
        axes[0, 1].axvline(x=0, color='r', linestyle='--', linewidth=2)
        axes[0, 1].set_title('残差分布')
        axes[0, 1].set_xlabel('残差值')
        axes[0, 1].set_ylabel('频数')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 预测误差随样本变化
        sample_indices = np.arange(len(y_test))
        axes[1, 0].plot(sample_indices, residuals, 'o-', markersize=3, alpha=0.6)
        axes[1, 0].axhline(y=0, color='r', linestyle='--', linewidth=2)
        axes[1, 0].set_title('预测误差随样本变化')
        axes[1, 0].set_xlabel('样本索引')
        axes[1, 0].set_ylabel('误差值')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 支持向量分布
        if X_test.shape[1] >= 2:
            axes[1, 1].scatter(X_test[:, 0], X_test[:, 1], c=y_test, 
                             cmap='viridis', alpha=0.6, label='数据点')
            
            if self.model.support_vectors_.shape[1] >= 2:
                axes[1, 1].scatter(self.model.support_vectors_[:, 0], 
                                 self.model.support_vectors_[:, 1],
                                 s=200, facecolors='none', edgecolors='black',
                                 linewidths=2, label='支持向量')
            
            axes[1, 1].set_title('支持向量分布')
            axes[1, 1].set_xlabel('特征1')
            axes[1, 1].set_ylabel('特征2')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


def generate_classification_data(n_samples=500, data_type='moons'):
    """生成分类示例数据"""
    if data_type == 'moons':
        X, y = make_moons(n_samples=n_samples, noise=0.2, random_state=42)
    elif data_type == 'circles':
        X, y = make_circles(n_samples=n_samples, noise=0.1, factor=0.5, random_state=42)
    else:
        X, y = make_classification(
            n_samples=n_samples,
            n_features=2,
            n_redundant=0,
            n_informative=2,
            n_clusters_per_class=1,
            random_state=42
        )
    return X, y


def generate_regression_data(n_samples=500):
    """生成回归示例数据"""
    np.random.seed(42)
    X = np.sort(5 * np.random.rand(n_samples, 1), axis=0)
    y = np.sin(X).ravel() + np.random.normal(0, 0.1, X.shape[0])
    return X, y


def main():
    """主函数 - 演示SVM分类和回归"""
    
    print("=" * 60)
    print("支持向量机(SVM)模型模板演示")
    print("=" * 60)
    
    # ==================== 分类任务 ====================
    print("\n【分类任务演示】")
    print("-" * 40)
    
    # 生成月牙形数据
    X_clf, y_clf = generate_classification_data(n_samples=300, data_type='moons')
    X_train_clf, X_test_clf, y_train_clf, y_test_clf = train_test_split(
        X_clf, y_clf, test_size=0.2, random_state=42
    )
    
    # 创建分类器
    clf = SVMClassifier(kernel='rbf', C=1.0, gamma='scale')
    
    # 预处理
    X_train_clf_scaled, X_test_clf_scaled = clf.preprocess(X_train_clf, X_test_clf)
    
    # 训练模型（不进行参数优化）
    print("训练SVM分类模型...")
    clf.train(X_train_clf_scaled, y_train_clf, optimize_params=False)
    
    # 评估模型
    print("\n评估分类模型:")
    clf_results = clf.evaluate(X_test_clf_scaled, y_test_clf)
    
    # 可视化决策边界
    clf.plot_decision_boundary(X_test_clf_scaled, y_test_clf, "SVM决策边界 (RBF核)")
    
    # 比较不同核函数
    print("\n比较不同核函数的决策边界...")
    clf.plot_kernel_comparison(X_test_clf_scaled, y_test_clf)
    
    # ==================== 回归任务 ====================
    print("\n【回归任务演示】")
    print("-" * 40)
    
    # 生成回归数据
    X_reg, y_reg = generate_regression_data(n_samples=200)
    X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
        X_reg, y_reg, test_size=0.2, random_state=42
    )
    
    # 创建回归器
    reg = SVMRegressor(kernel='rbf', C=10.0, gamma='scale', epsilon=0.1)
    
    # 预处理
    X_train_reg_scaled, X_test_reg_scaled = reg.preprocess(X_train_reg, X_test_reg)
    
    # 训练模型
    print("训练SVM回归模型...")
    reg.train(X_train_reg_scaled, y_train_reg, optimize_params=False)
    
    # 评估模型
    print("\n评估回归模型:")
    reg_results = reg.evaluate(X_test_reg_scaled, y_test_reg)
    
    # 可视化结果
    reg.plot_results(X_test_reg_scaled, y_test_reg, reg_results)
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
