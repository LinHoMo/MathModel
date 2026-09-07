# 图表规范（figure-rules.md）

> 图表是论文的"第二语言"。好的图表让结论一目了然，坏的图表让评委怀疑你的专业水平。
> 来源：Beacon Figure 评审体系（5维Nature级） + Modex figure_check.sh + Nature/Science 标准。

---

## 一、命名与引用规范

### 文件命名
- 格式：`fig_问题编号_序号.png`（如 `fig1_1.png`、`fig2_3.png`）
- 不用中文文件名（LaTeX 兼容性）
- 不用空格或特殊字符

### 图题规范
- 格式：`图 N 描述——（结论）`，结论部分点明从图中读出的关键信息
- 长度 ≤ 15 个中文字符（图题只是标签）
- **绝对禁止**图题中的 `$...$` 公式——Word 引擎无法解析
- LaTeX 中：`\caption{图 N 描述}`

---

## 二、格式规范

### 基础要求
- 矢量优先（PDF/EPS，LaTeX 首选）；位图 ≥ 300 dpi（打印）/ ≥ 150 dpi（屏幕）
- 字体嵌入，中文用 SimSun/SimHei（或 LaTeX 同款），西文与数学用 LaTeX 同款
- 字号 ≥ 9pt（坐标轴标签）/ ≥ 10pt（图例）
- 线条 ≥ 1pt
- 导出尺寸适合单栏（约 8-10 cm 宽）或双栏（约 16-18 cm 宽）

### 配色规范
- 配色 ≤ 3 色系
- **禁止**：matplotlib 默认 tab10、CSS 颜色名 `'blue'` `'red'`、`RdYlGn` 红绿灯配色、彩虹色
- **推荐**：学术配色方案（见 `plot_utils.py` 的 9 套配色）
  - Nature elegant: `#7AAEC8`（dusty-blue）/ `#E8945A`（warm-orange）/ `#7BC8A4`（mint）/ `#9B8EC4`（lavender）
  - NEJM: `#D55E00` / `#0072B2` / `#009E73` / `#CC79A7`
  - Science: `#0072B5` / `#E18727` / `#20854C` / `#BC3C29`
- 色盲友好：避免红绿同时作为对比色

### 图表必备元素
- 坐标轴标签 + 单位（中文：`时间 (s)`，英文：`Time (s)`）
- Legend（中文：`本文方法` `对比方法`）——Legend 不遮挡数据
- 网格线（alpha ≤ 0.3，仅主刻度）
- 标注文字用中文（仅变量符号用英文/LaTeX 数学模式）

### 禁止项
- `plt.title()` — 论文图不在图内放标题（图题在 `\caption{}` 中）
- 饼图 — 改横向柱状图（饼图在学术中已被淘汰）
- 3D 图 — 除非三维是信息本身而非装饰
- 无意义装饰（皮肤/渐变色/阴影效果）

---

## 三、内容规范

### 核心原则
**一张图只回答一个问题** —— 如果一张图试图回答两个问题，拆成两张。

### 图表角色分配（生成前填写）
| 字段 | 示例 |
|------|------|
| 论证角色 | "改进方法的精度优势" |
| 一句话结论 | "改进方法的 RMSE 较 baseline 降低 23%" |
| 数据来源 | `code/q2_main.py` 第 45-78 行 |

### 坐标轴
- 量纲与单位齐全
- 刻度字体清晰可读
- 对数轴标注为 \(10^0, 10^1, ...\)

### 图例
- 中文：`本文方法` `对比方法 A` `基准方法`
- 英文：`Proposed` `Baseline` `Method A`
- 位置：不遮挡数据（优先右上/右下/图外）

---

## 四、五维度图表评审标准（Nature 级）

