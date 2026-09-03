# 热传导建模知识库

> 本文件提供数学建模竞赛中热传导相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 高温防护服设计与多层材料隔热分析
- 焊接炉温度曲线优化
- 电子器件散热设计
- 建筑墙体保温性能分析
- 发动机叶片热防护
- 核反应堆热传导分析

### 1.2 常见约束条件
- 温度约束：最高/最低温度限值、温度梯度限制
- 材料约束：导热系数、比热容、密度
- 几何约束：厚度、面积、形状
- 边界条件：恒温、对流、辐射、绝热
- 时间约束：加热/冷却时间、稳态/瞬态要求
- 安全约束：热应力、材料失效温度

### 1.3 数据特点
- 材料参数：导热系数λ(W/m·K)、比热容c(J/kg·K)、密度ρ(kg/m³)
- 边界条件：环境温度、对流换热系数h(W/m²·K)
- 初始条件：初始温度分布
- 测量数据：温度传感器数据、热流密度
- 几何参数：各层厚度、接触热阻

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 解析法(分离变量) | 简单几何、线性问题 | 精确解、物理意义清晰 | 仅限简单情况 |
| 显式有限差分 | 瞬态热传导 | 实现简单 | 稳定性条件严格 |
| 隐式有限差分 | 瞬态热传导 | 无条件稳定 | 需解线性方程组 |
| 有限元法(FEM) | 复杂几何 | 适应性强 | 实现复杂 |
| 有限体积法(FVM) | 流固耦合 | 守恒性好 | 网格生成复杂 |
| Green函数法 | 基本解叠加 | 适用面广 | 计算量大 |

---

## 3. 数学基础

### 3.1 热传导控制方程

**三维非稳态热传导方程（含内热源）**：
```
ρc ∂T/∂t = ∂/∂x(λ ∂T/∂x) + ∂/∂y(λ ∂T/∂y) + ∂/∂z(λ ∂T/∂z) + q̇
```

**一维简化形式**：
```
∂T/∂t = α ∂²T/∂x² + q̇/(ρc)
```
其中热扩散率 α = λ/(ρc)

### 3.2 边界条件

**第一类（Dirichlet）- 已知温度**：
```
T|_{boundary} = T_s(t)
```

**第二类（Neumann）- 已知热流**：
```
-λ ∂T/∂n|_{boundary} = q(t)
```

**第三类（Robin）- 对流换热**：
```
-λ ∂T/∂n|_{boundary} = h(T - T∞)
```

### 3.3 多层平壁稳态导热

**接触热阻模型**：
```
T_i - T_{i+1} = q * L_i / λ_i
总热阻 R_total = Σ(L_i/λ_i) + 1/h₁ + 1/h₂
热流密度 q = (T_hot - T_cold) / R_total
```

### 3.4 有限差分离散（隐式格式）

**时间离散**：
```
(T_j^{n+1} - T_j^n) / Δt = α (T_{j+1}^{n+1} - 2T_j^{n+1} + T_{j-1}^{n+1}) / Δx²
```

整理为三对角矩阵：
```
-aT_{j-1}^{n+1} + (1+2a)T_j^{n+1} - aT_{j+1}^{n+1} = T_j^n
其中 a = αΔt/Δx²
```

---

## 4. Python实现

### 4.1 Thomas算法（三对角矩阵求解）

```python
import numpy as np

def thomas_solver(a, b, c, d):
    """
    Thomas算法求解三对角线性方程组 Ax = d
    
    Parameters
    ----------
    a : array
        下对角线 (n-1)
    b : array
        主对角线 (n)
    c : array
        上对角线 (n-1)
    d : array
        右侧向量 (n)
    
    Returns
    -------
    x : array
        解向量
    """
    n = len(b)
    
    # 前向消元
    c_prime = np.zeros(n-1)
    d_prime = np.zeros(n)
    
    c_prime[0] = c[0] / b[0]
    d_prime[0] = d[0] / b[0]
    
    for i in range(1, n):
        m = b[i] - a[i-1] * c_prime[i-1] if i < n else b[i]
        if i < n-1:
            c_prime[i] = c[i] / m
        d_prime[i] = (d[i] - a[i-1] * d_prime[i-1]) / m
    
    # 回代
    x = np.zeros(n)
    x[-1] = d_prime[-1]
    
    for i in range(n-2, -1, -1):
        x[i] = d_prime[i] - c_prime[i] * x[i+1]
    
    return x
```

