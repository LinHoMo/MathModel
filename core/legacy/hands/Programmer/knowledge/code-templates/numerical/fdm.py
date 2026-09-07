"""
模板来源: resources/code-templates/numerical/fdm.py
修改说明: 
  - 新增有限差分法模板
  - 支持热传导方程、波动方程、拉普拉斯方程
"""
import numpy as np
import matplotlib.pyplot as plt


class FiniteDifferenceMethod:
    """有限差分法求解PDE"""
    
    def __init__(self, x_grid, t_grid):
        self.x = x_grid
        self.t = t_grid
        self.dx = x_grid[1] - x_grid[0]
        self.dt = t_grid[1] - t_grid[0]
        self.nx = len(x_grid)
        self.nt = len(t_grid)
    
    def heat_equation_explicit(self, u0, alpha):
        """
        显式差分法求解热传导方程
        ∂u/∂t = α ∂²u/∂x²
        """
        r = alpha * self.dt / self.dx**2
        
        if r > 0.5:
            print(f"警告：r={r:.2f} > 0.5，数值可能不稳定")
        
        u = np.zeros((self.nt, self.nx))
        u[0, :] = u0
        
        for n in range(1, self.nt):
            for i in range(1, self.nx-1):
                u[n, i] = u[n-1, i] + r * (u[n-1, i+1] - 2*u[n-1, i] + u[n-1, i-1])
            
            # 边界条件
            u[n, 0] = u[n-1, 0] + r * (u[n-1, 1] - 2*u[n-1, 0] + u[n-1, -1])
            u[n, -1] = u[n, 0]
        
        return u
    
    def heat_equation_implicit(self, u0, alpha):
        """
        隐式差分法求解热传导方程（无条件稳定）
        """
        r = alpha * self.dt / self.dx**2
        
        # 构建三对角矩阵
        A = np.zeros((self.nx-2, self.nx-2))
        for i in range(self.nx-2):
            A[i, i] = 1 + 2*r
            if i > 0:
                A[i, i-1] = -r
            if i < self.nx-3:
                A[i, i+1] = -r
        
        u = np.zeros((self.nt, self.nx))
        u[0, :] = u0
        
        for n in range(1, self.nt):
            b = u[n-1, 1:-1].copy()
            b[0] += r * u[n, 0]
            b[-1] += r * u[n, -1]
            
            u[n, 1:-1] = np.linalg.solve(A, b)
            u[n, 0] = u[n, -1]
        
        return u
    
    def wave_equation(self, u0, v0, c):
        """
        有限差分法求解波动方程
        ∂²u/∂t² = c² ∂²u/∂x²
        """
        r = c * self.dt / self.dx
        
        if r > 1:
            print(f"警告：CFL数={r:.2f} > 1，数值不稳定")
        
        u = np.zeros((self.nt, self.nx))
        u[0, :] = u0
        u[1, :] = u0 + self.dt * v0
        
        for n in range(1, self.nt-1):
            for i in range(1, self.nx-1):
                u[n+1, i] = (2*u[n, i] - u[n-1, i] + 
                            r**2 * (u[n, i+1] - 2*u[n, i] + u[n, i-1]))
            
            # 边界条件
            u[n+1, 0] = u[n+1, 1]
            u[n+1, -1] = u[n+1, -2]
        
        return u
    
    def laplace_equation(self, u_init, bc_func, tol=1e-6, max_iter=1000):
        """
        迭代法求解拉普拉斯方程
        ∂²u/∂x² + ∂²u/∂y² = 0
        """
        u = u_init.copy()
        ny, nx = u.shape
        
        for iteration in range(max_iter):
            u_old = u.copy()
            
            for i in range(1, ny-1):
                for j in range(1, nx-1):
                    u[i, j] = 0.25 * (u[i+1, j] + u[i-1, j] + u[i, j+1] + u[i, j-1])
            
            u = bc_func(u)
            
            if np.max(np.abs(u - u_old)) < tol:
                print(f"收敛于第{iteration+1}次迭代")
                break
        
        return u
    
    def plot_heat_solution(self, u, title='热传导方程解', filename='figures/fdm_heat.png'):
        """绘制热传导方程解"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 时间演化
        for i in range(0, self.nt, self.nt//5):
            axes[0].plot(self.x, u[i, :], label=f't={self.t[i]:.2f}')
        axes[0].set_xlabel('x')
        axes[0].set_ylabel('u')
        axes[0].set_title('不同时间的解')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # 3D曲面
        X, T = np.meshgrid(self.x, self.t)
        im = axes[1].contourf(X, T, u, cmap='hot')
        axes[1].set_xlabel('x')
        axes[1].set_ylabel('t')
        axes[1].set_title('解的热力图')
        plt.colorbar(im, ax=axes[1])
        
        plt.suptitle(title)
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"图已保存: {filename}")


if __name__ == "__main__":
    # 示例：热传导方程
    print("有限差分法示例：热传导方程\n")
    
    # 定义网格
    x_grid = np.linspace(0, 1, 50)
    t_grid = np.linspace(0, 0.5, 100)
    
    fdm = FiniteDifferenceMethod(x_grid, t_grid)
    
    # 初始条件：sin(πx)
    u0 = np.sin(np.pi * x_grid)
    
    # 求解（α=0.01）
    alpha = 0.01
    u_explicit = fdm.heat_equation_explicit(u0, alpha)
    u_implicit = fdm.heat_equation_implicit(u0, alpha)
    
    # 绘制结果
    fdm.plot_heat_solution(u_explicit, '显式差分法', 'figures/fdm_heat_explicit.png')
    fdm.plot_heat_solution(u_implicit, '隐式差分法', 'figures/fdm_heat_implicit.png')
    
    # 比较
    plt.figure(figsize=(10, 6))
    plt.plot(x_grid, u0, 'k-', label='初始条件', linewidth=2)
    plt.plot(x_grid, u_explicit[-1, :], 'b--', label='显式差分法', linewidth=2)
    plt.plot(x_grid, u_implicit[-1, :], 'r--', label='隐式差分法', linewidth=2)
    plt.xlabel('x')
    plt.ylabel('u')
    plt.title(f'热传导方程解 (t={t_grid[-1]:.2f})')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('figures/fdm_heat_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("比较图已保存: figures/fdm_heat_comparison.png")
