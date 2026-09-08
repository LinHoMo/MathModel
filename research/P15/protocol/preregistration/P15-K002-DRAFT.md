# P15-K002 — Model Representation Efficacy
## 预注册（Preregistration）DRAFT v0.5（P0-E 完成 + 核心问题升级）

> **状态：`DRAFT`（v0.4 已锁 Measurement Gate；v0.5 随 P0-E 落地把核心问题升级为
> "从模型构造到可执行模型"的过程，新增 Fidelity 等执行级终点）**
> **科学定位**：K001（Knowledge 文本注入）已得 negative result；本实验检验**下一个杠杆：强制的结构化 Model Representation（输出契约）本身是否提升外部 Agent 的 Model Construction Quality——且现在是"从模型构造到可执行模型"的过程质量**。
> **上游**：P15-K001 ✅（Δ_K=+2.14 CI[+0.00,+6.41] negative；Sham 11/11 正确拒绝；adapted 58%）｜ KNOWLEDGE_BASE_QUALITY_BASELINE（仅 3/19 卡为完整建模知识）｜ **三仓库审计**（CROSS_REPO_AUDIT.md：BZD/MMA 无因果证据；LHM 六风险确认）｜ **战略裁决**（THREE_LAYER_ARCHITECTURE.md v3：Model Lifecycle 核心；五级正确性 L0–L4；三状态分离铁律；Fidelity 指标）｜ **P0-E ✅**（commit ad917d2：ExecutionAdapter + execution_result 一等 artifact + executed_by 绑定；P0-E4 Replay ✅ 本轮）

> **冻结顺序（用户裁决，写死）**：
> `P0-E（✅）→ runtime validation → K002 dry-run → 题目区分度检查 → measurement check（五 Gate）→ PREREGISTERED → FROZEN`
> 否则 K002 测出来的可能不是 MODEL_IR 的效果，而是 runtime 的缺陷。

> **核心问题（v0.5 升级，替代 v0.4 的"JSON 比自由文本好吗"）**：
> **结构化 Model Artifact 是否改善"从模型构造到可执行模型"的过程？**
> 观察对象从"产物好看"移到"产物能否真实执行、执行的是否是声明的模型"。

> **主线（死守）**：`Representation → Execution → Evidence → Validation → Capability`

---

## 0. 一句话

> 把"输出自由文本模型描述"与"强制按 MODEL_IR 18 字段 schema 输出结构化模型"对比，
> 在完全相同的题/LLM/预算/盲评下，检验**结构化输出契约是否本身改善 Model Construction Quality**。
> 这直接回答：MathModel 的 Harness 定位（标准化表达/接口/证据）除"测量"外是否也**提升**外部 Agent 的建模。

---

## 1. 背景与科学动机

### 1.1 为什么是 Representation 而不是更多知识
- K001 证明：外显 Knowledge 文本注入无显著可检效应（CI 下界触 0）。且 Sham 错位卡 11/11 被正确拒绝、adapted 58%——机制正常，效应缺位。
- 知识质量扫描证明：注入的恰是库内最优 3 张 Tier1 卡——排除"卡质量差"解释。
- 归因指向**信息增益 ceiling**：知识卡显式化的内容（Bellman 原理、守恒律等）本就是 LLM 已内化的；文本注入是可忽略的"建议"。

### 1.2 Representation 为什么可能是真杠杆
- 与"知识=外部建议（LLM 可忽略）"不同，**输出契约=强制约束（不满足即注册失败/评分受限）**。
- 结构化输出强制外部 Agent 把隐式推理**显式化**：变量必须声明语义、约束必须引用变量、方程必须与变量一致、结果必须绑定实验——这些"形式一致性"恰是自由文本最易含糊跳过的层面（P15-K001 2 个 FAIL run 即 Q1-only 覆盖不全，非文本质量问题）。
- 认知脚手架假说：输出约束改变生成过程（structured generation 引导完整遍历 schema 字段），而非仅改变产物格式。

### 1.3 对项目定位的意义
- 若 S > F：证明"标准化表达本身提升质量"——Harness 不仅是测量底座，还通过结构化状态约束提升外部 Agent 能力；直接回应审计风险 "Infrastructure without capability gain"。
- 若 S ≈ F：与 K001 一致，指向"纯基础设施/契约无能力增益"——需要 Critic/Evidence 等更强杠杆，或承认 Harness 是纯测量层。
- 若 S < F：结构化约束**有害**（框架化抑制自由建模）→ 重新评估 Model IR 强制方向。

