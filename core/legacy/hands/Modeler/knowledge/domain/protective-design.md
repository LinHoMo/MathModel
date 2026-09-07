# 防护设计建模知识库

> 本文件提供数学建模竞赛中防护设计相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 高温防护服设计与优化
- 防弹衣材料选择与层数优化
- 抗震结构设计
- 隔热材料性能分析
- 多层防护结构温度场分析

### 1.2 常见约束条件
- 皮肤温度不超过阈值（如44°C）
- 防护时间要求（如工作30分钟）
- 材料厚度和重量限制
- 成本预算限制
- 活动舒适性要求

### 1.3 数据特点
- 材料参数：导热系数、密度、比热容
- 环境参数：温度、热流密度
- 时间数据：加热/冷却曲线
- 几何参数：各层厚度
- 约束数据：温度阈值、防护时间

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 多层热传导PDE | 温度场分析 | 物理意义明确 | 求解复杂 |
| 有限差分法 | 数值求解 | 实现简单 | 精度受限 |
| Thomas算法 | 三对角矩阵求解 | 高效稳定 | 仅适用于三对角系统 |
| 枚举优化 | 离散参数优化 | 简单可靠 | 维数灾难 |
| 整数规划 | 层数优化 | 精确求解 | 计算复杂 |
| 遗传算法 | 多参数优化 | 全局搜索 | 收敛慢 |

---

## 3. 数学基础

### 3.1 傅里叶定律

**热传导基本方程**：
```
q = -k * ∇T
```
其中：
- q: 热流密度 (W/m²)
- k: 导热系数 (W/(m·K))
- T: 温度 (K)

**一维稳态热传导**：
```
q = k * (T_hot - T_cold) / d
```

### 3.2 非稳态导热

**热传导方程（一维）**：
```
∂T/∂t = α * ∂²T/∂x²
α = k / (ρ * cp)
```
其中：
- α: 热扩散系数 (m²/s)
- ρ: 密度 (kg/m³)
- cp: 比热容 (J/(kg·K))

**多层介质热传导**：
```
界面条件: k₁ * ∂T₁/∂x = k₂ * ∂T₂/∂x  (热流连续)
          T₁ = T₂  (温度连续)
```

### 3.3 初始条件和边界条件

**初始条件**：
```
T(x, 0) = T₀(x)
```

**边界条件**：
```
第一类: T(0, t) = T_surface  (已知温度)
第二类: -k * ∂T/∂x = q  (已知热流)
第三类: -k * ∂T/∂x = h * (T - T_∞)  (对流换热)
```

### 3.4 温度约束优化

**优化模型**：
```
min Σ wᵢ * dᵢ  (最小化总厚度)
s.t. T_skin(t_end) ≤ T_max  (皮肤温度约束)
     dᵢ ≥ 0  (厚度非负)
     dᵢ ∈ D  (离散取值，如层数)
```

---

## 4. Python实现

### 4.1 多层热传导有限差分

