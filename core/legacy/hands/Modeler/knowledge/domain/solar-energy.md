# 太阳能系统建模知识库

> 本文件提供数学建模竞赛中太阳能系统相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 定日镜场优化设计（镜面数量、布局、朝向）
- 太阳影子定位（通过影子长度推算时间/位置）
- 光伏发电系统设计与优化
- 太阳能热水器效率分析
- 太阳能建筑采光设计
- 太阳能海水淡化系统

### 1.2 常见约束条件
- 地理约束：纬度、经度、海拔
- 几何约束：镜面面积、间距、遮挡关系
- 光学约束：入射角、反射角、聚焦比
- 能量约束：辐射强度、光学效率、热损失
- 经济约束：投资成本、维护费用、发电收益
- 时间约束：季节变化、日照时长

### 1.3 数据特点
- 太阳位置：太阳高度角、方位角、时角
- 辐射数据：直射辐射(DNI)、散射辐射、总辐射
- 气象数据：云量、大气透明度、风速
- 几何参数：镜面尺寸、塔高、场地地形
- 性能数据：发电量、效率、温度

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 太阳位置算法 | 影子定位、日照分析 | 精确计算太阳位置 | 依赖天文公式 |
| 光学效率建模 | 定日镜场设计 | 物理意义明确 | 需要光学知识 |
| 蒙特卡洛光线追踪 | 复杂几何光学 | 适应性强 | 计算量大 |
| 遗传算法 | 镜场布局优化 | 全局最优 | 收敛慢 |
| 余弦效率分析 | 镜面朝向优化 | 计算简单 | 仅考虑几何因素 |
| 大气衰减模型 | 远距离传输 | 考虑大气影响 | 模型参数不确定 |

---

## 3. 数学基础

### 3.1 太阳位置计算

**太阳赤纬**（周年变化）：
```
δ = 23.45° * sin(360°/365 * (284 + n))
其中 n 为年积日（1月1日为1）
```

**时角**：
```
ω = 15° * (t_solar - 12)
t_solar: 当地真太阳时（小时）
```

**太阳高度角**：
```
sin(α) = sin(φ)sin(δ) + cos(φ)cos(δ)cos(ω)
φ: 当地纬度
```

**太阳方位角**：
```
cos(A) = (sin(δ) - sin(α)sin(φ)) / (cos(α)cos(φ))
```

### 3.2 影子长度计算

**垂直杆影子长度**：
```
L_shadow = H * cot(α)
H: 杆高
α: 太阳高度角
```

**影子方向**：
```
影子方向 = 方位角 + 180°（与太阳方位相反）
```

### 3.3 定日镜光学效率

**余弦效率**：
```
η_cos = cos(θ_i)
θ_i: 入射角（入射光线与镜面法线夹角）
```

**大气衰减效率**：
```
η_atm = ρ^d
ρ: 大气透明度（0.9-1.0）
d: 镜面到集热器距离
```

**遮挡效率**：
```
η_block = 1 - 遮挡面积/镜面面积
```

**总光学效率**：
```
η_optical = η_cos * η_atm * η_block * η_mirror
```

### 3.4 集热器接收功率

```
P_receiver = DNI * A_mirror * η_optical * η_cos
DNI: 法向直射辐照度 (W/m²)
A_mirror: 镜面面积 (m²)
```

---

## 4. Python实现

### 4.1 太阳位置算法

```python
import numpy as np
from datetime import datetime

def solar_position(lat, lon, dt):
    """
    计算太阳位置（高度角和方位角）
    
    Parameters
    ----------
    lat : float
        纬度 (度，北纬为正)
    lon : float
        经度 (度，东经为正)
    dt : datetime
        时间
    
    Returns
    -------
    elevation : float
        太阳高度角 (度)
    azimuth : float
        太阳方位角 (度，正南为0，顺时针为正)
    """
    # 年积日
    n = dt.timetuple().tm_yday
    
    # 太阳赤纬 (度)
    delta = 23.45 * np.sin(np.radians(360/365 * (284 + n)))
    
    # 时角 (度)
    hour = dt.hour + dt.minute/60 + dt.second/3600
    omega = 15 * (hour - 12)
    
    lat_rad = np.radians(lat)
    delta_rad = np.radians(delta)
    omega_rad = np.radians(omega)
    
    # 太阳高度角
    sin_alpha = (np.sin(lat_rad) * np.sin(delta_rad) + 
                 np.cos(lat_rad) * np.cos(delta_rad) * np.cos(omega_rad))
    elevation = np.degrees(np.arcsin(np.clip(sin_alpha, -1, 1)))
    
    # 太阳方位角
    cos_azimuth = ((np.sin(delta_rad) - np.sin(lat_rad) * sin_alpha) / 
                   (np.cos(lat_rad) * np.cos(np.radians(elevation))))
    azimuth = np.degrees(np.arccos(np.clip(cos_azimuth, -1, 1)))
    
    if omega > 0:  # 下午
        azimuth = -azimuth
    
    return elevation, azimuth

def shadow_length(pole_height, elevation_deg):
    """
    计算垂直杆影子长度
    
    Parameters
    ----------
    pole_height : float
        杆高 (m)
    elevation_deg : float
        太阳高度角 (度)
    
    Returns
    -------
    length : float
        影子长度 (m)
    """
    if elevation_deg <= 0:
        return float('inf')
    return pole_height / np.tan(np.radians(elevation_deg))
```

