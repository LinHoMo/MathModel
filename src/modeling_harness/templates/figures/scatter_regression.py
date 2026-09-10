"""散点+回归图模板 — scatter_regression.py

数据来源：`figures/all_results.json`
用途：相关性分析、拟合效果展示、误差分布
全局样式：`matplotlib_style_constants.py`
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from core.templates.figures.matplotlib_style_constants import (
    COLORS, PALETTE, FIG_SINGLE, RC_PARAMS, apply_style,
)

apply_style()


def plot_scatter_regression(
    x: np.ndarray,
    y: np.ndarray,
    label: str = "样本",
    xlabel: str = "X",
    ylabel: str = "Y",
    title: str | None = None,
    show_eq: bool = True,
    save_path: str | Path = "paper/figures/fig_scatter.png",
) -> str:
    """散点图 + 线性回归拟合 + 统计标注。

    Returns:
        保存路径（字符串）
    """
    x = np.asarray(x)
    y = np.asarray(y)
    # 去除 NaN
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

    fig, ax = plt.subplots(figsize=FIG_SINGLE)
    ax.scatter(x, y, color=COLORS["primary"], alpha=0.6, s=30, label=label, edgecolors="white", linewidth=0.5)

    # 回归线
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, slope * x_line + intercept, color=COLORS["secondary"], lw=2, label="线性拟合")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)

    # 统计标注
    if show_eq:
        eq_text = f"$y = {slope:.3f}x + {intercept:.3f}$\n$R^2 = {r_value**2:.4f}$, $p = {p_value:.2e}$"
        ax.text(0.05, 0.92, eq_text, transform=ax.transAxes, fontsize=10,
                verticalalignment="top", bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.5))

    ax.legend(frameon=False)
    ax.grid(True, alpha=0.3, linestyle="--")

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("【图X数据特征 - 模型拟合】")
    print(f"    R²={r_value**2:.4f}, MAE={np.mean(np.abs(y - (slope*x + intercept))):.4f}")
    print(f"    斜率={slope:.4f} ± {std_err:.4f}, 截距={intercept:.4f}")
    print(f"    p 值={p_value:.2e} {'(<0.05 显著)' if p_value < 0.05 else '(不显著)'}")
    print(f"    样本数={len(x)}, X∈[{x.min():.2f}, {x.max():.2f}], Y∈[{y.min():.2f}, {y.max():.2f}]")

    return str(save_path)


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    x = rng.uniform(0, 10, 50)
    y = 2.5 * x + 3.0 + rng.normal(0, 2, 50)
    plot_scatter_regression(x, y, xlabel="预测值", ylabel="实测值", title="预测-实测散点与拟合")
    print("Saved: paper/figures/fig_scatter.png")
