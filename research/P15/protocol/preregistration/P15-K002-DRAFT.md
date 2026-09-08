# P15-K002 — Model Representation Efficacy
## 预注册（Preregistration）DRAFT v0.1

> **状态：`DRAFT`（待三仓库审计报告回填"吸收优点"后定稿 → PREREGISTERED → FROZEN）**
> **科学定位**：K001（Knowledge 文本注入）已得 negative result；本实验检验**下一个杠杆：强制的结构化 Model Representation（输出契约）本身是否提升外部 Agent 的 Model Construction Quality**。
> **上游**：P15-K001 ✅（Δ_K=+2.14 CI[+0.00,+6.41] negative；Sham 11/11 正确拒绝；adapted 58%）｜ KNOWLEDGE_BASE_QUALITY_BASELINE（仅 3/19 卡为完整建模知识）

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

### 3.3 规模
| 用途 | 题 | 臂 | 重复 | runs |
|---|---|---|---|---|
| 主检验 | 2020_B、2018_A、2019_C | 3 | 5 | 45 |
| 泛化观察 | 2022_C、2024_A | 3 | 3 | 18 |
| **合计** | | | | **63** |

（与 K001 同题集同构；F/S 臂可与 K001 的 A/B 臂交叉参照。）

### 3.4 强制子问题覆盖 gate（K001 教训落点）
- 每 run 的 `problem_binding.sub_question_id` 必须覆盖该题全部子问题（2020_B→Q1-Q3 等），缺任一子问题 → 该 run 标记 `COVERAGE_FAIL`，**不进入主终点**（单独报告，与 K001 的 2 个 FAIL 同口径）。
- 同时记录 coverage 作为 RQ2 的连续指标。

### 3.5 题目区分度预检（K001 per-block 教训落点）
K001 按题分解发现 2019_C 全臂恒定同分（零区分度），实际有效 block 只有 2/3。K002 预注册：
- 主检验题集（2020_B/2018_A/2019_C）先各跑 1 个预检 rep（2 臂 × 3 题 = 6 runs），计算每题 F/S 各条件内方差与条件间差。
- **预检规则（预先声明）**：某题若 F/S 两臂全部 run 得分相同（条件内方差 = 0 且条件间差 = 0），标记为**无区分度 block**，从主效应估计中剔除并单列报告；剩余题正常进入主检验。
- 预检 run 计入最终分析（不浪费），仅标注来源。
- 若 3 题中 ≥2 题无区分度：判定主检验题集区分力不足，STOP 并回到题目选择（不继续跑满）。

---

## 4. 测量

### 4.1 主终点
- **MCQ_primary** = L2 composite（MODEL_CONSTRUCTION_RUBRIC v1.0：L2.1/2.2/2.4/2.5/2.6(权重3)/2.7，/13×100）——与 K001 **完全一致**，跨实验可比（注意 L2 已饱和，预期区分力有限，如实报告）。
- **VAL_primary** = L4 composite（L4.1–L4.5，/10×100）——**本实验新增关键终点**，针对 L4.3 0 分率 16.4%、L3.4 无一 2 分的已知弱环，检验"验证行为字段化"是否提升。
- 次要：L1（歧义处理 L1.4）、L3（求解层 L3.4 可复现性）分层报告。

### 4.2 盲评与盲法（Generator ≠ Evaluator 保持）
- 盲评包：仅含 submission_id + 题面 + 产物 + 评分表，无臂标识。
- **形式对齐要求（关键测量效度点）**：S 臂产物为 JSON——盲评包渲染为"字段名: 值"卡片；F 臂产物为文本——**原样呈现**（不做结构化重排）。预注册声明：若 F 臂文本含全部信息但格式松散导致漏评，属于**形式效度偏差**，需在敏感性分析中报告（可做二次"宽容评分"对照）。
- 独立 evaluator（外部 Agent，Doubao 系），与 generator 隔离。

### 4.3 过程与协变量
- knowledge_trace：K002 无知识注入，trace 记录**结构遍历**（字段级完成度：18 字段是否全部实质性填充，非空字符串）。
- tokens / 产物长度 / 信息密度（RQ5）。
- failure mode 标注（与 K001 FM 分类一致）。

---

## 5. 分析计划

- 主分析：F/S 配对差（blocked），效应量 + 95% CI（bootstrap / t 取决于分布），**与 K001 相同的决策门**（CI 下界 > 0 → positive）。
- 分层：主检验 3 题 / 泛化 2 题；按题报告。
- 敏感性：排除 COVERAGE_FAIL run 后重算；"宽容评分"对照。
- 不事后调 threshold；FROZEN 后不改 rubric/题面/schema。

---

## 6. 执行与治理

- 全程 `research/P15/`，不进 `core/`；不修改任何冻结规格（K001 frozen specs 原样保留）。
- 工具链：复用 k001_common/freeze/state 模式，新增 `k002_*`（register 增加 coverage gate；gen_bundles 生成 F/S 两种 prompt 模板）。
- 外部生成/盲评由独立 Agent 完成（与 K001 同模式：生成侧 1 个 Organizer + 分片子代理；盲评 3 个独立 evaluator）。
- 预注册签署 → FROZEN（哈希锁定 44+ 规格文件）→ PREFLIGHT → RUNNING → VALIDATION → ANALYSIS → CLOSED。

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

## 7. 已知局限（预先声明）
1. F 臂"自由格式"是相对概念：prompt 仍要求覆盖主要建模成分，测的是 **schema 强制 vs 文本要求**，不是"无结构 vs 有结构"的极端对比。
2. 盲评形式对齐不完美（JSON vs 文本呈现差异）——已设计敏感性分析。
3. n=42，功效有限（与 K001 同级）——以效应量+CI 为主，不宣称"无效应"为"无差异"。
4. Representation 与 Knowledge 的交互不在本实验范围（K001 已单独测 Knowledge）。
