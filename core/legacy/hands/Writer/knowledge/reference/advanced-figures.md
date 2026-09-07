# 高级科研图表库（Advanced Figures）

> 借鉴开源科研绘图方案（sci-box 类）整理的**高阶图表配方**，供 figure-generator / code-implementer 在
> 需要超出基础折线/柱状图的表达时使用。所有图最终仍须遵守 `figure-rules.md` 的命名与 300 dpi 规范。

## 使用原则

1. **只在论文有对应分析文字时引入**（W4）；不为炫技加图。
2. 每张高阶图的数据必须来自 `figures/all_results.json`（数值可追溯铁律）。
3. 优先矢量输出（`.pdf`/`.svg`）；位图 ≥300 dpi。
4. 中文论文图中文字用中文（matplotlib 需设置中文字体，如 `SimHei`/`Microsoft YaHei`，并 `plt.rcParams['axes.unicode_minus'] = False`）。

## 图表清单

### 1. 技术路线图 / 研究框架图（开篇必备）

用 matplotlib 的 FancyBboxPatch 或 graphviz 绘制 3–5 层结构：**问题分析 → 数据处理 → 模型构建 → 求解验证 → 结论**。

```python
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

def tech_roadmap(layers: list[list[str]], out: str) -> str:
    """layers: 自上而下每层的节点文字列表。输出横向分层的流程图。"""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.axis("off")
    n = len(layers)
    for i, layer in enumerate(layers):
        y = 1 - (i + 0.5) / n
        m = len(layer)
        for j, text in enumerate(layer):
            x = (j + 0.5) / m
            box = FancyBboxPatch((x - 0.35 / m, y - 0.035), 0.7 / m, 0.07,
                                 boxstyle="round,pad=0.01",
                                 fc="#DCE9F7", ec="#2C5F8A", lw=1.2)
            ax.add_patch(box)
            ax.text(x, y, text, ha="center", va="center", fontsize=9)
        if i > 0:  # 层间连线
            ax.annotate("", xy=(0.5, y + 0.035), xytext=(0.5, y + 1 / n - 0.035),
                        arrowprops=dict(arrowstyle="->", color="#2C5F8A"))
    plt.tight_layout(); plt.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out
```

### 2. 灵敏度龙卷风图（Tornado）

单参数灵敏度按影响幅度排序，评审一眼看到哪个参数最关键。

```python
def tornado(params: list[str], lows: list[float], highs: list[float],
            base: float, out: str) -> str:
    order = sorted(range(len(params)), key=lambda i: -(highs[i] - lows[i]))
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    for k, i in enumerate(order):
        ax.barh(k, highs[i] - base, left=base, height=0.6, color="#C0504D", label="上调" if k == 0 else "")
        ax.barh(k, lows[i] - base, left=base, height=0.6, color="#4F81BD", label="下调" if k == 0 else "")
    ax.set_yticks(range(len(order))); ax.set_yticklabels([params[i] for i in order])
    ax.axvline(base, color="k", lw=0.8); ax.legend(); ax.invert_yaxis()
    plt.tight_layout(); plt.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out
```

### 3. Taylor 图（模型对比）

用相关系数 + 标准差比 + RMSE 一张图对比多个模型，常见于预测/仿真类论文。

```python
import numpy as np

def taylor(ref_std: float, models: dict[str, tuple[float, float]], out: str) -> str:
    """models: {name: (corr, model_std)}。极坐标半圆。"""
    fig = plt.figure(figsize=(7, 7), dpi=300)
    ax = fig.add_subplot(111, polar=True)
    ax.set_thetamin(0); ax.set_thetamax(90)
    ax.plot([0], [ref_std], "k*", ms=12, label="参考")
    for name, (r, s) in models.items():
        theta = np.arccos(np.clip(r, -1, 1))
        ax.plot([theta], [s], "o", ms=8, label=name)
    ax.set_title("Taylor 图（相关性-标准差）", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))
    plt.tight_layout(); plt.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out
```

### 4. 雨云图（Raincloud，分布对比）

箱线图 + 密度 + 抖动散点三合一，比单画箱线图信息量大得多。

```python
import numpy as np

def raincloud(groups: dict[str, np.ndarray], out: str) -> str:
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    rng = np.random.default_rng(42)
    for k, (name, data) in enumerate(groups.items()):
        ax.boxplot(data, positions=[k], widths=0.15, showfliers=False)
        # 半小提琴（密度）：用 hist 近似，保持零依赖
        counts, edges = np.histogram(data, bins=20)
        w = (edges[1] - edges[0])
        ax.barh((edges[:-1] + edges[1:]) / 2, counts / counts.max() * 0.3,
                height=w * 0.9, left=k + 0.12, color="#9DC3E6", alpha=0.7)
        ax.scatter(np.full(len(data), k) - 0.18 + rng.normal(0, 0.02, len(data)),
                   data, s=6, alpha=0.35, color="#2C5F8A")
    ax.set_xticks(range(len(groups))); ax.set_xticklabels(groups.keys())
    plt.tight_layout(); plt.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out
```

