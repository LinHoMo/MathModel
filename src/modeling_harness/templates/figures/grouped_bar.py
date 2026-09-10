"""分组柱状图模板 — grouped_bar.py（多方法/多方案对比）

数据来源：`figures/all_results.json`
用途：多种方法、多种方案在同一指标上的对比
全局样式：`matplotlib_style_constants.py`
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from core.templates.figures.matplotlib_style_constants import (
    COLORS, PALETTE, FIG_DOUBLE, RC_PARAMS, apply_style,
)

apply_style()


def plot_grouped_bar(
    categories: list[str],
    series_dict: dict[str, np.ndarray | list[float]],
    ylabel: str = "指标值",
    title: str | None = None,
    show_values: bool = True,
    save_path: str | Path = "paper/figures/fig_grouped_bar.png",
) -> str:
    """分组柱状图（多系列并列对比）。

    Args:
        categories: X 轴类别列表
        series_dict: {系列名: 每类别值数组}

    Returns:
        保存路径（字符串）
    """
    n_cat = len(categories)
    n_series = len(series_dict)
    x = np.arange(n_cat)
    width = 0.8 / n_series

    fig, ax = plt.subplots(figsize=FIG_DOUBLE)
    for i, (name, vals) in enumerate(series_dict.items()):
        offset = (i - n_series / 2 + 0.5) * width
        bars = ax.bar(
            x + offset, vals, width, label=name,
            color=PALETTE[i % len(PALETTE)], edgecolor="white", linewidth=0.5,
        )
        if show_values:
            for bar, val in zip(bars, vals):
                ax.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{val:.2f}", ha="center", va="bottom", fontsize=8,
                )

    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.legend(frameon=False, ncol=min(n_series, 3))
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax.set_axisbelow(True)

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("【图X数据特征 - 多方案对比】")
    for name, vals in series_dict.items():
        arr = np.asarray(vals)
        print(f"    [{name}] 均值={arr.mean():.2f}, 最大值={arr.max():.2f} at [{categories[np.argmax(arr)]}]")
    best_per_cat = {cat: max(series_dict.keys(), key=lambda k: series_dict[k][i]) for i, cat in enumerate(categories)}
    from collections import Counter
    win_counts = Counter(best_per_cat.values())
    print(f"    各方案最优次数: {dict(win_counts)}")

    return str(save_path)


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    categories = ["准确率", "召回率", "F1", "AUC"]
    series = {
        "方法 A": rng.uniform(0.75, 0.92, 4),
        "方法 B": rng.uniform(0.68, 0.85, 4),
        "方法 C": rng.uniform(0.80, 0.95, 4),
    }
    plot_grouped_bar(categories, series, ylabel="得分", title="三种方法四指标对比")
    print("Saved: paper/figures/fig_grouped_bar.png")
