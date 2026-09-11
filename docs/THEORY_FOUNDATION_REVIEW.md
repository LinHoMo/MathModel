# THEORY_FOUNDATION_REVIEW — 理论基座缺口审查与优化方案

> Version: v0.1-draft ｜ Status: **REVIEW（待评审，未冻结）** ｜ Updated: 2026-09-11
> 性质：只读审查 + 方案提案，**不修改任何代码 / schema / runtime**；若立项实施，
> 一律走任务卡 + ADR（且不得触碰 canonical schema 与 runtime 业务逻辑的既有禁令）。
> 本文数字全部来自 `docs/STATUS.md` 机器实测口径与 `analysis/reports/` 正式报告，无新增编造。

---

## 0. 摘要（核心诊断）

> **落地状态（2026-09-11，标准层第一步）**：G4（EV1–EV5 证据义务矩阵）、G5（复杂度预算）、
> R3（结构距离工具）、R4（创新声明契约）均已实现并接入 `validate.py`（检查数 48→51）与 `cli/innovation_metrics.py`；
> 三实例已合规声明并反向验收；全量测试 681→683 passed。§9 记录了留给后续 agent 的遗留优化项。

当前 harness 的理论基座是一个**信任基座（negative epistemology）**：

> 它回答了「什么不可信」——反伪造（hash chain / execution_token）、反声明
> （Agent Claim ≠ System Fact）、可追溯（Evidence Graph / Replay / G1-G3），
> 且这套机制**工程上做得非常扎实**（651 tests / validate 48/0/0 / K003 执行闭环 66/66）。

但它**还没有回答「什么算好模型、什么算创新、如何知道」**（positive epistemology）：

| 维度 | 现状证据 | 结论 |
|---|---|---|
| 正向质量判据 | G1–G3 全是**诚实性门禁**（溯源/来源/校准披露），非质量判据；R1/R2（样本外、基线 delta）冻结为「不可算」 | 判据层无正向内容 |
| 创新理论 | 知识层仅有 6 张创新模式卡（`ip-*.yaml`），无创新定义、无度量、无生成/引导机制；`MODEL_QUALITY_CRITERIA` 明确不管创新 | 创新处于「未理论化」状态 |
| 测量工具 | K002 κ=0.4345 / K003 κ=0.260，持续 < 0.6；K003 L4 正效应被证循环论证（要求产出 validation_plan → rubric 评其存在） | 测量工具本身不可靠 |
| 实验对象 | K001–K003 全部在测 **harness 旋钮**（知识/表示/验证），从未对「模型自身的预测」做实验 | 实验性停留在「验证能跑」，未到「实验模型假设」 |

**一句话**：信任基座完备，质量/创新理论缺失，测量工具失准，实验对象偏窄——
三者叠加导致「能力提升」主张无法被独立证伪（`MODEL_QUALITY_CRITERIA §0` 自述的断层）。

优化方向因此有两条主线，**理论线**（补正向认识论）与**实验线**（把 harness 变成
「模型假设的检验器」），后者正是用户强调的「更加实验性」。

---

## 1. 审查方法与证据基线

- 按 AGENTS.md §1 必读顺序完整阅读：STATUS.md / V3.1_ARCHITECTURE.md /
  ONTOLOGY_TERMINOLOGY.md / TASKS.md / AGENTS.md。
- 扩展阅读：STRATEGIC_VERDICT.md、MODEL_CONSTRUCTION_GAP.md、
  MODEL_QUALITY_CRITERIA.md、P15/README.md、V3.1 架构文档。