### 4.2 隐式有限差分法求解一维热传导

```python
import numpy as np
from scipy.linalg import solve_banded

def implicit_heat_transfer_1d(L, T_total, nx, nt, alpha, T_init, T_left, T_right, h_left=None, h_right=None, T_inf_left=None, T_inf_right=None):
    """
    隐式有限差分法求解一维非稳态热传导
    
    Parameters
    ----------
    L : float
        厚度 (m)
    T_total : float
        总时间 (s)
    nx : int
        空间网格数
    nt : int
        时间步数
    alpha : float
        热扩散率 (m²/s)
    T_init : float
        初始温度 (°C)
    T_left, T_right : float
        边界温度 (°C)
    
    Returns
    -------
    T : array
        温度分布 (nt+1, nx+1)
    x : array
        空间坐标
    t : array
        时间坐标
    """
    dx = L / nx
    dt = T_total / nt
    r = alpha * dt / dx**2
    
    x = np.linspace(0, L, nx+1)
    t = np.linspace(0, T_total, nt+1)
    T = np.zeros((nt+1, nx+1))
    T[0, :] = T_init
    
    # 构建三对角矩阵系数
    # -a T_{j-1} + (1+2a) T_j - a T_{j+1} = T_j^n
    main_diag = np.ones(nx+1) * (1 + 2*r)
    upper_diag = np.ones(nx) * (-r)
    lower_diag = np.ones(nx) * (-r)
    
    # 边界条件处理
    if h_left is not None:  # Robin边界
        main_diag[0] = 1 + 2*r + 2*r*dx*h_left/alpha
    else:  # Dirichlet边界
        main_diag[0] = 1
        upper_diag[0] = 0
    
    if h_right is not None:  # Robin边界
        main_diag[-1] = 1 + 2*r + 2*r*dx*h_right/alpha
    else:  # Dirichlet边界
        main_diag[-1] = 1
        lower_diag[-1] = 0
    
    # 构建带状矩阵
    ab = np.zeros((3, nx+1))
    ab[0, 1:] = upper_diag
    ab[1, :] = main_diag
    ab[2, :-1] = lower_diag
    
    # 时间迭代
    for n in range(nt):
        rhs = T[n, :].copy()
        
        # 边界条件
        if h_left is not None:
            rhs[0] += 2*r*dx*h_left*T_inf_left/alpha
        else:
            rhs[0] = T_left
        
        if h_right is not None:
            rhs[-1] += 2*r*dx*h_right*T_inf_right/alpha
        else:
            rhs[-1] = T_right
        
        # 求解
        T[n+1, :] = solve_banded((1, 1), ab, rhs)
    
    return T, x, t
```

### 4.3 多层材料热传导