| 维度 | 满分 | 评分标准 |
|------|------|---------|
| 自解释性 | 2 | 2=不看正文也能理解；1=需配合正文；0=完全看不懂 |
| 规范性 | 2 | 2=坐标轴/单位/legend/字号全部规范；1=有 1-2 处不规范；0=严重不规范 |
| 信息量 | 2 | 2=信息密度恰如其分；1=偏多或偏少；0=信息缺失或过度堆砌 |
| 准确性 | 2 | 2=数据完全对应 stdout；1=有小偏差；0=数据与代码不一致 |
| 美观性 | 2 | 2=配色/布局/字体专业；1=基本可观；0=中小学生作图水平 |

**通过线**：总分 ≥ 7 且维度 1、4 各 ≥ 1.5 分。

---

## 五、不同图表类型的专项规范

### 折线图
- 线条 ≥ 1.5pt
- 不同方法用不同线型+颜色（实线/虚线/点划线）
- 标注关键数据点
- X 轴均匀刻度（除非对数轴）

### 散点图
- 点大小适中（`s=20-40`）
- 透明度 0.6-0.8（大量点避免重叠遮蔽）
- 有趋势线时标注 \(R^2\) 和 p 值

### 柱状图
- 柱子宽度适中（`width=0.6-0.8`）
- 不同组用不同颜色（≤3 色）
- 误差线显示 95% CI 或 ±1 SD
- 横向柱状图优于纵向（标签长时）

### 热力图
- Colorbar 标注物理含义
- 颜色映射用 `viridis` `plasma` `cividis`（色盲友好）
- 标注关键格子的数值

### 流程图/架构图
- 严格遵循 `drawio-rules.md`（11 条零容忍规则）或 `tikz-rules.md`
- 导出为 PNG（DOCX 兼容）或 PDF（LaTeX 兼容）
- 中文节点宽度根据字符数计算（见 `tikz-rules.md` 公式）

### 方案对比表
- LaTeX：三线表（`\toprule` `\midrule` `\bottomrule`）
- Markdown：`|---|---|` 分离行
- 数值来源：`figures/all_results.json`（不手写）

---

## 六、数据特征输出规范（LLM 看图方案）

绘制每张图后，必须在代码中 `print()` 结构化的数据特征摘要：

```python
print(f"FIGURE_SUMMARY: fig_03_velocity_profile.png")
print(f"  Type: time series line plot")
print(f"  X: Time (s), range 0-300")
print(f"  Y: Velocity (m/s), range 0.8-1.4")
print(f"  Key observations: velocity peaks at t≈50s (1.38 m/s)")
print(f"  Anomalies: none")
```

这样 LLM 虽然"看"不到图，但可以基于这些摘要写文字解读。

---

## 七、自动检查

使用项目统一校验脚本：
```bash
# 图表引用一致性 / 视觉质量 / 数据追溯统一由项目校验覆盖
py validate_project.py --project projects/<项目>
```

---

## 八、常见图表错误速查

| 错误 | 正确做法 |
|------|---------|
| 坐标轴无单位 | 加单位，如 `速度 (m/s)` |
| Legend 遮挡数据 | 移到右上角或图外 |
| 饼图 | 改横向柱状图 |
| 3D 柱状图 | 改 2D 分组柱状图 |
| matplotlib 默认配色 | 使用学术配色方案 |
| 字体太小看不清 | 最小 9pt |
| 标题在图中 | 移到 `\caption{}` |
| 图题有 `$x^2$` 公式 | 改为文字描述 |
| 只有一张图没有比较 | 加 baseline 对照 |
| 所有图同一颜色 | 不同方法不同颜色 |

## 附录 A: 图表尺寸标准表

| 期刊 | 单栏宽度 | 双栏宽度 | 字号 | 行宽 |
|------|---------|---------|------|------|
| Nature | 89 mm (3.5") | 183 mm (7.2") | 5-7 pt | 0.5 pt |
| IEEE | 3.5" | 7.16" | 8 pt | 0.5 pt |
| Science | 2.2-3.7" | 4.5-7.0" | 5-7 pt | 0.5 pt |
| Elsevier | 3.5" (单栏) | 7.0" (双栏) | 8 pt | 0.5 pt |

