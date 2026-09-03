# 科学图表模板库（FIGURE-TEMPLATE-INDEX）

> 来源：借鉴 MathModelAgent-main `skills/mathmodel-figure-templates/SKILL.md` 与 opendraft 的可视化规范。
> 用途：figure-generator agent 在生成图表时按类型选择对应模板。
> 配色常量：所有模板统一使用 `core/templates/figures/matplotlib_style_constants.py` 中的 `COLORS`。

---

## 快速选型

| 数据类型 | 推荐图 | 避免使用 | 模板路径 |
|---------|--------|---------|---------|
| 趋势/时序 | 折线图+置信带 | 纯折线无 CI | `templates/figures/template_line_ci.py` |
| 分布比较 | 箱线图/小提琴图 | 柱状图+误差棒 | `templates/figures/template_box_violin.py` |
| 相关性 | 散点图+回归线+r值 | 只有散点 | `templates/figures/template_scatter_reg.py` |
| 分类对比 | 水平条形图 | 3D 柱状图 | `templates/figures/template_hbar.py` |
| 参数敏感性 | 热力图/等高线 | 多条折线堆叠 | `templates/figures/template_heatmap.py` |
| 后验分布 | 密度图/直方图+KDE | 只有点估计 | `templates/figures/template_kde.py` |
| 模型对比 | 分组柱状图 | 饼图（≥5类）| `templates/figures/template_grouped_bar.py` |
| 流程/示意 | DrawIO/框架图 | 数据图冒充流程图 | 使用 diagram_gen.py |

---

## 配色常量（全局统一）

所有 matplotlib 图表使用以下常量（存储在 `matplotlib_style_constants.py`）：

```python
COLORS = {
    "primary":   "#2E5B88",   # 主色（蓝）
    "secondary": "#E85D4C",   # 辅色（红）
    "tertiary":  "#4A9B7F",   # 辅色（绿）
    "neutral":   "#7F7F7F",   # 灰色（参考线）
    "light":     "#B8D4E8",   # 浅色（背景带）
}

# 尺寸模板
FIG_SINGLE = (5, 4)     # 单图
FIG_DOUBLE = (10, 4)    # 并排双图
FIG_WIDE   = (8, 3)     # 宽图（时序）
FIG_SQUARE = (6, 6)     # 方形图（热力图/相关矩阵）
```

## 全局 rcParams

```python
import matplotlib.pyplot as plt
plt.rcParams.update({
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "legend.frameon": False,
    "font.size": 10,
})
# 中文论文加：
# plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
```

---

## 图表类型选择速查

| 场景 | 推荐 | 原因 |
|------|------|------|
| 展示某量随时间/参数变化 | 折线图+置信带 | 直观显示趋势与不确定性 |
| 比较组间分布差异 | 箱线图/小提琴图 | 同时展示中位数、四分位、异常值 |
| 展示两变量关系 | 散点图+回归线 | 相关系数一目了然 |
| 多模型/方案指标对比 | 分组柱状图 | 精确比较数值 |
| 两参数联合影响 | 热力图/等高线 | 二维敏感性全景展示 |
| 单变量分布形态 | 密度图+直方图+KDE | 完整分布信息 |
| 算法流程/模型结构 | DrawIO 框架图 | 清晰展示模块间关系 |

---

## 图表数据特征 print 规范

每张图生成后，必须用 `print()` 输出该图的关键数据特征，供论文撰写引用：

```python
# 时序图
print("【图X数据特征 - 时序】")
print(f"    时间范围: {x.min()} 至 {x.max()}")
print(f"    起点值: {y[0]:,.2f}, 终点值: {y[-1]:,.2f}")
print(f"    峰值: {y.max():,.2f}, 谷值: {y.min():,.2f}")
print(f"    整体趋势: {'上升' if y[-1] > y[0] else '下降'}")

# 模型拟合图
print("【图X数据特征 - 模型拟合】")
print(f"    R²: {r2:.4f}")
print(f"    MAE: {mae:.4f}, RMSE: {rmse:.4f}")

# 预测图（含置信区间）
print("【图X数据特征 - 预测结果】")
print(f"    点预测值: {prediction:,.2f}")
print(f"    95%置信区间: [{ci_lower:,.2f}, {ci_upper:,.2f}]")
```

---

## 禁止清单

1. 禁止 3D 可视化（失真）
2. 禁止雷达图（评审反感）
3. 禁止饼图≥5 类（难比较）
4. 禁止表格单元格 >300 字符（转正文段落）
5. 禁止连续 3+ 图无正文间隔
6. 禁止图后不输出数据特征（print 规范）
