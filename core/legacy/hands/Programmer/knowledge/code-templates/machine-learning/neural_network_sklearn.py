#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
神经网络模板 - 基于sklearn的MLPClassifier/MLPRegressor
功能：数据预处理、模型训练、评估、可视化
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.model_selection import train_test_split, learning_curve
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import (accuracy_score, classification_report, 
                             confusion_matrix, mean_squared_error, r2_score)
from sklearn.datasets import make_classification, make_regression
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class NeuralNetworkClassifier:
    """神经网络分类器封装类"""
    
    def __init__(self, hidden_layer_sizes=(100, 50), activation='relu',
                 max_iter=500, random_state=42):
        """
        初始化分类器
        参数：
            hidden_layer_sizes: 隐藏层神经元数量元组
            activation: 激活函数 ('relu', 'tanh', 'logistic')
            max_iter: 最大迭代次数
            random_state: 随机种子
        """
        self.hidden_layer_sizes = hidden_layer_sizes
        self.activation = activation
        self.max_iter = max_iter
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = None
        self.history = {'loss': [], 'accuracy': []}
    
    def preprocess(self, X_train, X_test):
        """数据标准化预处理"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        return X_train_scaled, X_test_scaled
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """
        训练模型
        参数：
            X_train: 训练特征
            y_train: 训练标签
            X_val: 验证特征（可选）
            y_val: 验证标签（可选）
        """
        self.model = MLPClassifier(
            hidden_layer_sizes=self.hidden_layer_sizes,
            activation=self.activation,
            max_iter=self.max_iter,
            random_state=self.random_state,
            early_stopping=True if X_val is not None else False,
            validation_fraction=0.1
        )
        
        self.model.fit(X_train, y_train)
        
        # 记录训练历史
        self.history['loss'] = self.model.loss_curve_
        if hasattr(self.model, 'validation_scores_'):
            self.history['val_score'] = self.model.validation_scores_
    
    def evaluate(self, X_test, y_test):
        """模型评估"""
        y_pred = self.model.predict(X_test)
        
        results = {
            'accuracy': accuracy_score(y_test, y_pred),
            'classification_report': classification_report(y_test, y_pred),
            'confusion_matrix': confusion_matrix(y_test, y_pred),
            'predictions': y_pred
        }
        
        print(f"测试集准确率: {results['accuracy']:.4f}")
        print("\n分类报告:")
        print(results['classification_report'])
        
        return results
    
    def plot_results(self, X_test, y_test, results):
        """可视化结果"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. 训练损失曲线
        axes[0, 0].plot(self.history['loss'], linewidth=2)
        axes[0, 0].set_title('训练损失曲线')
        axes[0, 0].set_xlabel('迭代次数')
        axes[0, 0].set_ylabel('损失值')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 混淆矩阵
        cm = results['confusion_matrix']
        im = axes[0, 1].imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        axes[0, 1].set_title('混淆矩阵')
        plt.colorbar(im, ax=axes[0, 1])
        axes[0, 1].set_xlabel('预测标签')
        axes[0, 1].set_ylabel('真实标签')
        
        # 在混淆矩阵上显示数字
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                axes[0, 1].text(j, i, format(cm[i, j], 'd'),
                               ha="center", va="center",
                               color="white" if cm[i, j] > cm.max()/2 else "black")
        
        # 3. 学习曲线
        train_sizes, train_scores, val_scores = learning_curve(
            self.model, X_test, y_test, cv=5,
            train_sizes=np.linspace(0.1, 1.0, 10),
            scoring='accuracy', n_jobs=-1
        )
        
        train_mean = np.mean(train_scores, axis=1)
        train_std = np.std(train_scores, axis=1)
        val_mean = np.mean(val_scores, axis=1)
        val_std = np.std(val_scores, axis=1)
        
        axes[1, 0].fill_between(train_sizes, train_mean - train_std,
                                train_mean + train_std, alpha=0.1, color='blue')
        axes[1, 0].fill_between(train_sizes, val_mean - val_std,
                                val_mean + val_std, alpha=0.1, color='orange')
        axes[1, 0].plot(train_sizes, train_mean, 'o-', color='blue', label='训练得分')
        axes[1, 0].plot(train_sizes, val_mean, 'o-', color='orange', label='验证得分')
        axes[1, 0].set_title('学习曲线')
        axes[1, 0].set_xlabel('训练样本数')
        axes[1, 0].set_ylabel('准确率')
        axes[1, 0].legend(loc='lower right')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 网络结构可视化
        layer_sizes = [X_test.shape[1]] + list(self.hidden_layer_sizes) + [len(np.unique(y_test))]
        axes[1, 1].set_title('网络结构')
        axes[1, 1].set_xlim(0, len(layer_sizes) + 1)
        axes[1, 1].set_ylim(0, max(layer_sizes) + 1)
        axes[1, 1].axis('off')
        
        for i, size in enumerate(layer_sizes):
            x = i + 1
            for j in range(size):
                y = (j + 1) * (max(layer_sizes) + 1) / (size + 1)
                circle = plt.Circle((x, y), 0.2, color='steelblue', alpha=0.7)
                axes[1, 1].add_patch(circle)
            
            axes[1, 1].text(x, -0.5, f'层{i}\n({size})', 
                           ha='center', fontsize=8)
        
        plt.tight_layout()
        plt.show()


