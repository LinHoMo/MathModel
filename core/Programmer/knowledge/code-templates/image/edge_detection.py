"""
图像边缘检测Pipeline模板
来源: 数学建模图像处理常用方法
适用问题: 边缘检测、直线/圆检测、轮廓分析
输入: 图像文件或numpy数组
输出: 边缘图、检测到的形状、轮廓特征
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Tuple, List, Dict
import warnings
warnings.filterwarnings('ignore')


class EdgeDetectionPipeline:
    """
    图像边缘检测Pipeline
    
    支持:
    - Canny边缘检测
    - 霍夫变换检测直线/圆
    - 轮廓提取+面积/周长计算
    
    Parameters
    ----------
    image : ndarray
        输入图像 (灰度或RGB)
    """

    def __init__(self, image: np.ndarray):
        if image.ndim == 3:
            self.gray = np.mean(image, axis=2).astype(np.uint8)
            self.rgb = image
        else:
            self.gray = image.astype(np.uint8)
            self.rgb = np.stack([image] * 3, axis=2)
        self.edges = None
        self.contours = None
        self.lines = None
        self.circles = None

    def preprocess(self, kernel_size: int = 5) -> np.ndarray:
        """
        高斯滤波去噪
        
        Parameters
        ----------
        kernel_size : int
            高斯核大小 (必须为奇数)
        """
        from scipy.ndimage import gaussian_filter
        self.gray_smooth = gaussian_filter(self.gray.astype(float), sigma=kernel_size / 3)
        return self.gray_smooth

    def canny_edge_detection(self, low_threshold: int = 50,
                              high_threshold: int = 150) -> np.ndarray:
        """
        Canny边缘检测
        
        Parameters
        ----------
        low_threshold : int
            低阈值
        high_threshold : int
            高阈值
        """
        from skimage.feature import canny

        if not hasattr(self, 'gray_smooth'):
            self.preprocess()

        self.edges = canny(self.gray_smooth / 255.0,
                          low_threshold=low_threshold / 255.0,
                          high_threshold=high_threshold / 255.0)
        return self.edges.astype(np.uint8) * 255

    def sobel_edge_detection(self) -> np.ndarray:
        """Sobel边缘检测 (备用方法)"""
        from scipy.ndimage import sobel

        if not hasattr(self, 'gray_smooth'):
            self.preprocess()

        sx = sobel(self.gray_smooth, axis=1)
        sy = sobel(self.gray_smooth, axis=0)
        self.edges = np.sqrt(sx ** 2 + sy ** 2)
        self.edges = (self.edges / self.edges.max() * 255).astype(np.uint8)
        return self.edges

    def detect_lines_hough(self, min_line_length: int = 50,
                           max_line_gap: int = 10) -> np.ndarray:
        """
        霍夫变换检测直线
        
        Returns
        -------
        lines : ndarray
            检测到的直线 [(x1,y1,x2,y2), ...]
        """
        from skimage.transform import hough_line, hough_line_peaks
        from skimage.feature import canny

        if self.edges is None:
            self.canny_edge_detection()

        # 霍夫变换
        tested_angles = np.linspace(-np.pi / 2, np.pi / 2, 360, endpoint=False)
        h, theta, d = hough_line(self.edges, theta=tested_angles)

        # 检测峰值
        _, angles, dists = hough_line_peaks(h, theta, d,
                                            min_line_distance=min_line_length,
                                            num_peaks=20)

        # 转换为端点坐标
        lines = []
        for angle, dist in zip(angles, dists):
            cos_a = np.cos(angle)
            sin_a = np.sin(angle)
            x0 = dist * cos_a
            y0 = dist * sin_a
            # 画线的两个端点
            x1 = int(x0 + 1000 * (-sin_a))
            y1 = int(y0 + 1000 * cos_a)
            x2 = int(x0 - 1000 * (-sin_a))
            y2 = int(y0 - 1000 * cos_a)
            lines.append((x1, y1, x2, y2))

        self.lines = np.array(lines) if lines else np.array([])
        return self.lines

    def detect_circles_hough(self, min_radius: int = 20,
                              max_radius: int = 100) -> np.ndarray:
        """
        霍夫变换检测圆
        
        Returns
        -------
        circles : ndarray
            检测到的圆 [(cx, cy, r), ...]
        """
        from skimage.transform import hough_circle, hough_circle_peaks
        from skimage.feature import canny

        if self.edges is None:
            self.canny_edge_detection()

        # 多尺度霍夫圆变换
        radii = range(min_radius, max_radius + 1, 2)
        hough_res = hough_circle(self.edges, radii)

        # 检测峰值
        accums, cx, cy, radii = hough_circle_peaks(hough_res, radii,
                                                    min_xdistance=30,
                                                    min_ydistance=30,
                                                    num_peaks=10)

        self.circles = np.column_stack([cx, cy, radii]) if len(cx) > 0 else np.array([])
        return self.circles

    def extract_contours(self) -> List[np.ndarray]:
        """
        轮廓提取
        
        Returns
        -------
        contours : list of ndarray
            轮廓列表
        """
        from skimage.measure import find_contours

        if self.edges is None:
            self.canny_edge_detection()

        # 二值化
        binary = (self.edges > 0).astype(float)

        # 提取轮廓
        contours_raw = find_contours(binary, level=0.5)
        self.contours = contours_raw
        return self.contours

    def compute_contour_features(self) -> List[Dict]:
        """
        计算轮廓特征 (面积、周长、质心、紧凑度)
        
        Returns
        -------
        features : list of dict
            各轮廓的特征
        """
        if self.contours is None:
            self.extract_contours()

        features = []
        for i, contour in enumerate(self.contours):
            # 面积 (Shoelace公式)
            x = contour[:, 1]
            y = contour[:, 0]
            area = 0.5 * np.abs(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1]))

            # 周长
            dx = np.diff(x)
            dy = np.diff(y)
            perimeter = np.sum(np.sqrt(dx ** 2 + dy ** 2))

            # 质心
            cx = np.mean(x)
            cy = np.mean(y)

            # 紧凑度 = 4π * 面积 / 周长²
            compactness = 4 * np.pi * area / (perimeter ** 2 + 1e-8)

            features.append({
                'contour_id': i,
                'area': area,
                'perimeter': perimeter,
                'centroid': (cx, cy),
                'compactness': compactness,
                'n_points': len(contour)
            })

        return features

    def draw_results(self, show_lines: bool = True, show_circles: bool = True,
                     show_contours: bool = True) -> np.ndarray:
        """
        在原图上绘制检测结果
        
        Returns
        -------
        result : ndarray
            标注后的图像
        """
        if self.rgb.ndim == 3:
            result = self.rgb.copy()
        else:
            result = np.stack([self.rgb] * 3, axis=2)

        # 边缘叠加 (红色)
        if self.edges is not None:
            edge_mask = self.edges > 0
            result[edge_mask] = [255, 0, 0]

        # 绘制直线 (绿色)
        if show_lines and self.lines is not None and len(self.lines) > 0:
            from skimage.draw import line
            for x1, y1, x2, y2 in self.lines:
                rr, cc = line(max(0, y1), max(0, x1),
                             min(result.shape[0] - 1, y2),
                             min(result.shape[1] - 1, x2))
                valid = (rr >= 0) & (rr < result.shape[0]) & (cc >= 0) & (cc < result.shape[1])
                result[rr[valid], cc[valid]] = [0, 255, 0]

        # 绘制圆 (蓝色)
        if show_circles and self.circles is not None and len(self.circles) > 0:
            from skimage.draw import circle_perimeter
            for cx, cy, r in self.circles:
                rr, cc = circle_perimeter(int(cy), int(cx), int(r),
                                         shape=result.shape[:2])
                valid = (rr >= 0) & (rr < result.shape[0]) & (cc >= 0) & (cc < result.shape[1])
                result[rr[valid], cc[valid]] = [0, 0, 255]

        return result.astype(np.uint8)

    def plot_pipeline(self, filename: Optional[str] = None):
        """可视化Pipeline各阶段结果"""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))

        # 原图
        axes[0, 0].imshow(self.gray, cmap='gray')
        axes[0, 0].set_title('Original (Grayscale)')
        axes[0, 0].axis('off')

        # 预处理
        if hasattr(self, 'gray_smooth'):
            axes[0, 1].imshow(self.gray_smooth, cmap='gray')
            axes[0, 1].set_title('Gaussian Filtered')
        axes[0, 1].axis('off')

        # 边缘
        if self.edges is not None:
            axes[0, 2].imshow(self.edges, cmap='gray')
            axes[0, 2].set_title('Canny Edges')
        axes[0, 2].axis('off')

        # 轮廓
        axes[1, 0].imshow(self.gray, cmap='gray')
        if self.contours:
            for contour in self.contours:
                axes[1, 0].plot(contour[:, 1], contour[:, 0], 'g-', linewidth=1)
        axes[1, 0].set_title(f'Contours ({len(self.contours or [])})')
        axes[1, 0].axis('off')

        # 直线
        axes[1, 1].imshow(self.gray, cmap='gray')
        if self.lines is not None and len(self.lines) > 0:
            for x1, y1, x2, y2 in self.lines:
                axes[1, 1].plot([x1, x2], [y1, y2], 'r-', linewidth=2)
        axes[1, 1].set_title(f'Lines ({len(self.lines or [])})')
        axes[1, 1].axis('off')

        # 圆
        axes[1, 2].imshow(self.gray, cmap='gray')
        if self.circles is not None and len(self.circles) > 0:
            for cx, cy, r in self.circles:
                circle = plt.Circle((cx, cy), r, fill=False, color='blue', linewidth=2)
                axes[1, 2].add_patch(circle)
        axes[1, 2].set_title(f'Circles ({len(self.circles or [])})')
        axes[1, 2].axis('off')

        plt.suptitle('Edge Detection Pipeline', fontsize=14)
        plt.tight_layout()
        if filename:
            plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()


def create_test_image(size: int = 200) -> np.ndarray:
    """创建测试图像: 圆+矩形+线条"""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    img[:] = [240, 240, 240]  # 灰色背景

    # 圆
    from skimage.draw import disk
    rr, cc = disk((80, 80), 40, shape=img.shape[:2])
    img[rr, cc] = [50, 50, 200]

    # 矩形
    from skimage.draw import rectangle
    rr, cc = rectangle(start=(100, 120), end=(160, 180), shape=img.shape[:2])
    img[rr, cc] = [200, 50, 50]

    # 对角线
    from skimage.draw import line
    rr, cc = line(20, 20, 180, 180)
    img[rr, cc] = [50, 200, 50]

    return img


def run_example():
    """示例: 图像边缘检测Pipeline"""
    print("=" * 60)
    print("图像边缘检测Pipeline示例")
    print("=" * 60)

    # 创建测试图像
    test_img = create_test_image(200)
    pipeline = EdgeDetectionPipeline(test_img)

    print(f"\n输入图像: {test_img.shape}")
    print(f"灰度图: {pipeline.gray.shape}")

    # Step 1: 预处理
    pipeline.preprocess(kernel_size=3)
    print(f"\nStep 1: 高斯滤波完成")

    # Step 2: Canny边缘检测
    edges = pipeline.canny_edge_detection(low_threshold=30, high_threshold=100)
    edge_ratio = np.sum(edges > 0) / edges.size
    print(f"Step 2: Canny边缘检测, 边缘像素比: {edge_ratio:.2%}")

    # Step 3: 轮廓提取
    contours = pipeline.extract_contours()
    print(f"Step 3: 提取到 {len(contours)} 个轮廓")

    # Step 4: 轮廓特征
    features = pipeline.compute_contour_features()
    print(f"Step 4: 轮廓特征:")
    for feat in features:
        print(f"  轮廓{feat['contour_id']}: 面积={feat['area']:.1f}, "
              f"周长={feat['perimeter']:.1f}, 紧凑度={feat['compactness']:.3f}")

    # Step 5: 直线检测
    lines = pipeline.detect_lines_hough(min_line_length=30)
    print(f"Step 5: 检测到 {len(lines)} 条直线")

    # Step 6: 圆检测
    circles = pipeline.detect_circles_hough(min_radius=15, max_radius=60)
    print(f"Step 6: 检测到 {len(circles)} 个圆")

    # 绘制Pipeline
    pipeline.plot_pipeline('figures/edge_detection_pipeline.png')
    print(f"\nPipeline可视化已保存: figures/edge_detection_pipeline.png")

    # 绘制最终结果
    result = pipeline.draw_results()
    plt.figure(figsize=(8, 8))
    plt.imshow(result)
    plt.title('Detection Results')
    plt.axis('off')
    plt.savefig('figures/edge_detection_results.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"检测结果已保存: figures/edge_detection_results.png")


if __name__ == "__main__":
    run_example()
