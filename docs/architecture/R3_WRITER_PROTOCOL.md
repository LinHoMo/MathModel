# R3 Writer Protocol — FROZEN v2

**Status**: FROZEN v2 (2026-09-07) — v1 作废于 R3.2
**Purpose**: R3.2 Structure-Preserving Model-to-Paper Transmission Intervention (Real Writer, Paired)

> **v2 变更（相对 v1）**
> 1. W0 不再复用 R2 模板产物；48 篇全部由真实 Writer 重新生成。
> 2. 每个 (question, arm) 单元的 **W0 → W1 必须背靠背连续生成**（同一批次、同一 Writer、同一参数）。
> 3. 旧模板 W0/W1 与 R3.1 pilot 8 篇标记为 `non-confirmatory`，排除出假设检验。
> 4. 新增 H18 Core Preservation guard。
> 5. 生成执行细则见 `projects/P13-3D-R3/GENERATION_SPEC.md`。
> 6. 预注册见 `docs/architecture/R3_2_REAL_WRITER_PREREG.md`。

## 1. Writer Model

| Parameter | Value |
|---|---|
| Model | GPT-4o (or Claude 3.5 Sonnet) |
| Version | 2026-09 snapshot |
| Temperature | 0.3 |
| Max tokens | 4096 |
| Top-p | 0.95 |
| Frequency penalty | 0.0 |
| Presence penalty | 0.0 |
| Seed | 42 (if supported) |

## 2. System Prompt (W0)

```
你是一个数学建模竞赛论文撰写专家。请根据以下模型构件，撰写一篇完整的数学建模竞赛论文。

要求：
1. 论文必须包含以下章节：摘要、问题重述、模型假设、符号说明、模型建立与求解、模型评价、结论
2. 所有数学公式必须使用 LaTeX 格式
3. 论文必须包含候选模型对比、选定模型说明、灵敏度分析
4. 论文长度：15-20 页
5. 语言：中文
```

## 3. System Prompt (W1)

```
你是一个数学建模竞赛论文撰写专家。请根据以下模型构件和结构化映射，撰写一篇完整的数学建模竞赛论文。

要求：
1. 论文必须包含以下章节：摘要、问题重述、模型假设、符号说明、模型建立与求解、模型评价、结论
2. 所有数学公式必须使用 LaTeX 格式
3. 论文必须包含候选模型对比、选定模型说明、灵敏度分析
4. 论文长度：15-20 页
5. 语言：中文
6. 严格按照结构化映射组织论文结构
```

## 4. User Prompt Template (W0)

```
## 模型构件

### 变量
{variables}

### 参数
{parameters}

### 机制
{mechanism}

### 目标
{objective}

### 约束
{constraints}

### 假设
{assumptions}

### 候选模型
{candidate_models}

### 选定模型
{selected_model}

### 灵敏度计划
{sensitivity_plan}

## 论文要求
请根据以上模型构件，撰写一篇完整的数学建模竞赛论文。
```

## 5. User Prompt Template (W1)

```
## 模型构件

### 变量
{variables}

### 参数
{parameters}

### 机制
{mechanism}

### 目标
{objective}

### 约束
{constraints}

### 假设
{assumptions}

### 候选模型
{candidate_models}

### 选定模型
{selected_model}

### 灵敏度计划
{sensitivity_plan}

## 结构化映射

### 论文章节结构
{section_map}

### 元素映射
{element_map}

### 主张清单
{claim_inventory}

### 候选模型映射
{candidate_model_map}

### 灵敏度映射
{sensitivity_map}

## 论文要求
请根据以上模型构件和结构化映射，撰写一篇完整的数学建模竞赛论文。
严格按照结构化映射组织论文结构，确保每个模型构件都在论文中有对应章节。
```

## 6. Paper Template