### 4.2 定日镜场效率计算

```python
import numpy as np

def cosine_efficiency(sun_elev, sun_az, mirror_normal):
    """
    计算余弦效率
    
    Parameters
    ----------
    sun_elev, sun_az : float
        太阳高度角和方位角 (度)
    mirror_normal : array
        镜面法线方向 [elev, az] (度)
    
    Returns
    -------
    eta_cos : float
        余弦效率
    """
    # 单位向量
    sun_vec = np.array([
        np.cos(np.radians(sun_elev)) * np.cos(np.radians(sun_az)),
        np.cos(np.radians(sun_elev)) * np.sin(np.radians(sun_az)),
        np.sin(np.radians(sun_elev))
    ])
    
    normal_vec = np.array([
        np.cos(np.radians(mirror_normal[0])) * np.cos(np.radians(mirror_normal[1])),
        np.cos(np.radians(mirror_normal[0])) * np.sin(np.radians(mirror_normal[1])),
        np.sin(np.radians(mirror_normal[0]))
    ])
    
    # 入射角余弦
    cos_incidence = np.dot(sun_vec, normal_vec)
    
    # 余弦效率 = |cos(θ_i)|
    eta_cos = abs(cos_incidence)
    
    return eta_cos

def atmospheric_attenuation(distance, rho=0.95):
    """
    计算大气衰减效率
    
    Parameters
    ----------
    distance : float
        镜面到集热器距离 (m)
    rho : float
        大气透明度
    
    Returns
    -------
    eta_atm : float
        大气衰减效率
    """
    return rho ** (distance / 1000)

def field_efficiency(mirrors, receiver_pos, sun_elev, sun_az):
    """
    计算镜场总效率
    
    Parameters
    ----------
    mirrors : list of dict
        镜面信息 [{'pos': [x,y], 'normal': [elev,az], 'area': A}, ...]
    receiver_pos : array
        集热器位置 [x, y, z]
    sun_elev, sun_az : float
        太阳位置
    
    Returns
    -------
    total_power : float
        总接收功率 (W)
    efficiencies : dict
        各效率分量
    """
    DNI = 1000  # W/m² 法向直射辐照度
    eta_mirror = 0.92  # 镜面反射率
    
    total_power = 0
    cos_eff = []
    atm_eff = []
    
    for mirror in mirrors:
        # 余弦效率
        eta_cos = cosine_efficiency(sun_elev, sun_az, mirror['normal'])
        
        # 大气衰减
        dist = np.linalg.norm(np.array(mirror['pos'] + [0]) - receiver_pos)
        eta_atm = atmospheric_attenuation(dist)
        
        # 单面镜子贡献
        P = DNI * mirror['area'] * eta_mirror * eta_cos * eta_atm
        total_power += P
        
        cos_eff.append(eta_cos)
        atm_eff.append(eta_atm)
    
    return total_power, {
        'cos_efficiency': np.mean(cos_eff),
        'atm_efficiency': np.mean(atm_eff),
        'mirror_reflectivity': eta_mirror
    }
```

### 4.3 镜场布局优化（遗传算法）

