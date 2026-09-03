# 图像处理方法论

> 本文件提供数学建模竞赛中常用的图像处理知识，包括核心技术、算法选择、防错策略和验证方法。

---

## 1. 技术选择决策树

```
图像处理任务类型识别：
├── 预处理
│   ├── 去噪 → 中值滤波/高斯滤波
│   ├── 增强 → 直方图均衡化/CLAHE
│   └── 标准化 → 缩放/归一化
├── 分割
│   ├── 阈值分割 → Otsu/自适应阈值
│   ├── 边缘检测 → Canny/Sobel
│   └── 区域分割 → 分水岭/区域生长
├── 特征提取
│   ├── 形态特征 → 轮廓/面积/周长
│   ├── 纹理特征 → LBP/HOG
│   └── 颜色特征 → HSV/颜色直方图
└── 识别/分类
    ├── 模板匹配 → cv2.matchTemplate
    ├── 目标检测 → YOLO/SSD
    └── OCR → Tesseract/PaddleOCR
```

---

## 2. 核心技术详解

### 2.1 图像读取与预处理

**代码框架**：
```python
import cv2
import numpy as np
from PIL import Image

def load_and_preprocess(image_path, target_size=None):
    # 读取图像
    img = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # 缩放
    if target_size:
        img_rgb = cv2.resize(img_rgb, target_size)
    
    # 灰度化
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    
    # 归一化
    img_normalized = img_rgb.astype(np.float32) / 255.0
    
    return img_rgb, gray, img_normalized
```

### 2.2 图像滤波与去噪

```python
def image_filtering(gray, method='gaussian'):
    if method == 'gaussian':
        filtered = cv2.GaussianBlur(gray, (5, 5), 0)
    elif method == 'median':
        filtered = cv2.medianBlur(gray, 5)
    elif method == 'bilateral':
        filtered = cv2.bilateralFilter(gray, 9, 75, 75)
    elif method == 'mean':
        filtered = cv2.blur(gray, (5, 5))
    
    return filtered
```

### 2.3 直方图均衡化

```python
def histogram_equalization(gray, method='clahe'):
    if method == 'global':
        equalized = cv2.equalizeHist(gray)
    elif method == 'clahe':
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        equalized = clahe.apply(gray)
    
    return equalized
```

---

### 2.4 边缘检测

**Canny边缘检测**：
```python
def canny_edge_detection(gray, low_threshold=50, high_threshold=150):
    edges = cv2.Canny(gray, low_threshold, high_threshold)
    return edges

def adaptive_canny(gray):
    median_val = np.median(gray)
    low = int(max(0, 0.67 * median_val))
    high = int(min(255, 1.33 * median_val))
    edges = cv2.Canny(gray, low, high)
    return edges
```

**Sobel边缘检测**：
```python
def sobel_edge_detection(gray):
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(sobelx**2 + sobely**2)
    magnitude = np.uint8(magnitude / magnitude.max() * 255)
    return magnitude
```

---

### 2.5 阈值分割

```python
def threshold_segmentation(gray, method='otsu'):
    if method == 'binary':
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    elif method == 'otsu':
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif method == 'adaptive':
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
    return binary
```

---

### 2.6 形态学操作

```python
def morphological_operations(binary, operation='open'):
    kernel = np.ones((5, 5), np.uint8)
    
    if operation == 'erosion':
        result = cv2.erode(binary, kernel, iterations=1)
    elif operation == 'dilation':
        result = cv2.dilate(binary, kernel, iterations=1)
    elif operation == 'open':
        result = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    elif operation == 'close':
        result = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    elif operation == 'gradient':
        result = cv2.morphologyEx(binary, cv2.MORPH_GRADIENT, kernel)
    
    return result
```

---

### 2.7 轮廓检测与特征提取

```python
def contour_features(binary):
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    features = []
    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        # 近似多边形
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 最小外接矩形
        rect = cv2.minAreaRect(contour)
        width, height = rect[1]
        aspect_ratio = max(width, height) / (min(width, height) + 1e-6)
        
        # 圆形度
        circularity = 4 * np.pi * area / (perimeter**2 + 1e-6)
        
        features.append({
            'area': area,
            'perimeter': perimeter,
            'vertices': len(approx),
            'aspect_ratio': aspect_ratio,
            'circularity': circularity
        })
    
    return features
```

---

### 2.8 透视变换

```python
def perspective_transform(image, src_points, dst_points):
    M = cv2.getPerspectiveTransform(src_points, dst_points)
    warped = cv2.warpPerspective(image, M, (image.shape[1], image.shape[0]))
    return warped

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect
```

---

## 3. 完整应用流程

### 3.1 文档复原

```python
def document_restoration(image_path):
    # 1. 读取图像
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. 去噪
    denoised = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 3. 边缘检测
    edges = cv2.Canny(denoised, 50, 150)
    
    # 4. 膨胀连接边缘
    dilated = cv2.dilate(edges, np.ones((3, 3)), iterations=2)
    
    # 5. 查找轮廓
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 6. 找到最大矩形轮廓
    largest = max(contours, key=cv2.contourArea)
    epsilon = 0.02 * cv2.arcLength(largest, True)
    approx = cv2.approxPolyDP(largest, epsilon, True)
    
    # 7. 透视变换
    if len(approx) == 4:
        pts = approx.reshape(4, 2)
        ordered = order_points(pts)
        dst = np.array([[0, 0], [500, 0], [500, 700], [0, 700]], dtype="float32")
        warped = perspective_transform(img, ordered, dst)
        return warped
    
    return img
```

### 3.2 零件识别

```python
def part_recognition(image_path, template_path):
    # 读取图像
    img = cv2.imread(image_path)
    template = cv2.imread(template_path)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    # 边缘检测
    edges = cv2.Canny(gray, 50, 150)
    template_edges = cv2.Canny(template_gray, 50, 150)
    
    # 模板匹配
    result = cv2.matchTemplate(edges, template_edges, cv2.TM_CCOEFF_NORMED)
    threshold = 0.8
    locations = np.where(result >= threshold)
    
    # 绘制匹配结果
    h, w = template.shape[:2]
    for pt in zip(*locations[::-1]):
        cv2.rectangle(img, pt, (pt[0] + w, pt[1] + h), (0, 255, 0), 2)
    
    return img, len(locations[0])
```

---

## 4. 常见陷阱与最佳实践

### 4.1 常见陷阱

| 错误类型 | 典型表现 | 防错方法 |
|---------|---------|---------|
| 噪声干扰 | 边缘检测效果差 | 先滤波去噪 |
| 阈值选择不当 | 分割结果不准确 | Otsu/自适应阈值 |
| 坐标变换错误 | 透视变换扭曲 | 检查点顺序 |
| 光照不均 | 局部区域效果差 | CLAHE/局部阈值 |
| 比例尺错误 | 测量结果不准 | 标定比例尺 |

### 4.2 最佳实践

- **预处理优先**：去噪→增强→分割
- **参数自适应**：根据图像特性自动调整阈值
- **多方法对比**：尝试多种方法选择最佳
- **可视化中间结果**：便于调试和验证
- **保存处理参数**：确保结果可复现

---

## 5. 验证清单

- [ ] 图像正确读取（尺寸、通道）
- [ ] 预处理效果良好（去噪、增强）
- [ ] 边缘检测清晰完整
- [ ] 分割结果准确
- [ ] 特征提取合理
- [ ] 坐标变换正确
- [ ] 结果可视化展示
- [ ] 处理参数可复现
