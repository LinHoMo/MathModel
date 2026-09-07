"""
随机森林模板
来源: 高教杯优秀论文 (C008, C052, C142)
适用问题: 分类/回归、特征重要性分析、非线性关系
输入: 特征矩阵X、目标变量y
输出: 训练好的模型、特征重要性、评估报告
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Tuple, List, Union
import warnings
warnings.filterwarnings('ignore')


class RandomForestModel:
    """
    随机森林模型模板
    
    Parameters
    ----------
    X : ndarray or DataFrame
        特征矩阵
    y : ndarray or Series
        目标变量
    task : str, default='classification'
        任务类型: 'classification' 或 'regression'
    feature_names : list, optional
        特征名称
    test_size : float, default=0.2
        测试集比例
    random_state : int, default=42
        随机种子
    """
    
    def __init__(
        self,
        X: np.ndarray,
        y: np.ndarray,
        task: str = 'classification',
        feature_names: Optional[List[str]] = None,
        test_size: float = 0.2,
        random_state: int = 42
    ):
        self.X = np.array(X)
        self.y = np.array(y)
        self.task = task
        self.feature_names = feature_names or [f'Feature_{i+1}' for i in range(self.X.shape[1])]
        self.test_size = test_size
        self.random_state = random_state
        
        self.model = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.y_pred = None
        self.y_prob = None
    
    def split_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """划分训练集/测试集"""
        from sklearn.model_selection import train_test_split
        
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, 
            test_size=self.test_size, 
            random_state=self.random_state,
            stratify=self.y if self.task == 'classification' else None
        )
        
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def fit(self, n_estimators: int = 100, max_depth: int = 10, **kwargs) -> dict:
        """
        训练随机森林模型
        
        Parameters
        ----------
        n_estimators : int
            树的数量
        max_depth : int
            最大深度
            
        Returns
        -------
        results : dict
            训练结果
        """
        from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
        from sklearn.model_selection import cross_val_score
        
        # 划分数据
        if self.X_train is None:
            self.split_data()
        
        # 创建模型
        if self.task == 'classification':
            self.model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=self.random_state,
                n_jobs=-1,
                **kwargs
            )
            scoring = 'accuracy'
        else:
            self.model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=self.random_state,
                n_jobs=-1,
                **kwargs
            )
            scoring = 'r2'
        
        # 交叉验证
        cv_scores = cross_val_score(self.model, self.X_train, self.y_train, 
                                   cv=5, scoring=scoring)
        
        # 训练模型
        self.model.fit(self.X_train, self.y_train)
        
        # 预测
        self.y_pred = self.model.predict(self.X_test)
        if self.task == 'classification':
            self.y_prob = self.model.predict_proba(self.X_test)
        
        # 计算特征重要性
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        results = {
            'cv_scores': cv_scores,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'feature_importances': dict(zip(self.feature_names, importances)),
            'feature_importances_sorted': [(self.feature_names[i], importances[i]) 
                                          for i in indices]
        }
        
        return results
    
    def evaluate(self) -> dict:
        """评估模型性能"""
        from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                                    f1_score, confusion_matrix, classification_report,
                                    mean_squared_error, mean_absolute_error, r2_score)
        
        evaluation = {}
        
        if self.task == 'classification':
            evaluation['accuracy'] = accuracy_score(self.y_test, self.y_pred)
            evaluation['precision'] = precision_score(self.y_test, self.y_pred, average='weighted')
            evaluation['recall'] = recall_score(self.y_test, self.y_pred, average='weighted')
            evaluation['f1'] = f1_score(self.y_test, self.y_pred, average='weighted')
            evaluation['confusion_matrix'] = confusion_matrix(self.y_test, self.y_pred)
            evaluation['classification_report'] = classification_report(self.y_test, self.y_pred)
        else:
            evaluation['mse'] = mean_squared_error(self.y_test, self.y_pred)
            evaluation['rmse'] = np.sqrt(evaluation['mse'])
            evaluation['mae'] = mean_absolute_error(self.y_test, self.y_pred)
            evaluation['r2'] = r2_score(self.y_test, self.y_pred)
        
        return evaluation
    
    def plot_feature_importance(self, top_n: int = 10):
        """绘制特征重要性图"""
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1][:top_n]
        
        plt.figure(figsize=(10, 6))
        plt.bar(range(top_n), importances[indices], align='center', color='steelblue', alpha=0.7)
        plt.xticks(range(top_n), [self.feature_names[i] for i in indices], rotation=45, ha='right')
        plt.xlabel('Features')
        plt.ylabel('Importance')
        plt.title(f'Top {top_n} Feature Importances')
        plt.tight_layout()
        plt.grid(True, alpha=0.3, axis='y')
        
        return plt.gcf()
    
    def plot_confusion_matrix(self):
        """绘制混淆矩阵（仅分类任务）"""
        if self.task != 'classification':
            print("混淆矩阵仅适用于分类任务")
            return
        
        cm = confusion_matrix(self.y_test, self.y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=np.unique(self.y),
                   yticklabels=np.unique(self.y))
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title('Confusion Matrix')
        plt.tight_layout()
        
        return plt.gcf()
    
    def plot_predictions(self):
        """绘制预测结果对比"""
        if self.task == 'regression':
            plt.figure(figsize=(10, 6))
            plt.scatter(self.y_test, self.y_pred, alpha=0.6, color='steelblue')
            plt.plot([self.y_test.min(), self.y_test.max()], 
                    [self.y_test.min(), self.y_test.max()], 
                    'r--', lw=2, label='Perfect Prediction')
            plt.xlabel('Actual')
            plt.ylabel('Predicted')
            plt.title('Actual vs Predicted')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            return plt.gcf()
    
    def get_feature_importance_table(self) -> pd.DataFrame:
        """获取特征重要性表"""
        importances = self.model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        df = pd.DataFrame({
            'Feature': [self.feature_names[i] for i in indices],
            'Importance': importances[indices],
            'Cumulative Importance': np.cumsum(importances[indices])
        })
        
        return df


def run_classification_example():
    """
    示例：客户分类预测
    
    使用鸢尾花数据集进行分类
    """
    from sklearn.datasets import load_iris
    
    # 加载数据
    iris = load_iris()
    X, y = iris.data, iris.target
    feature_names = iris.feature_names
    
    print("=" * 60)
    print("随机森林分类示例 - 鸢尾花分类")
    print("=" * 60)
    
    # 创建模型
    rf = RandomForestModel(
        X, y, 
        task='classification',
        feature_names=feature_names,
        test_size=0.2,
        random_state=42
    )
    
    # 训练模型
    results = rf.fit(n_estimators=100, max_depth=5)
    
    print(f"\n交叉验证分数: {results['cv_mean']:.4f} ± {results['cv_std']:.4f}")
    
    # 评估模型
    evaluation = rf.evaluate()
    print(f"\n测试集准确率: {evaluation['accuracy']:.4f}")
    print(f"F1分数: {evaluation['f1']:.4f}")
    print(f"\n分类报告:")
    print(evaluation['classification_report'])
    
    # 绘制特征重要性
    fig = rf.plot_feature_importance(top_n=4)
    plt.savefig('figures/rf_feature_importance.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # 绘制混淆矩阵
    fig = rf.plot_confusion_matrix()
    plt.savefig('figures/rf_confusion_matrix.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # 获取特征重要性表
    importance_table = rf.get_feature_importance_table()
    print("\n特征重要性:")
    print(importance_table)


def run_regression_example():
    """
    示例：波浪能功率预测
    
    使用Boston Housing数据集进行回归
    """
    from sklearn.datasets import make_regression
    
    # 生成回归数据
    np.random.seed(42)
    X, y = make_regression(n_samples=200, n_features=5, n_informative=3, 
                          noise=10, random_state=42)
    feature_names = ['波高', '波周期', '水深', '流速', '风速']
    
    print("=" * 60)
    print("随机森林回归示例 - 波浪能功率预测")
    print("=" * 60)
    
    # 创建模型
    rf = RandomForestModel(
        X, y, 
        task='regression',
        feature_names=feature_names,
        test_size=0.2,
        random_state=42
    )
    
    # 训练模型
    results = rf.fit(n_estimators=100, max_depth=10)
    
    print(f"\n交叉验证R²: {results['cv_mean']:.4f} ± {results['cv_std']:.4f}")
    
    # 评估模型
    evaluation = rf.evaluate()
    print(f"\n测试集R²: {evaluation['r2']:.4f}")
    print(f"RMSE: {evaluation['rmse']:.4f}")
    print(f"MAE: {evaluation['mae']:.4f}")
    
    # 绘制特征重要性
    fig = rf.plot_feature_importance(top_n=5)
    plt.savefig('figures/rf_regression_feature_importance.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # 绘制预测结果
    fig = rf.plot_predictions()
    plt.savefig('figures/rf_regression_predictions.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_classification_example()
    print("\n" + "=" * 60 + "\n")
    run_regression_example()
