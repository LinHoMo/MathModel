"""
XGBoost模型模板
来源: 高教杯优秀论文 (C142, C227, C305)
适用问题: 分类/回归、高精度预测、特征重要性分析
输入: 特征矩阵X、目标变量y
输出: 训练好的模型、特征重要性、评估报告
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class XGBoostModel:
    """
    XGBoost模型模板
    
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
    
    def fit(self, n_estimators: int = 100, max_depth: int = 6, 
            learning_rate: float = 0.1, **kwargs) -> dict:
        """
        训练XGBoost模型
        
        Parameters
        ----------
        n_estimators : int
            树的数量
        max_depth : int
            最大深度
        learning_rate : float
            学习率
            
        Returns
        -------
        results : dict
            训练结果
        """
        import xgboost as xgb
        from sklearn.model_selection import cross_val_score
        
        # 划分数据
        if self.X_train is None:
            self.split_data()
        
        # 创建模型
        if self.task == 'classification':
            self.model = xgb.XGBClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.random_state,
                use_label_encoder=False,
                eval_metric='mlogloss',
                **kwargs
            )
            scoring = 'accuracy'
        else:
            self.model = xgb.XGBRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                learning_rate=learning_rate,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=self.random_state,
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
    
    def hyperparameter_tuning(self, param_grid: Optional[dict] = None) -> dict:
        """
        超参数调优
        
        Parameters
        ----------
        param_grid : dict, optional
            参数网格
        
        Returns
        -------
        best_params : dict
            最佳参数
        """
        from sklearn.model_selection import GridSearchCV
        import xgboost as xgb
        
        if param_grid is None:
            param_grid = {
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.2],
                'n_estimators': [100, 200],
                'subsample': [0.7, 0.8, 0.9]
            }
        
        if self.task == 'classification':
            model = xgb.XGBClassifier(
                random_state=self.random_state,
                use_label_encoder=False,
                eval_metric='mlogloss'
            )
            scoring = 'accuracy'
        else:
            model = xgb.XGBRegressor(random_state=self.random_state)
            scoring = 'r2'
        
        grid_search = GridSearchCV(
            model, param_grid, cv=5, scoring=scoring, n_jobs=-1, verbose=1
        )
        grid_search.fit(self.X_train, self.y_train)
        
        self.model = grid_search.best_estimator_
        
        return {
            'best_params': grid_search.best_params_,
            'best_score': grid_search.best_score_
        }
    
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
        plt.bar(range(top_n), importances[indices], align='center', 
                color='steelblue', alpha=0.7)
        plt.xticks(range(top_n), [self.feature_names[i] for i in indices], 
                   rotation=45, ha='right')
        plt.xlabel('Features')
        plt.ylabel('Importance')
        plt.title(f'Top {top_n} Feature Importances (XGBoost)')
        plt.tight_layout()
        plt.grid(True, alpha=0.3, axis='y')
        
        return plt.gcf()


def run_example():
    """
    示例：信贷风险评估
    """
    from sklearn.datasets import make_classification
    
    # 生成示例数据
    np.random.seed(42)
    X, y = make_classification(n_samples=200, n_features=10, n_informative=5,
                              n_redundant=2, random_state=42)
    feature_names = [f'Feature_{i+1}' for i in range(10)]
    
    print("=" * 60)
    print("XGBoost分类示例 - 信贷风险评估")
    print("=" * 60)
    
    # 创建模型
    xgb_model = XGBoostModel(X, y, task='classification', feature_names=feature_names)
    
    # 训练模型
    results = xgb_model.fit(n_estimators=100, max_depth=6, learning_rate=0.1)
    
    print(f"\n交叉验证分数: {results['cv_mean']:.4f} ± {results['cv_std']:.4f}")
    
    # 评估模型
    evaluation = xgb_model.evaluate()
    print(f"\n测试集准确率: {evaluation['accuracy']:.4f}")
    print(f"F1分数: {evaluation['f1']:.4f}")
    print(f"\n分类报告:\n{evaluation['classification_report']}")
    
    # 绘制特征重要性
    fig = xgb_model.plot_feature_importance(top_n=10)
    plt.savefig('figures/xgb_feature_importance.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
