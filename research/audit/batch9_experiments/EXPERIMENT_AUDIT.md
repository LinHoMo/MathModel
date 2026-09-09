# P15 实验体系审计（audit Batch 9）

> 日期：2026-09-09 ｜ 审计人：MainAgent（audit Batch 9）｜ 范围：K001 / K002 / K003 / P1
> 立场：**实验有效性 ≠ 实验完成**；每个实验按 Construct / Measurement / Execution /
> Statistical / Interpretation 五维审计，负面结论按 pre-registered 决策门解读。

## 1. 实验矩阵

| 实验 | 测什么（Construct） | 设计与终点 | 状态 | 主结果 |
|---|---|---|---|---|
| **P15-K001** | Knowledge 注入（知识卡 vs Sham vs 空白） | 2×2×rep，55 runs（主检验 3 题×5 臂×3 rep + 泛化 2 题×5 臂×1 rep）；主终点 MCQ_primary（L2 composite） | CLOSED | Δ_K=+2.14 CI[+0.00,+6.41] → **negative**；Sham=+3.42 跨 0 |
| **P15-K002** | Model Representation（F/S/S+V 三臂） | 主检验 6 题×3 臂×3 rep + 泛化 2 题；主终点 MCQ（L2）+ VAL（L4 新增） | CLOSED | RQ1 S−F(MCQ)=**−4.85** CI[−7.98,−2.22] → **NEGATIVE**；SV−F(VAL)=+4.81 POSITIVE |
| **P15-K003** | Executed Representation（F/S/SV，构造+执行一体化） | 66 runs（主检验 6 题×3 臂×3 rep + 泛化 2 题×3 臂×2 rep）；L3 判据=真实执行事实 | **FROZEN**（生成中） | 待执行 |
| **P1** | Model Construction Loop 能力本体（非实验） | VS-001 垂直切片 M1→FAIL→M2→PASS + Replay；M3 竞技场；M4 知识引导 | 闭环 | 7/7 验收 PASS |

## 2. Construct validity（测的是声称的东西吗？）

- **K001**：测"建模知识注入 → Model Construction Quality"——终点 L2 composite 由
  独立盲评按 rubric v1.0 打分；Sham 臂控制"额外上下文"混淆。**成立**，但
  RQ5（method-family 识别）的 `allowed_model_families` 与生成侧 `model_family.primary`
  自由命名词表错位（如 dynamic_programming vs discrete_recurrence）→ **construct 被
  词表污染**，已判定为 tertiary measurement limitation，不影响主终点 MCQ（K001 报告 §3）。
- **K002**：测"结构化表示 → 建模质量"。**已知 construct 混淆**：S 臂强制 MODEL_IR
  暴露"无执行证据"，F 臂自由文本可叙述性声称 → L3 执行层系统性不对称
  （K002 报告：敏感性 C 仅保留 L2+L4 后 Δ=−1.94 CI[−3.53,−0.34] 仍 NEGATIVE，
  但幅度缩小——确认 L3 地板是 S 臂负分来源之一）。K003 的 G1 修订（v1.2 L3 判据=
  真实执行事实）正是对该 construct 缺陷的修正。
- **K003**：测"执行一体化下的表示效应"——三臂执行地位平等，L3 只看真实
  ExecutionResult/VR。**construct 修复完成**（G1 PASS）。

## 3. Measurement validity（测准了吗？）

| 维度 | K001 | K002 | K003 |
|---|---|---|---|
| Ceiling/Floor | 2020_B 13/15 满分（ceiling）；2019_C 全臂恒定 87.18（**零区分度 block**） | L2 结构维度饱和（K002 预检发现）→ v1.1 重评恢复区分度 | G2 校准 κ=0.712（优于 K002 的 0.4345） |
| Evaluator bias | 3 独立 evaluator，evaluator 与 generator 隔离；evaluator.model=doubao-pro | 3 evaluator；锚定澄清后 κ=0.4345，低 κ 维度敏感性 B 剔除 | 3 evaluator；锚定澄清 |
| Formatting confound | 各臂差异只在参考资料段（bundles 结构统一） | **存在**：S/S+V 臂天然像"漂亮 JSON" | 三臂执行地位平等，消除 |
| Vocabulary | **失败**（RQ5 词表错位） | 复用 K002 frozen 18 canonical 词表（G3 PASS，别名回归 25 用例） | 复用同一 frozen 词表 |
| Power | **受限**：n=11/臂，CI 宽（Δ_K 0~6.41 无法区分小效应/中等/噪声）；per-block 实际有效 block 2/3 | rep=3，块内均值 sd=2.667 | **如实声明**：power≥0.8 需 Δ≥3.7；区分度预检后不支持 → 不做事后提 rep（G5） |
| Endpoint 定义 | MCQ_primary=L2.1/2.2/2.4/2.5/2.6(权重3)/2.7，13 分 | MCQ（L2）+ VAL（L4） | MCQ + VAL + L3 执行事实 |

