# P15-K004-ref（P2-1b 参考臂尝试）——失败归档记录

> 归档日期：2026-09-10 ｜ 来源：并行会话（opencode）的 P2-1b 尝试
> 状态：**FAILED / NOT VALID DATA**（如实标注，禁止引用为 benchmark 结果）

## 事实

- `results/k004_ref_results.json`：32 条 Reference Constructor × RT 记录
  （8 题 × 2 seeds × R0/R1）
- **exec_status 分布：`not_executed` 16 / `error` 16 —— 0/32 执行成功**
- 结论：这是未完成的实验尝试（run_k004.py 调用 Reference Constructor
  执行全部失败），**不构成任何 benchmark 证据**。

## 为什么保留

失败记录也是证据（The Agent Is Not The State）：避免后人误以为
"Reference 臂已有数据"。正式 K004 见 `experiments/P15-K004/`
（18 单元 M/M/c 模板，Δ_L6=+1.0 CI[1,1] H1 SUPPORTED）；
Constructor-independent 正式设计见 `benchmark/constructor_independent/`
（P15-K005，120 runs 数据收集 BLOCKED 待外部 Constructor）。

## 教训

- "有数据文件" ≠ "有有效数据"；引用任何实验数字前必须检查
  exec_status / validation_status 分布。
- 并行会话的中间工作区（`research/P15/k004/`）未整理即留痕，
  归档于此并标注，不再作为活动代码目录。
