# 医学（Medicine）学科论文模板

> **学科范围**: 临床医学、流行病学、公共卫生、护理学、药学、生物医学
> **结构范式**: IMRaD + Ethics 声明 + 临床试验注册号 + CONSORT/STROBE 报告规范检查表
> **引用风格**: Vancouver（数字编号，引用顺序），上标或行内 [1]
> **推荐 BibTeX 样式**: `vancouver` / `unsrtnat` / `nature`（Nature 系）/ `elsarticle-vancouver`
> **本模板默认**: `vancouver`（医学通用，ICMJE 推荐）

---

## 一、学科结构特点

医学论文沿用 IMRaD，但国际医学期刊编辑委员会（ICMJE，即"温哥华小组"）在 Recommendations for the Conduct, Reporting, Editing, and Publication of Scholarly Work in Medical Journals 中规定了额外的报告要素。本模板在 IMRaD 基础上扩展：

1. **结构化摘要（Structured Abstract）**：Background / Methods / Results / Conclusions 四段式（ICMJE 推荐，多数医学期刊强制）
2. **Ethics 声明**：IRB / 伦理委员会批准号 + 知情同意（informed consent）声明
3. **临床试验注册号（Trial Registration）**：ICMJE 自 2005 年强制要求所有 RCT 在患者入组前于 ICTRP / ClinicalTrials.gov 注册
4. **CONSORT 检查表**（CONSORT 2010 Statement，Schulz et al. BMJ 2010）：随机对照试验（RCT）报告的 25 项条目检查表
5. **STROBE 检查表**（STROBE Statement, von Elm et al. PLoS Med 2007）：观察性研究（队列 / 病例对照 / 横断面）报告的 22 项条目检查表
6. **PRISMA 检查表**（针对系统综述/Meta 分析）
7. **数据共享声明**（ICMJE 2018 起建议）

### 1.1 IMRaD + 医学特化小节

| 顺序 | 小节 | 功能 |
|------|------|------|
| 1 | Title | 含研究设计标识（"A Randomized Controlled Trial" / "A Cohort Study"） |
| 2 | Structured Abstract | Background / Methods / Results / Conclusions，200-300 词 |
| 3 | Introduction | 背景 + 知识缺口 + 研究目的 |
| 4 | Methods | 研究设计、Setting、Participants、Intervention、Outcomes、Sample size、Randomisation、Blinding、Statistical analysis、Ethics、Trial registration |
| 5 | Results | 流程图（CONSORT flow diagram）、基线特征、主结局、次结局、不良事件 |
| 6 | Discussion | 主要发现、与文献对比、机制、局限性、普遍性、结论 |
| 7 | References | Vancouver 数字编号 |
| — | Supplementary | CONSORT / STROBE 检查表（附件） |

### 1.2 三大报告规范对照

| 规范 | 适用研究类型 | 条目数 | 关键参考 |
|------|------------|-------|---------|
| CONSORT 2010 | 随机对照试验（RCT） | 25 | Schulz KF, Altman DG, Moher D. BMJ 2010;340:c332 |
| STROBE | 观察性研究（队列 / 病例对照 / 横断面） | 22 | von Elm E, et al. PLoS Med 2007;4(10):e296 |
| PRISMA 2020 | 系统综述 / Meta 分析 | 27 | Page MJ, et al. BMJ 2021;372:n71 |

---

## 二、用户自定义扩展点

| 占位注释 | 说明 |
|---------|------|
| `% TODO: title` | 标题需含研究设计（如 "A Randomized Controlled Trial"） |
| `% TODO: structured-abstract` | Background / Methods / Results / Conclusions 四段 |
| `% TODO: trial-registration` | ClinicalTrials.gov NCT 号 + 注册日期 |
| `% TODO: ethics` | IRB 批准号 + 知情同意方式 |
| `% TODO: participants` | 入排标准、招募方式、setting |
| `% TODO: intervention` | 干预组与对照组详细描述 |
| `% TODO: outcomes` | 主要终点 + 次要终点 + 测量时点 |
| `% TODO: sample-size` | 样本量计算（检验效能、α、效应量） |
| `% TODO: randomisation` | 随机化方法、分配隐藏、盲法 |
| `% TODO: statistical-analysis` | 主要分析、亚组分析、缺失数据处理 |
| `% TODO: consort-flow` | CONSORT 流程图 |
| `% TODO: adverse-events` | 不良事件报告 |
| `% TODO: data-sharing` | ICMJE 数据共享声明 |

---

## 三、推荐 BibTeX 样式

| .bst 文件 | 适用期刊 | 引用格式 |
|----------|---------|---------|
| `vancouver` | NEJM / Lancet / JAMA / BMJ / ICMJE 系 | [1] 数字编号，引用顺序 |
| `nature` | Nature Medicine / Nature 子刊 | 上标数字 |
| `elsarticle-vancouver` | Elsevier 医学刊 | [1] 数字编号 |
| `unsrtnat` | 通用 Vancouver 替代 | [1] 引用顺序 |

医学期刊普遍要求 **Vancouver 风格**（ICMJE 推荐）：参考文献按引用先后编号，正文以方括号 [1] 或上标引用，作者列表前 6 名后接 "et al."。

---

## 四、期刊示例

| 期刊 | 影响因子（2024） | BibTeX 样式 | 报告规范 |
|------|----------------|------------|---------|
| New England Journal of Medicine (NEJM) | ~176 | vancouver | CONSORT |
| The Lancet | ~169 | vancouver | CONSORT / PRISMA |
| JAMA | ~63 | vancouver | CONSORT |
| BMJ | ~93 | vancouver | CONSORT / STROBE |
| Nature Medicine | ~82 | nature | CONSORT |
| PLOS Medicine | ~15 | vancouver | CONSORT / STROBE / PRISMA |

---

## 五、编译验证

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

模板使用标准 `article` 类 + `vancouver.bst`（TeX Live 内置），开箱即用。