```latex
\documentclass[12pt,a4paper]{article}
\usepackage[utf-8]{inputenc}
\usepackage{amsmath,amssymb}
\usepackage{geometry}
\geometry{margin=2.5cm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{hyperref}

\title{TITLE}
\author{数学建模竞赛参赛队}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
ABSTRACT
\end{abstract}

\section{问题重述}
PROBLEM_RESTATEMENT

\section{模型假设}
ASSUMPTIONS

\section{符号说明}
SYMBOLS

\section{模型建立与求解}
MODEL_BUILDING

\section{候选模型对比}
CANDIDATE_MODELS

\section{选定模型}
SELECTED_MODEL

\section{灵敏度分析}
SENSITIVITY

\section{模型评价}
MODEL_EVALUATION

\section{结论}
CONCLUSION

\end{document}
```

## 7. Generation Parameters

| Parameter | W0 | W1 |
|---|---|---|
| Temperature | 0.3 | 0.3 |
| Max tokens | 4096 | 4096 |
| Top-p | 0.95 | 0.95 |
| Seed | 42 | 42 |
| Model | GPT-4o | GPT-4o |
| System prompt | W0 prompt | W1 prompt |
| User prompt | Artifact only | Artifact + Mapping |

## 8. Frozen Files

| File | SHA256 | Status |
|---|---|---|
| `R3_WRITER_PROTOCOL.md` | (this file) | FROZEN |
| `R3_W0_PROMPT_TEMPLATE.md` | (to be frozen) | FROZEN |
| `R3_W1_PROMPT_TEMPLATE.md` | (to be frozen) | FROZEN |
| `R3_EXPERIMENT_RUNNER.py` | (to be frozen) | FROZEN |

## 9. Experimental Controls

1. **Same Writer**: W0 and W1 use identical model, temperature, seed, system prompt structure
2. **Only Variable**: Mapping Layer presence (W0=no mapping, W1=with mapping)
3. **Frozen Artifacts**: All 24 artifacts are frozen from R2
4. **Frozen Mappings**: All 24 mappings are frozen from R3 Phase 2
5. **Nopeek**: W0 generated first, frozen, then W1 generated
6. **Blind Evaluation**: Paper Quality evaluated blind to condition

## 10. Hypotheses

| ID | Hypothesis | Criterion |
|---|---|---|
| H13 | STC_meta(W1) - STC_meta(W0) ≥ 15pp | Meta-model coverage improvement |
| H14 | PQ(W1) - PQ(W0) ≥ 0.5 | Paper quality improvement |
| H15 | (B1-F - B0) under W1 > (B1-F - B0) under W0 | Transmission recovery |
| H16 | Mutations(W1) ≤ Mutations(W0) + 2 | No unauthorized mutation |
| H17 | Spearman(ΔSTC_meta, ΔPQ) > 0.5 | Mechanistic mediation |
| H18 | STC_core(W1) ≥ STC_core(W0) - 0.05 | Core preservation |

## 11. 成对生成铁律（v2 新增，治理级）

1. **单元内连续**：对任意 (question, arm)，先写 W0 落盘，紧接着写 W1。中途不得插入其他单元的生成。
2. **不回看**：W0 落盘即冻结，写完 W1 后不得回头修改 W0。
3. **不改 prompt**：W0/W1 的 system + user prompt 已冻结在 `projects/P13-3D-R3/prompts/`，本次只读取不编辑。
4. **不中途看结果**：全部 48 篇落盘并通过完整性门禁前，不运行 STC / PQ 评估，不据此调整任何 prompt 或映射。
5. **留痕**：每篇记录 `batch_id`、`generated_at`、`prompt_sha256`、`artifact_sha256`、`map_sha256(W1)`。

## 12. 输出规格（v2 新增）

- 格式：Markdown + 行内/行间 LaTeX（`$...$` / `$$...$$`）
- 必需章节（10 个）：摘要、问题重述、模型假设、符号说明、模型建立与求解、
  候选模型对比、选定模型说明、灵敏度分析、模型评价、结论
- 篇幅：正文 6000–11000 字符（含公式与表格标记）；低于 5000 判不合格需重生成
- 语言：中文，学术风格；论文内不得出现任何关于本实验、映射层、条件的元叙述
