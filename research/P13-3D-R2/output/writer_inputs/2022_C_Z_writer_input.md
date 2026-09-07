你是一位数学建模论文撰写专家。请根据以下信息撰写一篇完整的数学建模竞赛论文。

**题目**：古代玻璃制品的成分分析与鉴别

**问题描述**：
利用化学成分数据对古代玻璃制品进行分类和鉴别，建立聚类和判别模型。

**模型产物（MODEL_ARTIFACT）**：
以下是建模阶段产出的结构化模型信息。请严格基于此模型撰写论文，**不得修改、补充或删除模型中的任何元素**。

```json
{
  "problem_id": "2022_C",
  "assumptions": [
    {
      "id": "A1",
      "statement": "玻璃成分数据服从多元正态分布",
      "justification": "化学分析通例"
    },
    {
      "id": "A2",
      "statement": "不同类型的玻璃有可区分的成分特征",
      "justification": "题面前提"
    }
  ],
  "variables": [
    {
      "id": "X",
      "name": "成分向量",
      "description": "SiO2, Na2O, CaO 等含量",
      "unit": "%",
      "role": "input",
      "domain": "X ≥ 0, ΣX = 100%"
    },
    {
      "id": "label",
      "name": "玻璃类型标签",
      "description": "分类目标",
      "unit": "1",
      "role": "state",
      "domain": "离散类别"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "聚类数 K",
      "value_or_source": "待确定",
      "unit": "1",
      "source": "calibrated"
    },
    {
      "id": "p2",
      "name": "主成分保留数",
      "value_or_source": "方差贡献率 > 85%",
      "unit": "1",
      "source": "calibrated"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "各成分含量 ≥ 0 且总和 = 100%",
      "rationale": "化学约束"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "最大化聚类/判别准确率",
      "kind": "maximize",
      "rationale": "分类质量"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "PCA 降维",
      "equation": "Z = X·W (W 为特征向量矩阵)",
      "derivation_notes": "主成分分析"
    },
    {
      "id": "M2",
      "name": "K-means 聚类",
      "equation": "argmin Σ||x_i - μ_k||²",
      "derivation_notes": "欧氏距离聚类"
    }
  ],
  "candidate_models": [
    {
      "model": "PCA + K-means + LDA",
      "pros": "经典组合",
      "cons": "假设正态"
    },
    {
      "model": "t-SNE + DBSCAN",
      "pros": "非线性",
      "cons": "参数敏感"
    }
  ],
  "selected_model": "PCA + K-means + LDA",
  "selection_reason": "高维小样本适用 PCA 降维",
  "uncertainties": [],
  "sensitivity_plan": [],
  "problem_interpretation": "利用化学成分数据对古代玻璃制品进行分类和鉴别，建立聚类和判别模型。"
}
```

**论文要求**：
1. 按照标准数学建模论文格式撰写（摘要、问题重述、模型假设、符号说明、模型建立与求解、模型评价、参考文献）
2. 所有数学公式使用 LaTeX 格式
3. 论文中的所有变量、参数、约束、机制必须与 MODEL_ARTIFACT 完全一致
4. 不得引入 MODEL_ARTIFACT 中未定义的新变量、新约束或新机制
5. 不得修改 MODEL_ARTIFACT 中已有元素的含义或表达式
6. 摘要需概括问题、模型、主要结论
7. 模型假设需列出 MODEL_ARTIFACT 中的所有假设
8. 符号说明需列出 MODEL_ARTIFACT 中的所有变量和参数
9. 模型建立需详细展开 MODEL_ARTIFACT 中的所有机制方程
10. 模型评价需讨论局限性和改进方向

**输出格式**：LaTeX 格式的完整论文