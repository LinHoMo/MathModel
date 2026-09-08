# R3.2 Generation Spec — 真实 Writer 论文生成执行细则

**Status**: FROZEN (2026-09-07) · 供 Writer 执行体逐字遵守
> 2026-09-07 路径修正：P4 迁移后项目位于 `research\P13-3D-R3`，仅改物理路径，实验规则零改动。

## 1. 你（Writer）要做什么

对分配给你的每个 **(题目, arm)** 单元，做两次生成：

```
W0: 只读 artifact prompt  → 写  real_papers/W0/{qid}_{arm}.md
W1: 读 artifact + map     → 写  real_papers/W1/{qid}_{arm}.md
```

**必须先 W0 后 W1，W0 落盘后不得修改。**

## 2. 输入文件（只读，禁止修改）

| 用途 | 路径 |
|---|---|
| W0 完整 prompt | `C:\Users\Lin\Desktop\Programs\MathModel\research\P13-3D-R3\prompts\{qid}_{arm}_W0.json` |
| W1 完整 prompt | `C:\Users\Lin\Desktop\Programs\MathModel\research\P13-3D-R3\prompts\{qid}_{arm}_W1.json` |

prompt JSON 有两个字段：

- `system` — **你必须原样采纳为本次写作的系统指令**
- `user` — **你必须原样当作用户给你的写作任务**（里面是模型构件 MODEL_ARTIFACT，W1 还含结构化映射 MODEL_PAPER_MAP）

`arm` 文件名映射：`B0` → `B0`，`MMA` → `MMA`，`B1-F` → `B1_F`（例如 `2022_A_B1_F_W0.json`）。

## 3. 输出文件（必须写到精确路径）

```
C:\Users\Lin\Desktop\Programs\MathModel\research\P13-3D-R3\real_papers\W0\{qid}_{arm}.md
C:\Users\Lin\Desktop\Programs\MathModel\research\P13-3D-R3\real_papers\W1\{qid}_{arm}.md
```

其中 `{arm}` 用 `B0` / `MMA` / `B1_F`（下划线）。例如 `real_papers/W1/2022_A_B1_F.md`。

## 4. 写作硬约束

1. **忠实于构件**：论文里的变量、参数、约束、机制方程、目标函数、假设，
   必须与 `MODEL_ARTIFACT` 中给出的一一对应。**不得新增、不得删除、不得改写、不得重命名。**
2. **不得引入构件外的模型**：不要自己"补一个更合理的模型"，不要替换选定模型，不要重新论证模型选择。
   候选模型必须是构件里列出的那些，不多不少。
3. **W1 额外约束**：严格按 `MODEL_PAPER_MAP` 的 `section_map` / `element_map` /
   `candidate_model_map` / `sensitivity_map` / `question_map` 组织章节与元素落位。
   W1 与 W0 的差别**只允许是结构组织与呈现**，不允许改数学内容。
4. **公式**：LaTeX，行内 `$...$`，行间 `$$...$$`。
5. **篇幅**：正文 **6000–11000 字符**（含公式与 Markdown 标记）。不得少于 5000。
6. **10 个必需章节**（标题可用中文，顺序固定）：
   1. 摘要
   2. 问题重述
   3. 模型假设
   4. 符号说明
   5. 模型建立与求解
   6. 候选模型对比
   7. 选定模型说明
   8. 灵敏度分析
   9. 模型评价
   10. 结论

   若 `sensitivity_plan` 为空，仍需保留「灵敏度分析」章节，但**以常规学术方式自行展开**：写清将考察哪些关键参数、
   扰动范围思路与观测指标，并注明这些取值待实测数据标定。**不要凭空编造具体参数与范围**，
   也**绝对不要**出现"本构件未给出…""sensitivity_plan 为空""模型构件"这类表述。
7. **禁止元叙述（硬性，违反即作废重生成）**：论文必须读起来完全像一篇真实参赛论文。
   以下词**一个都不许出现**：
   `模型构件`、`本构件`、`构件`、`MODEL_ARTIFACT`、`MODEL_PAPER_MAP`、`结构化映射`、`映射`、
   `sensitivity_plan`、`selected_model`、`candidate_models`、`W0`、`W1`、`本实验`、`对照条件`。
   不得写"依据映射要求…""按照映射，本节…""本节对应 Q1…"这类把写作依据外露的话。
   需要引用元素编号时（如 p1、E4、M1）可以保留编号本身，但**不要解释编号来自哪里**。
8. **不要写代码块围栏包裹整篇论文**，直接输出 Markdown 正文。

## 5. 完成后回报

对每个单元报告一行：

```
{qid}/{arm}  W0={字符数}  W1={字符数}  sections=10/10
```

不要汇报论文内容细节，不要做自我评分。