### 5. 桑基图（Sankey，流量/去向）

适合能源流、资金流、转化漏斗。matplotlib 自带 `Sankey`：

```python
from matplotlib.sankey import Sankey

def sankey(flows: list[float], labels: list[str], out: str) -> str:
    fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
    sankey = Sankey(ax=ax, scale=1.0, offset=0.3, unit="")
    sankey.add(flows=flows, labels=labels, pathlengths=[0.25] * len(flows))
    sankey.finish(); ax.set_title("流量结构"); ax.axis("off")
    plt.tight_layout(); plt.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out
```

### 6. 热力图 + 显著性标注（相关矩阵/混淆矩阵）

```python
import numpy as np

def annotated_heatmap(matrix: np.ndarray, xlabels: list[str], ylabels: list[str],
                      out: str, cmap: str = "RdBu_r", fmt: str = "{:.2f}") -> str:
    fig, ax = plt.subplots(figsize=(0.9 * len(xlabels) + 2, 0.9 * len(ylabels) + 2), dpi=300)
    im = ax.imshow(matrix, cmap=cmap, vmin=-np.abs(matrix).max(), vmax=np.abs(matrix).max())
    ax.set_xticks(range(len(xlabels))); ax.set_xticklabels(xlabels, rotation=45, ha="right")
    ax.set_yticks(range(len(ylabels))); ax.set_yticklabels(ylabels)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(j, i, fmt.format(matrix[i, j]), ha="center", va="center",
                    color="w" if abs(matrix[i, j]) > 0.6 * np.abs(matrix).max() else "k", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.8)
    plt.tight_layout(); plt.savefig(out, bbox_inches="tight"); plt.close(fig)
    return out
```

### 7. SHAP 风格特征重要性（可解释性）

机器学习模型结论的支撑图。**数值必须来自实际计算**（如 `shap` 库或手动置换重要性），禁止手工编造条形。

### 8. 收敛曲线 + 多算法对比（优化类）

同一坐标轴画 ≥2 种算法的收敛曲线（纵轴对数刻度），并标注最终值；与 `all_results.json` 中的迭代记录一致。

## 选型速查

| 论文诉求 | 推荐图 |
|---|---|
| 展示整体思路 | 技术路线图（1） |
| 说明关键参数 | 龙卷风图（2） |
| 多模型预测对比 | Taylor 图（3）+ 收敛曲线（8） |
| 组间分布差异 | 雨云图（4） |
| 结构/流向占比 | 桑基图（5）或堆叠面积 |
| 变量关系总览 | 标注热力图（6） |
| 黑盒模型解释 | SHAP（7） |

## 色觉友好编码规范

> 约 8% 男性有色觉异常（红绿色盲为主）。科研图表必须保证**色盲读者也能区分所有数据系列**。

### 调色板

| 场景 | 推荐 | 禁用 |
|---|---|---|
| 分类色（≤8 类） | Okabe-Ito：`#0072B2 #E69F00 #009E73 #CC79A7 #56B4E9 #D55E00 #F0E442 #000000` | 彩虹色 jet/rainbow、红绿对 |
| 连续色（热力图/等高线） | `cividis`（色觉障碍设计）、`viridis` | `jet` `hot` `cool` `spring` |
| 发散色（正负对比） | `RdBu`（蓝红）、`PuOr`（橙紫） | 纯红绿 `RdGy` 对色盲不友好 |

```python
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73", "#CC79A7",
             "#56B4E9", "#D55E00", "#F0E442", "#000000"]
```

### 双编码原则

**颜色 + 形状/线型同时编码**，确保灰度打印也可区分：

```python
MARKERS = ["o", "s", "^", "D", "v", "<", ">", "p"]
LINESTYLES = ["-", "--", "-.", ":", "-", "--", "-.", ":"]

def plot_series(ax, x, ys: dict[str, list], **kw):
    for i, (name, y) in enumerate(ys.items()):
        ax.plot(x, y, color=OKABE_ITO[i % len(OKABE_ITO)],
                marker=MARKERS[i % len(MARKERS)],
                linestyle=LINESTYLES[i % len(LINESTYLES)],
                label=name, **kw)
    ax.legend()
```

### 灰度可区分性验证

生成灰度版本检查各系列是否仍可区分（标准差 > 阈值）：

```python
from PIL import Image
import numpy as np

def check_grayscale_distinguishable(img_path: str, n_series: int, min_std: float = 10.0) -> bool:
    img = Image.open(img_path).convert("L")
    arr = np.array(img)
    # 采样各系列区域的标准差（简化：按行分块）
    chunks = np.array_split(arr, n_series, axis=0)
    means = [c.mean() for c in chunks]
    return np.std(means) >= min_std
```

## 出版级输出（SVG + 300DPI 双导出）

### 统一导出函数

