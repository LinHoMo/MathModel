# P13-3C Report — Model Construction Generalization & Comparative Benchmark

> 日期：2026-09-06 · 实验性质：**能力实验**（区别于 P13-3B 的干预实验）。
> 治理铁律：**任何能力升级，如果没有 baseline，就不算能力升级。**
> 表述纪律：MMA 臂 = "MathModelAgent Modeler prompt 的 same-LLM
> operationalization baseline"，**不是**完整 MathModelAgent runtime 复刻。
> 评分口径纪律：**Rubric score ≠ absolute correctness**——分数是"当前冻结
> rubric 下由盲评得到的评分"；且盲评存在轮间评委方差，**消融结论只做
> 同轮内对比**（Round 4 四臂同轮同评委）。

## 0. Round 4 — Ablation（子干预归因实验）✅

**固定**：2024_A（机理）/ 2022_B（优化）、同 LLM/schema/scorer/rubric、
匿名四臂（W/X/Y/Z）、独立盲评。

**臂定义（预注册）**：
- B1-A = 仅对齐干预（对齐点→承载变量/方程映射 + 参数全声明）
- B1-C = 仅约束干预（约束形式化 + 变量域一致 + 工程边界完备）

### 4.1 消融矩阵（同轮盲评）

**2024_A（Mechanism）**

| 臂 | Struct | Math | Align | Composite | major 缺陷数 |
|---|---|---|---|---|---|
| B0 | 30 | 65 | 25 | 40.0 | 4 |
| **B1-A** | 63 | **45** | **50** | 52.7 | **6** |
| **B1-C** | 67 | **80** | 25 | 57.3 | **1** |
| B1-F | 100 | 70 | 100 | 90.0 | 2 |

**2022_B（Optimization）**

| 臂 | Struct | Math | Align | Composite | major 缺陷数 |
|---|---|---|---|---|---|
| B0 | 57.1 | 85 | 0 | 47.4 | 3 |
| **B1-A** | 90 | **20** | **100** | 70.0 | **5** |
| **B1-C** | 61.4 | **80** | 25 | 55.5 | **2** |
| B1-F | 90 | 55 | 100 | 81.7 | 2 |

### 4.2 H4a / H4b 判定

- **H4a（对齐干预 → Alignment↑↑/Structural↑/Math≈）：部分否定**。
  Alignment ↑↑ ✅（25→50、0→100）；Structural ↑ ✅；**但 Mathematical
  暴跌 ❌（65→45、85→20）**，且 major 缺陷数反超 B0（6>4、5>3）。
- **H4b（约束干预 → Structural↑↑/Math↑/Alignment≈）：成立**。
  Structural ↑（30→67、57.1→61.4）；Math 2024_A ↑（65→80）、2022_B 持平
  （85→80，同轮内）；Alignment ≈ ✅（25→25、0→25）；major 缺陷两题均降
  （4→1、3→2）。

### 4.3 核心发现：对齐干预在无约束纪律时**制造不被模型支持的主张**

**因果措辞纪律**：n=2 题 × 4 臂足以发现现象，不足以稳定估计交互效应量。
正式表述（全文以此为准）：

> 在本轮两个题目、四个实验臂的条件下，**单独施加 Alignment intervention
> 与 Mathematical Correctness 的下降同时出现，且该负向效应在两个 regime
> 中复现**；Full intervention 显著缓解该负向效应，提示 Alignment 与
> Formal Consistency 两类干预之间存在 **interaction**。

机理（评委逐条实锤，作为该现象的解释候选而非因果断言）：

1. **无生成通道的估计量**：B1-A 承诺"灭绝概率与规模方差对比"（Q2），
   但其确定性、无死亡项的模型根本不能生成该量——文字有映射、模型无
   通道（structural_degeneracy，major）；
2. **发散的新耦合**：为承载 Q4 新增的寄生者方程 dP/dt = γ_p·N·P − δ_P·P
   无饱和项且 P 不反馈 N——γ_p·N > δ_P 时 P 指数发散（物理不可能）；
