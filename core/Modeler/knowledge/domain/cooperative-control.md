# 协同控制领域知识

## 一、核心概念

### 1.1 协同控制定义
- **定义**: 多智能体协调完成共同任务
- **目标**: 一致性、编队、编队保持
- **应用**: 无人机编队、机器人协作、同心鼓

### 1.2 一致性协议
- **一阶一致性**: 位置一致性
- **二阶一致性**: 速度一致性
- **高阶一致性**: 加速度等

### 1.3 通信拓扑
- **有向图**: 单向通信
- **无向图**: 双向通信
- **切换拓扑**: 动态变化

---

## 二、同心鼓模型

### 2.1 问题描述
- 多人拉动绳子使鼓面弹球
- 需要协调各人拉力
- 目标：球弹起高度最大化

### 2.2 力学模型
```python
import numpy as np

class ConcentricDrumModel:
    """
    同心鼓力学模型
    """
    def __init__(self, n_players, rope_length, drum_mass):
        self.n = n_players
        self.L = rope_length
        self.m = drum_mass
        
        # 位置（极坐标）
        self.angles = np.linspace(0, 2*np.pi, n_players, endpoint=False)
        self.positions = np.zeros((n_players, 2))
        
        # 力
        self.forces = np.zeros(n_players)
    
    def update_positions(self):
        """更新鼓面位置"""
        # 计算合力
        F_x = np.sum(self.forces * np.cos(self.angles))
        F_y = np.sum(self.forces * np.sin(self.angles))
        
        # 合力方向
        direction = np.arctan2(F_y, F_x)
        
        # 更新角度
        self.angles = direction + np.linspace(0, 2*np.pi, self.n, endpoint=False)
        
        # 更新位置
        for i in range(self.n):
            self.positions[i] = [np.cos(self.angles[i]), np.sin(self.angles[i])]
    
    def ball_dynamics(self, ball_pos, ball_vel, g=9.81):
        """球的动力学"""
        # 球的运动方程
        ball_acc = np.array([0, -g])
        ball_vel += ball_acc * 0.01
        ball_pos += ball_vel * 0.01
        
        # 检测碰撞
        drum_center = np.mean(self.positions, axis=0)
        if ball_pos[1] < drum_center[1] + 0.1:  # 鼓面高度
            # 弹跳
            ball_vel[1] = abs(ball_vel[1]) * 0.9  # 恢复系数
        
        return ball_pos, ball_vel
```

### 2.3 优化模型
```python
def optimize_drum_pulls(n_players, n_rounds):
    """
    优化各人拉力
    """
    def objective(forces):
        # 模拟弹球高度
        height = simulate(forces)
        return -height  # 最大化高度
    
    # 优化算法
    from scipy.optimize import minimize
    
    x0 = np.ones(n_players) * 10  # 初始拉力
    result = minimize(objective, x0, method='L-BFGS-B', 
                     bounds=[(0, 50)] * n_players)
    
    return result.x
```

---

## 三、编队控制

### 3.1 领航-跟随
```python
def leader_follower_control(followers, leader_pos, leader_vel):
    """
    领航-跟随编队控制
    """
    Kp = 1.0  # 比例增益
    Kd = 0.5  # 微分增益
    
    for i, follower in enumerate(followers):
        # 期望位置
        desired_pos = leader_pos + desired_offset[i]
        
        # 控制律
        error = desired_pos - follower.pos
        error_vel = leader_vel - follower.vel
        
        control = Kp * error + Kd * error_vel
        
        follower.apply_control(control)
```

### 3.2 虚拟结构
```python
def virtual_structure_control(agents, formation_center):
    """
    虚拟结构编队控制
    """
    Kp = 2.0
    
    for i, agent in enumerate(agents):
        # 期望位置
        desired = formation_center + formation_offset[i]
        
        # 控制
        control = Kp * (desired - agent.pos)
        agent.apply_control(control)
```

### 3.3 一致性控制
```python
def consensus_control(agents, graph_adj):
    """
    一致性编队控制
    """
    K = 1.0
    
    for i, agent in enumerate(agents):
        # 邻居信息
        neighbors = np.where(graph_adj[i] > 0)[0]
        
        # 一致性误差
        error = np.zeros(2)
        for j in neighbors:
            error += (agents[j].pos - agent.pos)
        
        # 控制
        control = K * error
        agent.apply_control(control)
```

---

## 四、稳定性分析

### 4.1 Lyapunov稳定性
```python
def lyapunov_analysis(agents, V_func):
    """
    Lyapunov稳定性分析
    """
    # 计算Lyapunov函数值
    V_values = [V_func(agent) for agent in agents]
    
    # 检查导数
    dV = np.diff(V_values)
    
    return np.all(dV <= 0)  # 稳定性条件
```

### 4.2 特征值分析
```python
def eigenvalue_analysis(graph_laplacian):
    """
    特征值分析收敛性
    """
    eigenvalues = np.linalg.eigvalsh(graph_laplacian)
    
    # 检查连通性
    is_connected = np.sum(eigenvalues < 1e-10) == 1
    
    # 收敛速度
    algebraic_connectivity = np.sort(eigenvalues)[1]  # 第二小特征值
    
    return is_connected, algebraic_connectivity
```

---

## 五、论文写作要点

### 5.1 问题分析框架
1. **系统建模**: 动力学方程
2. **拓扑分析**: 通信结构
3. **控制设计**: 一致性协议
4. **稳定性分析**: Lyapunov方法
5. **仿真验证**: 编队效果
6. **灵敏度分析**: 参数影响

### 5.2 图表规范
- **编队轨迹图**: 路径+位置
- **误差收敛图**: 误差曲线
- **通信拓扑图**: 节点+边
- **控制输入图**: 控制信号

### 5.3 LaTeX代码
```latex
\begin{equation}
\dot{x}_i = \sum_{j \in N_i} (x_j - x_i)
\label{eq:consensus}
\end{equation}

\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{formation_control.pdf}
\caption{编队控制效果}
\label{fig:formation}
\end{figure}
```

---

## 六、参考文献

1. 周东华. 多智能体系统协调控制. 科学出版社, 2018.
2. Ren W. Consensus Tracking of Multi-Agent Systems. IEEE, 2007.
3. Olfati-Saber R. Consensus Problems in Networks of Agents. IEEE, 2001.
4. 吕金虎. 复杂网络同步. 科学出版社, 2006.
