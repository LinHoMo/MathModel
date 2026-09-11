# MODEL_QUALITY_CRITERIA — 模型质量判据（正式版）

> Version: v1.2 ｜ Status: **FROZEN**（2026-09-11；v1.2 修订：G4 支持 evidence_refs 对象形态、
> G5 升级为 used_in 显式引用契约 + 双级门禁（硬 FAIL / 启发式 WARN）、新增门禁金标准度量；
> v1.1：新增 G4 证据义务矩阵、G5 复杂度预算、R3 结构距离、R4 创新声明；G3 标记已实现）
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
| **G3** | 校准参数门禁 | 见 §2.1.1 | ✅ 已实现 |
| **G4** | 证据义务矩阵 | 见 §2.1.2 | ✅ 已实现 |
| **G5** | 复杂度预算 | 见 §2.1.3 | ✅ 已实现 |

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

#### 2.1.2 G4 定义（证据义务矩阵 / Evidential Lattice）

对每个活跃实例 `model_ir.json` 顶层可选 `evidence_obligations = {子问题: [证据层, ...]}`：

- 证据层词表（前缀 **EV** 规避既有 Evidence Gate E1–E9 编号冲突）：

  | 层 | 含义 | 机械证据信号（任一命中即支撑） |
  |---|---|---|
  | **EV1** | 数学必然 | `validations[].type` ∈ {invariant, conservation, well_posedness, dimension, optimality_check, exactness, balance}，或任一方程 `derivation_trace` 含 {守恒,不变,平衡,唯一,充要,一致} |
  | **EV2** | 机制保真 | 任一机制含非空 `governing_principle` 且 `related_equations` 非空 |
  | **EV3** | 数据拟合 | 拟合类验证 / `all_results` 含拟合指标键（rmse/mae/r²/误差等）/ claims 含 {数据驱动,拟合,插值,回归} |
  | **EV4** | 样本外预测 | 样本外/反事实验证（counterfactual/holdout/out_of_sample/…）/ claims 含 {实测,附件,样本外,留出} |
  | **EV5** | 决策效用 | sensitivity/robustness 验证 / `all_results` 含 `calibration_sensitivity` 等键 |

- 声明某一层而实例无对应证据 → **FAIL**（防「声称质量层级却无证据」）。
- 未声明 obligations → 不判失败（opt-in 契约，接口先行）。
- v1 粒度：**实例级证据检查**（不细分到子问题）；子问题粒度留待证据图深化。
- **v1.2 两种义务形态**：①字符串形态 `"EV1"` —— 由上表启发式信号支撑（向后兼容）；
  ②对象形态 `{"layer":"EV5","evidence_refs":["V01","CL02"]}` —— refs 必须解析到
  model_ir 真实 id（validation/claim/equation/mechanism/objective/constraint），
  refs 为空或不可解析 → **FAIL**（显式引用优先于凑词，是反例的根治手段）。

**反例（证伪条件）**：若某实例声明的义务层全部被「凑词」满足（如 claims 里塞"实测"字样而并无实测对照），说明信号词表可被 game → 应升级为显式引用（obligation → validation/claim 的 `evidence_refs` 存在性），而非扩充词表。

#### 2.1.3 G5 定义（复杂度预算 / Parsimony Budget，v1.2 双级）

对每个活跃实例 `model_ir.json` 的每个参数 `p`，存在两条证据路径：

- **显式路径（硬契约）**：`p.used_in = [{type, ref}, ...]`，type ∈
  {equation, mechanism, objective, constraint, validation, claim, code}；
  非 code 的 ref 必须解析到 model_ir 对应 id；code 的 ref 相对项目根（可带 `#Lxx`），
  文件须真实存在且不得 `../` 越界。声明了 used_in 却无任一可解析引用 → **硬 FAIL**
  （声明不诚实）。
- **启发式路径（咨询层）**：未声明 used_in 时回退字符串匹配——信号 = `parameter_id` /
  `symbol`（希腊转写、上下标剥离、分隔符/大小写归一）/ `name` / `value`
  （int↔float 互化、分隔串拆分）；语料 = model_ir（剔除 parameters 自证）+
  `all_results.json` + `artifacts/code/*.py` + 项目根 `*.md`。
- **双级判定（Two-tier Gate）**：显式契约破损 = 硬 FAIL（`check_parsimony_budget`）；
  启发式全未命中只计 suspect，由独立门禁 `check_dead_param_scan` 以 **WARN** 级报告、
  不阻塞——启发式不可靠（曾误判 2026b P13/P14），不得单独决定硬失败。
