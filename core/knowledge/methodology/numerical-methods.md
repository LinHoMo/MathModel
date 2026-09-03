# 数值分析方法论

> 本文档提供数值分析的完整方法论，包括求根、数值积分、矩阵分解等核心方法。

---

## 一、方法选择决策树

```
数值分析问题
├── 方程求根？
│   ├── 单根 → 牛顿法
│   ├── 重根 → 割线法
│   ├── 区间根 → 二分法
│   └── 多根 → 遗传算法
├── 数值积分？
│   ├── 等距节点 → 梯形法/Simpson法
│   ├── 高精度 → 高斯求积
│   └── 高维 → 蒙特卡洛积分
├── 线性方程组？
│   ├── 小规模 → 直接法（LU分解）
│   ├── 大规模稀疏 → 迭代法（CG/GMRES）
│   └── 最小二乘 → QR分解
└── 矩阵分解？
│   ├── 特征值 → QR算法
│   ├── 奇异值 → SVD分解
│   └── 正交化 → Gram-Schmidt/QR
```

---

## 二、方程求根

### 2.1 二分法

```python
def bisection(f, a, b, tol=1e-6, max_iter=100):
    """
    二分法求根
    f: 目标函数
    a, b: 区间端点
    tol: 容差
    """
    if f(a) * f(b) > 0:
        raise ValueError("f(a)和f(b)必须异号")
    
    for i in range(max_iter):
        c = (a + b) / 2
        
        if abs(f(c)) < tol or (b - a) / 2 < tol:
            return c, i + 1
        
        if f(a) * f(c) < 0:
            b = c
        else:
            a = c
    
    return (a + b) / 2, max_iter
```

### 2.2 牛顿法

```python
def newton(f, df, x0, tol=1e-6, max_iter=100):
    """
    牛顿法求根
    f: 目标函数
    df: 导函数
    x0: 初始猜测
    """
    x = x0
    
    for i in range(max_iter):
        fx = f(x)
        
        if abs(fx) < tol:
            return x, i + 1
        
        dfx = df(x)
        if abs(dfx) < 1e-10:
            raise ValueError("导数为零")
        
        x = x - fx / dfx
    
    return x, max_iter
```

### 2.3 割线法

```python
def secant(f, x0, x1, tol=1e-6, max_iter=100):
    """
    割线法求根（不需要导数）
    """
    f0, f1 = f(x0), f(x1)
    
    for i in range(max_iter):
        if abs(f1) < tol:
            return x1, i + 1
        
        if abs(f1 - f0) < 1e-10:
            raise ValueError("函数值差异过小")
        
        x_new = x1 - f1 * (x1 - x0) / (f1 - f0)
        x0, f0 = x1, f1
        x1 = x_new
        f1 = f(x1)
    
    return x1, max_iter
```

### 2.4 不动点迭代

```python
def fixed_point_iteration(g, x0, tol=1e-6, max_iter=100):
    """
    不动点迭代 x = g(x)
    """
    x = x0
    
    for i in range(max_iter):
        x_new = g(x)
        
        if abs(x_new - x) < tol:
            return x_new, i + 1
        
        x = x_new
    
    return x, max_iter
```

---

## 三、数值积分

### 3.1 梯形法

```python
def trapezoidal(f, a, b, n=100):
    """
    梯形法数值积分
    n: 区间数
    """
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)
    y = f(x)
    
    integral = h * (y[0]/2 + np.sum(y[1:-1]) + y[-1]/2)
    return integral
```

### 3.2 Simpson法

```python
def simpson(f, a, b, n=100):
    """
    Simpson法数值积分（n必须为偶数）
    """
    if n % 2 != 0:
        n += 1
    
    h = (b - a) / n
    x = np.linspace(a, b, n + 1)
    y = f(x)
    
    integral = h/3 * (y[0] + 4*np.sum(y[1::2]) + 2*np.sum(y[2:-1:2]) + y[-1])
    return integral
```

### 3.3 高斯求积

```python
from numpy.polynomial.legendre import leggauss

def gauss_legendre(f, a, b, n=5):
    """
    高斯-勒让德求积
    """
    # 获取节点和权重
    nodes, weights = leggauss(n)
    
    # 变换到[a,b]区间
    t = 0.5 * (b - a) * nodes + 0.5 * (a + b)
    w = 0.5 * (b - a) * weights
    
    # 计算积分
    integral = np.sum(w * f(t))
    return integral
```

### 3.4 自适应积分