```python
import matplotlib.pyplot as plt

PUB_WIDTHS = {"single": 8.0, "onehalf": 11.0, "double": 14.0}  # cm → inch
PUB_DPI = 300

def save_figure(fig, name: str, width_cm: float = 8.0, formats: tuple = ("svg", "pdf", "png")):
    """统一导出：矢量（svg/pdf）+ 位图（png@300dpi）。"""
    w_inch = width_cm / 2.54
    fig.set_size_inches(w_inch, w_inch * 0.618)  # 黄金比例高
    for fmt in formats:
        dpi = PUB_DPI if fmt == "png" else None
        fig.savefig(f"{name}.{fmt}", dpi=dpi, bbox_inches="tight",
                    pad_inches=0.05, metadata={"Creator": "MathModelSkills"})
    plt.close(fig)
```

### 出版风格预设

```python
def pub_style():
    plt.rcParams.update({
        "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
        "xtick.labelsize": 8, "ytick.labelsize": 8, "legend.fontsize": 8,
        "figure.dpi": 300, "savefig.dpi": 300,
        "axes.linewidth": 0.8, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "font.family": "serif",
        "mathtext.fontset": "stix",
        "axes.grid": False,
    })
```

### LaTeX 嵌入建议

```latex
% 单栏图（8cm 宽）
\includegraphics[width=8cm]{figures/result.svg}

% 双栏图（14cm 宽）
\includegraphics[width=14cm]{figures/compare.pdf}
```

优先使用 `.pdf`/`.svg` 矢量格式；仅在投稿系统不支持矢量时使用 `.png@300dpi`。

## 图表自检闭环

> 每张图生成后自动跑自检，不合格则重试或报警。由 figure-generator 和 final-validator 消费。

### 单图自检

```python
import os
import struct

def self_check_figure(path: str, min_dpi: int = 300, min_bytes: int = 5000,
                      max_bytes: int = 10_000_000) -> dict:
    """返回 {ok, errors, warnings}。"""
    errors, warnings = [], []
    if not os.path.exists(path):
        return {"ok": False, "errors": [f"文件不存在: {path}"], "warnings": []}
    size = os.path.getsize(path)
    if size < min_bytes:
        errors.append(f"文件过小 ({size}B < {min_bytes}B)，可能为空图或损坏")
    if size > max_bytes:
        warnings.append(f"文件过大 ({size}B > {max_bytes}B)，投稿系统可能拒收")

    ext = os.path.splitext(path)[1].lower()
    if ext == ".png":
        with open(path, "rb") as f:
            f.read(8)  # PNG signature
            # IHDR chunk: width(4) height(4) bitdepth(1) colortype(1) ...
            f.read(4)  # IHDR length
            f.read(4)  # "IHDR"
            w = struct.unpack(">I", f.read(4))[0]
            h = struct.unpack(">I", f.read(4))[0]
        if w < 400 or h < 300:
            warnings.append(f"分辨率偏低 ({w}x{h})，打印可能模糊")
    elif ext in (".svg", ".pdf", ".eps"):
        pass  # 矢量格式无需 DPI 检查
    else:
        warnings.append(f"非标准格式: {ext}")

    return {"ok": len(errors) == 0, "errors": errors, "warnings": warnings}
```

### 批量自检（投稿前）

```python
def batch_check_figures(figures_dir: str) -> dict:
    """扫描 figures/ 下所有图片，返回汇总报告。"""
    results = {"total": 0, "pass": 0, "fail": 0, "warn": 0, "details": []}
    if not os.path.isdir(figures_dir):
        return results
    for fname in sorted(os.listdir(figures_dir)):
        ext = os.path.splitext(fname)[1].lower()
        if ext not in (".png", ".jpg", ".svg", ".pdf", ".eps"):
            continue
        path = os.path.join(figures_dir, fname)
        r = self_check_figure(path)
        results["total"] += 1
        if r["ok"]:
            results["pass"] += 1
        else:
            results["fail"] += 1
        if r["warnings"]:
            results["warn"] += 1
        results["details"].append({"file": fname, **r})
    return results
```

### 色盲模拟（可选）

对 PNG 图做红绿色盲模拟，检查关键区域是否仍可区分：

```python
def simulate_deuteranopia(img_path: str, out_path: str) -> str:
    """简化版红绿色盲模拟（绿色→红色通道混合）。"""
    from PIL import Image
    import numpy as np
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    # 简化矩阵：deuteranopia 近似
    r = 0.625 * arr[:, :, 0] + 0.375 * arr[:, :, 1]
    g = 0.7 * arr[:, :, 0] + 0.3 * arr[:, :, 1]
    b = arr[:, :, 2]
    result = np.stack([r, g, b], axis=2).clip(0, 255).astype(np.uint8)
    Image.fromarray(result).save(out_path)
    return out_path
```

## 禁止事项

- 禁止用图表承载论文未分析的结论（评审反模式：图当主体）。
- 禁止截图外部工具的低分辨率位图。
- 禁止手绘数据点（所有坐标值必须可追溯到 `all_results.json`）。
- 禁止使用 `jet`/`rainbow` 等非色觉友好 colormap。
- 禁止仅靠颜色区分数据系列（必须同时用形状/线型双编码）。
