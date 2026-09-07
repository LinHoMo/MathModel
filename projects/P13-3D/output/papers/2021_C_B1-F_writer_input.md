# 数学建模论文撰写

## 题目原文

题目 2021_C

## 匿名建模产物（Identity: X）

```json
{
  "problem_id": "2021_C",
  "problem_interpretation": "五问共享一条证据链：报告流 →（纠正报告偏差与标签删失）→ 误报概率 →（预算约束）→ 调查优先级 →（检测努力对照下）→ 根除判定。模型构造的成功标准：五问中的每一问都能指认到本框架中的具体变量/方程（对齐点→变量承载），且所有不确定性显式传播。",
  "assumptions": [
    {
      "id": "A1",
      "statement": "Lab Status ∈ {Positive, Negative} 为金标准标签；Unprocessed/Unverified 为删失观测（非随机缺失，倾向新近报告），训练仅用金标准但删失比例进入偏差敏感性",
      "justification": "官方分类 + 删失机制显式建模"
    },
    {
      "id": "A2",
      "statement": "公众报告强度 λ_report(t) = κ·A(t)·e(t)：与丰度 A 和公众注意力 e(t)（媒体报道驱动的季节性）成正比——报告率≠丰度是本题首要混杂",
      "justification": "报告行为偏差的结构化表述"
    },
    {
      "id": "A3",
      "statement": "目击空间坐标经州政府地址转换，误差为各向同性小噪声",
      "justification": "数据说明"
    },
    {
      "id": "A4",
      "statement": "调查预算 B 为每期硬约束；检测努力（监测强度）在根除判定期不下降",
      "justification": "题面 limited resources + 根除判定的前提"
    }
  ],
  "variables": [
    {
      "id": "feat",
      "name": "报告特征向量",
      "description": "经纬度、月份、年、报告滞后 Δ=Submission−Detection、是否附图、文本 TF-IDF",
      "unit": "1",
      "role": "input",
      "domain": "混合类型"
    },
    {
      "id": "y",
      "name": "金标准标签",
      "description": "Positive=1 / Negative=0（仅金标准子集有定义）",
      "unit": "1",
      "role": "input",
      "domain": "{0,1}"
    },
    {
      "id": "p_hat",
      "name": "真阳性概率",
      "description": "纠正报告偏差后的后验概率",
      "unit": "1",
      "role": "derived",
      "domain": "[0,1]"
    },
    {
      "id": "S",
      "name": "调查队列",
      "description": "当期选送实验室的报告集合",
      "unit": "set",
      "role": "decision",
      "domain": "|S| ≤ B"
    },
    {
      "id": "A_t",
      "name": "隐丰度场",
      "description": "时空格点上的丰度强度（潜变量）",
      "unit": "count",
      "role": "state",
      "domain": "≥0"
    },
    {
      "id": "D_t",
      "name": "累计检测努力",
      "description": "累积调查/监测工时（根除判定的对照变量）",
      "unit": "hr",
      "role": "state",
      "domain": "单调递增"
    }
  ],
  "parameters": [
    {
      "id": "p1",
      "name": "调查预算 B",
      "value_or_source": "每期可送检数量（情景设定）",
      "unit": "count/期",
      "source": "assumed"
    },
    {
      "id": "p2",
      "name": "类别权重 w_pos",
      "value_or_source": "n_neg/n_pos 的平方根（不平衡折中）",
      "unit": "1",
      "source": "data"
    },
    {
      "id": "p3",
      "name": "报告偏差系数 κ 区间",
      "value_or_source": "媒体报道强度文献代理，[0.5, 2] 情景",
      "unit": "1",
      "source": "literature"
    },
    {
      "id": "p4",
      "name": "根除判定参数 (k, α)",
      "value_or_source": "k=3 年、α=0.05（功效分析给出）",
      "unit": "1",
      "source": "assumed"
    },
    {
      "id": "p5",
      "name": "分类器超参数 θ",
      "value_or_source": "分层 5 折交叉验证网格最优",
      "unit": "1",
      "source": "calibrated"
    },
    {
      "id": "p6",
      "name": "时空核带宽",
      "value_or_source": "k-距离/规则带宽（Scott）",
      "unit": "km",
      "source": "calibrated"
    }
  ],
  "constraints": [
    {
      "id": "C1",
      "expression": "p_hat ∈ [0,1]（校准输出经 Platt/isotonic 校准）",
      "rationale": "概率量且需校准才可作决策权重"
    },
    {
      "id": "C2",
      "expression": "|S| ≤ B，S ⊆ 未审报告集",
      "rationale": "预算硬约束"
    },
    {
      "id": "C3",
      "expression": "训练集 C3a：仅 Lab Status ∈ {Positive,Negative}；C3b：时间前滚切分（训练期 < 验证期）",
      "rationale": "标签可得性 + 防时间泄漏"
    },
    {
      "id": "C4",
      "expression": "A_t ≥ 0（用对数高斯过程/泊松自回归保证非负）",
      "rationale": "丰度非负——随机实现不得违反变量域"
    },
    {
      "id": "C5",
      "expression": "根除判定前提：D_t 在判定窗口内单调不降",
      "rationale": "无检测努力对照的零阳性不构成证据"
    }
  ],
  "objective": [
    {
      "id": "O1",
      "expression": "Q1 可预测性 = 前滚验证下 Ŝ_t（时空密度前沿）与实测的 CRPS + 扩散速度估计的 CI",
      "kind": "estimand",
      "rationale": "Q1 要求'可否预测及精度'——用 CRPS 而非单点误差"
    },
    {
      "id": "O2",
      "expression": "Q2 误报模型 = max PR-AUC（主指标）+ Brier（校准）",
      "kind": "maximize",
      "rationale": "极不平衡下 PR-AUC 为主、概率校准为排序的前提"
    },
    {
      "id": "O3",
      "expression": "Q3 优先级 = argmax_{|S|≤B} Σ_{i∈S} p_hat_i，空间分散 tie-break",
      "kind": "maximize",
      "rationale": "期望阳性发现最大化"
    },
    {
      "id": "O4",
      "expression": "Q4 更新 = 增量后验更新频率 argmin（漂移风险, 实验室吞吐成本）",
      "kind": "minimize",
      "rationale": "Q4 更新频率作为权衡而非拍定"
    },
    {
      "id": "O5",
      "expression": "Q5 根除 = P(λ_true < λ_thresh | D_t 不降, 连续 k=3 年零阳性) ≥ 1−α",
      "kind": "estimand",
      "rationale": "根除是'检测努力对照下'的统计判定"
    }
  ],
  "mechanism": [
    {
      "id": "M1",
      "name": "报告观测模型（偏差纠正）",
      "equation": "reports_t ~ Poisson(κ·e(t)·A_t)；log A_t = x_t（时空高斯过程，非负由对数链接保证）",
      "derivation_notes": "干预②③：κ 与 e(t) 把'报告率≠丰度'做成显式观测层；对数链接满足 C4"
    },
    {
      "id": "M2",
      "name": "时空扩散（可预测性）",
      "equation": "log A_{t+1}(x) = ρ·log A_t(x) + v·∇_x log A_t + w_t（平流-扩散核）",
      "derivation_notes": "扩散速度 v 与方向可估计并给 CI（Q1 的'精度'落点）"
    },
    {
      "id": "M3",
      "name": "误报分类（删失感知）",
      "equation": "p_hat = P(y=1|feat) = σ(f_θ(feat))，训练于金标准子集，类别加权 w_pos",
      "derivation_notes": "SHAP 输出特征重要性；Platt 校准到 C1"
    },
    {
      "id": "M4",
      "name": "优先级决策",
      "equation": "S* = argmax_{|S|≤B} Σ_{i∈S} p_hat_i − λ_disp·Σ_{i,j∈S} K_spatial(i,j)",
      "derivation_notes": "空间分散惩罚项 tie-break 防扎堆；贪心最优性由次模性近似保证"
    },
    {
      "id": "M5",
      "name": "根除判定（努力对照）",
      "equation": "P(λ_true ≤ λ* | reports=0, D_t) 用 Poisson 后验：1−e^{−λ*D_t_eff}；连续 k 年零阳性且上界 < λ* 判定成立",
      "derivation_notes": "干预②③：零阳性只有在检测努力对照下才是证据——D_t_eff 进入判定"
    },
    {
      "id": "M6",
      "name": "更新机制（双轨触发）",
      "equation": "每周增量更新；PSI(feat 分布) > 0.2 或 PR-AUC 降幅 > 0.05 → 全量重训",
      "derivation_notes": "更新频率 = 吞吐成本与漂移风险的显式权衡（O4）"
    }
  ],
  "candidate_models": [
    {
      "model": "泊松观测层 + 平流-扩散丰度场 + 删失感知分类（本框架）",
      "pros": "五问同源、偏差显式、判据含努力对照",
      "cons": "潜变量推断实现成本高"
    },
    {
      "model": "XGBoost 时空 + 随机森林分类（轻量替代）",
      "pros": "工程简单",
      "cons": "报告偏差只能情景化、根除判定缺努力对照"
    },
    {
      "model": "图像 CNN 辅助",
      "pros": "图像误报信号",
      "cons": "仅 3305/4440 部分记录附图且标注成本高，列为扩展"
    }
  ],
  "selected_model": "候选1（泊松观测 + 平流-扩散 + 删失感知分类 + 预算决策 + 努力对照根除判定）",
  "selection_reason": "五问同源一根证据链；报告偏差与检测努力两个混杂被显式建模而非讨论；每个对齐点有承载方程",
  "uncertainties": [
    {
      "source": "报告偏差系数 κ 与注意力 e(t)",
      "handling": "propagated",
      "effect": "丰度估计与扩散速度的区间（Q1 精度口径）"
    },
    {
      "source": "标签删失比例",
      "handling": "scenario",
      "effect": "分类器 PR-AUC 的下界敏感性"
    },
    {
      "source": "分类器 θ（交叉验证）",
      "handling": "propagated",
      "effect": "p_hat 的折间分布 → 排序稳健性"
    },
    {
      "source": "扩散参数 (ρ, v, w)",
      "handling": "propagated",
      "effect": "Q1 的 CRPS 与前沿区间"
    },
    {
      "source": "根除判定 (k, α, λ*)",
      "handling": "scenario",
      "effect": "功效分析给出需要的监测强度"
    }
  ],
  "sensitivity_plan": [
    {
      "parameter": "报告偏差 κ",
      "range": "[0.5, 2]（情景）",
      "metric": "丰度场 CRPS、扩散速度 CI 宽度"
    },
    {
      "parameter": "删失比例",
      "range": "实际值 ±50%",
      "metric": "PR-AUC 下界"
    },
    {
      "parameter": "分类阈值/预算 B",
      "range": "阈值 0.3-0.7 × B 50-500 网格",
      "metric": "期望阳性发现数曲线"
    },
    {
      "parameter": "判定参数 (k, α)",
      "range": "k∈{2,3,4}, α∈{0.01,0.05}",
      "metric": "所需监测强度 D_t_eff"
    },
    {
      "parameter": "时空核带宽",
      "range": "Scott 规则 ±50%",
      "metric": "前沿稳定性"
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

