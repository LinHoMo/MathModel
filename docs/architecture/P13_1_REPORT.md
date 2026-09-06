# P13-1 Report — Problem → Method 接口实验（2000C 消融，v2 最终版）

> 日期：2026-09-06 · 执行原则：**只允许增加"题目语义 → 已有方法选择器"的信息流，不允许增加新的认知层。**
> GT 冻结沿用基线 `projects/bench-m4-2000c/work/e2e_gt.json`；未调 GT、未加题目特判、未动 P7-P11 契约。
> **后续**：本报告 §3 的 A/B/C 数字为 P13-2 落地前（w_sem=3）口径；落地后的
> 复测与 top-1 分析见 `P13_2_REPORT.md`。

## 1. 任务书问题（置顶）

> **不是"我们成功实现了 features_for"，而是"同一道题，在冻结 GT 下，
> Problem Profile 是否改变了 Method Selection 的可测行为"。**

## 2. 交付了什么（信息流，无新认知层）

- **`problem_profile` DTO**（能力接口，非本体）：P8 冻结六键
  `problem_types / has_data / sample_size / time_series / objectives / uncertainty`
  + `note` 自由文本；画像存 `core/knowledge/bench/e2e/2000_C_profile_{global,per_question}.json`。
- **`handlers.features_for(features, qid)`**（~6 行，THREE_LAYER §3 已批准例外）：
  `per_question[qid]` 覆盖合并全局特征；`do_model_selection` 的 arena.select 与
  candidate 生成接线；全局 literature_search 不变。
- **`bench e2e run --profile`**：画像 → `RuntimeSession(features=...)`，
  副本存各项目 `work/e2e_profile.json` 作 provenance。
- **method_selection 口径钉死（v2 最终版）**：
  `top-3 GT hit = GT 方法至少有一个 canonical method 与该 question 的
  top-3 candidate/shortlist 方法匹配`（chosen + shortlist 去重保序取前 3）；
  top-1 / top-3 / candidate diversity / 每题 shortlist 全部留在 detail。

## 3. 消融结果（官方口径）

| 条件 | 输入 | **top-3 hit（value）** | top-1 | distinct_chosen |
|---|---|---|---|---|
| A Baseline | 缺省 `{"problem_types":["evaluation"]}` | **0** | 0 | 1（TOPSIS） |
| B Global Profile | 题目级六键特征 | **100**（4/4） | 0 | 1（TOPSIS） |
| C Per-question Profile | 每题独立六键特征 | **100**（4/4） | 0 | 1（TOPSIS） |

失败定位漏斗（detail 驱动）：画像已传入 ✅ → matcher 已召回（top-3 命中
GT "monte carlo"，MC 进 shortlist 第 3 位）✅ → **排序错**（top-1 仍 TOPSIS）❌
→ 非 GT canonicalization 问题 ✅。

## 4. 判定（按任务书结果矩阵）

- **A=0，B/C 明显 > 0 → 接口修复有效。** Problem Profile 改变了 Method
  Selection 的可测行为（0 → 100）。
- **B ≈ C（均 100）→ 全局画像已经足够，per-question 不再复杂化**（DTO 与
  features_for 保留，供 P13-2 排序修复后可能出现的逐题分化复用）。
- **top-1 全 0 → 失败分支锁定在"有候选但排序错"**——召回层已工作，错在
  排序权重。

> 备注（测量史）：初版 metric 实现把 chosen 重复计入 top-3（实际只检查 2 个
> 候选），曾得到官方 0/0/0（Case D 判定）。口径经任务书所有者按本报告 §2
> 定义修正后重测得出上表——修正只发生在测量仪器侧，GT 与画像词表零改动。

## 5. P13-2 决定（唯一靶点：排序再平衡）

score_detail 拆解（全局画像下）显示类型命中 +9 被非语义维度净抵消 −16：

| 维度 | mc-topsis (71) | mc-monte-carlo (66) | 差 |
|---|---|---|---|
| fit（含类型命中 +9） | 33 | 32 | +1 |
| data | 15 | 10 | +5 |
| interpretability | **10** | **5** | +5 |
| robustness | 6 | 5 | +1 |
| complexity | 5 | 3 | +2 |
| innovation | 2 | 4 | −2 |
| competition | **10** | **5** | +5 |
| evidence_cost | 3 | 5 | −2 |
| risk_penalty | −13 | −3 | −10 |

P13-2 = Retriever 打分再平衡（类型证据权重 vs applicability 基线 20+4×n
cap 40 + 质量维度），验收 = 同题集 top-1 从 TOPSIS 变为语义合理卡 + ≥2 题
消融防反向调参。**不加 Profile 字段、不复杂化 per-question、暂缓新方法卡**
（16 卡已有 MC，加卡不是瓶颈）。

## 6. 意外发现

- `risk_penalty`（P8 失败记忆）对 MC 友好（−3 vs TOPSIS −13）：失败记忆
  闭环在真实赛题上首次产生区分度；
- `distinct_chosen = 1` 贯穿三条件：通用优质卡垄断选型的机理由此定案。

## 7. 三件验收物（任务书要求）

1. **RAC**：基线项目仪表盘 experiment 4/8=50% / validation 4/8=50% /
   writing 0/20=0% / overall 12/70=17.1%（measurement metadata，不进能力均值）；
2. **A/B/C**：0 / 100 / 100（top-3 口径）；
3. **Δscore**：method selection 0 → **100**（top-3 口径，冻结 GT）；
   top-1 仍 0 → 即 P13-2 的输入。
