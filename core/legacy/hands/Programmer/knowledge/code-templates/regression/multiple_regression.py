"""
多元回归分析模板
来源: 高教杯优秀论文 (B007, B050, B160)
适用问题: 因素影响分析、预测模型、响应面分析
输入: 特征矩阵X、目标变量y
输出: 回归模型、诊断报告、预测结果
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class MultipleRegression:
    """
    多元回归分析模板
    
    Parameters
    ----------
    X : ndarray or DataFrame
        特征矩阵
    y : ndarray or Series
        目标变量
    feature_names : list, optional
        特征名称
    """
    
    def __init__(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ):
        self.X = np.array(X)
        self.y = np.array(y)
        self.feature_names = feature_names or [f'X{i+1}' for i in range(self.X.shape[1])]
        
        self.model = None
        self.X_with_const = None
        self.residuals = None
        self.fitted_values = None
    
    def fit(self) -> dict:
        """
        拟合多元线性回归模型
        
        Returns
        -------
        results : dict
            回归结果摘要
        """
        import statsmodels.api as sm
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        
        # 添加常数项
        self.X_with_const = sm.add_constant(self.X)
        
        # 拟合模型
        self.model = sm.OLS(self.y, self.X_with_const).fit()
        
        # 获取结果
        self.fitted_values = self.model.fittedvalues
        self.residuals = self.model.resid
        
        # 计算VIF
        vif_data = pd.DataFrame()
        vif_data['Feature'] = ['const'] + self.feature_names
        vif_data['VIF'] = [variance_inflation_factor(self.X_with_const, i) 
                          for i in range(self.X_with_const.shape[1])]
        
        results = {
            'summary': self.model.summary(),
            'r_squared': self.model.rsquared,
            'adj_r_squared': self.model.rsquared_adj,
            'coefficients': dict(zip(['const'] + self.feature_names, self.model.params)),
            'p_values': dict(zip(['const'] + self.feature_names, self.model.pvalues)),
            'vif': vif_data
        }
        
        return results
    
    def diagnose(self) -> dict:
        """
        模型诊断
        
        Returns
        -------
        diagnostics : dict
            诊断结果
        """
        from scipy import stats
        from statsmodels.stats.stattools import durbin_watson
        
        diagnostics = {}
        
        # 1. 正态性检验 (Shapiro-Wilk)
        stat, p_value = stats.shapiro(self.residuals)
        diagnostics['normality_test'] = {'statistic': stat, 'p_value': p_value}
        
        # 2. Durbin-Watson检验（自相关）
        dw = durbin_watson(self.residuals)
        diagnostics['durbin_watson'] = dw
        
        # 3. 异方差检验（Breusch-Pagan）
        from statsmodels.stats.diagnostic import het_breuschpagan
        bp_stat, bp_pvalue, _, _ = het_breuschpagan(self.residuals, self.X_with_const)
        diagnostics['heteroscedasticity_test'] = {'statistic': bp_stat, 'p_value': bp_pvalue}
        
        # 4. 残差统计
        diagnostics['residual_stats'] = {
            'mean': np.mean(self.residuals),
            'std': np.std(self.residuals),
            'min': np.min(self.residuals),
            'max': np.max(self.residuals)
        }
        
        return diagnostics
    
    def plot_diagnostics(self):
        """绘制诊断图"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. 残差 vs 拟合值
        axes[0, 0].scatter(self.fitted_values, self.residuals, alpha=0.6)
        axes[0, 0].axhline(y=0, color='r', linestyle='--')
        axes[0, 0].set_xlabel('Fitted Values')
        axes[0, 0].set_ylabel('Residuals')
        axes[0, 0].set_title('Residuals vs Fitted')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Q-Q图
        from scipy import stats
        stats.probplot(self.residuals, dist="norm", plot=axes[0, 1])
        axes[0, 1].set_title('Normal Q-Q Plot')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 残差直方图
        axes[1, 0].hist(self.residuals, bins=20, edgecolor='black', alpha=0.7)
        axes[1, 0].set_xlabel('Residuals')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Residuals Histogram')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 残差自相关图
        from pandas.plotting import autocorrelation_plot
        autocorrelation_plot(self.residuals, ax=axes[1, 1])
        axes[1, 1].set_title('Residuals Autocorrelation')
        
        plt.tight_layout()
        return fig
    
    def plot_coefficients(self):
        """绘制系数图"""
        coefs = pd.Series(self.model.params[1:], index=self.feature_names)
        errors = pd.Series(self.model.bse[1:], index=self.feature_names)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        coefs.plot(kind='barh', xerr=errors, ax=ax, color='steelblue', alpha=0.7)
        ax.set_xlabel('Coefficient Value')
        ax.set_title('Regression Coefficients with 95% CI')
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        ax.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        return fig
    
    def predict(self, X_new: np.ndarray) -> np.ndarray:
        """预测新数据"""
        import statsmodels.api as sm
        X_new_const = sm.add_constant(X_new)
        return self.model.predict(X_new_const)


def run_example():
    """
    示例：分析催化剂配比对产量的影响
    
    数据：C4烯烃产量与催化剂配比的关系
    """
    # 生成示例数据
    np.random.seed(42)
    n_samples = 50
    
    X = np.random.rand(n_samples, 3) * 10  # 3个因素
    y = 2 * X[:, 0] + 3 * X[:, 1] - 1.5 * X[:, 2] + 5 + np.random.randn(n_samples) * 0.5
    
    feature_names = ['催化剂A', '催化剂B', '催化剂C']
    
    # 创建回归分析对象
    reg = MultipleRegression(X, y, feature_names)
    
    # 拟合模型
    print("=" * 60)
    print("多元线性回归分析")
    print("=" * 60)
    results = reg.fit()
    
    print("\n回归结果摘要:")
    print(results['summary'])
    
    print(f"\nR²: {results['r_squared']:.4f}")
    print(f"调整R²: {results['adj_r_squared']:.4f}")
    
    print("\n系数:")
    for name, coef in results['coefficients'].items():
        print(f"  {name}: {coef:.4f}")
    
    print("\nVIF检验:")
    print(results['vif'])
    
    # 模型诊断
    print("\n" + "=" * 60)
    print("模型诊断")
    print("=" * 60)
    diagnostics = reg.diagnose()
    
    print(f"\n正态性检验 (Shapiro-Wilk): p={diagnostics['normality_test']['p_value']:.4f}")
    print(f"Durbin-Watson统计量: {diagnostics['durbin_watson']:.4f}")
    print(f"异方差检验 (Breusch-Pagan): p={diagnostics['heteroscedasticity_test']['p_value']:.4f}")
    
    # 绘制诊断图
    fig = reg.plot_diagnostics()
    plt.savefig('figures/regression_diagnostics.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # 绘制系数图
    fig = reg.plot_coefficients()
    plt.savefig('figures/regression_coefficients.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