3. **量纲失配**：新增耦合的质量作用项与声明单位冲突。

即：**对齐映射扩大了模型的主张面（新估计量、新耦合），约束纪律缺位时
每个新主张都是无支持主张**。这就是 Mathematical 45/20 的来源。

### 4.4 交互效应（Step 4 的核心答案）✅ 确认

- **B1-A 单独 = 有害**（math −20/−65，major 缺陷 +2/+2）；
- **B1-C 单独 = 安全但不足**（math 持平偏正、major −3/−1，但 alignment
  仍死）；
- **B1-F = A 的对齐收益 + C 的纪律包含**：alignment 达到 A 的水平
  （100/100），math 显著高于 A（70/55 vs 45/20）但低于 C（80/80）——
  **约束纪律部分（未完全）包含了对齐扩张的损伤**（更多机制面 = 更大
  误差面）。
- Composite 上的超可加性：2024_A B1-F 90.0 > max(B1-A 52.7, B1-C 57.3)；
  2022_B 81.7 > max(70.0, 55.5)。

**Model Construction 的分解结构（本轮确立）**：

```text
Model Construction
   ├── Problem Alignment（主张面：模型声称回答什么）
   └── Formal Consistency（支持面：模型能兑现什么）
两者缺一不可；先扩主张面、后补支持面 = 中间态更差（B1-A）。
```

### 4.5 缺陷计数指标（新增，独立于三维分）

major 缺陷数（评委独立列出）：B1-C 在两题均低于 B0（4→1、3→2），
是唯一"加干预、减缺陷"的臂；B1-A 在两题均高于 B0（4→6、3→5）。
**rubric 分与缺陷数在 B1-A 上出现背离**（composite 52.7/70.0 但缺陷
更多）——验证了"rubric score ≠ absolute correctness"，缺陷计数作为
独立仪表盘保留（severity/category/evidence 三字段永久记录）。

### 4.6 核心抽象：Claim Surface × Support Surface（P13-3 的中心概念）

四轮实验（干预 → 泛化 → 消融）共同指向同一个二维分解：

```text
                    Support Surface
                  （Formal Consistency：
                   方程/参数/约束/域——
                   模型能兑现什么）
                         ↑
                         │      ● B1-F（大主张 + 强支持）
                         │
                         │  ● MMA（中主张 + 中支持：
                         │    方案强、形式化缺）
          ● B0（小主张 + 中支持：      │
            少说所以少错）             │
                         │   ● B1-A（大主张 + 弱支持
                         │      = unsupported claims）
                         └──────────────────→
                              Claim Surface
                         （Problem Alignment：
                          模型声称回答什么）
```

四轮故事的同一机制四种读法：

| 轮 | 臂/现象 | Claim Surface | Support Surface | 结果 |
|---|---|---|---|---|
| R1-2 泛化 | B0 | 小（alignment 0-40） | 中（math 60-90） | "数学还能做但答非所问" |
| R1-2 泛化 | MMA | 中（alignment 58.3） | 中（方案强、形式化缺） | 结构↑对齐↑但 constraints 空置 |
| R4 消融 | B1-A | 大（alignment 50-100） | **未同步扩大** | unsupported claims → math 暴跌 |
| R4 消融 | B1-F | 大 | **同步扩大** | alignment 100 + structural 100 |

**因果故事（四轮串联）**：

```text
P13-3B Intervention Discovery（55→95 自评）
   ↓
P13-3C Cross-regime Generalization（3 regime，B1>MMA>B0）
   ↓
P13-3C-R4 Ablation / Interaction（H4a 否定 + 交互确认）
   ↓
★ Claim Surface × Support Surface ★
   ↓
P13-3C-R5 Expanded Benchmark（≥10 题验证）
   ↓
P13-3D Model → Paper
```

### 4.7 派生指标预注册：Claim Coverage / Support Coverage