### 1.4 三仓库审计启示（CROSS_REPO_AUDIT.md，已回填）
- **BZD/MMA 无任何因果证据**：BZD 全仓零测试零 benchmark（"基于 16 道题蒸馏"是 DOC_CLAIM）；MMA 无 benchmark/ablation（README 后期计划才有）。→ **LHM 的预注册实验是唯一能给出"知识/表示因果效应"数据的系统**——K002 延续这一稀缺性。
- **execution weakness 是公共缺口**：MMA 有 Code Interpreter（最强执行参考）、BZD 显式外包、LHM experiment 节点产占位 result。→ K002 的 S/V 臂产物必须含**真实数值**（validation_plan 强制字段已有此设计）；result 占位符修复列为 P0 工程项（experiment 节点未执行应标 `not_executed`，不得用假占位 claim）。
- **ontology 分叉直接污染测量**（RQ5 教训：`discrete_recurrence` vs `dynamic_programming`）。→ K002 的 S 臂 `model_family` 字段使用**单一受控词表**（若 `catalog/model_families.yaml` 已建则引用之；未建则用预注册固定枚举并声明为 K002 的受控词表，同时把"词表收敛"列为 P0 工程项）。
- **"更多上下文"必须对齐**：K001 Sham>K 教训 → K002 指令长度对齐 <10%（§3.1 已设计）+ 信息密度统计（RQ6）。

### 1.5 战略裁决（2026-09-09，用户定稿，本版全部落实）

| 裁决 | 结论 | 本版落实 |
|---|---|---|
| 臂结构 | **不扩 6 臂**，维持三臂 F/S/S+V（K001 已测 Knowledge/Sham，边际信息低；3 臂每臂 n 更大、功效更高） | §3.1 不变 |
| block 数 | **坚持 block ≥ 6**：K001 最小 p=0.25（block=3）是功效失败根因；block=6 → 2^6=64 置换，最小 p≈0.016 | §3.3 主检验 3→6 题 |
| 题目性质 | **不能只是"多几道"**：须不同建模结构、不同难度、不同 failure mode | §3.6 题目选择标准（新增） |
| 终点 | **L3/L4 终点**：Model Construction Quality 是核心；**论文/写作质量退为 secondary，永不作为 capability 主终点**（避免 "better writing = better modeling" 陷阱） | §4.1 主终点改为 L2+L3+L4 composite |
| 词表 | ontology 与 string vocabulary 分离（Concept→Mechanism→Family→Model→Method→Solver→Implementation） | §4.4 族命中 multi-field（新增） |
| 顺序 | **STOP abstract infra → MAKE MODEL EXECUTE → REAL RESULT → REAL EVIDENCE → BLIND EVALUATE → REPRESENTATION IMPROVES CONSTRUCTION** | 本节为路线承诺 |

---

## 2. 研究问题与假设

| # | 问题 | 统计量 |
|---|---|---|
| **RQ1（主）** | 强制结构化 MODEL_IR 是否提升 MCQ（L2 composite）？ | `mean(S) − mean(F)` |
| **RQ2** | 强制 Validation Plan 字段是否提升 VAL（L4 composite）？ | `mean(S+V) − mean(S)` |
| **RQ3** | 结构化是否提升**子问题覆盖度**（K001 最强区分维度）？ | 每 run sub-question coverage（Q1–Qn） |
| **RQ4** | 结构化/验证强制是否改变 failure mode 分布？ | FM 命中对比（重点 FM-MC-003、FM-VA-001/002） |
| **RQ5** | 效应是否跨题型泛化？ | 主检验 3 题 + 泛化 2 题分层报告 |
| **RQ6** | 结构化是否改变 token 成本/产物信息密度？ | tokens、产物长度、信息密度 |

### 预注册假设（双侧，不做方向性承诺；点估计方向报告）
- **H1（主）**：Representation 主效应 ≠ 0（S−F）。
- **H2**：Validation 强制效应 ≠ 0（S+V − S）。
- **H3**：子问题覆盖度差异 ≠ 0。
- **H4**：FM 分布差异 ≠ 0。