- 实测数字引用（全部来自 STATUS.md 机器口径）：
  - K001：Δ=+2.14，CI[+0.00,+6.41]，符号置换 p=1.0，方法族命中率 22%
  - K002：S−F(MCQ) Δ=−4.85 CI[−7.98,−2.22]（NEGATIVE）；SV−F(VAL) +4.81（POSITIVE）；κ=0.4345
  - K003：S−F(MCQ) +3.76 CI[+2.13,+5.44]（POSITIVE，d=1.01）；SV−F(VAL) +39.92；
    正效应全部来自 L4（S−F +1.58 / SV−F +3.59），L2 显著负（−0.41 / −0.50）；κ=0.260
  - 结构覆盖：词表修订 r1 前 10/19=52.6% → 修订后 19/19=100%（同命令可复现）
  - 方法卡 27 张、失败卡 22 条、创新模式卡 6 张、playbook 14 篇

---

## 2. 十个理论维度缺口分析

> 成熟度评级为**审查评估**（非机器实测）：● 强 ｜ ◐ 中 ｜ ○ 弱 ｜ × 空。

### D1 正向认识论（模型质量的正向定义）—— ○
- **证据**：G1（数值溯源）/G2（参数来源）/G3（校准披露）只约束「不说谎」；R1（样本外）/R2（基线 delta）因无真值卡与留出数据而冻结为「不可算」。三实例交付以「诚实 + 可执行」收口，但「模型是否更好」无正向判据。
- **理论缺陷**：系统只有**否定式**认识论（什么不能宣称），没有**肯定式**认识论（什么构成质量证据）。「Execution success ≠ Model correct」正确分离了状态，但「correct」没有操作化定义——这是理论基座最深缺口。
- **方案**：建立**模型证据层级理论（Evidential Lattice）**。按 question type 声明证据义务谱系，每层机械可判定：

  | 证据层 | 机械判定 | 适用 |
  |---|---|---|
  | 证据层（EV 前缀规避既有 Evidence Gate E1–E9 编号；v1.1 已实现为 G4） | 机械判定 | 适用 |
  |---|---|---|
  | EV1 数学必然 | 量纲一致 / 守恒律 / well-posedness / 边界闭合 | 机理题 |
  | EV2 机制保真 | 推导链 ↔ 第一性原理引用（机器检查引用存在 + 公式形态） | 机理题 |
  | EV3 数据拟合 | 留出集拟合误差（非训练集） | 数据题 |
  | EV4 样本外预测 | held-out 相对误差 vs 平凡基线 | 预测题 |
  | EV5 决策效用 | sensitivity / robustness / 成本-收益报告 | 决策题 |

  每个 question 在 MODEL_IR 声明 `evidence_obligations`，门禁按声明检查（v1.1 已实现，粒度先实例级、后子问题级）。
  **标准化的是接口与证据义务，不是答案**（与项目定位一致）。
- **实验**：E1 —— 合成真值基准（见 D7），把 R1/R2 从「不可算」变「可算」。

### D2 创新理论（什么是模型创新）—— × ← 用户强调点
- **证据**：知识层有 6 张 `ip-*.yaml` 创新模式卡（如 mechanism-data-hybrid、cluster-then-model），但：无创新定义、无度量、无生成机制；`MODEL_QUALITY_CRITERIA` 明确只管质量不管创新；盲评 L4 是唯一创新载体且 κ 不可靠。创新目前只能「靠 LLM 随机涌现」。
- **理论缺陷**：无「模型创新空间」的可操作定义 → 无法测量、无法引导、无法训练、无法在判据中给创新以地位。
- **方案**：**创新空间理论（Innovation Space）**，把创新分解为可判定维度：

  ```
  Innovation Vector v = (d_structure, mechanism_novelty, solver_novelty,
                         composition_novelty, representation_novelty)
  d_structure = 1 − max_{s'∈S_known} sim(s, s')    # 在结构本体图上的距离
  ```

  创新声明进入 MODEL_IR：`innovation: {dimensions, structure_distance, evidence}`；
  验证义务：任何 `distance > 0` 的维度须附「与已知结构的差异论证」证据（引用链 +
  差异描述存在性，机器可查）。详见 §4 正式定义。
