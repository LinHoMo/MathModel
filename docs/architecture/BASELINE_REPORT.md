# Capability Baseline Report — 首次能力基线（P13.0）

> 日期：2026-09-06 · 题目：**MCM/ICM 2000 C**（大象避孕飞镖种群控制，
> 本地 MMBench 语料 `2000_C`，含真实数据 data1/data2.csv）
> 项目：`projects/bench-m4-2000c/` · 测评链：`bench e2e`（run → metrics → report）
> 指标定义：`CAPABILITY_ROADMAP_P13_P17.md` §1 · 实现：`core/tools/evaluation/e2e_metrics.py`

这是本项目**第一次**回答"这个系统到底会不会做数模题"。分数不重要，
可复现、可比较的测量回路已经建立：**Baseline → 修改 Brain → 再跑 → Δscore**。

## 1. 测量回路（本次如何跑的）

```text
bench e2e run        真题导入（题面+数据）→ V3 认知管线（4 问题骨架）→ 指标底座
agent 真实解题       code/main.py：生存率估计 + Leslie 矩阵 + 避孕配额 +
                     bootstrap 不确定性 + 灾难恢复 + 规模泛化（seed=42，5 批 × 200 次）
                     → figures/all_results.json（全真实数值）→ output/MODEL_SPEC.md
                     + output/management_memo.md
证据注册             code/register_artifacts.py：真实实验/结果/声明入 V3 链
                     （E005-E008 → R005-R008 → C005-C008，claims 8/8）
GT + 评分            work/e2e_gt.json（8 要求项 + 6 方法族金标准）
                     work/e2e_response.json（agent 对照 GT 自评，口径公开）
bench e2e metrics    八项指标重算落盘 work/e2e_metrics.json
```

## 2. 基线分数

| 指标 | 值 (0-100) | 说明 |
|---|---|---|
| decomposition 子问题覆盖率 | **100** | 4 问题覆盖 8/8 金标准要求项 |
| method selection 方法正确率 | **0** | 管线 4 问全选 TOPSIS/AHP——见 §4 根因 |
| model correctness 数学正确性 | **70** | 方法族正确 + 搬迁均衡 700 与题面一致；扣分：校准乘子过大、无密度制约、仅雌性矩阵 |
| experiment validity 实验有效性 | **100**\* | 真实实验带 baseline/sensitivity/multi_run 标签、runs=5、seed 固定 |
| validation reliability 结论可靠性 | **100**\* | V3 证据链 8/8 claims 被支撑；论文侧校验缺席（见 \*） |
| innovation 新颖且可验证 | **0** | 无创新模式声明（patterns 未被管线消费） |
| writing completeness 论文完整度 | **n/a** | 未生成 paper/main.tex |
| end-to-end 最终成绩 | **71** | 分解：T1 21/25 + T2 22/25 + T4 13/15 + T5 8/10 + T6 7/10 + 论文 0/15 |
| **可得均值** | **63.0**（7/8 可算） | |

\* 口径披露：这两项由 V3 产物记账计算，其中确定性管线的占位产物与
agent 真实产物共同计入（占位产物自带稳健性标签）；它们度量的是
**证据链完整性与实验记账规范**，不是"实验做得对"——后者由 model
correctness 与评委 rubric 承担。写作侧校验（fact_check / 引用 / 数值
一致性）在论文缺席时不计入。

## 3. 测量回路当场抓到的 bug（基线的第一次胜利）

外部一致性校验（模型反推的搬迁均衡额应落在题面实际 600-800 头/年）直接
暴露了三处实现错误，全部修复后数字才收敛到物理合理区间：

1. 搬迁移除分数多乘一次雌性份额（r/total 被写成 r·share/total → 均衡
   1371 头，物理不合理）；
2. `calibrate_fertility` 把递增函数喂给要求递减的二分（收敛到上界 →
   p*=61.7% 的荒谬配额）；
3. 避孕情景年龄结构循环丢失"新注射"步骤（前后幼龄份额相同）。

这正是"测量优先"路线的价值：没有基线校验，这三个 bug 会一直潜伏。

## 4. 根因发现（P13 的靶子）

- **method_selection = 0 的两个根因**：
  1. **问题分解的语义没有进入管线**——RuntimeSession 只接收 `Q001…`
     标签，检索器看不到"生存率估计/Leslie 矩阵"的任务语义，选型退化为
     对空语义的默认打分（TOPSIS/AHP）；
  2. **知识库没有种群动力学方法卡**——16 张卡无 Leslie/生存分析/年龄
     结构家族，即便语义可见也无卡可选。
- **innovation = 0**：6 张创新模式卡存在但确定性管线从不消费
  （decision log 无 `pat-*` 引用）——知识层与执行层之间断路。
- **真实求解靠自己兜底**：本次解题的正确性完全来自 agent（Brain），
  runtime 骨架只提供记账与护栏——这正是三层定位的实证。

## 5. P13 backlog（按预期 Δ 收益排序）

1. **问题语义接入**：分解产出的任务文本进入检索器（预期 method
   selection 显著提升，decomposition 保持 100）；
2. **方法卡扩充**：种群动力学/生存分析/频率拟合等缺失家族（16 → ~24 卡）；
3. **论文生成接入**：paper/main.tex + 图表 → writing completeness 从 n/a
   变为可算（预期 end-to-end +10~15）；
4. **创新模式消费**：管线在合适节点消费 pat-*（innovation 0 → 有值）；
5. **agent 结果正式接入节点**：handlers 提供 agent 实验结果登记通道，
   替代事后注册脚本（experiment validity 口径净化）。

## 6. CUMCM 种子说明（诚实记录）

计划中"CUMCM 侧选 5 题补 reference_results"**未执行**：现有 13/22 份
rubric 的参考结果为空，而凭记忆填入数值属于伪造金标准（违反 W5-W8
同级诚信红线），网络来源的"官方答案"数值可靠性无法核实。CUMCM 侧数值
GT 的唯一诚实来源是**实际解题后回填**（P13+ 每解一题回填一份）；
在此之前 e2e 基线以 MMBench 语料（自带数据与评测口径）为准。

## 7. 下一次跑分

同一题集复跑即得 Δ；P13 exit criteria：≥5 题（跨 ≥2 年）可复现基线，
且至少一项指标 +10 个百分点。
