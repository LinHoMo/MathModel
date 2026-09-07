"""
模板来源: resources/code-templates/time-series/arima_model.py
修改说明: 
  - 新增ARIMA时间序列预测模板
  - 支持自动定阶、模型诊断、预测评估
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


class ARIMAForecaster:
    """ARIMA时间序列预测模型"""
    
    def __init__(self, order=(1, 1, 1)):
        self.order = order
        self.model = None
        self.results = None
        self.fitted_values = None
    
    def check_stationarity(self, series):
        """ADF平稳性检验"""
        result = adfuller(series)
        print(f'ADF统计量: {result[0]:.4f}')
        print(f'p值: {result[1]:.4f}')
        print('临界值:')
        for key, value in result[4].items():
            print(f'  {key}: {value:.4f}')
        
        is_stationary = result[1] < 0.05
        print(f'结论: {"平稳" if is_stationary else "非平稳，需要差分"}')
        return is_stationary
    
    def difference(self, series, d=1):
        """差分处理"""
        diff = series.copy()
        for _ in range(d):
            diff = diff.diff().dropna()
        return diff
    
    def auto_order(self, series, max_p=5, max_d=2, max_q=5):
        """自动定阶（基于AIC）"""
        best_aic = float('inf')
        best_order = (1, 1, 1)
        
        for p in range(max_p + 1):
            for d in range(max_d + 1):
                for q in range(max_q + 1):
                    try:
                        model = ARIMA(series, order=(p, d, q))
                        results = model.fit()
                        if results.aic < best_aic:
                            best_aic = results.aic
                            best_order = (p, d, q)
                    except:
                        continue
        
        self.order = best_order
        print(f"最优阶数: ARIMA{best_order}, AIC={best_aic:.2f}")
        return best_order
    
    def fit(self, train_data):
        """拟合模型"""
        self.model = ARIMA(train_data, order=self.order)
        self.results = self.model.fit()
        self.fitted_values = self.results.fittedvalues
        return self.results
    
    def predict(self, steps=10):
        """预测"""
        forecast = self.results.forecast(steps=steps)
        return forecast
    
    def evaluate(self, test_data, predictions):
        """评估预测精度"""
        mse = mean_squared_error(test_data, predictions)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(test_data, predictions)
        mape = np.mean(np.abs((test_data - predictions) / test_data)) * 100
        
        metrics = {
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'MAPE': mape
        }
        
        print("预测评估指标:")
        for name, value in metrics.items():
            print(f"  {name}: {value:.4f}")
        
        return metrics
    
    def plot_diagnostics(self, filename='figures/arima_diagnostics.png'):
        """模型诊断图"""
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        # 残差图
        residuals = self.results.resid
        axes[0, 0].plot(residuals)
        axes[0, 0].set_title('残差')
        axes[0, 0].set_xlabel('时间')
        
        # 残差直方图
        axes[0, 1].hist(residuals, bins=20, edgecolor='black')
        axes[0, 1].set_title('残差分布')
        
        # ACF
        plot_acf(residuals, lags=20, ax=axes[1, 0])
        axes[1, 0].set_title('残差ACF')
        
        # PACF
        plot_pacf(residuals, lags=20, ax=axes[1, 1])
        axes[1, 1].set_title('残差PACF')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"诊断图已保存: {filename}")
    
    def plot_forecast(self, train_data, test_data, predictions, 
                     filename='figures/arima_forecast.png'):
        """绘制预测结果"""
        plt.figure(figsize=(12, 6))
        
        plt.plot(train_data.index, train_data, label='训练集', color='blue')
        plt.plot(test_data.index, test_data, label='测试集', color='green')
        plt.plot(test_data.index, predictions, label='预测值', color='red', linestyle='--')
        
        plt.xlabel('时间')
        plt.ylabel('值')
        plt.title('ARIMA预测结果')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"预测图已保存: {filename}")


if __name__ == "__main__":
    # 示例：生成模拟数据
    np.random.seed(42)
    n = 100
    t = np.arange(n)
    trend = 0.5 * t
    seasonal = 10 * np.sin(2 * np.pi * t / 12)
    noise = np.random.normal(0, 2, n)
    data = 50 + trend + seasonal + noise
    
    series = pd.Series(data, index=pd.date_range('2020-01-01', periods=n, freq='M'))
    
    # 划分训练集和测试集
    train = series[:80]
    test = series[80:]
    
    # 创建预测器
    forecaster = ARIMAForecaster()
    
    # 检验平稳性
    forecaster.check_stationarity(train)
    
    # 自动定阶
    forecaster.auto_order(train)
    
    # 拟合
    forecaster.fit(train)
    
    # 预测
    predictions = forecaster.predict(steps=len(test))
    
    # 评估
    forecaster.evaluate(test, predictions)
    
    # 可视化
    forecaster.plot_diagnostics()
    forecaster.plot_forecast(train, test, predictions)
