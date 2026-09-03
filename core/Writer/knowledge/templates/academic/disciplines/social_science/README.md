# 社科（Social Science）学科论文模板

> **学科范围**: 社会学、人类学、政治学、传播学、社会工作、公共政策、定性研究方法学
> **结构范式**: 分叉结构 —— 定量研究（APA-IMRaD）/ 定性研究（生成性主题式）
> **引用风格**: APA 7（作者-年份，字母序），偶尔 Chicago author-date
> **推荐 BibTeX 样式**: `apalike` / `plainnat`（natbib + authoryear）/ `biblatex-apa`
> **本模板默认**: `apalike`（natbib + authoryear，APA 风格近似）

---

## 一、学科结构特点

社科论文最大的特点是 **方法论分叉**：定量研究沿用 APA-IMRaD 结构（同心理学），定性研究则采用更具生成性的结构。本模板在同一文件内提供两条分支，由用户根据方法论选择启用其一。

### 1.1 定量研究分支（Quantitative）

参照 APA Publication Manual (7th ed.)：

| 顺序 | 小节 | 功能 |
|------|------|------|
| 1 | Title Page | 标题、作者、单位、ORCID、通讯方式、字数 |
| 2 | Abstract | 150-250 词，含关键词 |
| 3 | Introduction（无 "Introduction" 标题） | 文献综述 + 假设推导（CARS 模型） |
| 4 | Method | Participants / Design / Measures / Procedure |
| 5 | Results | 描述统计 + 推断统计 + 假设检验 |
| 6 | Discussion | 结果解读 + 局限 + 未来研究 + 理论/实践意义 |
| 7 | References | APA 7 字母序 |
| 8 | Appendix | 量表、刺激材料 |

### 1.2 定性研究分支（Qualitative）

定性研究不强制 IMRaD，常采用主题式结构（Braun & Clarke 2006 主题分析 6 阶段）：

| 顺序 | 小节 | 功能 |
|------|------|------|
| 1 | Introduction | 现象、研究问题、立场声明（reflexivity） |
| 2 | Literature Review | 既有概念框架 + 缺口 |
| 3 | Methodology | 范式（建构主义/诠释主义）+ 方法（访谈/焦点小组/民族志）+ 抽样 + 分析（主题分析/扎根理论）+ 信效度（信任度 / Lincoln & Guba） |
| 4 | Findings | 主题树式呈现（每个主题：引文 + 诠释） |
| 5 | Discussion | 与既有文献对话 + 理论贡献 + 反身性 |
| 6 | Conclusion | 实践/政策意义 + 局限 |
| 7 | References | APA 7 |
| 8 | Appendix | 访谈转录（interview transcripts）、编码本 |

### 1.3 社科特有要素

1. **IRB / 伦理声明**：知情同意、隐私保护、脆弱人群保护
2. **反身性声明（Reflexivity Statement）**：研究者立场、潜在偏见、与被研究对象的关系（定性研究必备）
3. **访谈转录附录**：定性研究的原始材料透明性
4. **效度证据**：定量研究的构念效度（CFA）、内部一致性（Cronbach α）、重测信度
5. **信任度（Trustworthiness）**：定性研究的 Lincoln & Guba 四标准（credibility / transferability / dependability / confirmability）

---

## 二、用户自定义扩展点

打开 `main.tex` 后，先在 preamble 选择分支：
- **定量**：保留 `\section{Method}` / `\section{Results}` / `\section{Discussion}` 三节
- **定性**：将上述三节替换为 `\section{Methodology}` / `\section{Findings}` / `\section{Discussion}` 节，并展开访谈转录附录

| 占位注释 | 说明 |
|---------|------|
| `% TODO: research-paradigm` | 定性：声明建构主义/诠释主义/批判主义立场 |
| `% TODO: hypothesis` | 定量：列出 H1, H2, ... |
| `% TODO: participants` | 被试招募、抽样（目的抽样/雪球抽样）、样本量论证 |
| `% TODO: measures` | 量表来源、计分、信效度证据 |
| `% TODO: procedure` | 数据收集流程（访谈提纲 / 问卷发放） |
| `% TODO: analysis-quant` | 定量：ANOVA / 回归 / SEM |
| `% TODO: analysis-qual` | 定性：主题分析 6 阶段 / 扎根理论开放-轴心-选择编码 |
| `% TODO: themes` | 定性：主题树 + 受访者引文（编号 P1, P2, ...） |
| `% TODO: reflexivity` | 定性：研究者立场与潜在偏见 |
| `% TODO: irb` | IRB 批准号 + 知情同意方式 |
| `% TODO: transcripts` | 附录访谈转录 |

---

## 三、推荐 BibTeX 样式

| .bst 文件 | 适用领域 | 引用格式 | 排序 |
|----------|---------|---------|------|
| `apalike` | 社科 / 心理学 / 教育学（APA 风格近似） | (Author, Year) | 字母序 |
| `plainnat` | natbib 兼容通用风格 | (Author, Year) | 字母序 |
| `biblatex-apa` | 严格 APA 7（需 biblatex） | (Author, Year) | 字母序 |
| `chicago` / `chicagoa` | Chicago 风格（人类学 / 历史社会学） | (Author Year) | 字母序 |
| `asa` | 美国社会学会风格 | (Author Year) | 字母序 |

切换方法：修改 `\bibliographystyle{apalike}` 一行；如需严格 APA 7，改用 `biblatex` + `\usepackage[style=apa]{biblatex}`。

---

## 四、期刊示例

| 学科 | 顶刊 | BibTeX 样式 |
|------|------|------------|
| 社会学（定量） | American Sociological Review | asa |
| 社会学（定性） | Qualitative Research | apalike |
| 政治学 | American Political Science Review | apalike / chicago |
| 传播学 | Journal of Communication | apalike |
| 公共政策 | Policy Studies Journal | apalike |
| 人类学 | American Anthropologist | chicago |
| 社会工作 | Social Service Review | apalike |

---

## 五、编译验证

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

模板使用标准 `article` 类 + `apalike.bst`（TeX Live 内置），开箱即用。
