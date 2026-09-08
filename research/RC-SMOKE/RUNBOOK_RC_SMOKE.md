# RC Smoke Runbook — 独立验证线（与 P14 完全分离）

- Status: **FROZEN v1 (2026-09-07)** · 目的：回答唯一问题——
  > **这个已经冻结的 Harness（v3.1.0-rc1），面对真实用户任务，能不能从头跑到底？**
- 性质：RC 验证，不是科研实验；不产生研究结论；不借 smoke 结果修改架构。

## 1. 三条线

| 线 | 链路 | 材料 | 状态 |
|---|---|---|---|
| S1 Competition | 真题 → Harness → Model → Artifact → Quality Gate | `tests/fixtures/sample_incomplete_project/inputs/problem_cumcm2024A.txt`（2397B，真实 2024A 题面） | **就绪** |
| S2 Research | 科研问题 → Harness → Model → Experiment → Evidence | 待用户提供科研建模问题 | **阻塞（等材料）** |
| S3 Provider | 同一 workflow → external provider → canonical artifact | `core/adapters/` 当前为空，需先盘点 runtime/env 层的外部执行路径，定义 smoke 入口 | **阻塞（需盘点）** |

## 2. 每线判定

PASS = 全流程跑通且：产物经对应门禁（validate / gate / hash chain）全绿；status.json 可 `reconcile` 对账；run 可 `replay.py` 重放；无占位符/伪造引用。

FAIL 分级：
- **A 类（重开 RC issue）**：core runtime / canonical domain / state truth / replay / provider boundary 的真实缺陷。
- **B 类（不重开 RC）**：模型表现不好、评分不高、Writer/Builder 产出质量、提示词问题 → 归 `research/` `provider/` `skill/` `benchmark/` `instrument/` 层处理。
- **C 类（材料问题）**：题面/数据/配置不完整 → 补材料重跑，不计缺陷。

> 铁律：**不能因为 smoke 中模型表现不好就重新改架构。** 每条线收口产出一份 smoke 记录（入口命令、逐环节输出、门禁结果、缺陷分级清单）。

## 3. 执行顺序

S1 就绪即可跑（消耗真实 LLM 配额，执行前确认）；S2 等材料；S3 先做执行路径盘点（半小时级）再定入口。三线相互独立，各自收口。

## 4. 与 P14 的边界

- RC smoke 不使用 P14 的任何实体/门禁；P14 不因 smoke 结果调整冻结契约。
- 两条线唯一的交汇点：S3 Provider 线若暴露 provider boundary 缺陷，按 A 类开 RC issue，与 P14 无关。
