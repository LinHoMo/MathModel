# P13-2 Report — Retriever Ranking 修正实验（已收口）

> 日期：2026-09-06 · 原则：**不问"怎样让 Monte Carlo 排第一"，问"当前 ranking
> 为什么系统性地把语义匹配更强的方法压下去"**。不针对 2000C 手调。

## 1. 方法

1. **排序管线完整拆解**（守卫式影子评分器 `ranking_ablation.py`）：完整复刻
   `recommend() + _capability_match` 打分路径；**守卫 = 影子基线必须与真实
   retriever 全 case 逐卡一致，否则拒绝运行**。
2. **先验变体**（实验前注册）：语义证据 ×2（w_sem 3→6）/ 适配基线压平
   (20+4n,cap40 → 10+2n,cap20) / 质量维度减半 / 组合。
3. **评价**：2 道独立题（2000C 大象 / 2023C Wordle，GT 均于实验前预注册）
   + 评价类反向检查（AHP/TOPSIS 必须保持 top-1）。

## 2. 发现（按失败定位漏斗）

| 层 | 结果 |
|---|---|
| Profile → Runtime | ✅ 画像进入检索器（排序随语义改变） |
| semantic recall | ✅ 语义正确卡进入 top-3（P13-1 已证） |
| **ranking** | ❌ **唯一断点**：类型命中 +3 被质量维度净抵消（MC +9 vs −16） |
| GT canonicalization | ❌→✅ "time series"（带空格）永不命中 `classical_timeseries`
（连写）——`_method_hit` 增加紧凑匹配（统一规则，非单题特判）修复 |

## 3. 消融结果（影子评分器，守卫通过）

| case | V0 落地 w6 | V1 旧 w3 | V2 压平 w6 | V3 质量减半 w6 |
|---|---|---|---|---|
| 2000C top-1 | **mc-monte-carlo ✅** | mc-topsis ❌ | mc-monte-carlo ✅ | mc-monte-carlo ✅ |
| 2023C top-1 | **mc-grey-gm11 ✅** | mc-grey-gm11 ✅ | ✅ | ✅ |
| 反向检查（评价类） | **mc-ahp ✅** | mc-ahp ✅ | ✅ | ✅ |

## 4. 落地（最小 Runtime 例外）

`retriever.py`：类型命中权重 **+3 → +6**（语义证据 ×2），docstring 与
THREE_LAYER §3 例外登记。**零测试回归**（758 passed）；2000C 全局画像下
score 结构：MC fit 41(+18) > TOPSIS 33(+0)。

## 5. 管线集成验证（新权重，真实 pipeline，top-3 / top-1 口径）

| 条件 | top-3 | **top-1** | distinct_chosen |
|---|---|---|---|
| 2000C A 无画像 | 0 | 0 | 1（TOPSIS）——无语义即无召回，符合预期 |
| 2000C B 全局画像 | 100 | **100**（4/4 MC） | 1 |
| 2000C C 逐题画像 | 100 | **25** | 2 |
| 2023C 全局画像 | 100 | **100**（grey-gm11，classical_timeseries 族） | 1 |

**重要副产物**：B 明显 > C（top-1 100 vs 25）——逐题画像的类型集更窄，
语义证据反而更少（MC 2 类命中 vs 全局 3 类）。**per-question 画像不值得
复杂化**（P13-1 判定矩阵 "B明显>C" 分支坐实，且给出了机理）。

## 6. 退出判定（任务书退出条件）

> Ranking 修正能让语义正确的方法稳定进入 top-1 ✅（两道独立题 top-1 100%，
> 反向检查通过，零回退）。**0 → 100：方向有效，进入 P13-3 Model Construction。**

不进入下一轮的项：不加权重（一次到位，未叠加变体）；不加 Profile 字段；
不复杂化 per-question；暂缓新方法卡（两题均被现有 16 卡覆盖）。

## 7. 治理结论（P13-2 收口，正式）

1. **Per-question DTO 治理**：保留为接口，**冻结其 schema 与复杂度**；当前
   Method Selection 不再投入 per-question 建模（top-1 25% vs 100% 已证明
   当前复杂化方向是错的）。未来只有在真实题目上证明其产生**正 Δscore**
   才允许重新打开。
2. **测量层修正 ≠ 能力提升（边界披露，长期有效）**：2023C 的 0→100 中，
   `_method_hit` 紧凑匹配修复属 **measurement-layer correction，不计入
   Agent capability improvement**。真正属于 P13-2 的能力 Δ 只有：
   > **在 GT 冻结、测量规则统一后，语义 ranking 从 MC 非 top-1 → MC
   > top-1（2000C，GT 未动）。**
   2023C 的 100 是 canonicalization 修复后的首次可测读数——其排序基线
   本就正确（classical_timeseries 族基线即 #1）。
3. **P13-2 全部结果冻结**：不为把 per-question 的 25% 提上去继续优化——
   25% 本身已证明该方向是错的。

## 8. 遗留（记录，不阻塞）

- 候选多样性仍是低值（全局画像下 distinct_chosen=1）：排序修正后单选收敛
  到语义正确卡——多样性的价值留待 P13-3 模型比较阶段评估；
- `_method_hit` 紧凑匹配是词面归一化，非语义匹配；GT 词表随方法卡族演化
  时需维护（记录在 e2e_metrics docstring）。
