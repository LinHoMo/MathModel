#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交叉验证工具模板
功能：K折交叉验证、留一交叉验证、分层交叉验证
"""

import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import (KFold, LeaveOneOut, StratifiedKFold,
                                     cross_val_score, cross_validate,
                                     TimeSeriesSplit, ShuffleSplit)
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.svm import SVC, SVR
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, mean_squared_error, r2_score)
from sklearn.datasets import make_classification, make_regression
import pandas as pd
from typing import List, Dict, Tuple, Callable
import warnings
warnings.filterwarnings('ignore')

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class CrossValidationToolbox:
    """交叉验证工具箱"""
    
    def __init__(self, random_state=42):
        """
        初始化交叉验证工具箱
        参数：
            random_state: 随机种子
        """
        self.random_state = random_state
        self.results = {}
    
    def k_fold_cv(self, X, y, model, n_folds=5, scoring='accuracy', 
                  shuffle=True, random_state=None):
        """
        K折交叉验证
        参数：
            X: 特征矩阵
            y: 标签向量
            model: 机器学习模型
            n_folds: 折数
            scoring: 评分指标
            shuffle: 是否打乱数据
            random_state: 随机种子
        返回：
            交叉验证结果字典
        """
        if random_state is None:
            random_state = self.random_state
        
        # 创建K折交叉验证器
        kfold = KFold(
            n_splits=n_folds,
            shuffle=shuffle,
            random_state=random_state
        )
        
        print(f"执行K折交叉验证 (K={n_folds})...")
        print(f"评分指标: {scoring}")
        print("-" * 40)
        
        # 执行交叉验证
        cv_results = cross_validate(
            model, X, y,
            cv=kfold,
            scoring=scoring,
            return_train_score=True,
            return_estimator=True,
            n_jobs=-1
        )
        
        # 计算统计信息
        results = {
            'test_scores': cv_results['test_score'],
            'train_scores': cv_results['train_score'],
            'fit_times': cv_results['fit_time'],
            'score_times': cv_results['score_time'],
            'test_mean': np.mean(cv_results['test_score']),
            'test_std': np.std(cv_results['test_score']),
            'train_mean': np.mean(cv_results['train_score']),
            'train_std': np.std(cv_results['train_score']),
            'n_folds': n_folds,
            'scoring': scoring,
            'estimators': cv_results['estimator']
        }
        
        print(f"测试集{scoring}: {results['test_mean']:.4f} (+/- {results['test_std']:.4f})")
        print(f"训练集{scoring}: {results['train_mean']:.4f} (+/- {results['train_std']:.4f})")
        
        self.results['k_fold'] = results
        return results
    
    def stratified_k_fold_cv(self, X, y, model, n_folds=5, scoring='accuracy',
                             shuffle=True, random_state=None):
        """
        分层K折交叉验证
        参数：
            X: 特征矩阵
            y: 标签向量
            model: 机器学习模型
            n_folds: 折数
            scoring: 评分指标
            shuffle: 是否打乱数据
            random_state: 随机种子
        返回：
            交叉验证结果字典
        """
        if random_state is None:
            random_state = self.random_state
        
        # 创建分层K折交叉验证器
        skfold = StratifiedKFold(
            n_splits=n_folds,
            shuffle=shuffle,
            random_state=random_state
        )
        
        print(f"执行分层K折交叉验证 (K={n_folds})...")
        print(f"评分指标: {scoring}")
        print("-" * 40)
        
        # 执行交叉验证
        cv_results = cross_validate(
            model, X, y,
            cv=skfold,
            scoring=scoring,
            return_train_score=True,
            return_estimator=True,
            n_jobs=-1
        )
        
        # 计算统计信息
        results = {
            'test_scores': cv_results['test_score'],
            'train_scores': cv_results['train_score'],
            'fit_times': cv_results['fit_time'],
            'score_times': cv_results['score_time'],
            'test_mean': np.mean(cv_results['test_score']),
            'test_std': np.std(cv_results['test_score']),
            'train_mean': np.mean(cv_results['train_score']),
            'train_std': np.std(cv_results['train_score']),
            'n_folds': n_folds,
            'scoring': scoring,
            'estimators': cv_results['estimator']
        }
        
        print(f"测试集{scoring}: {results['test_mean']:.4f} (+/- {results['test_std']:.4f})")
        print(f"训练集{scoring}: {results['train_mean']:.4f} (+/- {results['train_std']:.4f})")
        
        self.results['stratified_k_fold'] = results
        return results
    
    def leave_one_out_cv(self, X, y, model, scoring='accuracy'):
        """
        留一交叉验证
        参数：
            X: 特征矩阵
            y: 标签向量
            model: 机器学习模型
            scoring: 评分指标
        返回：
            交叉验证结果字典
        """
        loo = LeaveOneOut()
        
        n_samples = len(X)
        print(f"执行留一交叉验证 (样本数: {n_samples})...")
        print(f"评分指标: {scoring}")
        print("-" * 40)
        
        # 执行交叉验证
        cv_results = cross_validate(
            model, X, y,
            cv=loo,
            scoring=scoring,
            return_train_score=True,
            return_estimator=True,
            n_jobs=-1
        )
        
        # 计算统计信息
        results = {
            'test_scores': cv_results['test_score'],
            'train_scores': cv_results['train_score'],
            'fit_times': cv_results['fit_time'],
            'score_times': cv_results['score_time'],
            'test_mean': np.mean(cv_results['test_score']),
            'test_std': np.std(cv_results['test_score']),
            'train_mean': np.mean(cv_results['train_score']),
            'train_std': np.std(cv_results['train_score']),
            'n_folds': n_samples,
            'scoring': scoring,
            'estimators': cv_results['estimator']
        }
        
        print(f"测试集{scoring}: {results['test_mean']:.4f} (+/- {results['test_std']:.4f})")
        print(f"训练集{scoring}: {results['train_mean']:.4f} (+/- {results['train_std']:.4f})")
        
        self.results['leave_one_out'] = results
        return results
    
    def time_series_cv(self, X, y, model, n_splits=5, scoring='neg_mean_squared_error',
                       test_size=None, gap=0):
        """
        时间序列交叉验证
        参数：
            X: 特征矩阵
            y: 标签向量
            model: 机器学习模型
            n_splits: 分割数
            scoring: 评分指标
            test_size: 测试集大小
            gap: 训练集和测试集之间的间隔
        返回：
            交叉验证结果字典
        """
        tscv = TimeSeriesSplit(
            n_splits=n_splits,
            test_size=test_size,
            gap=gap
        )
        
        print(f"执行时间序列交叉验证 (分割数: {n_splits})...")
        print(f"评分指标: {scoring}")
        print("-" * 40)
        
        # 执行交叉验证
        cv_results = cross_validate(
            model, X, y,
            cv=tscv,
            scoring=scoring,
            return_train_score=True,
            return_estimator=True,
            n_jobs=-1
        )
        
        # 计算统计信息
        results = {
            'test_scores': cv_results['test_score'],
            'train_scores': cv_results['train_score'],
            'fit_times': cv_results['fit_time'],
            'score_times': cv_results['score_time'],
            'test_mean': np.mean(cv_results['test_score']),
            'test_std': np.std(cv_results['test_score']),
            'train_mean': np.mean(cv_results['train_score']),
            'train_std': np.std(cv_results['train_score']),
            'n_folds': n_splits,
            'scoring': scoring,
            'estimators': cv_results['estimator']
        }
        
        print(f"测试集{scoring}: {results['test_mean']:.4f} (+/- {results['test_std']:.4f})")
        print(f"训练集{scoring}: {results['train_mean']:.4f} (+/- {results['train_std']:.4f})")
        
        self.results['time_series'] = results
        return results
    
    def compare_models(self, X, y, models_dict: Dict, cv_method='k_fold', 
                       n_folds=5, scoring='accuracy'):
        """
        比较多个模型的交叉验证性能
        参数：
            X: 特征矩阵
            y: 标签向量
            models_dict: 模型字典 {模型名称: 模型实例}
            cv_method: 交叉验证方法
            n_folds: 折数
            scoring: 评分指标
        返回：
            比较结果字典
        """
        print(f"比较{len(models_dict)}个模型的性能...")
        print(f"交叉验证方法: {cv_method}")
        print(f"评分指标: {scoring}")
        print("-" * 40)
        
        comparison_results = {}
        
        for model_name, model in models_dict.items():
            print(f"\n训练模型: {model_name}")
            
            # 选择交叉验证方法
            if cv_method == 'k_fold':
                results = self.k_fold_cv(X, y, model, n_folds, scoring, 
                                        shuffle=False)
            elif cv_method == 'stratified':
                results = self.stratified_k_fold_cv(X, y, model, n_folds, scoring,
                                                   shuffle=False)
            elif cv_method == 'loo':
                results = self.leave_one_out_cv(X, y, model, scoring)
            else:
                raise ValueError(f"未知的交叉验证方法: {cv_method}")
            
            comparison_results[model_name] = {
                'test_mean': results['test_mean'],
                'test_std': results['test_std'],
                'train_mean': results['train_mean'],
                'train_std': results['train_std'],
                'test_scores': results['test_scores']
            }
        
        # 找出最佳模型
        best_model_name = max(comparison_results.keys(),
                            key=lambda x: comparison_results[x]['test_mean'])
        
        print(f"\n{'='*60}")
        print(f"模型比较结果:")
        print(f"{'='*60}")
        
        for model_name, result in comparison_results.items():
            print(f"{model_name:20s}: "
                  f"测试{scoring} = {result['test_mean']:.4f} "
                  f"(+/- {result['test_std']:.4f})")
        
        print(f"\n最佳模型: {best_model_name}")
        
        self.results['comparison'] = {
            'results': comparison_results,
            'best_model': best_model_name,
            'scoring': scoring
        }
        
        return comparison_results
    
    def plot_cv_results(self, figsize=(14, 10)):
        """绘制交叉验证结果"""
        if not self.results:
            print("没有交叉验证结果可绘制")
            return
        
        # 确定子图数量
        n_results = len(self.results)
        n_cols = min(2, n_results)
        n_rows = (n_results + 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        if n_results == 1:
            axes = np.array([axes])
        axes = axes.ravel()
        
        for idx, (cv_type, result) in enumerate(self.results.items()):
            if cv_type == 'comparison':
                continue
            
            ax = axes[idx]
            
            # 绘制每折的分数
            if 'test_scores' in result:
                x = range(len(result['test_scores']))
                ax.bar(x, result['test_scores'], alpha=0.6, label='测试集', color='steelblue')
                ax.bar(x, result['train_scores'], alpha=0.3, label='训练集', color='orange')
                
                # 添加均值线
                ax.axhline(y=result['test_mean'], color='red', linestyle='--', 
                          linewidth=2, label=f'测试均值: {result["test_mean"]:.4f}')
                
                ax.set_xlabel('折数')
                ax.set_ylabel(result.get('scoring', '分数'))
                ax.set_title(f'{cv_type}交叉验证结果')
                ax.legend()
                ax.grid(True, alpha=0.3)
        
        # 绘制模型比较图
        if 'comparison' in self.results:
            ax = axes[len(self.results) - 1]
            comparison = self.results['comparison']['results']
            
            models = list(comparison.keys())
            test_means = [comparison[m]['test_mean'] for m in models]
            test_stds = [comparison[m]['test_std'] for m in models]
            
            x = range(len(models))
            bars = ax.bar(x, test_means, yerr=test_stds, capsize=5,
                         color='steelblue', edgecolor='black', alpha=0.7)
            
            # 标记最佳模型
            best_idx = np.argmax(test_means)
            bars[best_idx].set_color('red')
            bars[best_idx].set_alpha(0.8)
            
            ax.set_xlabel('模型')
            ax.set_ylabel(self.results['comparison']['scoring'])
            ax.set_title('模型性能比较')
            ax.set_xticks(x)
            ax.set_xticklabels(models, rotation=45, ha='right')
            ax.grid(True, alpha=0.3, axis='y')
        
        # 隐藏未使用的子图
        for idx in range(n_results, len(axes)):
            axes[idx].axis('off')
        
        plt.tight_layout()
        plt.show()
    
    def plot_learning_curves(self, X, y, models_dict: Dict, scoring='accuracy',
                            train_sizes=None, cv=5):
        """绘制学习曲线"""
        if train_sizes is None:
            train_sizes = np.linspace(0.1, 1.0, 10)
        
        fig, axes = plt.subplots(1, len(models_dict), figsize=(5 * len(models_dict), 5))
        if len(models_dict) == 1:
            axes = [axes]
        
        for idx, (model_name, model) in enumerate(models_dict.items()):
            print(f"计算学习曲线: {model_name}")
            
            train_sizes_abs, train_scores, val_scores = learning_curve(
                model, X, y,
                train_sizes=train_sizes,
                cv=cv,
                scoring=scoring,
                n_jobs=-1
            )
            
            train_mean = np.mean(train_scores, axis=1)
            train_std = np.std(train_scores, axis=1)
            val_mean = np.mean(val_scores, axis=1)
            val_std = np.std(val_scores, axis=1)
            
            ax = axes[idx]
            
            ax.fill_between(train_sizes_abs, train_mean - train_std,
                           train_mean + train_std, alpha=0.1, color='blue')
            ax.fill_between(train_sizes_abs, val_mean - val_std,
                           val_mean + val_std, alpha=0.1, color='orange')
            ax.plot(train_sizes_abs, train_mean, 'o-', color='blue', 
                   label='训练集', linewidth=2)
            ax.plot(train_sizes_abs, val_mean, 'o-', color='orange',
                   label='验证集', linewidth=2)
            
            ax.set_xlabel('训练样本数')
            ax.set_ylabel(scoring)
            ax.set_title(f'{model_name}学习曲线')
            ax.legend(loc='lower right')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


def generate_sample_data(data_type='classification', n_samples=1000, n_features=10):
    """生成示例数据"""
    if data_type == 'classification':
        X, y = make_classification(
            n_samples=n_samples,
            n_features=n_features,
            n_informative=6,
            n_redundant=2,
            n_classes=3,
            n_clusters_per_class=1,
            random_state=42
        )
    else:
        X, y = make_regression(
            n_samples=n_samples,
            n_features=n_features,
            n_informative=6,
            noise=0.1,
            random_state=42
        )
    
    return X, y


def main():
    """主函数 - 演示交叉验证工具"""
    
    print("=" * 60)
    print("交叉验证工具模板演示")
    print("=" * 60)
    
    # 创建交叉验证工具箱
    cv_toolbox = CrossValidationToolbox(random_state=42)
    
    # ==================== 分类任务 ====================
    print("\n【分类任务交叉验证】")
    print("-" * 40)
    
    # 生成分类数据
    X_clf, y_clf = generate_sample_data('classification', n_samples=500, n_features=10)
    print(f"分类数据: {X_clf.shape[0]}个样本, {X_clf.shape[1]}个特征")
    print(f"类别分布: {np.bincount(y_clf.astype(int))}")
    
    # 创建分类模型
    clf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    # 1. K折交叉验证
    print("\n1. K折交叉验证")
    kfold_results = cv_toolbox.k_fold_cv(
        X_clf, y_clf, clf_model,
        n_folds=5, scoring='accuracy'
    )
    
    # 2. 分层K折交叉验证
    print("\n2. 分层K折交叉验证")
    stratified_results = cv_toolbox.stratified_k_fold_cv(
        X_clf, y_clf, clf_model,
        n_folds=5, scoring='accuracy'
    )
    
    # 3. 留一交叉验证（使用小子集演示）
    print("\n3. 留一交叉验证（使用100个样本演示）")
    X_small, y_small = X_clf[:100], y_clf[:100]
    loo_results = cv_toolbox.leave_one_out_cv(
        X_small, y_small, clf_model,
        scoring='accuracy'
    )
    
    # 4. 模型比较
    print("\n4. 多模型比较")
    models_dict = {
        '随机森林': RandomForestClassifier(n_estimators=100, random_state=42),
        'SVM': SVC(kernel='rbf', random_state=42),
        '逻辑回归': LogisticRegression(max_iter=1000, random_state=42)
    }
    
    comparison_results = cv_toolbox.compare_models(
        X_clf, y_clf, models_dict,
        cv_method='stratified',
        n_folds=5,
        scoring='accuracy'
    )
    
    # 绘制结果
    cv_toolbox.plot_cv_results()
    
    # ==================== 回归任务 ====================
    print("\n【回归任务交叉验证】")
    print("-" * 40)
    
    # 生成回归数据
    X_reg, y_reg = generate_sample_data('regression', n_samples=500, n_features=10)
    print(f"回归数据: {X_reg.shape[0]}个样本, {X_reg.shape[1]}个特征")
    
    # 创建回归模型
    reg_model = RandomForestRegressor(n_estimators=100, random_state=42)
    
    # K折交叉验证
    print("\nK折交叉验证（回归）")
    reg_results = cv_toolbox.k_fold_cv(
        X_reg, y_reg, reg_model,
        n_folds=5, scoring='neg_mean_squared_error'
    )
    
    # 学习曲线
    print("\n绘制学习曲线...")
    cv_toolbox.plot_learning_curves(
        X_clf, y_clf, models_dict,
        scoring='accuracy'
    )
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)


# 学习曲线函数（需要导入）
from sklearn.model_selection import learning_curve


if __name__ == "__main__":
    main()