把上述定性机制变成可量化变量（R5 起由盲评评委直接输出）：

- **Claim Coverage** = 题目要求中被产物明确承载的对齐点比例
  （即 alignment 维度，已有）。
- **Support Coverage** = 产物主张（objective/estimand/mechanism 声称）中
  **有正式数学承载**的比例。判定三条件逐条核验：
  ①存在能生成该主张的机制方程；②方程引用的参数全部已声明；
  ③主张类型与模型结构相容（确定性模型不得声称随机量）。
  Support Coverage = 支持的主张数 / 总主张数。
- **Claim-Support Gap** = Claim Coverage − Support Coverage（B1-A 预期
  为大正值、B0 为负值、B1-F 接近 0）。
- 预期复现（R5 待验）：B0 claim↓/support 中；B1-A claim↑↑/support↓；
  B1-F claim↑/support↑。

## 1. 预注册（建模前落盘）

- **未见题（题型覆盖，三题三 regime，均未触碰）**：
  | 题 | regime | rubric |
  |---|---|---|
  | 2024_A 七鳃鳗性别比 | Mechanism（机理-生态） | `mc_2024A.json` |
  | 2021_C 亚洲大黄蜂 | Data（数据-分类-优先级） | `mc_2021C.json` |
  | 2022_B 两库水资源 | Optimization（资源-优化-政策） | `mc_2022B.json` |
- **三臂（同一 LLM）**：B0 原始核心 / MMA（Modeler 提示词逐字执行，
  `mma_modeler_prompt.md` 存档）/ B1（清单 v2 全项过检）。
- **评分契约**：MODEL_ARTIFACT v1（`core/schemas/model_artifact.schema.json`
  冻结）；盲评协议 = 匿名化 + 独立子代理评委（无臂身份知识）。
- **假设**：H1 in-domain（已证）；H2 out-of-domain transfer；H3 结构性传导。

## 2. 结果：3 题 × 3 臂 = 9 份 Model Artifact，全部匿名盲评

### 2.1 主矩阵（composite，等权三维）

| Arm \ Regime | Mechanism (2024_A) | Data (2021_C) | Optimization (2022_B) | **mean** | median |
|---|---|---|---|---|---|
| B0 | 55.7 | 63.7 | 30.7 | **50.0** | 55.7 |
| MMA | 83.3 | 85.0 | 83.3 | **83.9** | 83.3 |
| B1 | **96.7** | **96.7** | **88.3** | **93.9** | 96.7 |

### 2.2 分维度（不报 composite 的理由在此）

| 维度 | B0 | MMA | B1 | 备注 |
|---|---|---|---|---|
| Structural | 51.7 | **86.7** | **100** | B0 三题全崩；MMA 方案级结构强 |
| Mathematical | **76.7** | 73.3 | 81.7 | **最平的维度**——三臂差距最小 |
| Alignment | 21.7 | 58.3 | **100** | B0 的 0-40 是全实验最大信号 |

### 2.3 逐题逐维明细（解盲后）

| 题 | 臂 | Struct | Math | Align | 盲评关键扣分（全部有原文证据） |
|---|---|---|---|---|---|
| 2024_A | B0 | 57 | 85 | 25 | 三问无模型承载通道（Q1/Q3/Q4） |
| 2024_A | MMA | 90 | 85 | 75 | Q1 生态冲击通道在变量中不存在；constraints 空 |
| 2024_A | B1 | 100 | 90 | 100 | μ/ω/η/δ/φ/R0 未声明；噪声可产生 R<0 |
| 2021_C | B0 | 61 | 90 | 40 | **标签极性矛盾**（p_hat 定义为误报概率却按其降序优先调查）；无预算约束/更新机制/根除判定 |
| 2021_C | MMA | 80 | 75 | 100 | M1 计数与质心相加量纲不一致；根除判定的努力/阈值无可执行形式 |
| 2021_C | B1 | 100 | 90 | 100 | ρ/v/w、e(t)/λ*/D_t_eff/λ_disp/K_spatial 未声明 |
| 2022_B | B0 | 37 | 55 | **0** | 死水位/发电机制/抽水上限/短缺松弛/代价定义五项全缺；四问对齐 0 |
| 2022_B | MMA | 90 | 60 | 100 | 月期量与年率需求无折算；最低发电水位未入约束；过机流量与供水抽水口径混同 |
| 2022_B | B1 | 100 | 65 | 100 | **年率 g 按月复利（index_error）**；**s_e 以正号进入发电上界（sign_error，短缺越大约束越松）**；H_min_power/H_tail/g_e 未声明 |

