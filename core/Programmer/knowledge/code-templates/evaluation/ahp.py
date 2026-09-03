"""
模板来源: resources/code-templates/evaluation/ahp.py
修改说明: 
  - 新增AHP层次分析法模板
  - 支持一致性检验、组合赋权
"""
import numpy as np
import pandas as pd


class AHP:
    """AHP层次分析法"""
    
    def __init__(self, criteria, alternatives=None):
        """
        criteria: 准则层名称列表
        alternatives: 方案层名称列表
        """
        self.criteria = criteria
        self.alternatives = alternatives
        self.criteria_matrix = None
        self.criteria_weights = None
        self.alternative_matrices = {}
        self.alternative_weights = {}
        
        # 随机一致性指标RI表
        self.RI_table = {
            1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12,
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
        }
    
    def set_criteria_matrix(self, matrix):
        """设置准则层判断矩阵"""
        self.criteria_matrix = np.array(matrix, dtype=float)
        self.criteria_weights = self._calculate_weights(self.criteria_matrix)
        return self.criteria_weights
    
    def set_alternative_matrix(self, criterion, matrix):
        """设置方案层判断矩阵"""
        self.alternative_matrices[criterion] = np.array(matrix, dtype=float)
        self.alternative_weights[criterion] = self._calculate_weights(
            self.alternative_matrices[criterion]
        )
        return self.alternative_weights[criterion]
    
    def _calculate_weights(self, matrix):
        """计算权重（特征向量法）"""
        n = matrix.shape[0]
        
        # 计算特征值和特征向量
        eigenvalues, eigenvectors = np.linalg.eig(matrix)
        max_idx = np.argmax(eigenvalues.real)
        max_eigenvalue = eigenvalues[max_idx].real
        
        # 归一化特征向量
        weights = eigenvectors[:, max_idx].real
        weights = weights / weights.sum()
        
        # 一致性检验
        CI = (max_eigenvalue - n) / (n - 1) if n > 1 else 0
        RI = self.RI_table.get(n, 1.49)
        CR = CI / RI if RI > 0 else 0
        
        result = {
            'weights': weights,
            'max_eigenvalue': max_eigenvalue,
            'CI': CI,
            'RI': RI,
            'CR': CR,
            'consistent': CR < 0.1
        }
        
        return result
    
    def calculate_final_weights(self):
        """计算综合权重"""
        if self.criteria_weights is None:
            raise ValueError("请先设置准则层判断矩阵")
        
        n_alternatives = len(self.alternatives)
        final_weights = np.zeros(n_alternatives)
        
        for i, criterion in enumerate(self.criteria):
            if criterion in self.alternative_weights:
                alt_weights = self.alternative_weights[criterion]['weights']
                final_weights += self.criteria_weights['weights'][i] * alt_weights
        
        # 归一化
        final_weights = final_weights / final_weights.sum()
        
        return final_weights
    
    def get_results(self):
        """获取完整结果"""
        results = {
            'criteria_weights': self.criteria_weights,
            'alternative_weights': self.alternative_weights,
            'final_weights': self.calculate_final_weights()
        }
        return results
    
    def report(self):
        """生成报告"""
        print("=" * 60)
        print("AHP层次分析法报告")
        print("=" * 60)
        
        # 准则层权重
        print("\n【准则层权重】")
        for i, criterion in enumerate(self.criteria):
            print(f"  {criterion}: {self.criteria_weights['weights'][i]:.4f}")
        
        print(f"\n一致性检验: CR = {self.criteria_weights['CR']:.4f}")
        print(f"结论: {'通过' if self.criteria_weights['consistent'] else '未通过'}")
        
        # 方案层权重
        print("\n【方案层权重】")
        for criterion in self.criteria:
            if criterion in self.alternative_weights:
                print(f"\n  对准则 '{criterion}':")
                for j, alt in enumerate(self.alternatives):
                    print(f"    {alt}: {self.alternative_weights[criterion]['weights'][j]:.4f}")
        
        # 综合权重
        print("\n【综合权重】")
        final_weights = self.calculate_final_weights()
        sorted_idx = np.argsort(-final_weights)
        for rank, idx in enumerate(sorted_idx):
            print(f"  第{rank+1}名: {self.alternatives[idx]}, 权重={final_weights[idx]:.4f}")
        
        print("=" * 60)


def create_pairwise_matrix(values):
    """从一维比较值创建判断矩阵"""
    n = len(values)
    matrix = np.ones((n, n))
    
    for i in range(n):
        for j in range(n):
            if i != j:
                matrix[i, j] = values[i] / values[j]
    
    return matrix


if __name__ == "__main__":
    # 示例：学生评价
    print("AHP层次分析法示例：学生综合评价\n")
    
    # 准则层
    criteria = ['成绩', '出勤', '实践']
    criteria_matrix = [
        [1, 3, 1/2],
        [1/3, 1, 1/4],
        [2, 4, 1]
    ]
    
    # 方案层
    alternatives = ['学生A', '学生B', '学生C']
    
    # 对各准则的判断矩阵
    score_matrix = [
        [1, 2, 3],
        [1/2, 1, 2],
        [1/3, 1/2, 1]
    ]
    
    attendance_matrix = [
        [1, 1/2, 1/3],
        [2, 1, 1/2],
        [3, 2, 1]
    ]
    
    practice_matrix = [
        [1, 3, 5],
        [1/3, 1, 2],
        [1/5, 1/2, 1]
    ]
    
    # 创建AHP模型
    ahp = AHP(criteria, alternatives)
    ahp.set_criteria_matrix(criteria_matrix)
    ahp.set_alternative_matrix('成绩', score_matrix)
    ahp.set_alternative_matrix('出勤', attendance_matrix)
    ahp.set_alternative_matrix('实践', practice_matrix)
    
    # 输出结果
    ahp.report()
