"""
探索性数据分析(EDA)自动报告模板
来源: 高教杯优秀论文通用方法
适用问题: 数据理解、数据质量检查、特征分析
输入: pandas DataFrame
输出: EDA报告、可视化图表
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
from typing import Optional, Tuple, Dict, List
import warnings
warnings.filterwarnings('ignore')


class EDAReport:
    """
    探索性数据分析自动报告生成器
    
    Parameters
    ----------
    df : DataFrame
        原始数据
    target : str
        目标变量列名（可选）
    """
    
    def __init__(self, df: pd.DataFrame, target: Optional[str] = None):
        self.df = df.copy()
        self.target = target
        self.report = []
    
    def basic_info(self):
        """基础信息"""
        self.report.append("=" * 60)
        self.report.append("一、基础信息")
        self.report.append("=" * 60)
        
        self.report.append(f"\n样本数量: {len(self.df)}")
        self.report.append(f"特征数量: {len(self.df.columns)}")
        self.report.append(f"\n列名列表:")
        for i, col in enumerate(self.df.columns):
            dtype = self.df[col].dtype
            nunique = self.df[col].nunique()
            self.report.append(f"  {i+1}. {col} ({dtype}, {nunique}个唯一值)")
        
        return self
    
    def missing_analysis(self):
        """缺失值分析"""
        self.report.append("\n" + "=" * 60)
        self.report.append("二、缺失值分析")
        self.report.append("=" * 60)
        
        missing = self.df.isnull().sum()
        missing_pct = (missing / len(self.df)) * 100
        
        missing_df = pd.DataFrame({
            '缺失数量': missing,
            '缺失比例(%)': missing_pct
        })
        missing_df = missing_df[missing_df['缺失数量'] > 0].sort_values('缺失比例(%)', ascending=False)
        
        if len(missing_df) > 0:
            self.report.append(f"\n存在缺失值的列: {len(missing_df)}")
            for col, row in missing_df.iterrows():
                self.report.append(f"  {col}: {int(row['缺失数量'])} ({row['缺失比例(%)']:.2f}%)")
        else:
            self.report.append("\n无缺失值")
        
        return self
    
    def statistical_summary(self):
        """统计摘要"""
        self.report.append("\n" + "=" * 60)
        self.report.append("三、统计摘要")
        self.report.append("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            desc = self.df[numeric_cols].describe()
            self.report.append(f"\n数值特征 ({len(numeric_cols)}个):")
            self.report.append(desc.to_string())
        
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        if len(cat_cols) > 0:
            self.report.append(f"\n类别特征 ({len(cat_cols)}个):")
            for col in cat_cols:
                value_counts = self.df[col].value_counts().head(10)
                self.report.append(f"\n  {col} (前10):")
                for val, count in value_counts.items():
                    self.report.append(f"    {val}: {count}")
        
        return self
    
    def correlation_analysis(self, figsize: Tuple[int, int] = (10, 8)):
        """相关性分析"""
        self.report.append("\n" + "=" * 60)
        self.report.append("四、相关性分析")
        self.report.append("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 1:
            corr_matrix = self.df[numeric_cols].corr()
            
            # 高相关性对
            high_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    if abs(corr_matrix.iloc[i, j]) > 0.7:
                        high_corr.append((
                            corr_matrix.columns[i],
                            corr_matrix.columns[j],
                            corr_matrix.iloc[i, j]
                        ))
            
            if high_corr:
                self.report.append(f"\n高相关性特征对 (|r| > 0.7):")
                for col1, col2, corr in high_corr:
                    self.report.append(f"  {col1} <-> {col2}: {corr:.4f}")
            
            # 绘制热力图
            fig, ax = plt.subplots(figsize=figsize)
            im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1)
            ax.set_xticks(range(len(corr_matrix.columns)))
            ax.set_yticks(range(len(corr_matrix.columns)))
            ax.set_xticklabels(corr_matrix.columns, rotation=45, ha='right')
            ax.set_yticklabels(corr_matrix.columns)
            plt.colorbar(im, ax=ax)
            ax.set_title('Feature Correlation Matrix')
            plt.tight_layout()
            plt.savefig('figures/correlation_matrix.png', dpi=150, bbox_inches='tight')
            plt.close()
        
        return self
    
    def distribution_analysis(self, n_cols: int = 3, figsize: Tuple[int, int] = (15, 10)):
        """分布分析"""
        self.report.append("\n" + "=" * 60)
        self.report.append("五、分布分析")
        self.report.append("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
            fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
            if n_rows == 1:
                axes = axes.reshape(1, -1)
            
            for idx, col in enumerate(numeric_cols):
                row, col_idx = idx // n_cols, idx % n_cols
                ax = axes[row, col_idx]
                
                self.df[col].hist(bins=30, ax=ax, edgecolor='black', alpha=0.7)
                ax.set_title(col)
                ax.grid(True, alpha=0.3)
                
                # 正态性检验
                from scipy.stats import shapiro
                if len(self.df[col].dropna()) >= 3:
                    stat, p_value = shapiro(self.df[col].dropna()[:5000])
                    ax.text(0.05, 0.95, f'p={p_value:.4f}', transform=ax.transAxes, 
                           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            # 隐藏多余的子图
            for idx in range(len(numeric_cols), n_rows * n_cols):
                row, col_idx = idx // n_cols, idx % n_cols
                axes[row, col_idx].set_visible(False)
            
            plt.tight_layout()
            plt.savefig('figures/distribution_analysis.png', dpi=150, bbox_inches='tight')
            plt.close()
        
        return self
    
    def outlier_detection(self, method: str = 'iqr'):
        """异常值检测"""
        self.report.append("\n" + "=" * 60)
        self.report.append("六、异常值检测")
        self.report.append("=" * 60)
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        
        outlier_info = {}
        for col in numeric_cols:
            if method == 'iqr':
                Q1 = self.df[col].quantile(0.25)
                Q3 = self.df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                outliers = self.df[(self.df[col] < lower) | (self.df[col] > upper)]
            elif method == 'zscore':
                from scipy.stats import zscore
                z_scores = np.abs(zscore(self.df[col].dropna()))
                outliers = self.df[z_scores > 3]
            
            outlier_info[col] = len(outliers)
        
        self.report.append(f"\n异常值统计 ({method}方法):")
        for col, count in sorted(outlier_info.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                self.report.append(f"  {col}: {count}个 ({count/len(self.df)*100:.2f}%)")
        
        return self
    
    def target_analysis(self, figsize: Tuple[int, int] = (12, 5)):
        """目标变量分析"""
        if self.target is None or self.target not in self.df.columns:
            return self
        
        self.report.append("\n" + "=" * 60)
        self.report.append("七、目标变量分析")
        self.report.append("=" * 60)
        
        target = self.df[self.target]
        
        if target.dtype in ['object', 'category']:
            # 分类目标
            value_counts = target.value_counts()
            self.report.append(f"\n类别分布:")
            for val, count in value_counts.items():
                self.report.append(f"  {val}: {count} ({count/len(target)*100:.2f}%)")
            
            fig, axes = plt.subplots(1, 2, figsize=figsize)
            value_counts.plot(kind='bar', ax=axes[0], edgecolor='black')
            axes[0].set_title(f'{self.target} Distribution')
            axes[0].set_ylabel('Count')
            
            value_counts.plot(kind='pie', ax=axes[1], autopct='%1.1f%%')
            axes[1].set_title(f'{self.target} Proportion')
        else:
            # 数值目标
            self.report.append(f"\n统计信息:")
            self.report.append(f"  均值: {target.mean():.4f}")
            self.report.append(f"  标准差: {target.std():.4f}")
            self.report.append(f"  最小值: {target.min():.4f}")
            self.report.append(f"  最大值: {target.max():.4f}")
            
            fig, axes = plt.subplots(1, 2, figsize=figsize)
            target.hist(bins=30, ax=axes[0], edgecolor='black', alpha=0.7)
            axes[0].set_title(f'{self.target} Distribution')
            axes[0].grid(True, alpha=0.3)
            
            target.plot(kind='box', ax=axes[1])
            axes[1].set_title(f'{self.target} Box Plot')
        
        plt.tight_layout()
        plt.savefig('figures/target_analysis.png', dpi=150, bbox_inches='tight')
        plt.close()
        
        return self
    
    def generate_report(self) -> str:
        """生成完整报告"""
        self.basic_info()
        self.missing_analysis()
        self.statistical_summary()
        self.correlation_analysis()
        self.distribution_analysis()
        self.outlier_detection()
        self.target_analysis()
        
        return "\n".join(self.report)


def run_example():
    """
    示例：C题蔬菜数据EDA
    """
    # 生成模拟数据
    np.random.seed(42)
    n = 500
    
    data = {
        'price': np.random.uniform(3, 15, n),
        'sales': np.random.poisson(50, n),
        'temperature': np.random.normal(25, 5, n),
        'promotion': np.random.choice([0, 1], n, p=[0.7, 0.3]),
        'day_of_week': np.random.choice(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], n),
        'category': np.random.choice(['vegetable', 'fruit', 'meat'], n)
    }
    df = pd.DataFrame(data)
    
    # 添加一些缺失值
    df.loc[np.random.choice(n, 20), 'price'] = np.nan
    
    print("=" * 60)
    print("EDA自动报告示例 - 超市销售数据")
    print("=" * 60)
    
    # 生成报告
    reporter = EDAReport(df, target='sales')
    report = reporter.generate_report()
    print(report)
    
    # 保存报告
    with open('figures/eda_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\n报告已保存至 figures/eda_report.txt")
    print("图表已保存至 figures/ 目录")


if __name__ == "__main__":
    run_example()