- **实验**：E3 —— 创新引导对照（注入创新模式卡 vs 不注入），测结构距离分布与创新维度得分。

### D3 简约性理论（复杂度治理 / 奥卡姆剃刀）—— ×
- **证据**：无任何复杂度度量；G3 只约束校准参数「披露」，不约束参数冗余；盲评中「简洁优雅」无机械对应。
- **理论缺陷**：无法区分「复杂但必要」与「复杂且冗余」；无法支持「更简单模型同样好」的主张；复杂模型可凭「看起来认真」在盲评占优。
- **方案**：**复杂度预算（Parsimony Budget）**——独立参数自由度（带 provenance 计数）、MODEL_IR 结构规模、可拟合问题的 BIC/AIC 类比较；每个假设/参数须「付租」（解释方差或承载机制，机械检查其被使用边）。
- **实验**：E7 —— 同题多构造（参数多 vs 少）对照，测样本外表现与复杂度关系，检验复杂度惩罚是否改变排名。

### D4 测量可靠性（盲评 κ）—— ○
- **证据**：K002 κ=0.4345、K003 κ=0.260，持续 <0.6；L4 正效应被判循环（要求产出 A → 评 A 存在 → 得分高）；报告在「如实披露」与「合理化低 κ」之间反复。
- **理论缺陷**：rubric 维度未操作化到可稳定复评；一个 L 维度混多个构念；无锚定样例；主观评分被当主判据输入（`MODEL_QUALITY_CRITERIA §4` 已降级为辅助，但 K 系列结论仍以盲评为终点）。
- **方案**：**锚定样例评分（Anchored Scoring）+ 构念分解 + 机械代理替代**——每维度配每个分数档的真实锚定 bundle；维度级 κ 报告；能机械化的全部机械化（G1–G3 方向），盲评只保留不可机械化的构念（创新、优雅）并降级。
- **实验**：E2 —— 同一 66 bundle 三协议（无锚定 / 锚定 / 机械代理混合）复评，测 κ 提升与排序变化；通过标准：锚定协议 κ ≥ 0.6 或明确裁定「盲评仅方向性参考」。

### D5 因果识别 / 方差分解 —— ◐
- **证据**：K 系列预注册 / 冻结 / 配对 / bootstrap 制度强（P15 铁律）；但只报平均效应（Δ+CI），不知分数方差来自何处；K005 2×2 析因（4 Constructor × 2 Runtime × 8 题 × 2 seeds = 120 runs）已预注册，正式数据 BLOCKED。
- **理论缺陷**：不知道「LLM 采样噪声 vs 表示格式 vs 问题难度 vs constructor 差异」各占多少方差 → 无法判断实验功效、无法定位 harness 真实杠杆、无法给「增益显著」以完整因果解释。
- **方案**：**方差组分分析（Variance Components）**——K005 矩阵完成后做随机效应分解（constructor / runtime / problem / seed / 残差），输出各组方差占比；功效分析用实测方差而非假设。
- **实验**：E6 —— K005 正式数据收集（需外部 Constructor 会话，禁止伪造；复用现成预注册协议）。

### D6 证据图语义（强度 / 冲突 / 独立性）—— ◐
- **证据**：Evidence Graph 14 种 typed relation、invalidation 传播、retract 剪死边——结构机制强；但边无强度、无证据冲突检测、无独立性概念。
- **理论缺陷**：「supports」不区分机制推导 / 数据拟合 / 数值验证 / 专家判断；两个 result 支持矛盾 claim 时无任何机制；证据链强度无法评估。
- **方案**：**证据强度理论**——边带 strength 类型；claim 有 support profile（多层证据来源）；**冲突检测**（支持同一 claim 的反向 result → 触发 investigation 节点）；证据链最小切割（去掉某边 claim 是否仍成立）。
- **实验**：E8 —— 证据消融实验：对已完成实例做证据链消融（去机制证据 vs 去数据证据），看 claim 存活率与结论稳定性。

