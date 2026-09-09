# P15-K003 — Model Representation Efficacy under Executed Construction
## 预注册研究设计 DRAFT（v0.1）

> 日期：2026-09-09 ｜ 状态：**DRAFT（五 Gate 全部 PASS，2026-09-09 → 待 PREREGISTERED → FROZEN）**
> 上游证据：P15-K001（Δ_K=+2.14 CI[+0.00,+6.41] negative）· P15-K002
> （RQ1 S−F(MCQ)=−4.85 CI[−7.98,−2.22] NEGATIVE，归因 L3 格式不对称）·
> P1（VS-001 闭环 7/7，run_code_pipeline 真实执行可用）
> 本设计不修改 K001/K002 任何冻结项；K002 已 CLOSED。

---

## 0. 动机（为什么需要 K003）

K002 是**纯表示实验**：产物（F/S/SV 表示文件）不含真实执行。结果 RQ1
S−F(MCQ)=−4.85 NEGATIVE，但归因分析指出主因是 **L3 层格式不对称**——

- S 臂结构化 JSON 暴露"无执行证据"（L3.2 系统性低分）；
- F 臂自由文本可叙述性声称执行/验证（评分高于事实）。

因此 K002 的 L3 测的是"**执行证据声明完备性**"，不是"**真实执行质量**"。
S<F 不能归因于表示本身（混淆变量：声明 vs 事实）。

**K003 的核心设计改动：构造+执行一体化。** 三个臂的产物都必须经过
harness 真实执行（P1 的 `run_code_pipeline`），执行产物（execution_result /
数值验证 VR）进入盲评包。此时 L3 的评分对象是**真实执行事实**，三个臂
在执行证据上地位平等——干净测量"表示形式 → 模型构造质量"。

## 1. 研究问题与假设

**RQ1（主）**：在"构造+执行+验证"一体化条件下，结构化 Model Representation
（MODEL_IR）相对自由文本是否提升外部 Agent 的模型构造质量（MCQ_primary）？

- H0：Δ(S−F) ≤ 0
- H1：Δ(S−F) > 0（结构化表示在可执行条件下提升构造质量）

**RQ2（次）**：在 S 基础上强制 Validation Plan 字段（S+V）是否额外提升
验证质量（VAL_primary=L4）？K002 已观测 SV−S(MCQ)=+5.25 CI[+3.64,+6.67]
POSITIVE（敏感性 A），K003 在可执行条件下复测。

## 2. 臂（3 臂，同 K002，不扩）

| 臂 | 表示文件 | 代码 | 执行 |
|---|---|---|---|
| F | `model_doc.md`（自由文本，九部分） | `run_model.py`（ABI） | 必选 |
| S | `model_ir.json`（MODEL_IR 18 字段契约） | `run_model.py`（ABI） | 必选 |
| SV | `model_ir.json` + `validation_plan.json`（强制字段） | `run_model.py`（ABI） | 必选 |

- 固定 ABI：`def solve(inputs: dict) -> dict`（input.json → run_model.py →
  output.json → ExecutionResult），由 P1 harness 执行（subprocess，status 只来
  自 returncode；产出 code_hash / environment_hash / duration_ms / outputs）。
- **三臂执行地位完全平等**：F 臂代码同样真实执行、同样进盲评包。
  消除 K002 的格式不对称。

## 3. 每 run 管线（外部 Agent + Harness 分工）

```
题目（8 题冻结题面，sha256 绑定）
  ↓ 外部 Agent（Model Constructor，可插拔：Doubao/GPT/人）
表示文件（F/S/SV 各自格式）+ run_model.py
  ↓ Harness（LLM-free）
run_code_pipeline（真实 subprocess 执行）
  → ExecutionResult（真实数值/状态/哈希）
  → 数值验证（VR：constraint_violation / 可行性 / 残差，机械判定）
  ↓
盲评包 = 题目 + 表示文件 + 代码 + ExecutionResult + VR（匿名化，无臂标记）
  ↓ 3 独立 Evaluator（Anchored Protocol，GENERATOR≠EVALUATOR）
rubric v1.2 评分（L1=9/L2=15/L3=9/L4=9）
  ↓
配对分析（block 级配对差 + bootstrap CI）
```

**外部 Agent 只负责"构造模型 + 写代码"；执行、数值验证、评分判定全部由
harness 机械完成**（LLM-free 铁律不变，The Agent Is Not The State）。

## 4. 终点