### 2.4 评分标签置换的披露

两名评委返回的分析标签与文件字母发生了置换（各批判读引用的原文短语可
唯一追溯到特定臂产物文本）。解盲采用**内容特征追溯**：每条 critique 引用
的机制方程/字段与 ARM 文件逐一比对后归位（如 2021_C 的 "log A_{t+1}(x) =
ρ·log A_t(x)+v·∇+w_t" 唯一属于 B1）。盲评本身的有效性不受影响（评委
评分时无臂知识）；置换发生在评委输出命名层，解盲由内容比对完成并全程
可审计。

## 3. 判读

1. **H2（迁移性）：n=3 全部支持**。B1 在三道未见题、三个 regime 上
   composite 全部严格高于 B0（+41.0 / +33.0 / +57.6）；分维度上
   structural 与 alignment 全面领先，mathematical 领先幅度最小。
2. **H3（结构性传导）✅**：三维同步（B1 无任何一维低于 MMA）。
3. **核心科学发现（三维拆分的价值）**：
   - **B0 的失败签名跨 regime 稳定**：math 60-90 尚可，structural/alignment
     崩塌（alignment 0-40）——"数学会做，题意承载失败"在三个题型全部复现；
   - **mathematical 是最平的维度**（三臂均值 73-82）：LLM 天然擅长数学
     语法的正确，真正的分界在"形式化完备性 + 题意承载"；
   - **B1 的优势集中在 alignment（100 全满）与 structural（100 全满）**，
     即 Model Specification + Constraint Completeness + Problem Alignment
     ——而不是模型选择（三臂的 selected_model 在数据题上高度重叠）。
4. **MMA 剖面**：83.9 均值，优化 regime 追至 83.3（与 B1 仅差 5）——其
   优化决策树（LP/加权和/帕累托/分层短缺）是强先验；弱点跨 regime 稳定：
   constraints 空置或工程边界缺失、部分对齐通道缺承载变量。
5. **盲评持续抓到 B1 真缺陷**（三轮累计 7 项）：年率按月复利、短缺符号
   松弛约束、5 个未声明参数——全部进入清单 v2。自评膨胀的教训第三次
   验证。

## 4. 局限

1. n=3 题仍属小样本；H2 的表述为"三个未见题全部支持"，统计性结论需
   扩到 ≥10 题；
2. 盲评评委与被评系统共享底层 LLM（不同会话、无臂知识）；评委输出
   标签置换需内容追溯解码（已披露）；
3. MMA 为提示词级操作化（非其 runtime 复刻）；
4. 产物为构造层（无代码执行验证），实验正确性属 P14。

## 5. P13-3C-R5 预注册（Expanded Benchmark，≥10 题，下一轮执行）

### 5.1 设计变更（相对 Round 1-2）

- **恢复三臂**：B0 / MMA / B1-F——消融已完成归因（Round 4），R5 的任务
  是验证既定 Full intervention 的泛化性，不重复消融（成本纪律）。
- **4×3+1 题型矩阵**：Mechanism 3 / Data 3 / Optimization 3 / Hybrid 1
  = 10 题（已有 2024_A、2021_C、2022_B 计入各 regime 首席）。
  **Hybrid 判据**：必须真实串联 ≥2 个 construction regime
  （data → mechanism → optimization 类），不是多模型拼盘。
