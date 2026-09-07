# 教育学（Education）学科论文模板

> **学科范围**: 教育学、课程与教学论、教育技术、特殊教育、教育领导力、教师教育、高等教育研究
> **结构范式**: APA 7 + 教育干预设计 + 学习成效评估
> **引用风格**: APA 7（作者-年份，字母序）
> **推荐 BibTeX 样式**: `apalike` / `plainnat`（natbib + authoryear）/ `biblatex-apa`
> **本模板默认**: `apalike`（APA 风格近似，开箱即用）

---

## 一、学科结构特点

教育学论文严格遵循 **APA Publication Manual (7th ed.)**，与心理学同源。教育学研究的特点是聚焦"干预-评估"逻辑：

1. **教育干预设计（Intervention Design）**：基于学习科学理论设计教学干预，明确理论机制（theory of change）
2. **学习成效评估（Learning Outcomes Assessment）**：使用标准化测试 / 自报告 / 过程数据多源测量
3. **准实验设计（Quasi-Experimental Design）**：教育情境难做 RCT，多采用 DiD / matching / 阶梯 wedge 设计
4. **多层级数据（Multilevel Data）**：学生嵌套于班级，班级嵌套于学校，需多层线性模型（HLM）
5. **效应量报告（Effect Size）**：Cohen's d / Hedges' g，APA 7 强制
6. **IRB 与知情同意**：未成年人需家长同意 + 儿童赞同（assent）
7. **预注册（Pre-registration）**：教育研究正在向预注册转向（e.g. SREE, OSF）

### 1.1 APA 7 教育学论文小节

| 顺序 | 小节 | 功能 |
|------|------|------|
| 1 | Title Page | 标题、作者、单位、ORCID、通讯方式 |
| 2 | Abstract | 150-250 词 |
| 3 | Introduction（无 "Introduction" 标题） | 文献综述 + 干预理论机制 + 研究问题/假设 |
| 4 | Method | Participants / Research Design / Intervention / Measures / Procedure / Analysis |
| 5 | Results | 描述统计 + 主分析 + 调节 + 中介 + 效应量 |
| 6 | Discussion | 结果解读 + 理论贡献 + 实践意义 + 局限 + 未来研究 |
| 7 | References | APA 7 字母序 |
| 8 | Appendix | 干预材料、量表、编码手册 |

### 1.2 教育学特有要素

- **干预描述（Intervention Description）**：按 WhatWorks Clearinghouse 教学干预报告标准（WWC Standards 4.0）
- **理论机制（Theory of Change）**：干预为何有效的理论路径
- **忠实度（Fidelity of Implementation）**：干预实施忠实度测量
- **多层线性模型（HLM）**：处理嵌套数据的标准方法
- **实践意义（Practical Implications）**：对教师、学校、政策制定者的具体建议

---

## 二、用户自定义扩展点

| 占位注释 | 说明 |
|---------|------|
| `% TODO: research-question` | 研究问题 + 假设 H1, H2, ... |
| `% TODO: theory-of-change` | 干预的理论机制图 |
| `% TODO: participants` | 学校 / 班级 / 学生抽样，N 嵌套结构 |
| `% TODO: intervention` | 干预组与对照组详细描述 |
| `% TODO: fidelity` | 实施忠实度测量方法 |
| `% TODO: measures` | 学习成效 / 态度 / 过程数据量表 |
| `% TODO: procedure` | 前测-干预-后测-延迟后测时间线 |
| `% TODO: analysis` | HLM / DiD / moderation / mediation |
| `% TODO: effect-size` | Cohen's d / Hedges' g + 95% CI |
| `% TODO: practical-implications` | 对教师与政策制定者的建议 |
| `% TODO: irb` | IRB 批准 + 家长同意 + 儿童赞同 |
| `% TODO: preregistration` | 预注册链接（OSF / SREE） |

---

## 三、推荐 BibTeX 样式

| .bst 文件 | 适用 | 引用格式 | 排序 |
|----------|------|---------|------|
| `apalike` | 教育学（APA 近似） | (Author, Year) | 字母序 |
| `plainnat` | natbib 兼容通用 | (Author, Year) | 字母序 |
| `biblatex-apa` | 严格 APA 7（需 biblatex） | (Author, Year) | 字母序 |

---

## 四、期刊示例

| 学科 | 顶刊 | BibTeX 样式 |
|------|------|------------|
| 教育研究 | American Educational Research Journal | apalike |
| 教育心理学 | Journal of Educational Psychology | apalike |
| 教育技术 | Computers & Education | apalike |
| 高等教育 | Journal of Higher Education | apalike |
| 课程与教学 | Curriculum Inquiry | apalike |
| 教育政策 | Educational Evaluation and Policy Analysis | apalike |
| 特殊教育 | Exceptional Children | apalike |

---

## 五、编译验证

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

模板使用标准 `article` 类 + `apalike.bst`（TeX Live 内置），开箱即用。
