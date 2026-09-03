# 心理学（Psychology）学科论文模板

> **学科范围**: 实验心理学、认知心理学、发展心理学、社会心理学、临床心理学、心理测量学、认知神经科学
> **结构范式**: 严格 APA 7（Title Page / Abstract / Introduction / Method / Results / Discussion / References / Tables / Figures / Appendices）
> **引用风格**: APA 7（作者-年份，字母序）
> **推荐 BibTeX 样式**: `apalike` / `plainnat`（natbib + authoryear）/ `biblatex-apa`（严格 APA 7）
> **本模板默认**: `apalike`（APA 风格近似，开箱即用）

---

## 一、学科结构特点

心理学是 APA 格式的发源地（American Psychological Association），论文严格遵循 **APA Publication Manual (7th ed.)**。实验心理学论文的特点：

1. **严格 APA 7 结构**：Title Page → Abstract → Introduction（无 "Introduction" 标题）→ Method → Results → Discussion → References → Tables → Figures → Appendices
2. **被试信息（Participants）**：人口学统计 + 招募方式 + 样本量论证（power analysis）+ 退出来源（CONSORT flowchart 风格）
3. **实验设计（Design）**：明确自变量 / 因变量 / 控制变量 + 设计类型（between / within / mixed）
4. **材料（Materials / Stimuli）**：刺激列表、量表来源、计分方式
5. **程序（Procedure）**：实验流程逐步描述 + 随机化方法 + trial 结构
6. **统计报告标准**：效应量（Cohen's d / η² / OR）+ 95% CI + 精确 p 值（APA 7 不再用 p < .05）
7. **预注册（Pre-registration）**：心理学自 2014 年起预注册成为常态（OSF / AsPredicted）
8. **IRB + 知情同意**：所有人类被试研究必备
9. **开放科学（Open Science）**：数据 + 材料 + 预注册 + 代码共享（FAIR 原则）

### 1.1 APA 7 心理学论文小节

| 顺序 | 小节 | 功能 |
|------|------|------|
| 1 | Title Page | 标题、作者、单位、ORCID、通讯方式、字数、图数、表数、冲突声明 |
| 2 | Abstract | 150-250 词，含关键词 |
| 3 | Introduction（无 "Introduction" 标题） | 文献综述 + 研究问题 + 假设推导 |
| 4 | Method | Participants / Design / Materials / Procedure / Data Analysis |
| 5 | Results | 假设逐项检验，含描述统计 + 推断统计 + 效应量 + CI |
| 6 | Discussion | 结果解读 + 理论意义 + 局限 + 未来研究 |
| 7 | References | APA 7 字母序，DOI 必填 |
| 8 | Tables | 每表独立页 |
| 9 | Figures | 每图独立页 |
| 10 | Appendices | 量表、刺激材料、补充分析 |

### 1.2 Method 子节细节（APA 7 强制）

| 子节 | 内容 |
|------|------|
| Participants | $N$、抽样方式、power analysis、人口学统计、IRB 批准号 |
| Research Design | 设计类型（between / within / mixed），自变量（levels），因变量（scale of measurement），控制变量 |
| Materials | 量表（来源 + 计分 + Cronbach α）、刺激（来源 + 选择理由）、设备（型号 + 厂商） |
| Procedure | 知情同意 → 指导语 → 实验任务 → 消融（debriefing），随机化方法，trial 数量 |
| Data Analysis | 主分析模型、效应量指标、缺失数据处理、假设检验 α、软件 + 版本 |

### 1.3 统计报告规范（APA 7 2019 修订）

- **效应量必报**：Cohen's d / Hedges' g / η² / ω² / OR / RR
- **置信区间必报**：95% CI
- **精确 p 值**：p = .034（不再 p < .05），但 p < .001 仍可用
- **零结果报告**：等效性检验 / Bayes 因子推荐

---

## 二、用户自定义扩展点

| 占位注释 | 说明 |
|---------|------|
| `% TODO: hypothesis` | 研究假设 H1, H2, ... |
| `% TODO: participants` | 被试 N、招募、人口学、power analysis |
| `% TODO: design` | 实验设计（between/within/mixed）+ IV/DV |
| `% TODO: materials` | 量表来源 + 信效度 |
| `% TODO: procedure` | 实验流程 + 随机化 + trial 结构 |
| `% TODO: analysis` | 主分析 + 效应量 + 假设检验 |
| `% TODO: effect-size` | Cohen's d / η² + 95% CI |
| `% TODO: irb` | IRB 批准号 + 知情同意方式 |
| `% TODO: preregistration` | 预注册链接（OSF / AsPredicted） |
| `% TODO: open-science` | 数据 / 材料 / 代码共享链接 |
| `% TODO: limitations` | 局限与未来研究 |

---

## 三、推荐 BibTeX 样式

| .bst 文件 | 适用 | 引用格式 | 排序 |
|----------|------|---------|------|
| `apalike` | 心理学（APA 近似） | (Author, Year) | 字母序 |
| `plainnat` | natbib 兼容通用 | (Author, Year) | 字母序 |
| `biblatex-apa` | 严格 APA 7（需 biblatex） | (Author, Year) | 字母序 |

**说明**：`apalike.bst` 与严格 APA 7 仍有差异（如多作者列表、DOI 格式、期刊卷期格式）。如需严格合规，改用 `biblatex` + `\usepackage[style=apa]{biblatex}` + `biber` 编译。

---

## 四、期刊示例

| 学科 | 顶刊 | BibTeX 样式 | 备注 |
|------|------|------------|------|
| 综合心理学 | Psychological Bulletin | apalike | 综述 |
| 实验心理学 | Journal of Experimental Psychology: General | apalike | 实验 |
| 认知心理学 | Cognitive Psychology | apalike | |
| 社会心理学 | Journal of Personality and Social Psychology | apalike | |
| 发展心理学 | Child Development | apalike | SRCD 系 |
| 临床心理学 | Journal of Abnormal Psychology | apalike | |
| 心理科学 | Psychological Science | apalike | APS 系 |
| 认知神经科学 | Journal of Cognitive Neuroscience | apalike | MIT Press |
| 心理测量学 | Psychological Methods | apalike | |

---

## 五、编译验证

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

模板使用标准 `article` 类 + `apalike.bst`（TeX Live 内置），开箱即用。
