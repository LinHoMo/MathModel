---
name: figure-generator
description: '生成并规范命名论文所需图表，确保每张图都被正文引用和解读。'
hand: writer
utg_layer: L2
stage: 3
inputs:
  - figures/*.png
  - work/paper_structure.json
outputs:
  - paper/figures/
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> writer figure-generator`
- **输入**：all_results.json
- **输出**：`paper/figures/*.png`
- **核心步骤**：1. 生成图表 → 2. 规范命名 → 3. 渲染验证 → 4. 确保被正文引用
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Figure Generator

## Role

图表生成与规范命名师：把 Programmer 手 `figures/` 下的原始图表按规范命名后复制到论文目录，必要时为缺失图表补充生成，并维护 `paper/figures/` 目录与 `paper_structure.json` 中 `figure_plan` 的一致性。

## UTG Layer

L2 工具调用与生成层：图表是 LaTeX 正文之外的另一类实体产物，命名规范、格式规范、文件存在性是后续 reference-curator 和 guardrails-checker 校验的前提。本 agent 把"图表清单"从叙述性描述落地为符合命名规范的实体文件，使 `\includegraphics{figures/fig_1_1.png}` 这类引用不会在编译期失败。本 agent 与 section-writer 同属 L2，但职责分离：section-writer 写引用语法，figure-generator 落地图片文件。

## Contract

- 输入：
  - `figures/*.png`（Programmer 手输出，文件名可能不规范）
  - `figures/*.pdf` / `figures/*.eps`（矢量图，如有）
  - `work/paper_structure.json`（含 `figure_plan`，规定目标文件名）
- 输出：
  - `paper/figures/fig_<problem_id>_<seq>.png`（规范命名的图表文件）
  - `paper/figures/manifest.json`（每个文件的来源映射与说明，可选）

## Procedure

### Step 1: 读取图表计划

从 `work/paper_structure.json` 读取 `figure_plan` 数组，每一项含：
- `id`：如 `fig_1_1`
- `filename`：目标路径如 `paper/figures/fig_1_1.png`
- `source`：源文件如 `figures/result_q1_convergence.png`
- `caption_required`：是否需要 caption（默认 true）

### Step 2: 命名规范

图表命名规范（铁律 P4 同源）：

```
fig_<problem_id>_<seq>.<ext>
```

- `problem_id`：子问题编号（1, 2, 3...）
- `seq`：该子问题内的图表序号（1, 2, 3...）
- `ext`：`png` / `pdf` / `eps`

表格 LaTeX 文件不归本 agent 管理，但若 `table_plan` 含外部数据文件（如 `tables/result_1.xlsx`），同样按 `tab_<problem_id>_<seq>.<ext>` 规范命名。

### Step 3: 复制与重命名

对每个 `figure_plan` 项：
1. 确认源文件存在（`source` 路径）
2. 复制到 `filename` 目标路径
3. 矢量优先：若同时存在 `.pdf`/`.eps` 与 `.png`，复制矢量版本
4. 位图需 >= 300 dpi

### Step 4: 缺失图表补生成

若 `figure_plan` 中的图表在 Programmer 手 `figures/` 下不存在，本 agent 需补生成：
- 参考 `core/Writer/knowledge/reference/figure-rules-enhanced.md`（按题型分类的图表指南）
- 参考 `core/Writer/knowledge/reference/figure-guide.md`（图表生成指南）
- 参考 `core/Writer/knowledge/reference/figure-rules.md`（图表规范：命名、格式、配色、内容）
- 高阶图型（技术路线图 / 龙卷风图 / Taylor 图 / 雨云图 / 桑基图 / 标注热力图）参考
  `core/Writer/knowledge/reference/advanced-figures.md`（含零依赖代码配方与选型速查）
- 数据来源：`figures/all_results.json`
- **配色常量**：所有 matplotlib 图表统一引用 `core/templates/figures/matplotlib_style_constants.py` 的 `COLORS` / `PALETTE` / `RC_PARAMS`
- **图表选型速查**：参考 `core/templates/figures/FIGURE-TEMPLATE-INDEX.md`
- **🚨 每张图生成后必须 print() 该图的数据特征**（借鉴 MathModelAgent-main coder.py 规范）：
  ```python
  # 时序图
  print("【图X数据特征 - 时序】")
  print(f"    起点值: {y[0]:,.2f}, 终点值: {y[-1]:,.2f}")
  print(f"    峰值: {y.max():,.2f}, 谷值: {y.min():,.2f}")
  # 模型拟合
  print("【图X数据特征 - 模型拟合】R²={r2:.4f}, MAE={mae:.4f}")
  # 预测/灵敏度
  print("【图X数据特征 - 预测】点预测={pred:.2f}, 95%CI=[{lo:.2f},{hi:.2f}]")
  print("【图X数据特征 - 灵敏度】峰值=z{max_idx}={z_max:.3f} at ({x_label},{y_label})")
  ```
- 生成函数签名遵循原 Writer SKILL 的 L2 约定：

```python
def generate_figure(problem_id: int, fig_num: int, data: dict, caption: str) -> str:
    filename = f"paper/figures/fig_{problem_id}_{fig_num}.png"
    # ... 生成图表
    return filename
```

### Step 5: 编号连续性校验

确保图表编号连续：fig_1_1, fig_1_2, fig_2_1, fig_3_1...，不跳号。若 section-writer 中已写好的 `\ref{fig:...}` 引用对应不上，回写 `work/paper_structure.json` 同步 `figure_plan`。

### Step 6: 写出 manifest

可选输出 `paper/figures/manifest.json`，记录每个文件：
- `target_filename`
- `source_filename`
- `generated_by`（"copied" / "generated"）
- `dpi` / `format`
- `caption`（建议标题，供 section-writer 引用）

## Self-Check

- [ ] `paper/figures/` 目录存在且非空
- [ ] 文件数量 >= `get("paper.min_figures")`
- [ ] 每个文件名匹配 `^fig_\d+_\d+\.(png|pdf|eps)$`
- [ ] 编号连续无跳号
- [ ] 矢量图优先（同时存在 `.png` 与 `.pdf` 时已选 `.pdf`）
- [ ] 位图分辨率 >= 300 dpi（用 PIL 或 `identify` 抽检）
- [ ] `figure_plan` 中每一项的 `filename` 都真实存在
- [ ] 每个 `paper/figures/*.png` 都能被 `paper/main.tex` 中的 `\includegraphics` 引用（不出现孤立文件）
- [ ] 图表配色使用 `core/templates/figures/matplotlib_style_constants.py` 中的 `COLORS` / `PALETTE`，未引入硬编码随机色
- [ ] 每张生成后的图表都通过 `print()` 输出了数据特征（时序/拟合/预测/灵敏度等）
- [ ] 图表类型选型有参考 `core/templates/figures/FIGURE-TEMPLATE-INDEX.md`

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "writer",
  "stage": 3,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "figure-generator",
      "stage": 3,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/Writer/knowledge/reference/figure-rules-enhanced.md`（按题型分类的图表指南）
- `core/Writer/knowledge/reference/figure-rules.md`（图表规范：命名、格式、配色、内容）
- `core/Writer/knowledge/reference/figure-guide.md`（图表生成指南）
- `work/paper_structure.json`（`figure_plan` 输入）
- `figures/all_results.json`（补生成图表的数据来源）
- `core/Writer/laws/rules.md`（W1 图表数值与代码输出一致、W4 图表前后有分析文字——后者由 section-writer 保证，本 agent 负责图表实体可被引用）

## Iteration

自检失败时回退修正：
1. 命名不规范：批量重命名为 `fig_<problem_id>_<seq>.<ext>` 格式。
2. 编号跳号：重排 seq，并通知 section-writer 同步 `\ref{}`。
3. 文件缺失：调用 `generate_figure()` 补生成；若 `all_results.json` 中无对应数据，标记阻塞并退回 Programmer 手。
4. 分辨率不足：以 300 dpi 重新保存（位图）或建议使用矢量格式。
5. 孤立文件（未被引用）：在 `figure_plan` 中标记，由 section-writer 补引用或由本 agent 删除。
6. `runtime.strict_mode == True` 下任一阈值不达即标记阻塞，不进入 reference-curator。
