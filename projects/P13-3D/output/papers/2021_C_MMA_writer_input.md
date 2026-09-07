# 数学建模论文撰写

## 题目原文

题目 2021_C

## 匿名建模产物（Identity: Y）

```json
{
  "problem_id": "2021_C",
  "problem_interpretation": "以监督分类（误报概率）为核心、时空扩散预测为背景、预算约束排序为决策出口的五问一体化框架。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "Lab Status 为金标准标签，Unprocessed/Unverified 剔除",
      "justification": "官方分类"
    },
    {
      "id": "A2",
      "statement": "报告时空特征携带可学习信号（报告行为与真实分布相关）",
      "justification": "分类可行的前提"
    },
    {
      "id": "A3",
      "statement": "调查预算 B 为硬约束",
      "justification": "题面 limited resources"
    }
  ],
  "variables": [
    {
      "id": "feat",
      "name": "报告特征向量",
      "description": "经纬度、月份、年度、滞后天数、是否附图、文本 TF-IDF",
      "unit": "1",
      "role": "input",
      "domain": "混合"
    },
    {
      "id": "y",
      "name": "标签",
      "description": "Lab Status 二值化（Positive=1）",
      "unit": "1",
      "role": "input",
      "domain": "{0,1}"
    },
    {
      "id": "p_hat",
      "name": "阳性概率",
      "description": "分类器输出",
      "unit": "1",
      "role": "derived",
      "domain": "[0,1]"
    },
    {
      "id": "S",
      "name": "选中的调查集合",
      "description": "预算内报告子集",
      "unit": "set",
      "role": "decision",
      "domain": "|S| ≤ B"
    },
    {
      "id": "c_t",
      "name": "年度阳性计数",
      "description": "扩散序列",
      "unit": "count",
      "role": "state",
      "domain": "≥0"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "调查预算 B",
      "value_or_source": "题面 limited resources，情景设定",
      "unit": "count",
      "source": "assumed"
    },
    {
      "id": "p2",
      "name": "类别权重 w_pos",
      "value_or_source": "按类频率反比",
      "unit": "1",
      "source": "data"
    },
    {
      "id": "p3",
      "name": "DBSCAN 邻域 ε",
      "value_or_source": "k-距离图肘点",
      "unit": "km",
      "source": "calibrated"
    },
    {
      "id": "p4",
      "name": "根除阈值 k 年",
      "value_or_source": "情景设定 3 年",
      "unit": "yr",
      "source": "assumed"
    },
    {
      "id": "p5",
      "name": "XGBoost 超参",
      "value_or_source": "交叉验证网格",
      "unit": "1",
      "source": "calibrated"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "0 ≤ p_hat ≤ 1",
      "rationale": "概率量"
    },
    {
      "id": "C2",
      "expression": "|S| ≤ B 且 S ⊆ 待审报告集",
      "rationale": "调查资源硬约束"
    },
    {
      "id": "C3",
      "expression": "训练集仅含 Lab Status ∈ {Positive, Negative}",
      "rationale": "标签可得性（Unprocessed/Unverified 剔除）"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "min E[|c_t − ĉ_t|]（扩散外推误差）",
      "kind": "minimize",
      "rationale": "Q1"
    },
    {
      "id": "O2",
      "expression": "max AUC-ROC / PR-AUC（误报判别）",
      "kind": "maximize",
      "rationale": "Q2"
    },
    {
      "id": "O3",
      "expression": "max E[Σ_{i∈S} y_i]（预算内期望阳性发现）",
      "kind": "maximize",
      "rationale": "Q3"
    },
    {
      "id": "O4",
      "expression": "根除判定 = P(阳性率 < 阈值 | 监测努力) > 0.95 连续 3 年",
      "kind": "estimand",
      "rationale": "Q5"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "时空扩散预测",
      "equation": "ĉ_{t+1} = XGBoost(feat_{≤t}) + DBSCAN 加权重心外推",
      "derivation_notes": "留一年验证防泄漏"
    },
    {
      "id": "M2",
      "name": "误报分类",
      "equation": "p_hat = P(y=1 | feat)，随机森林 + 类别加权",
      "derivation_notes": "不平衡主指标 PR-AUC"
    },
    {
      "id": "M3",
      "name": "预算排序",
      "equation": "S* = argmax_{|S|≤B} Σ p_hat_i，空间覆盖 tie-break",
      "derivation_notes": "贪心最优性由排序可加性保证"
    },
    {
      "id": "M4",
      "name": "更新机制",
      "equation": "周级增量再训练 + PSI>0.2 触发全量重训",
      "derivation_notes": "双轨触发"
    },
    {
      "id": "M5",
      "name": "根除证据",
      "equation": "零阳性 k=3 年 且 阳性率 95% 置信上界 < 检出阈值（努力对照）",
      "derivation_notes": "零膨胀计数 + 功效分析"
    }
  ],
  "candidate_models": [
    {
      "model": "XGBoost+DBSCAN（时空）+ 随机森林（分类）",
      "pros": "非线性+可解释重要性",
      "cons": "调参成本"
    },
    {
      "model": "ARIMA（纯时间）+ Logistic",
      "pros": "简单",
      "cons": "丢失空间结构"
    },
    {
      "model": "图像 CNN 辅助分类",
      "pros": "图像信号",
      "cons": "3305 张标注成本高、仅 5% 记录附图"
    }
  ],
  "selected_model": "XGBoost+DBSCAN 时空扩散 + 随机森林误报分类 + 预算贪心排序 + 触发式更新",
  "selection_reason": "多因素非线性时空扩散需树模型+聚类；类别极不平衡决定以 PR-AUC 为主指标与类别加权；预算排序的期望效益目标使 p_hat 排序成为可证明的贪心最优；图像仅覆盖少数记录，首轮不引入 CNN",
  "uncertainties": [
    {
      "source": "报告行为偏差（公众报告率≠丰度）",
      "handling": "scenario",
      "effect": "报告率放大系数情景"
    },
    {
      "source": "标签缺失（Unprocessed/Unverified）",
      "handling": "scenario",
      "effect": "删失比例敏感性"
    },
    {
      "source": "分类器超参与不平衡权重",
      "handling": "propagated",
      "effect": "交叉验证分布"
    },
    {
      "source": "扩散外推",
      "handling": "propagated",
      "effect": "Bootstrap 区间"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "分类阈值",
      "range": "0.3-0.7",
      "metric": "查全率@预算 B"
    },
    {
      "parameter": "预算 B",
      "range": "50-500",
      "metric": "期望阳性发现数曲线"
    },
    {
      "parameter": "类别权重 w_pos",
      "range": "√ratio 至 ratio",
      "metric": "PR-AUC"
    },
    {
      "parameter": "DBSCAN ε",
      "range": "k-距离肘点 ±50%",
      "metric": "簇数/前沿稳定性"
    },
    {
      "parameter": "报告率放大系数",
      "range": "0.5×-2×",
      "metric": "扩散速度估计"
    }
  ]
}
```

---

# 数学建模论文撰写

请根据提供的建模产物，撰写完整的数学建模论文。

## 撰写要求

1. **问题重述**：用自己的语言重新描述题目要求，明确要回答的子问题。
2. **假设**：列出建模产物中明确声明的假设，说明每个假设的合理性。
3. **符号说明**：整理建模产物中的变量和参数，用表格呈现。
4. **模型建立**：
   - 目标函数/估计量：完整写出数学表达式。
   - 约束条件：逐条列出，附物理/工程解释。
   - 机理方程：写出状态转移方程或核心方程组。
   - 模型选择理由：为什么选这个模型而非其他候选。
5. **求解方法**：描述求解思路（数值/解析/仿真），给出算法步骤。

## 格式要求

- 公式用 LaTeX（$$...$$ 或 \[...\]）
- 无实验数据处以"待实验验证"或占位符标注
- 不要编造数据或实验结果
- 中文撰写
- 标题用 `# 建模论文`

## 重要提醒

- 严格基于提供的建模产物撰写，不要自行添加产物中没有的变量、约束或假设。
- 如果产物中缺少某个子问题的模型，如实说明"该子问题的模型待补充"。
- 保持学术论文的客观、严谨风格。

