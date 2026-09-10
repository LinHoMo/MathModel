# 插值与拟合方法论

> 本文档提供插值与拟合的完整方法论，包括样条插值、拉格朗日插值、非线性拟合等核心方法。

---

## 一、方法选择决策树

```
插值与拟合问题
├── 数据点数量？
│   ├── 少量(≤20) → 拉格朗日/牛顿插值
│   └── 大量(>20) → 样条插值/最小二乘拟合
├── 是否需要过数据点？
│   ├── 必须过点 → 插值（拉格朗日/样条）
│   └── 不需要过点 → 拟合（最小二乘）
├── 数据噪声？
│   ├── 无噪声 → 插值
│   └── 有噪声 → 拟合（平滑）
└── 光滑性要求？
    ├── 高光滑性 → 三次样条
    └── 一般 → 线性插值/多项式拟合
```

---

## 二、拉格朗日插值

### 2.1 模型原理

**拉格朗日多项式**：

```
L(x) = Σ yᵢ × lᵢ(x)

其中 lᵢ(x) = Π(j≠i) (x - xⱼ) / (xᵢ - xⱼ)
```

### 2.2 完整代码框架

```python
import numpy as np

class LagrangeInterpolation:
    def __init__(self, x_data, y_data):
        self.x = np.array(x_data, dtype=float)
        self.y = np.array(y_data, dtype=float)
        self.n = len(x_data)
    
    def basis_polynomial(self, i, x):
        """计算拉格朗日基多项式"""
        result = 1.0
        for j in range(self.n):
            if j != i:
                result *= (x - self.x[j]) / (self.x[i] - self.x[j])
        return result
    
    def interpolate(self, x):
        """计算插值"""
        result = 0.0
        for i in range(self.n):
            result += self.y[i] * self.basis_polynomial(i, x)
        return result
    
    def interpolate_array(self, x_array):
        """批量插值"""
        return np.array([self.interpolate(x) for x in x_array])
    
    def get_polynomial_coeffs(self):
        """获取多项式系数（通过Newton形式转换）"""
        # 使用numpy的多项式拟合
        coeffs = np.polyfit(self.x, self.y, self.n - 1)
        return coeffs
    
    def evaluate_polynomial(self, x, coeffs):
        """使用系数计算多项式值"""
        return np.polyval(coeffs, x)
```

### 2.3 使用示例

```python
import matplotlib.pyplot as plt

# 数据点
x_data = [0, 1, 2, 3, 4]
y_data = [1, 2, 4, 8, 16]

# 创建插值
lagrange = LagrangeInterpolation(x_data, y_data)

# 生成插值曲线
x_plot = np.linspace(0, 4, 100)
y_plot = lagrange.interpolate_array(x_plot)

# 绘图
plt.figure(figsize=(10, 6))
plt.plot(x_data, y_data, 'ro', label='数据点')
plt.plot(x_plot, y_plot, 'b-', label='拉格朗日插值')
plt.xlabel('x')
plt.ylabel('y')
plt.legend()
plt.title('拉格朗日插值')
plt.savefig('figures/lagrange_interpolation.png', dpi=300)
plt.close()
```

---

## 三、三次样条插值

### 3.1 模型原理

**三次样条**：在每个区间上使用三次多项式，保证一阶和二阶导数连续。

**边界条件**：
- 自然样条：S''(x₀) = S''(xₙ) = 0
- 固定边界：指定S'(x₀)和S'(xₙ)

### 3.2 完整代码框架

