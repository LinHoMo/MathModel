# P15-K004 预注册实验：L5 Revision 闭环端到端度量

> 状态：DRAFT v1.0 ｜ 日期：2026-09-10 ｜ 继承：P1-2（Revision 接入主 DAG）、P2-1（L6 判定）、P1-VS-001（M/M/c 模板）
> 关联：`ROADMAP.md → P3-2`

## 1. 研究问题（RQ）

L5（Model Revision）闭环在 Runtime 层是否**系统性地**把模型从"可检测错误"修正为
"数值正确"？量化为配对差分：

```
Δ_L6 = L6(R1 终态) − L6(R0 终态)
```

- R0（无 revision）：M1（注入确定性错误）执行 → L6 判定（预期 FAIL）
- R1（有 revision）：M1 执行 → FAIL → 注入 revision 包（正确 M2）→ 主 DAG
  revision 闭环 → M2 重跑 → L6 判定（预期 PASS）

## 2. 假设

- H1（修正有效性）：R1 的 L6 终态通过率 > R0（配对差分 Δ_L6 > 0）
- H2（失败真实性）：错误注入后 M1 的 L6 判定为 FAIL（非崩溃、非环境问题），
  即错误被"可检测"——L6 有区分度
- H3（可重放）：revision 闭环产物可 Replay（同输入同输出）

## 3. 设计

- **模板**：P1-VS-001 的 M/M/c 机场出租车排队模型（2019_C Q1），
  参数化 `(arrival_rate, num_servers, service_rate)`；
  错误注入 = `service_rate` 错误值使 `rho = λ/(c·μ) > 1`（系统不稳定）→
  `constraint_violation_max > 0` → L6 feasibility FAIL；修订 = 正确 `μ`
  使 `rho < 1` → cvm=0 → PASS。
- **单元**：6 变体 × 3 随机种子 = **18 单元**（变体 = λ 与 c 的不同组合，
  种子 = 到达序列随机性）。
- **每单元两臂**：R0（M1 孤跑）/ R1（M1→revision→M2）。
- **L6 判定**：`problem_cards/2019_C/gt.json#l6_assertions` v1.0
  （feasibility + objective_sane，数学必然，非答案数值）。
- **执行**：真实 subprocess（LocalPythonAdapter），stdout 末行 JSON 约定，
  仅依赖标准库（math/json）。

## 4. 端点

| 端点 | 定义 | 分析 |
|---|---|---|
| 主：Δ_L6 | 每单元 R1 终态 L6 score − R0 终态 L6 score（0/1 化 passed） | 配对差分 + bootstrap 95% CI（10000 次） |
| 次：修正轮数 | R1 中 FAIL→PASS 需要的 revision 次数 | 均值/分布 |
| 次：失败真实性 | M1 的 L6 判定（FAIL 且非 invalid） | 计数/18 |
| 次：Replay | revision 闭环 replay 成功 | 计数/18 |

## 5. 预注册 Gate（全部必须 PASS 才进入正式分析）

- G1 映射：18 单元 →（变体, 种子, 臂）双射可审计
- G2 注入有效性：18/18 M1 执行成功且 L6=FAIL（非崩溃非 invalid）
- G3 修订有效性：18/18 M2 执行成功且 L6=PASS
- G4 执行真实性：全部 subprocess 真实执行（有 execution_id/哈希）
- G5 功效：18 单元 × 配对差分，n=18 双侧 95% CI 报告（如实，不夸大）

## 6. 判定规则（预注册，禁止事后调整）

- H1 支持：Δ_L6 的 95% CI 下界 > 0
- H1 拒绝：CI 含 0
- **negative result 如实报告**（与 K001/K002 同纪律）

## 7. 范围与限制（如实披露）

- 单题模板（2019_C M/M/c）：结果不推广到全部题型；6 题全覆盖列为
  K004 v2 扩展（需多题模板化）。
- 错误注入为确定性机械注入（非 LLM 生成的多样错误）：测量的是
  "Runtime 能否系统性完成已检测错误的修订"，不是"Agent 能否发现新错误"。
- Revision 提议来自外部 Constructor（本实验直接注入正确 M2 包），
  测量 Revision **执行/验证/谱系**能力，不是 Revision **提议**能力。

## 8. 产物

- `research/P15/experiments/P15-K004/`：runs/（18 单元 × R0/R1 产物）、
  k004_report.json、K004_REPORT.md
- 脚本：`research/P15/scripts/k004_runner.py`
- 冻结/盲评：本实验全机械判定（无 LLM 盲评），无需 evaluator
