# 增强日志（三轮迭代记录：v2 MM-Agent+opendraft 对标 / v3 三仓库全面升级）

> 本项目历经三轮迭代增强，以下为各轮产物记录。

> **⚠️ 关键发现：摘要 t*=412.83 s 与结果 360.25 s 不一致（blocking 级内部矛盾），需立即修正！**

## v3 新增产物（基础设施 / 工具 / 模板库）— 2026-09-05

| 产物路径 | 来源 | 说明 |
|---------|------|------|
| `core/tools/text_cleanup.py` | opendraft-master engine/utils/text_cleanup.py | 10 步确定性文本清理流水线（填充词/强化词/同义词链/元评论/冗余短语/词汇多样化/声明校准/引用去重） |
| `core/tools/docx_post_processor.py` | opendraft-master engine/utils/docx_post_processor.py | DOCX 学术论文后处理（标题居中/机构信息/分页/表格宽度修复）；python-docx 可选依赖，未安装时降级为 no-op |
| `core/tools/tex_to_docx.py` (增强) | 本机增强 | pandoc 成功后可选后处理；新增 --institution / --verbose CLI 参数 |
| `core/tools/validate_project.py` (v3) | 本机增强 | 新增 3 项检查（ai_writing_patterns / data_feature_prints / abstract_body_numeric_consistency），总数 52 项 |
| `core/tools/writing_check.py` | MathModelAgent-main 6verity | 14 项论文质量自动扫描 |
| `core/Programmer/agents/code-implementer/SKILL.md` | 本机增强 | 新增 Step 3.7 结果规范格式化（`_print_result_summary()` + `_metadata` 层） |
| `core/templates/figures/matplotlib_style_constants.py` | 新建 | 统一色彩常量 `COLORS`/`PALETTE`/`RC_PARAMS` |
| `core/templates/figures/FIGURE-TEMPLATE-INDEX.md` | 新建 | 8 类数据→图表速查索引 |
| `core/templates/figures/line_ci.py` | 新建 | 时序+置信带模板 |
| `core/templates/figures/box_strip.py` | 新建 | 箱线+散点模板 |
| `core/templates/figures/heatmap.py` | 新建 | 热力图模板 |
| `core/templates/figures/grouped_bar.py` | 新建 | 分组柱状图模板 |
| `core/templates/figures/scatter_regression.py` | 新建 | 散点+回归模板 |
| `core/knowledge/pitfalls/TYPE-ANTIPATTERNS-CHECKLIST.md` | MathModelAgent-main + opendraft | ~50 条题型防错 |

## v2 新增产物（MM-Agent + opendraft 对标）— 2026-09-04

| # | 产物路径 | 来源 SKILL 增强 | 说明 |
|---|---------|----------------|------|
| 1 | `work/ambiguity_prescreen.md` | problem-parser Step 3.5 | 假设敏感性预检，覆盖 5 处关键歧义的解释与裁决 |
| 2 | `output/MODEL_SPEC.md` 第 10 章 | model-builder Step 6.5+6.7 | 代码实现任务清单（5 张子问题表）+ 工程优化铁律 |

## 增强产物

| # | 产物路径 | 内容 |
|---|---------|------|
| 3 | `work/weakness_report.json` | 新增 5 条 Skeptic 模式命中（引用质量/内部矛盾/过度声明/缺失替代），发现 **1 条 blocking 级内部矛盾** |
| 4 | `work/score_card_adversarial.json` | 新增 skeptic_additions（引用审查 + 5 条同行评审预测），最终分 5.5（不通过） |
| 5 | `work/reference_report.json` | 新增 cross_verified 字段（多源交叉验证），新增 skeptic_findings 结构 |
| 6 | `work/score_card.json` | 更新 adversarial 维度score 从 7.5 降为 5.5，加权总分 7.07，blocking 列表从 0 增为 1 |

## 关键发现

