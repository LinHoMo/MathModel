"""箱线图+散点图模板（分布对比）— box_strip.py

数据来源：`figures/all_results.json`
用途：多组分布对比、结果稳定性比较
全局样式：`matplotlib_style_constants.py`
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from core.templates.figures.matplotlib_style_constants import (
    COLORS, PALETTE, FIG_SINGLE, RC_PARAMS, apply_style,
)

apply_style()


def plot_box_strip(
    data_dict: dict[str, np.ndarray | list[float]],
    xlabel: str = "类别",
    ylabel: str = "指标值",
    title: str | None = None,
    show_points: bool = True,
    save_path: str | Path = "paper/figures/fig_boxplot.png",
) -> str:
    """箱线图 + 原始散点覆盖。

    Args:
        data_dict: {组名: 数据数组}

    Returns:
        保存路径（字符串）
    """
    labels = list(data_dict.keys())
    values = [np.asarray(v) for v in data_dict.values()]

    fig, ax = plt.subplots(figsize=FIG_SINGLE)

    # 箱线图
    bp = ax.boxplot(
        values, labels=labels, patch_artist=True,
        boxprops=dict(facecolor=COLORS["light"], color=COLORS["primary"]),
        medianprops=dict(color=COLORS["primary"], lw=2),
        whiskerprops=dict(color=COLORS["primary"]),
        capprops=dict(color=COLORS["primary"]),
        flierprops=dict(marker="o", markerfacecolor=COLORS["secondary"], ms=4),
    )

    # 散点覆盖
    if show_points:
        for i, vals in enumerate(values, start=1):
            jitter = np.random.default_rng(42).normal(0, 0.04, size=len(vals))
            ax.scatter(
                np.full(len(vals), i) + jitter, vals,
                color=COLORS["primary"], alpha=0.6, s=20, zorder=5,
            )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("【图X数据特征 - 分布对比】")
    for name, vals in zip(labels, values):
        arr = np.asarray(vals)
        print(f"    [{name}] 中位数={np.median(arr):.2f}, IQR=[{np.percentile(arr,25):.2f},{np.percentile(arr,75):.2f}], n={len(arr)}")

    return str(save_path)


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    data = {
        "方法 A": rng.normal(0.82, 0.05, 30),
        "方法 B": rng.normal(0.75, 0.08, 30),
        "方法 C": rng.normal(0.88, 0.03, 30),
    }
    plot_box_strip(data, title="三种方法准确率对比", ylabel="准确率")
    print("Saved: paper/figures/fig_boxplot.png")
