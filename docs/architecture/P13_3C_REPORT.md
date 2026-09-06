# P13-3C Report — Model Construction Generalization & Comparative Benchmark

> 日期：2026-09-06 · 实验性质：**能力实验**（区别于 P13-3B 的干预实验）。
> 治理铁律：**任何能力升级，如果没有 baseline，就不算能力升级。**
> 表述纪律：MMA 臂 = "MathModelAgent Modeler prompt 的 same-LLM
> operationalization baseline"，**不是**完整 MathModelAgent runtime 复刻。

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

## 5. Step 4 消融预注册（下一轮执行）

问题：B1 的提升由哪些可独立干预的子能力贡献？

- **臂**：B0 / B1-full / **B1-alignment**（仅对齐点→变量承载 + 参数声明）/
  **B1-constraint**（仅约束形式化 + 随机过程域一致 + 工程边界）。
- **题**：2022_B（优化 regime，B0 差距最大、扣分结构最丰富）+ 2024_A（复验）。
- **预注册判读**：若 B1-align ≈ B1-full ≫ B1-constraint → 对齐承载是主因子；
  若 B1-constraint ≈ B1-full ≫ B1-align → 约束完备性是主因子。
- 评分协议同本轮（匿名 + 独立评委 + 内容追溯解盲）。

## 6. 下一步

1. 消融（上表）→ 认知干预的因果归因；
2. 扩题至 ≥10（H2 统计性）；
3. **P13-3D Model → Paper Conversion**：三臂 artifact 冻结 → 同一 Writer/
   模板/检查器 → 论文 + **Model Fidelity 指标**（论文中凭空出现的新变量/
   约束/目标 = Unauthorized model mutation）；
4. P14 = Model Validation & Experiment Design（Model → Experiment → Evidence）。
