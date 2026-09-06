# Capability Roadmap P13–P17（能力路线图）

> 定位：这是 **Capability Roadmap**，不是 Runtime Roadmap——每个阶段的
> exit criteria 是**基线指标 Δ**，不是交付物清单。下层（Research Runtime /
> Guardrails）已冻结；本路线图全部投入 Agent Brain 与测量。
> 治理规则见 `THREE_LAYER_ARCHITECTURE.md`（三问门禁 + Δscore 判据）。

## 0. 研发闭环（自 P13 起唯一的工作方式）

> **治理铁律（P13-3C 起）：任何能力升级，如果没有 baseline，就不算能力
> 升级。** 干预实验（同题前后对照，如 P13-3B）与能力实验（跨题迁移 +
> 外部基线对照，如 P13-3C）是两种不同的证明，治理上分开锁死。

```text
BASELINE（首跑分数，预期很低——这正是价值）
   → 针对短板修改 Brain（指令 / 知识卡 / 策略）
   → 再跑同一题集
   → Δscore（哪个指标提升多少）
   → 有 Δ 才算能力进步；无 Δ 的改动回滚或存档
```

首跑的意义不是分数高，而是让"这个系统到底会不会做数学建模题"第一次变得
可测量、可比较、可归因。

### 实验矩阵（冻结，能力层 + 产品层分离）

| Experiment | Question | Baseline | Intervention | External |
|---|---|---|---|---|
| E1 | 已见题 | B0 | B1 | — |
| E2 | 未见题 | B0 | B1 | — |
| E3 | 未见题 | B0 | MMA（MathModelAgent） | ✓ |
| E4 | 未见题 | MMA | B1 | ✓ |
| E5 | 未见题 | 同 Model Artifact | 同 Writer | ✓（P13-3D） |

能力层结论：干预是否提高 Model Construction；产品层结论（P13-3D）：
更好的 Model Construction 是否转化成更好的论文（Paper Conversion
Efficiency = 同一 Writer 下模型分 → 论文分的转化率）。

## 1. 八项能力指标（可计算定义）

全部指标 0–100%；输入缺失时如实记 `n/a`（不臆造分数）。计算实现：
`core/tools/evaluation/e2e_metrics.py`（确定性，零 LLM）；题集与金标准：
MMBench 本地语料（111 题，全文+数据）+ CUMCM rubric 种子。

| # | 指标 | 可计算定义 | 金标准来源 |
|---|---|---|---|
| 1 | decomposition 子问题覆盖率 | 产出的问题分解（DAG questions）命中金标准子问题集的比例；命中 = 子问题语义对齐（题目要求项逐条对照） | CUMCM rubric dimensions（q1..qn）；MMBench `problem_requirement` 分解项 |
| 2 | method selection 方法正确率 | 选出的方法候选（top-3）命中金标准方法集的比例；方法名按方法卡家族归一 | CUMCM-Bench.json `core_methods`（32 题现成）；rubric 评审要点中的方法方向 |
| 3 | model correctness 数学正确性 | 评委 rubric 中"模型/公式/推导"维度按扣分制折算的得分率；有数值 GT 时叠加关键结果数值命中率 | rubric assessment_points + reference_results |
| 4 | experiment validity 实验有效性 | 确定性复合：对照基线存在 + 灵敏度分析存在（result tags）+ 多次运行（seed 42, ≥5 次均值±std）+ 实验确有检验对应 claim（Evidence Gate 通过率） | Registry/Graph 产物（tags、runs、coverage） |
| 5 | validation reliability 结论可靠性 | 确定性复合：fact_check 通过率 + 论文↔代码数值一致（consistency_checker）+ 引用零捏造（citation_check）+ 护栏全绿 | 校验工具输出 |
| 6 | innovation 新颖且可验证 | 声明的创新点数量中，有对应验证实验支撑的比例（创新模式卡消费 + experiment 存在）；叠加 rubric 创新维度得分 | decision log knowledge_refs + Registry |
| 7 | writing completeness 论文完整度 | final-validator 结构完整率（章节/图表/公式/参考文献达 env 阈值）+ 五维评分链 reader/judge 维得分率 | `paper/main.tex` + score_compute 链 |
| 8 | end-to-end 最终成绩 | 评委 rubric 总分（100 分制）；MMBench 侧用其自带 evaluation 口径。单一汇总数字 | bench rubric / MMBench evaluation |

汇总口径：题集内各指标取均值；报告同时给 per-problem 明细（`bench e2e report`）。

## 2. 阶段

### P13 — 数学推理基线（压缩为 P13-0..5，实验先行）

> 定位修正（2026-09-06，P13-1 后）：**end-to-end 是最终指标，不是开发指标**；
> 开发指标 = 7 项分指标，每个改动只认"它让哪个分指标动了多少"。
> 新增 **Measurement Integrity**（provenance-based realization v1，
> measurement metadata，非能力分数、不并入均值）——回答"分数有多少由
> agent 真实产物支撑"（见 `e2e_metrics.py` 与 BASELINE_REPORT §2）。

- **P13-0 Measurement / Baseline（✅ 已完成）**：`bench e2e` + 八项指标 +
  2000C 真实解题基线（`BASELINE_REPORT.md`）+ Measurement Integrity 仪表盘。
- **P13-1 Problem→Method 接口（✅ 已完成，v2 最终版）**：`problem_profile`
  DTO（六冻结键+note，非本体）+ `features_for()` + A/B/C 消融。口径钉死为
  top-3 shortlist GT hit 后官方结果 **A=0 / B=100 / C=100（top-1 仍 0）**：
  接口修复有效、全局画像已够用、失败分支锁定"有候选但排序错"。详见
  `P13_1_REPORT.md`。
