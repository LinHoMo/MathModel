# 图像处理与模式识别建模知识库

> 本文件提供数学建模竞赛中图像处理与模式识别相关问题的建模知识，包括问题特征、常用方法、数学基础、代码实现、常见陷阱和验证方法。

---

## 1. 问题特征

### 1.1 典型问题描述
- 撕碎纸片复原与拼接
- CT系统参数标定与图像重建
- 零件识别与分类
- 文字/图案识别
- 图像分割与特征提取

### 1.2 常见约束条件
- 纸片边缘匹配约束
- CT扫描角度和投影数量限制
- 图像分辨率和噪声
- 计算时间限制
- 识别准确率要求

### 1.3 数据特点
- 图像数据：像素矩阵、灰度值、颜色通道
- 边缘数据：轮廓坐标、梯度方向
- 投影数据：Radon变换结果
- 特征数据：形状描述符、纹理特征

---

## 2. 常用方法

| 方法 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 边缘提取（Canny） | 纸片轮廓检测 | 精度高、抗噪 | 参数敏感 |
| 图像分割 | 区域划分 | 自动化程度高 | 过分割问题 |
| Radon变换 | CT图像重建 | 数学基础扎实 | 计算量大 |
| 滤波反投影 | CT图像重建 | 重建速度快 | 伪影问题 |
| 特征提取（HOG/SIFT） | 模式识别 | 鲁棒性强 | 计算复杂 |
| 模板匹配 | 目标定位 | 简单有效 | 对旋转敏感 |

---

## 3. 数学基础

### 3.1 图像变换

**灰度变换**：
```
g(x,y) = T[f(x,y)]
线性: g = a*f + b
对数: g = c * log(1 + f)
伽马: g = c * f^γ
```

**傅里叶变换**：
```
F(u,v) = ΣΣ f(x,y) * exp(-j2π(ux/M + vy/N))
f(x,y) = (1/MN) ΣΣ F(u,v) * exp(j2π(ux/M + vy/N))
```

### 3.2 边缘检测

**梯度计算**：
```
Gx = ∂f/∂x ≈ [f(x+1,y) - f(x-1,y)] / 2
Gy = ∂f/∂y ≈ [f(x,y+1) - f(x,y-1)] / 2
|G| = sqrt(Gx² + Gy²)
θ = arctan(Gy / Gx)
```

**Canny边缘检测**：
1. 高斯滤波平滑
2. 计算梯度幅值和方向
3. 非极大值抑制
4. 双阈值检测和边缘连接

### 3.3 Radon变换

**连续Radon变换**：
```
Rf(ρ, θ) = ∫∫ f(x,y) * δ(x*cos(θ) + y*sin(θ) - ρ) dx dy
```

**离散Radon变换**：
```
Rf(ρ, θ) = ΣΣ f(i,j) * δ(i*cos(θ) + j*sin(θ) - ρ)
```

### 3.4 滤波反投影

**反投影**：
```
b(x,y) = ∫ Rf(ρ, θ)|_{ρ=x*cos(θ)+y*sin(θ)} dθ
```

**滤波反投影**：
```
f(x,y) = ∫ Q(Rf(ρ, θ))|_{ρ=x*cos(θ)+y*sin(θ)} dθ
Q: 滤波器（如Ram-Lak、Shepp-Logan）
```

---

## 4. Python实现

### 4.1 边缘检测

