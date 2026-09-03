"""
分类算法统一接口模板
来源: 高教杯优秀论文
适用问题: 二分类/多分类、客户流失预测、信用评分
输入: 特征矩阵X、标签y
输出: 分类模型、评估指标、特征重要性
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Optional, List, Tuple
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix, roc_curve, auc,
                             classification_report)
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class ClassificationSuite:
    """
    分类算法统一接口
    
    支持: 逻辑回归、决策树、随机森林、SVM、XGBoost
    
    Parameters
    ----------
    X : ndarray or DataFrame
        特征矩阵
    y : ndarray
        标签
    random_state : int
        随机种子
    """

    def __init__(self, X, y, random_state: int = 42):
        self.X = np.array(X)
        self.y = np.array(y)
        self.random_state = random_state
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)
        self.models = {}
        self.results = {}
        self.best_model = None
        self.best_model_name = None

    def _get_models(self) -> Dict:
        """获取所有分类器"""
        from sklearn.linear_model import LogisticRegression
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.svm import SVC

        models = {
            'LogisticRegression': LogisticRegression(
                max_iter=1000, random_state=self.random_state),
            'DecisionTree': DecisionTreeClassifier(
                max_depth=10, random_state=self.random_state),
            'RandomForest': RandomForestClassifier(
                n_estimators=100, max_depth=10, random_state=self.random_state),
            'SVM': SVC(
                kernel='rbf', probability=True, random_state=self.random_state),
        }

        # 尝试导入XGBoost
        try:
            from xgboost import XGBClassifier
            models['XGBoost'] = XGBClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.1,
                random_state=self.random_state, eval_metric='logloss'
            )
        except ImportError:
            pass

        return models

    def train_all(self, cv_folds: int = 5) -> pd.DataFrame:
        """
        训练所有分类器并进行交叉验证
        
        Returns
        -------
        results_df : DataFrame
            各模型的评估指标对比
        """
        models = self._get_models()
        cv = StratifiedKFold(n_splits=cv_folds, shuffle=True,
                             random_state=self.random_state)

        records = []
        for name, model in models.items():
            print(f"Training {name}...")

            # 交叉验证
            cv_scores = cross_val_score(model, self.X_scaled, self.y,
                                        cv=cv, scoring='accuracy')

            # 全数据训练
            model.fit(self.X_scaled, self.y)
            y_pred = model.predict(self.X_scaled)
            y_prob = model.predict_proba(self.X_scaled)[:, 1] if hasattr(model, 'predict_proba') else None

            # 计算指标
            record = {
                'Model': name,
                'CV_Mean': cv_scores.mean(),
                'CV_Std': cv_scores.std(),
                'Train_Accuracy': accuracy_score(self.y, y_pred),
                'Precision': precision_score(self.y, y_pred, average='weighted'),
                'Recall': recall_score(self.y, y_pred, average='weighted'),
                'F1': f1_score(self.y, y_pred, average='weighted'),
            }

            # ROC-AUC (二分类)
            if y_prob is not None and len(np.unique(self.y)) == 2:
                fpr, tpr, _ = roc_curve(self.y, y_prob)
                record['AUC'] = auc(fpr, tpr)

            records.append(record)
            self.models[name] = model
            self.results[name] = {
                'y_pred': y_pred,
                'y_prob': y_prob,
                'cv_scores': cv_scores
            }

        results_df = pd.DataFrame(records).sort_values('CV_Mean', ascending=False)

        # 选择最佳模型
        self.best_model_name = results_df.iloc[0]['Model']
        self.best_model = self.models[self.best_model_name]

        return results_df

    def get_confusion_matrix(self, model_name: Optional[str] = None) -> np.ndarray:
        """获取混淆矩阵"""
        name = model_name or self.best_model_name
        if name not in self.results:
            raise ValueError(f"模型 {name} 未训练")
        return confusion_matrix(self.y, self.results[name]['y_pred'])

    def get_feature_importance(self, model_name: Optional[str] = None,
                               feature_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        获取特征重要性
        
        Parameters
        ----------
        model_name : str, optional
            模型名称，默认为最佳模型
        feature_names : list, optional
            特征名称列表
        """
        name = model_name or self.best_model_name
        model = self.models[name]

        if feature_names is None:
            feature_names = [f'Feature_{i}' for i in range(self.X.shape[1])]

        # 获取特征重要性
        if hasattr(model, 'feature_importances_'):
            importance = model.feature_importances_
        elif hasattr(model, 'coef_'):
            importance = np.abs(model.coef_[0])
        else:
            print(f"模型 {name} 不支持特征重要性")
            return None

        # 归一化
        importance = importance / importance.sum()

        df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': importance
        }).sort_values('Importance', ascending=False)

        return df

    def plot_roc_curves(self, filename: Optional[str] = None):
        """绘制所有模型的ROC曲线"""
        if len(np.unique(self.y)) != 2:
            print("ROC曲线仅支持二分类问题")
            return

        plt.figure(figsize=(10, 8))
        colors = plt.cm.Set1(np.linspace(0, 1, len(self.results)))

        for (name, result), color in zip(self.results.items(), colors):
            if result['y_prob'] is not None:
                fpr, tpr, _ = roc_curve(self.y, result['y_prob'])
                roc_auc = auc(fpr, tpr)
                plt.plot(fpr, tpr, color=color, linewidth=2,
                         label=f'{name} (AUC = {roc_auc:.3f})')

        plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curves - All Models')
        plt.legend(loc='lower right')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

    def plot_confusion_matrix(self, model_name: Optional[str] = None,
                              filename: Optional[str] = None):
        """绘制混淆矩阵热力图"""
        import seaborn as sns

        cm = self.get_confusion_matrix(model_name)
        name = model_name or self.best_model_name

        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=sorted(np.unique(self.y)),
                    yticklabels=sorted(np.unique(self.y)))
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.title(f'Confusion Matrix - {name}')
        plt.tight_layout()

        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

    def plot_feature_importance(self, model_name: Optional[str] = None,
                                feature_names: Optional[List[str]] = None,
                                top_n: int = 15, filename: Optional[str] = None):
        """绘制特征重要性图"""
        df = self.get_feature_importance(model_name, feature_names)
        if df is None:
            return

        name = model_name or self.best_model_name
        df = df.head(top_n)

        plt.figure(figsize=(10, 6))
        plt.barh(range(len(df)), df['Importance'].values, color='steelblue')
        plt.yticks(range(len(df)), df['Feature'].values)
        plt.xlabel('Importance')
        plt.title(f'Feature Importance - {name}')
        plt.gca().invert_yaxis()
        plt.tight_layout()

        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()


