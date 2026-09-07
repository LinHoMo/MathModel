# 光学系统建模知识库

> 本文件提供数学建模竞赛中光学系统相关问题的建模知识，包括定日镜场、FAST反射面、光学优化等问题。

---

## 1. 问题特征

### 1.1 典型问题描述
- 定日镜场优化设计
- FAST主动反射面形状调节
- 聚光系统效率优化
- 光路追踪与分析

### 1.2 常见约束条件
- 几何约束：镜面尺寸、间距、角度范围
- 光学约束：反射角、入射角、聚焦精度
- 能量约束：能量密度、热效应
- 工程约束：成本、维护难度

### 1.3 数据特点
- 几何数据：坐标、角度、距离
- 光学数据：反射率、透射率、散射
- 能量数据：功率密度、效率
- 时间数据：太阳位置随时间变化

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 几何光学 | 光路追踪 | 精确 | 计算量大 |
| 光线追踪法 | 复杂系统 | 灵活 | 需要大量采样 |
| 优化算法 | 镜场布局 | 自动搜索 | 可能陷入局部最优 |
| 数值模拟 | 能量分布 | 直观 | 需要精确模型 |

---

## 3. 数学基础

### 3.1 反射定律

**入射角等于反射角**：
```
θ_i = θ_r
```

**向量形式**：
```
r = i - 2(i·n)n
```
其中：
- i: 入射方向向量
- r: 反射方向向量
- n: 镜面法向量

### 3.2 定日镜场模型

**镜面效率**：
```
η = η_cos × η_atm × η_shad × η_refl
```
其中：
- η_cos: 余弦效率
- η_atm: 大气衰减效率
- η_shad: 遮挡效率
- η_refl: 镜面反射率

**余弦效率**：
```
η_cos = cos(θ)
```
其中θ为入射角与镜面法线的夹角。

### 3.3 FAST反射面模型

**抛物面方程**：
```
z = (x² + y²) / (4f)
```
其中f为焦距。

**形状调节**：
- 主动反射面：通过促动器调节面板位置
- 球面拟合：将抛物面近似为球面
- 精度要求：面形误差 < λ/16

---

## 4. 代码实现

### 4.1 光线追踪

```python
import numpy as np

def reflect(incident, normal):
    """
    计算反射方向
    
    Parameters
    ----------
    incident : array
        入射方向向量
    normal : array
        镜面法向量
    
    Returns
    -------
    reflected : array
        反射方向向量
    """
    # 归一化
    incident = incident / np.linalg.norm(incident)
    normal = normal / np.linalg.norm(normal)
    
    # 反射公式
    reflected = incident - 2 * np.dot(incident, normal) * normal
    
    return reflected

def ray_trace(start_point, direction, mirrors):
    """
    光线追踪
    
    Parameters
    ----------
    start_point : array
        光线起点
    direction : array
        光线方向
    mirrors : list
        镜面列表 [(position, normal), ...]
    
    Returns
    -------
    path : list
        光线路径点
    """
    path = [start_point]
    current_point = start_point
    current_dir = direction
    
    for mirror_pos, mirror_normal in mirrors:
        # 计算光线与镜面交点
        # 这里简化处理，实际需要求解交点
        hit_point = mirror_pos  # 简化
        
        # 计算反射方向
        reflected = reflect(current_dir, mirror_normal)
        
        path.append(hit_point)
        current_point = hit_point
        current_dir = reflected
    
    return path
```

### 4.2 定日镜效率计算

