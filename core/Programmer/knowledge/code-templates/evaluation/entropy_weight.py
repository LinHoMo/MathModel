"""
模板来源: resources/code-templates/evaluation/entropy_weight.py
修改说明: 
  - 新增熵权法模板
  - 支持正向/负向指标处理
"""
import numpy as np
import pandas as pd


class EntropyWeight:
    """熵权法确定指标权重"""
    
    def __init__(self, data):
        """
        data: DataFrame或ndarray，行为样本，列为指标
        """
        self.data = np.array(data, dtype=float)
        self.n_samples, self.n_indicators = self.data.shape
        self.weights = None
        self.entropy = None
    
    def normalize(self, method='positive'):
        """
        标准化处理
        method: 'positive'正向指标, 'negative'负向指标
        """
        min_vals = self.data.min(axis=0)
        max_vals = self.data.max(axis=0)
        
        # 避免除零
        range_vals = max_vals - min_vals
        range_vals[range_vals == 0] = 1
        
        if method == 'positive':
            normalized = (self.data - min_vals) / range_vals
        else:
            normalized = (max_vals - self.data) / range_vals
        
        # 处理零值（避免ln(0)）
        normalized = normalized + 1e-10
        
        return normalized
    
    def calculate_entropy(self):
        """计算信息熵"""
        normalized = self.normalize()
        
        # 计算比重
        p = normalized / normalized.sum(axis=0)
        
        # 计算信息熵
        k = 1 / np.log(self.n_samples)
        self.entropy = -k * (p * np.log(p)).sum(axis=0)
        
        return self.entropy
    
    def calculate_weights(self):
        """计算权重"""
        if self.entropy is None:
            self.calculate_entropy()
        
        # 差异系数
        d = 1 - self.entropy
        
        # 权重
        self.weights = d / d.sum()
        
        return self.weights
    
    def get_comprehensive_score(self, weights=None):
        """计算综合得分"""
        if weights is None:
            weights = self.calculate_weights()
        
        normalized = self.normalize()
        scores = (normalized * weights).sum(axis=1)
        
        return scores
    
    def get_results(self):
        """获取完整结果"""
        if self.weights is None:
            self.calculate_weights()
        
        results = {
            'entropy': self.entropy,
            'weights': self.weights,
            'diversity': 1 - self.entropy,
            'scores': self.get_comprehensive_score()
        }
        return results
    
    def report(self, indicator_names=None):
        """生成报告"""
        if self.weights is None:
            self.calculate_weights()
        
        print("=" * 60)
        print("熵权法分析报告")
        print("=" * 60)
        
        print("\n【指标权重】")
        for i in range(self.n_indicators):
            name = indicator_names[i] if indicator_names else f"指标{i+1}"
            print(f"  {name}: 权重={self.weights[i]:.4f}, "
                  f"信息熵={self.entropy[i]:.4f}, "
                  f"差异系数={1-self.entropy[i]:.4f}")
        
        print("\n【综合得分】")
        scores = self.get_comprehensive_score()
        sorted_idx = np.argsort(-scores)
        for rank, idx in enumerate(sorted_idx):
            print(f"  第{rank+1}名: 样本{idx+1}, 得分={scores[idx]:.4f}")
        
        print("=" * 60)


if __name__ == "__main__":
    # 示例：学生综合评价
    print("熵权法示例：学生综合评价\n")
    
    # 数据：行为学生，列为指标
    data = pd.DataFrame({
        '成绩': [85, 92, 78, 95, 88, 76, 91],
        '出勤': [90, 85, 95, 88, 92, 80, 87],
        '作业': [88, 90, 82, 96, 85, 78, 93],
        '竞赛': [75, 88, 70, 92, 80, 65, 85]
    })
    
    indicator_names = ['成绩', '出勤', '作业', '竞赛']
    
    # 创建熵权法模型
    ew = EntropyWeight(data)
    
    # 输出结果
    ew.report(indicator_names)
