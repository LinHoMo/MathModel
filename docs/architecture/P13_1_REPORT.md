# P13-1 Report — Problem → Method 接口实验（2000C 消融）

> 日期：2026-09-06 · 执行原则：**只允许增加"题目语义 → 已有方法选择器"的信息流，不允许增加新的认知层。**
> GT 冻结沿用基线 `projects/bench-m4-2000c/work/e2e_gt.json`；未调 GT、未加题目特判、未动 P7-P11 契约。

## 1. 任务书问题（置顶）

> 给 Agent 的方法选择器提供题目语义之后，method selection 是否真的提高？

## 2. 交付了什么（信息流，无新认知层）

- **`problem_profile` DTO**（能力接口，非本体）：P8 冻结六键
  `problem_types / has_data / sample_size / time_series / objectives / uncertainty`
  + `note` 自由文本；两份画像存 `core/knowledge/bench/e2e/2000_C_profile_{global,per_question}.json`。
- **`handlers.features_for(features, qid)`**（~6 行，THREE_LAYER §3 已批准例外）：
  `per_question[qid]` 覆盖合并全局特征；`do_model_selection` 的 arena.select 与
  candidate 生成接线；全局 literature_search 不变。
- **`bench e2e run --profile`**：画像 → `RuntimeSession(features=...)`，
  副本存各项目 `work/e2e_profile.json` 作 provenance。

## 3. 消融结果（官方口径 = 已提交的 metric 实现）

| 条件 | 输入 | method selection | distinct_chosen |
|---|---|---|---|
| A Baseline | 缺省 `{"problem_types":["evaluation"]}` | **0** | 1（TOPSIS） |
| B Global Profile | 题目级六键特征 | **0** | 1（TOPSIS） |
| C Per-question Profile | 每题独立六键特征 | **0** | 1（TOPSIS） |

**官方判定：Case D —— 接口成功但能力没有提升。** 按纪律，本轮就地停止：
未为让 Δ 变正修改任何评分规则、GT 或画像词表。

## 4. Case D 调查（用户预设路径：查 Retriever / Arena / MethodCard matching）

### 4.1 接口本身已验证打通 ✅

画像确实进入检索器并**改变了排序**：

| 特征 | top-3 排名 |
|---|---|
| A 默认 | AHP 70 > TOPSIS 69 > PCA 60（TOPSIS 靠质量分上位） |
| B 全局画像 | TOPSIS 71 > AHP 68 > **Monte Carlo 66（从落榜升至 #3）** |
| C 逐题画像 | 每题 top3 = [TOPSIS, AHP, Monte Carlo]（语义命中一致） |

### 4.2 根因一（测量侧）：metric top-3 实现把 chosen 重复计入

`e2e_metrics._metrics` 的 `top3 = chosen + shortlist[:2]`——而 `shortlist[0]`
就是 chosen，导致实际只检查 **2 个不同候选**；Monte Carlo 恰在 shortlist
第 3 位，从未被检查。按路线图已发布的定义（"选出的方法候选（top-3）命中
金标准方法集的比例"），修正口径的诊断值为：

- **A = 0%**（默认特征下 MC 不在 shortlist）
- **B = 100%**（4/4 题 shortlist 含 mc-monte-carlo → GT "monte carlo" 命中）
- **C = 100%**（同上）

**此为诊断信息，不改变本轮官方结果**；metric 实现修复列为 P13-2 第一项，
修复后用同一冻结 GT 重测并全程披露。

### 4.3 根因二（能力侧）：检索器打分结构性压制语义证据（P13-2 真靶点）

全局画像下的 score_detail 拆解（total = fit+data+interpretability+robustness
+complexity+innovation+competition+evidence_cost+risk_penalty）：

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

结论：**类型命中（MC +9）被非语义维度净抵消（约 −16）**——即使画像完美，
类型证据在当前权重结构下不可能改变"通用优质卡"（TOPSIS/AHP）对专用卡的
位次。这不是知识缺失（16 卡里已有 MC），是**打分权重结构问题**。

## 5. P13-2 决定（按 Case D 分支，提前锁死的触发条件）

1. **metric top-3 修复**（测量基础设施，非能力改动）→ 用冻结 GT 重测 A/B/C；
2. **Retriever 打分再平衡调查**：类型命中权重 vs applicability 基线（20+4×n，
   cap 40）+ 质量维度——目标：让"语义类型证据"能影响位次，同时不为结果
   反向调参（任何权重改动都要在 ≥2 道题上做消融）；
3. **不加 Problem Profile 字段**（本轮红线延续）；population dynamics 卡
   暂缓——16 卡已有 MC，证明"加卡"不是当前瓶颈。

## 6. 值得记录的意外发现

- `risk_penalty`（失败记忆）对 MC 友好（−3 vs TOPSIS −13）：P8 的失败记忆
  闭环在真实赛题上首次产生了区分度；
- `distinct_chosen = 1` 贯穿三条件：通用优质卡垄断选型，正是基线报告
  "TOPSIS/AHP 全选"现象的机理层解释。