```python
import numpy as np
from scipy.linalg import solve_banded

class MultilayerHeatTransfer:
    """多层介质热传导模型"""
    
    def __init__(self, layers, dx, dt):
        """
        Parameters
        ----------
        layers : list
            各层材料参数 [(k, rho, cp, thickness), ...]
        dx : float
            空间步长 (m)
        dt : float
            时间步长 (s)
        """
        self.layers = layers
        self.dx = dx
        self.dt = dt
        self.n_layers = len(layers)
        
        # 计算各层节点数
        self.n_nodes = [int(layer[3] / dx) + 1 for layer in layers]
        self.total_nodes = sum(self.n_nodes)
        
        # 初始化温度场
        self.T = np.zeros(self.total_nodes)
        self.T_new = np.zeros(self.total_nodes)
    
    def build_coefficient_matrix(self):
        """构建系数矩阵（三对角）"""
        n = self.total_nodes
        ab = np.zeros((3, n))  # [下对角, 主对角, 上对角]
        
        node_idx = 0
        for layer_idx, (k, rho, cp, thickness) in enumerate(self.layers):
            n_layer = self.n_nodes[layer_idx]
            alpha = k / (rho * cp)
            
            for i in range(n_layer):
                if layer_idx == 0 and i == 0:
                    # 左边界（第一类边界条件）
                    ab[1, node_idx] = 1
                elif layer_idx == self.n_layers - 1 and i == n_layer - 1:
                    # 右边界（第三类边界条件）
                    h = 10  # 对流换热系数
                    ab[0, node_idx] = 0
                    ab[1, node_idx] = 1 + h * self.dx / k
                    ab[2, node_idx] = -1
                else:
                    # 内部节点
                    r = alpha * self.dt / self.dx**2
                    ab[0, node_idx] = r  # 下对角
                    ab[1, node_idx] = -2 * r  # 主对角
                    ab[2, node_idx] = r  # 上对角
                
                node_idx += 1
        
        # 处理层间界面
        self._handle_interfaces(ab)
        
        return ab
    
    def _handle_interfaces(self, ab):
        """处理层间界面条件"""
        node_idx = 0
        for layer_idx in range(self.n_layers - 1):
            node_idx += self.n_nodes[layer_idx] - 1
            
            k1 = self.layers[layer_idx][0]
            k2 = self.layers[layer_idx + 1][0]
            
            # 界面热流连续
            ab[1, node_idx] = -(k1 + k2) / self.dx**2
            ab[2, node_idx] = k2 / self.dx**2
            ab[0, node_idx + 1] = k1 / self.dx**2
    
    def solve(self, T_surface, T_init, T_ambient, n_steps, h_conv=10):
        """
        求解温度场
        
        Parameters
        ----------
        T_surface : float
            外表面温度 (°C)
        T_init : float
            初始温度 (°C)
        T_ambient : float
            环境温度 (°C)
        n_steps : int
            时间步数
        h_conv : float
            对流换热系数 (W/(m²·K))
        
        Returns
        -------
        T_history : ndarray
            温度场历史 (n_steps, total_nodes)
        """
        # 初始化
        self.T[:] = T_init
        T_history = np.zeros((n_steps, self.total_nodes))
        
        # 构建系数矩阵
        ab = self.build_coefficient_matrix()
        
        # 右端项
        b = np.zeros(self.total_nodes)
        
        for step in range(n_steps):
            # 更新右端项
            b[:] = self.T
            
            # 边界条件
            b[0] = T_surface  # 左边界
            
            # 右边界（对流）
            b[-1] = h_conv * T_ambient * self.dt / (self.layers[-1][0] * self.dx)
            
            # 求解三对角方程组
            self.T_new = solve_banded((1, 1), ab, b)
            
            # 更新
            self.T[:] = self.T_new
            T_history[step, :] = self.T.copy()
        
        return T_history
    
    def get_skin_temperature(self, T_history):
        """获取皮肤温度曲线"""
        # 皮肤位于最内层（最后一层的最后一个节点）
        return T_history[:, -1]
```

### 4.2 Thomas算法

```python
import numpy as np

def thomas_algorithm(a, b, c, d):
    """
    Thomas算法求解三对角方程组
    
    a*x[i-1] + b*x[i] + c*x[i+1] = d[i]
    
    Parameters
    ----------
    a : ndarray
        下对角线元素 (n-1,)
    b : ndarray
        主对角线元素 (n,)
    c : ndarray
        上对角线元素 (n-1,)
    d : ndarray
        右端项 (n,)
    
    Returns
    -------
    x : ndarray
        解向量 (n,)
    """
    n = len(b)
    
    # 前向消元
    c_prime = np.zeros(n-1)
    d_prime = np.zeros(n)
    
    c_prime[0] = c[0] / b[0]
    d_prime[0] = d[0] / b[0]
    
    for i in range(1, n-1):
        m = b[i] - a[i-1] * c_prime[i-1]
        c_prime[i] = c[i] / m
        d_prime[i] = (d[i] - a[i-1] * d_prime[i-1]) / m
    
    # 最后一行
    m = b[n-1] - a[n-2] * c_prime[n-2]
    d_prime[n-1] = (d[n-1] - a[n-2] * d_prime[n-2]) / m
    
    # 回代
    x = np.zeros(n)
    x[n-1] = d_prime[n-1]
    
    for i in range(n-2, -1, -1):
        x[i] = d_prime[i] - c_prime[i] * x[i+1]
    
    return x

# 验证
def verify_thomas():
    """验证Thomas算法"""
    # 构建测试方程组
    n = 5
    a = np.array([1, 1, 1, 1])  # 下对角
    b = np.array([4, 4, 4, 4, 4])  # 主对角
    c = np.array([1, 1, 1, 1])  # 上对角
    d = np.array([5, 6, 6, 6, 5])  # 右端项
    
    x = thomas_algorithm(a, b, c, d)
    
    # 验证
    A = np.diag(b) + np.diag(a, -1) + np.diag(c, 1)
    residual = A @ x - d
    
    print(f"残差: {np.max(np.abs(residual)):.2e}")
    return x
```

