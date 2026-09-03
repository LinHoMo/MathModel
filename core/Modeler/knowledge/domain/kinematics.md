# 运动学与路径规划领域知识

## 一、核心概念

### 1.1 运动学基础
- **位置**: 向量 r = (x, y, z)
- **速度**: v = dr/dt
- **加速度**: a = dv/dt
- **角速度**: ω = dθ/dt

### 1.2 坐标系
- **直角坐标系**: (x, y)
- **极坐标系**: (r, θ)
- **参数方程**: x(t), y(t)

### 1.3 刚体运动
- **平动**: 所有点运动相同
- **转动**: 绕固定轴旋转
- **平面运动**: 平动+转动

---

## 二、板凳龙运动模型

### 2.1 问题描述
- 多节板凳连接成龙形
- 每节板凳可相对转动
- 需要设计运动路径和形态

### 2.2 运动学建模
**位置关系**:
```
r_i = r_{i-1} + L * (cos(θ_i), sin(θ_i))
r_i: 第i节位置
L: 板凳长度
θ_i: 第i节方向角
```

**速度关系**:
```
v_i = v_{i-1} + L * ω_i * (-sin(θ_i), cos(θ_i))
```

**约束条件**:
- 相邻板凳间距 = L
- 角度变化率 ≤ ω_max

### 2.3 Python实现
```python
import numpy as np

class BenchDragon:
    """
    板凳龙运动模型
    """
    def __init__(self, n_segments, segment_length):
        self.n = n_segments
        self.L = segment_length
        self.positions = np.zeros((n_segments, 2))
        self.angles = np.zeros(n_segments)
    
    def forward_kinematics(self, angles):
        """
        正运动学：已知角度求位置
        """
        self.angles = angles
        self.positions[0] = [0, 0]
        
        for i in range(1, self.n):
            self.positions[i] = (self.positions[i-1] + 
                                self.L * np.array([np.cos(angles[i-1]), 
                                                   np.sin(angles[i-1])]))
        return self.positions
    
    def inverse_kinematics(self, target_pos, method='analytical'):
        """
        逆运动学：已知目标位置求角度
        """
        angles = np.zeros(self.n)
        
        for i in range(self.n - 1):
            dx = target_pos[i+1, 0] - target_pos[i, 0]
            dy = target_pos[i+1, 1] - target_pos[i, 1]
            angles[i] = np.arctan2(dy, dx)
        
        return angles
    
    def check_collision(self, obstacles):
        """
        碰撞检测
        """
        for pos in self.positions:
            for obs in obstacles:
                if np.linalg.norm(pos - obs['center']) < obs['radius']:
                    return True
        return False
```

---

## 三、路径规划算法

### 3.1 A*算法
```python
def a_star(start, goal, grid, obstacles):
    """
    A*路径规划
    """
    import heapq
    
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    
    while open_set:
        _, current = heapq.heappop(open_set)
        
        if current == goal:
            return reconstruct_path(came_from, current)
        
        for neighbor in get_neighbors(current, grid):
            if neighbor in obstacles:
                continue
            
            tentative_g = g_score[current] + distance(current, neighbor)
            
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    
    return None

def heuristic(a, b):
    return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
```

### 3.2 RRT算法
```python
def rrt(start, goal, obstacles, max_iter=1000):
    """
    快速随机树算法
    """
    tree = {'nodes': [start], 'parents': [None]}
    
    for _ in range(max_iter):
        # 随机采样
        if np.random.rand() < 0.1:
            random_point = goal
        else:
            random_point = np.random.uniform(0, 100, 2)
        
        # 找最近节点
        distances = [np.linalg.norm(np.array(node) - random_point) for node in tree['nodes']]
        nearest_idx = np.argmin(distances)
        nearest = tree['nodes'][nearest_idx]
        
        # 扩展
        direction = (random_point - nearest) / np.linalg.norm(random_point - nearest)
        new_point = nearest + direction * 0.5
        
        # 碰撞检测
        if not any(np.linalg.norm(new_point - obs['center']) < obs['radius'] for obs in obstacles):
            tree['nodes'].append(new_point)
            tree['parents'].append(nearest_idx)
            
            if np.linalg.norm(new_point - goal) < 0.5:
                return reconstruct_rrt_path(tree)
    
    return None
```

### 3.3 人工势场法
```python
def artificial_potential_field(position, goal, obstacles, k_att=1.0, k_rep=100.0):
    """
    人工势场法
    """
    # 引力
    F_att = k_att * (goal - position)
    
    # 斥力
    F_rep = np.zeros(2)
    for obs in obstacles:
        diff = position - obs['center']
        dist = np.linalg.norm(diff)
        if dist < obs['radius'] + 1.0:
            F_rep += k_rep * (1/dist - 1/(obs['radius'] + 1.0)) * (diff / dist**2)
    
    return F_att + F_rep
```

---

## 四、形态调节

### 4.1 形态优化
```
min Σ ||r_i - r_i^target||²
s.t. ||r_{i+1} - r_i|| = L
     |θ_{i+1} - θ_i| ≤ Δθ_max
```

### 4.2 动态形态控制
```python
def dynamic_shape_control(current_shape, target_shape, dt):
    """
    动态形态控制
    """
    velocity = (target_shape - current_shape) / dt
    return velocity
```

---

## 五、论文写作要点

### 5.1 问题分析框架
1. **运动学模型**: 位置、速度关系
2. **约束条件**: 长度、角度、碰撞
3. **路径规划**: A*、RRT、势场法
4. **形态调节**: 目标形态跟踪
5. **仿真验证**: 运动轨迹
6. **灵敏度分析**: 参数影响

### 5.2 图表规范
- **运动轨迹**: 2D/3D路径
- **形态变化**: 动画/关键帧
- **速度曲线**: 时间序列
- **碰撞检测**: 安全距离

### 5.3 LaTeX代码
```latex
\begin{equation}
\mathbf{r}_i = \mathbf{r}_{i-1} + L(\cos\theta_i, \sin\theta_i)
\label{eq:kinematics}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{dragon_motion.pdf}
\caption{板凳龙运动轨迹}
\label{fig:dragon}
\end{figure}
```

---

## 六、参考文献

1. Craig J J. Introduction to Robotics. Pearson, 2017.
2. LaValle S M. Planning Algorithms. Cambridge University Press, 2006.
3. 蔡自兴. 机器人学. 清华大学出版社, 2015.
4. Lynch K M. Modern Robotics. Cambridge University Press, 2017.
