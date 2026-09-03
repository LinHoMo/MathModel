"""
有限差分法求解热传导PDE模板
来源: 高教杯优秀论文
适用问题: 热传导、扩散方程、稳态温度场
输入: 网格参数、初始条件、边界条件
输出: 温度场分布、可视化结果
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')


class FiniteDifferenceHeat:
    """
    有限差分法求解热传导方程
    
    支持显式/隐式格式，1D/2D网格
    
    Parameters
    ----------
    nx : int
        空间网格数
    nt : int
        时间步数
    L : float
        空间域长度
    T : float
        模拟总时间
    """

    def __init__(self, nx: int = 50, nt: int = 200, L: float = 1.0, T: float = 0.5):
        self.nx = nx
        self.nt = nt
        self.L = L
        self.T = T
        self.dx = L / (nx - 1)
        self.dt = T / (nt - 1)
        self.x = np.linspace(0, L, nx)
        self.t = np.linspace(0, T, nt)

    def _build_tridiag(self, n: int, diag: float, lower: float, upper: float) -> np.ndarray:
        """构建三对角矩阵"""
        A = np.zeros((n, n))
        for i in range(n):
            A[i, i] = diag
            if i > 0:
                A[i, i - 1] = lower
            if i < n - 1:
                A[i, i + 1] = upper
        return A

    def thomas_algorithm(self, a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray) -> np.ndarray:
        """
        Thomas算法（追赶法）求解三对角方程组
        a: 下对角线, b: 主对角线, c: 上对角线, d: 右端向量
        """
        n = len(b)
        c_ = np.zeros(n)
        d_ = np.zeros(n)
        x = np.zeros(n)

        # 前向消元
        c_[0] = c[0] / b[0]
        d_[0] = d[0] / b[0]
        for i in range(1, n):
            m = b[i] - a[i] * c_[i - 1]
            c_[i] = c[i] / m
            d_[i] = (d[i] - a[i] * d_[i - 1]) / m

        # 回代
        x[-1] = d_[-1]
        for i in range(n - 2, -1, -1):
            x[i] = d_[i] - c_[i] * x[i + 1]

        return x

    def solve_explicit(self, u0: np.ndarray, alpha: float,
                       bc_left: float = 0.0, bc_right: float = 0.0) -> np.ndarray:
        """
        显式格式求解1D热传导方程
        ∂u/∂t = α ∂²u/∂x²
        稳定性条件: r = α·dt/dx² ≤ 0.5
        """
        r = alpha * self.dt / self.dx ** 2
        if r > 0.5:
            print(f"警告: r={r:.3f}>0.5, 显式格式可能不稳定")

        u = np.zeros((self.nt, self.nx))
        u[0, :] = u0.copy()

        for n in range(1, self.nt):
            # 内部节点更新
            for i in range(1, self.nx - 1):
                u[n, i] = u[n - 1, i] + r * (u[n - 1, i + 1] - 2 * u[n - 1, i] + u[n - 1, i - 1])
            # 边界条件
            u[n, 0] = bc_left
            u[n, -1] = bc_right

        return u

    def solve_implicit(self, u0: np.ndarray, alpha: float,
                       bc_left: float = 0.0, bc_right: float = 0.0) -> np.ndarray:
        """
        隐式格式（Crank-Nicolson）求解1D热传导方程
        无条件稳定，精度O(Δt²+Δx²)
        """
        r = alpha * self.dt / self.dx ** 2
        nx_int = self.nx - 2  # 内部节点数

        # 构建系数矩阵 A·u^{n+1} = B·u^n
        A = self._build_tridiag(nx_int, 1 + 2 * r, -r, -r)
        B = self._build_tridiag(nx_int, 1 - 2 * r, r, r)

        u = np.zeros((self.nt, self.nx))
        u[0, :] = u0.copy()

        for n in range(1, self.nt):
            # 右端项
            b = B @ u[n - 1, 1:-1]
            b[0] += r * bc_left
            b[-1] += r * bc_right

            # 使用Thomas算法求解
            u[n, 1:-1] = self.thomas_algorithm(
                np.full(nx_int, -r), np.full(nx_int, 1 + 2 * r),
                np.full(nx_int, -r), b
            )
            u[n, 0] = bc_left
            u[n, -1] = bc_right

        return u

    def solve_2d_explicit(self, u0_2d: np.ndarray, alpha: float,
                          bc_func: Optional[Callable] = None) -> np.ndarray:
        """
        显式格式求解2D热传导方程
        ∂u/∂t = α (∂²u/∂x² + ∂²u/∂y²)
        """
        ny, nx = u0_2d.shape
        r = alpha * self.dt / self.dx ** 2

        u = np.zeros((self.nt, ny, nx))
        u[0, :, :] = u0_2d.copy()

        for n in range(1, self.nt):
            u[n, :, :] = u[n - 1, :, :].copy()
            for i in range(1, ny - 1):
                for j in range(1, nx - 1):
                    u[n, i, j] = u[n - 1, i, j] + r * (
                        u[n - 1, i + 1, j] + u[n - 1, i - 1, j] +
                        u[n - 1, i, j + 1] + u[n - 1, i, j - 1] -
                        4 * u[n - 1, i, j]
                    )
            # 应用边界条件
            if bc_func is not None:
                u[n, :, :] = bc_func(u[n, :, :])

        return u

    def analytical_1d(self, x: np.ndarray, t: float, alpha: float, n_terms: int = 50) -> np.ndarray:
        """1D热传导方程解析解（u₀=sin(πx), 边界=0）"""
        u = np.zeros_like(x)
        for k in range(1, n_terms + 1):
            u += (2 / (k * np.pi)) * np.sin(k * np.pi * x) * np.exp(-alpha * (k * np.pi) ** 2 * t)
        return u

    def plot_solution(self, u: np.ndarray, title: str = "温度场分布", filename: Optional[str] = None):
        """绘制2D热图"""
        fig, ax = plt.subplots(figsize=(10, 6))
        X, T = np.meshgrid(self.x, self.t)
        im = ax.contourf(X, T, u, cmap='hot', levels=30)
        ax.set_xlabel('x')
        ax.set_ylabel('t')
        ax.set_title(title)
        plt.colorbar(im, ax=ax, label='Temperature')
        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        return fig

    def plot_comparison(self, u_ex: np.ndarray, u_im: np.ndarray, filename: Optional[str] = None):
        """比较显式/隐式结果"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # 不同时间快照
        snap_indices = [0, self.nt // 4, self.nt // 2, self.nt - 1]
        for idx in snap_indices:
            axes[0].plot(self.x, u_ex[idx, :], label=f't={self.t[idx]:.3f}')
        axes[0].set_title('Explicit Method')
        axes[0].set_xlabel('x')
        axes[0].set_ylabel('u')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)

        for idx in snap_indices:
            axes[1].plot(self.x, u_im[idx, :], label=f't={self.t[idx]:.3f}')
        axes[1].set_title('Implicit Method')
        axes[1].set_xlabel('x')
        axes[1].set_ylabel('u')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)

        plt.suptitle('Explicit vs Implicit Finite Difference')
        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        return fig