**关键结论**：K001/K002 都出现过测量层问题（词表错位 / 格式不对称），且都被
**如实记录、不掩盖、不影响负面结论解读**——这本身符合"measurement failure ≠
capability failure"治理原则。K003 把前两轮全部测量教训固化为 Gate（G1-G5）。

## 4. Execution validity（测量的是真实执行吗？）

- **历史 P0**：K003 生成阶段曾发现 generator 可直接制造 execution_result
  （`{status:success, outputs:...}` 由 Agent 写入）——**violates generator≠executor 边界**。
- **治理闭环（Batch 4，已提交）**：
  1. `research/P15/experiments/P15-K003/scripts/execution_writer.py` = execution_result
     唯一写入路径（rebuild_all 幂等）；`k003_formal_runner` 委托 writer；
  2. `make_submission_id` 改 uuid4（旧 sha256(f"{problem}_{arm}_seed{s}")[:12] 可暴力
     反推分组——已不可链接）；
  3. registry.create 对 execution_result 做 schema 实例校验 + status 枚举门禁
     （Batch 1 FIX：success 必须 code_hash≥16 且与 code 一致、outputs 非空）。
- **现状**：generator 无 execution_result 写权限；ExecutionResult.status 只来自真实
  subprocess returncode。**Execution validity = 成立**（K003 G4 exec 1.00 全 PASS）。

## 5. Statistical validity

- K001：配对分析 Δ_K=+2.14 CI[+0.00,+6.41]——CI 下界恰触 0，按预注册门
  **negative result**（不是"无效应"，是"未达证明标准"）；Sham=+3.42 跨 0 →
  "更多上下文处理效应"与"知识内容效应"无法分离。
- K002：RQ1 Δ=−4.85 CI 上界 −2.22 < 0 → 显著负，NEGATIVE 成立；敏感性地基（剔除
  低 κ 维度）Δ=−6.60 更强——结论稳健。
- K003：功效边界**预先声明**（Δ≥3.7 才 power≥0.8），区分度预检后观测效应不支持
  就如实报告低功效，无设计外调参——符合"不做事后调 threshold"铁律。

## 6. Interpretation audit（负面结论怎么读？）

| 表述 | 允许？ | 依据 |
|---|---|---|
| "知识卡无效" | ❌ 禁止 | 须区分 Ontology / Utilization / Causal Effect / Measurement Validity / Power（K001-ATTRIBUTION.md） |
| "K001 Δ_K 未达证明标准（negative）" | ✅ | CI 下界 +0.00 ≤ 0，pre-registered gate |
| "更多上下文（Sham）可能比知识内容更有增益，不可区分" | ✅ | Sham>K 且 CI 跨 0 |
| "K002 强制结构化表示在主检验上显著降低 MCQ" | ✅ | Δ=−4.85 CI[−7.98,−2.22] |
| "K002 的 S 臂低分部分来自格式不对称（测量构造）" | ✅ | 敏感性 C 证实 L3 地板 |
| "K003 会解决表示实验的执行证据混淆" | ✅（设计声明，待执行证实） | G1 v1.2 判据切换 |

## 7. 结论与遗留

- **已证实的负面结论**：K001 knowledge 效应未达证明标准；K002 RQ1 结构化表示
  未带来 MCQ 提升（且存在测量构造混淆）——**两个负面结果按预注册门如实落定，
  不因负面而返工、不推 P15.2**。
- **实验体系净改进**：K003 是前两轮教训的固化产物（词表 frozen / L3 执行判据 /
  功效边界 / execution 写入治理）——**Measurement validity 逐轮增强**，这是 P15
  系列本身最重要的实验方法学产出。
- **遗留**：K003 66 runs 执行中（生成+盲评+配对分析未完成）；三实验对比表与
  P16 决策在 K003 CLOSED 后落定；K001 2 个 FAIL run（batch0 claude Q1-only）作为
  已知生成侧缺陷记录在案，不追溯重跑（冻结协议一致性）。
