# Input Authenticity Protocol — CUMCM Benchmark

> **P15 Input Authenticity Recovery**
> Generated: 2026-09-08
> Status: 5/5 benchmark problems recovered and verified; 0 BLOCKED

---

## 1. Input Authenticity Gate — 定义与检查项

Input Authenticity Gate 是 benchmark 运行前的强制门禁，确保 pipeline 接收到的题面是**真实的 CUMCM 官方题面**，而非伪造、混淆或 methodology paper。

### 1.1 检查项（全部通过方可放行）

| # | 检查项 | 通过标准 | 失败动作 |
|---|--------|----------|----------|
| G1 | 题面来源可追溯 | source_url 非空，且属于 Level 0–3 | BLOCKED |
| G2 | 双源交叉验证 | 至少 2 个独立来源题面内容一致 | pending（继续搜索） |
| G3 | 年份/编号/标题匹配 | problem_id 中的年份和字母与题面内标题一致 | BLOCKED |
| G4 | 问题数量完整 | sub_question_count 与题面实际问题数一致 | BLOCKED |
| G5 | 无 methodology 污染 | 题面仅含问题描述，不含解题思路/代码/论文 | BLOCKED |
| G6 | SHA256 已冻结 | text_sha256 已计算并写入 manifest | 必须补算 |
| G7 | 本地文件存在 | problem_statement.txt 在 problem_cards/<id>/ 下 | BLOCKED |

### 1.2 铁律

- **不得伪造 CUMCM 题面**。找不到可信来源时标记 `BLOCKED — authentic input unavailable`。
- **不得把 methodology paper / 解题博客当 problem statement**。博客中的"原题再现"段落可用，但必须剥离解题分析。
- **不得修改已冻结的题面文件**。如需修正，创建新版本并更新 SHA256。

---

## 2. Source Hierarchy（来源层级）

| Level | 类型 | 示例 | 使用规则 |
|-------|------|------|----------|
| **Level 0** | 官方 | mcm.edu.cn 官网题面、官方竞赛规则、官方题面 PDF | 最高可信度，可单独作为 ground truth |
| **Level 1** | 高校/赛区 | 大学教务处/数模协会 repost PDF、赛区组委会文件 | 高可信度，需 1 个 Level 0–2 来源交叉验证 |
| **Level 2** | 已发表获奖论文 | 中国大学生在线 (dxs.moe.gov.cn) 展示的国奖论文、官方讲评 | 可用于验证题面标题和问题范围，不直接提取题面文本 |
| **Level 3** | 成熟建模资源 | CSDN 原题再现、高校课程 PDF、集搜客论坛原题帖 | 需 2 个独立 Level 3+ 来源交叉验证 |
| **Level 4** | GitHub/Blogs | 个人博客、GitHub repo、知乎 | 只能用于发现资料线索，**不能未验证当 ground truth** |

### 使用规则

1. 优先搜索 Level 0 官方来源。
2. Level 0 不可得时，使用 Level 1–3 来源，必须满足**双源交叉验证**。
3. Level 4 仅用于发现线索，找到后必须升级到 Level 3+ 验证。
4. 任何来源的题面文本必须剥离解题思路、代码、论文内容，仅保留问题陈述本身。

---

## 3. 验证流程

```
Search → Source ranking → Cross-check → Authenticity verification → Local freeze → SHA256 → Manifest
```

### 3.1 Search
- 使用 `general_search` 多关键词并行搜索（中文原题名 + 英文 + 年份）。
- 关键词必须包含：年份、"全国大学生数学建模竞赛"、题号、题目关键词。

### 3.2 Source ranking
- 按 Source Hierarchy 对搜索结果分级。
- 优先抓取 Level 0–2 来源的完整内容。

### 3.3 Cross-check
- 对至少 2 个独立来源的题面文本逐段比对。
- 比对维度：背景描述、参数数值、问题数量、问题措辞、附件清单。
- 允许的差异：排版格式、图片引用（图1/图2等）、空白字符。
- 不允许的差异：参数数值不同、问题数量不同、核心约束不同。

