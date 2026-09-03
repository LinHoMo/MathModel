---
name: method-matcher
description: '从知识库检索并对比候选模型，为每个子问题输出至少 2 个有实质差异的候选。用于建模选型，避免单一方法拍脑袋。'
hand: modeler
utg_layer: L2
stage: 3
inputs:
  - work/type_classification.json
outputs:
  - work/method_candidates.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> modeler method-matcher`
- **输入**：question_spec + type_classification
- **输出**：`work/method_candidates.json`
- **核心步骤**：1. 检索知识库 → 2. 每个子问题给 ≥2 个实质不同的候选 → 3. 写候选对比 → 4. 写 method_candidates.json
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Method Matcher

## Role

方法匹配：从知识库为每个子问题选出至少 `min_candidate_models` 个候选模型并对比，禁止凭直觉直接定模型。

## UTG Layer

L2 工具调用层。本层强制方法选择必须经过知识库检索与候选对比流程，对应铁律 M1（模型选择必须比较至少 2 个候选方法）。候选对比是结构化产物，不是自由文本叙述。

## Contract

- **输入**：`work/type_classification.json`。
- **输出**：`work/method_candidates.json`，结构：
  ```json
  {
    "min_candidate_models": 2,
    "scoring_method": "fivedim_weighted (MM-Agent 2025)",
    "sub_problems": [
      {
        "id": 1,
        "candidates": [
          {
            "name": "...",
            "family": "...",
            "pros": "...",
            "cons": "...",
            "applicability": "...",
            "innovation_tags": ["..."],
            "mapping_source": "core/knowledge/paper-cases/METHOD-MAPPING.md#...",
            "hmml_node": "领域X>子领域X.X>方法名",
            "fivedim_score": {
              "assumptions": 4,
              "structure": 3,
              "variables": 4,
              "dynamics": 3,
              "solvability": 4,
              "weighted_total": 3.65,
              "verdict": "推荐 | 可考虑 | 不推荐"
            },
            "selected": true,
            "selection_reason": "假设与结构双高，且题给数据维度覆盖充分"
          }
        ]
      }
    ]
  }
  ```
- **候选数量约束**：`candidates.length >= get("modeling.min_candidate_models")`（默认 2）。

## Procedure

### Step 1: 读取题型判定

- 读 `work/type_classification.json`，获取 `topic_type` 与 `recommended_directions`。

### Step 2: 检索方法库

- **优先检索 CUMCM-HMML 三级知识库**：读 `core/knowledge/methodology/CUMCM-HMML.md`，按题型→领域→子领域→方法节点的路径定位候选方法族。HMML 每个节点包含"题型适配""近三年使用频率""常见扣分点""推荐工具""详细文档"五类国赛专属信息。
- 先走决策树收敛方法族：读 `core/knowledge/methodology/METHOD-DECISION-TREE.md`（机器可读版 `METHOD-DECISION-TREE.json`），按子问题特征回答分支问题（Q1–Q8），得到候选方法族，并把走过的分支序列记入候选的 `decision_path`。
- 依据 `recommended_directions.methodology` 检索 `core/knowledge/methodology/` 方法文档。
- 依据 `core/knowledge/paper-cases/METHOD-MAPPING.md` 获取"方法-题型"匹配关系。
- 依据 `core/knowledge/paper-cases/INNOVATION-TAGS.md` 识别可叠加的创新方向。
- 子问题需要外部数据时，参考 `core/knowledge/data-sources/DATA-SOURCES.md` 评估数据可得性（影响候选适用性）。
- **避档检查**：参考 `core/knowledge/methodology/method-trends-2010-2025.md`，若候选为近三年大幅降档方法（AHP、灰色预测、模糊评价、排队论），必须有替代方案或在 HMML 标注的特定场景下使用，避免评阅降档。

### Step 3: 选候选

- 对每个子问题，选出 `>= get("modeling.min_candidate_models")` 个候选模型。
- 候选之间必须有实质差异（不同方法族，非同族参数变体）。
- 读取 env 阈值：
  ```python
  from core.env.loader import get
  min_n = get("modeling.min_candidate_models", default=2)
  ```

### Step 3.5: 五维评分（Critic，借鉴 MM-Agent 多维评估法）

> 借鉴 LLM-MM-Agent（NeurIPS 2025）的 METHOD_CRITIQUE_PROMPT 五维评分体系，为每个候选方法计算量化评分，取最高分者为推荐方案（selected）。

对**每个子问题的每个候选方法**，按以下五维评分（每维度 1-5 分），并计算加权总分：

| 维度 | 权重 | 评估要点 |
|---|---|---|
| 假设适配度（Assumptions） | 30% | 方法的数学假设是否与问题内在特性匹配？如线性回归假设线性关系，但本题存在指数增长 → 低分 |
| 结构适配度（Structure） | 25% | 方法框架能否刻画问题的逻辑/层次/时空关系？如网络流问题是否用图论模型 |
| 变量适配度（Variables） | 20% | 方法处理的变量类型与问题是否兼容？如离散决策变量是否被正确处理 |
| 动力学适配度（Dynamics） | 15% | 方法的时间/动态特性是否匹配问题演化行为？如是否需要考虑时间延迟/反馈环 |
| 可解性（Solvability） | 10% | 在现实资源约束下是否可解？NP-hard 是否需要启发式近似 |

**评分规则**：
- 加权总分 = 假设×0.30 + 结构×0.25 + 变量×0.20 + 动力×0.15 + 可解×0.10
- ≥4.5 分为强推荐，3.5-4.5 分为可考虑，<3.5 分为不推荐
- 取最高分者为 `selected` 推荐方案；当两名差距 <0.5 分时，两个均进入下游由 model-builder 起草对比
- 评分结果写入候选的 `fivedim_score` 字段

### Step 4: 标注对比

- 每个候选填 `name/family/pros/cons/applicability`，并标 `innovation_tags`、`mapping_source`（引用 METHOD-MAPPING.md 的具体条目）。
- 额外标注 `fivedim_score`（五维评分明细与加权总分）和 `hmml_node`（引用的 CUMCM-HMML 节点路径，如"领域2>子领域2.4>NSGA-II"）。

### Step 5: 导出

- 写 `work/method_candidates.json`，顶层记录 `min_candidate_models` 实际取值。

## Self-Check

- [ ] 每个子问题的 `candidates.length >= get("modeling.min_candidate_models")`（默认 2）
- [ ] 每个候选含 name/family/pros/cons/applicability 五字段
- [ ] 每个候选的 `mapping_source` 真实引用 `METHOD-MAPPING.md` 条目
- [ ] 候选之间有实质差异（非同族参数变体）
- [ ] 创新方向已标 `innovation_tags`（参考 `INNOVATION-TAGS.md`）
- [ ] 物理约束/业务约束优先级高于拟合好看（M1）
- [ ] env 阈值 `min_candidate_models` 已读取并记录在输出顶层
- [ ] 每个候选已标注 `hmml_node`（CUMCM-HMML 节点路径）
- [ ] 每个候选已做五维评分（`fivedim_score` 含 assumptions/structure/variables/dynamics/solvability 五项 + weighted_total + verdict）
- [ ] 评分加权公式正确：假设×0.30 + 结构×0.25 + 变量×0.20 + 动力×0.15 + 可解×0.10
- [ ] `selected=true` 的候选是加权最高分；同分差距<0.5 时多个 selected=true
- [ ] 降档方法（AHP/灰色预测/模糊评价）已标注替代方案或使用场景限制
- [ ] 避档检查已通过（参考 `method-trends-2010-2025.md`）

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "modeler",
  "stage": 3,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "method-matcher",
      "stage": 3,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/knowledge/methodology/CUMCM-HMML.md` —— **三级层次化方法知识库（国赛首选检索）**，12 大领域 / 38 子领域 / 96 方法节点