### D7 泛化语料（真值缺口）—— ○
- **证据**：benchmark 语料全为 CUMCM 竞赛题（2026 题无真值卡）；R1/R2 因「无参考解/留出数据」冻结；CUMCM 22 份 rubric 中 13 份 `reference_results` 为空（不凭记忆伪造 GT——这是对的）。
- **理论缺陷**：harness 宣称通用「Model Construction」，但验证语料只有竞赛题，泛化主张无证据；竞赛题「无真值」使正向判据长期空转。
- **方案**：**双轨语料**——(a) **合成真值题**（Synthetic Ground-Truth Generator：LLM-free 模板，已知真实机制 + 可调难度/噪声/机制复杂度 → 真值由构造器直接给出），解锁 R1/R2；(b) 真实竞赛题保留「不可算但可比」（实例内 baseline delta）。
- **实验**：E1 —— 20 道合成题（5 结构族 × 4 难度），全循环跑通，报告预测误差与基线 delta。

### D8 学习闭环（知识更新理论）—— ○
- **证据**：K001 证明知识注入无测量效应（Δ=+2.14 CI 触 0，命中率 22%）；失败记忆（22 条 fm-*）与方法卡（27 张 mc-*）只增不减；无「何时失败卡升级为门禁」「何时知识卡降权」的规则。
- **理论缺陷**：知识库是**累积型**不是**学习型**——不根据实测结果调权，与 K001 负结果自洽（注入不改变选择）。「knowledge → better construction」从未被证明，也从未被设计成可学习的。
- **方案**：**信用加权知识更新（Credibility-weighted Knowledge）**——每条 mck/fm 卡带效果计数器（使用场景下的命中/失败统计）；检索按实测效果加权；知识卡升级为门禁须达证据阈值（≥N 次使用 + 命中率 > P + 无反例）。
- **实验**：E5（K006）——把失败记忆反哺检索（失败卡 → 红旗），第二轮构造 vs 无更新对照组，测选择改变率。

### D9 模型即假设（预测实验范式）—— ○ ← 实验性核心
- **证据**：K003 证明「验证义务 + 执行闭环」是唯一正效应来源（SV−F VAL +39.92）；但验证对象是「代码能跑、字段齐全」，不是「模型预测是否正确」。
- **理论缺陷**：当前实验范式是**验证模型能跑**（execution / fidelity / structure），不是**实验模型的预测**。数学建模的本质是「模型 = 关于世界的假设」，harness 却没有把它当作假设来检验。
- **方案**：**Model-as-Hypothesis 范式**——每个构造的模型必须产出**可证伪预测（Predictive Probes）**：在未观测条件下的模型预测（如 2026A 烘干题：预测未测烘房温度下的时长）；harness 机械执行预测实验（模拟器 / 留出数据 / 附件实测），按**预测命中率**给模型评分。模型是假设生成器（外部 Constructor 产出），harness 是检验器（LLM-free 机械执行）——不违反 core LLM-free。
- **实验**：E4 —— 预测探针基准：2026A 烘干题 5 个未测条件预测 vs 附件数据/模拟器，命中率作主终点。

### D10 实验文化制度化（范围与边际）—— ◐
- **证据**：预注册 / 冻结 / 盲评隔离 / 负结果如实披露的制度**在 repo 内是顶级的**；但 K 系列已边际递减：K001 negative、K002 negative、K003 positive-but-circular-L4；且实验假设空间被局限在「harness 旋钮」上。
- **理论缺陷**：实验对象的「理论模型」没有随实验迭代——三场实验都在回答「表示/知识/验证哪个有用」，没有一场回答「模型的预测可信吗」或「创新可测量吗」。
- **方案**：把 §2 的 E1–E8 立项为 **K 系列下一梯队（K006–K009）**，预注册制度原样继承；新增「实验对象登记」：每个实验必须声明其在「模型质量 / 模型创新 / 测量方法 / 学习机制」四象限中的位置，防止重复测量同一旋钮。