- **difficulty control**：每题跑前生成 `question_profile`
  （id / regime / difficulty / subproblem_count / data_dependency /
  model_family / mechanism_depth / optimization_depth / ambiguity_level），
  **difficulty 在看到三臂结果之前锁定**；已有三题的 profile 标注为
  post-hoc（结果已见），不进入难度控制分析。
- **自评降级**：agent self-score 全面降级为 diagnostic only；主结果 =
  匿名产物 → 独立评委 → rubric score + critical defect log
  （severity / category / evidence）。

### 5.2 预注册假设

- **H5 Cross-regime generalization**：B1-F > B0 在 Mechanism / Data /
  Optimization / Hybrid 四 regime 分别成立。
- **H6 External baseline advantage**：B1-F > MMA 的 +10 分差在 ≥10 题上
  保持稳定（3 题现状：93.9 vs 83.9）。
- **H7 Dimension-specific effect**：Alignment 呈 B1 ≫ MMA > B0、
  Structural 呈 B1 > MMA > B0、Mathematical 差距最小——若在 10 题复现，
  则结论固化为"**B1 的优势不是数学计算能力，而是模型规格完整性与问题
  承载能力**"。

### 5.3 新增派生指标

Claim Coverage / Support Coverage / **Claim-Support Gap**（定义见 §4.7）
由盲评评委随 rubric 分一并输出。

### 5.4 统计计划

mean / median / per-question Δ / per-regime Δ / per-dimension Δ /
major defect count；三臂同题 = 天然 paired design，报告配对差值而非
独立样本比较；n≥10 后做 simple paired analysis（Wilcoxon signed-rank）。

## 6. P13-3D 预注册（Model → Paper Causal Transmission）

### 6.1 设计

三臂产物（B0 / MMA / B1-F）**冻结后**送入**完全相同的** Writer / 模板 /
检查器 / 数据 → 论文。Writer 禁止重新建模：Model Artifact 是唯一真源。

### 6.2 双指标

1. **Paper Quality**：数学正确、逻辑、完整性、结果、表达、结构
   （评委 rubric，盲评同协议）。
2. **Model Fidelity Gate**：论文 vs Artifact 逐项核对
   （variables / objective / constraints / assumptions）——论文中出现
   Artifact 没有的新变量/约束/目标/假设 = **Unauthorized Model
   Mutation**，单独记录（不计入 Paper Quality，作为 Writer 行为的独立
   仪表盘）。没有 Fidelity Gate，"好模型 → 好论文"的传导实验会被
   Writer 的暗中重建模污染。

### 6.3 核心问题

- **能力层**（P13-3C 已答）：干预是否提高 Model Construction？
- **产品层**（P13-3D 待答）：更好的 Model Construction 是否自然转化成
  更好的论文（Paper Conversion Efficiency）？若外部臂"模型弱、论文强"，
  则识别并吸收其 Model→Paper compiler。

## 7. 终局架构方向（Round 4 consolidation 确立）

MathModelAgent Modeler 强在"知道该往哪走"（决策树/EDA/方案规划），
我们的核心强在"走到之后把模型造完整"（主张-支持配对）。终局形态：

```text
MMA-style Planner（方法选型/规划）
        ↓
Our Model Construction Core（形式化/约束/对齐/传播）
        ↓
Formal Model → Experiment → Evidence
        ↓
Same Paper Writer → Final Paper
```

目标不是证明"我们全面更强"，而是**识别 pipeline 每个阶段最强的组件**。


## 8. P13-3C-R5 结果 — Controlled Cross-Question Validation（✅ 7 题三臂 21 artifact 全部盲评）

执行纪律：验证不创新（无新干预）；三臂固定；question_profile 先于 artifact 冻结
（10 题全部 pre_registered difficulty）；自评不参与；评委输出标签置换再次发生，
按内容特征追溯解盲（全程可审计）。

### 8.1 首表：分维度（7 题 mean，Composite 垫后）