```python
import numpy as np
from scipy import ndimage

def canny_edge_detection(image, sigma=1.0, low_threshold=0.1, high_threshold=0.2):
    """
    Canny边缘检测实现
    
    Parameters
    ----------
    image : ndarray
        输入图像（灰度）
    sigma : float
        高斯滤波标准差
    low_threshold : float
        低阈值（比例）
    high_threshold : float
        高阈值（比例）
    
    Returns
    -------
    edges : ndarray
        边缘图像（二值）
    """
    # 1. 高斯滤波
    blurred = ndimage.gaussian_filter(image, sigma)
    
    # 2. 计算梯度
    Gx = ndimage.sobel(blurred, axis=0)
    Gy = ndimage.sobel(blurred, axis=1)
    
    magnitude = np.sqrt(Gx**2 + Gy**2)
    direction = np.arctan2(Gy, Gx)
    
    # 3. 非极大值抑制
    M, N = magnitude.shape
    nms = np.zeros_like(magnitude)
    
    for i in range(1, M-1):
        for j in range(1, N-1):
            angle = direction[i, j]
            
            # 量化方向到0°, 45°, 90°, 135°
            if angle < 0:
                angle += np.pi
            
            if (angle < np.pi/8) or (angle >= 7*np.pi/8):
                neighbors = [magnitude[i, j-1], magnitude[i, j+1]]
            elif angle < 3*np.pi/8:
                neighbors = [magnitude[i-1, j+1], magnitude[i+1, j-1]]
            elif angle < 5*np.pi/8:
                neighbors = [magnitude[i-1, j], magnitude[i+1, j]]
            else:
                neighbors = [magnitude[i-1, j-1], magnitude[i+1, j+1]]
            
            if magnitude[i, j] >= max(neighbors):
                nms[i, j] = magnitude[i, j]
    
    # 4. 双阈值检测
    low = low_threshold * np.max(nms)
    high = high_threshold * np.max(nms)
    
    edges = np.zeros_like(nms)
    edges[nms >= high] = 1
    edges[(nms >= low) & (nms < high)] = 0.5
    
    # 5. 边缘连接（简化版）
    # 实际应用中需要更复杂的连接算法
    
    return edges > 0
```

### 4.2 Radon变换与CT重建

```python
import numpy as np
from scipy.ndimage import rotate

def radon_transform(image, theta_range=None):
    """
    Radon变换
    
    Parameters
    ----------
    image : ndarray
        输入图像
    theta_range : ndarray
        投影角度范围
    
    Returns
    -------
    sinogram : ndarray
        正弦图（Radon变换结果）
    """
    if theta_range is None:
        theta_range = np.linspace(0, 180, 180)
    
    M, N = image.shape
    diag = int(np.ceil(np.sqrt(M**2 + N**2)))
    
    sinogram = np.zeros((diag, len(theta_range)))
    
    for i, theta in enumerate(theta_range):
        # 旋转图像
        rotated = rotate(image, theta, reshape=False)
        
        # 沿列求和（投影）
        sinogram[:, i] = np.sum(rotated, axis=0)
    
    return sinogram

def filtered_back_projection(sinogram, theta_range=None):
    """
    滤波反投影重建
    
    Parameters
    ----------
    sinogram : ndarray
        正弦图
    theta_range : ndarray
        投影角度范围
    
    Returns
    -------
    reconstruction : ndarray
        重建图像
    """
    if theta_range is None:
        theta_range = np.linspace(0, 180, sinogram.shape[1])
    
    n_proj, n_angles = sinogram.shape
    reconstruction = np.zeros((n_proj, n_proj))
    
    # Ram-Lak滤波器
    freq = np.fft.fftfreq(n_proj)
    filter_kernel = np.abs(freq)
    filter_kernel = np.fft.fftshift(filter_kernel)
    
    for i, theta in enumerate(theta_range):
        # 滤波
        proj = sinogram[:, i]
        proj_fft = np.fft.fft(proj)
        proj_filtered = np.real(np.fft.ifft(proj_fft * filter_kernel))
        
        # 反投影
        rotated = rotate(proj_filtered.reshape(1, -1), theta, reshape=False)
        reconstruction += rotated
    
    # 归一化
    reconstruction *= np.pi / (2 * len(theta_range))
    
    return reconstruction

def create_shepp_logan_phantom(n=256):
    """创建Shepp-Logan模型（测试用）"""
    phantom = np.zeros((n, n))
    
    # 主椭圆
    y, x = np.ogrid[-n//2:n//2, -n//2:n//2]
    mask = (x**2 / (0.4*n)**2 + y**2 / (0.5*n)**2) < 1
    phantom[mask] = 1
    
    # 内部椭圆
    mask2 = (x**2 / (0.2*n)**2 + y**2 / (0.3*n)**2) < 1
    phantom[mask2] = 0.8
    
    return phantom
```

