"""
PyTorch深度学习模板
来源: 高教杯论文深度学习应用
适用问题: 分类、回归、序列建模
输入: 训练数据
输出: 训练好的模型、预测结果
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from typing import Optional, Tuple, List
import matplotlib.pyplot as plt


class NeuralNetworkTemplate(nn.Module):
    """
    神经网络模板
    
    Parameters
    ----------
    input_size : int
        输入特征数
    hidden_sizes : list
        隐藏层大小
    output_size : int
        输出大小
    dropout : float
        Dropout率
    """
    
    def __init__(self, input_size: int, hidden_sizes: List[int], 
                 output_size: int, dropout: float = 0.2):
        super().__init__()
        
        layers = []
        prev_size = input_size
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.BatchNorm1d(hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_size = hidden_size
        
        layers.append(nn.Linear(prev_size, output_size))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)


class LSTMModel(nn.Module):
    """
    LSTM模型模板
    """
    
    def __init__(self, input_size: int, hidden_size: int, 
                 num_layers: int, output_size: int, dropout: float = 0.2):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        # LSTM
        lstm_out, _ = self.lstm(x)
        
        # 全连接层
        out = self.fc(lstm_out[:, -1, :])
        
        return out


class Trainer:
    """
    模型训练器
    """
    
    def __init__(self, model: nn.Module, learning_rate: float = 0.001):
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = None
        self.train_losses = []
        self.val_losses = []
    
    def fit(self, train_loader: DataLoader, val_loader: Optional[DataLoader] = None,
            epochs: int = 100, task: str = 'regression'):
        """
        训练模型
        
        Parameters
        ----------
        train_loader : DataLoader
            训练数据
        val_loader : DataLoader
            验证数据
        epochs : int
            训练轮数
        task : str
            任务类型: 'regression' 或 'classification'
        """
        # 设置损失函数
        if task == 'regression':
            self.criterion = nn.MSELoss()
        else:
            self.criterion = nn.CrossEntropyLoss()
        
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        for epoch in range(epochs):
            # 训练
            self.model.train()
            train_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                loss.backward()
                self.optimizer.step()
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            self.train_losses.append(train_loss)
            
            # 验证
            if val_loader:
                val_loss = self.evaluate(val_loader, task)
                self.val_losses.append(val_loss)
                
                # 早停
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                    # 保存最佳模型
                    torch.save(self.model.state_dict(), 'best_model.pth')
                else:
                    patience_counter += 1
                
                if patience_counter >= patience:
                    print(f"Early stopping at epoch {epoch+1}")
                    break
            
            # 打印进度
            if (epoch + 1) % 10 == 0:
                if val_loader:
                    print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
                else:
                    print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss:.6f}")
        
        return self
    
    def evaluate(self, data_loader: DataLoader, task: str = 'regression') -> float:
        """评估模型"""
        self.model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for batch_X, batch_y in data_loader:
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                total_loss += loss.item()
        
        return total_loss / len(data_loader)
    
    def predict(self, data_loader: DataLoader) -> np.ndarray:
        """预测"""
        self.model.eval()
        predictions = []
        
        with torch.no_grad():
            for batch_X, _ in data_loader:
                outputs = self.model(batch_X)
                predictions.append(outputs.numpy())
        
        return np.concatenate(predictions, axis=0)
    
    def plot_loss(self, figsize: Tuple[int, int] = (10, 5)):
        """绘制损失曲线"""
        fig, ax = plt.subplots(figsize=figsize)
        
        ax.plot(self.train_losses, label='Train Loss')
        if self.val_losses:
            ax.plot(self.val_losses, label='Val Loss')
        
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Loss')
        ax.set_title('Training History')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig


def run_example():
    """
    示例：回归问题
    """
    print("=" * 60)
    print("PyTorch模板示例 - 回归问题")
    print("=" * 60)
    
    # 生成数据
    np.random.seed(42)
    n_samples = 1000
    n_features = 10
    
    X = np.random.randn(n_samples, n_features)
    y = np.sum(X[:, :3], axis=1) + 0.1 * np.random.randn(n_samples)
    
    # 转换为PyTorch张量
    X_tensor = torch.FloatTensor(X)
    y_tensor = torch.FloatTensor(y.reshape(-1, 1))
    
    # 划分数据集
    train_size = int(0.8 * n_samples)
    X_train, X_val = X_tensor[:train_size], X_tensor[train_size:]
    y_train, y_val = y_tensor[:train_size], y_tensor[train_size:]
    
    # 创建DataLoader
    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32)
    
    # 创建模型
    model = NeuralNetworkTemplate(
        input_size=n_features,
        hidden_sizes=[64, 32],
        output_size=1,
        dropout=0.2
    )
    
    print(f"\n模型结构:")
    print(model)
    
    # 训练
    trainer = Trainer(model, learning_rate=0.001)
    trainer.fit(train_loader, val_loader, epochs=50, task='regression')
    
    # 评估
    val_loss = trainer.evaluate(val_loader, task='regression')
    print(f"\n验证集MSE: {val_loss:.6f}")
    
    # 绘制损失曲线
    fig = trainer.plot_loss()
    plt.savefig('figures/pytorch_loss.png', dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    run_example()
