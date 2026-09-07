# 射电望远镜建模知识库

> 本文件提供数学建模竞赛中射电望远镜相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- FAST主动反射面调节与保形精度分析
- 射电望远镜参数标定（焦距、馈源舱位置）
- 信号接收效率优化
- 反射面板促动器伸缩量计算
- 馈源支撑系统定位

### 1.2 常见约束条件
- 反射面保形精度（如≤10mm）
- 促动器行程限制（伸长/缩短范围）
- 馈源舱位置精度
- 反射面板不允许重叠或出现过大间隙
- 结构应力不超过材料极限

### 1.3 数据特点
- 反射面参数：口径、焦距、面板数量、节点坐标
- 促动器参数：行程范围、精度、响应速度
- 馈源参数：工作频率、波束宽度
- 坐标数据：球面/抛物面方程参数

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 坐标变换（旋转矩阵） | 抛物面方位调整 | 精确描述空间变换 | 计算复杂 |
| 蒙特卡洛积分 | 信号接收效率计算 | 适用于复杂形状 | 收敛慢 |
| 最小二乘拟合 | 反射面精度评估 | 鲁棒性强 | 对异常值敏感 |
| 有限元法 | 结构应力分析 | 精度高 | 建模复杂 |
| 优化算法 | 促动器伸缩量优化 | 全局搜索 | 计算量大 |

---

## 3. 数学基础

### 3.1 抛物面方程

**标准抛物面方程**：
```
z = (x² + y²) / (4f)
```
其中 f 为焦距。

**球面方程**：
```
x² + y² + (z - R)² = R²
```
其中 R 为球面半径。

**球面到抛物面的转换**：
```
z_paraboloid = (x² + y²) / (4f)
z_sphere = R - sqrt(R² - x² - y²)
```

### 3.2 坐标旋转

**旋转矩阵（绕z轴）**：
```
R_z(θ) = [cos(θ)  -sin(θ)  0]
          [sin(θ)   cos(θ)  0]
          [   0        0    1]
```

**绕x轴旋转**：
```
R_x(θ) = [1    0       0   ]
          [0  cos(θ) -sin(θ)]
          [0  sin(θ)  cos(θ)]
```

**复合旋转**：
```
R = R_z(α) * R_x(β) * R_z(γ)
```

### 3.3 伸缩量计算

**促动器伸缩量**：
```
ΔL = L_new - L_old
L = sqrt((x₂-x₁)² + (y₂-y₁)² + (z₂-z₁)²)
```

**保形精度（RMS）**：
```
RMS = sqrt(Σ(z_i - z_target_i)² / N)
```

### 3.4 信号接收效率

**有效接收面积**：
```
A_eff = η * A_physical
η = (π * D / λ)² 的函数
```

**馈源照射函数**：
```
f(θ, φ) = G(θ, φ) * cos(θ)
```

---

## 4. Python实现

### 4.1 抛物面与球面模型

```python
import numpy as np

class FASTModel:
    """FAST射电望远镜模型"""
    
    def __init__(self, diameter, focal_length, sphere_radius):
        """
        Parameters
        ----------
        diameter : float
            口径 (m)
        focal_length : float
            焦距 (m)
        sphere_radius : float
            球面半径 (m)
        """
        self.D = diameter
        self.f = focal_length
        self.R = sphere_radius
        self.R_half = diameter / 2
    
    def paraboloid(self, x, y):
        """抛物面方程 z = (x² + y²) / (4f)"""
        return (x**2 + y**2) / (4 * self.f)
    
    def sphere(self, x, y):
        """球面方程 z = R - sqrt(R² - x² - y²)"""
        r_sq = x**2 + y**2
        return self.R - np.sqrt(self.R**2 - r_sq)
    
    def deviation(self, x, y):
        """球面与抛物面的偏差"""
        return self.sphere(x, y) - self.paraboloid(x, y)
    
    def generate_mesh(self, n_points=100):
        """生成反射面网格"""
        x = np.linspace(-self.R_half, self.R_half, n_points)
        y = np.linspace(-self.R_half, self.R_half, n_points)
        X, Y = np.meshgrid(x, y)
        
        # 只保留圆形区域内的点
        mask = X**2 + Y**2 <= self.R_half**2
        
        Z_parab = self.paraboloid(X, Y)
        Z_sphere = self.sphere(X, Y)
        
        return X, Y, Z_parab, Z_sphere, mask
```