def run_example():
    """示例: 使用sklearn乳腺癌数据集"""
    from sklearn.datasets import load_breast_cancer

    print("=" * 60)
    print("分类算法统一接口示例 - 乳腺癌分类")
    print("=" * 60)

    # 加载数据
    data = load_breast_cancer()
    X, y = data.data, data.target
    feature_names = data.feature_names

    print(f"\n数据集: Breast Cancer Wisconsin")
    print(f"样本数: {X.shape[0]}, 特征数: {X.shape[1]}")
    print(f"类别分布: {np.bincount(y)} (0=malignant, 1=benign)")

    # 创建分类套件
    suite = ClassificationSuite(X, y, random_state=42)

    # 训练所有模型
    print("\n--- 训练所有模型 ---")
    results_df = suite.train_all(cv_folds=5)
    print("\n模型对比:")
    print(results_df.to_string(index=False))

    # 混淆矩阵
    print(f"\n--- 最佳模型: {suite.best_model_name} ---")
    cm = suite.get_confusion_matrix()
    print(f"混淆矩阵:\n{cm}")

    # 分类报告
    y_pred = suite.results[suite.best_model_name]['y_pred']
    print(f"\n分类报告:\n{classification_report(y, y_pred)}")

    # 特征重要性
    importance = suite.get_feature_importance(feature_names=feature_names)
    print(f"\nTop 10 特征重要性:")
    print(importance.head(10).to_string(index=False))

    # 绘图
    suite.plot_roc_curves('figures/classification_roc.png')
    suite.plot_confusion_matrix(filename='figures/classification_cm.png')
    suite.plot_feature_importance(feature_names=feature_names,
                                  filename='figures/classification_importance.png')
    print("\n图片已保存到 figures/ 目录")


if __name__ == "__main__":
    run_example()