- 学术配色建议使用色盲友好、黑白打印也清晰的色板（如 matplotlib 的 `tab10` / `Set2`）

## 附录 B: caption 引用规范

### \label 命名约定
- 图: `\label{fig:short_description}`（如 `\label{fig:risk_surface}`）
- 表: `\label{tab:short_description}`（如 `\label{tab:bmi_groups}`）
- 算法: `\label{alg:short_description}`

### 引用语法
- 图: `图~\ref{fig:xxx}`（波浪号防止换行）
- 表: `表~\ref{tab:xxx}`
- 算法: `算法~\ref{alg:xxx}`

### 禁止
- 直接写 `图1`、`表2`（应使用 \ref）
- \label 与 \ref 不匹配（由 figure_caption_check.py 检测）
- 未引用的 figure（每个 figure 必须在正文引用至少一次）

---

## 九、R7 新增专项规范

### 9.1 双 y 轴规范

双 y 轴用于同一图表中展示两个量纲不同的时间序列（如左轴温度、右轴湿度）。

#### 配色规范
- **左轴与其数据线同色**：左 y 轴刻度/标签颜色 = 左侧数据线颜色
- **右轴与其数据线同色**：右 y 轴刻度/标签颜色 = 右侧数据线颜色
- **推荐使用 plot_utils.get_palette 的相邻两色**（如 nature[0] 与 nature[3]）
- 严禁两轴都用默认黑色——评委无法快速对应数据与轴

#### 标签清晰
- 左轴标签 + 单位：`ax.set_ylabel('Temperature (°C)', color=left_color)`
- 右轴标签 + 单位：`ax2.set_ylabel('Humidity (%)', color=right_color)`
- 刻度颜色与轴标签同色：`ax.tick_params(axis='y', colors=left_color)`

#### 反模式
```python
# ❌ 错误：两轴均黑色
ax2 = ax.twinx()
ax.plot(t, temp)        # 默认蓝色
ax2.plot(t, humidity)   # 默认橙色
ax.set_ylabel('Temperature')      # 黑色
ax2.set_ylabel('Humidity')        # 黑色

# ✅ 正确：轴色与数据色对应
colors = get_palette('nature')
ax.plot(t, temp, color=colors[0])
ax2 = ax.twinx()
ax2.plot(t, humidity, color=colors[3])
ax.set_ylabel('Temperature (°C)', color=colors[0])
ax2.set_ylabel('Humidity (%)', color=colors[3])
ax.tick_params(axis='y', colors=colors[0])
ax2.tick_params(axis='y', colors=colors[3])
```

### 9.2 误差棒规范

#### 视觉参数
- `capsize=3-5`：误差棒两端必须有横线（"帽子"），避免成为无意义的线段
- `capthick=1.0-1.5`：帽子厚度 ≥ 主线厚度
- `elinewidth=0.8-1.2`：误差棒主线略细于数据线
- `error_kw={'capsize': 4, 'capthick': 1.2, 'elinewidth': 1.0}`

#### 标注规范
**必须在图注或 caption 中明确标注误差棒含义**：
- 95% CI（置信区间）：`误差棒表示 95% 置信区间（基于 t 分布）`
- ±1 SD（标准差）：`误差棒表示 ±1 倍标准差`
- ±1 SEM（标准误）：`误差棒表示 ±1 倍标准误`（不推荐用于数据展示，SEM 易让读者误解为 SD）

#### 95% CI vs SD 选择
| 场景 | 推荐 | 理由 |
|------|------|------|
| 总体均值估计 | 95% CI | CI 反映均值的精度 |
| 数据分散程度 | ±1 SD | SD 反映个体变异 |
| 多组均值比较 | 95% CI | 不重叠的 CI 提示显著差异 |
| 个体差异展示 | ±1 SD | 评委关心数据分布 |

#### 反模式
- 误差棒无 capsize（成"光秃线段"，难以辨识方向）
- caption 未说明 CI 还是 SD（评委无法判断数据分散度）
- 用 SEM 代替 SD 让误差棒看起来更小（学术不端边界）

