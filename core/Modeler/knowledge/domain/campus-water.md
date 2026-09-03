# 校园供水系统管理知识库

> 本文件提供数学建模竞赛中校园供水系统管理相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 智能供水管理系统设计
- 管网漏损检测与定位
- 用水需求预测与调度
- 供水管网压力优化
- 水质监测与预警

### 1.2 常见约束条件
- 水力约束：管道流量、压力限制
- 质量约束：水质标准、余氯要求
- 经济约束：能耗成本、漏损成本
- 设备约束：水泵容量、水箱容积
- 时间约束：峰谷用水规律

### 1.3 数据特点
- 传感器数据：流量、压力、水质
- 时间序列：历史用水量、设备状态
- 空间数据：管网拓扑、节点坐标
- 设备数据：水泵参数、管道属性

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 时间序列预测 | 需求预测 | 捕捉周期性 | 对突变不敏感 |
| 网络流优化 | 水量调度 | 全局最优 | 计算复杂度高 |
| 异常检测 | 漏损识别 | 实时性强 | 误报率较高 |
| 水力模型 | 管网分析 | 物理意义明确 | 需要详细参数 |
| 机器学习 | 综合预测 | 非线性拟合 | 需要大量数据 |
| 智能调度 | 运行优化 | 自适应性强 | 实现复杂 |

---

## 3. 数学基础

### 3.1 水力模型

**节点流量平衡**：
```
Σ Q_in - Σ Q_out = Q_demand
```

**管道压降（Hazen-Williams公式）**：
```
h_f = 10.67 · L · Q^1.852 / (C^1.852 · D^4.87)
```

其中：
- h_f: 摩擦水头损失 (m)
- L: 管道长度 (m)
- Q: 流量 (m³/s)
- C: Hazen-Williams系数
- D: 管道直径 (m)

**能量方程**：
```
H_i + P_i/(ρg) + z_i = H_j + P_j/(ρg) + z_j + h_f
```

### 3.2 需求预测

**季节性ARIMA模型**：
```
ARIMA(p,d,q)(P,D,Q)_s
```

**指数平滑模型**：
```
S_t = α · Y_t + (1-α) · S_{t-1}
```

**用水量预测公式**：
```
Q(t) = Q_base · f(t) · g(d) · h(w)
```

其中：
- Q_base: 基础用水量
- f(t): 时间因子（峰谷系数）
- g(d): 星期因子
- h(w): 天气因子

### 3.3 漏损检测

**漏损指数**：
```
LI = (Q_in - Q_out) / Q_in
```

**夜间最小流量法**：
```
L = Q_min - Q_expected
```

其中：
- L: 漏损量
- Q_min: 夜间最小流量
- Q_expected: 预期最小流量

**压力-漏损关系**：
```
L = L_0 · (P/P_0)^N1
```

其中：
- L_0: 参考压力下的漏损量
- N1: 漏损指数（通常1.0-1.5）

### 3.4 优化调度

**目标函数**：
```
min C = C_energy + C_leakage + C_quality
```

**能耗成本**：
```
C_energy = Σ P_i · t_i · c_e
```

其中：
- P_i: 水泵功率
- t_i: 运行时间
- c_e: 电价

**约束条件**：
- 节点压力约束：P_min ≤ P_i ≤ P_max
- 流量约束：Q_min ≤ Q_i ≤ Q_max
- 水箱容积约束：V_min ≤ V_i ≤ V_max

---

## 4. 代码实现

### 4.1 时间序列需求预测

