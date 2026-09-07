# 理工（STEM）学科论文模板

> **学科范围**: 科学（Science）、技术（Technology）、工程（Engineering）、数学（Mathematics）、计算机科学（CS）、物理、化学、材料、机械、电子、自动化等
> **结构范式**: 标准 IMRaD（Introduction / Methods / Results and Discussion）
> **引用风格**: 数字编号 [1], [2], [3]-[5]
> **推荐 BibTeX 样式**: `IEEEtran` / `elsarticle-num` / `ACM-Reference-Format` / `siamplain` / `unsrtnat`
> **本模板默认**: `IEEEtran`（数字编号，引用顺序排序）

---

## 一、学科结构特点

理工科论文几乎统一采用 **IMRaD 结构**（Introduction, Methods, Results, and Discussion），该结构由 American National Standards Institute（ANSI）于 1972 年标准化（ANSI Z39.16-1972）。本模板在标准 IMRaD 基础上扩展以下理工科特有要素：

1. **算法伪代码（Algorithm Pseudocode）**：CS / OR / 控制领域必备，使用 `algorithm` + `algorithmic` 环境呈现
2. **实验细节（Experimental Setup）**：明确数据集、baseline、评估指标、硬件环境
3. **可复现性声明（Reproducibility Statement）**：代码/数据/超参/随机种子可获取性声明
4. **消融实验（Ablation Study）**：剥离组件验证各模块贡献
5. **统计显著性检验**：t-test / Wilcoxon / bootstrap 置信区间

### 1.1 IMRaD 标准小节

| 顺序 | 小节 | 功能 | 篇幅占比 |
|------|------|------|---------|
| 1 | Abstract | 问题 / 方法 / 关键结果 / 意义（150-250 词） | ~3% |
| 2 | Introduction | 背景 → 缺口 → 贡献 → 路线图（CARS 模型） | ~15% |
| 3 | Related Work | 按方法聚类对比，定位贡献 | ~10% |
| 4 | Methods / System Model | 问题形式化、记号、模型假设、算法 | ~20% |
| 5 | Experiments / Results | 实验设置、主结果、消融、统计检验 | ~30% |
| 6 | Discussion | 结果解读、与相关工作对比、局限性 | ~10% |
| 7 | Conclusion | 贡献回顾 + 未来工作 | ~5% |
| 8 | References | 数字编号，按引用顺序 | — |

### 1.2 CARS 模型（Swales 1990）应用于 Introduction

引言遵循 Swales 提出的 **Create A Research Space** 三语步模型：

- **Move 1 — Establish a territory**：声称研究领域重要性，综述近期研究
- **Move 2 — Establish a niche**：指出已有研究的缺口 / 矛盾 / 局限
- **Move 3 — Occupy the niche**：陈述本文目的、贡献、路线图

---

## 二、用户自定义扩展点

打开 `main.tex` 后，请按以下占位注释逐项替换：

| 占位注释 | 说明 |
|---------|------|
| `% TODO: title` | 论文标题 |
| `% TODO: authors` | 作者列表与单位 |
| `% TODO: abstract` | 150-250 词摘要 |
| `% TODO: keywords` | 4-6 个关键词 |
| `% TODO: intro-CARS` | 按 CARS 三语步撰写引言 |
| `% TODO: related-work` | 按方法聚类综述 |
| `% TODO: method` | 形式化、算法、复杂度 |
| `% TODO: experiment-setup` | 数据集 / baseline / 指标 / 硬件 |
| `% TODO: results` | 主结果 + 消融 + 统计检验 |
| `% TODO: reproducibility` | 代码仓库链接 / DOI / 随机种子 |
| `% TODO: limitations` | 局限性与未来工作 |

### 可选扩展

- **理论证明**：在 Methods 后增加 `Appendix: Proofs` 节，使用 `amsthm` 的 `theorem`/`lemma`/`proof` 环境
- **复杂网络图**：用 `tikz` + `positioning` 库绘制系统架构
- **大表格**：跨栏使用 `table*` + `booktabs`
- **超链接**：取消注释 `hyperref` 加载行

---

## 三、推荐 BibTeX 样式

| .bst 文件 | 适用领域 | 引用格式 | 排序 |
|----------|---------|---------|------|
| `IEEEtran` | 工程 / 电子 / 计算机 | [1], [2], [3]-[5] | 引用顺序 |
| `ACM-Reference-Format` | 计算机（ACM 系） | [1] | 引用顺序 |
| `elsarticle-num` | 工程 / 材料（Elsevier 系） | [1] | 引用顺序 |
| `siamplain` | 数学 / 应用数学 | [1] | 字母序 |
| `unsrtnat` | 通用数字风格 | [1] | 引用顺序 |
| `plainnat` / `abbrvnat` | 通用（natbib 兼容） | [1] 或 (Author, Year) | 字母序 |

切换方法：修改 `\bibliographystyle{IEEEtran}` 一行即可。

---

## 四、期刊示例

| 学科 | 顶刊 / 顶会 | BibTeX 样式 |
|------|-----------|------------|
| 电子电气 | IEEE Transactions on Signal Processing | IEEEtran |
| 计算机 | ACM Computing Surveys / NeurIPS / ICML | ACM-Reference-Format |
| 物理 | Physical Review Letters | revtex4-2 |
| 材料 | Acta Materialia（Elsevier） | elsarticle-num |
| 数学 | SIAM Journal on Applied Mathematics | siamplain |
| 机械 | Journal of Mechanical Design（ASME） | asmejour |
| 化学 | ACS Nano / JACS | achemso |

---

## 五、编译验证

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

模板使用标准 `article` 类 + `IEEEtran.bst`，在标准 TeX Live / MiKTeX 下开箱即用，无需额外下载。