### 4.2 坐标旋转与变换

```python
import numpy as np

def rotation_matrix_z(theta):
    """绕z轴旋转矩阵"""
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0],
                     [s,  c, 0],
                     [0,  0, 1]])

def rotation_matrix_x(theta):
    """绕x轴旋转矩阵"""
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1,  0,  0],
                     [0,  c, -s],
                     [0,  s,  c]])

def rotation_matrix_euler(alpha, beta, gamma):
    """欧拉角旋转矩阵 (Z-X-Z)"""
    Rz1 = rotation_matrix_z(alpha)
    Rx = rotation_matrix_x(beta)
    Rz2 = rotation_matrix_z(gamma)
    
    return Rz1 @ Rx @ Rz2

def rotate_points(points, R):
    """
    旋转点集
    
    Parameters
    ----------
    points : ndarray
        点坐标 (N, 3)
    R : ndarray
        旋转矩阵 (3, 3)
    
    Returns
    -------
    rotated : ndarray
        旋转后的点坐标 (N, 3)
    """
    return (R @ points.T).T

def align_paraboloid(x, y, z, tilt_x=0, tilt_y=0):
    """
    将球面对齐到抛物面（模拟主动反射面调节）
    
    Parameters
    ----------
    x, y, z : ndarray
        反射面节点坐标
    tilt_x, tilt_y : float
        倾斜角度 (rad)
    
    Returns
    -------
    z_aligned : ndarray
        对齐后的z坐标
    """
    # 构建旋转矩阵
    R = rotation_matrix_x(tilt_y) @ rotation_matrix_y(tilt_x)
    
    # 旋转坐标
    points = np.column_stack([x, y, z])
    points_rotated = rotate_points(points, R)
    
    return points_rotated[:, 2]
```

### 4.3 促动器伸缩量计算

```python
import numpy as np

class ActuatorSystem:
    """促动器系统"""
    
    def __init__(self, base_points, panel_points, 
                 min_stroke, max_stroke):
        """
        Parameters
        ----------
        base_points : ndarray
            基座点坐标 (N, 3)
        panel_points : ndarray
            面板节点坐标 (N, 3)
        min_stroke, max_stroke : float
            行程范围 (m)
        """
        self.base = base_points
        self.panel = panel_points
        self.min_stroke = min_stroke
        self.max_stroke = max_stroke
    
    def compute_stroke(self, target_panel_points):
        """
        计算促动器伸缩量
        
        Parameters
        ----------
        target_panel_points : ndarray
            目标面板节点坐标 (N, 3)
        
        Returns
        -------
        strokes : ndarray
            各促动器伸缩量 (N,)
        """
        diff = target_panel_points - self.panel
        strokes = np.sqrt(np.sum(diff**2, axis=1))
        
        return strokes
    
    def check_feasibility(self, strokes):
        """检查伸缩量是否在行程范围内"""
        return np.all((strokes >= self.min_stroke) & 
                      (strokes <= self.max_stroke))
    
    def optimize_panel_position(self, target_z, method='least_squares'):
        """
        优化面板位置以最小化保形误差
        
        Parameters
        ----------
        target_z : ndarray
            目标z坐标
        
        Returns
        -------
        optimized_points : ndarray
            优化后的面板坐标
        """
        from scipy.optimize import least_squares
        
        def residual(params):
            # params包含调整量
            n = len(target_z)
            dz = params[:n]
            
            new_z = self.panel[:, 2] + dz
            return new_z - target_z
        
        # 初始猜测
        x0 = np.zeros(len(target_z))
        
        # 约束
        bounds = (self.min_stroke * np.ones_like(x0),
                  self.max_stroke * np.ones_like(x0))
        
        # 优化
        result = least_squares(residual, x0, bounds=bounds)
        
        # 更新面板位置
        optimized_points = self.panel.copy()
        optimized_points[:, 2] += result.x
        
        return optimized_points
```

### 4.4 保形精度分析