```python
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

class WaterDemandForecast:
    """
    用水需求预测模型
    """
    def __init__(self, data, freq='H'):
        """
        Parameters
        ----------
        data : array
            历史用水量数据
        freq : str
            数据频率
        """
        self.data = np.array(data)
        self.freq = freq
    
    def arima_forecast(self, steps=24, order=(1,1,1)):
        """
        ARIMA预测
        
        Parameters
        ----------
        steps : int
            预测步数
        order : tuple
            ARIMA阶数 (p,d,q)
        """
        model = ARIMA(self.data, order=order)
        fitted = model.fit()
        
        forecast = fitted.forecast(steps=steps)
        confidence = fitted.get_forecast(steps=steps).conf_int()
        
        return forecast, confidence
    
    def exponential_smoothing_forecast(self, steps=24, seasonal_periods=24):
        """
        指数平滑预测
        """
        model = ExponentialSmoothing(
            self.data,
            trend='add',
            seasonal='add',
            seasonal_periods=seasonal_periods
        )
        fitted = model.fit()
        
        forecast = fitted.forecast(steps=steps)
        
        return forecast
    
    def daily_pattern(self):
        """
        提取日用水模式
        """
        n = len(self.data)
        hours_per_day = 24 if self.freq == 'H' else 96
        
        # 按天分组
        n_days = n // hours_per_day
        daily_profiles = self.data[:n_days * hours_per_day].reshape(n_days, hours_per_day)
        
        # 计算平均模式
        avg_pattern = np.mean(daily_profiles, axis=0)
        
        # 计算峰谷系数
        peak_factor = np.max(avg_pattern) / np.mean(avg_pattern)
        valley_factor = np.min(avg_pattern) / np.mean(avg_pattern)
        
        return avg_pattern, peak_factor, valley_factor
    
    def weekly_pattern(self):
        """
        提取周用水模式
        """
        # 按星期分组计算
        weekly_means = []
        for day in range(7):
            day_data = self.data[day::7]
            weekly_means.append(np.mean(day_data))
        
        return np.array(weekly_means)
    
    def decompose(self):
        """
        时间序列分解
        """
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        decomposition = seasonal_decompose(
            self.data,
            model='additive',
            period=24 if self.freq == 'H' else 96
        )
        
        return {
            'trend': decomposition.trend,
            'seasonal': decomposition.seasonal,
            'residual': decomposition.resid
        }
```

### 4.2 水力模型计算

```python
import numpy as np
from scipy.optimize import fsolve

class HydraulicModel:
    """
    管网水力模型
    """
    def __init__(self, network):
        """
        Parameters
        ----------
        network : dict
            管网拓扑结构
        """
        self.nodes = network['nodes']
        self.pipes = network['pipes']
        self.n_nodes = len(network['nodes'])
        self.n_pipes = len(network['pipes'])
    
    def hazen_williams(self, Q, L, C, D):
        """
        Hazen-Williams水头损失公式
        
        Parameters
        ----------
        Q : float
            流量 (m³/s)
        L : float
            管道长度 (m)
        C : float
            Hazen-Williams系数
        D : float
            管道直径 (m)
        
        Returns
        -------
        h_f : float
            水头损失 (m)
        """
        return 10.67 * L * Q**1.852 / (C**1.852 * D**4.87)
    
    def pressure_drop(self, Q, L, C, D, elevation_diff=0):
        """
        计算两点间压降
        """
        h_f = self.hazen_williams(Q, L, C, D)
        return h_f + elevation_diff
    
    def solve_network(self, demands, elevations, tank_levels):
        """
        求解管网水力方程
        
        Parameters
        ----------
        demands : array
            节点需水量 (m³/s)
        elevations : array
            节点高程 (m)
        tank_levels : dict
            水箱水位
        
        Returns
        -------
        pressures : array
            节点压力 (m)
        flows : array
            管道流量 (m³/s)
        """
        def equations(x):
            pressures = x[:self.n_nodes]
            flows = x[self.n_nodes:self.n_nodes + self.n_pipes]
            
            eqs = []
            
            # 节点连续性方程
            for i in range(self.n_nodes):
                inflow = 0
                outflow = 0
                
                for j, pipe in enumerate(self.pipes):
                    if pipe['from'] == i:
                        outflow += flows[j]
                    elif pipe['to'] == i:
                        inflow += flows[j]
                
                eqs.append(inflow - outflow - demands[i])
            
            # 管道能量方程
            for j, pipe in enumerate(self.pipes):
                i_from = pipe['from']
                i_to = pipe['to']
                
                h_f = self.hazen_williams(
                    abs(flows[j]),
                    pipe['length'],
                    pipe['C'],
                    pipe['diameter']
                )
                
                # 方向修正
                if flows[j] > 0:
                    eqs.append(pressures[i_from] - pressures[i_to] - h_f)
                else:
                    eqs.append(pressures[i_to] - pressures[i_from] - h_f)
            
            return eqs
        
        # 初始猜测
        x0 = np.zeros(self.n_nodes + self.n_pipes)
        x0[:self.n_nodes] = 30  # 初始压力30m
        
        # 求解
        solution = fsolve(equations, x0)
        
        pressures = solution[:self.n_nodes]
        flows = solution[self.n_nodes:]
        
        return pressures, flows
    
    def calculate_energy(self, flows, pump_efficiency=0.75, electricity_cost=0.8):
        """
        计算水泵能耗
        
        Parameters
        ----------
        flows : array
            管道流量
        pump_efficiency : float
            水泵效率
        electricity_cost : float
            电价 (元/kWh)
        """
        # 假设水泵扬程
        total_head = 40  # m
        
        # 总流量
        total_flow = np.sum(flows[flows > 0])
        
        # 功率计算 (kW)
        power = 9.81 * total_flow * total_head / pump_efficiency
        
        # 日能耗 (kWh)
        daily_energy = power * 24
        
        # 日费用
        daily_cost = daily_energy * electricity_cost
        
        return power, daily_energy, daily_cost
```

