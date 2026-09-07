"""
模板来源: resources/code-templates/evaluation/dea.py
修改说明: 
  - 新增DEA数据包络分析模板
  - 支持CCR模型、效率分析
"""
import numpy as np
from scipy.optimize import linprog


class DEA:
    """DEA数据包络分析"""
    
    def __init__(self, inputs, outputs, input_names=None, output_names=None, 
                 dmu_names=None):
        """
        inputs: 输入矩阵（行为DMU，列为输入指标）
        outputs: 输出矩阵（行为DMU，列为输出指标）
        """
        self.inputs = np.array(inputs, dtype=float)
        self.outputs = np.array(outputs, dtype=float)
        self.n_dmu = self.inputs.shape[0]
        self.n_input = self.inputs.shape[1]
        self.n_output = self.outputs.shape[1]
        
        self.input_names = input_names or [f"输入{i+1}" for i in range(self.n_input)]
        self.output_names = output_names or [f"输出{i+1}" for i in range(self.n_output)]
        self.dmu_names = dmu_names or [f"DMU{i+1}" for i in range(self.n_dmu)]
        
        self.results = None
    
    def ccr_model(self, dmu_idx):
        """CCR模型求解单个DMU效率"""
        # 目标函数：最大化输出加权和
        c = np.zeros(self.n_input + self.n_output)
        c[self.n_input:] = -self.outputs[dmu_idx]
        
        # 约束：输入加权和=1
        A_eq = np.zeros((1, self.n_input + self.n_output))
        A_eq[0, :self.n_input] = self.inputs[dmu_idx]
        b_eq = [1]
        
        # 约束：输出加权和 - 输入加权和 <= 0
        A_ub = np.zeros((self.n_dmu, self.n_input + self.n_output))
        for j in range(self.n_dmu):
            A_ub[j, :self.n_input] = -self.inputs[j]
            A_ub[j, self.n_input:] = self.outputs[j]
        b_ub = np.zeros(self.n_dmu)
        
        # 变量边界
        bounds = [(0, None)] * (self.n_input + self.n_output)
        
        # 求解
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                        bounds=bounds, method='highs')
        
        if result.success:
            efficiency = -result.fun
            weights = result.x
            return efficiency, weights
        else:
            return None, None
    
    def calculate_all(self):
        """计算所有DMU效率"""
        efficiencies = []
        weights_list = []
        
        for i in range(self.n_dmu):
            eff, w = self.ccr_model(i)
            efficiencies.append(eff)
            weights_list.append(w)
        
        self.results = {
            'efficiencies': np.array(efficiencies),
            'weights': weights_list,
            'efficient_dmus': np.where(np.array(efficiencies) >= 0.9999)[0],
            'inefficient_dmus': np.where(np.array(efficiencies) < 0.9999)[0]
        }
        
        return self.results
    
    def get_benchmarks(self, inefficient_idx):
        """获取无效DMU的标杆"""
        if self.results is None:
            self.calculate_all()
        
        weights = self.results['weights'][inefficient_idx]
        input_weights = weights[:self.n_input]
        output_weights = weights[self.n_input:]
        
        # 找标杆（权重非零的DMU）
        benchmark_input = np.where(input_weights > 1e-6)[0]
        benchmark_output = np.where(output_weights > 1e-6)[0]
        
        return {
            'input_weights': dict(zip(self.input_names, input_weights)),
            'output_weights': dict(zip(self.output_names, output_weights)),
            'input_benchmarks': [self.dmu_names[i] for i in benchmark_input],
            'output_benchmarks': [self.dmu_names[i] for i in benchmark_output]
        }
    
    def report(self):
        """生成报告"""
        if self.results is None:
            self.calculate_all()
        
        print("=" * 70)
        print("DEA数据包络分析报告")
        print("=" * 70)
        
        print(f"\nDMU数量: {self.n_dmu}")
        print(f"输入指标: {self.n_input}个")
        print(f"输出指标: {self.n_output}个")
        
        print("\n【效率值】")
        for i in range(self.n_dmu):
            status = "有效" if self.results['efficiencies'][i] >= 0.9999 else "无效"
            print(f"  {self.dmu_names[i]}: {self.results['efficiencies'][i]:.4f} ({status})")
        
        print(f"\n有效DMU: {[self.dmu_names[i] for i in self.results['efficient_dmus']]}")
        print(f"无效DMU: {[self.dmu_names[i] for i in self.results['inefficient_dmus']]}")
        
        print("\n【无效DMU分析】")
        for idx in self.results['inefficient_dmus']:
            print(f"\n  {self.dmu_names[idx]}:")
            benchmark = self.get_benchmarks(idx)
            print(f"    输入权重: {benchmark['input_weights']}")
            print(f"    输出权重: {benchmark['output_weights']}")
        
        print("=" * 70)


if __name__ == "__main__":
    # 示例：学生效率评价
    print("DEA示例：学生效率评价\n")
    
    # 输入：学生投入
    inputs = [
        [100, 20, 50],  # 学生A
        [120, 30, 60],  # 学生B
        [80, 15, 40],   # 学生C
        [150, 40, 80],  # 学生D
        [90, 25, 55],   # 学生E
    ]
    
    # 输出：学习成果
    outputs = [
        [85, 2, 1],  # 学生A
        [92, 3, 2],  # 学生B
        [78, 1, 0],  # 学生C
        [95, 4, 3],  # 学生D
        [88, 2, 1],  # 学生E
    ]
    
    # 创建DEA模型
    dea = DEA(
        inputs, outputs,
        input_names=['学习时间', '课外辅导', '资料费用'],
        output_names=['成绩', '证书数', '竞赛获奖'],
        dmu_names=['学生A', '学生B', '学生C', '学生D', '学生E']
    )
    
    # 输出结果
    dea.report()
