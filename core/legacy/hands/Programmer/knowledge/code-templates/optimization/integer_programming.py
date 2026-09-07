"""
0-1整数规划求解模板
来源: 数学建模常用方法
适用问题: 背包问题、选址问题、指派问题、排班问题
输入: 目标函数系数、约束矩阵、约束类型
输出: 最优解、最优值、约束松弛分析
"""

import numpy as np
from typing import List, Tuple, Optional, Dict
import warnings
warnings.filterwarnings('ignore')


class IntegerProgramming:
    """
    0-1整数规划求解器 (使用PuLP库)
    
    标准形式:
        min/max  c^T x
        s.t.     A_ub x <= b_ub
                 A_eq x = b_eq
                 x_i ∈ {0, 1}
    
    Parameters
    ----------
    n_vars : int
        决策变量数量
    sense : str
        'min' 或 'max'
    """

    def __init__(self, n_vars: int, sense: str = 'min'):
        self.n_vars = n_vars
        self.sense = sense
        self.obj_coeffs = np.zeros(n_vars)
        self.constraints = []
        self.var_names = [f'x_{i}' for i in range(n_vars)]

    def set_objective(self, coeffs: np.ndarray, quadratic: Optional[np.ndarray] = None):
        """
        设置目标函数
        min/max c^T x + 0.5 x^T Q x
        """
        self.obj_coeffs = np.array(coeffs, dtype=float)
        self.quadratic = quadratic

    def add_constraint(self, coeffs: np.ndarray, rhs: float, sense: str = '<=',
                       name: str = ''):
        """
        添加线性约束
        
        Parameters
        ----------
        coeffs : ndarray
            约束系数向量
        rhs : float
            右端常数
        sense : str
            '<=', '>=', '='
        name : str
            约束名称
        """
        if name == '':
            name = f'constraint_{len(self.constraints)}'
        self.constraints.append({
            'coeffs': np.array(coeffs, dtype=float),
            'rhs': float(rhs),
            'sense': sense,
            'name': name
        })

    def solve(self) -> Dict:
        """
        使用PuLP求解0-1整数规划
        
        Returns
        -------
        result : dict
            包含最优解、最优值、状态
        """
        try:
            import pulp
        except ImportError:
            print("请安装PuLP: pip install pulp")
            return {'status': 'error', 'message': 'PuLP not installed'}

        # 创建问题
        prob = pulp.LpProblem('IntegerProgramming', 
                              pulp.LpMinimize if self.sense == 'min' else pulp.LpMaximize)

        # 创建0-1变量
        x = [pulp.LpVariable(self.var_names[i], cat='Binary') for i in range(self.n_vars)]

        # 目标函数
        prob += pulp.lpSum(self.obj_coeffs[i] * x[i] for i in range(self.n_vars))

        # 添加约束
        for cons in self.constraints:
            expr = pulp.lpSum(cons['coeffs'][i] * x[i] for i in range(self.n_vars))
            if cons['sense'] == '<=':
                prob += expr <= cons['rhs'], cons['name']
            elif cons['sense'] == '>=':
                prob += expr >= cons['rhs'], cons['name']
            else:
                prob += expr == cons['rhs'], cons['name']

        # 求解
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        # 提取结果
        status = pulp.LpStatus[prob.status]
        solution = np.array([x[i].varValue for i in range(self.n_vars)])
        obj_value = pulp.value(prob.objective)

        return {
            'status': status,
            'solution': solution.astype(int),
            'objective': obj_value,
            'n_vars': self.n_vars,
            'n_constraints': len(self.constraints)
        }


def solve_knapsack(weights: np.ndarray, values: np.ndarray,
                   capacity: float) -> Dict:
    """
    0-1背包问题
    
    max  Σ v_i x_i
    s.t. Σ w_i x_i <= C
         x_i ∈ {0, 1}
    
    Parameters
    ----------
    weights : ndarray
        物品重量
    values : ndarray
        物品价值
    capacity : float
        背包容量
    """
    n = len(weights)
    ip = IntegerProgramming(n, sense='max')
    ip.set_objective(values)
    ip.add_constraint(weights, capacity, '<=', 'capacity')
    
    result = ip.solve()
    
    # 分析结果
    selected = np.where(result['solution'] == 1)[0]
    total_weight = weights[selected].sum()
    total_value = values[selected].sum()
    
    result['selected_items'] = selected
    result['total_weight'] = total_weight
    result['total_value'] = total_value
    
    return result