- 复杂度指标（param/explicit/suspect/eq/mech）随门禁消息报告，为 Rank 数据，不阻塞。

**当前基线（已实测）**：三实例 46 个参数全部显式声明 used_in（explicit=17/12/17，
suspect=0），死参数扫描「扫描 0 个未声明参数」；金标准
`tests/fixtures/param_usage_gold.json` 度量启发式 FP=FN=0。

**反例（证伪条件）**：若 used_in 声明被人工发现指向无关组件（声明与数学不符），
说明生成过程不可信 → 该参数引用必须回到方程 latex/代码逐个人工核对，并在金标准中标注。

#### 2.1.4 G4/G5 的已知局限（诚实披露）

- 启发式（G4 词表、G5 字符串匹配）会漏（凑词通过）也会误（表示变体漏配）：
  v1.2 已把启发式降级为 WARN 咨询层，硬失败只由可证伪的显式契约承担。
- 已用「真实踩坑」加固：2026b P13/P14 字符串值 + 浮点格式漏配 → 值信号/归一化修复 +
  对抗回归测试（test_parsimony_budget.py）+ 失败卡 fm-gate-heuristic-false-positive。
- 门禁质量由金标准持续度量（test_gate_gold_standard.py，FP/FN 须为 0）；
  遗留：子问题粒度义务（§9.4）、本体图连续化（§9.3）、符号映射表（§9.6）
  见 THEORY_FOUNDATION_REVIEW.md §9。

### 2.2 排序线 Rank（非阻塞，冻结口径）

E1/E2 需要**参考解 / 留出数据**，当前语料不具备（2026 题无真值卡）。做法：**冻结口径，运行时一律输出 `不可算`，不阻塞交付**。真值到位后再启用为 Gate。

| 编号 | 判据 | 冻结口径（输入 → 计算 → 阈值） | 状态 |
|---|---|---|---|
| **R1** | 样本外预测 | 输入：留出集（题面外的数据点）；计算：留出集上的相对误差；阈值：优于平凡基线（均值/线性外推） | 口径已冻结，数据缺失 → 不可算 |
| **R2** | 基线 delta | 输入：最简可用 baseline（常物性 / 无移动边界 / 均匀假设）的对照运行；计算：Δ = 主模型指标 − baseline 指标；阈值：bootstrap 置信区间不含 0（沿用 K001 判法） | 口径已冻结，需对照运行 → 不可算 |
| **R3** | 结构距离 | 输入：模型结构声明 + 题面 `allowed_modeling_structures`；计算：声明值优先，未声明用一阶二值（family ∈ allowed → 0 否则 1）；阈值：无（排序参考） | ✅ 工具已实现（`cli/innovation_metrics.py`），v1 二值待本体图深化 |
| **R4** | 创新声明 | 输入：`innovation.dimensions` + `difference_arguments`；计算：契约核验（维度词表 / 值域 / 非零维度须附差异论证）；阈值：无（创新进 Rank 不进 Gate，但契约是 Gate） | ✅ 契约门禁已实现（validate.py `check_innovation_declaration`） |

---

## 3. 判据自身的证伪条件

本判据集若出现下列任一情况，须重新设计：

- **无增量**：三实例按 G1–G5 排序与盲评排序**完全一致** → 未提供盲评之外的信息。
- **不可判**：多数实例在某条上恒返"不可算" → 该条在真实语料上不可用。
- **可 game**：存在"只提升 G 分数而不改善 R1/R2"的平凡构造 → 判据被规避。
- **信号词表可 game**：G4 字符串形态被凑词满足、G5 启发式被无关数值误判 → 已有对象形态 evidence_refs / used_in 显式契约作为根治出口；金标准 FP/FN > 0 即触发规则复审。

---

## 4. 与现有机制的关系

| 现有机制 | 覆盖 | 本文处置 |
|---|---|---|
| L2 Fidelity | MODEL_IR ↔ 代码语义 | 保留，不重复 |
| L3 数值判定 | 约束/目标/域有限非负 | 保留 |
| L4 盲评 | 主观质量 | **降级为辅助**；主判据交 G1–G3 |
| `check_numeric_traceability` | 数值溯源 | 即 **G1** |
| `check_parameter_provenance` | 参数来源 | 即 **G2** |
| `check_calibration_parameters` | 校准参数 | 即 **G3** |
| `check_evidence_obligations` | 证据义务矩阵 | 即 **G4** |
| `check_parsimony_budget` | 复杂度预算（硬：显式契约） | 即 **G5** 硬层 |
| `check_dead_param_scan` | 死参数启发式扫描（WARN 级） | 即 **G5** 软层（双级门禁） |
| `check_innovation_declaration` / `cli/innovation_metrics.py` | 创新声明契约 / 结构距离 | 即 **R4** / **R3** |
| Evidence Gate E1–E9 | 证据完备性 | 保留，不重复（与 G4 的 EV1–EV5 证据层是不同编号体系） |