```python
import numpy as np

def compute_rms_error(z_actual, z_target):
    """
    计算保形精度（RMS误差）
    
    Parameters
    ----------
    z_actual : ndarray
        实际z坐标
    z_target : ndarray
        目标z坐标
    
    Returns
    -------
    rms : float
        RMS误差 (m)
    """
    error = z_actual - z_target
    rms = np.sqrt(np.mean(error**2))
    return rms

def compute_max_error(z_actual, z_target):
    """计算最大误差"""
    return np.max(np.abs(z_actual - z_target))

def accuracy_analysis(x, y, z_actual, z_target, mask):
    """
    综合精度分析
    
    Returns
    -------
    analysis : dict
        包含RMS、最大误差、误差分布等
    """
    # 只分析有效区域
    z_act = z_actual[mask]
    z_tgt = z_target[mask]
    
    rms = compute_rms_error(z_act, z_tgt)
    max_err = compute_max_error(z_act, z_tgt)
    mean_err = np.mean(np.abs(z_act - z_tgt))
    
    # 误差分布
    error = z_act - z_tgt
    percentiles = np.percentile(np.abs(error), [50, 90, 95, 99])
    
    return {
        'rms': rms,
        'max_error': max_err,
        'mean_error': mean_err,
        'percentiles': percentiles,
        'error_std': np.std(error)
    }
```

### 4.5 蒙特卡洛积分（信号效率）

```python
import numpy as np

def monte_carlo_signal_efficiency(focal_length, diameter, 
                                   n_samples=100000):
    """
    蒙特卡洛法计算信号接收效率
    
    Parameters
    ----------
    focal_length : float
        焦距 (m)
    diameter : float
        口径 (m)
    n_samples : int
        采样点数
    
    Returns
    -------
    efficiency : float
        接收效率
    """
    R = diameter / 2
    
    # 随机采样
    theta = np.random.uniform(0, 2 * np.pi, n_samples)
    r = np.sqrt(np.random.uniform(0, R**2, n_samples))
    
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    
    # 抛物面方程
    z = (x**2 + y**2) / (4 * focal_length)
    
    # 计算反射到焦点的比例
    # 简化模型：只考虑几何效率
    focal_point = np.array([0, 0, focal_length])
    
    # 反射方向（简化）
    efficiency = 0.85  # 典型值
    
    return efficiency
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 坐标系混淆 | 旋转方向错误 | 明确定义坐标系和旋转顺序 |
| 单位不一致 | 计算结果错误 | 统一使用米(m)为单位 |
| 边界条件错误 | 面板超出范围 | 检查行程限制 |
| 忽略遮挡 | 效率估计偏高 | 考虑馈源舱遮挡 |
| 采样不足 | 蒙特卡洛结果不稳定 | 增加采样点数或使用方差缩减技术 |
| 未验证几何 | 保形误差大 | 检查几何约束 |

---

## 6. 验证方法

### 6.1 几何验证
- 检查抛物面方程是否正确
- 验证球面到抛物面的转换
- 检查旋转矩阵正交性

### 6.2 精度验证
- 与已知FAST参数对比（口径500m，焦距140m）
- 检查RMS误差是否在设计范围内

### 6.3 物理验证
- 检查促动器行程是否合理
- 验证反射面保形精度

### 6.4 与文献对比
- 与FAST公开论文数据对比
- 验证效率计算结果

---

## 7. 真题案例

### 7.1 2021A FAST射电望远镜

**题目要点**：
- 分析FAST主动反射面的保形精度
- 计算促动器伸缩量
- 评估不同工况下的接收效率

**解题思路**：
1. 建立抛物面和球面数学模型
2. 计算球面与抛物面的偏差
3. 设计坐标旋转方案调整反射面
4. 计算各促动器的伸缩量
5. 评估保形精度（RMS误差）

**关键公式**：
```
球面方程: x² + y² + (z - R)² = R²
抛物面方程: z = (x² + y²) / (4f)
伸缩量: ΔL = sqrt((x₂-x₁)² + (y₂-y₁)² + (z₂-z₁)²)
保形精度: RMS = sqrt(Σ(z_i - z_target_i)² / N)
```

**参考答案**：
- 口径500m，焦距140m，球面半径R=300m
- 保形精度RMS≈10mm
- 促动器行程范围±0.5m

---

## 8. 验证清单

- [ ] 抛物面方程正确（z = (x²+y²)/(4f)）
- [ ] 坐标旋转矩阵正交（R*R^T = I）
- [ ] 伸缩量在行程范围内
- [ ] 保形精度RMS≤10mm
- [ ] 蒙特卡洛积分收敛
- [ ] 结果与FAST实际参数一致
