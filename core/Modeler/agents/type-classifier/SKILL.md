---
name: type-classifier
description: '识别赛题类型（A 物理 / B 实验 / C 数据 / D 运筹 / E 综合）并推荐方法方向。在 problem-parser 产出 question_spec.json 后执行。'
hand: modeler
utg_layer: L1
stage: 2
inputs:
  - work/question_spec.json
outputs:
  - work/type_classification.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> modeler type-classifier`
- **输入**：work/question_spec.json
- **输出**：`work/type_classification.json`
- **核心步骤**：1. 读题型知识 → 2. 判 A/B/C/D/E → 3. 给方法方向 → 4. 写 type_classification.json
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Type Classifier

## Role

题型识别 A/B/C/D/E，并给出推荐方法方向，把题型判定从模糊直觉固化为关键词决策树输出。

## UTG Layer

L1 形式化规约层。题型判定是后续方法匹配的入口，归类歧义会向下游传播放大。本 agent 用显式决策树把判定依据固化：
- 输入关键词 → 唯一题型映射，判定路径可追溯。
- 推荐方向指向具体知识库文档，避免"凭印象选题"。

> **借鉴 MM-Agent 的「文献检索 + 证据提取」思想**：type-classifier 在关键词分类基础上，增加「出题人追溯」与「真题家族映射」两个增强步骤（Step 2.5 + Step 2.6），用历史真题的出题规律交叉印证分类结果。

## Contract

- **输入**：`work/question_spec.json`（由 problem-parser 产出）。
- **输出**：`work/type_classification.json`，结构：
  ```json
  {
    "topic_type": "A-physical | B-experiment | C-data | D-operations | E-interdisciplinary",
    "decision_path": ["关键词命中链路"],
    "matched_keywords": ["..."],
    "examiner_tracker": {
      "identified_entity": "...",
      "likely_examiner_team": "... | unknown",
      "historical_preferences": ["方法偏好1", "方法偏好2"],
      "cross_validation": "一致 | 冲突"
    },
    "family_mapping": {
      "family_name": "...",
      "historical_siblings": ["2023A", "2025A"],
      "core_methods": ["几何光学", "数值优化"],
      "bonus_methods": ["多模型对照", "灵敏度分析"]
    },
    "recommended_directions": {
      "methodology": ["core/knowledge/methodology/xxx.md"],
      "domain": ["core/Modeler/knowledge/domain/xxx.md"],
      "problem_type_guide": "core/Modeler/knowledge/problem-types/type-x-xxx.md"
    },
    "confidence": "high | medium | low"
  }
  ```

## Procedure

### Step 1: 读取规约

- 读 `work/question_spec.json` 的 `background.domain_keywords`、`background.physical_processes`、`metadata.topic_type`（初判值）。

### Step 2: 沿决策树匹配

按下方"题型识别决策树"逐层匹配关键词，记录命中路径 `decision_path`。

### Step 2.5: 出题人追溯（增强，借鉴 MM-Agent 文献检索思路）

> 借鉴 LLM-MM-Agent 的文献追溯思想，增加对 CUMCM 出题人/命题单位的追踪，与关键词型分类交叉印证。

参考 `core/knowledge/problems/INDEX.md` 中的「出题方向」，执行以下操作：

1. **提取题面背景实体**：从赛题 `background.context` 中识别核心实体（如「导弹」「定日镜」「干涉光谱」「NIPT」）。
2. **映射到命题单位/团队**：参考 `core/knowledge/problems/CUMCM-EXAMINER-TRACKER.md`（如有该文件）或 INDEX.md 的「出题方向备注」，判断该实体历史上由哪个单位/团队反复命题。
3. **检索同命题团队的历年真题**：在 `core/knowledge/paper-cases/` 中检索同一命题团队历年的赛题，提取：
   - 该团队命题的**稳定方法论偏好**（如系统工程院偏 ODE/连续力学、国防科大偏优化调度、中南大学偏数据+评价）
   - 该团队命题的**题面结构模式**（如「物理背景 + 多段递进子问 + 开放最后一问」）
4. **交叉印证**：将出题人/团队的方法论偏好与 Step 2 关键词分类结果对照。若一致则 `confidence` 升级；若不一致，以**出题方向为准**（评阅由该团队的专家主导），`confidence` 保持并在 `decision_path` 中记录冲突。

### Step 2.6: 真题家族映射

> 将当前赛题映射到「历史赛题家族」，用家族内的方法演进规律推荐方法方向。

1. **识别赛题家族**：参考 `core/knowledge/problems/INDEX.md` 的「家族列」（同一命题方向下的历年真题组成家族，如「定日镜家族」：2019A+2023A+2025A）
2. **读取家族方法演进**：参考 `core/knowledge/methodology/method-trends-2010-2025.md` 与 `core/knowledge/paper-cases/METHOD-TOPIC-GRAPH.json`，分析该家族的：
   - **基础方法**（历年都必须用到的，如定日镜家族的几何光学 + 数值优化）
   - **进阶加分方法**（近年评阅明确鼓励的，如多模型对照、机理+数据混合）
3. **写入输出**：将「基础方法 + 进阶加分方法」作为 `recommended_directions.methodology` 的来源补充。

### Step 3: 确定题型

- 输出 `topic_type`（枚举 A-physical/B-experiment/C-data/D-operations/E-interdisciplinary）。
- 多分支命中时，以最深叶子节点为准；冲突时 `confidence=low` 并在 decision_path 标注冲突。

### Step 4: 推荐方法方向

- 依据命中叶子节点，给出 `recommended_directions`，指向 `core/knowledge/methodology/`、`core/Modeler/knowledge/domain/` 与对应 `core/Modeler/knowledge/problem-types/type-x-xxx.md` 专项文档。

### Step 5: 导出

- 写 `work/type_classification.json`。

## 题型识别决策树

> 原建模手 SKILL.md 的决策树迁移至此保留，不得丢失。

```
问题关键词分析：
├── 物理过程（运动/动力/热传导/电磁/光学） → A题：物理建模类
│   ├── 波浪/水动力 → 参考 core/Modeler/knowledge/domain/wave-energy.md
│   ├── 光学/反射/聚焦 → 参考 core/Modeler/knowledge/domain/optical-systems.md
│   ├── 热传导/温度 → 参考 core/Modeler/knowledge/domain/thermal-systems.md, heat-transfer.md, protective-design.md
│   ├── 机械运动/振动 → 参考 core/knowledge/methodology/optimization.md
│   ├── 航天/轨道 → 参考 core/Modeler/knowledge/domain/aerospace-dynamics.md
│   ├── 太阳能/影子 → 参考 core/Modeler/knowledge/domain/solar-energy.md
│   ├── 系泊/海洋 → 参考 core/Modeler/knowledge/domain/mooring-system.md
│   ├── 望远镜/FAST → 参考 core/Modeler/knowledge/domain/telescope-optics.md
│   ├── 防护服/隔热 → 参考 core/Modeler/knowledge/domain/protective-design.md
│   └── 图像处理/CT → 参考 core/Modeler/knowledge/domain/image-processing.md, core/knowledge/methodology/image-processing-methods.md
├── 实验数据（正交试验/响应面/因素分析） → B题：实验设计类
│   ├── 化学反应/催化剂 → 参考 core/Modeler/knowledge/domain/chemical-experiments.md
│   ├── 调度/路径规划 → 参考 core/Modeler/knowledge/domain/scheduling.md
│   ├── 博弈/竞争策略 → 参考 core/knowledge/methodology/game-theory.md, core/Modeler/knowledge/domain/game-strategy.md
│   └── 无人机/定位 → 参考 core/Modeler/knowledge/domain/drone-positioning.md
├── 商业数据（销售/客户/金融） → C题：数据分析类
│   ├── 会员/客户画像 → 参考 core/Modeler/knowledge/domain/data-mining.md, customer-analytics.md
│   ├── 时间序列预测 → 参考 core/knowledge/methodology/time-series.md
│   ├── 信贷/风险 → 参考 core/Modeler/knowledge/domain/financial-risk.md, finance-credit.md
│   └── 农业/种植 → 参考 core/Modeler/knowledge/domain/agriculture.md
├── 评价/决策/调度 → D题：综合评价与优化调度类
│   ├── 方案评价 → 参考 core/knowledge/methodology/evaluation-methods.md
│   ├── 图论/网络 → 参考 core/knowledge/methodology/graph-theory.md
│   ├── 建筑评价 → 参考 core/Modeler/knowledge/domain/building-evaluation.md
│   └── 交通运营 → 参考 core/Modeler/knowledge/domain/traffic-operations.md
├── 排队/服务系统 → 参考 core/knowledge/methodology/queueing-theory.md
├── 风电/能源 → 参考 core/Modeler/knowledge/domain/wind-energy.md
├── 管道/路由 → 参考 core/Modeler/knowledge/domain/pipeline-routing.md
├── 供水/水利 → 参考 core/Modeler/knowledge/domain/campus-water.md
└── 土壤/环境 → 参考 core/Modeler/knowledge/domain/soil-pollution.md