| Arm | Structural | Mathematical | Alignment | Claim Cov | Support Cov | Composite(mean) |
|---|---|---|---|---|---|---|
| B0 | 28.4 | **73.6** | 9.3 | 9.3 | 14.3 | **37.1** |
| MMA | 72.9 | 59.3 | 76.2 | 76.2 | 41.7 | **69.5** |
| B1-F | **94.3** | 71.4 | **92.9** | 92.9 | 55.9 | **86.2** |

（逐题 composite：B0 = 43.3/38.3/63.7/34.4/23.3/30.0/26.4；
MMA = 46.0/35.0/80.7/86.7/73.3/81.7/82.8；B1 = 81.7/86.7/96.7/95.0/85.0/**60.0**/98.3）

### 8.2 假设判定

- **H5 ✅（7/7）**：B1-F > B0 在全部 7 道未见题成立，跨 4 regime（含 hybrid）。
- **H6 部分（6/7）**：B1-F > MMA 在 6/7 成立（mean 差 +16.7，比 3 题时的 +10 扩大）。
  **例外：2025_B（可持续旅游）MMA 81.7 > B1 60**——见 8.3。
- **H7 ✅（最强形式）**：Mathematical 维 B1（71.4）**低于 B0（73.6）**、三臂几乎无差
  ——B1 的优势不是数学计算能力，而是 Structural（94.3 vs 28.4）与 Alignment
  （92.9 vs 9.3）。与你的预判完全一致且更强。

### 8.3 2025_B 失利剖析（R5 最重要的诚实读数）

盲评在 B1-F 的 2025_B 产物中抓到**真实符号错误**：需求模型
"(p̄/p_eff)^{e_p} 配 e_p<0" → 价格上升需求反增（sign_error），叠加多个未声明
参数（V0/p̄/shift/Foot_max）→ math 50。而 MMA 臂恰好强在"优化-约束显式结构"
（其 Modeler prompt 的决策树对本题型是强先验）→ 81.7。

结论：**清单干预不是万能护身符**——它系统性地修复"结构/对齐"类失败，但不
保证消除所有数学错误；在"优化-约束显式化"这类 MMA 决策树已覆盖的题型上，
MMA 臂可以反超。**这不是清单失败，是能力剖面互补的证据。**

### 8.4 Claim×Support 平面（7 题均值）

```text
Support Cov
 100 │
     │              ● B1(55.9)
  50 │       ● MMA(41.7)
     │  ● B0(14.3)
   0 └──────────────────→ Claim Cov
       9.3      76.2    92.9
```

三臂在 7 题上保持了 Pilot 预测的空间关系（B0 低主张/中支持、MMA 中-中、
B1 高主张/高支持）；**B1-F 的 Support Coverage（55.9）仍未达满**——
残差缺口 = 逐臂未声明参数/符号类缺陷的总和，即清单的下一步靶点。

### 8.5 缺陷计数（R5 major 缺陷/产物，均值）

B0 ≈ 3.6、MMA ≈ 2.4、B1 ≈ 2.3——B1 与 MMA 的缺陷数接近，但 B1 的缺陷
集中在"参数声明/量纲"类（可机械核查），MMA 集中在"约束空置/对齐缺承载"
类（需人工判断）。P13-3D 的 Fidelity Gate 应优先机械化前一类。

## 9. P13-3 收口判定

- H5/H7 成立、H6 6/7 成立且均值差扩大 → **P13-3C 通过，正式收口**。
- 不再继续优化 Model Construction checklist（收益递减；2025_B 失利指向
  的是"优化-约束显式化"先验，属 Planner 层问题，非 Construction 层）。
- 下一阶段：**P13-3D Model → Paper**（三臂产物冻结 → 同一 Writer →
  Paper Quality + Model Fidelity Gate / Unauthorized Model Mutation）。
- 保留资产：MODEL_ARTIFACT v1 schema、10 题 profile（difficulty 前置）、
  盲评协议（内容追溯解盲）、Claim/Support/Gap 指标、缺陷计数仪表盘。