### 预先声明的结论形态
| 结果形态 | 解释 | 后续动作 |
|---|---|---|
| `S > F` 且 CI 下界 > 0 | 纯结构化提升 L2（低概率，L2 已饱和） | 确立 Model IR 强制价值 |
| `S+V > S` 且 CI 下界 > 0 | **验证行为字段化提升 L4**（主预期） | Validation Plan 纳入 MODEL_IR 契约；下一轮测 Critic 叠加 |
| `S ≈ F` 且 `S+V ≈ S` | Representation 与验证强制均无效应 | 强化"纯契约无增益"风险；转向 Critic/Evidence 或接受 Harness=纯测量 |
| `S+V ≈ S ≈ F` 但 L4 全体低分 | 字段化不改变行为（Agent 仍不执行验证） | 需更强执行机制（L4 结果 gate：无极限检验即 FAIL） |
| `S+V < S` | 强制字段有害（负担 > 收益） | 改引导式验证要求 |

---

## 3. 实验设计

### 3.0 子维度分布证据（决定三臂结构）
P15-K001 盲评 55 份的 22 维分布（`research/P15/analysis/dimension_distribution.json`）：
- **L2 结构维度已饱和**：L2.1（变量）/L2.2（参数）/L2.3（假设）≈ 满分（avg 1.98–2.00/2），L2.7 1.96/2——K001 的 18 字段 MODEL_IR 强制下 Agent 结构产物已接近天花板。
- **弱环全部在"非强制字段"**：L4.3 极限/边界检验 avg 0.84（**唯一有 0 分**，9/55）、L3.4 可复现性 avg 1.04（**无一 2 分**）、L1.4 歧义标注 avg 1.00（全 1 分）、L3.5 结果合理性 1.00。
- **结论**：结构化契约的效应局限在被结构化的字段；**验证行为（极限检验/多 seed/歧义处理）未被强制，所以 Agent 普遍不做**。K002 因此增加第三臂：把验证行为也字段化。

### 3.1 条件（3 臂）

| 臂 | Representation | 强制字段 | 输出要求 | 角色 |
|---|---|---|---|---|
| **F** | free-form | 无 | prompt 要求完整描述假设/变量/参数/目标/约束/方程/求解/验证，自由格式文本 | 基线 |
| **S** | structured | MODEL_IR 18 字段（K001 同款） | 按 MODEL_IR schema 输出 JSON；`k002_register.py` 机械校验 | 纯 Representation |
| **S+V** | structured + validation fields | MODEL_IR 18 字段 + **Validation Plan 字段**（极限/边界检验、多 seed 可复现、敏感性扰动、歧义处理方案、主张-证据对应） | 同上 + Validation Plan 强制字段校验 | Representation + Validation 强制 |

**指令长度对齐**：F 臂追加与 S 臂 schema 说明等长的引导句；S 与 S+V 的差异仅在 Validation Plan 字段说明——三臂 prompt 长度差 <10%，排除"更多上下文"替代解释（K001 Sham 教训）。

**对照组说明**：K002 无 Sham 臂——无知识注入；"更多上下文/处理资源"由指令长度对齐 + 信息密度统计控制。

### 3.2 实验单位与区组
```
Problem    = block（区组）
Arm        = treatment（F/S/S+V）
Replication = stochastic repeat（seed 42/43/44/45/46，5 rep）
```
统计比较同题配对差（臂内 5 rep 均值差 + 配对 CI），block 吸收题目难度。

### 3.3 规模（block≥6 裁决版）
| 用途 | 题 | 臂 | 重复 | runs |
|---|---|---|---|---|
| 主检验 | **6 题**（2020_B、2018_A、2019_C + **3 新增**，见 §3.6） | 3 | 5 | **90** |
| 泛化观察 | 2022_C、2024_A | 3 | 3 | 18 |
| **合计** | | | | **108** |

- **block=6 → 2^6=64 种配对排列，最小 p≈0.016**（K001 block=3 最小 p=0.25 的 15 倍功效余量）。
- 3 道新增题的 **Input Authenticity 是 PREREGISTERED 前置**：每道必须走题面来源→官方存档交叉验证→SHA256 冻结→manifest 登记（0 BLOCKED 才允许冻结；找不到可信来源则标记 BLOCKED，不伪造题面）。若新增题在预注册期不可得，退回 §3.6 的备选路径并如实声明功效降级。
- （与 K001 同题集同构的 3 题保证跨实验可比；F/S 臂可与 K001 的 A/B 臂交叉参照。）

