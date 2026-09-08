# R3.2 最终报告：真实 LLM Writer 下显式结构传输的效果判定（G7）

- 预注册：`docs/architecture/R3_2_REAL_WRITER_PREREG.md`（FROZEN，2026-09-07）
- 生成规格：`research/P13-3D-R3/GENERATION_SPEC.md`（FROZEN）
- 执行链：G0 冻结 → G1 语料生成（48 篇）→ G2 语料门禁 → G3 STC v2 → G4 Fidelity v2 → G5 Blind PQ → G6 配对分析 → →报告
- 判定日期：2026-09-07
- 状态：**实验收口，正式结论以下文 H13–H18 为准**

## 1. 研究问题（R3）

> 显式 `MODEL_PAPER_MAP` 是否能够在不修改模型内容的前提下，提高 Model→Paper 的结构传输（STC）与论文质量（PQ），同时不增加未经授权的模型变异（Mutation）？

## 2. 设计与执行摘要

24 个单元（8 题 × 3 arm：B0 / MMA / B1-F），每单元两条件：W0（仅模型构件）与 W1（构件 + 显式映射层）。生成规格冻结数学内容（W1 只允许结构重组），因此自变量的可行作用通道为：meta 元素（候选模型 / 选定模型 / 灵敏度计划）的显式调度与章节组织。

语料：48 篇真实 LLM 生成论文，全部通过 R3-G2 语料门禁（篇幅 / 10 章节 / 泄漏词 / 10 章节齐全），24/24 单元合格。生成批次：主批次 13:37–15:21（47 篇）+ 修复批次 20:25–20:27（1 篇对，见 §6）。

盲评协议：每题 6 篇匿名（随机编号 seed 42，8 个独立评委），评分维度 4 项（0–100），PQ = 均值；密钥文件在评审上下文之外；评审 standalone 评分（题面全文不在仓库中，以论文自身问题重述为参照，48 篇统一口径）。

## 3. 结果：H13–H18

| 假设 | 判据 | 实测 | 判定 |
|---|---|---|---|
| H13 结构传输 | mean ΔSTC_meta ≥ +0.15 且配对单侧 p<0.05 | **−0.035**（t=−0.894, p_t=0.810；Wilcoxon n=4, p=0.828） | **FAIL** |
| H14 论文质量 | mean ΔPQ ≥ +5 且 p<0.05 | **−0.01**（t=−0.056, p_t=0.522；Wilcoxon p=0.220） | **FAIL** |
| H15 能力恢复 | (PQ_B1F−PQ_B0)\|W1 > 同\|W0 且差 ≥ +10 | d1=+2.50，d0=+2.38，diff=**+0.13** | **FAIL** |
| H16 无未授权变异 | Mutations(W1) ≤ W0+2 且逐单元不劣化 | **271 → 263**（−8），恶化单元=无 | **PASS** |
| H17 机制证据 | Spearman(ΔSTC_meta, ΔPQ) > 0.5 | **+0.001** | **FAIL** |
| H18 核心内容保持 | mean ΔSTC_core ≥ −0.05 且无单元 < −0.15 | mean **−0.014** ✓；min **−0.333** ✗（2020_B/MMA；2022_A/MMA −0.167） | **FAIL** |

四象限判定：**无效果且无害（No-effect & Harmless）**。

批次敏感性：剔除修复批次单元 2020_B/B0 后，H13 更负（mean −0.058, p=0.956）——结论对语料修复不敏感，且该单元是唯一映射方向为正的单元。

长度协变量：W1/W0 字符比均值 0.997（条件间篇幅受控）；越界单元 2023_C/MMA（0.59，W1 被压缩，ΔPQ=−2.4，未见质量收益）。

## 4. 解读

1. **质量方差由构件质量（arm）主导，不由 Writer 条件主导。** 盲评中 arm 间 PQ 差异巨大（如 2024_B：B1-F arm ≈82.7 vs B0 arm ≈64.3、MMA ≈66.7，跨 arm 差约 18 分），而同单元 W0/W1 差均值仅 −0.01。这直接支持 Harness 的产品论点：**Model→Paper 的质量上限由 Model Construction 决定**；Writer 侧结构干预在内容受控时是近似无操作。
2. **映射的真实作用是"组织"而非"内容"**，而本轮测量链（STC v2 元素提及式 + fidelity 内容忠实度）主要测内容层；组织质量的提升真实存在（抽读可见：小节编号化、符号表按状态/决策/参数重排、灵敏度参数主次重排），但只能通过 PQ 的 communication 维度部分体现（个别单元 +0.3~+0.5，方向一致、量级不足）。
3. **W0 基线已接近饱和**：W0 冻结 prompt 本身已强制全部组件在场，映射对"在场性"（STC 可测部分）没有额外杠杆——这是 H13 零效应的机制解释。
4. **映射是弱保护性的**：H16 不但通过，总变异还下降 8 起（271→263），三个 W1 被压缩的单元变异同步下降。显式调度未诱发任何额外越界。