```python
import numpy as np
from scipy.interpolate import CubicSpline, interp1d

class SplineInterpolation:
    def __init__(self, x_data, y_data, boundary_type='natural'):
        self.x = np.array(x_data, dtype=float)
        self.y = np.array(y_data, dtype=float)
        self.boundary_type = boundary_type
        
        # 创建样条
        if boundary_type == 'natural':
            self.cs = CubicSpline(self.x, self.y, bc_type='natural')
        elif boundary_type == 'clamped':
            self.cs = CubicSpline(self.x, self.y, bc_type='clamped')
        else:
            self.cs = CubicSpline(self.x, self.y)
    
    def interpolate(self, x):
        """计算插值"""
        return self.cs(x)
    
    def derivative(self, x, order=1):
        """计算导数"""
        return self.cs(x, order)
    
    def integral(self, a, b):
        """计算积分"""
        return self.cs.integrate(a, b)
    
    def get_coefficients(self):
        """获取各区间系数"""
        return self.cs.c
    
    def plot_spline(self, filename='figures/spline_interpolation.png'):
        """绘制样条曲线"""
        x_plot = np.linspace(self.x[0], self.x[-1], 200)
        y_plot = self.cs(x_plot)
        
        # 计算导数
        dy_plot = self.cs(x_plot, 1)
        d2y_plot = self.cs(x_plot, 2)
        
        fig, axes = plt.subplots(3, 1, figsize=(10, 12))
        
        # 样条曲线
        axes[0].plot(self.x, self.y, 'ro', label='数据点')
        axes[0].plot(x_plot, y_plot, 'b-', label='三次样条')
        axes[0].set_ylabel('f(x)')
        axes[0].legend()
        axes[0].set_title('三次样条插值')
        
        # 一阶导数
        axes[1].plot(x_plot, dy_plot, 'g-', label="f'(x)")
        axes[1].set_ylabel("f'(x)")
        axes[1].legend()
        axes[1].set_title('一阶导数')
        
        # 二阶导数
        axes[2].plot(x_plot, d2y_plot, 'm-', label="f''(x)")
        axes[2].set_ylabel("f''(x)")
        axes[2].set_xlabel('x')
        axes[2].legend()
        axes[2].set_title('二阶导数')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
```

### 3.3 使用示例

```python
# 数据点
x_data = [0, 1, 2, 3, 4, 5]
y_data = [0, 1, 4, 9, 16, 25]

# 自然样条
spline = SplineInterpolation(x_data, y_data, boundary_type='natural')

# 插值
x_test = 2.5
print(f"S({x_test}) = {spline.interpolate(x_test)}")
print(f"S'({x_test}) = {spline.derivative(x_test, 1)}")
print(f"S''({x_test}) = {spline.derivative(x_test, 2)}")

# 积分
print(f"∫S(x)dx from 0 to 5 = {spline.integral(0, 5)}")

# 绘图
spline.plot_spline()
```

---

## 四、牛顿插值

### 4.1 模型原理

**牛顿插值多项式**：

```
N(x) = f[x₀] + f[x₀,x₁](x-x₀) + f[x₀,x₁,x₂](x-x₀)(x-x₁) + ...
```

**差商表**：

| 阶数 | x₀ | x₁ | x₂ | ... |
|------|----|----|----|-----|
| 0阶 | f(x₀) | f(x₁) | f(x₂) | ... |
| 1阶 | f[x₀,x₁] | f[x₁,x₂] | ... | |
| 2阶 | f[x₀,x₁,x₂] | ... | | |

### 4.2 代码实现

```python
class NewtonInterpolation:
    def __init__(self, x_data, y_data):
        self.x = np.array(x_data, dtype=float)
        self.y = np.array(y_data, dtype=float)
        self.n = len(x_data)
        self.divided_diff_table = self._compute_divided_differences()
    
    def _compute_divided_differences(self):
        """计算差商表"""
        table = np.zeros((self.n, self.n))
        table[:, 0] = self.y
        
        for j in range(1, self.n):
            for i in range(self.n - j):
                table[i, j] = (table[i+1, j-1] - table[i, j-1]) / \
                              (self.x[i+j] - self.x[i])
        
        return table
    
    def interpolate(self, x):
        """计算插值"""
        result = self.divided_diff_table[0, 0]
        product_term = 1.0
        
        for j in range(1, self.n):
            product_term *= (x - self.x[j-1])
            result += self.divided_diff_table[0, j] * product_term
        
        return result
    
    def get_coefficients(self):
        """获取多项式系数"""
        return self.divided_diff_table[0, :]
```

---

## 五、非线性最小二乘拟合

### 5.1 模型原理

**目标**：min Σ(yᵢ - f(xᵢ; β))²

**常用模型**：
- 指数模型：y = a × exp(bx)
- 幂函数模型：y = a × x^b
- 对数模型：y = a + b × ln(x)
- Sigmoid模型：y = a / (1 + exp(-b(x-c)))

### 5.2 完整代码框架

