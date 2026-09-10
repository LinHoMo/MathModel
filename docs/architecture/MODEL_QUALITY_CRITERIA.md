# MODEL_QUALITY_CRITERIA — 模型质量判据（正式版）

> Version: v1.0 ｜ Status: **FROZEN**（2026-09-11，取代 v0.1-draft）
> 目的：给「模型好不好、是否更准更有效」立一套**独立于 harness 自身打分**的判据，
> 使"能力"命题可被证伪。本文是判据真源；实现状态逐条标注。
> 落地顺序（用户裁定）：**标准层 → 能力层 → 产物层**（先后关系，非并行）。

---

## 0. 为什么需要这份文档

当前"能力提升"的主张缺独立标尺，四处证据指向同一断层：

| 证据 | 事实 | 暴露的问题 |
|---|---|---|
| K001 | 知识注入 Δ=+2.14，置信区间触 0，p=1.0 | 负结果，但能力命题未被判死 |
| K002 | 纯表示 S−F(MCQ)=−4.85，显著负 | 结构化表示不产生建模价值 |
| K003 | S+3.76 全来自 L4；L2 构造层为负 | 正效应来源受限，且 L4 被判循环论证 |
| 盲评 κ | K002 κ=0.4345 / K003 κ=0.260，均 <0.6 | 测量工具本身不可靠 |
| STRATEGIC_VERDICT §4-Round2 攻击 5 | "要求产出 validation_plan → rubric 评其存在 → 得分高" | 自我打分循环 |

**结论**：没有独立判据时，"模型更好"无法与"自己给自己打分"区分。本文即为此立靶。

---

## 1. 判据本身必须满足的四条原则

1. **独立性**：判据输入不得含 harness 自身评分或 LLM 盲评结论（否则循环）。
2. **可证伪**：每条判据配反例——什么样的结果会推翻"模型 X 更好"。
3. **机械优先**：能程序判定的不用人评。
4. **可复现**：给定（模型定义 + 数据 + 种子），判定确定且可重算。

违反任一条的判据不得进入"能力"结论，只能进"观察"。

---

## 2. 两层结构

### 2.1 合格线 Gate（阻塞式，随 `validate.py` 自动执行）

只收**当前语料上确定可判**的判据。

| 编号 | 判据 | 机械定义 | 实现状态 |
|---|---|---|---|
| **G1** | 数值溯源 | 文档（`*.md`）中的数值须能追溯到 `all_results.json` ∪ `inputs/problem.txt`（相对容差 0.5%、绝对 0.01） | ✅ 已实现 |
| **G2** | 参数来源 | 每个参数须有 `source` 且 ∈ 批准词表；`source=="problem_given"` 的**数值**参数，其值须在 `inputs/problem.txt` 可匹配（仅允许 ×10^k 单位换算，k∈[-9,9]） | ✅ 已实现 |
| **G3** | 校准参数门禁 | 见 §2.1.1 | ⏳ 待实现 |

#### 2.1.1 G3 定义（校准参数门禁）

对每个活跃实例 `model_ir.json` 的每个参数 `p`：

- 若 `p.source ∈ {problem_given, derived, convention}` → **豁免**（题面给定 / 由其它量推导 / 仓库约定）。
- 否则（如 `assumption_derived` / `reasoning` / `calibration` / `estimated` —— 即**建模者自选、结论敏感**的量）→ 必须同时满足：

  **(a) 显式锚定**：`p` 含字段 `calibration_anchor_ref`，其值为某个 `assumption_id`；该假设在同文件 `assumptions` 中 `type == "calibration_anchor"`。缺失或不匹配 → **FAIL**。

  **(b) 敏感性证据**：`all_results.json` 顶层含 `calibration_sensitivity` 对象，且 `calibration_sensitivity[p.parameter_id]` 存在并满足：

  ```
  { "symbol": str, "nominal": number,
    "varied": { "<自变量名>": [v1, v2, ...] },   # 长度 ≥ 2
    "outcomes": [o1, o2, ...] }                   # 与 varied 各轴等长
  ```

  `varied` 任一轴长度 <2 或缺字段 → **FAIL**。

**反例（证伪条件）**：若某参数的取值在题面已给定（尽管被标为 `assumption_derived`），G3 的 (a)(b) 即为多余负担 → 应改标 `problem_given`，而非放宽 G3。