## 5. 仪器局限（解释力边界）

- STC v2 为元素提及式二值/比例度量，**不含组织质量维度**；PQ 的 communication 维度是唯一部分覆盖该通道的指标，且为单评委。
- Fidelity 匹配器对改写不敏感（全部论文触发 P1/P3/P5/P6），绝对值噪声大，仅配对差值可用。
- PQ 为每题单评委、单轮，无评分者间信度估计；ΔPQ 的置信区间宽于 +5 判据，但不能排除极小正效应。
- 题面全文不在仓库，盲评以论文自身问题重述为参照（48 篇统一口径，对条件无差分偏倚，但 problem_alignment 维度的解释力受限）。
- 语料中数学错误随 arm 分布（如 2024_B 两个 arm 的损失函数语义缺陷、2024_C 一个 arm 的轮作约束违反），这些是构件级缺陷，两条件同源继承——恰好再次隔离了"Writer 干预不修数学"的边界。

## 6. Provenance 与执行日志（2026-09-07）

1. P4 迁移缺陷修复：`research/P13-3D/scripts/` 27 个脚本 ROOT 计算修正（`parents[3]`）；此前 `r3g_corpus_check.py` 曾误报 0/48。
2. 路径卫生：RUNBOOK / GENERATION_SPEC / RESUME 中旧 `projects/P13-3D-R3` 路径修正为 `research/P13-3D-R3`；语料门禁唯一入口 `research/P13-3D/scripts/r3g_corpus_check.py`。
3. 语料来源：主批次 47 篇由前一会话于 13:37–15:21 按冻结 prompt 生成（W0→W1 逐 arm 交错落盘，冻结输入 mtime 均早于生成且未被改动）；RUNBOOK 13:40 的"429 阻塞至 18:09"快照已过期。
4. 语料门禁盲区外补：48 篇 SHA256 全库去重发现 **2020_B/B0 单元 W0/W1 字节级相同**（配对失效），已按冻结 prompt 重生成（20:25–20:27，修复批次），复跑门禁 24/24 PASS、全库零重复。**建议后续将配对唯一性检查固化进 r3g_corpus_check.py**（本轮以外部哈希核验代行，未改动冻结仪器）。
5. G3–G6 由本会话按预注册执行：STC v2 / Fidelity v2 原样调用（校准状态 F1=1.000 未动）；盲评 8 包 + seed 42 + 密钥隔离（key 存放于 blind/ 上一级）。
6. 模拟结果降级：`output/evaluation/hypothesis_results.json`（R3.1 模板语料 + 模拟评估的 H13/H14/H15 FAIL、H16 PASS）自本报告起**降级为 pipeline/sanity evidence**，不进入正式结论。

## 7. 结论（R3 Final Answer）

> 在真实 LLM Writer、数学内容冻结的条件下，显式 `MODEL_PAPER_MAP` **未能**提升 Model→Paper 的结构传输与论文质量（H13/H14/H15/H17 FAIL），**但也不增加**未经授权的模型变异（H16 PASS，且总变异略降）；核心内容保持均值达标但存在两个越界单元（H18 FAIL，2020_B/MMA −0.333、2022_A/MMA −0.167）。

对 Harness 的含义（研究结论，不改 runtime）：

- Model→Paper 的主要杠杆在**构件质量**（arm 维度），Writer 侧结构映射在当前仪器与内容受控设计下无可测收益——资源应优先投向 Model Construction 与 P14（Model → Experiment/Evidence）。
- 映射层保留为**无害选项**（H16 通过）；若未来启用，需先建立能测"组织质量"的仪器（结构对齐评分、多评委 PQ、章节—元素对齐矩阵），否则无法验证其收益。
- 两个 H18 越界单元提示：压缩式改写（W1 更短）可能造成元素丢失，GENERATION_SPEC 的"同等篇幅"约束建议在后续轮次中以机械门禁（字数比 ∈ [0.85, 1.18]）强制。

## 8. 产物清单

| 产物 | 路径 |
|---|---|
| 冻结清单（48 sha256/mtime/批次） | `real_evaluation/corpus_manifest.json` |
| G3 STC v2 逐论文结果 | `real_evaluation/r32_stc.json` |
| G4 Fidelity v2 逐论文结果 | `real_evaluation/r32_fidelity.json` |
| G5 盲评包 / 原始评分 / 去匿名结果 | `real_evaluation/blind/`、`real_evaluation/r32_blind_pq.json`、`real_evaluation/blind_key.json` |
| G6 配对分析（H13–H18） | `real_evaluation/r32_paired_analysis.json` |
| 评测器（本轮新增，research 轨道） | `research/P13-3D/scripts/r32_eval.py` |
| 单一状态真源 | `research/P13-3D-R3/state/status.json` |