- `core/knowledge/methodology/` —— 41 个方法论文档（方法细节参阅）
- `core/knowledge/paper-cases/METHOD-MAPPING.md` —— 方法-题型匹配
- `core/knowledge/paper-cases/INNOVATION-TAGS.md` —— 创新方向标签
- `core/knowledge/paper-cases/reference/` —— 扩展检索源
- `core/knowledge/methodology/method-trends-2010-2025.md` —— 方法频率/趋势（避档参考）
- `core/knowledge/review/scoring-criteria.md` —— 评分细则（常见扣分点引用源）
- `core/env/loader.py` —— `get("modeling.min_candidate_models")`

## Iteration

当候选不足 `min_candidate_models` 时：
1. 扩大检索至 `core/knowledge/paper-cases/reference/` 与跨题型案例。
2. 若仍不足，回退 type-classifier 复核 `recommended_directions` 是否过窄。
3. 补足后重新对比，确保每个候选有真实差异。

## 风险探针（P2-3，编码前的最后一道闸）

选定候选后、**在投入编码前**必须先跑限时探针，产出 `work/risk_probe.json`。
目的：在花几小时实现之前，先用低成本暴露"这个方法根本走不通"。

必须覆盖 5 项，每项给出结论与依据：

| # | 探针项 | 要回答的问题 |
|---|--------|-------------|
| 1 | 假设成立性 | 关键假设在本题参数下真的成立吗？失效边界在哪？ |
| 2 | 数据覆盖 | 题给数据是否覆盖模型所需维度？有无缺失？ |
| 3 | 输出退化与集中 | 结果会不会退化成常数/极值集中/多解难辨？ |
| 4 | 扰动敏感性 | 参数小幅扰动，结论会不会翻转？ |
| 5 | 规模可行性 | 数据规模下算法能否在时限内跑完？ |

产物格式：

```json
{
  "candidate": "主选方案",
  "baseline": "可用的简化基线（探针必须给出基线，不允许跳过基线上复杂模型）",
  "checks": [{"name": "假设成立性", "result": "pass", "detail": "..."}],
  "risks": [{"risk": "...", "mitigation": "..."}],
  "verdict": "pass | pass_with_watch | fail"
}
```

**verdict 为 fail 时不得进入编码**，必须更换候选。门禁会强制检查：
`python core/tools/gate.py <项目> modeler method-matcher`。