### 4.3 纸片复原

```python
import numpy as np
from scipy.spatial.distance import cdist

class PaperPiece:
    """纸片类"""
    
    def __init__(self, piece_id, image, contour):
        """
        Parameters
        ----------
        piece_id : int
            纸片编号
        image : ndarray
            纸片图像
        contour : ndarray
            轮廓坐标
        """
        self.id = piece_id
        self.image = image
        self.contour = contour
        self.edges = self._extract_edges()
    
    def _extract_edges(self):
        """提取四条边"""
        n_points = len(self.contour)
        n_per_edge = n_points // 4
        
        edges = []
        for i in range(4):
            start = i * n_per_edge
            end = (i + 1) * n_per_edge
            edges.append(self.contour[start:end])
        
        return edges
    
    def edge_similarity(self, edge1, edge2):
        """计算两条边的相似度"""
        if len(edge1) != len(edge2):
            # 重采样到相同长度
            from scipy.interpolate import interp1d
            
            t1 = np.linspace(0, 1, len(edge1))
            t2 = np.linspace(0, 1, len(edge2))
            
            f1 = interp1d(t1, edge1.T, axis=1)
            f2 = interp1d(t2, edge2.T, axis=1)
            
            t_common = np.linspace(0, 1, min(len(edge1), len(edge2)))
            edge1_resampled = f1(t_common).T
            edge2_resampled = f2(t_common).T
        else:
            edge1_resampled = edge1
            edge2_resampled = edge2
        
        # 计算距离
        dist = np.mean(np.sqrt(np.sum((edge1_resampled - edge2_resampled)**2, axis=1)))
        
        return 1 / (1 + dist)

def match_pieces(pieces):
    """
    匹配纸片
    
    Parameters
    ----------
    pieces : list
        纸片列表
    
    Returns
    -------
    matches : list
        匹配结果 [(piece1, edge1, piece2, edge2), ...]
    """
    n = len(pieces)
    similarity_matrix = np.zeros((n*4, n*4))
    
    # 计算所有边对的相似度
    for i in range(n):
        for j in range(i+1, n):
            for e1 in range(4):
                for e2 in range(4):
                    sim = pieces[i].edge_similarity(
                        pieces[i].edges[e1],
                        pieces[j].edges[e2]
                    )
                    similarity_matrix[i*4+e1, j*4+e2] = sim
                    similarity_matrix[j*4+e2, i*4+e1] = sim
    
    # 贪心匹配
    matches = []
    used = set()
    
    for _ in range(n-1):
        # 找最大相似度
        max_sim = 0
        best_match = None
        
        for i in range(n*4):
            if i in used:
                continue
            for j in range(i+1, n*4):
                if j in used:
                    continue
                if similarity_matrix[i, j] > max_sim:
                    max_sim = similarity_matrix[i, j]
                    best_match = (i//4, i%4, j//4, j%4)
        
        if best_match:
            matches.append(best_match)
            used.add(best_match[0]*4 + best_match[1])
            used.add(best_match[2]*4 + best_match[3])
    
    return matches
```

### 4.4 特征提取

