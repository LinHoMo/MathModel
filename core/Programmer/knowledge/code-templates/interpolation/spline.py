"""
模板来源: resources/code-templates/interpolation/spline.py
修改说明: 
  - 新增样条插值模板
  - 支持三次样条、B样条
"""
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline, BSpline, make_interp_spline


class SplineInterpolation:
    """样条插值"""
    
    def __init__(self, x_data, y_data):
        self.x = np.array(x_data, dtype=float)
        self.y = np.array(y_data, dtype=float)
    
    def natural_cubic_spline(self, x_eval=None):
        """自然三次样条插值"""
        cs = CubicSpline(self.x, self.y, bc_type='natural')
        
        if x_eval is None:
            x_eval = np.linspace(self.x[0], self.x[-1], 100)
        
        y_eval = cs(x_eval)
        return x_eval, y_eval, cs
    
    def clamped_cubic_spline(self, fp_start, fp_end, x_eval=None):
        """固定边界三次样条插值"""
        cs = CubicSpline(self.x, self.y, bc_type=((1, fp_start), (1, fp_end)))
        
        if x_eval is None:
            x_eval = np.linspace(self.x[0], self.x[-1], 100)
        
        y_eval = cs(x_eval)
        return x_eval, y_eval, cs
    
    def bspline(self, k=3, x_eval=None):
        """B样条插值"""
        # 需要至少k+1个数据点
        if len(self.x) < k + 1:
            raise ValueError(f"B样条需要至少{k+1}个数据点")
        
        spl = make_interp_spline(self.x, self.y, k=k)
        
        if x_eval is None:
            x_eval = np.linspace(self.x[0], self.x[-1], 100)
        
        y_eval = spl(x_eval)
        return x_eval, y_eval, spl
    
    def derivative(self, cs, x_eval, order=1):
        """计算导数"""
        return cs(x_eval, order)
    
    def integral(self, cs, a, b):
        """计算积分"""
        return cs.integrate(a, b)
    
    def plot_comparison(self, filename='figures/spline_comparison.png'):
        """比较不同样条方法"""
        x_plot = np.linspace(self.x[0], self.x[-1], 100)
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 原始数据
        axes[0, 0].plot(self.x, self.y, 'ro', label='数据点')
        axes[0, 0].set_title('原始数据')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 自然三次样条
        x_nat, y_nat, _ = self.natural_cubic_spline(x_plot)
        axes[0, 1].plot(self.x, self.y, 'ro', label='数据点')
        axes[0, 1].plot(x_nat, y_nat, 'b-', label='自然三次样条')
        axes[0, 1].set_title('自然三次样条')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 三次样条导数
        _, _, cs = self.natural_cubic_spline(x_plot)
        dy = cs(x_plot, 1)
        axes[1, 0].plot(x_plot, dy, 'g-', label="一阶导数")
        axes[1, 0].set_title('导数')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 三次样条积分
        x_int = np.linspace(self.x[0], self.x[-1], 50)
        y_int = [self.integral(cs, self.x[0], x) for x in x_int]
        axes[1, 1].plot(x_int, y_int, 'm-', label='积分')
        axes[1, 1].set_title('积分')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"比较图已保存: {filename}")


if __name__ == "__main__":
    # 示例：数据插值
    print("样条插值示例\n")
    
    # 生成数据点
    x_data = np.array([0, 1, 2, 3, 4, 5])
    y_data = np.array([0, 1, 4, 9, 16, 25])
    
    # 创建插值器
    spline = SplineInterpolation(x_data, y_data)
    
    # 测试点
    x_test = 2.5
    
    # 自然三次样条
    x_nat, y_nat, cs_nat = spline.natural_cubic_spline()
    print(f"自然三次样条在x={x_test}处的值: {cs_nat(x_test):.4f}")
    print(f"一阶导数: {spline.derivative(cs_nat, x_test, 1):.4f}")
    print(f"二阶导数: {spline.derivative(cs_nat, x_test, 2):.4f}")
    
    # 积分
    print(f"从0到5的积分: {spline.integral(cs_nat, 0, 5):.4f}")
    
    # 绘制比较图
    spline.plot_comparison()