### 2.2 排序线 Rank（非阻塞，冻结口径）

E1/E2 需要**参考解 / 留出数据**，当前语料不具备（2026 题无真值卡）。做法：**冻结口径，运行时一律输出 `不可算`，不阻塞交付**。真值到位后再启用为 Gate。

| 编号 | 判据 | 冻结口径（输入 → 计算 → 阈值） | 状态 |
|---|---|---|---|
| **R1** | 样本外预测 | 输入：留出集（题面外的数据点）；计算：留出集上的相对误差；阈值：优于平凡基线（均值/线性外推） | 口径已冻结，数据缺失 → 不可算 |
| **R2** | 基线 delta | 输入：最简可用 baseline（常物性 / 无移动边界 / 均匀假设）的对照运行；计算：Δ = 主模型指标 − baseline 指标；阈值：bootstrap 置信区间不含 0（沿用 K001 判法） | 口径已冻结，需对照运行 → 不可算 |

---

## 3. 判据自身的证伪条件

本判据集若出现下列任一情况，须重新设计：

- **无增量**：三实例按 G1–G3 排序与盲评排序**完全一致** → 未提供盲评之外的信息。
- **不可判**：多数实例在某条上恒返"不可算" → 该条在真实语料上不可用。
- **可 game**：存在"只提升 G 分数而不改善 R1/R2"的平凡构造 → 判据被规避。

---

## 4. 与现有机制的关系

| 现有机制 | 覆盖 | 本文处置 |
|---|---|---|
| L2 Fidelity | MODEL_IR ↔ 代码语义 | 保留，不重复 |
| L3 数值判定 | 约束/目标/域有限非负 | 保留 |
| L4 盲评 | 主观质量 | **降级为辅助**；主判据交 G1–G3 |
| `check_numeric_traceability` | 数值溯源 | 即 **G1** |
| `check_parameter_provenance` | 参数来源 | 即 **G2** |
| Evidence Gate E1–E9 | 证据完备性 | 保留，不重复 |

**κ 处置**：κ < 0.6 的盲评维度不得作为主判据输入；若保留须注明"仅方向性参考"。

---

## 5. 决策记录（本轮）

| 决策 | 取舍 | 理由 |
|---|---|---|
| 走方案 C（判据分两层），非 A（全门禁）、非 B（先建题库） | 能判的立即成禁，不能判的如实标"不可算" | A 在无真值语料上必假绿或误伤；B 短期交付不了 |
| G3 取**严格版**（要求敏感性证据），非仅要求披露 | 用户裁定 ② | 敏感性是"该参数是否可信"的实质证据，仅披露不足以约束 |
| E1/E2 暂入 Rank（非阻塞） | 不阻塞交付 | 当前无参考解/留出数据，硬门禁会空转 |
| 落地顺序：标准层 → 能力层 → 产物层 | 用户裁定 | 先有独立靶子，能力提升才可判 |

**G3 上线的即时影响（已勘察）**：三实例中仅 `cumcm2026a` 触发——`P08`（恒温目标 50 °C）与 `P12`（烘房温度时间常数 450 s）均为 `source=assumption_derived` 且无 `calibration_sensitivity` 记录，需补。`cumcm2026b`（全 `problem_given`/`derived`/`convention`）与 `cumcm2024a` 不触发。

---

## 6. 非目标（YAGNI）

不做横向排名（无真值）；不改 `src/modeling_harness/runtime/` 业务逻辑；不新增第三方依赖；不重复 L2/L3/Evidence Gate 已覆盖的检查。

---

## 附：本文引用的证据位置

| 论断 | 来源 |
|---|---|
| K001/K002/K003 数值与结论 | `docs/architecture/STRATEGIC_VERDICT.md` §3 |
| L2 构造层为负、L4 循环论证 | `docs/architecture/STRATEGIC_VERDICT.md` §4 Round 2 |
| L3 仅结构检查、κ 不达标 | `docs/architecture/MODEL_CONSTRUCTION_GAP.md` §2.3/§2.4 |
| G1 实现 | `src/modeling_harness/cli/validate.py::check_numeric_traceability` |
| G2 实现 | `src/modeling_harness/cli/validate.py::check_parameter_provenance` |
| G3 即时影响勘察 | 三实例 `model_ir.json` 的 `parameters[*].source` |
