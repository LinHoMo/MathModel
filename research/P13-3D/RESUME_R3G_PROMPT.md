# R3.2 重启提示词（新会话直接复制使用）

> 资产核对快照（2026-09-07 13:30，由主会话门禁实测，非口述）：
> - 24 冻结 artifact（`research/P13-3D-R2/output/artifacts/`）+ manifest ✅
> - 24 冻结 map（`research/P13-3D-R3/output/maps/`）✅
> - 48 冻结 prompt（`research/P13-3D-R3/prompts/`）✅
> - real_papers：仅 2019_A / 2022_A / 2017_B / 2022_C 四题共 24 篇落盘；
>   2020_B / 2024_B / 2023_C / 2024_C 四题 **0 篇**（MISSING）。
> - 门禁实测 `cells ok = 0/24, papers = 24/48`。落盘的 24 篇均为 BAD（泄漏词或 <5000 字符）。
> 因此 8 题 × 6 篇 = 48 篇**全部需生成**，但请仍以下方第一步门禁实测为准。

---

复制以下整段到新会话（把 `R3.2 真实 Writer 对照实验 —— 接续生成（48 篇论文）` 以下内容粘贴）：

---

# R3.2 真实 Writer 对照实验 —— 接续生成（48 篇论文）

## 背景
这是 P13-3D 项目的 R3.2 预注册实验（docs/architecture/R3_2_REAL_WRITER_PREREG.md），
目标是生成 48 篇"真实 Writer 论文"做 W0(仅构件) vs W1(构件+映射) 配对对照。
测量器 STC v2 已修复并校准，协议已冻结，现在唯一要做的是**生成合格语料**。
工作目录：C:\Users\Lin\Desktop\Programs\MathModel
项目目录：C:\Users\Lin\Desktop\Programs\MathModel\projects\P13-3D-R3

## 第一步（必做）：先定位真实缺口
python core/tools/evaluation/r3g_corpus_check.py
```
（在 MathModel 根目录跑；它会列出 24 个单元中哪些 W0/W1 缺失或不合格，
原因写在 --json 输出的 reason 里。以此为准，别信口头描述。）

## 第二步：读两份冻结规格（逐条遵守）
1. research/P13-3D-R3/GENERATION_SPEC.md  —— 论文写作硬约束（尤其第 7 条"禁止元叙述"）
2. research/P13-3D-R3/RUNBOOK_R3G.md      —— 分题生成协议 + 每题的现成子 agent 提示词模板

## 第三步：生成（用子 agent，一次一个题目 = 3 arm × 2 条件 = 6 篇）
对每个尚未合格的题目 {QID}（共 8 个：2019_A 2022_A 2017_B 2022_C 2020_B 2024_B 2023_C 2024_C），
用 Agent 工具起 general-purpose 子 agent，prompt 照抄 RUNBOOK_R3G.md 第 2 节模板（把 {QID} 替换成题目号）。
- 每个子 agent 内部按 B0→MMA→B1_F 顺序，每个 arm 先写 W0 落盘、紧接写 W1，W0 不得回改。
- 输出路径：real_papers/W0/{QID}_{arm}.md 与 real_papers/W1/{QID}_{arm}.md（arm 用 B0/MMA/B1_F，下划线）。
- 输入 prompt：research/P13-3D-R3/prompts/{QID}_{arm}_W0.json / _W1.json，其中 system 原样作为系统指令、user 原样作为写作任务。

## 第四步（关键纪律）
- 每篇 6000–11000 字符，10 个必需章节齐全（摘要/问题重述/模型假设/符号说明/模型建立与求解/
候选模型对比/选定模型说明/灵敏度分析/模型评价/结论）。
- 论文内"禁止出现"：模型构件、本构件、构件、结构化映射、映射、MODEL_ARTIFACT、MODEL_PAPER_MAP、
sensitivity_plan、selected_model、candidate_models、W0、W1、本实验、实验条件 —— 全部是泄漏词，破坏盲评。
- 不要自行"补更合理的模型"或替换选定模型；候选模型必须是构件里列出的那些。
- W1 与 W0 只允许结构组织差异，不允许改写数学内容或写得更详细。

## 第五步：并发纪律（防 429 限流）
每次最多并行 2–3 个子 agent。若报错 429"使用量超出频率限制"，停止并发，改单发，
或等到报错里给的"重置"时间后再跑。宁可串行也不触发限流导致任务卡死。

## 完成标准
python core/tools/evaluation/r3g_corpus_check.py   →  24/24 单元 PASS（48 篇齐全、无泄漏、篇幅达标）
跑通后停止，回报：已合格单元数/24，并把门禁输出尾部贴给我。
不要在语料门禁通过前运行任何 STC / PQ 评估，也不要据此修改 prompt 或映射。

## 我已经替你确认好的输入资产（不用重建）
- 24 个冻结 Model Artifact：research/P13-3D-R2/output/artifacts/*.json
- 24 个冻结 Model→Paper Map：research/P13-3D-R3/output/maps/*_map.json
- 48 个冻结 Writer prompt：research/P13-3D-R3/prompts/*_W*.json