### 3.4 Authenticity verification
- 确认题面不是 methodology paper（无解题步骤、无代码、无结果）。
- 确认年份/编号/标题与 problem_id 一致。
- 确认问题数量完整。

### 3.5 Local freeze
- 将验证通过的题面写入 `research/P15/benchmark/problem_cards/<problem_id>/problem_statement.txt`（UTF-8）。
- 文件仅包含题面文本，不含来源标注或解题内容。

### 3.6 SHA256
- 计算 `sha256(problem_statement.txt)` 并记录。
- 后续任何修改必须重新计算并更新 manifest。

### 3.7 Manifest
- 将所有元数据写入 `research/P15/benchmark/manifests/input_manifest.json`。
- 包含：problem_id, title, source_url, source_type, retrieval_date, text_sha256, authenticity_status, verification_notes。

---

## 4. Benchmark Problem 真实性状态表

| problem_id | 标题 | 状态 | 来源层级 | SHA256 (前16位) | 问题数 | 备注 |
|------------|------|------|----------|-------------------|--------|------|
| **2024_A** | 板凳龙闹元宵 | ✅ verified | Level 1 (高校PDF) + Level 3 (CSDN) | `9baf81fb40f82f77` | 5 | **P0 污染已修复**。原 examples/problems/cumcm2024A.txt 是"防空导弹"（实为2025_A），现已替换为真实板凳龙题面 |
| **2022_C** | 古代玻璃制品的成分分析与鉴别 | ✅ verified | Level 3 (CSDN) + Level 3 (DAMO) | `ec5e098f9dbe858e` | 4 | 双源一致；官方讲评(北大邓明华)确认标题 |
| **2020_B** | 穿越沙漠 | ✅ verified | Level 3 (CSDN) + Level 3 (论坛) | `a2d0867169b94c59` | 3 | 双源一致；官方讲评(浙大谈之奕)确认标题 |
| **2018_A** | 高温作业专用服装设计 | ✅ verified | Level 3 (论坛) + Level 2 (dxs.moe.gov.cn论文) | `6b4062dcd020bd6b` | 3 | 双源一致 |
| **2019_C** | 机场的出租车问题 | ✅ verified | Level 3 (163新闻) + Level 3 (BNUZ课程PDF) | `4fc950a9a2251043` | 4 | 双源一致；官方讲评(韩中庚)确认标题 |

### 详细来源记录

#### 2024_A — 板凳龙闹元宵
- **来源1 (Level 1)**: 哈尔滨信息工程学院基础部 PDF — `https://jichu.greathiit.com/uploadfile/2024/1015/20241015214200626.pdf`
- **来源2 (Level 3)**: CSDN blog weixin_66547608 — `https://blog.csdn.net/weixin_66547608/article/details/142006824`
- **辅助验证 (Level 2)**: 中国大学生在线 A题讲评(复旦蔡志杰) — `https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmstjp_2024sxjmstjp/241202/1982935.shtml`
- **交叉验证结果**: 两来源题面文本完全一致。关键参数：223节板凳、龙头341cm/龙身220cm、板宽30cm、孔径5.5cm、孔距板头27.5cm、螺距55cm、初始第16圈、速度1m/s、300s、调头空间直径9m、盘出螺距1.7m、速度上限2m/s。
- **P0 污染说明**: 原 `examples/problems/cumcm2024A.txt` 内容为"防空导弹拦截弹道目标"，经核实该内容实际是 **2025_A** 题面。pipeline 因此收到了错误题面。本次恢复已将真实 2024_A 题面冻结到 problem_cards/2024_A/。

#### 2022_C — 古代玻璃制品的成分分析与鉴别
- **来源1 (Level 3)**: CSDN blog 2403_87108415 — `https://blog.csdn.net/2403_87108415/article/details/149259357`
- **来源2 (Level 3)**: DAMO开发者矩阵 — `https://damodev.csdn.net/688991ecbb9d8e0ecec3d611.html`
- **辅助验证 (Level 2)**: 中国大学生在线 C题讲评(北大邓明华) — `https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmstjp_2022sxjmstjp/230404/1834982.shtml`
- **交叉验证结果**: 两来源"原题再现"段落完全一致。4个问题，高钾/铅钡玻璃分类，85%-105%有效数据范围，3个附件表单。

