# 经管（Economics / Management）学科论文模板

> **学科范围**: 经济学（宏观/微观/计量/发展/劳动/金融）、管理学（战略/组织行为/运营/会计/营销）
> **结构范式**: 理论文（Theory）+ 实证论文（Empirical）双轨
> **引用风格**: 作者-年份（Author, Year），字母序
> **推荐 BibTeX 样式**: `aea` / `econometrica` / `plainnat` / `apalike` / `chicago`
> **本模板默认**: `plainnat`（natbib + authoryear，经济学通用）

---

## 一、学科结构特点

经济学与管理学论文有两条主要范式：

1. **理论论文（Theory Paper）**：构建数理模型，推导命题（propositions），辅以数值示例
2. **实证论文（Empirical Paper）**：基于观测数据识别因果效应，重点在识别策略（identification strategy）与稳健性（robustness）

经管论文与理工 IMRaD 的关键差异：

- **引言先呈现结论**：经济学传统（特别是 AEA 系期刊）要求 Introduction 第一段就陈述主要发现与机制，而不像理工那样按 CARS 三语步铺垫
- **理论模型独立成节**：实证论文常含 Theoretical Framework 节，再接 Empirical Strategy
- **识别策略（Identification Strategy）**：实证论文核心，包括 IV / DiD / RDD / RCT / natural experiment
- **稳健性检验（Robustness Checks）**：实证论文必备，多组子节
- **政策含义（Policy Implications）**：经济学顶刊要求明确讨论政策启示
- **数据来源声明**：明确数据提供方、获取方式、清洗代码可复现性

### 1.1 实证经济学论文小节

| 顺序 | 小节 | 功能 |
|------|------|------|
| 1 | Introduction | 第一段直陈结论；之后是文献定位、识别策略、贡献 |
| 2 | Institutional Background | 制度背景（政策/市场环境） |
| 3 | Theoretical Framework | 简化理论模型，推导可检验假说 |
| 4 | Data | 数据来源、样本构造、关键变量定义、描述统计 |
| 5 | Empirical Strategy | 计量模型、识别假设、IV/DiD/RDD 设定 |
| 6 | Results | 主回归 + 异质性 + 机制 |
| 7 | Robustness Checks | 替代样本 / 替代设定 / 安慰剂 / 工具变量诊断 |
| 8 | Discussion / Policy Implications | 政策含义 + 局限 |
| 9 | Conclusion | 贡献回顾 |
| 10 | References | 作者-年份，字母序 |
| — | Appendix | 推导、补充表格 |
| — | Replication Data | 数据 + 代码（多数顶刊强制） |

### 1.2 理论经济学论文小节

| 顺序 | 小节 | 功能 |
|------|------|------|
| 1 | Introduction | 现象 + 已有模型局限 + 本文贡献 |
| 2 | Model | 环境、参与者、信息、行动、均衡概念 |
| 3 | Equilibrium Analysis | 命题 + 证明 |
| 4 | Comparative Statics | 比较静态分析 |
| 5 | Numerical Example | 数值示例 |
| 6 | Discussion | 与已有模型对比 + 拓展 |
| 7 | Conclusion | 总结 |
| 8 | Appendix | 完整证明 |

### 1.3 管理学论文（实证）小节

参照 AMJ / ASQ 风格：

| 顺序 | 小节 | 功能 |
|------|------|------|
| 1 | Introduction | 研究问题 + 贡献 hook |
| 2 | Theory and Hypotheses | 文献综述 + 假设推导 |
| 3 | Methods | 样本、变量、模型 |
| 4 | Results | 主效应 + 调节 + 中介 |
| 5 | Discussion | 贡献 + 局限 + 未来研究 |
| 6 | Conclusion | 实践启示 |

---

## 二、用户自定义扩展点

| 占位注释 | 说明 |
|---------|------|
| `% TODO: lead-finding` | Introduction 第一段直陈主要发现 |
| `% TODO: institutional-background` | 制度背景（经济学实证必备） |
| `% TODO: theoretical-framework` | 理论模型 + 可检验假说 |
| `% TODO: data-sources` | 数据来源、提供方、获取方式 |
| `% TODO: identification` | 识别策略（IV / DiD / RDD / natural experiment） |
| `% TODO: main-regression` | 主回归表 |
| `% TODO: heterogeneity` | 异质性分析 |
| `% TODO: mechanism` | 机制检验 |
| `% TODO: robustness` | 稳健性检验（多重） |
| `% TODO: policy-implications` | 政策含义 |
| `% TODO: replication-data` | 数据 + 代码可复现性声明 |

---

## 三、推荐 BibTeX 样式

| .bst 文件 | 适用领域 | 引用格式 | 排序 |
|----------|---------|---------|------|
| `plainnat` | 通用经管（natbib） | (Author, Year) | 字母序 |
| `apalike` | 管理学（APA 近似） | (Author, Year) | 字母序 |
| `econometrica` | Econometrica 系 | (Author, Year) | 字母序 |
| `aea` | American Economic Association | (Author, Year) | 字母序 |
| `chicago` | Chicago 风格（金融） | (Author Year) | 字母序 |
| `elsarticle-harv` | Elsevier 经管刊 | (Author, Year) | 字母序 |

---

## 四、期刊示例

| 学科 | 顶刊 | BibTeX 样式 |
|------|------|------------|
| 经济学（综合） | American Economic Review | aea |
| 计量经济学 | Econometrica | econometrica |
| 经济学（宏观） | Journal of Political Economy | chicago |
| 经济学（应用） | Quarterly Journal of Economics | chicago |
| 金融学 | Journal of Finance | jfe / chicago |
| 会计学 | The Accounting Review | apalike |
| 营销学 | Journal of Marketing | apalike |
| 战略管理 | Strategic Management Journal | apalike |
| 组织行为 | Academy of Management Journal | apalike |
| 运营管理 | Management Science | apalike / informs |

---

## 五、编译验证

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

模板使用标准 `article` 类 + `plainnat.bst`（TeX Live 内置），开箱即用。
