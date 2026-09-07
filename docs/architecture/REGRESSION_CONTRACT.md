# REGRESSION_CONTRACT — 五轴 Non-regression 契约（System Hardening P5）

> 建立：2026-09-07 ｜ 机器判据：`python -m pytest tests/regression -q` 全绿 = 五轴通过
> 把「不降级」从人的判断变成机器可判的契约。任何兼容性声明必须在这里兑现。

## 五轴定义与判据

| 轴 | 定义 | 机器判据 | 载体 |
|---|---|---|---|
| **functional** 功能不降级 | V2 29-step legacy 模式全部核心能力仍可用 | R1–R8 全部 PASS（new_project / state init / gate CLI / catalog v5 双视图 / manifest 无漂移 / orchestrator V3+legacy 干跑 / validate / doctor） | `tests/regression/test_v2_capability_regression.py` |
| **semantic** 语义不降级 | 旧 artifact/evidence 可读且含义不变 | 归档样例可打开（status schema_version==3 + registry/graph 可解析）+ reconcile 报告可产出 | `test_non_regression_contract.py::test_semantic_axis` |
| **quality** 质量不降级 | 能力指标不倒退 | `research/bench-m4-2000c/work/e2e_metrics.json` 与基线锚点逐指标对照：无指标下降 > 5 个百分点 | `test_non_regression_contract.py::test_quality_axis` |
| **data** 数据不降级 | 旧项目可迁移 | V2 `work/state.json` → `convert_project()` → `state/status.json`（schema_version 3，legacy-imported） | `test_non_regression_contract.py::test_data_axis` |
| **operational** 运行不降级 | crash/resume/rerun/invalidate 生命周期语义不坏 | 崩溃一致性 + 对账 + RuntimeSession 端到端测试全绿 | `test_non_regression_contract.py::test_operational_axis` |

## 基线锚点（quality 轴，机器文件为真源）

锚点 = `research/bench-m4-2000c/work/e2e_metrics.json`（八项指标机器重算结果），
与 `docs/architecture/BASELINE_REPORT.md`（2026-09-06 基线）保持一致；两者冲突时
**以机器文件为准**（状态真源原则，同 STATE_TRUTH）。

| 指标 | 基线值 |
|---|---|
| decomposition | 100 |
| method selection | 0（已知 backlog：TOPSIS/AHP 全选，见 BASELINE_REPORT §4） |
| model correctness | 70 |
| experiment validity | 100 |
| validation reliability | 100 |
| innovation | 0（patterns 未被管线消费，已知 backlog） |
| writing completeness | n/a（未生成 tex） |
| end-to-end | 71 |

**裁决规则**：quality 轴对「已计算」指标执行 `当前 ≥ 基线 − 5`；指标因输入缺失
记为 absent/n/a 不扣分但必须如实报告（同 BASELINE §1「缺输入如实记 n/a」）。

## 执行与治理

- 单命令：`python -m pytest tests/regression -q`；退出码 0 = 五轴通过。
- `docs/STATUS.md` 的 `Non-regression: 5/5` 行只允许抄这条命令的机器输出。
- 新功能/重构合入前必须重跑；轴失败按 COMPATIBILITY_POLICY 的例外流程处理
 （修复根因，禁止放宽阈值来"通过"）。
- 基线更新流程：能力实验产生正 Δ（Δscore 判据）后，把新的 e2e_metrics.json
  与 BASELINE_REPORT 一并更新并记录 commit——**不允许单方面改基线**。