---

## 3. 优化方案总览

### 3.1 两条主线

```
主线 A · 理论线：信任基座 → 信任基座 + 质量/创新理论
  D1 Evidential Lattice（证据义务矩阵）
  D2 Innovation Space（创新空间，见 §4）
  D3 Parsimony Budget（复杂度预算）
  D6 Evidence Strength（证据强度/冲突）
  D8 Credibility-weighted Knowledge（信用加权知识更新）

主线 B · 实验线：harness 旋钮实验 → 模型假设实验
  D7 Synthetic Ground-Truth（合成真值，解锁 R1/R2）
  D9 Predictive Probes（预测探针，Model-as-Hypothesis）
  D5 Variance Components（方差分解，K005 落地）
  D4 Anchored Scoring（锚定测量，κ 修复）
  D10 实验对象登记（四象限防重复）
```

### 3.2 三阶段路线图（沿用用户裁定的「标准层 → 能力层 → 产物层」顺序）

| 阶段 | 内容 | 交付物 | 是否触碰禁令区 |
|---|---|---|---|
| **标准层（判据）** | D1 证据义务矩阵化（G4）、D3 复杂度预算（G5）、D2 创新声明接口（R3 结构距离 / R4 创新维度） | `MODEL_QUALITY_CRITERIA` 修订案 + validator 提案 + MODEL_IR 扩展提案 | 判据文档可改；validator/schema 实施须任务卡 + ADR（现为提案） |
| **能力层（度量）** | D4 锚定盲评协议 v2、D5 方差组分分析、D7 合成真值生成器（LLM-free）、D8 信用加权检索 | 新实验协议（K006–K009 预注册）+ 测量工具 | 均在 research/ 与测量层，不触 runtime 业务 |
| **产物层（应用）** | D9 预测探针进生产 DAG、D6 证据冲突检测、创新报告进 MODEL_IR | 实例级试点（2026A 预测探针）+ 真值卡建设 | 生产 DAG 改动须走既有治理例外通道（RUNTIME_CONTRACTS） |

### 3.3 优先级矩阵（影响 × 成本）

| 优先 | 方案 | 理由 |
|---|---|---|
| P0 | D7 合成真值生成器 + E1 | 一次解锁 R1/R2 + D1 的实证基础，杠杆最大 |
| P0 | D4 锚定评分 + E2 | 修测量工具，后续所有实验的终点可信 |
| P1 | D2 创新空间 + E3 | 用户强调点：创新从「无法言说」变「可度量可引导」 |
| P1 | D9 预测探针 + E4 | 实验性升级：从验证到实验 |
| P2 | D5 方差分解（K005）/ D8 知识闭环（K006）/ D6 证据强度 / D3 复杂度预算 | 依赖 P0 的语料与测量先行 |

---

## 4. 理论模型创新提案：Innovation Space（创新空间）

> 目标：把「模型创新」从盲评印象变成**接口 + 证据**（与项目「标准化表达/接口/证据而非答案」定位一致）。

### 4.1 形式定义

- 结构本体图 `O`：节点 = Modeling Structure（建模结构/regime），边 = 父子/组合关系。
- 题的已知结构集 `S_known ⊂ O`（来自 benchmark 的 `allowed_modeling_structures`）。
- 模型声明结构 `s ∈ O`；**结构距离** `d_structure(s) = 1 − max_{s'∈S_known} sim(s, s')`，`sim` 在 `O` 上定义（祖先/子孙/邻居衰减相似度）。
- **创新向量** `v = (d_structure, mechanism_novelty, solver_novelty, composition_novelty, representation_novelty)`，各分量 ∈ [0,1]，由机械特征提取（MODEL_IR 字段比对 / 代码依赖 / 结构图）给出候选值，人工或盲评确认。

