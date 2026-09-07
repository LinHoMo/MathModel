"""
Thomas算法（追赶法）求解三对角线性方程组模板
来源: 数值分析经典算法
适用问题: 三对角方程组、有限差分法中的隐式格式
输入: 三对角矩阵系数、右端向量
输出: 方程组解、与numpy求解对比
"""

import numpy as np
import time
from typing import Tuple
import warnings
warnings.filterwarnings('ignore')


class ThomasSolver:
    """
    Thomas算法（追赶法）求解三对角线性方程组
    
    Ax = d, 其中A为三对角矩阵:
    | b₀ c₀  0   0  ...  0  |
    | a₁ b₁ c₁  0  ...  0  |
    |  0 a₂ b₂ c₂  ...  0  |
    |  :  :  :  :   :   :  |
    |  0  0  0  0 aₙ₋₁ bₙ₋₁|
    
    时间复杂度: O(n), 空间复杂度: O(n)
    """

    def __init__(self):
        self.lower = None   # 下对角线 a
        self.diagonal = None  # 主对角线 b
        self.upper = None   # 上对角线 c
        self.rhs = None     # 右端向量 d
        self.solution = None

    def set_coefficients(self, lower: np.ndarray, diagonal: np.ndarray,
                         upper: np.ndarray, rhs: np.ndarray) -> None:
        """
        设置三对角矩阵系数
        
        Parameters
        ----------
        lower : ndarray, shape (n-1,)
            下对角线 a[1], a[2], ..., a[n-1]
        diagonal : ndarray, shape (n,)
            主对角线 b[0], b[1], ..., b[n-1]
        upper : ndarray, shape (n-1,)
            上对角线 c[0], c[1], ..., c[n-2]
        rhs : ndarray, shape (n,)
            右端向量 d[0], d[1], ..., d[n-1]
        """
        n = len(diagonal)
        if len(lower) != n - 1 or len(upper) != n - 1 or len(rhs) != n:
            raise ValueError("输入维度不匹配")

        self.lower = lower.copy().astype(float)
        self.diagonal = diagonal.copy().astype(float)
        self.upper = upper.copy().astype(float)
        self.rhs = rhs.copy().astype(float)

    def solve(self) -> np.ndarray:
        """
        执行Thomas算法
        
        Returns
        -------
        x : ndarray
            方程组解
        """
        n = len(self.diagonal)

        # 前向消元: 消去下对角线
        c_star = np.zeros(n - 1)
        d_star = np.zeros(n)

        # 第一行
        c_star[0] = self.upper[0] / self.diagonal[0]
        d_star[0] = self.rhs[0] / self.diagonal[0]

        for i in range(1, n):
            denom = self.diagonal[i] - self.lower[i - 1] * c_star[i - 1]
            if i < n - 1:
                c_star[i] = self.upper[i] / denom
            d_star[i] = (self.rhs[i] - self.lower[i - 1] * d_star[i - 1]) / denom

        # 回代: 从最后一行向上求解
        x = np.zeros(n)
        x[-1] = d_star[-1]
        for i in range(n - 2, -1, -1):
            x[i] = d_star[i] - c_star[i] * x[i + 1]

        self.solution = x
        return x

    def get_lu(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        返回LU分解结果 (L和U矩阵)
        A = L·U, L为下三角, U为上三角
        """
        n = len(self.diagonal)
        L = np.eye(n)
        U = np.zeros((n, n))

        # L的下对角线
        for i in range(1, n):
            L[i, i - 1] = self.lower[i - 1] / (
                self.diagonal[i - 1] if i == 1 else
                self.diagonal[i - 1] - self.lower[i - 2] * (self.upper[i - 2] /
                    (self.diagonal[i - 2] if i == 2 else 1))
            )

        # U的主对角线和上对角线
        c_star = np.zeros(n)
        c_star[0] = self.upper[0] / self.diagonal[0]
        for i in range(1, n - 1):
            denom = self.diagonal[i] - self.lower[i - 1] * c_star[i - 1]
            c_star[i] = self.upper[i] / denom

        for i in range(n):
            U[i, i] = self.diagonal[i] - (self.lower[i - 1] * c_star[i - 1] if i > 0 else 0)
            if i < n - 1:
                U[i, i + 1] = self.upper[i]

        return L, U

    def verify(self) -> float:
        """验证解的正确性，返回残差范数"""
        if self.solution is None:
            raise ValueError("请先调用solve()")

        n = len(self.diagonal)
        A = np.zeros((n, n))
        for i in range(n):
            A[i, i] = self.diagonal[i]
            if i > 0:
                A[i, i - 1] = self.lower[i - 1]
            if i < n - 1:
                A[i, i + 1] = self.upper[i]

        residual = np.linalg.norm(A @ self.solution - self.rhs)
        return residual


def build_random_tridiag(n: int, seed: int = 42) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """生成随机三对角系统（对角占优，确保可解）"""
    np.random.seed(seed)

    # 主对角线（强对角占优保证稳定性）
    diagonal = np.random.uniform(5, 10, n)

    # 下对角线和上对角线
    lower = np.random.uniform(-1, 1, n - 1)
    upper = np.random.uniform(-1, 1, n - 1)

    # 右端向量
    x_exact = np.random.uniform(-5, 5, n)
    rhs = np.zeros(n)
    for i in range(n):
        rhs[i] = diagonal[i] * x_exact[i]
        if i > 0:
            rhs[i] += lower[i - 1] * x_exact[i - 1]
        if i < n - 1:
            rhs[i] += upper[i] * x_exact[i + 1]

    return lower, diagonal, upper, rhs, x_exact


def run_example():
    """示例: 求解三对角方程组并与numpy对比"""
    print("=" * 60)
    print("Thomas算法（追赶法）求解三对角方程组")
    print("=" * 60)

    sizes = [10, 100, 1000, 5000]

    for n in sizes:
        print(f"\n--- n = {n} ---")
        lower, diagonal, upper, rhs, x_exact = build_random_tridiag(n)

        # Thomas算法
        solver = ThomasSolver()
        solver.set_coefficients(lower, diagonal, upper, rhs)

        t0 = time.time()
        x_thomas = solver.solve()
        t_thomas = time.time() - t0

        residual = solver.verify()
        err_thomas = np.max(np.abs(x_thomas - x_exact))

        # numpy.linalg.solve (构建完整矩阵)
        A_full = np.diag(diagonal) + np.diag(lower, -1) + np.diag(upper, 1)
        t0 = time.time()
        x_numpy = np.linalg.solve(A_full, rhs)
        t_numpy = time.time() - t0

        err_numpy = np.max(np.abs(x_numpy - x_exact))

        print(f"  Thomas: max_error={err_thomas:.2e}, time={t_thomas*1000:.3f}ms, residual={residual:.2e}")
        print(f"  Numpy:  max_error={err_numpy:.2e}, time={t_numpy*1000:.3f}ms")
        print(f"  加速比: {t_numpy / t_thomas:.1f}x")

    # 小规模详细展示
    print("\n" + "=" * 60)
    print("详细示例: n=5")
    print("=" * 60)
    lower = np.array([-1, -1, -1, -1], dtype=float)
    diagonal = np.array([4, 4, 4, 4, 4], dtype=float)
    upper = np.array([-1, -1, -1, -1], dtype=float)
    rhs = np.array([3, 2, 2, 2, 3], dtype=float)

    print("\n三对角矩阵 A:")
    n = len(diagonal)
    A = np.diag(diagonal) + np.diag(lower, -1) + np.diag(upper, 1)
    print(A)
    print(f"\n右端向量 d: {rhs}")

    solver = ThomasSolver()
    solver.set_coefficients(lower, diagonal, upper, rhs)
    x = solver.solve()

    print(f"\n解 x: {x}")
    print(f"验证 Ax: {A @ x}")
    print(f"残差范数: {solver.verify():.2e}")


if __name__ == "__main__":
    run_example()
