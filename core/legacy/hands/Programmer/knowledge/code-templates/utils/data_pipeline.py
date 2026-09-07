"""
数据预处理管道
来源: 高教杯优秀论文通用方法
适用问题: 从原始数据到建模就绪数据的完整流程
输入: 原始数据
输出: 清洗后的特征矩阵、预处理管道对象
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, List, Dict, Any
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.feature_selection import SelectKBest, f_classif, f_regression, mutual_info_classif
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')


class DataPipeline:
    """
    数据预处理管道
    
    支持完整的数据预处理流程：
    1. 数据加载与初步检查
    2. 缺失值处理
    3. 异常值处理
    4. 特征工程
    5. 特征选择
    6. 数据标准化
    """
    
    def __init__(self, target_col: Optional[str] = None, task: str = 'classification'):
        """
        Parameters
        ----------
        target_col : str
            目标变量列名
        task : str
            任务类型: 'classification' 或 'regression'
        """
        self.target_col = target_col
        self.task = task
        self.pipeline_log = []
        self.fitted = False
        
        # 预处理器
        self.imputer = None
        self.scaler = None
        self.encoder = None
        self.feature_selector = None
        self.selected_features = None
    
    def log(self, message: str):
        """记录处理日志"""
        self.pipeline_log.append(message)
    
    def load_and_check(self, df: pd.DataFrame) -> pd.DataFrame:
        """步骤1: 数据加载与初步检查"""
        self.log("=" * 50)
        self.log("步骤1: 数据加载与初步检查")
        self.log("=" * 50)
        
        self.log(f"样本数量: {len(df)}")
        self.log(f"特征数量: {len(df.columns)}")
        
        # 缺失值统计
        missing = df.isnull().sum()
        missing_pct = (missing / len(df)) * 100
        self.log(f"缺失值列数: {(missing > 0).sum()}")
        
        # 数据类型统计
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        self.log(f"数值特征: {len(numeric_cols)}个")
        self.log(f"类别特征: {len(cat_cols)}个")
        
        return df.copy()
    
    def handle_missing(self, df: pd.DataFrame, strategy: str = 'auto') -> pd.DataFrame:
        """
        步骤2: 缺失值处理
        
        Parameters
        ----------
        df : DataFrame
            输入数据
        strategy : str
            策略: 'auto', 'mean', 'median', 'mode', 'knn', 'drop'
        """
        self.log("\n步骤2: 缺失值处理")
        
        df = df.copy()
        
        if strategy == 'auto':
            # 自动选择策略
            for col in df.columns:
                if df[col].isnull().sum() > 0:
                    missing_pct = df[col].isnull().sum() / len(df)
                    
                    if missing_pct > 0.5:
                        # 缺失过多，删除
                        df = df.drop(columns=[col])
                        self.log(f"  删除列 {col} (缺失{missing_pct:.1%})")
                    elif df[col].dtype in ['object', 'category']:
                        # 类别特征用众数
                        df[col] = df[col].fillna(df[col].mode()[0])
                        self.log(f"  {col}: 众数填充")
                    elif missing_pct < 0.1:
                        # 缺失较少，用中位数
                        df[col] = df[col].fillna(df[col].median())
                        self.log(f"  {col}: 中位数填充")
                    else:
                        # 缺失较多，用KNN
                        df[col] = df[col].fillna(df[col].median())
                        self.log(f"  {col}: 中位数填充")
        
        elif strategy == 'drop':
            df = df.dropna()
            self.log(f"  删除含缺失值的行，剩余{len(df)}行")
        
        elif strategy == 'knn':
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                imputer = KNNImputer(n_neighbors=5)
                df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
                self.log(f"  KNN填充数值特征")
        
        return df
    
    def handle_outliers(self, df: pd.DataFrame, method: str = 'iqr', threshold: float = 1.5) -> pd.DataFrame:
        """
        步骤3: 异常值处理
        
        Parameters
        ----------
        df : DataFrame
            输入数据
        method : str
            方法: 'iqr', 'zscore', 'clip'
        threshold : float
            阈值
        """
        self.log("\n步骤3: 异常值处理")
        
        df = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if self.target_col in numeric_cols:
            numeric_cols = numeric_cols.drop(self.target_col)
        
        for col in numeric_cols:
            if method == 'iqr':
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                
                outliers = ((df[col] < lower) | (df[col] > upper)).sum()
                
                if outliers > 0:
                    df[col] = df[col].clip(lower, upper)
                    self.log(f"  {col}: 处理{outliers}个异常值 (IQR)")
            
            elif method == 'zscore':
                from scipy.stats import zscore
                z_scores = np.abs(zscore(df[col].dropna()))
                outliers = (z_scores > threshold).sum()
                
                if outliers > 0:
                    df.loc[z_scores > threshold, col] = df[col].median()
                    self.log(f"  {col}: 处理{outliers}个异常值 (Z-score)")
        
        return df
    
    def encode_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        步骤4: 类别编码
        """
        self.log("\n步骤4: 类别编码")
        
        df = df.copy()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        
        for col in cat_cols:
            if col == self.target_col:
                continue
            
            unique_vals = df[col].nunique()
            
            if unique_vals == 2:
                # 二分类，Label Encoding
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.log(f"  {col}: Label编码 (2类)")
            elif unique_vals <= 10:
                # 少量类别，One-Hot Encoding
                dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
                df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
                self.log(f"  {col}: One-Hot编码 ({unique_vals}类)")
            else:
                # 大量类别，频率编码
                freq = df[col].value_counts() / len(df)
                df[col] = df[col].map(freq)
                self.log(f"  {col}: 频率编码 ({unique_vals}类)")
        
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        步骤5: 特征工程
        """
        self.log("\n步骤5: 特征工程")
        
        df = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if self.target_col in numeric_cols:
            numeric_cols = numeric_cols.drop(self.target_col)
        
        # 多项式特征（前5个数值特征）
        if len(numeric_cols) >= 2:
            for i in range(min(2, len(numeric_cols))):
                for j in range(i+1, min(3, len(numeric_cols))):
                    col1, col2 = numeric_cols[i], numeric_cols[j]
                    new_col = f"{col1}_x_{col2}"
                    df[new_col] = df[col1] * df[col2]
            self.log(f"  生成交互特征")
        
        # 对数特征（正数值）
        for col in numeric_cols[:3]:
            if (df[col] > 0).all():
                new_col = f"{col}_log"
                df[new_col] = np.log1p(df[col])
                self.log(f"  生成对数特征: {new_col}")
        
        return df
    
    def select_features(self, df: pd.DataFrame, n_features: Optional[int] = None) -> pd.DataFrame:
        """
        步骤6: 特征选择
        """
        self.log("\n步骤6: 特征选择")
        
        if self.target_col is None or self.target_col not in df.columns:
            return df
        
        df = df.copy()
        X = df.drop(columns=[self.target_col])
        y = df[self.target_col]
        
        # 删除非数值列
        X = X.select_dtypes(include=[np.number])
        
        if n_features is None:
            n_features = min(20, len(X.columns))
        
        if n_features >= len(X.columns):
            return df
        
        # 选择方法
        if self.task == 'classification':
            selector = SelectKBest(mutual_info_classif, k=n_features)
        else:
            selector = SelectKBest(f_regression, k=n_features)
        
        X_selected = selector.fit_transform(X, y)
        selected_mask = selector.get_support()
        selected_cols = X.columns[selected_mask].tolist()
        
        self.selected_features = selected_cols
        self.log(f"  从{len(X.columns)}个特征中选择{n_features}个")
        
        # 保留未选中的特征（用于记录）
        dropped_cols = X.columns[~selected_mask].tolist()
        self.log(f"  删除特征: {dropped_cols[:5]}...")
        
        return df[self.target_col.tolist() + selected_cols]
    
    def normalize(self, df: pd.DataFrame, method: str = 'standard') -> pd.DataFrame:
        """
        步骤7: 数据标准化
        """
        self.log("\n步骤7: 数据标准化")
        
        df = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if self.target_col in numeric_cols:
            numeric_cols = numeric_cols.drop(self.target_col)
        
        if method == 'standard':
            self.scaler = StandardScaler()
        elif method == 'minmax':
            self.scaler = MinMaxScaler()
        
        if len(numeric_cols) > 0:
            df[numeric_cols] = self.scaler.fit_transform(df[numeric_cols])
            self.log(f"  {method}标准化 {len(numeric_cols)}个特征")
        
        return df
    
    def fit_transform(self, df: pd.DataFrame, **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        完整管道执行
        
        Parameters
        ----------
        df : DataFrame
            原始数据
        **kwargs : dict
            各步骤参数
        
        Returns
        -------
        X : DataFrame
            预处理后的特征
        y : DataFrame/Series
            目标变量
        """
        # 加载检查
        df = self.load_and_check(df)
        
        # 缺失值处理
        df = self.handle_missing(df, kwargs.get('missing_strategy', 'auto'))
        
        # 异常值处理
        df = self.handle_outliers(df, kwargs.get('outlier_method', 'iqr'))
        
        # 类别编码
        df = self.encode_categorical(df)
        
        # 特征工程
        df = self.engineer_features(df)
        
        # 特征选择
        df = self.select_features(df, kwargs.get('n_features', None))
        
        # 标准化
        df = self.normalize(df, kwargs.get('normalize_method', 'standard'))
        
        # 分离特征和目标
        if self.target_col and self.target_col in df.columns:
            X = df.drop(columns=[self.target_col])
            y = df[self.target_col]
        else:
            X = df
            y = None
        
        self.fitted = True
        self.log("\n" + "=" * 50)
        self.log("预处理完成")
        self.log("=" * 50)
        
        return X, y
    
    def get_log(self) -> str:
        """获取处理日志"""
        return "\n".join(self.pipeline_log)


