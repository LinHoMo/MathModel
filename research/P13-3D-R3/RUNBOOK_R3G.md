# R3.2 RUNBOOK — 真实 Writer 语料生成（可中断恢复）

**目的**：任何新 session（零上下文）打开本文件即可接着把 48 篇论文生成完。
**当前状态**：24/48 落盘，但 **0/24 单元通过门禁**（元叙述泄漏），需全部重生成。
> 路径口径（2026-09-07 P4 迁移后唯一入口）：项目在 `research/P13-3D-R3`，
> 语料门禁脚本在 `research/P13-3D/scripts/r3g_corpus_check.py`。旧 `projects/` 路径一律作废。

---

## 0. 三步定位（每次进入先做）

```bash
cd C:/Users/Lin/Desktop/Programs/MathModel
python research/P13-3D/scripts/r3g_corpus_check.py
```

输出末尾给出 `deficient:` 列表 —— 那就是本次要补的单元。
`sec=x/10` 表示必需章节命中数，`BAD` 原因见 `--json` 里的 `reason` 字段。

## 1. 为什么 0/24 不过（务必先读，避免重蹈覆辙）

`GENERATION_SPEC.md` 旧版规则 6 要求 Writer 在 `sensitivity_plan` 为空时写明
"本构件未给出灵敏度计划（sensitivity_plan 为空）"，W1 又被引导写"依据结构化映射…"。
结果 **48 篇里每一篇都出现了实验用语泄漏**，盲评会一眼看出条件 → 实验作废。

**规格已修**：`GENERATION_SPEC.md` 第 6、7 条现明确禁止
`模型构件 / 本构件 / 构件 / 结构化映射 / 映射 / sensitivity_plan / W0 / W1 / 本实验` 等词。
泄漏词表同步进了 `r3g_corpus_check.py::LEAK_PATTERNS`。

## 2. 生成方式：一个子 agent 负责一个题目（3 arm × 2 条件 = 6 篇）

**不要自己写**。用 Agent 工具起 `general-purpose` 子 agent，每个负责一个题目。
子 agent 的 prompt 模板（把 `{QID}` 换成题目号，共 8 个：
`2020_B` `2024_B` `2023_C` `2024_C` `2019_A` `2022_A` `2017_B` `2022_C`）：

```
你是 R3.2 实验的 Writer 执行体。请为题目 {QID} 生成 6 篇真实数学建模竞赛论文。

第一步（必读）：读 C:\Users\Lin\Desktop\Programs\MathModel\research\P13-3D-R3\GENERATION_SPEC.md，
逐条遵守，尤其第 7 条「禁止元叙述」。

背景：已预注册的对照实验，自变量只有一个——是否给 Writer 提供"结构化映射层"。
W0 只给模型构件，W1 给模型构件+映射。两篇必须同等风格、同等深度、同等篇幅，
W1 不允许额外发挥或写得更详细，只允许结构组织更贴合映射。

根目录：C:\Users\Lin\Desktop\Programs\MathModel\research\P13-3D-R3
按 arm 顺序 B0 → MMA → B1_F，对每个 arm：
1. Read prompts/{QID}_{arm}_W0.json，将 system 原样作为写作系统指令、user 原样作为写作任务
2. Write real_papers/W0/{QID}_{arm}.md（覆盖已有文件；6000–11000 字符，10 章节齐全）
3. Read prompts/{QID}_{arm}_W1.json
4. Write real_papers/W1/{QID}_{arm}.md

上一版被判不合格的原因，务必避免：
- 篇幅不足 6000 字符
- 出现"本构件""模型构件""sensitivity_plan（为空）""依据结构化映射"等实验用语（元叙述泄漏，破坏盲评）

每篇独立一个 Write 调用。每个 arm 内 W0 先落盘，再写 W1，W0 不得回改。
完成后只回报 3 行：{QID}/{arm}  W0={n}chars  W1={n}chars  sections=10/10
```

**并发**：一次最多起 4 个子 agent。遇到 `429 使用量超出频率限制` 立即停止并发，
改为单发，或等到错误里给的 `重置` 时间之后再跑。

## 3. 单元 → 文件映射（供校验）

| qid | arm 文件名 | W0 输出 | W1 输出 |
|---|---|---|---|
| * | `B0` / `MMA` / `B1_F` | `real_papers/W0/{qid}_{arm}.md` | `real_papers/W1/{qid}_{arm}.md` |

prompt 文件名同构：`prompts/{qid}_{arm}_W0.json` / `_W1.json`。

## 4. 生成完成后的执行顺序（不得跳步）

```bash
# R3-G2 门禁：48/48 且全部 ok
python research/P13-3D/scripts/r3g_corpus_check.py

# R3-G3 STC v2（core/meta/overall，逐元素）
# R3-G4 Fidelity Gate v2（mutation）
# R3-G5 Blind PQ（随机化编号、评审盲态）
# R3-G6 配对分析 → H13–H18
```

门禁通过前 **禁止**运行 STC / PQ 评估，禁止据此调整 prompt 或映射。

## 5. 进度快照（2026-09-07 13:40）

| 项 | 状态 |
|---|---|
| R3-G0 冻结协议 v2 + 预注册 + 归档旧语料 | ✅ |
| 24 个冻结 artifact / 24 个冻结 map / 48 个冻结 prompt | ✅ |
| 语料生成 | ⚠️ 24/48 落盘，0 单元合格（泄漏），需全量重生成 |
| 阻塞原因 | 账户 429 限流，18:09（UTC+8）重置 |
| R3-G2 ~ G7 | ⬜ 未开始 |
