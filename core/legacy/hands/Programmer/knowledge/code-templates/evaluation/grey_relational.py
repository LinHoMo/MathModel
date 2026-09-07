"""
模板来源: resources/code-templates/evaluation/grey_relational.py
修改说明: 
  - 新增灰色关联分析模板
  - 支持多种关联系数计算方法
"""
import numpy as np
import pandas as pd


class GreyRelationalAnalysis:
    """灰色关联分析"""
    
    def __init__(self, reference, compare, method='euclidean'):
        """
        reference: 参考序列（最优方案）
        compare: 比较序列矩阵（行为方案，列为指标）
        method: 'euclidean'欧氏距离, 'manhattan'曼哈顿距离
        """
        self.reference = np.array(reference, dtype=float)
        self.compare = np.array(compare, dtype=float)
        self.method = method
        self.n_samples = self.compare.shape[0]
        self.n_indicators = self.compare.shape[1]
    
    def normalize(self, method='mean'):
        """标准化处理"""
        all_data = np.vstack([self.reference, self.compare])
        
        if method == 'mean':
            mean_vals = all_data.mean(axis=0)
            mean_vals[mean_vals == 0] = 1
            ref_norm = self.reference / mean_vals
            comp_norm = self.compare / mean_vals
        elif method == 'minmax':
            min_vals = all_data.min(axis=0)
            max_vals = all_data.max(axis=0)
            range_vals = max_vals - min_vals
            range_vals[range_vals == 0] = 1
            ref_norm = (self.reference - min_vals) / range_vals
            comp_norm = (self.compare - min_vals) / range_vals
        else:
            ref_norm = self.reference
            comp_norm = self.compare
        
        return ref_norm, comp_norm
    
    def calculate_deltas(self):
        """计算差序列"""
        ref_norm, comp_norm = self.normalize()
        deltas = np.abs(comp_norm - ref_norm)
        return deltas
    
    def calculate_coefficients(self, rho=0.5):
        """计算关联系数"""
        deltas = self.calculate_deltas()
        
        min_delta = deltas.min()
        max_delta = deltas.max()
        
        coefficients = (min_delta + rho * max_delta) / (deltas + rho * max_delta)
        return coefficients
    
    def calculate_relational_degree(self, weights=None, rho=0.5):
        """计算关联度"""
        coefficients = self.calculate_coefficients(rho)
        
        if weights is None:
            weights = np.ones(self.n_indicators) / self.n_indicators
        
        degree = (coefficients * weights).sum(axis=1)
        return degree
    
    def rank(self, weights=None, rho=0.5):
        """排序"""
        degree = self.calculate_relational_degree(weights, rho)
        rank_idx = np.argsort(-degree)
        return rank_idx, degree
    
    def get_results(self, weights=None, rho=0.5):
        """获取完整结果"""
        coefficients = self.calculate_coefficients(rho)
        degree = self.calculate_relational_degree(weights, rho)
        rank_idx = np.argsort(-degree)
        
        results = {
            'coefficients': coefficients,
            'degree': degree,
            'rank': rank_idx
        }
        return results
    
    def report(self, sample_names=None, indicator_names=None, weights=None, rho=0.5):
        """生成报告"""
        coefficients = self.calculate_coefficients(rho)
        degree = self.calculate_relational_degree(weights, rho)
        rank_idx = np.argsort(-degree)
        
        print("=" * 70)
        print("灰色关联分析报告")
        print("=" * 70)
        
        print(f"\n参考序列: {self.reference}")
        print(f"关联系数计算方法: {self.method}")
        print(f"分辨率ρ: {rho}")
        
        print("\n【关联系数矩阵】")
        df_coeff = pd.DataFrame(
            coefficients,
            index=[sample_names[i] if sample_names else f"样本{i+1}" for i in range(self.n_samples)],
            columns=[indicator_names[j] if indicator_names else f"指标{j+1}" for j in range(self.n_indicators)]
        )
        print(df_coeff.to_string())
        
        print("\n【关联度排序】")
        for rank, idx in enumerate(rank_idx):
            name = sample_names[idx] if sample_names else f"样本{idx+1}"
            print(f"  第{rank+1}名: {name}, 关联度={degree[idx]:.4f}")
        
        print("=" * 70)


if __name__ == "__main__":
    # 示例：学生综合评价
    print("灰色关联分析示例：学生综合评价\n")
    
    # 参考序列（最优方案）
    reference = [95, 95, 95, 95]  # 最高分、最高出勤等
    
    # 比较序列（各学生）
    compare = [
        [85, 90, 88, 75],  # 学生A
        [92, 85, 90, 88],  # 学生B
        [78, 95, 82, 70],  # 学生C
        [95, 88, 96, 92],  # 学生D
        [88, 92, 85, 80],  # 学生E
    ]
    
    sample_names = ['学生A', '学生B', '学生C', '学生D', '学生E']
    indicator_names = ['成绩', '出勤', '作业', '竞赛']
    
    # 创建灰色关联分析模型
    gra = GreyRelationalAnalysis(reference, compare)
    
    # 输出结果
    gra.report(sample_names, indicator_names)