### 4.3 漏损检测

```python
import numpy as np
from scipy import stats

class LeakageDetection:
    """
    漏损检测模型
    """
    def __init__(self, flow_data, pressure_data=None):
        """
        Parameters
        ----------
        flow_data : array
            流量数据 (n_timesteps, n_points)
        pressure_data : array
            压力数据
        """
        self.flow_data = np.array(flow_data)
        self.pressure_data = pressure_data
    
    def mass_balance(self, inflow, outflow, tolerance=0.05):
        """
        质量平衡分析
        
        Parameters
        ----------
        inflow : array
            入流量
        outflow : array
            出流量
        tolerance : float
            容许误差
        
        Returns
        -------
        leakage : array
            漏损量
        is_leak : bool
            是否存在漏损
        """
        leakage = inflow - outflow
        leakage_ratio = np.mean(leakage) / np.mean(inflow)
        
        is_leak = leakage_ratio > tolerance
        
        return leakage, is_leak, leakage_ratio
    
    def minimum_night_flow(self, flow_data, expected_mnf=None):
        """
        夜间最小流量法
        
        Parameters
        ----------
        flow_data : array
            24小时流量数据
        expected_mnf : float
            预期最小流量
        """
        # 找到夜间最小流量（通常在凌晨2-4点）
        night_hours = list(range(2, 5))
        mnf = np.min(flow_data[night_hours])
        
        if expected_mnf is None:
            # 使用统计方法估算
            expected_mnf = np.mean(flow_data[night_hours]) * 0.8
        
        leakage = mnf - expected_mnf
        
        return {
            'mnf': mnf,
            'expected_mnf': expected_mnf,
            'leakage': leakage,
            'is_leak': leakage > 0
        }
    
    def pressure_leakage_correlation(self, pressure, leakage, window=24):
        """
        压力-漏损相关性分析
        """
        # 滑动窗口分析
        n = len(pressure)
        correlations = []
        
        for i in range(window, n):
            p_window = pressure[i-window:i]
            l_window = leakage[i-window:i]
            
            corr, p_value = stats.pearsonr(p_window, l_window)
            correlations.append((corr, p_value))
        
        avg_corr = np.mean([c[0] for c in correlations])
        
        return avg_corr, correlations
    
    def anomaly_detection(self, flow_data, threshold=2.0):
        """
        异常检测（基于统计方法）
        
        Parameters
        ----------
        flow_data : array
            流量数据
        threshold : float
            异常阈值（标准差倍数）
        """
        mean_flow = np.mean(flow_data)
        std_flow = np.std(flow_data)
        
        # 计算Z-score
        z_scores = (flow_data - mean_flow) / std_flow
        
        # 检测异常
        anomalies = np.abs(z_scores) > threshold
        anomaly_indices = np.where(anomalies)[0]
        
        return {
            'anomalies': anomalies,
            'anomaly_indices': anomaly_indices,
            'z_scores': z_scores,
            'threshold': threshold
        }
    
    def locate_leakage(self, flow_measurements, pipe_network):
        """
        漏损定位
        
        Parameters
        ----------
        flow_measurements : dict
            各测量点流量
        pipe_network : dict
            管网拓扑
        """
        # 基于流量差值的漏损定位
        leak_suspects = []
        
        for pipe_id, pipe in pipe_network.items():
            q_in = flow_measurements.get(pipe['from'], 0)
            q_out = flow_measurements.get(pipe['to'], 0)
            
            # 流量差
            delta_q = q_in - q_out
            
            if delta_q > 0:  # 存在流量损失
                leak_suspects.append({
                    'pipe': pipe_id,
                    'from': pipe['from'],
                    'to': pipe['to'],
                    'leakage': delta_q,
                    'confidence': delta_q / q_in if q_in > 0 else 0
                })
        
        # 按漏损量排序
        leak_suspects.sort(key=lambda x: x['leakage'], reverse=True)
        
        return leak_suspects
```

### 4.4 智能调度

