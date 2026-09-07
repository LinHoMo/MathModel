"""
LSTM时间序列模板
来源: 高教杯优秀论文通用方法
适用问题: 长序列预测、复杂时序模式学习
输入: 时间序列数据、网络配置
输出: 训练好的LSTM模型、预测结果
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple, List, Dict
import warnings
warnings.filterwarnings('ignore')


class LSTMCell:
    """
    LSTM单元
    """
    
    def __init__(self, input_size: int, hidden_size: int):
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # 权重初始化
        scale = np.sqrt(2.0 / (input_size + hidden_size))
        
        # 遗忘门
        self.Wf = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.bf = np.zeros((hidden_size, 1))
        
        # 输入门
        self.Wi = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.bi = np.zeros((hidden_size, 1))
        
        # 候选记忆
        self.Wc = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.bc = np.zeros((hidden_size, 1))
        
        # 输出门
        self.Wo = np.random.randn(hidden_size, input_size + hidden_size) * scale
        self.bo = np.zeros((hidden_size, 1))
        
        # 梯度
        self.dWf = np.zeros_like(self.Wf)
        self.dbf = np.zeros_like(self.bf)
        self.dWi = np.zeros_like(self.Wi)
        self.dbi = np.zeros_like(self.bi)
        self.dWc = np.zeros_like(self.Wc)
        self.dbc = np.zeros_like(self.bc)
        self.dWo = np.zeros_like(self.Wo)
        self.dbo = np.zeros_like(self.bo)
    
    def sigmoid(self, x):
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def tanh(self, x):
        return np.tanh(x)
    
    def forward(self, x, h_prev, c_prev):
        """前向传播"""
        # 拼接输入和上一个隐藏状态
        concat = np.vstack([h_prev, x])
        
        # 遗忘门
        f = self.sigmoid(np.dot(self.Wf, concat) + self.bf)
        
        # 输入门
        i = self.sigmoid(np.dot(self.Wi, concat) + self.bi)
        
        # 候选记忆
        c_tilde = self.tanh(np.dot(self.Wc, concat) + self.bc)
        
        # 更新记忆
        c = f * c_prev + i * c_tilde
        
        # 输出门
        o = self.sigmoid(np.dot(self.Wo, concat) + self.bo)
        
        # 隐藏状态
        h = o * self.tanh(c)
        
        # 保存中间值用于反向传播
        self.cache = (concat, f, i, c_tilde, c, o, h, c_prev)
        
        return h, c
    
    def backward(self, dh, dc):
        """反向传播"""
        concat, f, i, c_tilde, c, o, h, c_prev = self.cache
        
        # 输出门梯度
        do = dh * self.tanh(c)
        self.dWo += np.dot(do, concat.T)
        self.dbo += do
        
        # 记忆梯度
        dc_total = dc + dh * o * (1 - self.tanh(c) ** 2)
        
        # 候选记忆梯度
        dc_tilde = dc_total * i
        self.dWc += np.dot(dc_tilde, concat.T)
        self.dbc += dc_tilde
        
        # 输入门梯度
        di = dc_total * c_tilde
        self.dWi += np.dot(di, concat.T)
        self.dbi += di
        
        # 遗忘门梯度
        df = dc_total * c_prev
        self.dWf += np.dot(df, concat.T)
        self.dbf += df
        
        # 传播到上一个时间步
        dc_prev = dc_total * f
        
        # 传播到输入
        dconcat = (np.dot(self.Wf.T, df) + np.dot(self.Wi.T, di) + 
                  np.dot(self.Wc.T, dc_tilde) + np.dot(self.Wo.T, do))
        
        dh_prev = dconcat[:self.hidden_size, :]
        dx = dconcat[self.hidden_size:, :]
        
        return dx, dh_prev, dc_prev


class LSTM:
    """
    LSTM网络
    
    Parameters
    ----------
    input_size : int
        输入特征数
    hidden_size : int
        隐藏层大小
    output_size : int
        输出大小
    learning_rate : float
        学习率
    """
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        output_size: int,
        learning_rate: float = 0.01
    ):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate
        
        # LSTM单元
        self.lstm = LSTMCell(input_size, hidden_size)
        
        # 输出层
        scale = np.sqrt(2.0 / (hidden_size + output_size))
        self.Wy = np.random.randn(output_size, hidden_size) * scale
        self.by = np.zeros((output_size, 1))
        
        self.costs = []
    
    def forward(self, X_sequence: List[np.ndarray]):
        """
        前向传播（整个序列）
        
        Parameters
        ----------
        X_sequence : list
            输入序列 [x1, x2, ..., xT]
        
        Returns
        -------
        outputs : list
            输出序列
        """
        h = np.zeros((self.hidden_size, 1))
        c = np.zeros((self.hidden_size, 1))
        
        self.hiddens = [(h, c)]
        outputs = []
        
        for x in X_sequence:
            h, c = self.lstm.forward(x, h, c)
            self.hiddens.append((h, c))
            
            # 输出
            y = np.dot(self.Wy, h) + self.by
            outputs.append(y)
        
        return outputs
    
    def compute_loss(self, outputs, targets):
        """计算损失（MSE）"""
        loss = 0
        for y, t in zip(outputs, targets):
            loss += np.mean((y - t) ** 2)
        return loss / len(outputs)
    
    def backward(self, outputs, targets):
        """反向传播"""
        # 输出层梯度
        dWy = np.zeros_like(self.Wy)
        dby = np.zeros_like(self.by)
        
        dh = np.zeros((self.hidden_size, 1))
        dc = np.zeros((self.hidden_size, 1))
        
        for t in range(len(outputs) - 1, -1, -1):
            # 输出层梯度
            dy = 2 * (outputs[t] - targets[t]) / len(outputs)
            dWy += np.dot(dy, self.hiddens[t+1][0].T)
            dby += dy
            
            # LSTM梯度
            dh += np.dot(self.Wy.T, dy)
            
            # 时间反向传播
            dx, dh, dc = self.lstm.backward(dh, dc)
        
        # 更新输出层参数
        self.Wy -= self.learning_rate * dWy
        self.by -= self.learning_rate * dby
        
        # 更新LSTM参数（裁剪梯度）
        self._clip_gradients()
        
        self.lstm.Wf -= self.learning_rate * self.lstm.dWf
        self.lstm.bf -= self.learning_rate * self.lstm.dbf
        self.lstm.Wi -= self.learning_rate * self.lstm.dWi
        self.lstm.bi -= self.learning_rate * self.lstm.dbi
        self.lstm.Wc -= self.learning_rate * self.lstm.dWc
        self.lstm.bc -= self.learning_rate * self.lstm.dbc
        self.lstm.Wo -= self.learning_rate * self.lstm.dWo
        self.lstm.bo -= self.learning_rate * self.lstm.dbo
        
        # 重置梯度
        self.lstm.dWf = np.zeros_like(self.lstm.Wf)
        self.lstm.dbf = np.zeros_like(self.lstm.bf)
        self.lstm.dWi = np.zeros_like(self.lstm.Wi)
        self.lstm.dbi = np.zeros_like(self.lstm.bi)
        self.lstm.dWc = np.zeros_like(self.lstm.Wc)
        self.lstm.dbc = np.zeros_like(self.lstm.bc)
        self.lstm.dWo = np.zeros_like(self.lstm.Wo)
        self.lstm.dbo = np.zeros_like(self.lstm.bo)
    
    def _clip_gradients(self, max_norm: float = 5.0):
        """梯度裁剪"""
        for attr in ['dWf', 'dWi', 'dWc', 'dWo']:
            grad = getattr(self.lstm, attr)
            norm = np.linalg.norm(grad)
            if norm > max_norm:
                setattr(self.lstm, attr, grad * max_norm / norm)
    
    def fit(self, X_sequences: List[List[np.ndarray]], 
            y_sequences: List[List[np.ndarray]],
            epochs: int = 100, verbose: bool = True):
        """
        训练模型
        
        Parameters
        ----------
        X_sequences : list
            输入序列列表
        y_sequences : list
            目标序列列表
        epochs : int
            训练轮数
        verbose : bool
            是否打印
        """
        for epoch in range(epochs):
            total_loss = 0
            
            for X_seq, y_seq in zip(X_sequences, y_sequences):
                # 前向传播
                outputs = self.forward(X_seq)
                
                # 计算损失
                loss = self.compute_loss(outputs, y_seq)
                total_loss += loss
                
                # 反向传播
                self.backward(outputs, y_seq)
            
            avg_loss = total_loss / len(X_sequences)
            self.costs.append(avg_loss)
            
            if verbose and (epoch + 1) % 20 == 0:
                print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")
        
        return self
    
    def predict_sequence(self, X_sequence: List[np.ndarray]) -> List[np.ndarray]:
        """预测序列"""
        return self.forward(X_sequence)
    
    def plot_cost(self, figsize: Tuple[int, int] = (8, 5)):
        """绘制损失曲线"""
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(self.costs, 'b-', linewidth=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Loss')
        ax.set_title('Training Loss')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig


def create_sequences(data: np.ndarray, seq_length: int, pred_length: int = 1):
    """
    创建序列数据
    
    Parameters
    ----------
    data : ndarray
        时间序列数据
    seq_length : int
        输入序列长度
    pred_length : int
        预测序列长度
    
    Returns
    -------
    X : list
        输入序列
    y : list
        目标序列
    """
    X, y = [], []
    for i in range(len(data) - seq_length - pred_length + 1):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length:i+seq_length+pred_length])
    return X, y


def run_example():
    """
    示例：电力负荷预测
    """
    # 生成模拟时间序列
    np.random.seed(42)
    n = 500
    t = np.arange(n)
    
    # 趋势 + 季节性 + 周期性
    trend = 0.02 * t
    daily = 5 * np.sin(2 * np.pi * t / 24)  # 日周期
    weekly = 2 * np.sin(2 * np.pi * t / 168)  # 周周期
    noise = np.random.randn(n) * 0.3
    series = 50 + trend + daily + weekly + noise
    
    # 标准化
    mean = np.mean(series)
    std = np.std(series)
    series_norm = (series - mean) / std
    
    # 创建序列数据
    seq_length = 24
    pred_length = 1
    X, y = create_sequences(series_norm, seq_length, pred_length)
    
    # 转换为LSTM输入格式
    X_seq = [x.reshape(-1, 1) for x in X]
    y_seq = [yy.reshape(-1, 1) for yy in y]
    
    # 划分训练集和测试集
    train_size = int(0.8 * len(X_seq))
    X_train, X_test = X_seq[:train_size], X_seq[train_size:]
    y_train, y_test = y_seq[:train_size], y_seq[train_size:]
    
    print("=" * 60)
    print("LSTM时间序列示例 - 电力负荷预测")
    print("=" * 60)
    
    # 创建并训练模型
    lstm = LSTM(
        input_size=1,
        hidden_size=32,
        output_size=1,
        learning_rate=0.005
    )
    
    lstm.fit(X_train, y_train, epochs=100, verbose=True)
    
    # 预测
    y_pred = lstm.predict_sequence(X_test)
    
    # 反标准化
    y_test_orig = [yy * std + mean for yy in y_test]
    y_pred_orig = [yy * std + mean for yy in y_pred]
    
    # 评估
    y_test_arr = np.array([yy.flatten() for yy in y_test_orig])
    y_pred_arr = np.array([yy.flatten() for yy in y_pred_orig])
    
    mse = np.mean((y_test_arr - y_pred_arr) ** 2)
    rmse = np.sqrt(mse)
    mape = np.mean(np.abs((y_test_arr - y_pred_arr) / y_test_arr)) * 100
    
    print(f"\n预测评估:")
    print(f"MSE: {mse:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"MAPE: {mape:.2f}%")
    
    # 绘图
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # 预测对比
    axes[0].plot(y_test_arr.flatten(), 'g-', label='Actual', alpha=0.7)
    axes[0].plot(y_pred_arr.flatten(), 'r--', label='Predicted', alpha=0.7)
    axes[0].set_xlabel('Sample')
    axes[0].set_ylabel('Load (kW)')
    axes[0].set_title('LSTM: Actual vs Predicted')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 损失曲线
    axes[1].plot(lstm.costs, 'b-', linewidth=2)
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Loss')
    axes[1].set_title('Training Loss')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figures/lstm_forecast.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