```python
import numpy as np
from scipy.optimize import differential_evolution

def optimize_mirror_field(n_mirrors, field_radius, receiver_pos, sun_elev, sun_az):
    """
    优化定日镜场布局
    
    Parameters
    ----------
    n_mirrors : int
        镜面数量
    field_radius : float
        场地半径 (m)
    receiver_pos : array
        集热器位置
    
    Returns
    -------
    best_layout : array
        最优镜面位置
    best_power : float
        最大总功率
    """
    def objective(params):
        # 解码参数: [x1,y1,x2,y2,...] -> 镜面位置
        positions = params.reshape(n_mirrors, 2)
        
        # 构建镜面列表
        mirrors = []
        for i in range(n_mirrors):
            mirrors.append({
                'pos': positions[i],
                'normal': [0, 0],  # 简化：法线朝上
                'area': 50  # 50 m²
            })
        
        total_power, _ = field_efficiency(mirrors, receiver_pos, sun_elev, sun_az)
        return -total_power  # 最小化负功率
    
    # 边界: 每个镜面的x,y坐标
    bounds = [(-field_radius, field_radius)] * (2 * n_mirrors)
    
    result = differential_evolution(
        objective, bounds, seed=42,
        maxiter=100, popsize=20
    )
    
    best_layout = result.x.reshape(n_mirrors, 2)
    best_power = -result.fun
    
    return best_layout, best_power
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 太阳位置计算错误 | 影子方向相反 | 检查方位角定义（正南/正北） |
| 方位角符号混乱 | 方位角计算错误 | 统一约定：正南为0°，顺时针为正 |
| 时角未修正 | 时间计算偏差 | 使用真太阳时（考虑时差和经度修正） |
| 忽略大气衰减 | 远距离效率偏高 | 加入大气透明度衰减 |
| 遮挡分析遗漏 | 实际功率偏低 | 考虑镜间遮挡和塔影 |
| 网格过粗 | 优化结果非最优 | 增加种群数量和迭代次数 |
| 忽略季节变化 | 年发电量不准确 | 计算典型日或全年平均 |

---

## 6. 验证方法

### 6.1 太阳位置验证
- 与天文软件（如SunCalc）结果对比
- 检查春分/秋分正午太阳高度角 = 90° - |纬度|

### 6.2 影子长度验证
- 正午影子方向应指向正北（北半球）
- 影子长度变化趋势与太阳高度角一致

### 6.3 能量平衡验证
- 总接收功率 = 辐射强度 × 总镜面积 × 总效率
- 光学效率各分量应在合理范围（0-1）

### 6.4 物理合理性检查
- 余弦效率应 ≤ 1
- 大气衰减效率随距离增加而减小
- 总功率数量级应合理（MW级）

---

## 7. 真题案例

### 案例1：2015A 太阳影子定位

**问题核心**：通过影子长度和方向推算地理位置和时间

**建模要点**：
1. 建立太阳位置与影子的几何关系
2. 利用影子长度反推太阳高度角
3. 利用影子方向反推太阳方位角
4. 结合日期信息求解经纬度

**典型解法**：
```
1. 建立影子长度与太阳高度角的关系: L = H / tan(α)
2. 建立太阳位置与经纬度、时间的关系
3. 联立方程求解经纬度和时间
4. 多组数据最小二乘拟合
```

**关键公式**：
```
sin(α) = sin(φ)sin(δ) + cos(φ)cos(δ)cos(ω)
L = H / tan(α)
A = arctan(sin(ω) / (cos(ω)sin(φ) - tan(δ)cos(φ)))
```

### 案例2：2023A 定日镜场优化设计

**问题核心**：设计定日镜场布局，最大化年发电量

**建模要点**：
1. 太阳位置的时空变化模型
2. 余弦效率、大气衰减、遮挡效率计算
3. 镜面布局优化（位置、数量、面积）
4. 年发电量积分

---

## 8. 代码模板参考

- 太阳位置: 自定义算法或 `pysolar` 库
- 光线追踪: `rayoptics` 或自定义
- 优化算法: `scipy.optimize.differential_evolution`
- 数据处理: `pandas`, `numpy`

---

## 9. 验证清单

- [ ] 太阳赤纬计算公式正确（考虑年变化）
- [ ] 时角使用真太阳时
- [ ] 方位角定义清晰（正南/正北，顺时针/逆时针）
- [ ] 余弦效率物理意义正确
- [ ] 大气衰减模型参数合理
- [ ] 遮挡分析已考虑
- [ ] 年发电量积分方法正确
- [ ] 结果数量级与实际电站一致

---

## 10. 参考文献

1. Duffie J A. Solar Engineering of Thermal Processes. Wiley, 2013.
2. 王志峰. 太阳能热发电站. 中国电力出版社, 2016.
3. Iqbal M. An Introduction to Solar Radiation. Academic Press, 1983.
4. 刘鉴. 太阳能光伏发电系统工程. 清华大学出版社, 2018.