```python
def adaptive_simpson(f, a, b, tol=1e-6, max_depth=10):
    """
    自适应Simpson积分
    """
    def simpson_rule(f, a, b):
        c = (a + b) / 2
        h = b - a
        return h/6 * (f(a) + 4*f(c) + f(b))
    
    def adaptive(f, a, b, tol, whole, depth):
        c = (a + b) / 2
        left = simpson_rule(f, a, c)
        right = simpson_rule(f, c, b)
        current = left + right
        
        if abs(current - whole) <= 15 * tol or depth >= max_depth:
            return current + (current - whole) / 15
        
        return adaptive(f, a, c, tol/2, left, depth+1) + \
               adaptive(f, c, b, tol/2, right, depth+1)
    
    whole = simpson_rule(f, a, b)
    return adaptive(f, a, b, tol, whole, 0)
```

---

## 四、矩阵分解

### 4.1 LU分解

```python
import numpy as np
from scipy.linalg import lu

def lu_decomposition(A):
    """
    LU分解：A = LU
    """
    P, L, U = lu(A)
    return P, L, U

def solve_lu(A, b):
    """使用LU分解求解Ax=b"""
    P, L, U = lu(A)
    y = np.linalg.solve(L, P @ b)
    x = np.linalg.solve(U, y)
    return x
```

### 4.2 QR分解

```python
def qr_decomposition(A):
    """
    QR分解：A = QR
    """
    Q, R = np.linalg.qr(A)
    return Q, R

def solve_qr(A, b):
    """使用QR分解求解最小二乘问题"""
    Q, R = np.linalg.qr(A)
    x = np.linalg.solve(R, Q.T @ b)
    return x
```

### 4.3 SVD分解

```python
def svd_decomposition(A):
    """
    SVD分解：A = UΣV^T
    """
    U, s, Vt = np.linalg.svd(A)
    return U, s, Vt

def pseudoinverse(A):
    """使用SVD计算伪逆"""
    U, s, Vt = svd_decomposition(A)
    s_inv = np.where(s > 1e-10, 1/s, 0)
    return Vt.T @ np.diag(s_inv) @ U.T
```

### 4.4 特征值分解

```python
def eigen_decomposition(A):
    """
    特征值分解：A = VΛV⁻¹
    """
    eigenvalues, eigenvectors = np.linalg.eig(A)
    return eigenvalues, eigenvectors

def matrix_power(A, n):
    """使用特征值分解计算矩阵幂"""
    eigenvalues, eigenvectors = eigen_decomposition(A)
    Lambda = np.diag(eigenvalues ** n)
    return eigenvectors @ Lambda @ np.linalg.inv(eigenvectors)
```

---

## 五、迭代法求解线性方程组

### 5.1 Jacobi迭代

```python
def jacobi(A, b, x0=None, tol=1e-6, max_iter=100):
    """
    Jacobi迭代法
    """
    n = len(b)
    x = x0 if x0 is not None else np.zeros(n)
    
    D = np.diag(A)
    R = A - np.diag(D)
    
    for i in range(max_iter):
        x_new = (b - R @ x) / D
        
        if np.linalg.norm(x_new - x) < tol:
            return x_new, i + 1
        
        x = x_new
    
    return x, max_iter
```

### 5.2 Gauss-Seidel迭代

```python
def gauss_seidel(A, b, x0=None, tol=1e-6, max_iter=100):
    """
    Gauss-Seidel迭代法
    """
    n = len(b)
    x = x0 if x0 is not None else np.zeros(n)
    
    for i in range(max_iter):
        x_new = x.copy()
        
        for j in range(n):
            sum1 = np.dot(A[j, :j], x_new[:j])
            sum2 = np.dot(A[j, j+1:], x[j+1:])
            x_new[j] = (b[j] - sum1 - sum2) / A[j, j]
        
        if np.linalg.norm(x_new - x) < tol:
            return x_new, i + 1
        
        x = x_new
    
    return x, max_iter
```

---

## 六、竞赛常见场景

### 6.1 方程求根

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 物理方程求解 | 牛顿法 | A001, A070 |
| 参数估计 | 非线性最小二乘 | B007, B050 |
| 优化问题 | 梯度下降 | C142 |

### 6.2 数值积分

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 概率密度积分 | Simpson法 | C305 |
| 高维积分 | 蒙特卡洛 | A147 |
| 高精度积分 | 高斯求积 | A092 |

### 6.3 线性代数

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 最小二乘 | QR分解 | B195 |
| 特征值问题 | QR算法 | A022 |
| 矩阵求逆 | SVD分解 | D033 |

---

## 七、参考资源

### 7.1 教材推荐

- 《数值分析》（李庆扬）
- 《矩阵计算》（Golub）
- 《Numerical Methods》（Burden）

### 7.2 Python库

- numpy：基础数值计算
- scipy.linalg：线性代数
- scipy.optimize：优化求根

### 7.3 检查清单

- [ ] 收敛性验证
- [ ] 数值稳定性检查
- [ ] 误差分析完成
- [ ] 矩阵条件数检查
- [ ] 迭代次数合理
