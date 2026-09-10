# P15-K004 报告：L5 Revision 闭环端到端度量

> 预注册：`research/P15/protocol/preregistration/P15-K004-DRAFT.md` v1.0
> 生成：2026-09-10 ｜ 数据：`k004_report.json`（18 单元全量明细）

## 结论

**H1 SUPPORTED**：Δ_L6 均值 = +1.0000，95% CI = [+1.0000, +1.0000]（18 单元
配对差分，bootstrap 10000 次）。L5 Revision 闭环（M1 FAIL → revision → M2 PASS）
在 Runtime 层**系统性**地把模型从"可检测错误"修正为"数值正确"。

| 端点 | 结果 |
|---|---|
| Δ_L6（主） | +1.0000 CI[+1.0000, +1.0000]，H1 支持 |
| M1 失败真实性（G2） | 18/18（L6 判 FAIL，非崩溃非 invalid） |
| M2 通过（G3） | 18/18（L6 判 PASS） |
| Replay（G4/G5） | 18/18（subprocess 真实执行） |
| 修正轮数 | 均值 1.0（一次修订即达 PASS） |

## 方法与限制（如实披露）

- 模板：P1-VS-001 M/M/c 排队（2019_C Q1），6 变体 × 3 种子 = 18 单元；
  错误注入机械确定性（service_rate → rho>1 → cvm>0 → L6 FAIL），
  修订注入正确参数版 M2。
- **测量范围**：本实验证明"Runtime 能系统性完成**已检测**错误的修订、验证与
  谱系记录"（Revision 执行/验证层）。**不测量**"Agent 能否发现新错误"
  （Revision 提议层）——后者属 Constructor 能力，需 K004 v2（多题 + LLM 错误
  注入 + 裸 Constructor 对照臂）。
- 全机械判定（无 LLM 盲评）：L6 由 `validate_against_gt`（2019_C gt 断言
  feasibility + objective_sane）判定，无评估者偏差。
- Δ=+1 为饱和结果（机械注入保证可修正）：如实报告，不夸大普适性。

## 对 K002 SV−F(VAL)=+4.81 假设的承接

K002 SV 臂（MODEL_IR + Validation Plan）的 VAL 正增益，本实验给出机制解释：
**验证义务 → 可检测失败 → Revision 闭环修正**——即"验证 + 修订"链条在 Runtime
层真实可执行，是结构化表示提升终态质量的因果路径之一。K004 提供了该路径的
首个系统级可执行证据（单题模板范围内）。