### 4.2 MODEL_IR 扩展接口（提案 → v1.1 已落地为 opt-in 契约）

```jsonc
{
  "innovation": {
    "structure_distance": 0.42,        // 机械计算，须附结构图引用
    "dimensions": {
      "mechanism_novelty": 0.3,
      "solver_novelty": 0.0,
      "composition_novelty": 0.8,      // 跨结构组合
      "representation_novelty": 0.0
    },
    "difference_arguments": [           // 验证义务：distance>0 的维度必须引用
      {"dimension": "composition_novelty", "vs_known": "M001", "argument_ref": "model.md#sec3"}
    ]
  }
}
```

### 4.3 门禁语义（v1.1 已实现：`check_innovation_declaration`，契约核验；Rank 由 `innovation_metrics.py` 承担）

- `structure_distance == 0` 且各维度均为 0 → 模型为**已知结构的忠实实例化**（合规，创新声明不可虚报）。
- 任一维度 > 0 → 必须附 `difference_arguments`（引用链 + 差异论证存在性，机器可查）；缺失 → 该创新声明 FAIL（防「自称创新」）。
- 创新得分**进 Rank 不进 Gate**（与 R1/R2 同理：创新是排序线，不是合格线）。

### 4.4 证伪条件

若出现「结构距离高但盲评/预测表现差」的模型被广泛采用 → 结构距离不是好的创新代理，须换度量（与 `MODEL_QUALITY_CRITERIA §3` 同款自反证伪）。

---

## 5. 实验性增强提案（K 系列下一梯队）

> 编号约定：本节实验编号 **E1–E8** 属提案命名空间（对应 K006–K009），
> 与已实现的证据层 **EV1–EV5** 无编号冲突（EV 前缀为证据层专用）。

| 实验 | 名称 | 设计要点 | 主终点 | 前置 |
|---|---|---|---|---|
| E1 | Synthetic GT | 20 合成题（5 结构族 × 4 难度），LLM-free 生成器（模板 + 已知机制 + 可调噪声/复杂度），真值由构造器给出 | R1/R2 可算后的预测误差、基线 delta | 生成器 |
| E2 | Anchored Scoring | 66 bundle × 3 协议（无锚定/锚定/机械混合）复评 | κ 提升、排序稳定性 | 锚定样例集 |
| E3 | Innovation Guidance | 创新模式卡注入 vs 无注入，同一 constructor | 结构距离分布、创新维度得分 | D2 接口落地 |
| E4 | Predictive Probes | 2026A 烘干：模型预测 5 个未测条件 vs 附件数据/模拟器 | 预测命中率 | 探针协议 |
| E5 | Knowledge Loop（K006） | 失败记忆反哺检索 vs 无更新 | 选择改变率（第二轮构造） | 信用加权检索 |
| E6 | Variance Components | K005 正式 120 runs（外部 Constructor） | 四源方差占比、功效重算 | 外部会话（已 BLOCKED 如实） |
| E7 | Parsimony | 同题多构造（参数多 vs 少） | 样本外表现 vs 复杂度 | E1 语料 |
| E8 | Evidence Ablation | 已完成实例证据链消融 | claim 存活率、结论稳定性 | — |

**全部遵守 P15 铁律**：预注册先行、冻结后只读、盲评隔离、负结果如实、种子 42、多种子 ≥5。

---

## 6. 边界与合规声明（v1.1 落地补充：新门禁全部为 opt-in 契约，未触碰 canonical schema 与 runtime 业务逻辑，core 保持零依赖）

- 本文是**只读审查 + 提案**：未修改任何代码 / schema / runtime / 测试。
- 若立项：标准层实施走任务卡（六要素）+ ADR；触碰 `schemas/v3/` 或 `runtime/` 业务逻辑
  属既有禁令区，须先走治理例外通道（RUNTIME_CONTRACTS），**不预设豁免**。