```python
import numpy as np

def extract_hog_features(image, pixels_per_cell=8, 
                         cells_per_block=2, orientations=9):
    """
    HOG特征提取
    
    Parameters
    ----------
    image : ndarray
        输入图像
    pixels_per_cell : int
        每个cell的像素数
    cells_per_block : int
        每个block的cell数
    orientations : int
        方向直方图的bin数
    
    Returns
    -------
    features : ndarray
        HOG特征向量
    """
    from scipy.ndimage import sobel
    
    # 1. 计算梯度
    gx = sobel(image, axis=0)
    gy = sobel(image, axis=1)
    
    magnitude = np.sqrt(gx**2 + gy**2)
    direction = np.arctan2(gy, gx) % np.pi
    
    # 2. 划分cell并计算直方图
    M, N = image.shape
    n_cells_y = M // pixels_per_cell
    n_cells_x = N // pixels_per_cell
    
    features = []
    
    for i in range(n_cells_y):
        for j in range(n_cells_x):
            # 提取cell
            y_start = i * pixels_per_cell
            y_end = (i + 1) * pixels_per_cell
            x_start = j * pixels_per_cell
            x_end = (j + 1) * pixels_per_cell
            
            mag_cell = magnitude[y_start:y_end, x_start:x_end]
            dir_cell = direction[y_start:y_end, x_start:x_end]
            
            # 计算方向直方图
            hist = np.zeros(orientations)
            for m, d in zip(mag_cell.flatten(), dir_cell.flatten()):
                bin_idx = int(d / np.pi * orientations) % orientations
                hist[bin_idx] += m
            
            features.extend(hist)
    
    features = np.array(features)
    
    # 3. 块归一化
    block_size = cells_per_block ** 2 * orientations
    n_blocks = len(features) // block_size
    
    for i in range(n_blocks):
        start = i * block_size
        end = start + block_size
        block = features[start:end]
        
        norm = np.sqrt(np.sum(block**2) + 1e-6)
        features[start:end] = block / norm
    
    return features

def extract_shape_features(contour):
    """提取形状特征"""
    # 计算周长和面积
    perimeter = np.sum(np.sqrt(np.sum(np.diff(contour, axis=0)**2, axis=1)))
    area = np.abs(np.sum(contour[:, 0] * np.roll(contour[:, 1], -1) - 
                         contour[:, 1] * np.roll(contour[:, 0], -1)) / 2)
    
    # 圆形度
    circularity = 4 * np.pi * area / (perimeter**2 + 1e-6)
    
    # 紧凑度
    compactness = perimeter**2 / (4 * np.pi * area + 1e-6)
    
    # 偏心率
    moments = cv2.moments(contour)
    hu_moments = cv2.HuMoments(moments).flatten()
    
    return {
        'perimeter': perimeter,
        'area': area,
        'circularity': circularity,
        'compactness': compactness,
        'hu_moments': hu_moments
    }
```

---

## 5. 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 阈值选择不当 | 边缘检测效果差 | 使用自适应阈值（Otsu） |
| 噪声干扰 | 伪边缘多 | 先进行高斯滤波 |
| Radon变换角度不足 | 重建图像模糊 | 增加投影角度数量 |
| 反投影未滤波 | 图像模糊 | 使用Ram-Lak或Shepp-Logan滤波器 |
| 特征维数过高 | 计算慢、过拟合 | 使用PCA降维 |
| 图像旋转未处理 | 匹配失败 | 使用旋转不变特征 |

---

## 6. 验证方法

### 6.1 边缘检测验证
- 检查边缘连续性
- 验证边缘定位精度

### 6.2 CT重建验证
- 与Shepp-Logan模型对比
- 计算重建误差（MSE、PSNR）

### 6.3 纸片复原验证
- 检查拼接缝隙
- 验证图像连续性

### 6.4 特征提取验证
- 检查特征区分度
- 验证分类准确率

---

## 7. 真题案例

### 7.1 2013B 撕碎纸片复原

**题目要点**：
- 将撕碎的纸片重新拼接
- 恢复原始图像内容

**解题思路**：
1. 边缘检测提取纸片轮廓
2. 计算边缘相似度
3. 贪心或动态规划匹配
4. 拼接并验证

### 7.2 2017A CT系统参数标定

**题目要点**：
- 标定CT系统参数（角度、间距）
- 重建图像

**解题思路**：
1. 使用已知模型（如楔形块）标定
2. Radon变换获取正弦图
3. 滤波反投影重建
4. 验证重建精度

**关键公式**：
```
Radon变换: Rf(ρ,θ) = ∫f(x,y)δ(xcosθ+ysinθ-ρ)dxdy
滤波反投影: f(x,y) = ∫Q(Rf(ρ,θ))|_{ρ=xcosθ+ysinθ}dθ
```

---

## 8. 验证清单

- [ ] 边缘检测参数合理（σ、阈值）
- [ ] Radon变换角度覆盖完整（0-180°）
- [ ] 反投影滤波器正确（Ram-Lak）
- [ ] 纸片匹配准确率>90%
- [ ] 特征提取具有区分度
- [ ] 图像重建误差MSE<0.01
