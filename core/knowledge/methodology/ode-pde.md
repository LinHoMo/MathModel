# 微分方程数值求解方法论

> 本文档提供微分方程数值求解的完整方法论，包括ODE、PDE、有限差分法等核心方法。

---

## 一、方法选择决策树

```
微分方程求解
├── 方程类型？
│   ├── 常微分方程(ODE) → 数值积分方法
│   │   ├── 初值问题 → Euler/RK4/odeint
│   │   └── 边值问题 → 打靶法/有限差分
│   └── 偏微分方程(PDE) → 空间离散化
│       ├── 抛物型(热传导) → 显式/隐式差分
│       ├── 双曲型(波动) → 特征线法/差分
│       └── 椭圆型(拉普拉斯) → 迭代法
├── 线性/非线性？
│   ├── 线性 → 直接法/迭代法
│   └── 非线性 → 线性化/迭代
└── 稳定性要求？
    ├── 刚性方程 → 隐式方法
    └── 非刚性 → 显式方法
```

---

## 二、常微分方程初值问题

### 2.1 Euler法

```python
def euler_method(f, y0, t_span, h=0.01):
    """
    Euler法求解ODE
    f: dy/dt = f(t, y)
    y0: 初始条件
    t_span: (t0, tf)
    h: 步长
    """
    t0, tf = t_span
    t = np.arange(t0, tf + h, h)
    y = np.zeros(len(t))
    y[0] = y0
    
    for i in range(1, len(t)):
        y[i] = y[i-1] + h * f(t[i-1], y[i-1])
    
    return t, y
```

### 2.2 改进Euler法（Heun方法）

```python
def improved_euler(f, y0, t_span, h=0.01):
    """
    改进Euler法（预测-校正）
    """
    t0, tf = t_span
    t = np.arange(t0, tf + h, h)
    y = np.zeros(len(t))
    y[0] = y0
    
    for i in range(1, len(t)):
        k1 = f(t[i-1], y[i-1])
        k2 = f(t[i], y[i-1] + h * k1)
        y[i] = y[i-1] + h/2 * (k1 + k2)
    
    return t, y
```

### 2.3 Runge-Kutta法（RK4）

```python
def runge_kutta_4(f, y0, t_span, h=0.01):
    """
    经典四阶Runge-Kutta法
    """
    t0, tf = t_span
    t = np.arange(t0, tf + h, h)
    y = np.zeros(len(t))
    y[0] = y0
    
    for i in range(1, len(t)):
        k1 = f(t[i-1], y[i-1])
        k2 = f(t[i-1] + h/2, y[i-1] + h/2 * k1)
        k3 = f(t[i-1] + h/2, y[i-1] + h/2 * k2)
        k4 = f(t[i-1] + h, y[i-1] + h * k3)
        
        y[i] = y[i-1] + h/6 * (k1 + 2*k2 + 2*k3 + k4)
    
    return t, y
```

### 2.4 scipy.integrate.odeint

```python
from scipy.integrate import odeint

def solve_ode_scipy(f, y0, t_span, h=0.01):
    """
    使用scipy求解ODE
    """
    t0, tf = t_span
    t = np.arange(t0, tf + h, h)
    y = odeint(f, y0, t)
    return t, y.flatten()
```

### 2.5 刚性方程求解

```python
from scipy.integrate import solve_ivp

def solve_stiff_ode(f, y0, t_span):
    """
    求解刚性ODE（使用BDF方法）
    """
    sol = solve_ivp(f, t_span, y0, method='BDF', dense_output=True)
    return sol
```

---

## 三、常微分方程边值问题

### 3.1 打靶法

```python
def shooting_method(f, bc, t_span, h=0.01, tol=1e-6):
    """
    打靶法求解边值问题
    f: dy/dt = f(t, y)
    bc: 边界条件函数 bc(y0, yf) = 0
    """
    t0, tf = t_span
    
    # 猜测初始斜率
    slope0 = 0.0
    slope1 = 1.0
    
    # 求解两个初值问题
    def ode_func(t, y):
        return [y[1], f(t, y)]
    
    # 第一次猜测
    sol0 = solve_ivp(ode_func, t_span, [0, slope0], dense_output=True)
    res0 = bc(sol0.y[0, 0], sol0.y[0, -1])
    
    # 第二次猜测
    sol1 = solve_ivp(ode_func, t_span, [0, slope1], dense_output=True)
    res1 = bc(sol1.y[0, 0], sol1.y[0, -1])
    
    # 割线法迭代
    for _ in range(100):
        slope_new = slope1 - res1 * (slope1 - slope0) / (res1 - res0)
        
        sol = solve_ivp(ode_func, t_span, [0, slope_new], dense_output=True)
        res = bc(sol.y[0, 0], sol.y[0, -1])
        
        if abs(res) < tol:
            return sol.t, sol.y[0]
        
        slope0, res0 = slope1, res1
        slope1, res1 = slope_new, res
    
    return sol.t, sol.y[0]
```

---

## 四、偏微分方程有限差分法

### 4.1 热传导方程（抛物型）