### 4.3 防护服优化

```python
import numpy as np
from itertools import product

def optimize_protective_clothing(materials, T_max=44, t_protect=1800,
                                   weight_limit=5, cost_limit=1000):
    """
    防护服多层结构优化
    
    Parameters
    ----------
    materials : list
        材料列表 [(name, k, rho, cp, thickness_options, cost_per_m2), ...]
    T_max : float
        皮肤最高允许温度 (°C)
    t_protect : float
        防护时间 (s)
    weight_limit : float
        重量限制 (kg/m²)
    cost_limit : float
        成本限制 (元/m²)
    
    Returns
    -------
    best_design : dict
        最优设计方案
    """
    best_design = None
    best_weight = float('inf')
    
    # 枚举所有可能的组合
    thickness_options = [m[4] for m in materials]
    
    for combo in product(*thickness_options):
        # 检查总厚度
        total_thickness = sum(combo)
        
        # 检查重量
        total_weight = sum(combo[i] * materials[i][2] for i in range(len(materials)))
        if total_weight > weight_limit:
            continue
        
        # 检查成本
        total_cost = sum(combo[i] * materials[i][5] for i in range(len(materials)))
        if total_cost > cost_limit:
            continue
        
        # 热传导分析
        layers = [(materials[i][1], materials[i][2], materials[i][3], combo[i]) 
                  for i in range(len(materials))]
        
        model = MultilayerHeatTransfer(layers, dx=0.001, dt=1)
        T_history = model.solve(
            T_surface=100,  # 假设外表面温度100°C
            T_init=20,
            T_ambient=20,
            n_steps=t_protect
        )
        
        T_skin = model.get_skin_temperature(T_history)
        
        if np.max(T_skin) <= T_max:
            if total_weight < best_weight:
                best_weight = total_weight
                best_design = {
                    'thicknesses': combo,
                    'total_thickness': total_thickness,
                    'total_weight': total_weight,
                    'total_cost': total_cost,
                    'max_skin_temp': np.max(T_skin),
                    'T_skin_curve': T_skin
                }
    
    return best_design

def optimize_with_genetic_algorithm(materials, T_max=44, t_protect=1800):
    """
    使用遗传算法优化防护服设计
    """
    from scipy.optimize import differential_evolution
    
    def objective(x):
        """目标函数：最小化总重量"""
        thicknesses = [materials[i][4][int(x[i])] for i in range(len(materials))]
        
        total_weight = sum(thicknesses[i] * materials[i][2] 
                          for i in range(len(materials)))
        
        # 热传导分析
        layers = [(materials[i][1], materials[i][2], materials[i][3], thicknesses[i]) 
                  for i in range(len(materials))]
        
        model = MultilayerHeatTransfer(layers, dx=0.001, dt=1)
        T_history = model.solve(100, 20, 20, t_protect)
        T_skin = model.get_skin_temperature(T_history)
        
        # 约束惩罚
        penalty = 0
        if np.max(T_skin) > T_max:
            penalty = 1000 * (np.max(T_skin) - T_max)
        
        return total_weight + penalty
    
    # 变量边界（每层厚度选项的索引）
    bounds = [(0, len(materials[i][4]) - 1) for i in range(len(materials))]
    
    result = differential_evolution(objective, bounds, seed=42, maxiter=100)
    
    return result
```

### 4.4 温度场可视化