### 9.3 inset 规范

inset（嵌入子图）用于局部放大，主图全貌 + inset 细节。

#### 指示线
- 必须使用 `ax.indicate_inset_zoom(ax_inset, edgecolor='gray', alpha=0.5)`
- 指示线连接主图放大区域与 inset 边界，方便评委对应位置
- 颜色用灰色（`'gray'` / `'#888888'`），不抢主图焦点

#### 边框
- inset 边框线宽 `0.5-0.8pt`，颜色与指示线一致（灰色）
- inset 内部刻度字号 ≤ 主图刻度字号（避免视觉冲突）

#### 标签位置
- inset 标题用小字号（`fontsize=7-8`），位于 inset 左上角或顶部
- 标题内容明确：`Zoom: x=[4,6]` 或 `Detail: t=50-60s`
- 不与主图 legend 重叠

#### 反模式
```python
# ❌ 错误：无指示线，inset 浮在主图上无对应关系
ax_inset = ax.inset_axes([0.55, 0.55, 0.4, 0.4])
ax_inset.plot(x_zoom, y_zoom)
# 缺少 ax.indicate_inset_zoom(ax_inset)

# ✅ 正确：完整 inset 规范
ax_inset = ax.inset_axes([0.55, 0.55, 0.4, 0.4])
ax_inset.plot(x_zoom, y_zoom, color=palette[2])
ax_inset.tick_params(labelsize=7)
ax_inset.set_title(f'Zoom: x=[{x_zoom.min()}, {x_zoom.max()}]', fontsize=8)
ax.indicate_inset_zoom(ax_inset, edgecolor='gray', alpha=0.5)
```

---

## 附录 C: CUMCM 评审视角图表偏好

> 基于 2015-2024 年全国大学生数学建模竞赛优秀论文图表统计归纳。
> 评审视角：评委平均 7-10 分钟看一篇论文，图表是第一印象的决定性因素。

### C.1 图表数量偏好

| 论文段 | 推荐图表数 | 类型偏好 |
|------|---------|---------|
| 问题重述 + 假设 | 0-1 | 流程图 / 假设树 |
| 模型建立 | 2-4 | 流程图 / 模型结构图 / 关系图 |
| 模型求解 | 3-6 | 收敛曲线 / 迭代过程 / 算法对比 |
| 结果分析 | 4-8 | 主结果图 / 灵敏度 / 鲁棒性 / 对比图 |
| 总计 | 9-19 | 每页 1-2 张图 |

**反模式**：
- 全文 < 5 张图（信息密度过低，评委怀疑工作不充分）
- 全文 > 25 张图（信息堆砌，主次不分，评委疲劳）
- 同一结果用 3 种图重复展示（图表冗余）

### C.2 图表类型偏好（按题型）

| 题型 | 高频图表 | 加分项 |
|------|---------|------|
| 优化类 | 决策变量时序图 / 目标函数收敛曲线 / 灵敏度龙卷风图 | Pareto 前沿（多目标） |
| 评价类 | 雷达图 / 热力图（指标×方案）/ 排名对比柱状图 | TOPSIS 相对接近度时序 |
| 预测类 | 实际 vs 预测散点图 / 残差图 / 滚动预测曲线 | 误差分布箱线图 |
| 统计类 | 分布直方图 / Q-Q 图 / 假设检验箱线图（含显著性标注） | 后验分布对比 |
| 微分方程 | 解的时序图 / 相图 / 3D 轨迹图 | 参数敏感性曲面 |
| 网络/图论 | 网络拓扑图 / 路径示意图 / 度分布 | 社区结构可视化 |
| 仿真 | 状态转移图 / 蒙特卡洛收敛曲线 | 多场景对比 |

### C.3 配色规范偏好