```python
import numpy as np
from scipy.optimize import minimize

class SmartScheduling:
    """
    智能供水调度系统
    """
    def __init__(self, demand_forecast, pump_params, tank_params, electricity_tariff):
        """
        Parameters
        ----------
        demand_forecast : array
            24小时需求预测
        pump_params : dict
            水泵参数
        tank_params : dict
            水箱参数
        electricity_tariff : array
            分时电价
        """
        self.demand = demand_forecast
        self.pumps = pump_params
        self.tanks = tank_params
        self.tariff = electricity_tariff
        
        self.n_hours = len(demand_forecast)
    
    def optimize_schedule(self):
        """
        优化调度方案
        """
        def objective(x):
            """
            目标函数：最小化总成本
            """
            # x包含：水泵运行状态、水箱水位
            pump_schedule = x[:self.n_hours * self.pumps['n_pumps']]
            tank_levels = x[self.n_hours * self.pumps['n_pumps']:]
            
            # 能耗成本
            energy_cost = np.sum(pump_schedule * self.tariff * self.pumps['power'])
            
            # 漏损成本（与压力相关）
            pressure_cost = np.sum(tank_levels * self.pumps['leakage_coeff'])
            
            # 水质成本（停留时间）
            quality_cost = np.sum(np.maximum(tank_levels - self.tanks['optimal_level'], 0) * 0.1)
            
            return energy_cost + pressure_cost + quality_cost
        
        def constraint_demand(x):
            """需求满足约束"""
            pump_schedule = x[:self.n_hours * self.pumps['n_pumps']]
            total_supply = np.sum(pump_schedule.reshape(self.n_hours, self.pumps['n_pumps']), axis=1)
            return total_supply - self.demand
        
        def constraint_tank_level(x):
            """水箱水位约束"""
            tank_levels = x[self.n_hours * self.pumps['n_pumps']:]
            return np.minimum(tank_levels - self.tanks['min_level'], 
                            self.tanks['max_level'] - tank_levels)
        
        # 初始解
        x0 = np.zeros(self.n_hours * self.pumps['n_pumps'] + self.tanks['n_tanks'])
        x0[:self.n_hours * self.pumps['n_pumps']] = 0.5  # 初始开度50%
        x0[self.n_hours * self.pumps['n_pumps']:] = self.tanks['optimal_level']
        
        # 约束
        constraints = [
            {'type': 'ineq', 'fun': constraint_demand},
            {'type': 'ineq', 'fun': constraint_tank_level}
        ]
        
        # 边界
        bounds = [(0, 1)] * (self.n_hours * self.pumps['n_pumps']) + \
                [(self.tanks['min_level'], self.tanks['max_level'])] * self.tanks['n_tanks']
        
        # 优化
        result = minimize(objective, x0, method='SLSQP', 
                         bounds=bounds, constraints=constraints)
        
        return self._parse_result(result.x)
    
    def _parse_result(self, x):
        """解析优化结果"""
        pump_schedule = x[:self.n_hours * self.pumps['n_pumps']]
        tank_levels = x[self.n_hours * self.pumps['n_pumps']:]
        
        return {
            'pump_schedule': pump_schedule.reshape(self.n_hours, self.pumps['n_pumps']),
            'tank_levels': tank_levels.reshape(-1, self.tanks['n_tanks']),
            'total_cost': self._calculate_cost(x),
            'total_energy': self._calculate_energy(x)
        }
    
    def _calculate_cost(self, x):
        pump_schedule = x[:self.n_hours * self.pumps['n_pumps']]
        return np.sum(pump_schedule.reshape(self.n_hours, self.pumps['n_pumps']) * 
                     self.tariff.reshape(-1, 1) * self.pumps['power'])
    
    def _calculate_energy(self, x):
        pump_schedule = x[:self.n_hours * self.pumps['n_pumps']]
        return np.sum(pump_schedule.reshape(self.n_hours, self.pumps['n_pumps']) * 
                     self.pumps['power'])
    
    def real_time_adjustment(self, current_state, measured_demand):
        """
        实时调度调整
        """
        # 计算偏差
        error = measured_demand - self.demand
        
        # PID控制调整
        kp, ki, kd = 0.5, 0.1, 0.05
        
        adjustment = kp * error + ki * np.sum(error) + kd * np.diff(error)
        
        return adjustment
```

### 4.5 数据可视化