### 3.4 强制子问题覆盖 gate（K001 教训落点）
- 每 run 的 `problem_binding.sub_question_id` 必须覆盖该题全部子问题（2020_B→Q1-Q3 等），缺任一子问题 → 该 run 标记 `COVERAGE_FAIL`，**不进入主终点**（单独报告，与 K001 的 2 个 FAIL 同口径）。
- 同时记录 coverage 作为 RQ2 的连续指标。

### 3.5 题目区分度预检（K001 per-block 教训落点）
K001 按题分解发现 2019_C 全臂恒定同分（零区分度），实际有效 block 只有 2/3。K002 预注册：
- 主检验题集（6 题）先各跑 1 个预检 rep（2 臂 × 6 题 = 12 runs），计算每题 F/S 各条件内方差与条件间差。
- **预检规则（预先声明）**：某题若 F/S 两臂全部 run 得分相同（条件内方差 = 0 且条件间差 = 0），标记为**无区分度 block**，从主效应估计中剔除并单列报告；剩余题正常进入主检验。
- 预检 run 计入最终分析（不浪费），仅标注来源。
- 若主检验题中 ≥2 题无区分度：判定题集区分力不足，STOP 并回到题目选择（不继续跑满）。

### 3.6 题目选择标准（"多几道"不够——须结构/难度/failure-mode 多样化）
3 道新增题 + 既有 3 道主检验题，必须在以下三维度上分散（预注册时逐题登记，缺任一维度即换题）：

| 维度 | 要求 | 对应既有题 |
|---|---|---|
| **建模结构**（L1 taxonomy） | 6 题覆盖 ≥4 种 Problem Structure（motion/geometry、diffusion、queue/service、decision/evaluation、network、game、data 等） | 2020_B=discrete sequential；2018_A=diffusion/PDE；2019_C=queue（区分度存疑，预检把关） |
| **难度梯度** | 至少含 1 道"易错在分解"、1 道"易错在求解"、1 道"易错在验证"的题（按 K001 FM 分布预判） | 待新增题补足 |
| **failure mode 多样性** | 3 道新增题不应与既有题共享同一主导 FM（避免 2019_C 全臂同分重现） | 待新增题补足 |

- 新增题候选必须满足：官方/高校存档来源可得（Input Authenticity 流程）、存在权威 gold/评分标准或可构造验证期望、不在 K001 五题集内。
- **备选路径（预先声明）**：若某维度无法凑足（如 3 道新增题 authenticity 不可得），退回"5 题就绪集 + 已有主检验 3 题"，同时如实声明 block 退回 3、功效回到 K001 同级——**不降级题目真实性换数量**。

---

## 4. 测量

### 4.1 主终点（L3/L4 终点裁决版 + v0.5 执行级终点）
- **MCQ_primary（主）** = **L2 + L3 + L4 composite**（MODEL_CONSTRUCTION_RUBRIC v1.0，标准化到 /100）：
  - L2 结构完备（L2.1/2.2/2.4/2.5/2.6(权重3)/2.7）——与 K001 **完全一致**，保证跨实验可比；
  - L3 求解层（L3.1–L3.5：可执行性/稳定性/可复现性/合理性）——锚 L3.4（K001 无一 2 分弱环）；
  - L4 验证层（L4.1–L4.5：基线/敏感性/极限检验/不确定性/主张证据）——锚 L4.3（K001 唯一 0 分弱环）。
  - **论文/写作质量不是本实验终点**（治理声明：writing 永不作为 capability 主终点；"better writing ≠ better modeling"）。
- **VAL_primary（次主）** = L4 composite（/10×100）单列——检验"验证行为字段化"是否提升（S+V vs S）。
- **执行级终点（v0.5 新增，P0-E 使能）**——回答"从模型构造到可执行模型"的过程质量：
  - `execution_success_rate`：可执行产物中真实执行 status=success 的比例（**execution_result 一等 artifact 的 status，非 LLM 声称**）；
  - `invalid_model_rate`：执行失败/无效（failed/timeout/invalid）比例，按失败原因归因；
  - `correction_count`：从首版到成功执行的迭代修正次数（可追踪版本序列）；
  - `model_fidelity`（**Model-to-Execution Fidelity，L2 核心指标**）：执行代码与 MODEL_IR 声明的一致性（objective/constraints/variables/equations 语义映射）——代码执行成功 ≠ 跑的是声明的模型；K002 首次测量；
  - `evidence_completeness`：ExecutionResult → Evidence → Validation 链各环节是否齐备；
  - `final_mathematical_correctness`：盲评终审的数学正确性（L3/L4 语义判定）。
  - 执行级终点从 **K002 dry-run** 起预检（Measurement Gate G4 要求），FROZEN 时连同 rubric 冻结。