#### 评委偏好（基于优秀论文统计）
- **首选**：Nature / NEJM / Science 三大期刊配色（用 plot_utils.get_palette 直接调用）
- **次选**：色盲友好配色（okabe_ito / colorblind）—— 评委中有约 5% 色盲
- **避免**：
  - matplotlib 默认 tab10（评委一眼识别"未调配色"）
  - 红绿对比（色盲不友好）
  - 彩虹色（jet）—— 已被科学可视化界淘汰
  - 全图单一颜色（无区分度）

#### 连续 colormap 偏好
- 热力图 / 散点热力图：viridis / plasma / cividis / magma / inferno（感知均匀 + 色盲友好）
- 用 `plot_utils.get_colormap('viridis')` 获取
- **严禁** jet / rainbow / gist_rainbow

### C.4 标注规范偏好

#### 必备标注
- 坐标轴标签 + 单位（`时间 (s)` / `温度 (°C)` / `距离 (m)`）
- 图例 + 数据系列明确命名（`本文方法` / `对比方法` / `基准`）
- 关键数据点数值标注（如最值点 / 拐点 / 临界点）

#### 显著性标注（假设检验题型）
- 必须用 `***` / `**` / `*` 标注 p 值（p<0.001 / 0.01 / 0.05）
- 标注线连接比较组（U 形或方括号形）
- caption 说明统计检验方法（如 `Mann-Whitney U 检验, n=30`）

#### 反模式（评委扣分项）
- 坐标轴无单位（评委无法判断量纲）
- 图例缺失或与数据线无法对应
- 图题含 `$x^2$` 公式（Word 渲染失败）
- 饼图（已被学术界淘汰，改横向柱状图）
- 3D 柱状图（信息密度低于 2D 分组柱状图）
- 图内有 `plt.title()`（标题应放在 `\caption{}` 中）

### C.5 图表 caption 偏好

#### 结构（CUMCM 优秀论文三段式）
1. **描述**：图 N 描述——主语+谓语+宾语
2. **结论**：从图中读出的关键信息
3. **说明**：数据来源 / 计算方法 / 异常说明

#### 长度
- 中文 caption ≤ 30 字（图题只是标签，详细解读在正文）
- 英文 caption ≤ 25 words（MCM/ICM）

#### 反例 vs 正例
```
❌ 图1 结果
✅ 图1 不同算法在测试集上的收敛曲线——改进方法（红色）在第 50 轮达到 95% 精度，较 baseline 提前 30 轮
```

### C.6 评审视角一句话总结

> **"图表是评委 7 分钟内对论文质量第一判断依据。一张规范的图抵半页文字解读，一张糟糕的图让评委怀疑全篇。"**

#### 评审优先级（高到低）
1. **图题与正文呼应**（图被正文引用 + caption 自解释）
2. **数据与代码一致**（stdout 输出能复现图）
3. **配色与字体规范**（学术配色 + 中文不豆腐块）
4. **信息密度恰当**（一张图一个核心结论）
5. **细节完整**（坐标轴单位 + legend + 误差棒 + 关键点标注）

---

## 十、matplotlib → TikZ 桥接

> 来源：matplotlib pgf backend 官方文档 + tikzplotlib/matlab2tikz 停更公告（R6 调研）。
> 场景：用 matplotlib 探索数据后，需要把图表以矢量 + LaTeX 字体形式嵌入论文。

### 10.1 推荐方案：matplotlib `pgf` backend（官方支持）

matplotlib 内置 `pgf` 后端，可将图表导出为 PGF（Portable Graphics Format），
LaTeX 通过 `\input` 直接加载，无需任何第三方转换工具。

**优势**：
- 矢量图（与 PDF 同等质量）
- 字体与正文一致（直接调用 LaTeX 字体）
- 可在 LaTeX 中编辑文字（图中的 label/caption 可被 `\input` 后再修改）
- 官方维护，无停更风险
- 支持中文（需 ctex 环境）

**使用示例**：