- **MCQ_primary** = (L2+L3+L4)/(15+9+9) × 100（与 K001/K002 同口径可比）
- **VAL_primary** = L4/9 × 100
- 执行级终点（观测）：execution_success_rate / model_fidelity /
  constraint_violation_max / correction_count
- **L3 判据 v1.2（关键修订）**：L3 各维度评分对象 = 盲评包中的真实
  ExecutionResult / VR 数值，**禁止以"声明执行/声称验证"作为评分依据**；
  无执行产物 → 该维度 0 分（与 K002 的"设计完备性"口径切换为"执行事实"口径）。

## 5. 规模与功效

- 主检验：6 题（2020_B/2018_A/2019_C/2018_B/2017_B/2011_B）× 3 臂 × 3 rep = **54 runs**
- 泛化：2 题（2022_C/2024_A）× 3 臂 × 2 rep = **12 runs**
- 合计 **66 runs**（每 run 含真实执行，成本高于 K002，rep 由 5 降为 3）
- **功效预计算（`k003_power.py`，K002 per-block sd=4.62 实测，Monte Carlo 200k）**：

  | 效应量 Δ(S−F) | power（配对 t 双侧 α=0.05, df=5, rep=3） |
  |---|---|
  | 2.14（K001 观测量级） | 0.273 |
  | 3.0 | 0.571 |
  | 3.3 | 0.676 |
  | 3.9 | 0.845 |
  | 4.5 | 0.940 |

  **power≥0.8 需 Δ≥3.7**。如实声明：rep=3 为成本—功效权衡（每 run 含真实
  执行），功效边界已知；**区分度预检（18 runs）后若观测效应方向/幅度不支持
  （Δ<3 且 CI 含 0），如实报告低功效观察，不做事后提 rep**（预注册纪律）。
- 题目区分度预检：6 题各 1 rep × 3 臂 = 18 runs（正式实验前，外部 Agent 生成）
- 决策门：同 K001/K002——block 级配对差 95% CI 下界 > 0 → positive

## 6. 五 Gate（预注册前置，全部 PASS 才 PREREGISTERED）

| Gate | 内容 | 状态 |
|---|---|---|
| G1 | 22 评分维度 ↔ 产物字段映射表（v1.2：L3 维度映射到 execution_result/VR 字段） | ✅ PASS |
| G2 | 3 evaluator 校准 κ（Anchored Protocol v1.2a，校准集 8 份含真实执行产物） | ✅ PASS（mean κ=0.712，13/22 达标，残余全归因，2026-09-09） |
| G3 | 词表（复用 K002 frozen `model_families.yaml` + 别名回归测试 25 用例） | ✅ PASS |
| G4 | 执行有效性 dry-run（run_code_pipeline 在 6 题上真实跑通，execution_success_rate=1.00，5 场景 fidelity 校验） | ✅ PASS |
| G5 | 功效（Monte Carlo 200k，K002 per-block sd=4.62，Δ≥3.7→power≥0.8） | ✅ PASS |

## 7. 与 P1 的关系

K003 的生成产物直接进 P1 的 `run_code_pipeline`（真实执行）——K003 测的
就是 P1 改造后的能力（infra 改变可测量行为的实证）。若 K003 RQ1 仍 negative，
则结论升级为"结构化表示在可执行条件下亦无构造质量增益"（更强的 negative）；
若 positive，则 K002 的 negative 可归因于"纯表示无执行"的设计缺陷（K002 已
如实记录，不推翻）。

## 8. 冻结与发布

- 冻结：协议 + 模板 F/S/SV + 词表 + 8 题题面（复用 K002 verified）+ rubric v1.2
- 状态机：DESIGN → REVIEW → PREREGISTERED → FROZEN → PREFLIGHT → RUNNING →
  VALIDATION → ANALYSIS → CLOSED（复用 k002_state.py 模式）
- 发布：正式报告 `P15-K003-REPORT.md`（含与 K001/K002 三实验对比表）

## 9. 风险与测量边界

- **成本**：66 runs 每 run 含代码生成 + 真实执行，是 K002 的 1.6 倍工作量；
  rep=3 功效依赖块内 sd（K002 实测 per-block sd=4.62，块内均值 sd=2.07@5rep，
  @3rep 略高——G5 如实计算）。
- **代码质量混淆**：F 臂代码质量可能低于 S 臂（表示结构化有助于写代码）——
  这是"表示 → 执行能力"的真实机制，不视为混淆，反而增强 RQ1 检验力。
- **执行环境**：Python 3.12、无 scipy（与 K002 同）；题面数据由 run_model.py
  自带（self-contained，禁外部网络）。