class NeuralNetworkRegressor:
    """神经网络回归器封装类"""
    
    def __init__(self, hidden_layer_sizes=(100, 50), activation='relu',
                 max_iter=500, random_state=42):
        """
        初始化回归器
        参数：
            hidden_layer_sizes: 隐藏层神经元数量元组
            activation: 激活函数 ('relu', 'tanh', 'logistic')
            max_iter: 最大迭代次数
            random_state: 随机种子
        """
        self.hidden_layer_sizes = hidden_layer_sizes
        self.activation = activation
        self.max_iter = max_iter
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.model = None
        self.history = {'loss': []}
    
    def preprocess(self, X_train, X_test):
        """数据标准化预处理"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        return X_train_scaled, X_test_scaled
    
    def train(self, X_train, y_train):
        """训练模型"""
        self.model = MLPRegressor(
            hidden_layer_sizes=self.hidden_layer_sizes,
            activation=self.activation,
            max_iter=self.max_iter,
            random_state=self.random_state
        )
        
        self.model.fit(X_train, y_train)
        self.history['loss'] = self.model.loss_curve_
    
    def evaluate(self, X_test, y_test):
        """模型评估"""
        y_pred = self.model.predict(X_test)
        
        results = {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred),
            'predictions': y_pred
        }
        
        print(f"均方误差 (MSE): {results['mse']:.4f}")
        print(f"均方根误差 (RMSE): {results['rmse']:.4f}")
        print(f"R² 分数: {results['r2']:.4f}")
        
        return results
    
    def plot_results(self, X_test, y_test, results):
        """可视化结果"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. 训练损失曲线
        axes[0, 0].plot(self.history['loss'], linewidth=2, color='blue')
        axes[0, 0].set_title('训练损失曲线')
        axes[0, 0].set_xlabel('迭代次数')
        axes[0, 0].set_ylabel('损失值')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 预测值 vs 真实值
        y_pred = results['predictions']
        axes[0, 1].scatter(y_test, y_pred, alpha=0.6, edgecolors='k', linewidth=0.5)
        min_val = min(y_test.min(), y_pred.min())
        max_val = max(y_test.max(), y_pred.max())
        axes[0, 1].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2)
        axes[0, 1].set_title('预测值 vs 真实值')
        axes[0, 1].set_xlabel('真实值')
        axes[0, 1].set_ylabel('预测值')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 残差分布
        residuals = y_test - y_pred
        axes[1, 0].hist(residuals, bins=30, edgecolor='black', alpha=0.7)
        axes[1, 0].axvline(x=0, color='r', linestyle='--', linewidth=2)
        axes[1, 0].set_title('残差分布')
        axes[1, 0].set_xlabel('残差值')
        axes[1, 0].set_ylabel('频数')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 预测误差随样本变化
        sample_indices = np.arange(len(y_test))
        axes[1, 1].plot(sample_indices, residuals, 'o-', markersize=3, alpha=0.6)
        axes[1, 1].axhline(y=0, color='r', linestyle='--', linewidth=2)
        axes[1, 1].set_title('预测误差随样本变化')
        axes[1, 1].set_xlabel('样本索引')
        axes[1, 1].set_ylabel('误差值')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


def generate_classification_data(n_samples=1000, n_features=10, n_classes=3):
    """生成分类示例数据"""
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=6,
        n_redundant=2,
        n_classes=n_classes,
        n_clusters_per_class=1,
        random_state=42
    )
    return X, y


def generate_regression_data(n_samples=1000, n_features=10):
    """生成回归示例数据"""
    X, y = make_regression(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=6,
        noise=0.1,
        random_state=42
    )
    return X, y


def main():
    """主函数 - 演示神经网络分类和回归"""
    
    print("=" * 60)
    print("神经网络模板演示 (sklearn MLP)")
    print("=" * 60)
    
    # ==================== 分类任务 ====================
    print("\n【分类任务演示】")
    print("-" * 40)
    
    # 生成示例数据
    X_clf, y_clf = generate_classification_data()
    X_train_clf, X_test_clf, y_train_clf, y_test_clf = train_test_split(
        X_clf, y_clf, test_size=0.2, random_state=42, stratify=y_clf
    )
    
    # 创建并训练分类器
    clf = NeuralNetworkClassifier(
        hidden_layer_sizes=(128, 64, 32),
        activation='relu',
        max_iter=500,
        random_state=42
    )
    
    # 数据预处理
    X_train_clf_scaled, X_test_clf_scaled = clf.preprocess(X_train_clf, X_test_clf)
    
    # 训练模型
    print("训练分类模型...")
    clf.train(X_train_clf_scaled, y_train_clf)
    
    # 评估模型
    print("\n评估分类模型:")
    clf_results = clf.evaluate(X_test_clf_scaled, y_test_clf)
    
    # 可视化
    clf.plot_results(X_test_clf_scaled, y_test_clf, clf_results)
    
    # ==================== 回归任务 ====================
    print("\n【回归任务演示】")
    print("-" * 40)
    
    # 生成示例数据
    X_reg, y_reg = generate_regression_data()
    X_train_reg, X_test_reg, y_train_reg, y_test_reg = train_test_split(
        X_reg, y_reg, test_size=0.2, random_state=42
    )
    
    # 创建并训练回归器
    reg = NeuralNetworkRegressor(
        hidden_layer_sizes=(128, 64, 32),
        activation='relu',
        max_iter=500,
        random_state=42
    )
    
    # 数据预处理
    X_train_reg_scaled, X_test_reg_scaled = reg.preprocess(X_train_reg, X_test_reg)
    
    # 训练模型
    print("训练回归模型...")
    reg.train(X_train_reg_scaled, y_train_reg)
    
    # 评估模型
    print("\n评估回归模型:")
    reg_results = reg.evaluate(X_test_reg_scaled, y_test_reg)
    
    # 可视化
    reg.plot_results(X_test_reg_scaled, y_test_reg, reg_results)
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
