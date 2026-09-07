"""
岭回归/LASSO回归模板
来源: 高教杯优秀论文 (B007, B160)
适用问题: 多重共线性处理、特征选择、正则化回归
输入: 特征矩阵X、目标变量y
输出: 正则化模型、系数路径、交叉验证结果
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class RegularizedRegression:
    """
    正则化回归模型模板
    
    Parameters
    ----------
    X : ndarray or DataFrame
        特征矩阵
    y : ndarray or Series
        目标变量
    feature_names : list, optional
        特征名称
    random_state : int, default=42
        随机种子
    """
    
    def __init__(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None,
        random_state: int = 42
    ):
        self.X = np.array(X)
        self.y = np.array(y)
        self.feature_names = feature_names or [f'X{i+1}' for i in range(self.X.shape[1])]
        self.random_state = random_state
        
        self.scaler = None
        self.ridge_model = None
        self.lasso_model = None
        self.X_scaled = None
    
    def preprocess(self) -> np.ndarray:
        """数据标准化"""
        from sklearn.preprocessing import StandardScaler
        
        self.scaler = StandardScaler()
        self.X_scaled = self.scaler.fit_transform(self.X)
        
        return self.X_scaled
    
    def fit_ridge(self, alpha: float = 1.0) -> dict:
        """
        拟合岭回归
        
        Parameters
        ----------
        alpha : float
            正则化强度
        
        Returns
        -------
        results : dict
            拟合结果
        """
        from sklearn.linear_model import Ridge, RidgeCV
        from sklearn.model_selection import cross_val_score
        
        if self.X_scaled is None:
            self.preprocess()
        
        # 交叉验证选择alpha
        alphas = np.logspace(-3, 3, 100)
        ridge_cv = RidgeCV(alphas=alphas, cv=5)
        ridge_cv.fit(self.X_scaled, self.y)
        best_alpha = ridge_cv.alpha_
        
        # 拟合最优模型
        self.ridge_model = Ridge(alpha=best_alpha)
        self.ridge_model.fit(self.X_scaled, self.y)
        
        # 交叉验证
        cv_scores = cross_val_score(self.ridge_model, self.X_scaled, self.y, 
                                   cv=5, scoring='r2')
        
        results = {
            'best_alpha': best_alpha,
            'cv_scores': cv_scores,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'coefficients': dict(zip(self.feature_names, self.ridge_model.coef_)),
            'intercept': self.ridge_model.intercept_,
            'r_squared': self.ridge_model.score(self.X_scaled, self.y)
        }
        
        return results
    
    def fit_lasso(self, alpha: float = 0.1) -> dict:
        """
        拟合LASSO回归
        
        Parameters
        ----------
        alpha : float
            正则化强度
        
        Returns
        -------
        results : dict
            拟合结果
        """
        from sklearn.linear_model import Lasso, LassoCV
        from sklearn.model_selection import cross_val_score
        
        if self.X_scaled is None:
            self.preprocess()
        
        # 交叉验证选择alpha
        alphas = np.logspace(-3, 3, 100)
        lasso_cv = LassoCV(alphas=alphas, cv=5, random_state=self.random_state)
        lasso_cv.fit(self.X_scaled, self.y)
        best_alpha = lasso_cv.alpha_
        
        # 拟合最优模型
        self.lasso_model = Lasso(alpha=best_alpha)
        self.lasso_model.fit(self.X_scaled, self.y)
        
        # 交叉验证
        cv_scores = cross_val_score(self.lasso_model, self.X_scaled, self.y, 
                                   cv=5, scoring='r2')
        
        # 特征选择
        n_nonzero = np.sum(self.lasso_model.coef_ != 0)
        selected_features = [self.feature_names[i] for i in range(len(self.feature_names)) 
                           if self.lasso_model.coef_[i] != 0]
        
        results = {
            'best_alpha': best_alpha,
            'cv_scores': cv_scores,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'coefficients': dict(zip(self.feature_names, self.lasso_model.coef_)),
            'intercept': self.lasso_model.intercept_,
            'r_squared': self.lasso_model.score(self.X_scaled, self.y),
            'n_nonzero': n_nonzero,
            'selected_features': selected_features
        }
        
        return results
    
    def plot_coefficient_path(self):
        """绘制系数路径图"""
        from sklearn.linear_model import Ridge, Lasso
        
        if self.X_scaled is None:
            self.preprocess()
        
        alphas = np.logspace(-3, 3, 100)
        
        ridge_coefs = []
        lasso_coefs = []
        
        for alpha in alphas:
            ridge = Ridge(alpha=alpha)
            ridge.fit(self.X_scaled, self.y)
            ridge_coefs.append(ridge.coef_)
            
            lasso = Lasso(alpha=alpha, max_iter=10000)
            lasso.fit(self.X_scaled, self.y)
            lasso_coefs.append(lasso.coef_)
        
        ridge_coefs = np.array(ridge_coefs)
        lasso_coefs = np.array(lasso_coefs)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # 岭回归系数路径
        for i in range(len(self.feature_names)):
            ax1.plot(np.log10(alphas), ridge_coefs[:, i], 
                    label=self.feature_names[i], linewidth=2)
        ax1.set_xlabel('log10(alpha)')
        ax1.set_ylabel('Coefficients')
        ax1.set_title('Ridge Coefficient Path')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # LASSO系数路径
        for i in range(len(self.feature_names)):
            ax2.plot(np.log10(alphas), lasso_coefs[:, i], 
                    label=self.feature_names[i], linewidth=2)
        ax2.set_xlabel('log10(alpha)')
        ax2.set_ylabel('Coefficients')
        ax2.set_title('LASSO Coefficient Path')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def compare_models(self) -> pd.DataFrame:
        """比较普通回归、岭回归、LASSO回归"""
        from sklearn.linear_model import LinearRegression
        from sklearn.model_selection import cross_val_score
        
        if self.X_scaled is None:
            self.preprocess()
        
        models = {
            'Linear': LinearRegression(),
            'Ridge': self.ridge_model,
            'LASSO': self.lasso_model
        }
        
        results = []
        for name, model in models.items():
            if model is None:
                continue
            cv_scores = cross_val_score(model, self.X_scaled, self.y, cv=5, scoring='r2')
            results.append({
                'Model': name,
                'CV_R2_Mean': cv_scores.mean(),
                'CV_R2_Std': cv_scores.std(),
                'Train_R2': model.score(self.X_scaled, self.y)
            })
        
        return pd.DataFrame(results)


def run_example():
    """
    示例：催化剂配比优化（含多重共线性）
    """
    from sklearn.datasets import make_regression
    
    # 生成示例数据（含多重共线性）
    np.random.seed(42)
    n_samples = 100
    
    # 生成相关特征
    X1 = np.random.rand(n_samples) * 10
    X2 = X1 + np.random.randn(n_samples) * 0.5  # 与X1高度相关
    X3 = np.random.rand(n_samples) * 10
    X4 = X2 * 0.8 + np.random.randn(n_samples) * 0.3  # 与X2相关
    
    X = np.column_stack([X1, X2, X3, X4])
    y = 2 * X1 + 3 * X2 - 1.5 * X3 + 0.5 * X4 + np.random.randn(n_samples) * 2
    
    feature_names = ['催化剂A', '催化剂B', '温度', '压力']
    
    print("=" * 60)
    print("正则化回归示例 - 催化剂配比优化")
    print("=" * 60)
    
    # 创建模型
    reg = RegularizedRegression(X, y, feature_names)
    
    # 岭回归
    print("\n岭回归:")
    ridge_results = reg.fit_ridge()
    print(f"最佳alpha: {ridge_results['best_alpha']:.4f}")
    print(f"交叉验证R²: {ridge_results['cv_mean']:.4f} ± {ridge_results['cv_std']:.4f}")
    print(f"系数: {ridge_results['coefficients']}")
    
    # LASSO回归
    print("\nLASSO回归:")
    lasso_results = reg.fit_lasso()
    print(f"最佳alpha: {lasso_results['best_alpha']:.4f}")
    print(f"交叉验证R²: {lasso_results['cv_mean']:.4f} ± {lasso_results['cv_std']:.4f}")
    print(f"非零系数: {lasso_results['n_nonzero']}/{len(feature_names)}")
    print(f"选择的特征: {lasso_results['selected_features']}")
    
    # 模型比较
    print("\n模型比较:")
    comparison = reg.compare_models()
    print(comparison.to_string(index=False))
    
    # 绘制系数路径
    fig = reg.plot_coefficient_path()
    plt.savefig('figures/regularization_path.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