```python
import matplotlib.pyplot as plt
import numpy as np

def plot_water_system_dashboard(demand, supply, pressure, leakage):
    """
    绘制供水系统监控仪表盘
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    hours = np.arange(len(demand))
    
    # 供需平衡图
    ax1 = axes[0, 0]
    ax1.plot(hours, demand, 'b-', linewidth=2, label='需水量')
    ax1.plot(hours, supply, 'r--', linewidth=2, label='供水量')
    ax1.fill_between(hours, demand, supply, alpha=0.3, color='gray')
    ax1.set_xlabel('时间 (h)')
    ax1.set_ylabel('流量 (m³/h)')
    ax1.set_title('供需平衡')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 压力分布图
    ax2 = axes[0, 1]
    ax2.plot(hours, pressure, 'g-', linewidth=2)
    ax2.axhline(y=20, color='r', linestyle='--', label='最低压力')
    ax2.axhline(y=40, color='orange', linestyle='--', label='最高压力')
    ax2.set_xlabel('时间 (h)')
    ax2.set_ylabel('压力 (m)')
    ax2.set_title('管网压力')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 漏损趋势图
    ax3 = axes[1, 0]
    ax3.bar(hours, leakage, color='red', alpha=0.6)
    ax3.set_xlabel('时间 (h)')
    ax3.set_ylabel('漏损量 (m³/h)')
    ax3.set_title('漏损趋势')
    ax3.grid(True, alpha=0.3)
    
    # 能耗分析图
    ax4 = axes[1, 1]
    energy = supply * 0.05  # 简化能耗计算
    ax4.fill_between(hours, 0, energy, alpha=0.3, color='blue')
    ax4.plot(hours, energy, 'b-', linewidth=2)
    ax4.set_xlabel('时间 (h)')
    ax4.set_ylabel('能耗 (kWh)')
    ax4.set_title('水泵能耗')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 忽略时变特性 | 预测偏差大 | 考虑峰谷系数和周期性 |
| 水力模型简化过度 | 压力计算错误 | 使用完整水力方程 |
| 漏损阈值不当 | 误报或漏报 | 根据历史数据动态调整 |
| 电价模型错误 | 调度成本偏差 | 使用实际分时电价 |
| 忽略水质约束 | 水质风险 | 加入停留时间约束 |
| 实时性不足 | 响应延迟 | 使用增量更新算法 |

---

## 6. 验证方法

### 6.1 模型验证
- 与历史数据对比（RMSE、MAE）
- 检查预测区间覆盖率
- 验证水力模型压力计算

### 6.2 系统验证
- 模拟漏损场景测试检测率
- 评估调度方案的成本节约
- 检验需求预测准确性

### 6.3 稳健性测试
- 极端用水场景
- 设备故障场景
- 传感器数据缺失场景

### 6.4 性能评估
- 计算响应时间
- 评估算法收敛性
- 分析计算复杂度

---

## 7. 真题案例

### 2020E 校园供水系统

**题目概述**：设计智能校园供水管理系统，实现需求预测、漏损检测和优化调度。

**关键信息**：
- 校园管网拓扑结构
- 历史用水量数据
- 水泵和水箱参数
- 分时电价信息

**解题思路**：
1. 建立用水需求预测模型（ARIMA/指数平滑）
2. 构建管网水力模型
3. 设计漏损检测算法
4. 开发智能调度优化模型
5. 开发监控仪表盘

**参考代码框架**：
```python
# 2020E问题求解框架
# 1. 数据加载
demand_data = [...]  # 历史用水量

# 2. 需求预测
forecaster = WaterDemandForecast(demand_data)
forecast = forecaster.arima_forecast(steps=24)

# 3. 水力模型
network = {
    'nodes': [...],
    'pipes': [...]
}
hydraulic = HydraulicModel(network)
pressures, flows = hydraulic.solve_network(demands, elevations, tank_levels)

# 4. 漏损检测
detector = LeakageDetection(flow_data)
leakage, is_leak = detector.mass_balance(inflow, outflow)

# 5. 智能调度
scheduler = SmartScheduling(forecast, pump_params, tank_params, tariff)
schedule = scheduler.optimize_schedule()

# 6. 可视化
plot_water_system_dashboard(demand, supply, pressure, leakage)
```

---

## 8. 参考文献

| 论文编号 | 核心方法 | 关键创新 |
|---------|---------|---------|
| 2020E-A01 | ARIMA+水力模型 | 需求预测与调度结合 |
| 2020E-A02 | 异常检测+优化 | 实时漏损定位 |
| 2020E-A03 | 机器学习+控制 | 自适应调度算法 |

---

## 9. 验证清单

- [ ] 需求预测MAPE < 15%
- [ ] 水力模型压力误差 < 5%
- [ ] 漏损检测准确率 > 90%
- [ ] 调度方案成本节约 > 10%
- [ ] 系统响应时间 < 1秒
- [ ] 水质约束满足要求
- [ ] 峰谷调度效果明显
- [ ] 实时监控界面完整
