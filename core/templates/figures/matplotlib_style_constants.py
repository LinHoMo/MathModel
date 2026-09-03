"""matplotlib 科学图表配色与尺寸常量

来源：借鉴 MathModelAgent-main backend/app/tools/matplotlib_setup.py
用途：所有 figure-generator 产物统一引用此模块的常量
"""

# 竞赛向配色常量（色盲友好，灰度可区分）
COLORS = {
    "primary":   "#2E5B88",   # 主色（蓝）
    "secondary": "#E85D4C",   # 辅色（红）
    "tertiary":  "#4A9B7F",   # 辅色（绿）
    "neutral":   "#7F7F7F",   # 灰色（参考线/边框）
    "light":     "#B8D4E8",   # 浅色（置信带/填充）
    "accent1":   "#E8A838",   # 强调色（橙）
    "accent2":   "#9B59B6",   # 强调色（紫）
}

# 色板列表（多序列时按序取用）
PALETTE = [
    COLORS["primary"],
    COLORS["secondary"],
    COLORS["tertiary"],
    COLORS["accent1"],
    COLORS["accent2"],
]

# 尺寸模板（单位：英寸；避免"大图综合征"）
FIG_SINGLE = (5, 4)     # 单图
FIG_DOUBLE = (10, 4)    # 并排双图
FIG_WIDE   = (8, 3)     # 宽图（时序）
FIG_SQUARE = (6, 6)     # 方形图（热力图/相关矩阵）
FIG_LARGE  = (7, 5)     # 大图（主结果图）

# 全局 rcParams（复制到图表脚本顶部使用）
RC_PARAMS = {
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": True,
    "axes.spines.bottom": True,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "legend.frameon": False,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.grid": False,
}


def apply_style(font_family=None):
    """应用全局样式，可选指定中文字体"""
    import matplotlib.pyplot as plt
    plt.rcParams.update(RC_PARAMS)
    if font_family:
        plt.rcParams["font.sans-serif"] = [font_family]
        plt.rcParams["axes.unicode_minus"] = False
