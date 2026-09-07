#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facebook Prophet时间序列预测模板
功能：数据准备、模型训练、预测、可视化
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 尝试导入prophet，如果未安装则使用模拟版本
try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False
    print("警告: Prophet未安装，使用模拟版本进行演示")
    print("安装命令: pip install prophet")

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class ProphetTimeSeriesPredictor:
    """Prophet时间序列预测器"""
    
    def __init__(self, yearly_seasonality=True, weekly_seasonality=True,
                 daily_seasonality=False, changepoint_prior_scale=0.05,
                 seasonality_prior_scale=10.0):
        """
        初始化Prophet预测器
        参数：
            yearly_seasonality: 是否包含年度季节性
            weekly_seasonality: 是否包含周度季节性
            daily_seasonality: 是否包含日度季节性
            changepoint_prior_scale: 变化点先验尺度
            seasonality_prior_scale: 季节性先验尺度
        """
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
        self.changepoint_prior_scale = changepoint_prior_scale
        self.seasonality_prior_scale = seasonality_prior_scale
        
        self.model = None
        self.forecast = None
        self.history = None
    
    def prepare_data(self, df, date_column='ds', value_column='y'):
        """
        数据准备
        参数：
            df: DataFrame，包含日期和值列
            date_column: 日期列名
            value_column: 值列名
        返回：
            处理后的DataFrame
        """
        # 确保日期格式
        df = df.copy()
        df[date_column] = pd.to_datetime(df[date_column])
        
        # 按日期排序
        df = df.sort_values(date_column).reset_index(drop=True)
        
        # 处理缺失值
        if df[value_column].isna().any():
            print(f"警告: 发现{df[value_column].isna().sum()}个缺失值，使用线性插值填充")
            df[value_column] = df[value_column].interpolate(method='linear')
        
        # 重命名列以符合Prophet要求
        df = df.rename(columns={date_column: 'ds', value_column: 'y'})
        
        self.history = df
        print(f"数据准备完成: {len(df)}条记录")
        print(f"时间范围: {df['ds'].min()} 至 {df['ds'].max()}")
        
        return df
    
    def train(self, df, periods=None, freq='D'):
        """
        训练模型并生成预测
        参数：
            df: 训练数据
            periods: 预测期数（如果为None，则不预测）
            freq: 预测频率
        """
        if not HAS_PROPHET:
            print("使用模拟Prophet进行训练...")
            self._simulate_train(df)
            if periods:
                self._simulate_predict(periods, freq)
            return
        
        # 创建Prophet模型
        self.model = Prophet(
            yearly_seasonality=self.yearly_seasonality,
            weekly_seasonality=self.weekly_seasonality,
            daily_seasonality=self.daily_seasonality,
            changepoint_prior_scale=self.changepoint_prior_scale,
            seasonality_prior_scale=self.seasonality_prior_scale
        )
        
        # 训练模型
        print("训练Prophet模型...")
        self.model.fit(df)
        
        # 如果指定了预测期数，则生成预测
        if periods:
            self.forecast(periods, freq)
        
        print("模型训练完成!")
    
    def forecast(self, periods, freq='D', include_history=True):
        """
        生成预测
        参数：
            periods: 预测期数
            freq: 预测频率
            include_history: 是否包含历史数据
        """
        if not HAS_PROPHET:
            self._simulate_predict(periods, freq)
            return
        
        # 创建未来日期
        future = self.model.make_future_dataframe(
            periods=periods, 
            freq=freq,
            include_history=include_history
        )
        
        # 生成预测
        self.forecast = self.model.predict(future)
        
        print(f"预测完成: {periods}个未来时间点")
        
        return self.forecast
    
    def _simulate_train(self, df):
        """模拟训练过程"""
        self.history = df
        self.model = type('MockProphet', (), {
            'fit': lambda self, df: None,
            'predict': lambda self, future: None
        })()
    
    def _simulate_predict(self, periods, freq):
        """模拟预测过程"""
        if self.history is None:
            print("错误: 请先训练模型")
            return
        
        # 生成模拟预测
        last_date = self.history['ds'].max()
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=periods,
            freq=freq
        )
        
        # 简单线性外推 + 噪声
        last_values = self.history['y'].tail(10).values
        trend = np.polyfit(range(len(last_values)), last_values, 1)[0]
        
        future_values = []
        for i in range(periods):
            future_value = last_values[-1] + trend * (i + 1)
            future_value += np.random.normal(0, np.std(last_values) * 0.1)
            future_values.append(future_value)
        
        self.forecast = pd.DataFrame({
            'ds': future_dates,
            'yhat': future_values,
            'yhat_lower': [v - np.std(last_values) * 0.5 for v in future_values],
            'yhat_upper': [v + np.std(last_values) * 0.5 for v in future_values]
        })
    
    def plot_forecast(self, figsize=(14, 8)):
        """绘制预测结果"""
        if self.forecast is None:
            print("没有预测结果可绘制")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        
        # 1. 主预测图
        if HAS_PROPHET and self.model and hasattr(self.model, 'plot'):
            self.model.plot(self.forecast, ax=axes[0, 0])
        else:
            # 模拟绘图
            if self.history is not None:
                axes[0, 0].plot(self.history['ds'], self.history['y'], 
                              'k.', label='历史数据', alpha=0.5)
            axes[0, 0].plot(self.forecast['ds'], self.forecast['yhat'], 
                          'b-', label='预测值')
            if 'yhat_lower' in self.forecast.columns:
                axes[0, 0].fill_between(
                    self.forecast['ds'],
                    self.forecast['yhat_lower'],
                    self.forecast['yhat_upper'],
                    color='blue', alpha=0.2, label='置信区间'
                )
        
        axes[0, 0].set_title('Prophet预测结果')
        axes[0, 0].set_xlabel('日期')
        axes[0, 0].set_ylabel('值')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 组件分解图
        if HAS_PROPHET and self.model and hasattr(self.model, 'plot_components'):
            self.model.plot_components(self.forecast, ax=axes[0, 1])
        else:
            # 模拟组件图
            axes[0, 1].text(0.5, 0.5, '组件分解图\n(需要安装Prophet)', 
                          ha='center', va='center', transform=axes[0, 1].transAxes)
        
        axes[0, 1].set_title('组件分解')
        
        # 3. 预测分布
        if 'yhat' in self.forecast.columns:
            axes[1, 0].hist(self.forecast['yhat'], bins=30, 
                          edgecolor='black', alpha=0.7, color='steelblue')
            axes[1, 0].axvline(x=self.forecast['yhat'].mean(), color='red', 
                             linestyle='--', linewidth=2, label=f'均值: {self.forecast["yhat"].mean():.2f}')
            axes[1, 0].set_title('预测值分布')
            axes[1, 0].set_xlabel('预测值')
            axes[1, 0].set_ylabel('频数')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
        
        # 4. 预测统计信息
        if self.forecast is not None and 'yhat' in self.forecast.columns:
            stats_text = f"""
预测统计信息:
================
预测期数: {len(self.forecast)}
预测均值: {self.forecast['yhat'].mean():.2f}
预测标准差: {self.forecast['yhat'].std():.2f}
预测最小值: {self.forecast['yhat'].min():.2f}
预测最大值: {self.forecast['yhat'].max():.2f}

置信区间宽度:
"""
            if 'yhat_lower' in self.forecast.columns:
                width = self.forecast['yhat_upper'] - self.forecast['yhat_lower']
                stats_text += f"平均宽度: {width.mean():.2f}\n"
                stats_text += f"最大宽度: {width.max():.2f}\n"
            
            if self.history is not None:
                stats_text += f"\n历史数据统计:\n"
                stats_text += f"数据点数: {len(self.history)}\n"
                stats_text += f"历史均值: {self.history['y'].mean():.2f}\n"
                stats_text += f"历史标准差: {self.history['y'].std():.2f}\n"
            
            axes[1, 1].text(0.1, 0.5, stats_text, transform=axes[1, 1].transAxes,
                           fontsize=10, verticalalignment='center',
                           fontfamily='monospace',
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            axes[1, 1].axis('off')
            axes[1, 1].set_title('预测统计信息')
        
        plt.tight_layout()
        plt.show()
    
    def plot_forecast_detail(self, figsize=(12, 6)):
        """绘制详细的预测图"""
        if self.forecast is None:
            print("没有预测结果可绘制")
            return
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # 绘制历史数据
        if self.history is not None:
            ax.plot(self.history['ds'], self.history['y'], 
                   'k.', label='历史数据', alpha=0.5, markersize=3)
        
        # 绘制预测值
        ax.plot(self.forecast['ds'], self.forecast['yhat'], 
               'b-', label='预测值', linewidth=2)
        
        # 绘制置信区间
        if 'yhat_lower' in self.forecast.columns:
            ax.fill_between(
                self.forecast['ds'],
                self.forecast['yhat_lower'],
                self.forecast['yhat_upper'],
                color='blue', alpha=0.2, label='80%置信区间'
            )
        
        # 标记预测起点
        if self.history is not None:
            last_historical_date = self.history['ds'].max()
            ax.axvline(x=last_historical_date, color='red', 
                      linestyle='--', alpha=0.7, label='预测起点')
        
        ax.set_title('Prophet时间序列预测', fontsize=14)
        ax.set_xlabel('日期', fontsize=12)
        ax.set_ylabel('值', fontsize=12)
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


def generate_sample_data(n_days=365 * 2, trend=0.05, seasonal_period=365):
    """
    生成示例时间序列数据
    参数：
        n_days: 天数
        trend: 趋势斜率
        seasonal_period: 季节性周期
    """
    # 生成日期序列
    start_date = datetime(2020, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(n_days)]
    
    # 生成趋势
    trend_component = np.arange(n_days) * trend
    
    # 生成季节性
    seasonal_component = 10 * np.sin(2 * np.pi * np.arange(n_days) / seasonal_period)
    
    # 生成周度季节性
    weekly_component = 2 * np.sin(2 * np.pi * np.arange(n_days) / 7)
    
    # 生成噪声
    noise = np.random.normal(0, 1, n_days)
    
    # 组合成最终值
    values = 50 + trend_component + seasonal_component + weekly_component + noise
    
    # 创建DataFrame
    df = pd.DataFrame({
        'ds': dates,
        'y': values
    })
    
    return df


def main():
    """主函数 - 演示Prophet时间序列预测"""
    
    print("=" * 60)
    print("Facebook Prophet时间序列预测模板演示")
    print("=" * 60)
    
    # 生成示例数据
    print("\n【生成示例数据】")
    print("-" * 40)
    
    # 生成两年的日度数据
    sample_data = generate_sample_data(n_days=730, trend=0.02)
    print(f"生成了{len(sample_data)}条日度数据")
    print(f"数据预览:\n{sample_data.head()}")
    
    # 创建预测器
    predictor = ProphetTimeSeriesPredictor(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        seasonality_prior_scale=10.0
    )
    
    # 准备数据
    prepared_data = predictor.prepare_data(sample_data, date_column='ds', value_column='y')
    
    # 训练模型并预测未来30天
    print("\n【训练模型并预测】")
    print("-" * 40)
    
    predictor.train(prepared_data, periods=30, freq='D')
    
    # 绘制预测结果
    print("\n【绘制预测结果】")
    print("-" * 40)
    
    predictor.plot_forecast()
    predictor.plot_forecast_detail()
    
    # 示例2: 使用真实场景的数据
    print("\n【示例2: 销售数据预测】")
    print("-" * 40)
    
    # 模拟销售数据
    np.random.seed(42)
    n_weeks = 104  # 2年
    weeks = pd.date_range(start='2020-01-01', periods=n_weeks, freq='W')
    
    # 销售趋势 + 季假日效应
    sales_trend = 1000 + np.arange(n_weeks) * 5
    seasonal = 200 * np.sin(2 * np.pi * np.arange(n_weeks) / 52)
    holiday_effect = np.where(
        (np.arange(n_weeks) % 52 >= 48) | (np.arange(n_weeks) % 52 <= 2),
        300, 0  # 年末年初促销
    )
    noise = np.random.normal(0, 50, n_weeks)
    
    sales_values = sales_trend + seasonal + holiday_effect + noise
    
    sales_df = pd.DataFrame({
        'ds': weeks,
        'y': sales_values
    })
    
    # 创建销售预测器
    sales_predictor = ProphetTimeSeriesPredictor(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05
    )
    
    # 准备数据
    sales_data = sales_predictor.prepare_data(sales_df)
    
    # 训练并预测未来12周
    sales_predictor.train(sales_data, periods=12, freq='W')
    
    # 绘制结果
    sales_predictor.plot_forecast()
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("=" * 60)
    print("\n提示: 安装Prophet以获得完整功能:")
    print("  pip install prophet")
    print("或")
    print("  conda install -c conda-forge prophet")


if __name__ == "__main__":
    main()
