# Capability Validation（Δscore）— P1 改造能力对比

> 日期："2026-09-10T07:54:16"
> 同题（2024_A）：pre = P1 前真实产物（B0-R2 时代）｜ post = P1 闭环产物（vs001：M1→FAIL→M2→PASS + Replay）

## 一、八项能力指标 Δ

| 指标 | pre | post | Δ |
|---|---|---|---|
| 问题分解覆盖 | 20.0 | 40.0 | +20.0 |
| 模型结构对齐（allowed_modeling_structures） | 0.0 | 0.0 | +0.0 |
| 模型正确性（gt 数值对照） | — | — | — |
| 实验有效性 | 100.0 | — | — |
| 验证可靠性 | 100.0 | — | — |
| 创新性 | 0.0 | 0.0 | +0.0 |
| 论文完备性 | 16.2 | — | — |
| 端到端 | — | — | — |

**口径说明**：`—` = 该期产物无对应环节产物（如 pre 无 model_ir → structure 0；post 无论文产物 → writing/experiment 为 None），如实不估算。

## 二、P1 专属执行级指标（Model Construction Loop 机械证据）

- 真实执行：3/3 success（rate=1.0）
- 数值验证：3 次（含 1 次如实 FAIL——M1 缺陷模型被真实拦截）
- MODEL_IR：3 个（M1/M2 独立 artifact，不覆盖）
- 修订谱系边：revision_of=1、supersede=1
- 实现/证据边：implemented_by=3、verified_by=3

## 三、结论与局限

- **P1 的直接能力证据在执行级**：真实执行 2/2 success、M1 数值 FAIL 被拦截、修订后 M2 PASS、谱系与证据边完整——这是 P1 前（无执行闭环）不存在的机制。
- **八项指标是论文管线测量**，与 P1 的模型闭环改造正交；可比项中 decomposition 20→40（P1 产物分解更完整）。
- **局限（如实）**：pre/post 是不同期真实产物，非受控 A/B——本报告是能力状态对比，因果效应测量属 K 系列实验（K001-K003 已按预注册门执行）。