- 全部方案保持 **core LLM-free**：合成真值生成器 = 模板 + 确定性机制，预测实验 = 机械执行，
  创新向量 = 特征提取；LLM 只出现在外部 Constructor（现状不变）。
- 全部数字以 STATUS.md 实测口径为准；本审查中的成熟度评级为**评估意见**，非测量数据。

---

## 7. 待人工确认项（建议登记 T-CONF-xxx）

| # | 问题 | 选项 | 建议 |
|---|---|---|---|
| C-1 | 创新空间（D2）是否作为 MODEL_IR 扩展接口立项？ | A 仅文档/ B 接口+门禁 / C 暂缓 | B（接口先行，门禁随 G 系列） |
| C-2 | 合成真值生成器（D7）是否立项？ | A 立项 / B 暂缓 | A（解锁 R1/R2，杠杆最大） |
| C-3 | 盲评处置（D4）：锚定协议或「仅方向性参考」？ | A 锚定重修 / B 降级 / C 双轨 | A（先试锚定，κ 仍 <0.6 再降级） |
| C-4 | K 系列下一梯队命名（K006–K009 对应 E5/E4/E3/E1）是否确认？ | A 确认 / B 调整 | A |

---

## 8. 验收标准（本文档自身）

1. 十个维度均有「现状证据（可追溯）+ 缺陷 + 方案 + 实验」四要素。
2. 所有引用数字可回溯到 STATUS.md / analysis/reports/（本节已列）。
3. 方案不违反 AGENTS.md §5 禁令（无新运行时依赖、不改 canonical schema、
   core LLM-free、不伪造产物）。
4. 若用户裁定立项，再按任务卡流程拆解实施，本文不构成实施授权。


---

## 9. 遗留弱项与后续优化（登记给后续 agent 继续思考）

> 用户裁定：凡「轻微优化 / 无真实更优化」的部分不得硬改，一律文档记录给后续 agent。
> 本节即该登记册；每条含背景、方案、收益与验证方式。已实现的门禁与工具按「先入流程、再迭代」原则落地。

### 9.1 显式引用契约（根治 G4/G5 启发式的核心遗留项）—— 建议优先

- **背景**：G5 死参数判定与 G4 证据支撑目前靠**字符串/词表启发式**。真实踩坑（2026b P13/P14）证明：表示变体（字符串值、int↔float、符号转写）永远有边界；反之「凑词通过」「无关数值误判通过」也防不住。
- **方案**：契约级升级——① `parameters[].used_in = [{type: "equation|code|objective|constraint|validation", ref: "E01" | "solve.py#L42", how: "symbol|value"}]`，门禁从「全库猜引用」变「核验声明引用」（ref 可解析 + 声明字段在 target 中真实出现）；② `evidence_obligations` 的每层加 `evidence_refs`（指向具体 validation/claim/result 键），G4 从「词表命中」变「引用存在性核验」。
- **收益**：误报/漏报从「字符串匹配问题」降为「声明不诚实问题」，后者才是门禁该管的；同时给 Evidence Graph 提供参数→方程、义务→证据的真实边（反哺 D6）。
- **代价**：Constructor/实例需多声明字段（表达接口标准化，符合项目定位）；需先修订 MODEL_IR 契约文档（不改 canonical schema，靠 additionalProperties 渐进）。
- **验证**：对三实例补齐 used_in 声明后，G5 误报回归测试全部保留仍绿；再注入「声明了 used_in 但引用不存在」→ 新门禁 FAIL。

### 9.2 双级门禁（启发式 → WARN，显式 → FAIL）

- **背景**：当前启发式未命中直接 FAIL；修复后走向「从宽匹配」（宁可漏报死参数），又丢了查真死参数的能力。
- **方案**：检测分层——硬信号（显式 refs / parameter_id 引用）未命中才判 FAIL；软信号（符号/名称/值启发式）未命中且无显式声明 → **WARN**（可能死参数，人工确认）。对齐 validate.py 既有 WARN 级机制。
- **验证**：构造「只有软信号缺失」的夹具 → 应 WARN 不 FAIL；构造「显式声明但引用缺失」→ FAIL。

