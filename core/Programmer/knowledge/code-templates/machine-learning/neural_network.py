"""
神经网络模板
来源: 高教杯优秀论文通用方法
适用问题: 分类、回归、特征学习
输入: 训练数据、网络配置
输出: 训练好的模型、预测结果、评估指标
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple, List, Dict
import warnings
warnings.filterwarnings('ignore')


class NeuralNetwork:
    """
    多层感知机神经网络（从零实现）
    
    Parameters
    ----------
    layer_dims : list
        各层神经元数量，如 [10, 64, 32, 1]
    learning_rate : float
        学习率
    activation : str
        激活函数: 'relu', 'sigmoid', 'tanh'
    epochs : int
        训练轮数
    batch_size : int
        批大小
    """
    
    def __init__(
        self,
        layer_dims: List[int],
        learning_rate: float = 0.01,
        activation: str = 'relu',
        epochs: int = 100,
        batch_size: int = 32
    ):
        self.layer_dims = layer_dims
        self.learning_rate = learning_rate
        self.activation = activation
        self.epochs = epochs
        self.batch_size = batch_size
        
        self.parameters = {}
        self.costs = []
    
    def _initialize_parameters(self):
        """初始化参数（He初始化）"""
        np.random.seed(42)
        L = len(self.layer_dims)
        
        for l in range(1, L):
            # He初始化: sqrt(2/n_l-1)
            self.parameters[f'W{l}'] = np.random.randn(
                self.layer_dims[l-1], self.layer_dims[l]
            ) * np.sqrt(2.0 / self.layer_dims[l-1])
            self.parameters[f'b{l}'] = np.zeros((1, self.layer_dims[l]))
    
    def _relu(self, Z):
        """ReLU激活函数"""
        return np.maximum(0, Z)
    
    def _relu_backward(self, dA, Z):
        """ReLU反向传播"""
        dZ = np.array(dA, copy=True)
        dZ[Z <= 0] = 0
        return dZ
    
    def _sigmoid(self, Z):
        """Sigmoid激活函数"""
        return 1 / (1 + np.exp(-np.clip(Z, -500, 500)))
    
    def _sigmoid_backward(self, dA, Z):
        """Sigmoid反向传播"""
        s = self._sigmoid(Z)
        return dA * s * (1 - s)
    
    def _tanh(self, Z):
        """Tanh激活函数"""
        return np.tanh(Z)
    
    def _tanh_backward(self, dA, Z):
        """Tanh反向传播"""
        t = np.tanh(Z)
        return dA * (1 - t ** 2)
    
    def _linear_forward(self, A, W, b):
        """线性前向传播"""
        Z = np.dot(A, W) + b
        return Z, (A, W, b)
    
    def _activation_forward(self, A_prev, W, b, activation):
        """激活前向传播"""
        Z, linear_cache = self._linear_forward(A_prev, W, b)
        
        if activation == 'relu':
            A = self._relu(Z)
        elif activation == 'sigmoid':
            A = self._sigmoid(Z)
        elif activation == 'tanh':
            A = self._tanh(Z)
        else:
            raise ValueError(f"Unknown activation: {activation}")
        
        return A, (linear_cache, Z)
    
    def _forward(self, X):
        """完整前向传播"""
        caches = []
        A = X
        L = len(self.layer_dims)
        
        for l in range(1, L-1):
            A, cache = self._activation_forward(
                A, self.parameters[f'W{l}'], self.parameters[f'b{l}'], self.activation
            )
            caches.append(cache)
        
        # 输出层（线性输出）
        AL, cache = self._linear_forward(
            A, self.parameters[f'W{L-1}'], self.parameters[f'b{L-1}']
        )
        caches.append(cache)
        
        return AL, caches
    
    def _compute_cost(self, AL, Y):
        """计算损失（MSE）"""
        m = Y.shape[0]
        cost = np.mean((AL - Y) ** 2)
        return cost
    
    def _linear_backward(self, dZ, cache):
        """线性反向传播"""
        A_prev, W, b = cache
        m = A_prev.shape[0]
        
        dW = np.dot(A_prev.T, dZ) / m
        db = np.sum(dZ, axis=0, keepdims=True) / m
        dA_prev = np.dot(dZ, W.T)
        
        return dA_prev, dW, db
    
    def _activation_backward(self, dA, cache, activation):
        """激活反向传播"""
        linear_cache, Z = cache
        
        if activation == 'relu':
            dZ = self._relu_backward(dA, Z)
        elif activation == 'sigmoid':
            dZ = self._sigmoid_backward(dA, Z)
        elif activation == 'tanh':
            dZ = self._tanh_backward(dA, Z)
        else:
            raise ValueError(f"Unknown activation: {activation}")
        
        return self._linear_backward(dZ, linear_cache)
    
    def _backward(self, AL, Y, caches):
        """完整反向传播"""
        grads = {}
        L = len(caches)
        m = AL.shape[0]
        
        # 输出层梯度
        dAL = 2 * (AL - Y) / m
        
        # 输出层反向传播
        current_cache = caches[L-1]
        grads[f'dA{L-1}'], grads[f'dW{L}'], grads[f'db{L}'] = \
            self._linear_backward(dAL, current_cache)
        
        # 隐藏层反向传播
        for l in range(L-1, 0, -1):
            current_cache = caches[l-1]
            grads[f'dA{l-1}'], grads[f'dW{l}'], grads[f'db{l}'] = \
                self._activation_backward(grads[f'dA{l}'], current_cache, self.activation)
        
        return grads
    
    def _update_parameters(self, grads):
        """更新参数"""
        L = len(self.layer_dims)
        
        for l in range(1, L):
            self.parameters[f'W{l}'] -= self.learning_rate * grads[f'dW{l}']
            self.parameters[f'b{l}'] -= self.learning_rate * grads[f'db{l}']
    
    def fit(self, X: np.ndarray, y: np.ndarray, verbose: bool = True):
        """
        训练模型
        
        Parameters
        ----------
        X : ndarray
            训练数据 (n_samples, n_features)
        y : ndarray
            目标值 (n_samples, 1)
        verbose : bool
            是否打印训练过程
        """
        self._initialize_parameters()
        
        for epoch in range(self.epochs):
            # 前向传播
            AL, caches = self._forward(X)
            
            # 计算损失
            cost = self._compute_cost(AL, y)
            self.costs.append(cost)
            
            # 反向传播
            grads = self._backward(AL, y, caches)
            
            # 更新参数
            self._update_parameters(grads)
            
            if verbose and (epoch + 1) % 50 == 0:
                print(f"Epoch {epoch+1}/{self.epochs}, Cost: {cost:.6f}")
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """预测"""
        AL, _ = self._forward(X)
        return AL
    
    def plot_cost(self, figsize: Tuple[int, int] = (8, 5)):
        """绘制损失曲线"""
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(self.costs, 'b-', linewidth=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Cost')
        ax.set_title('Training Cost')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig


def run_example():
    """
    示例：房价预测神经网络
    """
    from sklearn.datasets import make_regression
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    
    # 生成示例数据
    np.random.seed(42)
    X, y = make_regression(n_samples=500, n_features=10, noise=0.1, random_state=42)
    y = y.reshape(-1, 1)
    
    # 划分数据
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 标准化
    scaler_X = StandardScaler()
    X_train = scaler_X.fit_transform(X_train)
    X_test = scaler_X.transform(X_test)
    
    scaler_y = StandardScaler()
    y_train = scaler_y.fit_transform(y_train)
    y_test_scaled = scaler_y.transform(y_test)
    
    print("=" * 60)
    print("神经网络示例 - 房价预测")
    print("=" * 60)
    
    # 创建并训练模型
    nn = NeuralNetwork(
        layer_dims=[10, 64, 32, 1],
        learning_rate=0.01,
        activation='relu',
        epochs=200,
        batch_size=32
    )
    
    nn.fit(X_train, y_train, verbose=True)
    
    # 预测
    y_pred_scaled = nn.predict(X_test)
    y_pred = scaler_y.inverse_transform(y_pred_scaled)
    y_test_original = scaler_y.inverse_transform(y_test_scaled)
    
    # 评估
    mse = np.mean((y_pred - y_test_original) ** 2)
    rmse = np.sqrt(mse)
    r2 = 1 - np.sum((y_test_original - y_pred) ** 2) / np.sum((y_test_original - np.mean(y_test_original)) ** 2)
    
    print(f"\n测试集 MSE: {mse:.4f}")
    print(f"测试集 RMSE: {rmse:.4f}")
    print(f"测试集 R²: {r2:.4f}")
    
    # 绘制损失曲线
    fig = nn.plot_cost()
    plt.savefig('figures/nn_cost.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # 绘制预测对比
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(y_test_original, y_pred, alpha=0.5)
    ax.plot([y_test_original.min(), y_test_original.max()], 
            [y_test_original.min(), y_test_original.max()], 
            'r--', lw=2, label='Perfect Prediction')
    ax.set_xlabel('Actual')
    ax.set_ylabel('Predicted')
    ax.set_title('Neural Network: Actual vs Predicted')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('figures/nn_prediction.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