```python
def heat_equation_explicit(u0, x_grid, t_grid, alpha):
    """
    显式差分法求解热传导方程
    ∂u/∂t = α ∂²u/∂x²
    """
    nx = len(x_grid)
    nt = len(t_grid)
    dx = x_grid[1] - x_grid[0]
    dt = t_grid[1] - t_grid[0]
    
    u = np.zeros((nt, nx))
    u[0, :] = u0
    
    r = alpha * dt / dx**2  # 稳定性条件：r <= 0.5
    
    if r > 0.5:
        print(f"警告：r={r:.2f} > 0.5，数值不稳定")
    
    for n in range(1, nt):
        for i in range(1, nx-1):
            u[n, i] = u[n-1, i] + r * (u[n-1, i+1] - 2*u[n-1, i] + u[n-1, i-1])
        
        # 边界条件
        u[n, 0] = u[n-1, 0] + r * (u[n-1, 1] - 2*u[n-1, 0] + u[n-1, -1])
        u[n, -1] = u[n, 0]  # 周期边界
    
    return u

def heat_equation_implicit(u0, x_grid, t_grid, alpha):
    """
    隐式差分法求解热传导方程（无条件稳定）
    """
    nx = len(x_grid)
    nt = len(t_grid)
    dx = x_grid[1] - x_grid[0]
    dt = t_grid[1] - t_grid[0]
    
    r = alpha * dt / dx**2
    
    # 构建三对角矩阵
    A = np.zeros((nx-2, nx-2))
    for i in range(nx-2):
        A[i, i] = 1 + 2*r
        if i > 0:
            A[i, i-1] = -r
        if i < nx-3:
            A[i, i+1] = -r
    
    u = np.zeros((nt, nx))
    u[0, :] = u0
    
    for n in range(1, nt):
        b = u[n-1, 1:-1].copy()
        b[0] += r * u[n, 0]
        b[-1] += r * u[n, -1]
        
        u[n, 1:-1] = np.linalg.solve(A, b)
        u[n, 0] = u[n, -1]  # 周期边界
    
    return u
```

### 4.2 波动方程（双曲型）

```python
def wave_equation(u0, v0, x_grid, t_grid, c):
    """
    有限差分法求解波动方程
    ∂²u/∂t² = c² ∂²u/∂x²
    """
    nx = len(x_grid)
    nt = len(t_grid)
    dx = x_grid[1] - x_grid[0]
    dt = t_grid[1] - t_grid[0]
    
    r = c * dt / dx  # CFL条件：r <= 1
    
    u = np.zeros((nt, nx))
    u[0, :] = u0
    u[1, :] = u0 + dt * v0  # 初始速度
    
    for n in range(1, nt-1):
        for i in range(1, nx-1):
            u[n+1, i] = 2*u[n, i] - u[n-1, i] + r**2 * (u[n, i+1] - 2*u[n, i] + u[n, i-1])
        
        # 边界条件
        u[n+1, 0] = u[n+1, 1]
        u[n+1, -1] = u[n+1, -2]
    
    return u
```

### 4.3 拉普拉斯方程（椭圆型）

```python
def laplace_equation(u_init, bc_func, x_grid, y_grid, tol=1e-6, max_iter=1000):
    """
    迭代法求解拉普拉斯方程
    ∂²u/∂x² + ∂²u/∂y² = 0
    """
    nx, ny = len(x_grid), len(y_grid)
    u = u_init.copy()
    
    dx = x_grid[1] - x_grid[0]
    dy = y_grid[1] - y_grid[0]
    
    for iteration in range(max_iter):
        u_old = u.copy()
        
        for i in range(1, nx-1):
            for j in range(1, ny-1):
                u[i, j] = 0.25 * (u[i+1, j] + u[i-1, j] + u[i, j+1] + u[i, j-1])
        
        # 应用边界条件
        u = bc_func(u, x_grid, y_grid)
        
        # 收敛检查
        if np.max(np.abs(u - u_old)) < tol:
            print(f"收敛于第{iteration+1}次迭代")
            break
    
    return u
```

---

## 五、竞赛常见场景

### 5.1 物理建模

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 热传导 | 有限差分法 | A070, A147 |
| 波动传播 | 特征线法/差分 | A022, A171 |
| 流体流动 | 有限体积法 | A092 |

### 5.2 工程应用

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 结构变形 | 有限元法 | D017, D026 |
| 电路仿真 | ODE求解 | D033 |
| 控制系统 | 状态空间 | A196 |

### 5.3 生物/化学

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 种群动力学 | Lotka-Volterra方程 | C101 |
| 化学反应动力学 | 刚性ODE | B007 |
| 扩散过程 | 反应扩散方程 | A147 |

---

## 六、参考资源

### 6.1 教材推荐

- 《数值求解微分方程》（李荣华）
- 《偏微分方程数值解法》（陆金甫）
- 《Finite Difference Methods》（Strikwerda）

### 6.2 Python库

- scipy.integrate：ODE求解器
- FEniCS：有限元方法
- FiPy：有限差分PDE

### 6.3 检查清单

- [ ] 稳定性条件满足
- [ ] 收敛性验证
- [ ] 边界条件正确
- [ ] 时间步长合理
- [ ] 与解析解对比（如有）