```python
import matplotlib
matplotlib.use('pgf')  # 切换到 pgf 后端
import matplotlib.pyplot as plt

plt.rcParams.update({
    'pgf.texsystem': 'xelatex',          # 用 xelatex 编译（支持中文）
    'pgf.rcfonts': False,                # 不使用 matplotlib 的 rc 字体，改用 LaTeX 字体
    'font.family': 'serif',
    'text.usetex': False,                # False=用 mathtext 渲染数学；True=调用 LaTeX
})

fig, ax = plt.subplots(figsize=(3.5, 2.5))
ax.plot([1, 2, 3], [4, 5, 6])
ax.set_xlabel('Time (s)')
ax.set_ylabel('Velocity (m/s)')
fig.savefig('figure.pgf')                # 导出 PGF 文件
fig.savefig('figure.pdf')                # 同时导出 PDF 作为备份/预览
```

在 LaTeX 中加载：

```latex
\usepackage{pgfplots}                    % 加载 pgf 宏包
% ...
\begin{figure}[htbp]
\centering
\input{figure.pgf}                       % 直接 \input PGF 文件
\caption{速度随时间变化}
\label{fig:velocity}
\end{figure}
```

### 10.2 不推荐：tikzplotlib / matlab2tikz（已停更）

| 工具 | 状态 | 替代方案 |
|------|------|---------|
| `tikzplotlib` | 2022 年起官方停更，不再维护 | matplotlib `pgf` backend |
| `matlab2tikz` | 2020 年起官方停更 | MATLAB 自带 `exportgraphics` + PDF |

**为何不推荐**：
- 停更后与新版本 matplotlib 不兼容（如 3.7+ 的图例 API 变更）
- 复杂图表（双 y 轴、break axis、twin axis）转换失败率高
- 输出的 TikZ 代码冗长，难以人工编辑
- 缺乏中文支持（pgf backend 可直接用 ctex）

### 10.3 注意事项

#### 10.3.1 pgf backend 需要 LaTeX 环境

`pgf` 后端在 `savefig` 时会调用 `xelatex`/`pdflatex`，因此必须安装 TeX Live / MiKTeX。
CI/CD 环境若无 LaTeX，建议：
- 开发时用 pgf backend 导出 `.pgf` + `.pdf`
- 提交仓库时同时保留两份
- 论文中优先 `\input{.pgf}`，CI 校验时用 `\includegraphics{.pdf}` 兜底

#### 10.3.2 中文字体配置

```python
plt.rcParams.update({
    'pgf.texsystem': 'xelatex',
    'pgf.preamble': r'''
        \usepackage{ctex}               % 中文支持
        \setCJKmainfont{SimSun}         % 正文宋体
    ''',
})
```

#### 10.3.3 PDF 与 PGF 双格式导出

matplotlib 原生 `savefig` 即可导出 PDF（预览/兜底）与 PGF（LaTeX 直接输入）两种格式。

```python
# ... 绘图 ...
fig.savefig('figure.pgf')                # PGF for LaTeX
fig.savefig('figure.pdf')                # PDF for preview/fallback
```

#### 10.3.4 反模式

```python
# ❌ 错误：用 tikzplotlib 转换（已停更，复杂图失败）
import tikzplotlib
tikzplotlib.save('figure.tex')           # 高概率出错

# ❌ 错误：用 SVG 中转（中文丢失）
fig.savefig('figure.svg')                # SVG 后端不保留中文字体

# ✅ 正确：用 pgf backend 直接导出
matplotlib.use('pgf')
fig.savefig('figure.pgf')
```

### 10.4 何时仍应直接写 TikZ

以下场景 matplotlib 无法表达，应直接手写 TikZ（见 `tikz-templates.md`）：

- 流程图 / 状态机 / 神经网络架构图（节点+连线）
- 控制系统框图
- 立体几何示意图
- 自定义坐标系（极坐标、对数极坐标的特殊标注）

数据图（折线/柱状/散点/热力图）优先用 matplotlib + pgf backend，
结构图优先用 TikZ。两者**不要混用**于同一图表。
