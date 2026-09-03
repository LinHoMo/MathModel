"""
模型验证工具模板
来源: 高教杯优秀论文通用方法
适用问题: 模型验证、交叉验证、残差分析
输入: 模型、数据
输出: 验证报告、诊断图
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple, Dict, Any
import warnings
warnings.filterwarnings('ignore')


class ModelValidator:
    """
    模型验证工具
    
    Parameters
    ----------
    model : object
        训练好的模型（sklearn风格）
    X_train : ndarray
        训练特征
    X_test : ndarray
        测试特征
    y_train : ndarray
        训练目标
    y_test : ndarray
        测试目标
    task : str
        任务类型: 'classification' 或 'regression'
    """
    
    def __init__(
        self,
        model,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
        task: str = 'classification'
    ):
        self.model = model
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.task = task
        
        self.y_pred = model.predict(X_test)
        self.y_prob = None
        if hasattr(model, 'predict_proba'):
            try:
                self.y_prob = model.predict_proba(X_test)
            except:
                pass
    
    def cross_validation(self, cv: int = 5, scoring: str = 'accuracy') -> Dict[str, float]:
        """
        交叉验证
        
        Parameters
        ----------
        cv : int
            折数
        scoring : str
            评估指标
        
        Returns
        -------
        results : dict
            交叉验证结果
        """
        from sklearn.model_selection import cross_val_score
        
        X_combined = np.vstack([self.X_train, self.X_test])
        y_combined = np.hstack([self.y_train, self.y_test])
        
        scores = cross_val_score(self.model, X_combined, y_combined, cv=cv, scoring=scoring)
        
        results = {
            'mean': scores.mean(),
            'std': scores.std(),
            'min': scores.min(),
            'max': scores.max(),
            'scores': scores
        }
        
        return results
    
    def classification_metrics(self) -> Dict[str, Any]:
        """分类模型评估指标"""
        from sklearn.metrics import (accuracy_score, precision_score, recall_score, 
                                    f1_score, roc_auc_score, confusion_matrix, 
                                    classification_report)
        
        metrics = {
            'accuracy': accuracy_score(self.y_test, self.y_pred),
            'precision': precision_score(self.y_test, self.y_pred, average='weighted'),
            'recall': recall_score(self.y_test, self.y_pred, average='weighted'),
            'f1': f1_score(self.y_test, self.y_pred, average='weighted'),
            'confusion_matrix': confusion_matrix(self.y_test, self.y_pred),
            'classification_report': classification_report(self.y_test, self.y_pred)
        }
        
        if self.y_prob is not None and len(np.unique(self.y_test)) == 2:
            metrics['auc'] = roc_auc_score(self.y_test, self.y_prob[:, 1])
        
        return metrics
    
    def regression_metrics(self) -> Dict[str, float]:
        """回归模型评估指标"""
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        metrics = {
            'mse': mean_squared_error(self.y_test, self.y_pred),
            'rmse': np.sqrt(mean_squared_error(self.y_test, self.y_pred)),
            'mae': mean_absolute_error(self.y_test, self.y_pred),
            'r2': r2_score(self.y_test, self.y_pred)
        }
        
        # MAPE
        mask = self.y_test != 0
        if mask.any():
            metrics['mape'] = np.mean(np.abs((self.y_test[mask] - self.y_pred[mask]) / self.y_test[mask])) * 100
        
        return metrics
    
    def residual_analysis(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        残差分析
        
        Returns
        -------
        residuals : ndarray
            残差
        stats : dict
            残差统计
        """
        residuals = self.y_test - self.y_pred
        
        stats = {
            'mean': np.mean(residuals),
            'std': np.std(residuals),
            'min': np.min(residuals),
            'max': np.max(residuals),
            'median': np.median(residuals)
        }
        
        return residuals, stats
    
    def plot_diagnostics(self, figsize: Tuple[int, int] = (12, 10)):
        """
        绘制诊断图
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        
        if self.task == 'regression':
            residuals = self.y_test - self.y_pred
            
            # 1. 残差 vs 拟合值
            axes[0, 0].scatter(self.y_pred, residuals, alpha=0.6)
            axes[0, 0].axhline(y=0, color='r', linestyle='--')
            axes[0, 0].set_xlabel('Fitted Values')
            axes[0, 0].set_ylabel('Residuals')
            axes[0, 0].set_title('Residuals vs Fitted')
            axes[0, 0].grid(True, alpha=0.3)
            
            # 2. Q-Q图
            from scipy import stats
            stats.probplot(residuals, dist="norm", plot=axes[0, 1])
            axes[0, 1].set_title('Normal Q-Q Plot')
            axes[0, 1].grid(True, alpha=0.3)
            
            # 3. 残差直方图
            axes[1, 0].hist(residuals, bins=20, edgecolor='black', alpha=0.7)
            axes[1, 0].set_xlabel('Residuals')
            axes[1, 0].set_ylabel('Frequency')
            axes[1, 0].set_title('Residuals Histogram')
            axes[1, 0].grid(True, alpha=0.3)
            
            # 4. 预测 vs 真实
            axes[1, 1].scatter(self.y_test, self.y_pred, alpha=0.6)
            axes[1, 1].plot([self.y_test.min(), self.y_test.max()], 
                          [self.y_test.min(), self.y_test.max()], 
                          'r--', lw=2, label='Perfect Prediction')
            axes[1, 1].set_xlabel('Actual')
            axes[1, 1].set_ylabel('Predicted')
            axes[1, 1].set_title('Actual vs Predicted')
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        
        elif self.task == 'classification':
            from sklearn.metrics import confusion_matrix, roc_curve, auc
            
            # 1. 混淆矩阵
            cm = confusion_matrix(self.y_test, self.y_pred)
            im = axes[0, 0].imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
            axes[0, 0].set_title('Confusion Matrix')
            plt.colorbar(im, ax=axes[0, 0])
            axes[0, 0].set_xlabel('Predicted')
            axes[0, 0].set_ylabel('Actual')
            
            # 添加数值标注
            for i in range(cm.shape[0]):
                for j in range(cm.shape[1]):
                    axes[0, 0].text(j, i, format(cm[i, j], 'd'),
                                   ha="center", va="center",
                                   color="white" if cm[i, j] > cm.max()/2 else "black")
            
            # 2. ROC曲线（二分类）
            if self.y_prob is not None and len(np.unique(self.y_test)) == 2:
                fpr, tpr, _ = roc_curve(self.y_test, self.y_prob[:, 1])
                roc_auc = auc(fpr, tpr)
                
                axes[0, 1].plot(fpr, tpr, 'b-', lw=2, 
                              label=f'ROC curve (AUC = {roc_auc:.4f})')
                axes[0, 1].plot([0, 1], [0, 1], 'r--', lw=2, label='Random')
                axes[0, 1].set_xlabel('False Positive Rate')
                axes[0, 1].set_ylabel('True Positive Rate')
                axes[0, 1].set_title('ROC Curve')
                axes[0, 1].legend()
                axes[0, 1].grid(True, alpha=0.3)
            else:
                axes[0, 1].text(0.5, 0.5, 'ROC not available\n(multiclass or no prob)', 
                              ha='center', va='center', transform=axes[0, 1].transAxes)
            
            # 3. 类别分布
            unique, counts = np.unique(self.y_test, return_counts=True)
            axes[1, 0].bar(unique, counts, color='steelblue', alpha=0.7)
            axes[1, 0].set_xlabel('Class')
            axes[1, 0].set_ylabel('Count')
            axes[1, 0].set_title('Test Set Class Distribution')
            axes[1, 0].grid(True, alpha=0.3, axis='y')
            
            # 4. 预测概率分布
            if self.y_prob is not None:
                axes[1, 1].hist(self.y_prob[:, 1], bins=20, edgecolor='black', alpha=0.7)
                axes[1, 1].set_xlabel('Predicted Probability')
                axes[1, 1].set_ylabel('Frequency')
                axes[1, 1].set_title('Prediction Probability Distribution')
                axes[1, 1].grid(True, alpha=0.3)
            else:
                axes[1, 1].text(0.5, 0.5, 'Probability not available', 
                              ha='center', va='center', transform=axes[1, 1].transAxes)
        
        plt.tight_layout()
        return fig
    
    def generate_report(self) -> str:
        """生成验证报告"""
        report_lines = [
            "=" * 60,
            "模型验证报告",
            "=" * 60,
            f"\n任务类型: {self.task}",
            f"训练集大小: {len(self.X_train)}",
            f"测试集大小: {len(self.X_test)}"
        ]
        
        if self.task == 'classification':
            metrics = self.classification_metrics()
            report_lines.extend([
                "\n分类指标:",
                "-" * 40,
                f"准确率: {metrics['accuracy']:.4f}",
                f"精确率: {metrics['precision']:.4f}",
                f"召回率: {metrics['recall']:.4f}",
                f"F1分数: {metrics['f1']:.4f}",
            ])
            if 'auc' in metrics:
                report_lines.append(f"AUC: {metrics['auc']:.4f}")
        else:
            metrics = self.regression_metrics()
            report_lines.extend([
                "\n回归指标:",
                "-" * 40,
                f"MSE:  {metrics['mse']:.4f}",
                f"RMSE: {metrics['rmse']:.4f}",
                f"MAE:  {metrics['mae']:.4f}",
                f"R²:   {metrics['r2']:.4f}",
            ])
            if 'mape' in metrics:
                report_lines.append(f"MAPE: {metrics['mape']:.2f}%")
        
        # 交叉验证
        try:
            cv_results = self.cross_validation()
            report_lines.extend([
                "\n交叉验证:",
                "-" * 40,
                f"均值: {cv_results['mean']:.4f}",
                f"标准差: {cv_results['std']:.4f}",
                f"范围: [{cv_results['min']:.4f}, {cv_results['max']:.4f}]"
            ])
        except:
            report_lines.append("\n交叉验证: 无法执行")
        
        return "\n".join(report_lines)


def run_example():
    """
    示例：随机森林模型验证
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    
    # 生成示例数据
    np.random.seed(42)
    X, y = make_classification(n_samples=200, n_features=10, n_informative=5,
                              n_redundant=2, random_state=42)
    
    # 划分数据
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # 训练模型
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    print("=" * 60)
    print("模型验证示例 - 随机森林分类")
    print("=" * 60)
    
    # 创建验证器
    validator = ModelValidator(model, X_train, X_test, y_train, y_test, task='classification')
    
    # 生成报告
    print(validator.generate_report())
    
    # 绘制诊断图
    fig = validator.plot_diagnostics()
    plt.savefig('figures/model_diagnostics.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