```python
import numpy as np
from scipy.optimize import curve_fit
from scipy.optimize import leastsq

class NonlinearFitting:
    def __init__(self, x_data, y_data):
        self.x = np.array(x_data, dtype=float)
        self.y = np.array(y_data, dtype=float)
    
    def exponential(self, x, a, b):
        """指数模型 y = a * exp(b * x)"""
        return a * np.exp(b * x)
    
    def power(self, x, a, b):
        """幂函数模型 y = a * x^b"""
        return a * np.power(x, b)
    
    def logarithmic(self, x, a, b):
        """对数模型 y = a + b * ln(x)"""
        return a + b * np.log(x)
    
    def sigmoid(self, x, a, b, c):
        """Sigmoid模型 y = a / (1 + exp(-b * (x - c)))"""
        return a / (1 + np.exp(-b * (x - c)))
    
    def gaussian(self, x, a, b, c):
        """高斯模型 y = a * exp(-(x - b)^2 / (2 * c^2))"""
        return a * np.exp(-(x - b) ** 2 / (2 * c ** 2))
    
    def fit(self, model_func, p0=None):
        """拟合模型"""
        try:
            popt, pcov = curve_fit(model_func, self.x, self.y, p0=p0)
            perr = np.sqrt(np.diag(pcov))
            
            # 计算R²
            y_pred = model_func(self.x, *popt)
            ss_res = np.sum((self.y - y_pred) ** 2)
            ss_tot = np.sum((self.y - np.mean(self.y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            return {
                'params': popt,
                'pcov': pcov,
                'perr': perr,
                'r_squared': r_squared,
                'y_pred': y_pred
            }
        except Exception as e:
            print(f"拟合失败: {e}")
            return None
    
    def compare_models(self, models_dict):
        """比较多个模型"""
        results = {}
        
        for name, model_func in models_dict.items():
            result = self.fit(model_func)
            if result:
                results[name] = result
        
        # 按R²排序
        sorted_results = sorted(results.items(), 
                               key=lambda x: x[1]['r_squared'], 
                               reverse=True)
        
        return sorted_results
```

### 5.3 使用示例

```python
import matplotlib.pyplot as plt

# 生成带噪声的数据
np.random.seed(42)
x_data = np.linspace(0, 5, 50)
y_true = 2.5 * np.exp(0.8 * x_data)
y_data = y_true + np.random.normal(0, 0.5, len(x_data))

# 拟合
fitter = NonlinearFitting(x_data, y_data)

# 指数拟合
result = fitter.fit(fitter.exponential, p0=[1, 0.5])
print(f"指数拟合: a={result['params'][0]:.3f}, b={result['params'][1]:.3f}")
print(f"R² = {result['r_squared']:.4f}")

# 模型比较
models = {
    'exponential': fitter.exponential,
    'power': fitter.power,
    'sigmoid': fitter.sigmoid
}
comparison = fitter.compare_models(models)
print("\n模型比较（按R²排序）:")
for name, res in comparison:
    print(f"  {name}: R² = {res['r_squared']:.4f}")
```

---

## 六、竞赛常见场景

### 6.1 数据插补

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 缺失数据插补 | 三次样条 | C008, C052 |
| 传感器数据修复 | 拉格朗日插值 | A022, A171 |
| 时间序列对齐 | 线性插值 | C142 |

### 6.2 曲线拟合

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 物理规律拟合 | 非线性最小二乘 | A001, A070 |
| 经验公式建立 | 多项式拟合 | B007, B050 |
| 增长曲线拟合 | Sigmoid/Logistic | C101 |

### 6.3 数值积分/微分

| 场景 | 推荐方法 | 参考论文 |
|------|---------|---------|
| 数值积分 | 样条+积分 | A147 |
| 数值微分 | 样条+求导 | A092 |

---

## 七、参考资源

### 7.1 教材推荐

- 《数值分析》（李庆扬）
- 《计算方法》（邓建中）
- 《Numerical Recipes》（Press等）

### 7.2 Python库

- scipy.interpolate：插值函数
- scipy.optimize：曲线拟合
- numpy.polyfit：多项式拟合

### 7.3 检查清单

- [ ] 数据点无重复
- [ ] 插值方法选择恰当
- [ ] 拟合模型R²可接受
- [ ] 外推风险已说明
- [ ] 光滑性满足要求