```python
import numpy as np

def heliostat_efficiency(heliostat_pos, target_pos, sun_pos, 
                        mirror_normal, mirror_reflectivity=0.9):
    """
    计算定日镜效率
    
    Parameters
    ----------
    heliostat_pos : array
        定日镜位置
    target_pos : array
        目标位置
    sun_pos : array
        太阳位置
    mirror_normal : array
        镜面法向量
    mirror_reflectivity : float
        镜面反射率
    
    Returns
    -------
    efficiency : float
        总效率
    """
    # 入射方向（从太阳到镜面）
    incident = heliostat_pos - sun_pos
    incident = incident / np.linalg.norm(incident)
    
    # 反射方向（从镜面到目标）
    reflected = target_pos - heliostat_pos
    reflected = reflected / np.linalg.norm(reflected)
    
    # 余弦效率
    cos_efficiency = max(0, np.dot(mirror_normal, incident))
    
    # 距离衰减（大气效率）
    distance = np.linalg.norm(target_pos - heliostat_pos)
    atm_efficiency = np.exp(-0.0001 * distance)  # 简化模型
    
    # 总效率
    efficiency = cos_efficiency * atm_efficiency * mirror_reflectivity
    
    return efficiency
```

### 4.3 镜场优化

```python
import numpy as np
from scipy.optimize import differential_evolution

def optimize_heliostat_layout(n_heliostats, target_pos, sun_pos, 
                             bounds, objective='maximize_flux'):
    """
    优化定日镜布局
    
    Parameters
    ----------
    n_heliostats : int
        定日镜数量
    target_pos : array
        目标位置
    sun_pos : array
        太阳位置
    bounds : list
        位置边界
    objective : str
        优化目标
    
    Returns
    -------
    optimal_layout : array
        最优布局
    max_efficiency : float
        最大效率
    """
    def layout_efficiency(layout):
        """
        计算布局效率
        layout: [x1, y1, x2, y2, ..., xn, yn]
        """
        # 重塑为坐标
        positions = layout.reshape(n_heliostats, 2)
        
        total_flux = 0
        for i in range(n_heliostats):
            # 简化：假设镜面法向量指向目标
            heliostat_pos = np.array([positions[i, 0], positions[i, 1], 0])
            mirror_normal = target_pos - heliostat_pos
            mirror_normal = mirror_normal / np.linalg.norm(mirror_normal)
            
            # 计算效率
            eff = heliostat_efficiency(
                heliostat_pos, target_pos, sun_pos, 
                mirror_normal, mirror_reflectivity=0.9
            )
            total_flux += eff
        
        return -total_flux  # 最小化负效率
    
    # 优化
    result = differential_evolution(
        layout_efficiency, 
        bounds * n_heliostats,
        seed=42,
        maxiter=100
    )
    
    optimal_layout = result.x.reshape(n_heliostats, 2)
    max_efficiency = -result.fun
    
    return optimal_layout, max_efficiency
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 忽略余弦效率 | 能量估计偏高 | 必须计算入射角 |
| 遮挡遗漏 | 镜间遮挡未考虑 | 检查遮挡效率 |
| 坐标系混乱 | 光路计算错误 | 统一坐标系 |
| 法向量错误 | 反射方向错误 | 验证法向量 |
| 忽略大气衰减 | 远距离效率估计偏高 | 加入衰减模型 |

---

## 6. 验证方法

### 6.1 几何验证
- 检查镜面法向量是否指向目标
- 验证入射角和反射角关系
- 检查镜面间距是否满足约束

### 6.2 能量验证
- 与已知效率对比
- 检查能量守恒
- 验证效率在合理范围（0-1）

### 6.3 灵敏度分析
- 改变太阳位置，观察效率变化
- 改变镜面数量，观察效率变化
- 改变目标位置，观察效率变化

---

## 7. 参考论文

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| A028 | 几何光学+优化 | FAST反射面调节 |
| A092 | 粒子群优化 | 定日镜场布局 |
| A115 | 几何模型 | 主动反射面形状 |
| A165 | 机理分析 | 定日镜场优化 |
| A175 | 优化设计 | 定日镜场效率 |

---

## 8. 验证清单

- [ ] 光路计算正确（入射角=反射角）
- [ ] 余弦效率计算正确
- [ ] 遮挡效率已考虑
- [ ] 大气衰减已建模
- [ ] 镜面间距满足约束
- [ ] 效率在合理范围（0-1）
- [ ] 灵敏度分析已执行
