"""热力图模板 — heatmap.py（灵敏度矩阵/交叉结果）

数据来源：`figures/all_results.json`
用途：参数灵敏度矩阵、指标交叉对比、热力分布
全局样式：`matplotlib_style_constants.py`
"""

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from core.templates.figures.matplotlib_style_constants import (
    COLORS, PALETTE, FIG_SQUARE, RC_PARAMS, apply_style,
)

apply_style()


def plot_heatmap(
    matrix: np.ndarray,
    row_labels: list[str],
    col_labels: list[str],
    fmt: str = ".2f",
    cmap: str = "Blues",
    xlabel: str = "参数",
    ylabel: str = "输出指标",
    title: str | None = None,
    save_path: str | Path = "paper/figures/fig_heatmap.png",
) -> str:
    """二维数值热力图，单元格内标注数值。

    Returns:
        保存路径（字符串）
    """
    fig, ax = plt.subplots(figsize=FIG_SQUARE)
    im = ax.imshow(matrix, cmap=cmap, aspect="auto", vmin=np.nanmin(matrix), vmax=np.nanmax(matrix))

    ax.set_xticks(range(len(col_labels)))
    ax.set_yticks(range(len(row_labels)))
    ax.set_xticklabels(col_labels, rotation=45, ha="right")
    ax.set_yticklabels(row_labels)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)

    # 单元格数值标注
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            if not np.isnan(val):
                color = "white" if val > np.nanmean(matrix) else "black"
                ax.text(j, i, f"{val:{fmt}}", ha="center", va="center", color=color, fontsize=9)

    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()

    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("【图X数据特征 - 灵敏度热力】")
    print(f"    矩阵最大={np.nanmax(matrix):.4f} at ({np.unravel_index(np.nanargmax(matrix), matrix.shape)})")
    print(f"    矩阵最小={np.nanmin(matrix):.4f} at ({np.unravel_index(np.nanargmin(matrix), matrix.shape)})")
    print(f"    矩阵均值={np.nanmean(matrix):.4f}, 标准差={np.nanstd(matrix):.4f}")
    print(f"    整体变异系数={np.nanstd(matrix) / abs(np.nanmean(matrix)):.2%}")

    return str(save_path)


if __name__ == "__main__":
    rng = np.random.default_rng(42)
    matrix = rng.uniform(0.1, 0.9, (4, 5))
    plot_heatmap(
        matrix,
        row_labels=[f"指标{i+1}" for i in range(4)],
        col_labels=["-20%", "-10%", "基准", "+10%", "+20%"],
        title="参数灵敏度矩阵",
    )
    print("Saved: paper/figures/fig_heatmap.png")
