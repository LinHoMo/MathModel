# Modeling Knowledge Base Quality Baseline — 知识库质量分层审计

> 定位：P15-K001 negative result 归因的配套证据——回答"知识库本身的质量是否已达建模知识标准"。
> 数据：`core/knowledge/methods/cards/` 全量 19 卡字段结构扫描（`research/P15/analysis/card_quality_scan.json`）。
> 日期：2026-09-09

---

## 1. 全量分层结果

| 层级 | 标准 | 卡 | 数量 |
|---|---|---|---|
| **Tier1 — 完整建模知识** | mechanism（核心机理）+ structure_signals（结构信号）+ formulations（数学形式）+ solvers（求解层） | mc-dp、mc-numerical-pde、mc-queuing-theory | **3** |
| Tier2 — 有机理无结构信号 | mechanism 但缺 structure_signals | （无） | 0 |
| **Tier3 — 约束/风险/验证骨架** | 有 requires/risks/validation/anti_patterns/known_failures，**缺 mechanism/formulations/solvers/structure_signals** | mc-ahp、mc-arima、mc-entropy-weight、mc-fuzzy-evaluation、mc-ga、mc-grey-gm11、mc-kmeans、mc-lstm、mc-monte-carlo、mc-nsga2、mc-ols、mc-pca、mc-pso、mc-sa、mc-topsis、mc-xgboost | **16** |

（16 张 Tier3 卡均含 P8 决策字段：objective_types/applicability/evidence_requirements/costs/robustness 等——作为"选择决策辅助"可用，但作为"建模知识"不完整。）

---

## 2. 关键结论

### 2.1 P15-K001 注入的是知识库中质量最优的 3 张卡
主检验三题（2020_B/2018_A/2019_C）的匹配卡恰好是 3 张 Tier1 卡。**即使注入最高质量知识仍得 negative result**，说明当前瓶颈不在"知识卡质量不足"这一单因素上（排除"注入的是劣质卡"的解释）。

### 2.2 但 Tier1 卡的信息仍可能是 LLM 已内化的
Tier1 与 Tier3 的核心差异是 mechanism/structure_signals——即"**什么结构使该方法成立**"。这类知识恰恰是 LLM 预训练中大量接触的内容（DP 的 Bellman 原理、PDE 的守恒律）。归因 2.1（信息增益 ceiling）与本次扫描互相印证：**知识卡显式化的内容 = LLM 参数中已有的内容**。

### 2.3 真正的知识缺口可能不在这 19 卡覆盖的方法族
本库覆盖的方法族（DP/PDE/Queueing/GA/TOPSIS/回归/聚类…）都是"经典方法"。而知识库审计（knowledge_calibration）曾指出 L1 骨架缺 competition/game、network/traffic、scheduling 等结构。**知识库的"结构覆盖"缺口（problem structure 维度）比"方法卡字段完整性"缺口更实质**。

---

## 3. 升级路线（不盲目扩卡）

| 动作 | 依据 | 优先级 |
|---|---|---|
| 16 张 Tier3 卡补 mechanism/formulations/solvers/structure_signals | 对齐 Tier1 标准，使"建模知识"定位在库内一致 | P1（可在下一轮实验后做，避免与实验混淆） |
| L1 结构覆盖扩展（game/network/scheduling） | knowledge_calibration 审计缺口 | P1（需先过 Architecture Gate，见 knowledge_calibration/ARCHITECTURE_GATE_REPORT.md） |
| 知识卡 → MODEL_IR 的结构化映射 | 卡是文本，注入后自由吸收；缺少"卡字段 → MODEL_IR 字段"的机械映射 | **P0（直接关联下一轮 Representation 实验）** |

---

## 4. 对下一轮实验设计的含义

知识库质量扫描强化了归因结论：**下一轮不应以"更多/更好知识文本"为主效应**，而应转向：
1. **Representation effect**：强制结构化 MODEL_IR（schema 约束 + 知识字段映射）vs 自由文本——测"标准化表达"本身
2. **结构覆盖效应**：补齐 L1 结构（game/network/scheduling）后测"结构识别"是否提升
3. 知识卡升级作为**平行工程项**（不与实验混为因果证据）