```python
import numpy as np

def multilayer_heat_transfer(layers, L_total, T_total, nx_total, alpha_list, T_init, T_left, T_right, h_left=None, h_right=None):
    """
    多层平壁热传导（隐式有限差分）
    
    Parameters
    ----------
    layers : list
        各层厚度 [L1, L2, ...]
    alpha_list : list
        各层热扩散率 [α1, α2, ...]
    
    Returns
    -------
    T : array
        温度分布
    x : array
        空间坐标
    """
    n_layers = len(layers)
    nx_per_layer = nx_total // n_layers
    
    # 计算每层网格数（按厚度比例分配）
    nx_list = [max(2, int(nx_total * L / L_total)) for L in layers]
    
    # 构建完整网格
    x_all = []
    alpha_all = []
    
    x_offset = 0
    for i, (L, alpha) in enumerate(zip(layers, alpha_list)):
        nx = nx_list[i]
        dx = L / (nx - 1)
        x_layer = np.linspace(x_offset, x_offset + L, nx)
        alpha_layer = np.full(nx, alpha)
        
        x_all.append(x_layer)
        alpha_all.append(alpha_layer)
        
        x_offset += L
    
    x = np.concatenate(x_all)
    alpha = np.concatenate(alpha_all)
    nx = len(x)
    
    # 隐式求解（简化版）
    dt = T_total / 1000
    T = np.zeros((1001, nx))
    T[0, :] = T_init
    
    for n in range(1000):
        # 构建三对角矩阵
        r = alpha * dt / (x[1] - x[0])**2
        
        main_diag = 1 + 2*r
        upper_diag = -r
        lower_diag = -r
        
        # 求解
        A = np.diag(main_diag) + np.diag(upper_diag[1:], 1) + np.diag(lower_diag[:-1], -1)
        rhs = T[n, :].copy()
        rhs[0] = T_left
        rhs[-1] = T_right
        
        T[n+1, :] = np.linalg.solve(A, rhs)
    
    return T, x
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 稳定性条件违反 | 显式格式发散 | 隐式格式或减小时间步长 |
| 单位不一致 | 温度/热流数量级错误 | 统一使用SI单位制 |
| 边界条件类型混淆 | 结果失真 | 明确区分Dirichlet/Neumann/Robin |
| 网格过粗 | 精度不足 | 进行网格收敛性验证 |
| 材料界面处理错误 | 接触热阻不连续 | 正确处理界面热流连续条件 |
| 初始条件不一致 | 初始阶段异常 | 合理设置初始温度分布 |
| 忽略辐射换热 | 高温结果偏低 | 高温时考虑Stefan-Boltzmann定律 |

---

## 6. 验证方法

### 6.1 解析解对比
- 一维稳态：q = ΔT / Σ(L_i/λ_i)
- 一维瞬态（半无限大物体）：T(x,t) = T_i + (T_s - T_i) * erfc(x/(2√(αt)))

### 6.2 网格收敛性验证
```
GCI = |f₂ - f₁| / r^p
其中 f₁, f₂ 为不同网格密度的结果，r 为网格比，p 为收敛阶
```

### 6.3 能量守恒验证
- 稳态：流入热量 = 流出热量
- 瞬态：能量增量 = 流入热量 - 流出热量 + 内热源

### 6.4 物理合理性检查
- 温度应在初始温度和边界温度之间
- 热流方向应从高温指向低温
- 温度分布应单调（无内热源时）

---

## 7. 真题案例

### 案例1：2018A 高温作业专用服装设计

**问题核心**：设计多层防护服，使人体皮肤温度不超过安全限值

**建模要点**：
1. 建立多层织物热传导模型（4-5层材料）
2. 考虑空气层热阻
3. 皮肤表面热边界条件（对流+辐射）
4. 目标：在满足安全约束下最小化服装厚度

**典型解法**：
```
1. 建立一维多层热传导方程
2. 隐式有限差分法求解
3. Thomas算法高效求解三对角矩阵
4. 参数灵敏度分析：各层厚度对温度的影响
5. 优化：遗传算法搜索最优厚度组合
```

**关键参数**：
- 外层：耐高温纤维，λ ≈ 0.04 W/m·K
- 隔热层：气凝胶，λ ≈ 0.02 W/m·K
- 内层：棉织物，λ ≈ 0.06 W/m·K
- 空气层：λ ≈ 0.026 W/m·K

### 案例2：2020A 焊接炉温度曲线

**问题核心**：设计焊接炉升温-保温-降温曲线

**建模要点**：
1. 建立炉内热传导和对流模型
2. 温度均匀性约束
3. 焊接工艺温度要求
4. 能耗最小化

---

## 8. 代码模板参考

- Thomas算法: 自定义实现或 `scipy.linalg.solve_banded`
- PDE求解: `scipy.integrate.solve_ivp`（半离散化）
- 有限元: `fenics` 或 `pyansys`
- 优化: `scipy.optimize.minimize`

---

## 9. 验证清单

- [ ] 热扩散率α = λ/(ρc) 计算正确
- [ ] 边界条件类型正确（Dirichlet/Neumann/Robin）
- [ ] 隐式格式无条件稳定
- [ ] 网格密度足够（进行收敛性验证）
- [ ] 能量守恒满足
- [ ] 温度分布物理合理
- [ ] 单位统一（m, s, W, K）
- [ ] 材料参数取自可靠来源

---

## 10. 参考文献

1. 杨世铭. 传热学. 高等教育出版社, 2006.
2. Incropera F P. Fundamentals of Heat and Mass Transfer. Wiley, 2011.
3. Patankar S V. Numerical Heat Transfer and Fluid Flow. CRC Press, 1980.
4. 王补宣. 工程传热传质学. 科学出版社, 2015.
