"""
模板来源: resources/code-templates/numerical/runge_kutta.py
修改说明: 
  - 新增Runge-Kutta ODE求解模板
  - 支持RK4、自适应步长、刚性方程
"""
import numpy as np
from scipy.integrate import odeint, solve_ivp
import matplotlib.pyplot as plt


class ODESolver:
    """常微分方程求解器"""
    
    def __init__(self, f):
        """
        f: 函数 f(t, y)，返回dy/dt
        """
        self.f = f
    
    def euler(self, y0, t_span, h=0.01):
        """Euler法"""
        t0, tf = t_span
        t = np.arange(t0, tf + h, h)
        y = np.zeros(len(t))
        y[0] = y0
        
        for i in range(1, len(t)):
            y[i] = y[i-1] + h * self.f(t[i-1], y[i-1])
        
        return t, y
    
    def runge_kutta_4(self, y0, t_span, h=0.01):
        """经典四阶Runge-Kutta法"""
        t0, tf = t_span
        t = np.arange(t0, tf + h, h)
        y = np.zeros(len(t))
        y[0] = y0
        
        for i in range(1, len(t)):
            k1 = self.f(t[i-1], y[i-1])
            k2 = self.f(t[i-1] + h/2, y[i-1] + h/2 * k1)
            k3 = self.f(t[i-1] + h/2, y[i-1] + h/2 * k2)
            k4 = self.f(t[i-1] + h, y[i-1] + h * k3)
            
            y[i] = y[i-1] + h/6 * (k1 + 2*k2 + 2*k3 + k4)
        
        return t, y
    
    def scipy_solve(self, y0, t_span, method='RK45', h=0.01):
        """使用scipy求解"""
        t0, tf = t_span
        t_eval = np.arange(t0, tf + h, h)
        
        sol = solve_ivp(self.f, t_span, [y0], method=method, 
                       t_eval=t_eval, dense_output=True)
        
        return sol.t, sol.y[0]
    
    def solve_stiff(self, y0, t_span):
        """求解刚性方程（使用BDF方法）"""
        sol = solve_ivp(self.f, t_span, [y0], method='BDF', 
                       dense_output=True)
        
        return sol.t, sol.y[0]
    
    def adaptive_step_rk45(self, y0, t_span, tol=1e-6, h_init=0.01):
        """自适应步长RK45"""
        t0, tf = t_span
        t = [t0]
        y = [y0]
        h = h_init
        
        while t[-1] < tf:
            # 4阶和5阶RK
            k1 = self.f(t[-1], y[-1])
            k2 = self.f(t[-1] + h/4, y[-1] + h/4 * k1)
            k3 = self.f(t[-1] + 3*h/8, y[-1] + 3*h/32 * k1 + 9*h/32 * k2)
            k4 = self.f(t[-1] + 12*h/13, y[-1] + 1932*h/2197 * k1 - 7200*h/2197 * k2 + 7296*h/2197 * k3)
            k5 = self.f(t[-1] + h, y[-1] + 439*h/216 * k1 - 8*h * k2 + 3680*h/513 * k3 - 845*h/4104 * k4)
            k6 = self.f(t[-1] + h/2, y[-1] - 8*h/27 * k1 + 2*h * k2 - 3544*h/2565 * k3 + 1859*h/4104 * k4 - 11*h/40 * k5)
            
            # 5阶解
            y5 = y[-1] + h * (16*h/135 * k1 + 6656*h/12825 * k3 + 28561*h/56430 * k4 - 9*h/50 * k5 + 2*h/55 * k6)
            
            # 误差估计
            error = abs(h * (1*h/360 * k1 - 128*h/4275 * k3 - 2197*h/75240 * k4 + 1*h/50 * k5 + 2*h/55 * k6))
            
            # 调整步长
            if error < tol:
                t.append(t[-1] + h)
                y.append(y5)
            
            h = h * min(2, max(0.1, 0.84 * (tol/error)**0.25))
        
        return np.array(t), np.array(y)


def lotka_volterra(t, y, alpha=1.5, beta=1.0, delta=0.5, gamma=3.0):
    """Lotka-Volterra捕食者-猎物模型"""
    x, z = y
    dxdt = alpha * x - beta * x * z
    dzdt = delta * x * z - gamma * z
    return [dxdt, dzdt]


if __name__ == "__main__":
    # 示例：求解ODE
    print("Runge-Kutta ODE求解示例\n")
    
    # 定义ODE: dy/dt = -2y + 1, y(0) = 0
    def f(t, y):
        return -2 * y + 1
    
    # 创建求解器
    solver = ODESolver(f)
    
    # 初始条件和时间范围
    y0 = 0
    t_span = (0, 5)
    
    # Euler法
    t_euler, y_euler = solver.euler(y0, t_span, h=0.1)
    print(f"Euler法: y(5) = {y_euler[-1]:.6f}")
    
    # RK4法
    t_rk4, y_rk4 = solver.runge_kutta_4(y0, t_span, h=0.1)
    print(f"RK4法: y(5) = {y_rk4[-1]:.6f}")
    
    # scipy求解
    t_scipy, y_scipy = solver.scipy_solve(y0, t_span)
    print(f"scipy: y(5) = {y_scipy[-1]:.6f}")
    
    # 解析解: y(t) = 0.5 * (1 - exp(-2t))
    t_exact = np.linspace(0, 5, 100)
    y_exact = 0.5 * (1 - np.exp(-2 * t_exact))
    print(f"解析解: y(5) = {0.5 * (1 - np.exp(-10)):.6f}")
    
    # 绘制比较图
    plt.figure(figsize=(10, 6))
    plt.plot(t_exact, y_exact, 'k-', label='解析解', linewidth=2)
    plt.plot(t_euler, y_euler, 'o--', label='Euler法', markersize=4)
    plt.plot(t_rk4, y_rk4, 's--', label='RK4法', markersize=4)
    plt.plot(t_scipy, y_scipy, '^--', label='scipy', markersize=4)
    plt.xlabel('t')
    plt.ylabel('y')
    plt.title('ODE求解方法比较')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('figures/ode_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("\n比较图已保存: figures/ode_comparison.png")