- **P13-2 Retriever 打分再平衡（✅ 已完成）**：守卫式影子评分器消融
  （`ranking_ablation.py`）定位唯一断点 = 类型命中 +3 被质量维度净抵消；
  落地 w_sem 3→6（例外已登记），修复 `_method_hit` 连写 token 归一化伪影。
  管线集成验证：2000C top-1 0→100、2023C top-1 100、评价类反向检查零回退；
  **B 明显 > C**（top-1 100 vs 25）——per-question 画像不值得复杂化。
  详见 `P13_2_REPORT.md`。
- **P13-3 Model Construction（进行中，首测 ✅）**：核心问题——**选对
  方法以后，Agent 能不能把数学模型正确地建立出来**。三个独立测量：
  1. **Structural correctness**：变量/参数/目标函数/约束/状态转移是否完整
     且相互一致；
  2. **Mathematical correctness**：推导错误、量纲/边界/符号/索引问题
     （错误分类学扣分制）；
  3. **Problem alignment**：模型是否真的回答题目——"数学上正确但解决了
     另一个问题"是数模 Agent 最典型的失败，此项独立测量。
  首测（2000C，测量仪 `model_construction.py` + 预注册 rubric
  `mc_2000C.json`）：structural 80 / mathematical 55 / alignment 100 /
  composite 78.3——短板分布"结构好、数学弱"被三维拆分暴露。详见
  `P13_3_REPORT.md`。
  **禁令（P13-3 生效）**：不碰 Cross-question synthesis / 新 Relation /
  新 IR / 新 Validator / 新 Artifact / Agent 数量扩张——P13-3 只在
  Brain / Knowledge / Evaluation 层工作。
- **P13-3C Generalization & Comparative Benchmark（✅ 3 题三臂完成）**：
  B0/MMA/B1 × 2024_A(机理)/2021_C(数据)/2022_B(优化) = 9 份 MODEL_ARTIFACT
  全部匿名盲评。**B1 mean 93.9 > MMA 83.9 > B0 50.0，三 regime 全胜**
  （H2 n=3 支持）；分维度：structural B1 满分、alignment B1 满分、
  **mathematical 最平（B1 81.7 / B0 76.7 / MMA 73.3）**；B0 的失败签名
  跨 regime 稳定（math 尚可 60-90，alignment 0-40 崩塌）。盲评三轮累计
  抓到 B1 七项真缺陷（全部入清单 v2）。消融（B1-align/B1-constraint）
  已预注册。详见 `P13_3C_REPORT.md`。
- **P13-3D Model → Paper Conversion（待 P13-3C ≥3 题）**：三臂模型产物 →
  同一 Writer/模板/检查器 → 论文，测 Paper Conversion Efficiency（模型分 →
  论文分的转化率）；若外部系统模型弱但论文强，则识别并吸收其
  Model→Paper compiler。
- **P13-4 Real Experiment（P14，定位修正）**：**Model → Evidence**——模型
  → 应该测什么 → 实验设计 → 模拟/优化/统计检验 → 证据 → 证据是否支持
  模型 → 模型修正。对比基线 = "模型 → 直接跑实验"。
- **P13-5 Re-run Benchmark**：同题集复测 → Δscore；exit criteria = ≥5 题
  （跨 ≥2 年）可复现基线且至少一项指标 +10 个百分点。

**纪律（P13-1 确立）**：实验结果为 0 时本轮就地停止，不为让 Δ 变正继续
修改；只允许增加"题目语义 → 已有方法选择器"的信息流，不允许增加新的
认知层。若出现"架构缺口"，先过三问门禁——通常答案是改 Brain 指令/知识
或修真实 bug，**绝不为此开新 P 阶段**。

### P14 — 模型构建智能（Model Construction）

- Scope：假设生成质量（assumption 四维评分的真实使用）、公式推导链完整性
  （model-builder / dag-builder 指令强化）、候选模型真实比较
  （candidate arena 消费率）。
- Exit criteria：`model correctness` 相对基线 Δ>0，且 `decomposition`
  不回退（回退即回滚）。

### P15 — 实验智能（Experiment Intelligence）

- Scope：实验设计质量（ExperimentPlanner 的 checks 覆盖率）、参数选择与
  多初始点、失败恢复（failure memory 写入→消费闭环）、结果解释忠实度。
- Exit criteria：`experiment validity` Δ>0；failure memory 至少新增 3 条
  真实失败案例且被后续 run 消费。

### P16 — 竞赛策略（Competition Strategy）

- Scope：时间预算分配（time_budget）、取舍规则（何时放弃一个子问题）、
  创新点寻找（patterns + EXAMINER-TRACKER 消费）、按题型调权
  （weight_profiles）。
- Exit criteria：`end-to-end` Δ>0（策略改动只认总分）；`innovation` Δ>0。

### P17 — 全面测评（Full Evaluation）

- Scope：多题全量跑分（MMBench 111 题全量 + CUMCM 种子扩充）、跨阶段
  Δ 对比、回归纪律（冻结层测试全绿 + 八项指标无一回退）。
- Exit criteria：≥2 个完整测评轮次；形成"每轮改动 → Δ"台账；
  八项指标成为唯一进度度量（测试数量仅守冻结层）。

## 3. 与冻结层的边界

P13–P17 **不新增** Runtime 契约 / Guardrails 语义层。若能力改进疑似需要
动冻结层：先过三问门禁——通常答案是"改 Brain 指令或知识卡"，而不是
"加一层"；确属真实需求的例外按 `THREE_LAYER_ARCHITECTURE.md` §3 流程。