def run_example():
    """示例: 1D热传导方程 ∂u/∂t = 0.01·∂²u/∂x², u(0,x)=sin(πx)"""
    print("=" * 60)
    print("有限差分法求解热传导PDE")
    print("=" * 60)

    fdm = FiniteDifferenceHeat(nx=50, nt=300, L=1.0, T=0.5)
    alpha = 0.01
    u0 = np.sin(np.pi * fdm.x)

    print(f"\n网格参数: nx={fdm.nx}, nt={fdm.nt}")
    print(f"扩散系数: α={alpha}")
    print(f"网格比: r={alpha * fdm.dt / fdm.dx**2:.4f}")

    # 显式求解
    u_explicit = fdm.solve_explicit(u0, alpha)
    print(f"\n显式格式完成")

    # 隐式求解
    u_implicit = fdm.solve_implicit(u0, alpha)
    print(f"隐式格式完成")

    # 解析解
    u_exact = fdm.analytical_1d(fdm.x, fdm.T, alpha)
    err_explicit = np.max(np.abs(u_explicit[-1, :] - u_exact))
    err_implicit = np.max(np.abs(u_implicit[-1, :] - u_exact))
    print(f"\n最终时刻最大误差:")
    print(f"  显式: {err_explicit:.6f}")
    print(f"  隐式: {err_implicit:.6f}")

    # 绘制结果
    fdm.plot_solution(u_explicit, 'Explicit FD Solution', 'figures/fdm_explicit.png')
    fdm.plot_solution(u_implicit, 'Implicit FD Solution', 'figures/fdm_implicit.png')
    fdm.plot_comparison(u_explicit, u_implicit, 'figures/fdm_comparison.png')
    print("\n图片已保存到 figures/ 目录")


if __name__ == "__main__":
    run_example()
