---
name: assumption-validator
description: '对每条假设做四维量化评分（物理合理性 / 数学一致性 / 数据支撑度 / 影响程度），低于阈值即回退修正模型。'
hand: modeler
utg_layer: L4
stage: 5
inputs:
  - work/model_draft.md
outputs:
  - work/assumption_validation.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> modeler assumption-validator`
- **输入**：work/model_draft.md
- **输出**：`work/assumption_validation.json`
- **核心步骤**：1. 抽取假设 → 2. 四维评分（物理/数学/数据/影响）→ 3. 低于 6.0 分回退 → 4. 写 assumption_validation.json
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Assumption Validator

## Role

假设四维评分验证：对每个假设打量化分数，综合评分达阈值才放行，禁止自由文本描述"假设合理"。

## UTG Layer

L4 异构验证层。本层用结构化评分替代主观判断，对应铁律 M2（每个假设必须有量化验证）。评分必须通过工具调用产生，不是叙述。

## Contract

- **输入**：`work/model_draft.md`（含假设列表，`validation` 字段待填）。
- **输出**：`work/assumption_validation.json`，结构：
  ```json
  {
    "threshold": 6.0,
    "assumptions": [
      {
        "id": "H1",
        "content": "...",
        "necessity": "...",
        "type": "critical | secondary | simplification",
        "validation": {
          "physical_rationality": 0.0,
          "math_consistency": 0.0,
          "data_support": 0.0,
          "impact_degree": 0.0,
          "composite_score": 0.0
        },
        "passed": true
      }
    ],
    "all_passed": true,
    "contradictions": []
  }
  ```
- **通过条件**：每个假设 `composite_score >= get("modeling.assumption_score_threshold")`（默认 6.0）。

## Procedure

### Step 1: 提取假设

- 用 `core/knowledge/validation/assumption_validator.py` 的 `AssumptionValidator.extract_from_text(model_draft_text)` 提取假设，或直接读取草稿中的假设段。提取时记录**假设敏感性预检**（铁律 M8）：模糊表述、≥2 种解释与验算过程、最终采用解释；关键假设须标记 `parameterizable: true` 以便代码层可切换（如 `get("modeling.assumption.<name>")`）。

### Step 2: 四维评分

对每个假设打分（每维 0-10）：

| 维度 | 权重 | 评分锚点 |
|------|------|---------|
| physical_rationality 物理合理性 | 30% | 9-10=完全符合物理；5-6=部分符合；1-2=严重违反 |
| math_consistency 数学一致性 | 25% | 9-10=推导完整；5-6=有 gaps；1-2=严重错误 |
| data_support 数据支撑度 | 25% | 9-10=充分数据；5-6=有限；1-2=无支撑 |
| impact_degree 影响程度 | 20% | 9-10=影响小；5-6=中等；1-2=影响大 |

综合评分公式（权重与上表一致）：

```
composite_score = 0.30*physical_rationality + 0.25*math_consistency + 0.25*data_support + 0.20*impact_degree
```

### Step 3: 阈值判定

- 读取 env 阈值：
  ```python
  from core.env.loader import get
  threshold = get("modeling.assumption_score_threshold", default=6.0)
  ```
- `passed = composite_score >= threshold`。

### Step 4: 一致性与矛盾检查

- 调用 `AssumptionValidator.validate_all()` 检查假设间矛盾（`contradiction_pairs`：理想/实际、刚体/弹性、忽略/考虑、线性/非线性、均匀/非均匀、稳态/瞬态、无摩擦/有摩擦、无阻力/有阻力）。
- 调用 `check_necessity()` 确认必要性说明 >=10 字且含原因词。
- 调用 `check_validation_score()` 确认评分字段齐全且在 [0,10]。

### Step 5: 导出

- 写 `work/assumption_validation.json`，顶层记录 `threshold` 与 `all_passed`。

## Self-Check

- [ ] 每个假设的四维评分均在 [0,10]
- [ ] `composite_score` 按 0.30/0.25/0.25/0.20 权重计算
- [ ] 每个假设 `composite_score >= get("modeling.assumption_score_threshold")`（默认 6.0）
- [ ] 评分通过 `AssumptionValidator` 工具调用产生，非自由文本（M2）
- [ ] `validate_all()` 未发现假设间矛盾
- [ ] 每个假设 `necessity` >=10 字且含原因词（因为/由于/为了/需要/必须/假设/简化）
- [ ] 假设敏感性预检已记录（模糊表述 / ≥2 种解释与验算 / 最终解释，铁律 M8）
- [ ] 关键假设标记 `parameterizable: true`（可参数化，代码层可切换，铁律 M8）
- [ ] 假设敏感性预检记录（铁律 M8）：每个关键假设标注敏感性等级（高/中/低），高敏感性假设标记为"可参数化"
- [ ] 关键假设可参数化标记：高敏感性假设需在 Programmer 手做 ±20% 灵敏度扫描（`sensitivity_range: 0.20`）
- [ ] 假设敏感性预检结果已记录在 `assumption_validation.json` 的 `sensitivity_flags` 字段（含假设 ID、敏感性等级、是否可参数化、灵敏度扫描范围）
- [ ] env 阈值 `assumption_score_threshold` 已读取并记录在输出顶层

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "modeler",
  "stage": 5,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "assumption-validator",
      "stage": 5,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/knowledge/validation/assumption_validator.py` —— 评分与矛盾检查实现
- `core/knowledge/methodology/hypothesis-validation.md` —— 验证方法学
- `core/env/loader.py` —— `get("modeling.assumption_score_threshold")`

## Iteration

当存在假设 `composite_score < threshold` 或检测到矛盾时：
1. 分析不通过原因（物理违反/推导 gap/数据缺失/影响过大）。
2. 回退 model-builder 修正假设或调整模型结构（如放宽/收紧假设、补数据来源）。
3. 重新评分，循环直至 `all_passed == true` 且无矛盾。
4. 修正后的假设回写 `model_draft.md` 后再导出 `assumption_validation.json`。
