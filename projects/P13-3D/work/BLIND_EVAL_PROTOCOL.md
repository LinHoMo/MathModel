# P13-3D Blind Evaluation Protocol

> 本协议定义 P13-3D（Model → Paper Conversion）的盲评流程。
> 核心原则：**Artifact 是唯一真源；Writer 不含反作弊条款；Fidelity Gate 独立于 Paper Quality。**

## 1. 评估架构

```
                    Model Artifact (frozen)
                          │
                       FREEZE
                          │
             ┌────────────┴────────────┐
             │                         │
          Same Writer              Fidelity Gate
             │                     (artifact vs paper)
             ↓                         │
           Paper                        │
             │                         │
             └──────────┬──────────────┘
                        ↓
              ┌─────────┴─────────┐
              │                   │
         Paper Quality      Fidelity Score
         (4 dimensions)     (mutation log)
              │                   │
              └─────────┬─────────┘
                        ↓
                   Final Results
```

## 2. Paper Quality 评分维度

| 维度 | 定义 | 评分标准 |
|---|---|---|
| Mathematical correctness | 公式/推导/量纲正确性 | 0-100，扣分制（每个错误 -5~-15） |
| Problem alignment | 论文是否回答了题目要求 | 0-100，子问题覆盖度 × 正确性 |
| Completeness | 模型组件覆盖度 | 0-100，变量/约束/目标/假设/方程覆盖率 |
| Communication | 表达清晰度、结构合理性 | 0-100，可读性/结构/图表/符号一致性 |

**不合并为单一 composite**——四个维度独立报告。

## 3. Fidelity Gate 评分

### 3.1 五类 Mutation

| Type | 定义 | 严重性 |
|---|---|---|
| Addition | Artifact 中不存在的元素出现在论文中 | critical/major/minor |
| Deletion | Artifact 中的元素在论文中消失 | critical/major/minor |
| Modification | 同一 id 的表达式/定义发生变化 | critical/major/minor |
| Renaming | 同一实体在论文中使用不同名称 | major/minor |
| Semantic Drift | 同一术语在 Artifact 和论文中含义不同 | critical/major/minor |

### 3.2 Fidelity Score 计算

```
Fidelity Score = 1 − Σ(severity_weight × count) / total_elements

severity_weights: critical=1.0, major=0.5, minor=0.1
```

### 3.3 Addition 独立计数

Addition 不计入 Fidelity Score（因为它不是"丢失"而是"篡改"），但单独计数：
- critical addition: 添加了改变模型行为的元素
- major addition: 添加了新能力/新约束
- minor addition: 补充说明/细化

## 4. 盲评流程

### 4.1 匿名化

1. 三臂产物标记为 X/Y/Z（随机映射，映射表仅存主报告）
2. 论文文风可能泄露臂信息（已知局限，记录但不校正）

### 4.2 评委输入

每题一个评委，输入：
- 题目原文
- 三份匿名论文（X/Y/Z）
- 三份对应匿名 artifact（X/Y/Z）

### 4.3 评委输出

```json
{
  "papers": [
    {
      "id": "X",
      "scores": {
        "math_correctness": 85,
        "problem_alignment": 90,
        "completeness": 80,
        "communication": 75
      },
      "comments": "数学推导正确，但缺少对Q3的讨论..."
    },
    {
      "id": "Y",
      "scores": {...},
      "comments": "..."
    },
    {
      "id": "Z",
      "scores": {...},
      "comments": "..."
    }
  ],
  "fidelity_audit": [
    {
      "paper_id": "X",
      "mutations": [
        {
          "type": "deletion",
          "severity": "major",
          "category": "constraints",
          "affected_object": "capacity_constraint",
          "artifact_ref": "constraints.capacity_constraint",
          "paper_ref": "section_3.2",
          "description": "Capacity constraint from artifact not found in paper"
        }
      ],
      "additions": [
        {
          "type": "addition",
          "severity": "minor",
          "category": "assumptions",
          "affected_object": "new_assumption_1",
          "paper_ref": "section_2.3",
          "description": "Writer added an assumption not in artifact"
        }
      ]
    }
  ]
}
```

## 5. 双向检查规则

### 5.1 Artifact → Paper（遗漏检查）

逐项核对 artifact 中的每个元素是否出现在论文中：
- Variables: 每个变量是否在符号表或正文中出现
- Parameters: 每个参数是否声明并使用
- Constraints: 每个约束是否在模型建立部分出现
- Objective: 目标函数/估计量是否完整写出
- Mechanism: 方程组是否完整呈现
- Assumptions: 假设是否逐条列出

### 5.2 Paper → Artifact（篡改检查）

逐项核对论文中的每个模型元素是否在 artifact 中有对应：
- 新变量: 论文中出现的变量是否在 artifact 的 variables 列表中
- 新约束: 论文中的约束是否在 artifact 的 constraints 列表中
- 新假设: 论文中的假设是否在 artifact 的 assumptions 列表中
- 修改的方程: 论文中的方程是否与 artifact 的 mechanism 一致

### 5.3 Semantic Drift 检查

- 同一术语在 artifact 和论文中含义是否一致
- 例如: artifact 中 "capacity" 指物理容量，论文中变成"成本上限"

## 6. 严重性判定标准

### Critical（必须修复）
- 改变模型行为的核心变异
- 例如: 删除目标函数、修改核心方程、添加改变结论的约束

### Major（应该修复）
- 影响模型完整性的变异
- 例如: 删除约束、添加新变量、修改参数值

### Minor（可以接受）
- 不影响模型行为的变异
- 例如: 符号重排、同义替换、省略细节说明

## 7. 已知局限

1. 评委与生成侧同底层 LLM（不同会话、无臂知识）
2. 论文文风可能泄露臂信息（记录但不校正）
3. Semantic Drift 检测依赖 LLM 语义判断（非确定性）
4. 本轮 n=3 题，统计性结论需扩大到 ≥10 题
