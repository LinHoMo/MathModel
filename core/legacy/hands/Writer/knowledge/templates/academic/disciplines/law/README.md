# 法学（Law）学科论文模板

> **学科范围**: 法学（普通法 / 大陆法 / 比较法 / 国际法 / 跨学科法学）
> **结构范式**: IRAC（Issue / Rule / Application / Conclusion）+ 法评文章结构（law review article）
> **引用风格**: Bluebook（美）/ OSCOLA（英）/ AGLC（澳）；脚注为主
> **推荐 BibTeX 样式**: `oscola` / `bluebook`（非标准 .bst，多用 biblatex 风格）/ `plain`
> **本模板默认**: `plain` + `footnote` 引用（通用可编译）

---

## 一、学科结构特点

法学论文与 IMRaD 截然不同。法学学术论文主要有两类：

1. **法律评析文章（Law Review Article）**：长篇（8000-30000 词），围绕一个法律问题展开 doctrinal analysis
2. **法律备忘录 / 案例分析（Legal Memo / Case Note）**：严格遵循 IRAC 框架

### 1.1 IRAC 框架

IRAC 是法学教育与执业中通用的法律分析框架，源自美国法学院教育传统（Harvard Case Method），并被普通法系广泛采用：

| 字母 | 含义 | 功能 |
|------|------|------|
| **I** | Issue | 识别法律争议（"Whether...?"） |
| **R** | Rule | 陈述相关法律规则（制定法 / 判例 / 学理） |
| **A** | Application | 将规则适用于本案事实（类比区分 precedent） |
| **C** | Conclusion | 得出结论并指出遗留问题 |

**变体**：IRAC → CREAC（Conclusion, Rule, Explanation, Application, Conclusion）→ CRAC（Conclusion, Rule, Application, Conclusion）→ FIRAC（Facts, Issue, Rule, Application, Conclusion）

### 1.2 法评文章结构（Law Review Article）

参照 Harvard Law Review / Yale Law Journal 风格：

| 顺序 | 小节 | 功能 |
|------|------|------|
| 1 | Introduction | 提出法律问题 + 论点路线图 |
| 2 | Background | 现行法律框架（制定法 + 判例）梳理 |
| 3 | The Problem | 现行法律的缺陷 / 矛盾 / 不确定 |
| 4 | Proposed Solution | 立法 / 司法 / 行政建议 |
| 5 | Analysis / Application | 将建议适用于假设案例，对比现行法 |
| 6 | Counter-arguments | 回应反对意见 |
| 7 | Implications | 对相邻法律领域的影响 |
| 8 | Conclusion | 重申论点 |

### 1.3 法学特有要素

1. **大量脚注（Footnotes）**：法学论文正文简练，几乎所有引用与推论都进脚注；典型法评文章脚注占总篇幅 30-50%
2. **案例引用格式**：Bluebook（美，e.g. *Brown v. Board of Education*, 347 U.S. 483 (1954)）/ OSCOLA（英，e.g. *Donoghue v Stevenson* [1932] AC 562）
3. **制定法引用**：e.g. 42 U.S.C. § 1983 (2018)
4. **_signals**：[no signal] / see / see also / cf. / but see / contra
5. **Id. / Supra / Infra**：交叉引用缩写

---

## 二、用户自定义扩展点

| 占位注释 | 说明 |
|---------|------|
| `% TODO: issue` | 法律争议（"Whether..."问句） |
| `% TODO: rule` | 相关法律规则（制定法条款 + 判例原则） |
| `% TODO: application` | 规则适用于事实，类比区分 precedent |
| `% TODO: counter-argument` | 反对意见与回应 |
| `% TODO: conclusion` | 结论与遗留问题 |
| `% TODO: bluebook-citation` | 案例与制定法的 Bluebook 引用 |
| `% TODO: footnote-discussion` | 脚注中的学理讨论（同引） |

---

## 三、推荐 BibTeX 样式

| .bst / 风格 | 适用 | 引用格式 | 备注 |
|----------|------|---------|------|
| `oscola` | 英国法学（OSCOLA 4th ed.） | 脚注数字 + 作者-年份 | biblatex 风格 |
| `bluebook` | 美国法学（Bluebook 21st ed.） | 脚注 + *Case* 1 U.S. 1 (year) | biblatex 风格（非官方） |
| `plain` + 手动脚注 | 通用法学（最低门槛） | 数字脚注 | 本模板默认 |
| `aglc` | 澳大利亚法学（AGLC 4th ed.） | 脚注 + AGLC 格式 | biblatex 风格 |

**重要说明**：法学论文的脚注引用多为手工编辑（含 signals、Id.、cross-reference），现有 BibTeX .bst 难以完全自动化。建议：
- 投稿时按目标期刊的官方 Bluebook / OSCOLA / AGLC 手册逐条核对脚注
- 使用 `biblatex` + `style=oscola`（OSCOLA 4th）或 `style=british-legal` 简化自动化

---

## 四、期刊示例

| 法系 | 顶刊 | 引用风格 |
|------|------|---------|
| 美国法 | Harvard Law Review | Bluebook |
| 美国法 | Yale Law Journal | Bluebook |
| 英国法 | Law Quarterly Review | OSCOLA |
| 国际法 | American Journal of International Law | Bluebook |
| 比较法 | American Journal of Comparative Law | Bluebook |
| 澳大利亚法 | Melbourne University Law Review | AGLC |
| 欧盟法 | Common Market Law Review | 非标准 |

---

## 五、编译验证

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

模板使用标准 `article` 类 + `plain.bst`（TeX Live 内置），开箱即用。脚注采用 `\footnote{}` + 手动 Bluebook/OSCOLA 格式，无需额外 .bst 文件。