def run_example():
    """
    示例：C题蔬菜数据预处理
    """
    # 生成模拟数据
    np.random.seed(42)
    n = 500
    
    data = {
        'price': np.random.uniform(3, 15, n),
        'sales': np.random.poisson(50, n),
        'temperature': np.random.normal(25, 5, n),
        'humidity': np.random.uniform(40, 80, n),
        'promotion': np.random.choice([0, 1], n, p=[0.7, 0.3]),
        'category': np.random.choice(['vegetable', 'fruit', 'meat'], n),
        'day_of_week': np.random.choice(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], n),
        'stock': np.random.poisson(100, n)
    }
    df = pd.DataFrame(data)
    
    # 添加缺失值
    df.loc[np.random.choice(n, 30), 'price'] = np.nan
    df.loc[np.random.choice(n, 20), 'humidity'] = np.nan
    
    print("=" * 60)
    print("数据预处理管道示例 - 超市销售数据")
    print("=" * 60)
    
    # 创建管道
    pipeline = DataPipeline(target_col='sales', task='regression')
    
    # 执行预处理
    X, y = pipeline.fit_transform(df, n_features=10)
    
    # 输出日志
    print(pipeline.get_log())
    
    print(f"\n预处理结果:")
    print(f"  特征矩阵形状: {X.shape}")
    print(f"  目标变量形状: {y.shape if y is not None else 'None'}")
    print(f"  特征列: {list(X.columns)}")


if __name__ == "__main__":
    run_example()