参考 core/knowledge/methodology/method-trends-2010-2025.md 获取方法频率统计和趋势分析
参考 core/Modeler/knowledge/problem-types/type-a-physical.md 获取A题完整建模流程
参考 core/Modeler/knowledge/problem-types/type-b-experiment.md 获取B题完整建模流程
参考 core/Modeler/knowledge/problem-types/type-c-data.md 获取C题完整建模流程
参考 core/Modeler/knowledge/problem-types/type-d-operations.md 获取D题完整建模流程
参考 core/Modeler/knowledge/problem-types/type-e-interdisciplinary.md 获取E题完整建模流程
```

## Self-Check

- [ ] `topic_type` 取值在 A-physical/B-experiment/C-data/D-operations/E-interdisciplinary 枚举内
- [ ] `decision_path` 完整记录命中关键词链路，可追溯
- [ ] `recommended_directions.problem_type_guide` 指向对应 `core/Modeler/knowledge/problem-types/type-x-xxx.md`
- [ ] 命中的 `core/Modeler/knowledge/domain/` 与 `core/knowledge/methodology/` 文档路径真实存在
- [ ] 多分支冲突时 `confidence=low` 且冲突已标注
- [ ] 未凭直觉判定，每个判定都有关键词证据
- [ ] `examiner_tracker` 已填写：含 `identified_entity`、`likely_examiner_team`、`cross_validation`
- [ ] `family_mapping` 已填写：含 `family_name`、`historical_siblings`、`core_methods`、`bonus_methods`
- [ ] 出题人追溯结果与关键词分类已做交叉印证（一致时 confidence 升级，冲突时已记录）
- [ ] 进阶加分方法（bonus_methods）来自近年评阅鼓励方向（参考 scoring-criteria.md）

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "modeler",
  "stage": 2,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "type-classifier",
      "stage": 2,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/Modeler/knowledge/problem-types/type-a-physical.md`
