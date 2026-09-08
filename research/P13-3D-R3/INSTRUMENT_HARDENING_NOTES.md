# P13-3D-R3.1 Instrument Hardening Notes

- 版本语义：`P13-3D-R3` = **closed**（结论不变，见 `real_evaluation/R3_2_FINAL_REPORT.md`）；`P13-3D-R3.1` = **instrument hardening**（纯基础设施增强，不改变任何已发布结果，不重开 R3）。
- 日期：2026-09-07

## H1 配对唯一性 → 已实现（corpus gate v1.1）

`research/P13-3D/scripts/r3g_corpus_check.py` 升级为 v1.1，additive 新增语料级检查，阻断四类缺陷：

| 类 | 缺陷 | 检查 |
|---|---|---|
| A | 同一 `(question, arm, writer)` 出现多份 paper（非规范命名/冗余副本） | 扫描 W0/W1 全部 `*.md`，非 `{qid}_{arm}.md` 规范名 → `unexpected_files` |
| B | 同一 paper 内容被配给多个单元 | 内容 hash 分组，跨文件名重复 → `cross_cell_duplicates` |
| C | 同一单元 W0/W1 字节级重复（本轮 2020_B/B0 实际发生过） | 同文件名双条件同 hash → `same_cell_duplicates` |
| D | 任意不同单元共享完全相同内容 hash | 同 B（显式分组列出） |

判定语义：单元级检查（存在/篇幅/章节/泄漏）**冻结不变**；总 gate = `cells_ok AND pairing_ok`。v1.1 上线即复跑现存语料：`cells 24/24, pairing OK (files=48, unique_hashes=48), GATE PASS`——零回归。动机与历史：本轮曾出现 C 类缺陷，当时由外部 SHA256 核验代行；固化后 corpus gate 自身成为实验完整性的最后一道门。

## H2 篇幅比门禁 → 设计冻结入 Writer Instrument v2（本轮不实现）

动机：2023_C/MMA 的 W1 出现 `0.59×` 压缩，说明 `min_chars >= 5000` 只防"太短"，不防 mapping-assisted 条件因组织压缩而改变论文形态。

设计（草案，**阈值必须由下一版 preregistration 冻结，禁止依据 2023_C 事后调参**）：

```text
length_ratio = len(paper) / median(len(valid_papers in matched cohort))
0.75 <= length_ratio <= 1.25      # corpus validity gate，仅防异常压缩/膨胀
```

要点：相对约束而非抬高绝对字数（避免"写得更长"变成隐藏实验因素）；cohort 定义（同 question 同 condition 合格论文 / 全语料中位数）留给 v2 prereg 决定；**长度门禁负责防止异常压缩/膨胀，不负责制造质量**。

处置：`GENERATION_SPEC.md` 保持 FROZEN 不动；本条仅作为 Writer Instrument v2 的设计输入。

## 与路线的关系

两个 hardening 均不改变 `v3.1.x` 核心架构边界，不重跑已关闭的 P13-3D R3 结论，不产生新的实验声明。后继研究问题（组织质量度量：relationship preservation / structural organization / alignment preservation）记录于 R3 最终报告 §5，归属后续仪器研究与 P14 证据链设计参考。