- 分层报告：L2（K001 可比）、L3、L4、L1（问题理解）各自独立报告，不混成一个总分掩盖维度差异。

### 4.2 盲评与盲法（Generator ≠ Evaluator 保持）
- 盲评包：仅含 submission_id + 题面 + 产物 + 评分表，无臂标识。
- **形式对齐要求（关键测量效度点）**：S 臂产物为 JSON——盲评包渲染为"字段名: 值"卡片；F 臂产物为文本——**原样呈现**（不做结构化重排）。预注册声明：若 F 臂文本含全部信息但格式松散导致漏评，属于**形式效度偏差**，需在敏感性分析中报告（可做二次"宽容评分"对照）。
- 独立 evaluator（外部 Agent，Doubao 系），与 generator 隔离。

### 4.3 过程与协变量
- knowledge_trace：K002 无知识注入，trace 记录**结构遍历**（字段级完成度：18 字段是否全部实质性填充，非空字符串）。
- tokens / 产物长度 / 信息密度（RQ6）。
- failure mode 标注（与 K001 FM 分类一致）。

### 4.4 族命中判定（RQ5 教训：ontology 与字符串分离）
- 不使用 `model_family.primary == "dynamic_programming"` 严格字符串匹配。
- 命中 = `primary OR secondary OR mechanism OR solver` 任一落在预注册受控词表内（§1.5 的 Concept→Mechanism→Family→Model→Method→Solver 层级，词表在 FROZEN 时一并冻结）。
- 未命中但可论证的（out_of_catalog）：不自动判错，由盲评语义判断（与 K001 一致）。

---

## 5. 分析计划

- 主分析：F/S 配对差（blocked），效应量 + 95% CI（bootstrap / t 取决于分布），**与 K001 相同的决策门**（CI 下界 > 0 → positive）。
- 分层：主检验 3 题 / 泛化 2 题；按题报告。
- 敏感性：排除 COVERAGE_FAIL run 后重算；"宽容评分"对照。
- 不事后调 threshold；FROZEN 后不改 rubric/题面/schema。

---

## 6. 执行与治理

- 全程 `research/P15/`，不进 `core/`；不修改任何冻结规格（K001 frozen specs 原样保留）。
- 工具链：复用 k001_common/freeze/state 模式，新增 `k002_*`（register 增加 coverage gate + validation_plan gate；gen_bundles 生成 F/S/S+V 三种 prompt 模板）。
- **P0-E 前置（用户裁决 2026-09-09，优先级最高）**：K002 冻结排在 `P0-E Executable Model Runtime` 之后——ExecutionAdapter（真实执行）、execution_result 一等 artifact、Evidence←Execution 绑定、runtime validation 完成，再走 K002 dry-run → 五 Gate → PREREGISTERED → FROZEN。P0 工程项（①result 占位符治理 ✅ ②词表收敛 ✅ ③features 契约 ✅）已完成。
- 外部生成/盲评由独立 Agent 完成（与 K001 同模式：生成侧 1 个 Organizer + 分片子代理；盲评 3 个独立 evaluator）。
- 预注册签署 → **五 Gate 全 PASS（§7.5）** → FROZEN（哈希锁定 44+ 规格文件）→ PREFLIGHT → RUNNING → VALIDATION → ANALYSIS → CLOSED。

---

## 8. Validation Plan 字段规格（S+V 臂强制字段，草案）

S+V 臂在 MODEL_IR 之外强制输出 `validation_plan`，直接锚定 L4.3/L3.4/L1.4 三个已知弱维：

```jsonc
{
  "validation_plan": {
    "limit_tests": [                       // 锚 L4.3（K001 唯一有 0 分维度）
      {"condition": "c→0 时排队系统退化为无等待", "expected": "J→仅收益项", "result": "…"}
    ],
    "multi_seed": {                        // 锚 L3.4（K001 无一 2 分维度）
      "seeds": [42, 43, 44, 45, 46],
      "n_runs": 5,
      "metric": "目标函数值",
      "tolerance": "cv<10%",
      "result": "cv=…"
    },
    "sensitivity": [                       // 锚 L4.2
      {"parameter": "λ（到达率）", "range": "±20%", "metric": "J", "result": "…"}
    ],
    "ambiguity_handling": [                // 锚 L1.4（K001 全 1 分维度）
      {"source": "题面歧义点", "interpretations": ["…", "…"], "adopted": "…", "justification": "…"}
    ],
    "claim_evidence_map": [                // 锚 L4.5
      {"claim": "…", "evidence_ref": "experiment/…", "status": "supported|refuted|unresolved"}
    ]
  }
}
```