#### 2020_B — 穿越沙漠
- **来源1 (Level 3)**: CSDN blog gzn00417 — `https://blog.csdn.net/gzn00417/article/details/108521037`
- **来源2 (Level 3)**: 集搜客论坛 2020全套题 — `https://www.gooseeker.com/doc/thread-17986-1-1.html`
- **辅助验证 (Level 2)**: 中国大学生在线 B题讲评(浙大谈之奕) — `https://dxs.moe.gov.cn/zx/a/qkt_sxjm_sxjmstjp/201204/1601201.shtml`
- **交叉验证结果**: 两来源题面文本一致。8条游戏规则，3大问题（含多人模式子问题），6个关卡。

#### 2018_A — 高温作业专用服装设计
- **来源1 (Level 3)**: 集搜客论坛 2018全套题 — `https://www.gooseeker.com/doc/thread-17969-1-1.html`
- **来源2 (Level 2)**: 中国大学生在线获奖论文 PDF（含问题重述）— `https://dxs.moe.gov.cn/zx/2018/1101/1541041099335.pdf`
- **交叉验证结果**: 两来源一致。3个问题，4层模型(I/II/III织物+IV空气间隙)，假人37°C，75°C/65°C/80°C三种工况，47°C/44°C灼伤阈值。

#### 2019_C — 机场的出租车问题
- **来源1 (Level 3)**: 163.com 2019全套题 — `http://m.163.com/dy/article/EOUL3NBE054535JN.html`
- **来源2 (Level 3)**: BNUZ 数学模型课程 PDF — `http://www.bnumm.cn/static/courseware/theory/2.pdf`
- **辅助验证 (Level 2)**: 中国大学生在线 C题讲评(韩中庚) — `https://dxs.moe.gov.cn/zx/a/hd_sxjm_sxjmstjp_2019sxjmstjp/210607/1699705.shtml`
- **交叉验证结果**: 两来源一致。4个问题，蓄车池/乘车区设置，司机A/B选择决策，2车道上车点优化，短途优先权方案。

---

## 5. 论文规范核验结果

### 5.1 官方来源

- **文档**: 《全国大学生数学建模竞赛论文格式规范（2026年修订稿）》
- **发布方**: 全国大学生数学建模竞赛组委会
- **发布日期**: 2026-03-03
- **URL**: `https://www.mcm.edu.cn/html_cn/node/4cd596519c9eb9fbd866398f6df0caa3.html`
- **是否原始来源**: 是（Level 0 官方）

### 5.2 逐条核验

| 规范项 | 官方规定 | 来源条款 | 核验状态 |
|--------|----------|----------|----------|
| **页数** | 正文从第四页开始，**不超过30页**（2026修订稿硬上限）；2023/2024版为"尽量控制在20页以内"（软目标） | 第四条 | ✅ 官方确认。**注意：20页是软目标，30页是2026硬上限** |
| **摘要** | 第三页为摘要专用页，含标题和关键词，无需翻译成英文，**不超过一页** | 第三条 | ✅ 官方确认 |
| **页码** | 从摘要页开始，页脚中部，阿拉伯数字从1连续编号 | 第三条 | ✅ 官方确认 |
| **目录** | 不要目录 | 第四条 | ✅ 官方确认 |
| **匿名** | 论文任何地方不能有参赛者身份、学校、赛区信息 | 第六条 | ✅ 官方确认 |
| **附录** | 正文之后，页数不限，必须包含全部完整可运行源程序代码；缺少程序或程序不能运行可能取消评奖资格 | 第五条 | ✅ 官方确认 |
| **参考文献** | 所有引用他人或公开资料必须按科技论文规范列出参考文献，并在正文引用处标注 | 第七条 | ✅ 官方确认 |
| **电子版** | PDF或Word格式，单独文件，不超过20MB，第一页必须为摘要页（不含承诺书和编号页） | 第十条 | ✅ 官方确认 |
| **支撑材料** | RAR或ZIP压缩，不超过20MB，包含所有可运行源程序和数据资料；文件列表放入附录 | 第十一条 | ✅ 官方确认 |
| **页边距** | A4纸，上下左右至少2.5cm | 第一条 | ✅ 官方确认 |

