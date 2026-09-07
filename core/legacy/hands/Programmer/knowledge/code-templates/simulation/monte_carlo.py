"""
蒙特卡洛仿真框架模板
来源: 数学建模常用方法
适用问题: 积分近似、风险评估、排队系统、期权定价
输入: 概率分布、目标函数、仿真参数
输出: 估计值、置信区间、收敛诊断
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, Optional, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')


class MonteCarloSimulator:
    """
    蒙特卡洛仿真框架
    
    支持:
    - 自定义概率分布采样
    - 方差缩减技术（重要性抽样、对偶变量）
    - 收敛性诊断
    - 置信区间计算
    
    Parameters
    ----------
    n_samples : int
        样本数量
    seed : int
        随机种子
    """

    def __init__(self, n_samples: int = 100000, seed: int = 42):
        self.n_samples = n_samples
        self.seed = seed
        np.random.seed(seed)
        self.results = {}

    def estimate_integral(self, func: Callable, a: float, b: float,
                          method: str = 'standard') -> Dict:
        """
        蒙特卡洛估计定积分 ∫_a^b f(x) dx
        
        Parameters
        ----------
        func : callable
            被积函数
        a, b : float
            积分区间
        method : str
            'standard': 标准MC
            'importance': 重要性抽样
            'antithetic': 对偶变量
        """
        if method == 'standard':
            # 标准MC: 均匀采样
            x = np.random.uniform(a, b, self.n_samples)
            values = func(x)
            estimate = (b - a) * np.mean(values)
            std_err = (b - a) * np.std(values) / np.sqrt(self.n_samples)

        elif method == 'importance':
            # 重要性抽样: 使用beta分布作为建议分布
            # 适用于[0,1]区间上的积分
            if a == 0 and b == 1:
                alpha_imp, beta_imp = 2, 2  # Beta(2,2)作为建议分布
                x = np.random.beta(alpha_imp, beta_imp, self.n_samples)
                pdf_imp = lambda t: (t ** (alpha_imp - 1) * (1 - t) ** (beta_imp - 1) /
                                     np.math.beta(alpha_imp, beta_imp))
                values = func(x) / pdf_imp(x)
                estimate = np.mean(values)
                std_err = np.std(values) / np.sqrt(self.n_samples)
            else:
                # 一般区间: 变换到[0,1]
                t = np.random.beta(2, 2, self.n_samples)
                x = a + (b - a) * t
                pdf_imp = lambda tt: 6 * tt * (1 - tt)  # Beta(2,2)的PDF
                values = func(x) / pdf_imp(t) * (b - a)
                estimate = np.mean(values)
                std_err = np.std(values) / np.sqrt(self.n_samples)

        elif method == 'antithetic':
            # 对偶变量法
            n_half = self.n_samples // 2
            x = np.random.uniform(a, b, n_half)
            x_anti = a + b - x  # 对偶样本
            values_pos = func(x)
            values_neg = func(x_anti)
            combined = (values_pos + values_neg) / 2
            estimate = (b - a) * np.mean(combined)
            std_err = (b - a) * np.std(combined) / np.sqrt(n_half)

        else:
            raise ValueError(f"Unknown method: {method}")

        ci_95 = (estimate - 1.96 * std_err, estimate + 1.96 * std_err)

        self.results[method] = {
            'estimate': estimate,
            'std_error': std_err,
            'ci_95': ci_95,
            'n_samples': self.n_samples
        }

        return self.results[method]

    def simulate_random_walk(self, n_steps: int = 1000, n_paths: int = 100,
                              mu: float = 0.0, sigma: float = 1.0,
                              dt: float = 0.01) -> Dict:
        """
        几何布朗运动 (GBM) 仿真
        dS = μS dt + σS dW
        
        Parameters
        ----------
        n_steps : int
            时间步数
        n_paths : int
            路径数
        mu : float
            漂移率
        sigma : float
            波动率
        dt : float
            时间步长
        """
        S0 = 100  # 初始价格
        t = np.linspace(0, n_steps * dt, n_steps + 1)

        # 生成GBM路径
        dW = np.random.normal(0, np.sqrt(dt), (n_paths, n_steps))
        S = np.zeros((n_paths, n_steps + 1))
        S[:, 0] = S0

        for i in range(n_steps):
            S[:, i + 1] = S[:, i] * np.exp((mu - 0.5 * sigma ** 2) * dt + sigma * dW[:, i])

        # 统计
        final_prices = S[:, -1]
        stats = {
            'mean': np.mean(final_prices),
            'std': np.std(final_prices),
            'percentile_5': np.percentile(final_prices, 5),
            'percentile_95': np.percentile(final_prices, 95),
            'prob_loss': np.mean(final_prices < S0),
            'paths': S,
            'time': t
        }

        self.results['random_walk'] = stats
        return stats

    def convergence_analysis(self, func: Callable, a: float, b: float,
                              sample_sizes: Optional[np.ndarray] = None) -> Dict:
        """
        收敛性诊断: 分析不同样本量下的估计精度
        
        Returns
        -------
        analysis : dict
            包含样本量、估计值、标准误差
        """
        if sample_sizes is None:
            sample_sizes = np.logspace(2, 5, 20).astype(int)

        estimates = []
        std_errors = []
        true_value = None  # 如有解析解

        for n in sample_sizes:
            np.random.seed(self.seed)
            x = np.random.uniform(a, b, n)
            values = func(x)
            est = (b - a) * np.mean(values)
            se = (b - a) * np.std(values) / np.sqrt(n)
            estimates.append(est)
            std_errors.append(se)

        # 尝试解析解 (f(x)=x²在[0,1]的积分=1/3)
        if a == 0 and b == 1:
            true_value = 1 / 3

        analysis = {
            'sample_sizes': sample_sizes,
            'estimates': np.array(estimates),
            'std_errors': np.array(std_errors),
            'true_value': true_value
        }

        self.results['convergence'] = analysis
        return analysis

    def estimate_pi(self, n_samples: int = None) -> Dict:
        """
        蒙特卡洛估计π (单位圆面积/正方形面积)
        """
        n = n_samples or self.n_samples
        x = np.random.uniform(-1, 1, n)
        y = np.random.uniform(-1, 1, n)
        inside = x ** 2 + y ** 2 <= 1
        pi_est = 4 * np.mean(inside)
        se = 4 * np.std(inside) / np.sqrt(n)

        result = {
            'estimate': pi_est,
            'std_error': se,
            'ci_95': (pi_est - 1.96 * se, pi_est + 1.96 * se),
            'n_samples': n,
            'x_in': x[inside], 'y_in': y[inside],
            'x_out': x[~inside], 'y_out': y[~inside]
        }

        self.results['pi'] = result
        return result

    def plot_convergence(self, filename: Optional[str] = None):
        """绘制收敛性诊断图"""
        if 'convergence' not in self.results:
            print("请先运行convergence_analysis()")
            return

        data = self.results['convergence']
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # 估计值收敛
        ax1.plot(data['sample_sizes'], data['estimates'], 'b-o', markersize=4)
        if data['true_value'] is not None:
            ax1.axhline(y=data['true_value'], color='r', linestyle='--',
                        label=f'True = {data["true_value"]:.4f}')
        ax1.fill_between(data['sample_sizes'],
                         data['estimates'] - 1.96 * data['std_errors'],
                         data['estimates'] + 1.96 * data['std_errors'],
                         alpha=0.3, color='blue', label='95% CI')
        ax1.set_xscale('log')
        ax1.set_xlabel('Number of Samples')
        ax1.set_ylabel('Estimate')
        ax1.set_title('MC Estimate Convergence')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 标准误差
        ax2.loglog(data['sample_sizes'], data['std_errors'], 'r-o', markersize=4)
        # 理论收敛速率 O(1/√n)
        theory = data['std_errors'][0] * np.sqrt(data['sample_sizes'][0]) / np.sqrt(data['sample_sizes'])
        ax2.loglog(data['sample_sizes'], theory, 'k--', label='O(1/√n)')
        ax2.set_xlabel('Number of Samples')
        ax2.set_ylabel('Standard Error')
        ax2.set_title('Standard Error vs Sample Size')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

    def plot_random_walk(self, filename: Optional[str] = None):
        """绘制随机游走路径"""
        if 'random_walk' not in self.results:
            print("请先运行simulate_random_walk()")
            return

        data = self.results['random_walk']
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # 路径
        for i in range(min(20, len(data['paths']))):
            ax1.plot(data['time'], data['paths'][i], alpha=0.5, linewidth=0.8)
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Price')
        ax1.set_title('Geometric Brownian Motion Paths')
        ax1.grid(True, alpha=0.3)

        # 终值分布
        final = data['paths'][:, -1]
        ax2.hist(final, bins=50, density=True, alpha=0.7, color='steelblue')
        ax2.axvline(x=np.mean(final), color='red', linestyle='--',
                    label=f'Mean={np.mean(final):.2f}')
        ax2.set_xlabel('Final Price')
        ax2.set_ylabel('Density')
        ax2.set_title('Distribution of Final Prices')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()

    def plot_pi_estimation(self, filename: Optional[str] = None):
        """绘制π估计可视化"""
        if 'pi' not in self.results:
            print("请先运行estimate_pi()")
            return

        data = self.results['pi']
        fig, ax = plt.subplots(figsize=(8, 8))

        ax.scatter(data['x_in'], data['y_in'], s=1, c='blue', alpha=0.5, label='Inside')
        ax.scatter(data['x_out'], data['y_out'], s=1, c='red', alpha=0.5, label='Outside')

        # 画单位圆
        theta = np.linspace(0, 2 * np.pi, 100)
        ax.plot(np.cos(theta), np.sin(theta), 'k-', linewidth=2)

        ax.set_aspect('equal')
        ax.set_title(f'MC Estimate of π = {data["estimate"]:.6f} ± {data["std_error"]:.6f}')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()


def run_example():
    """示例: 蒙特卡洛积分估计 + 收敛分析"""
    print("=" * 60)
    print("蒙特卡洛仿真框架示例")
    print("=" * 60)

    mc = MonteCarloSimulator(n_samples=50000, seed=42)

    # 示例1: 定积分 ∫₀¹ x² dx = 1/3
    print("\n--- 示例1: 定积分估计 ---")
    func = lambda x: x ** 2
    true_val = 1 / 3

    for method in ['standard', 'importance', 'antithetic']:
        res = mc.estimate_integral(func, 0, 1, method=method)
        err = abs(res['estimate'] - true_val)
        print(f"\n  {method:12s}: estimate={res['estimate']:.6f}, "
              f"error={err:.6f}, CI={res['ci_95']}")

    # 示例2: 收敛性诊断
    print("\n--- 示例2: 收敛性诊断 ---")
    analysis = mc.convergence_analysis(func, 0, 1)
    print(f"  样本量从 {analysis['sample_sizes'][0]} 到 {analysis['sample_sizes'][-1]}")
    print(f"  最终估计: {analysis['estimates'][-1]:.6f} (true=0.333333)")
    print(f"  最终标准误差: {analysis['std_errors'][-1]:.6f}")

    # 示例3: 随机游走 (GBM)
    print("\n--- 示例3: 几何布朗运动 ---")
    gbm = mc.simulate_random_walk(n_steps=252, n_paths=1000, mu=0.05, sigma=0.2)
    print(f"  初始价格: 100")
    print(f"  终值均值: {gbm['mean']:.2f}")
    print(f"  终值标准差: {gbm['std']:.2f}")
    print(f"  5%分位数: {gbm['percentile_5']:.2f}")
    print(f"  95%分位数: {gbm['percentile_95']:.2f}")
    print(f"  亏损概率: {gbm['prob_loss']:.4f}")

    # 示例4: 估计π
    print("\n--- 示例4: 蒙特卡洛估计π ---")
    pi_res = mc.estimate_pi(n_samples=10000)
    print(f"  估计值: {pi_res['estimate']:.6f}")
    print(f"  真实值: {np.pi:.6f}")
    print(f"  绝对误差: {abs(pi_res['estimate'] - np.pi):.6f}")

    # 绘图
    mc.plot_convergence('figures/mc_convergence.png')
    mc.plot_random_walk('figures/mc_gbm.png')
    mc.plot_pi_estimation('figures/mc_pi.png')
    print("\n图片已保存到 figures/ 目录")


if __name__ == "__main__":
    run_example()