- **登记校验**（k002_register.py）：`limit_tests` 非空、`multi_seed.n_runs≥3`、`sensitivity` 非空、`ambiguity_handling` 非空、`claim_evidence_map` 每 claim 有 evidence_ref——机械 gate，非自报。
- 注意：**字段非空 ≠ 内容正确**（L4.3 要 2 分需检验结果合理）。本设计测的是"字段化是否驱动 Agent 执行验证行为"（1 分门槛：做了）；内容质量（2 分）由盲评判断——两者分开报告，避免"非空即正确"的 Formalized nonsense 风险。
- 设计约束：Validation Plan 字段只在 S+V 臂出现；S 臂维持 K001 同款 18 字段——保证 S 臂与 K001 B/D 臂可交叉参照（跨实验一致性）。

---

## 7.5 Measurement Gate（五 Gate 前置，全部 PASS 才允许 FROZEN）

> 背景：RQ5 词表错位（`dynamic_programming` vs `discrete_recurrence`）是一次真实的
> measurement failure——"我们测的东西"不是"我们声称测的东西"。K002 预注册此 Gate，
> 在 PREREGISTERED 之前逐项验证（每项附证据，不是口头声明）：

| # | Gate | 问题 | 验证方式 | 通过标准 |
|---|---|---|---|---|
| G1 | **Construct validity** | L3/L4 终点是否真的测 Model Construction？ | 逐维度对照 rubric 定义与 MODEL_IR 18 字段 + validation_plan 字段，确认评分项可被产物字段触发 | 每个评分维度至少 1 个产物字段可支撑（映射表冻结） |
| G2 | **Instrument validity** | evaluator 是否真的按 rubric 测？ | 3 个独立 evaluator 在 5 份盲评样例上的评分一致性（K001 已有 55 份基线可复用） | 维度级 Cohen's κ ≥ 0.6 或分歧可归因于模糊声明（报告） |
| G3 | **Vocabulary validity** | ontology 是否统一？ | `catalog/model_families.yaml` 单一词表 + 生成侧/评分侧解析测试（K001 词表错位回归用例） | 三源全部解析到 canonical，无 OUT_OF_CATALOG 意外 |
| G4 | **Execution validity** | 需要 execution 的终点（L3.4/L4）是否真的由真实执行支撑？ | 若某维度依赖数值结果，产物必须含 execution_result 或等价真实数值 provenance | 预检 run 的 L3/L4 评分项全部绑定真实数值（无占位） |
| G5 | **Statistical validity** | block 数是否足够？ | 预检 6 题区分度（§3.5）；block=6 排列功效预计算 | ≥4/6 题有区分度且功效 ≥0.8（效应量按 K001 Δ=+2.14 估计） |

- 任一 Gate FAIL → 回到对应修复（词表/工具/rubric/题集），修复后重跑该 Gate，全部 PASS 才 PREREGISTERED。
- Gate 证据归档到 `research/P15/protocol/preregistration/P15-K002-GATES.md`（冻结时一并 hash）。

---

## 7. 已知局限（预先声明）
1. F 臂"自由格式"是相对概念：prompt 仍要求覆盖主要建模成分，测的是 **schema 强制 vs 文本要求**，不是"无结构 vs 有结构"的极端对比。
2. 盲评形式对齐不完美（JSON vs 文本呈现差异）——已设计敏感性分析。
3. **n=108**（主检验 90 + 泛化 18；block=6 主检验最小 p≈0.016）。仍以效应量+CI 为主，不宣称"无效应"为"无差异"。
4. Representation 与 Knowledge 的交互不在本实验范围（K001 已单独测 Knowledge）。
5. 审计启示的 P0 工程项（result 占位/词表收敛/features 契约）与实验并行推进；若工程项未完成，K002 的 F/S 对照仍有效（research 层独立），但"生产层一致性"结论需以工程项完成后的复检为准。
6. **3 道新增题是 PREREGISTERED 前置**：若 authenticity 不可得则退回 5 题就绪集（block 降级到 3），如实声明功效降级；**不降级题目真实性换数量**。