```python
import numpy as np
import matplotlib.pyplot as plt

def plot_temperature_field(T_history, dx, dt, layer_boundaries=None):
    """
    绘制温度场
    
    Parameters
    ----------
    T_history : ndarray
        温度场历史 (n_steps, n_nodes)
    dx : float
        空间步长
    dt : float
        时间步长
    layer_boundaries : list
        层间界面位置
    """
    n_steps, n_nodes = T_history.shape
    
    x = np.arange(n_nodes) * dx
    t = np.arange(n_steps) * dt
    
    X, T = np.meshgrid(x, t)
    
    plt.figure(figsize=(12, 6))
    plt.pcolormesh(X, T, T_history, cmap='hot', shading='auto')
    plt.colorbar(label='温度 (°C)')
    plt.xlabel('位置 (m)')
    plt.ylabel('时间 (s)')
    plt.title('温度场分布')
    
    # 标记层间界面
    if layer_boundaries:
        for boundary in layer_boundaries:
            plt.axvline(x=boundary, color='w', linestyle='--', linewidth=0.5)
    
    plt.tight_layout()
    plt.show()

def plot_skin_temperature(T_skin, dt, T_max=44):
    """绘制皮肤温度曲线"""
    t = np.arange(len(T_skin)) * dt
    
    plt.figure(figsize=(10, 5))
    plt.plot(t, T_skin, 'r-', linewidth=2)
    plt.axhline(y=T_max, color='b', linestyle='--', label=f'温度阈值 {T_max}°C')
    plt.xlabel('时间 (s)')
    plt.ylabel('皮肤温度 (°C)')
    plt.title('皮肤温度变化曲线')
    plt.legend()
    plt.grid(True)
    plt.show()
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 网格划分不当 | 数值振荡或精度差 | 满足稳定性条件 r≤0.5 |
| 界面条件错误 | 温度不连续 | 确保热流和温度连续 |
| 边界条件设置错误 | 结果不合理 | 仔细检查物理边界 |
| 忽略接触热阻 | 温度预测偏低 | 考虑层间接触热阻 |
| 离散化误差 | 与解析解偏差大 | 减小dx和dt |
| 未验证稳定性 | 计算发散 | 检查CFL条件 |

---

## 6. 验证方法

### 6.1 解析验证
- 与一维稳态热传导解析解对比
- 检查热流连续性

### 6.2 能量守恒验证
- 检查输入热量 = 储存热量 + 输出热量

### 6.3 网格收敛性验证
- 减小网格尺寸，检查结果变化

### 6.4 与实验数据对比
- 与已知防护服测试数据对比

### 6.5 物理合理性检查
- 温度变化趋势是否合理
- 皮肤温度是否在安全范围内

---

## 7. 真题案例

### 7.1 2018A 高温作业专用服装设计

**题目要点**：
- 设计高温作业防护服
- 多层材料选择与厚度优化
- 保证皮肤温度不超过44°C
- 防护时间至少30分钟

**解题思路**：
1. 建立多层热传导模型
2. 确定各层材料热物性参数
3. 使用有限差分法求解温度场
4. 优化各层厚度以满足约束
5. 考虑重量和成本约束

**关键公式**：
```
热传导方程: ∂T/∂t = α * ∂²T/∂x²
界面条件: k₁∂T₁/∂x = k₂∂T₂/∂x, T₁ = T₂
边界条件: T(0,t) = 100°C, -k∂T/∂x = h(T-T_∞)
```

**参考答案**：
- 外层：耐高温材料（如芳纶），厚度约2-3mm
- 中间层：隔热材料（如气凝胶），厚度约5-8mm
- 内层：舒适层（如棉），厚度约1-2mm
- 总厚度：约8-13mm
- 皮肤最高温度：约42-44°C

---

## 8. 验证清单

- [ ] 热传导方程正确（∂T/∂t = α∂²T/∂x²）
- [ ] 界面条件满足（热流连续、温度连续）
- [ ] 边界条件设置正确
- [ ] 数值稳定性满足（r≤0.5）
- [ ] 皮肤温度≤44°C
- [ ] 防护时间≥30分钟
- [ ] 总厚度和重量在合理范围
- [ ] 能量守恒检验通过
