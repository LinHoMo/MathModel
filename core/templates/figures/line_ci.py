"""时序图模板（折线+置信带）— line_ci.py

数据来源：`figures/all_results.json`
用途：时序演变、迭代收敛、曲线走势
全局样式：`matplotlib_style_constants.py`
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from core.templates.figures.matplotlib_style_constants import (
    COLORS, PALETTE, FIG_SINGLE, RC_PARAMS, apply_style,
)

apply_style()


def plot_time_series_ci(
    x: np.ndarray,
    y: np.ndarray,
    y_lower: np.ndarray | None = None,
    y_upper: np.ndarray | None = None,
    label: str = "数值",
    xlabel: str = "时间 / s",
    ylabel: str = "幅值",
    title: str | None = None,
    save_path: str | Path = "paper/figures/fig_timeline.png",
) -> str:
    """时序折线 + 可选置信带。

    Returns:
        保存路径（字符串）
    """
    fig, ax = plt.subplots(figsize=FIG_SINGLE)
    ax.plot(x, y, color=COLORS["primary"], lw=2, label=label, marker="o", ms=4)

    if y_lower is not None and y_upper is not None:
        ax.fill_between(
            x, y_lower, y_upper,
            color=COLORS["light"], alpha=0.6, label="95% 置信带",
        )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.legend(frameon=False)
    ax.grid(True, alpha=0.3, linestyle="--")

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    # 数据特征输出（铁律：每图必出）
    print("【图X数据特征 - 时序】")
    print(f"    起点值: {y[0]:,.2f}, 终点值: {y[-1]:,.2f}")
    print(f"    峰值: {y.max():,.2f} at x={x[np.argmax(y)]:.2f}")
    print(f"    谷值: {y.min():,.2f} at x={x[np.argmin(y)]:.2f}")
    print(f"    均值±标准差: {y.mean():.2f} ± {y.std():.2f}")
    if y_lower is not None and y_upper is not None:
        ci_width = (y_upper - y_lower).mean()
        print(f"    平均置信带宽: {ci_width:.2f}")

    return str(save_path)


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    x = np.linspace(0, 10, 50)
    y = np.sin(x) * np.exp(-x / 8) + rng.normal(0, 0.02, 50)
    ci = 0.05 + 0.03 * np.random.random(50)
    plot_time_series_ci(x, y, y - ci, y + ci, label="衰减振荡曲线")
    print("Saved: paper/figures/fig_timeline.png")