def solve_facility_location(n_facilities: int, n_customers: int,
                            fixed_costs: np.ndarray, variable_costs: np.ndarray,
                            demands: np.ndarray, capacities: np.ndarray,
                            max_facilities: int) -> Dict:
    """
    设施选址问题 (Fixed-Charge Facility Location)
    
    min  Σ f_i y_i + Σ Σ c_ij x_ij
    s.t. Σ_j x_ij = d_i  (每个客户需求满足)
         Σ_i x_ij <= K_j y_j  (设施容量限制)
         Σ y_i <= p  (最多开设p个设施)
         x_ij >= 0, y_i ∈ {0,1}
    """
    n_x = n_facilities * n_customers  # x变量数量
    n_y = n_facilities  # y变量数量
    n_total = n_x + n_y

    ip = IntegerProgramming(n_total, sense='min')

    # 目标函数: 固定成本 + 变量成本
    obj = np.zeros(n_total)
    obj[:n_x] = variable_costs.flatten()
    obj[n_x:] = fixed_costs
    ip.set_objective(obj)

    # 需求约束: 每个客户被服务一次
    for j in range(n_customers):
        coeffs = np.zeros(n_total)
        for i in range(n_facilities):
            coeffs[i * n_customers + j] = 1
        ip.add_constraint(coeffs, demands[j], '=', f'demand_{j}')

    # 容量约束
    for i in range(n_facilities):
        coeffs = np.zeros(n_total)
        coeffs[i * n_customers:(i + 1) * n_customers] = 1
        coeffs[n_x + i] = -capacities[i]
        ip.add_constraint(coeffs, 0, '<=', f'capacity_{i}')

    # 最多开设p个设施
    coeffs = np.zeros(n_total)
    coeffs[n_x:] = 1
    ip.add_constraint(coeffs, max_facilities, '<=', 'max_facilities')

    result = ip.solve()

    # 解析结果
    y = result['solution'][n_x:]
    x = result['solution'][:n_x].reshape(n_facilities, n_customers)
    opened = np.where(y == 1)[0]

    result['opened_facilities'] = opened
    result['assignment'] = x
    result['n_opened'] = len(opened)

    return result


def run_example():
    """示例: 背包问题 + 设施选址"""
    print("=" * 60)
    print("0-1整数规划求解示例")
    print("=" * 60)

    # 示例1: 0-1背包问题
    print("\n--- 示例1: 0-1背包问题 ---")
    np.random.seed(42)
    n_items = 10
    weights = np.random.randint(1, 20, n_items).astype(float)
    values = np.random.randint(10, 100, n_items).astype(float)
    capacity = 50.0

    print(f"物品数量: {n_items}")
    print(f"背包容量: {capacity}")
    print(f"物品重量: {weights}")
    print(f"物品价值: {values}")

    result = solve_knapsack(weights, values, capacity)
    print(f"\n最优解: x = {result['solution']}")
    print(f"选中物品: {result['selected_items']}")
    print(f"总重量: {result['total_weight']}/{capacity}")
    print(f"总价值: {result['total_value']}")
    print(f"状态: {result['status']}")

    # 示例2: 简单整数规划
    print("\n--- 示例2: 混合整数规划 ---")
    ip = IntegerProgramming(4, sense='min')
    ip.set_objective(np.array([2, 3, 1, 4], dtype=float))
    ip.add_constraint(np.array([1, 1, 0, 0]), 5, '<=', 'c1')
    ip.add_constraint(np.array([0, 0, 1, 1]), 4, '<=', 'c2')
    ip.add_constraint(np.array([1, 0, 1, 0]), 3, '<=', 'c3')
    ip.add_constraint(np.array([0, 1, 0, 1]), 6, '<=', 'c4')

    result = ip.solve()
    print(f"最优解: x = {result['solution']}")
    print(f"最优值: {result['objective']}")
    print(f"状态: {result['status']}")

    # 验证约束
    print("\n约束验证:")
    for cons in ip.constraints:
        lhs = cons['coeffs'] @ result['solution']
        print(f"  {cons['name']}: {lhs} {cons['sense']} {cons['rhs']}")


if __name__ == "__main__":
    run_example()
