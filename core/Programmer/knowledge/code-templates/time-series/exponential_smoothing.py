"""
模板来源: resources/code-templates/time-series/exponential_smoothing.py
修改说明: 
  - 新增指数平滑时间序列预测模板
  - 支持单参数/双参数/三参数指数平滑
"""
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt, ExponentialSmoothing
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


class ExponentialSmoothingForecaster:
    """指数平滑时间序列预测模型"""
    
    def __init__(self, model_type='simple', seasonal_periods=None):
        """
        model_type: 'simple', 'holt', 'holt_winters'
        seasonal_periods: 季节周期（仅Holt-Winters需要）
        """
        self.model_type = model_type
        self.seasonal_periods = seasonal_periods
        self.model = None
        self.results = None
    
    def fit(self, train_data, alpha=None, beta=None, gamma=None):
        """拟合模型"""
        if self.model_type == 'simple':
            self.model = SimpleExpSmoothing(train_data)
            self.results = self.model.fit(smoothing_level=alpha)
        
        elif self.model_type == 'holt':
            self.model = Holt(train_data)
            self.results = self.model.fit(
                smoothing_level=alpha, 
                smoothing_trend=beta
            )
        
        elif self.model_type == 'holt_winters':
            self.model = ExponentialSmoothing(
                train_data,
                trend='add',
                seasonal='add',
                seasonal_periods=self.seasonal_periods
            )
            self.results = self.model.fit(
                smoothing_level=alpha,
                smoothing_trend=beta,
                smoothing_seasonal=gamma
            )
        
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
    
    def optimize_params(self, train_data, val_data):
        """参数优化"""
        best_score = float('inf')
        best_params = None
        
        alpha_range = np.arange(0.1, 1.0, 0.1)
        beta_range = np.arange(0.01, 0.5, 0.05)
        gamma_range = np.arange(0.01, 0.5, 0.05)
        
        for alpha in alpha_range:
            for beta in beta_range:
                try:
                    if self.model_type == 'simple':
                        self.fit(train_data, alpha=alpha)
                    elif self.model_type == 'holt':
                        self.fit(train_data, alpha=alpha, beta=beta)
                    elif self.model_type == 'holt_winters':
                        for gamma in gamma_range:
                            self.fit(train_data, alpha=alpha, beta=beta, gamma=gamma)
                            pred = self.predict(steps=len(val_data))
                            score = mean_squared_error(val_data, pred)
                            if score < best_score:
                                best_score = score
                                best_params = (alpha, beta, gamma)
                    else:
                        continue
                    
                    if self.model_type != 'holt_winters':
                        pred = self.predict(steps=len(val_data))
                        score = mean_squared_error(val_data, pred)
                        if score < best_score:
                            best_score = score
                            best_params = (alpha, beta)
                
                except:
                    continue
        
        print(f"最优参数: {best_params}, MSE: {best_score:.4f}")
        return best_params
    
    def plot_forecast(self, train_data, test_data, predictions, 
                     filename='figures/exp_smoothing_forecast.png'):
        """绘制预测结果"""
        plt.figure(figsize=(12, 6))
        
        plt.plot(train_data.index, train_data, label='训练集', color='blue')
        plt.plot(test_data.index, test_data, label='测试集', color='green')
        plt.plot(test_data.index, predictions, label='预测值', color='red', linestyle='--')
        
        plt.xlabel('时间')
        plt.ylabel('值')
        plt.title(f'{self.model_type}预测结果')
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
    trend = 0.3 * t
    seasonal = 8 * np.sin(2 * np.pi * t / 12)
    noise = np.random.normal(0, 1.5, n)
    data = 50 + trend + seasonal + noise
    
    series = pd.Series(data, index=pd.date_range('2020-01-01', periods=n, freq='M'))
    
    # 划分训练集和测试集
    train = series[:80]
    test = series[80:]
    
    # 测试不同模型
    for model_type in ['simple', 'holt', 'holt_winters']:
        print(f"\n{'='*50}")
        print(f"模型类型: {model_type}")
        print('='*50)
        
        forecaster = ExponentialSmoothingForecaster(
            model_type=model_type,
            seasonal_periods=12 if model_type == 'holt_winters' else None
        )
        
        forecaster.fit(train)
        predictions = forecaster.predict(steps=len(test))
        forecaster.evaluate(test, predictions)
        forecaster.plot_forecast(train, test, predictions, 
                                f'figures/{model_type}_forecast.png')