### 9.3 R3 结构距离：本体图连续化 + 声明值审计

- **背景**：当前一阶二值（family ∈ allowed → 0/1），声明值直接采用且不审计；三实例均声明 0.00。
- **方案**：① 建结构本体图 `O`（节点=建模结构，边=父子/组合），`d_structure = 1 − max sim(s, s_known)` 连续化；② 审计声明值与机械计算值的偏差，偏差超阈值 → WARN（防虚报创新/虚报从众）。
- **验证**：本体图 20+ 节点时，对 2026a（组合 novelty=0.3）给出非平凡距离并解释。

### 9.4 G4 子问题粒度 + 证据独立性

- **背景**：G4 现为实例级（任一证据支撑全实例所有子问题的同层声明）。
- **方案**：义务按子问题声明（接口已支持），证据检查下钻到子问题；引入证据冲突/独立性（同一证据支撑两层声明时权重衰减）。
- **验证**：构造「Q2 声明 EV3 但该子问题无拟合证据」→ 子问题级 FAIL。

### 9.5 门禁自身质量度量（门禁的门禁）

- **背景**：本次 P13/P14 事件暴露「门禁没被真实语料度量过」。
- **方案**：建**参数使用金标准表**（三实例每个参数的 used/not-used 人工真值），每次门禁改动后重跑对照，报告误报率/漏报率；阈值：误报率 < 5%（宁可漏报）、漏报率 < 1%（真死必抓）。
- **验证**：金标准表入库 `tests/fixtures/`，CI 里随 pytest 跑。

### 9.6 符号归一化表完备化（低优先）

- **背景**：`_normalize_symbol` 覆盖希腊字母 + 上下标 + 分隔符 + 大小写，但「语义等价字符串不同」的情况（COVER_RADII_DIR vs ρ_ring,dir）靠归一化永远治不彻底。
- **方案**：维护「声明符号 ↔ 代码标识符」映射表（实例内），作为 used_in 契约的前置一步；不在字符串归一化上无限加规则。

### 9.7 轻微优化记录（未做，留档）

- validate.py 新门禁的 FAIL 消息可进一步输出「该参数已尝试的全部信号」明细（当前只报死参数清单 + used/total）。
- `innovation_metrics.py` 可加 `--json` 输出便于流水线消费（当前仅表格）。
- G5 语料可加入 `artifacts/data/*.csv`（当前只含 code/*.py 与根 md）；因可能引入大量噪声，未做——留给后续 agent 用金标准表验证后再启用。

---

## 10. 本次落地变更清单（v1.1，供追溯）

| 变更 | 文件 | 验证 |
|---|---|---|
| G4 证据义务矩阵门禁 | `src/modeling_harness/cli/validate.py::check_evidence_obligations` | 单测 10 例 + 实例反向验收 |
| G5 复杂度预算门禁（含值/符号归一化与真实踩坑回归） | `validate.py::check_parsimony_budget` + `tests/unit/test_parsimony_budget.py` | 单测 9 例（含 P13/P14 回归、int↔float、分隔符变体） |
| R4 创新声明契约门禁 | `validate.py::check_innovation_declaration` | 单测 8 例 + 实例反向验收 |
| R3 结构距离工具 | `src/modeling_harness/cli/innovation_metrics.py` | 单测 4 例 + 三实例运行 |
| 三实例合规声明 + registry sha256 同步 | `projects/{cumcm2024a,cumcm2026a,cumcm2026b}/model_ir.json` + `state/registry.json` | validate 51/0/0 |
| 判据文档 v1.1 | `docs/architecture/MODEL_QUALITY_CRITERIA.md` | 本文 §2.1.2–2.1.4 |