### 5.3 评阅标准

- **官方来源**: `https://www.mcm.edu.cn/jxie/papers/EIMI2011_Xie.pdf`（谢金星，CUMCM 官方介绍论文）
- **四项评阅标准**（官方原文）:
  1. **假设的合理性** (reasonability of model assumptions)
  2. **建模的创造性** (creativity/innovation of the model)
  3. **结果的正确性** (correctness of the solutions)
  4. **文字表述的清晰程度** (readability of the presentation)
- **核验状态**: ✅ 官方确认。摘要在初评中占有重要权重（"全国评阅时将首先根据摘要和论文整体结构及概貌对论文优劣进行初步筛选"），但官方未给出精确百分比权重。

### 5.4 对 env/config.yaml 的影响

当前 `core/env/config.yaml` 中 `paper.min_pages: 17` 是合理的软目标下限。但需注意：
- 2026 修订稿将正文硬上限从"尽量20页"改为"不超过30页"，意味着 17–20 页仍是推荐范围，但 20 页不再是硬上限。
- 建议保持 `min_pages: 17` 作为质量门槛，不设硬上限（或设为 30 以匹配 2026 规范）。

---

## 6. BLOCKED 项清单

| problem_id | 状态 | 原因 |
|------------|------|------|
| — | — | **无 BLOCKED 项**。5/5 benchmark 题目均已从至少 2 个独立来源恢复并交叉验证通过。 |

### 历史 BLOCKED 项（已解除）

| problem_id | 原状态 | 解除方式 |
|------------|--------|----------|
| 2024_A | input_file 错误（防空导弹≠板凳龙） | 从高校PDF + CSDN双源恢复真实题面 |
| 2022_C | input_file=null | 从CSDN + DAMO双源恢复 |
| 2020_B | input_file=null | 从CSDN + 论坛双源恢复 |
| 2018_A | input_file=null | 从论坛 + dxs.moe.gov.cn双源恢复 |
| 2019_C | input_file=null | 从163新闻 + BNUZ课程PDF双源恢复 |

---

## 7. 产出文件清单

| 文件 | 绝对路径 | 说明 |
|------|----------|------|
| 协议文档 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\measurement_recovery\INPUT_AUTHENTICITY_PROTOCOL.md` | 本文件 |
| 输入清单 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\benchmark\manifests\input_manifest.json` | 机器可读 manifest |
| 2024_A 题面 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\benchmark\problem_cards\2024_A\problem_statement.txt` | 板凳龙闹元宵（已修复P0污染） |
| 2022_C 题面 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\benchmark\problem_cards\2022_C\problem_statement.txt` | 古代玻璃制品的成分分析与鉴别 |
| 2020_B 题面 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\benchmark\problem_cards\2020_B\problem_statement.txt` | 穿越沙漠 |
| 2018_A 题面 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\benchmark\problem_cards\2018_A\problem_statement.txt` | 高温作业专用服装设计 |
| 2019_C 题面 | `C:\Users\Lin\Desktop\Programs\MathModel\research\P15\benchmark\problem_cards\2019_C\problem_statement.txt` | 机场的出租车问题 |

---

## 8. 后续行动建议

1. **修正 examples/problems/cumcm2024A.txt**: 将错误的"防空导弹"内容替换为真实板凳龙题面，或删除该文件并指向 problem_cards/2024_A/。
2. **pipeline 输入源切换**: 将 benchmark 运行的题面输入源从 `examples/problems/` 切换到 `research/P15/benchmark/problem_cards/`，确保使用已验证题面。
3. **附件数据恢复**: 5道题均有附件数据（Excel/PDF），当前仅恢复了题面文本。后续可考虑恢复附件数据并计算 attachment_sha256。
4. **env 配置更新**: 评估是否将 `paper.min_pages` 保持 17，以及是否需要添加 `paper.max_pages: 30` 以匹配 2026 规范。
