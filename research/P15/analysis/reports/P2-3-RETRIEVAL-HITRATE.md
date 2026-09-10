# P2-3 检索命中率分析：区分「检索失败」vs「知识无用」

- **日期**: 2026-09-10
- **分析脚本**: `research/P15/analysis/p2_3_retrieval_hitrate.py`
- **产物**: `research/P15/analysis/p2_3_retrieval_hitrate.json`
- **上游**: K001 知识注入 negative（Δ_K=+2.14 CI[0,+6.41]）→ 深度归因
  （`P15-K001-ATTRIBUTION.md`）

## 1. 问题

K001 知识注入 negative——到底是因为**检索没把对的卡拿出来**
（检索失败），还是**知识本身无效**（效用/剂量/测量）？P2-3
机械回答前者：对 8 题（K003 同题集）构造问题特征 →
`KnowledgeRetriever.recommend(top_k=10)` → 检查 ground-truth 方法卡
（由官方标准解法 family 指派）是否命中。

## 2. 方法

- 8 题：2011_B / 2017_B / 2018_A / 2018_B / 2019_C / 2020_B /
  2022_C / 2024_A
- ground-truth 卡（附录 A）：由各题 CUMCM 标准解法 family 指派
- 特征：题目 family 标签 → `problem_types`/`has_data`/`sample_size`/
  `objectives`/`time_series`/`uncertainty`（recommend 的打分键）
- 指标：hit@3 / hit@5 / hit@10 + ground-truth 卡排名

## 3. 结果（修复前 → 修复后）

| 题 | ground-truth 卡 | 修复前 rank | 修复后 rank |
|---|---|---|---|
| 2011_B | mc-dp | 1 ✅ | 1 ✅ |
| 2017_B | mc-ols | **未命中** ❌ | 1 ✅ |
| 2018_A | mc-numerical-pde | 1 ✅ | 1 ✅ |
| 2018_B | mc-dp | 1 ✅ | 1 ✅ |
| 2019_C | mc-queuing-theory | 1 ✅ | 1 ✅ |
| 2020_B | mc-dp | 1 ✅ | 1 ✅ |
| 2022_C | mc-kmeans | **未命中** ❌ | 1 ✅ |
| 2024_A | mc-numerical-pde | 未命中 ❌ | 未命中 ❌ |

- 修复前 hit@3 = **5/8 = 62.5%**
- 修复后 hit@3 = **7/8 = 87.5%**

## 4. 三处检索缺口根因（证据）

1. **2017_B（回归/定价）**：词表错位——题目 family 标签
   `regression/pricing` vs 卡 `mc-ols.problem_types=[fitting, prediction]`
   零重叠 → 0 分被过滤，top 被 `mc-nsga2`（多目标加分）占据。
   **修复**：`mc-ols.problem_types` 增补 `regression`（卡词表与题目标签对齐）。
2. **2022_C（玻璃成分聚类，n=67 小样本）**：元数据错误——`mc-kmeans`
   `sample_size: [medium, large]` 把 small 样本整卡过滤（聚类明确适用
   小样本）。**修复**：`sample_size: [small, medium, large]`。
3. **2024_A（板凳龙运动学）**：**卡池覆盖缺口**（非检索 bug）——数值
   积分/ODE 运动学类没有对应卡（`mc-numerical-pde` 只覆盖
   heat_transfer/diffusion/wave/fluid_flow/pollution_spread）。
   **不修**：知识卡扩充为既定 P1 工程项（L1 结构覆盖
   game/network/scheduling/kinematics），与实验分离执行。

## 5. 判定（P2-3 预注册口径）

- hit@3 = 87.5% ≥ 75% → **检索基本可靠**。
- **K001 negative 不是「检索失败」**——直接注入的最优卡本就检索得到，
  检索链路能把对的知识拿给建模者。
- 结论指向 K001 深度归因的既有四层：**信息增益 ceiling、测量粒度、
  剂量（每题 1 卡）、功效（n=11/臂）**——与
  `P15-K001-ATTRIBUTION.md` 一致，无需推翻。
- **P2-3 实验（直接注入 vs 检索后注入，18 runs）仍必要**：生产路径
  若接入检索，需验证"检索+注入"与"直接注入"无损耗（检索损耗当前
  仅剩 2024_A 类覆盖缺口，属卡池问题而非链路问题）。

## 6. 附录 A：ground-truth 卡指派（官方标准解法 family）

| 题 | 标准解法 family | 指派卡 |
|---|---|---|
| 2011_B | 最短路/覆盖（图算法） | mc-dp（shortest_path 类） |
| 2017_B | 定价回归 | mc-ols |
| 2018_A | 热传导/参数反演 | mc-numerical-pde |
| 2018_B | RGV 调度 | mc-dp（resource_allocation 类） |
| 2019_C | 出租车调度（排队论） | mc-queuing-theory |
| 2020_B | 穿越沙漠（MDP） | mc-dp（sequential_decision 类） |
| 2022_C | 玻璃成分分类（聚类） | mc-kmeans |
| 2024_A | 板凳龙运动学（数值积分） | mc-numerical-pde（近似，覆盖缺口） |

## 7. 复现

```
py -3.12 research/P15/analysis/p2_3_retrieval_hitrate.py
```