- `core/Modeler/knowledge/problem-types/type-b-experiment.md`
- `core/Modeler/knowledge/problem-types/type-c-data.md`
- `core/Modeler/knowledge/problem-types/type-d-operations.md`
- `core/Modeler/knowledge/problem-types/type-e-interdisciplinary.md`
- `core/knowledge/methodology/method-trends-2010-2025.md`（方法频率/趋势）
- `core/knowledge/methodology/CUMCM-HMML.md`（三级方法知识库，含国赛专属节点信息）
- `core/knowledge/problems/INDEX.md`（赛题索引，含「出题方向」和「家族」列）
- `core/knowledge/problems/CUMCM-EXAMINER-TRACKER.md`（出题人/命题团队追踪，如有）
- `core/knowledge/review/scoring-criteria.md`（评阅扣分点 → bonus_methods 来源）
- `core/Modeler/knowledge/domain/`（领域知识索引）

## Iteration

当关键词不足以唯一判定（`confidence=low`）时：
1. 回退 problem-parser 补充 `background.domain_keywords` / `physical_processes`。
2. 重新匹配决策树，直至 `confidence` 达 medium 以上。
3. 若仍冲突，按"物理过程优先于数据分析"的竞赛惯例暂定，并在 decision_path 标注待 method-matcher 复核。