**κ 处置**：κ < 0.6 的盲评维度不得作为主判据输入；若保留须注明"仅方向性参考"。

---

## 5. 决策记录（本轮）

| 决策 | 取舍 | 理由 |
|---|---|---|
| 走方案 C（判据分两层），非 A（全门禁）、非 B（先建题库） | 能判的立即成禁，不能判的如实标"不可算" | A 在无真值语料上必假绿或误伤；B 短期交付不了 |
| G3 取**严格版**（要求敏感性证据），非仅要求披露 | 用户裁定 ② | 敏感性是"该参数是否可信"的实质证据，仅披露不足以约束 |
| E1/E2 暂入 Rank（非阻塞） | 不阻塞交付 | 当前无参考解/留出数据，硬门禁会空转 |
| 落地顺序：标准层 → 能力层 → 产物层 | 用户裁定 | 先有独立靶子，能力提升才可判 |
| 新增 G4/G5/R3/R4（v1.1） | 标准层第一步落地 | 补「正向质量证据 + 复杂度治理 + 创新接口」，全为 opt-in 契约 + 机械核验 |
| G4 证据层用 EV 前缀 | 规避既有 Evidence Gate E1–E9 编号 | 术语唯一（ONTOLOGY 原则） |
| G5 值/符号匹配从宽（宁可漏报死参数，不误伤被引用参数） | 真实踩坑（2026b P13/P14 误报）后裁定 | 启发式有边界；根治走显式引用契约 |
| **v1.2：used_in 显式引用契约落地（§9.1）** | 参数→使用位置显式化，硬核验可解析 | 隐式关系靠猜是误报根因；显式契约可证伪 |
| **v1.2：双级门禁，启发式降 WARN（§9.2）** | 硬 FAIL 只给显式契约；启发式未命中 WARN | 不可靠信号不得单独决定硬失败 |
| **v1.2：门禁金标准度量（§9.5）** | 46 参数真值固化，FP/FN 锁 0 基线 | 新门禁先在真实语料度量再启用 |
| **v1.2：G4 对象形态 evidence_refs** | 显式引用优先于启发式凑词 | 给「凑词 game」留根治出口 |

**v1.1 上线的即时影响（已实测）**：三实例均声明 `evidence_obligations` 与 `innovation`；G4/G5/R4 全部 PASS（used=17/17、12/12、17/17）；反向验收（注入非法层 / 移除创新论证）门禁正确 FAIL 并点名；R3 工具输出三实例 d_structure=0.00（2026a 含 composition_novelty=0.3）。

**v1.2 上线的即时影响（已实测）**：三实例 46 参数全部机器生成并人工抽审 used_in
（每参数 2–12 个真实引用，zero-hit=[]）；validate 52 通过/0 失败/0 警告
（复杂度预算 explicit=46/46、死参数扫描扫描 0 个未声明参数）；新增单测 17 个
（test_explicit_refs.py 13、test_gate_gold_standard.py 4），全量 700 passed；
金标准度量启发式 FP=FN=0。

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
| G4 实现 | `src/modeling_harness/cli/validate.py::check_evidence_obligations` |
| G5 实现（硬层） | `src/modeling_harness/cli/validate.py::check_parsimony_budget` |
| G5 软层 / used_in 解析 | `validate.py::check_dead_param_scan` / `_resolve_used_in` |
| 门禁金标准 | `tests/fixtures/param_usage_gold.json` + `tests/unit/test_gate_gold_standard.py` |
| used_in 生成器（机器扫描，非编造） | `scripts/_gen_used_in.py` / `scripts/_gen_gold.py` |
| R3 实现 | `src/modeling_harness/cli/innovation_metrics.py` |
| R4 实现 | `src/modeling_harness/cli/validate.py::check_innovation_declaration` |
| v1.1 局限与根治方向 | `docs/THEORY_FOUNDATION_REVIEW.md` §9 |