### ⚠️ BLOCKING：摘要-结果数值不一致

- **问题**：摘要正文声明 "t* = 412.83 s"，但 `figures/all_results.json` 中 `problem_2.values.t_star = 360.25`
- **差距**：52.58 s（相对差 14.6%）
- **严重度**：阻塞级——这是评委第一件事就会核对的数值，不一致直接导致论文可信度崩溃
- **修复建议**：统一为 all_results.json 的值（360.25 s），将摘要 412.83 改为 360.25

### MAJOR：薄矩形碰撞判据论证缺失

- **问题**：板凳为长矩形（2.20 m × 0.30 m），论文仅用中心线距离判据，未讨论与 OBB 矩形相交判据的差异
- **修复建议**：补充薄矩形近似等价性论证（误差量级 ≈ (w/L)² ≈ 1.8%）

### MAJOR：替代解法讨论缺失

- **问题**：论文未讨论其他碰撞检测方法（如 SAT 算法）以及龙头非匀速驱动的模型扩展
- **修复建议**：在假设局限性小节中增加简要讨论

### MINOR：引用填充

- `optimization`（最优化理论与方法）：项目核心为运动学递推，无具体定理引用
- `modeling`（数学模型通用教材）：无具体页码/定理引用，被更专业的文献覆盖

## 同行评审预测（Top 3 高概率追问）

1. **高概率**：摘要与结果节 t* 数值不一致（已在 blocking 中）
2. **高概率**：板凳矩形碰撞判据的薄矩形近似是否合理？
3. **中概率**：S 形几何方程组的求解是否收敛？有无多解？

## Cross 验证状态

- 引用总数：10
- 有 DOI 可在线验证：1（numpy，DOI 10.1038/s41586-020-2649-2）
- 无 DOI 需静态检查：9（中文教材为主）
- 当前网络状态离线，CrossRef + OpenAlex 双源确认暂不可用
- spiral_kinematics 期刊论文建议补充 DOI

---

## 修复清单（按优先级）

| 优先级 | 问题 | 修复动作 | 负责方 |
|--------|------|---------|--------|
| **P0** | 摘要 t* = 412.83 ≠ 结果 360.25 | 统一为 360.25（以 all_results.json 为准） | section-writer |
| **P1** | 薄矩形碰撞判据未论证 | 补充 (w/L)² 量级误差分析 | section-writer |
| **P2** | 引用填充（optimization, modeling） | 移除或补充具体定理引用 | reference-curator |
| **P3** | spiral_kinematics 缺 DOI | 补充 DOI 或更换为有 DOI 的文献 | reference-curator |
| **P4** | 龙头非匀速扩展讨论缺失 | 假设 H3 局限性小节补充 | section-writer |
| **P5** | 摘要主观词'最为自然' | 改为'是合适的参数化选择' | section-writer |

---

## 执行记录

- 2026-09-04：v2 完成（MM-Agent + opendraft 对标）
- 2026-09-05：v3 完成（三仓库全面对标 — 基础设施/工具/模板库）
- 下次重跑触发条件：用户手动要求或 SKILL.md 再次更新

## 关联产物索引

| 产物 | 路径 |
|------|------|
| 假设敏感性预检 | `work/ambiguity_prescreen.md` |
| 代码实现任务清单 | `output/MODEL_SPEC.md` 第 10 章 |
| Skeptic 弱点报告 | `work/weakness_report.json` |
| 对抗性评分（增强） | `work/score_card_adversarial.json` |
| 多源引用验证 | `work/reference_report.json` |
| 综合评分卡 | `work/score_card.json` |

---

> **增强版本**：v3（2026-09-05 起用三仓库全面对标标准）
> 原始 29 步 pipeline 产物保持不变，新增产物追加到 `work/` 和 `output/` 目录。
> 
> **v3 详细日志见**：`work/round3_integration_summary.md`
> **v2 历史日志见**：本文件（v2 章节仍有效）
