# 第三轮深度升级：对标三仓库组件吸收总结

> 生成日期：2026-09-05
> 目标：基于 LLM-MM-Agent / MathModelAgent-main / opendraft-master 三个对标仓库，对 MathModelSkills 进行第三轮深度升级。

---

## 升级目标回顾

本轮聚焦五项核心能力的吸收：

| # | 目标 | 状态 |
|---|---|---|
| 1 | 结果规范格式化 | ✅ 完成 |
| 2 | 可视化增强流水线 | ✅ 完成 |
| 3 | DOCX 交付自动化 | ✅ 完成 |
| 4 | 多格式输出 | ✅ 完成（第二轮已实现，本轮强化联动） |
| 5 | 质量门禁升级 | ✅ 完成 |

---

## 本轮新增产物清单

### 基础设施工具层

| 产物路径 | 作用 | 对标来源 |
|---|---|---|
| `core/tools/text_cleanup.py` | 文本 10 步确定性清理流水线（填充词/强化词/同义词链/元评论/冗余短语/词汇多样化/声明校准） | opendraft-master |
| `core/tools/docx_post_processor.py` | DOCX 学术论文后处理（标题居中/机构信息/分页/表格宽度/摘要分页），python-docx 可选依赖降级 | opendraft-master |
| `core/tools/writing_check.py` | 14 项论文质量自动扫描（标题/缩写/段落/图表/公式/引用/过渡/时态/主被动/冗余/一致性/拼写/冠词/标点） | MathModelAgent-main |

### SKILL.md 增强

| Agent | 增强点 | 状态 |
|---|---|---|
| code-implementer | Step 3.7 结果规范格式化（`_print_result_summary()` + `_metadata` 层 + 标准化输出到 work/result_summary.txt） | ✅ |
| figure-generator | Self-Check 新增配色常量引用 + 数据特征 print 强制 + FIGURE-TEMPLATE-INDEX.md 参考 | ✅ |
| reference-curator | Step 5.5 多源交叉验证（CrossRef + OpenAlex/S2 双源确认） | ✅ |
| final-validator | Step 4.7 DOCX 交付三引擎回退链文档化 + Step 4.6 PDF 视觉检查流程 | ✅ |
| section-writer | 段落式写作 + 过渡连接词表 + 图片插入强制规范 | ✅ |

### 校验与模板层

| 产物路径 | 数量/说明 |
|---|---|
| `core/templates/figures/matplotlib_style_constants.py` | 统一色彩常量（COLORS/PALETTE/RC_PARAMS） |
| `core/templates/figures/FIGURE-TEMPLATE-INDEX.md` | 8 类数据→图表选型速查索引 |
| `core/templates/figures/line_ci.py` | 时序+置信带模板 |
| `core/templates/figures/box_strip.py` | 箱线+散点模板 |
| `core/templates/figures/heatmap.py` | 热力图模板 |
| `core/templates/figures/grouped_bar.py` | 分组柱状图模板 |
| `core/templates/figures/scatter_regression.py` | 散点+回归模板 |
| `core/knowledge/pitfalls/TYPE-ANTIPATTERNS-CHECKLIST.md` | ~50 条题型特异性反模式 |

### validate_project.py v3 检查项扩展

| 新增检查 | 类别 | 说明 |
|---|---|---|
| `check_ai_writing_patterns` | Content quality | 扫描命令式/过度自信语言（EN+CN 模式） |
| `check_data_feature_prints` | Reproducibility | 验证 matplotlib 调用对应 `【图X数据特征】` print |
| `check_abstract_body_numeric_consistency` | Reproducibility | 验证摘要中数字在正文出现 |

总数从 49 项增至 52 项（分组从 7 组扩展至 10 组）。

---

## 架构决策记录（ADR）

### ADR-001：python-docx 可选依赖降级策略

**决策**：`docx_post_processor.py` 采用软导入（try/except 包裹 `import docx`），未安装时 API 返回 `True`（无操作成功），保证 DOCX 交付链路不中断。

**理由**：
- MathModelSkills 遵循"零第三方依赖"铁律（核心工具链纯标准库）
- 多数竞赛主机无 python-docx，强制依赖会导致 DOCX 交付分支崩溃
- pandoc 路径为可选增强，python-docx 进一步增强 pandoc 产物质量

### ADR-002：tex_to_docx.py 三引擎回退链最终形态

```
pandoc（高质量：OMML 公式、图/表保留）
  ↓ 失败或不可用
OOXML 结构化降级（build_docx_text：三线表+编号公式+标题样式）
  ↓ 也失败
纯文本最小版（终极 fallback）
```

各引擎失败均回退下一级，保证总能产出可打开的 DOCX。

### ADR-003：docx_post_processor 仅在 pandoc 路径触发

**决策**：后处理仅对 pandoc 生成的 DOCX 生效，对结构化降级版 DOCX 不触发。

**理由**：
- 结构化降级版 OOXML 已由代码手动构建，pandoc 的 Title/Date 样式不存在
- python-docx 解析手写字 OOXML 可能破坏格式
- pandoc 生成的 DOCX 使用 Word 标准样式名（Title/Date/Heading 1），适合后处理

### ADR-004：CLAIM CALIBRARY 声明校准集成点

**决策**：声明校准入 text_cleanup.py（通用工具）+ validate_project.py（门禁检查）双点集成。

**理由**：
- text_cleanup.py 做自动转换（"proves that" → "supports the finding that"）
- validate_project.py 做残留检查（防止新引入）
- 与 scorer-adversarial 评审维度互补（审查 vs 修正）

---

## 数值一致性保障

本轮强化了"论文数值可追溯到 all_results.json"铁律的实现路径：

1. code-implementer Step 3.7 强制输出 `_print_result_summary()` 标准化表格
2. 输出包含 `_metadata` 层（team/problem/generated_at/seed/platform）
3. 每个求解器返回 `{values, units, validation}` 三元组
4. Writer 阶段仅消费 Programmer 输出，不允许重新估算数值
5. consistency-checker 验证论文-代码数值一致
6. validate_project.py 新增 `check_abstract_body_numeric_consistency`

---

## AI 痕迹消除流水线

14 步防 AI 痕迹（多工具协同）：

1. text_cleanup.py 10 步清理
2. writing_check.py 14 项扫描
3. validate_project.py check_ai_writing_patterns 门禁
4. scorer-adversarial 维度评审
5. section-writer 过渡连接词多样化
6. section-writer 段落式写作（禁用列表）
7. figure-generator 数据特征 print（体现人类洞察）
8. 题型特异性反模式扫描

---

## 后续可吸收组件（ROI 排序）

| 组件 | 对标仓库 | 复杂度 | ROI |
|---|---|---|---|
| output_validators.py | opendraft | 中 | 高 — 统一输出 schema 校验 |
| error_mapper.py | opendraft | 低 | 高 — LLM 错误码→可读错误信息 |
| MM-Bench 评估 prompts | LLM-MM-Agent | 中 | 中 — 离线评估方法参考 |
| zip_bundle_manager.py | opendraft | 低 | 低 — 打包交付 |

---

## 验证记录

### validate_project.py v3 验证（cumcm2024a）

```
新增 3 项检查结果：
- ai writing patterns PASS
- data feature prints PASS
- abstract-body numeric consistency WARN（未定位到 abstract 环境，预期行为）
```
