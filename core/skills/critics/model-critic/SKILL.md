---
name: model-critic
description: '模型质量前置审查：假设合理性、方法-问题匹配度、可解性、复杂度必要性、失败记忆比对。fail 触发反馈环回 model_construction。'
role: critic
node: model_critique
validator: model-critic
utg_layer: L4（异构验证）前置化
inputs:
  - state/registry.json        # M/A artifacts
  - state/decisions.json       # 选型决策（chosen/alternatives/criteria）
  - state/evidence_graph.json
outputs:
  - work/model_critique.md     # 批判报告（PASS/FAIL + 逐项依据）
---

## 执行卡片（先读这里）

- **门禁**: 本 skill 即门禁——输出 PASS 或 FAIL，FAIL 时引擎按 on_fail 回退 model_construction
- **输入**: Model artifacts（M###）+ 选型决策（D###）+ 问题特征
- **核心动作**: 五维批判（见 Procedure），任何一维 FAIL 即整体 FAIL
- **工具**: `python core/tools/knowledge.py show <card_id>`（方法卡）、`failures <card_id>`（失败记忆）

---

# Model Critic

## Role

模型进入实验前的守门人。**不是打分员**——输出判定（PASS/FAIL）而非分数，FAIL 必须给出可执行的修正方向。

## 与 V2 的区别

V2 assumption-validator 只查假设四维评分；V3 model-critic 前移到 model_construction 之后、experiment 之前，且消费 Knowledge 层：方法卡 risks 与失败记忆直接作为批判 checklist。

## Procedure

### Step 1: 加载批判对象

- 读 Registry 中本 Question 的 model artifacts（M###）与 assumption artifacts（A###）。
- 读 Decision Log 中该 Question 的选型决策（D###，含 alternatives 与 criteria）。

### Step 2: 五维批判

1. **假设合理性**（承 V2 assumption-validator）: 每条假设有 necessity；简化假设不改变问题本质；关键假设标注敏感性影响。
2. **方法-问题匹配**: 检索 `python core/tools/knowledge.py show <选型 card_id>`，逐条比对 good_for 是否真的覆盖本问题特征；requires 是否满足（数据/规模/前提）。
3. **失败记忆比对**: `python core/tools/knowledge.py failures <card_id>`，逐条检查当前建模是否已落入历史失败模式（symptom 比对）。
4. **可解性**: 模型在时限内可计算（规模估计）；参数可辨识（有数据支撑或有文献先验）。
5. **复杂度必要性**: 若选型比 alternatives 中落选者更复杂，必须有明确理由（决策 reasoning）——否则"简单方法够用"优先。

### Step 3: 输出判定

写 `work/model_critique.md`：

```
verdict: PASS | FAIL
per-dimension: 假设[ok/问题] 方法匹配[...] 失败记忆[...] 可解性[...] 复杂度[...]
fail_reasons: （FAIL 时逐条列出，指向具体 M###/A###/D###）
revision_direction: （FAIL 时给 model_construction 的修正方向，可执行）
```

### Step 4: 登记后果

- PASS: 对 model artifacts 执行 `mark_validated("model-critic", report)`。
- FAIL: 若决策层面问题（选型错了），在 Decision Log `invalidate(D###, ...)` 并说明；建模层面问题则只在批判报告中指出。

## Self-Check

- [ ] 五维全部检查（不是只查假设）
- [ ] 每条 FAIL 理由指向具体 artifact/decision ID
- [ ] revision_direction 可执行（不是"再改好一点"）
- [ ] 失败记忆比对至少覆盖选型方法的全部关联 failure

## Iteration

- FAIL → 引擎自动回退 model_construction 重做（on_fail 反馈环，max_retries=2）。
- 2 轮仍 FAIL → blocked，等待人工介入（换方法需回 model_selection 并 invalidate 旧决策）。
