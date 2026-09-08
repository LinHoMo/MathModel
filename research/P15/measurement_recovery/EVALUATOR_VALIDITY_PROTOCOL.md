# Evaluator Validity Protocol — Phase 3 Audit & Redesign

> **文档定位**: MathModel 仓库全部 evaluator 的有效性审计协议与重设计规范。
> **审计范围**: `core/tools/evaluation/` (10 文件), `core/validators/` (35 文件), `core/evaluation/` (前向兼容包), `research/P15/scripts/` (4 文件), `research/P13-3D/scripts/` (36 文件)
> **核心原则**: deterministic > semantic；测量有效性驱动，非分数驱动。
> **审计日期**: 2026-09-08
> **状态**: DRAFT v1.0（research 层实现，验证后再考虑迁入 core）

---

## 0. 执行摘要

当前 evaluator 体系存在 **3 个 P0 级测量无效问题** 和 **8 个 P1 级测量不可靠问题**：

| # | 问题 | 严重度 | 受影响能力 |
|---|------|--------|-----------|
| EVAL-BUG-001 | 空壳 artifact 判全 PASS（无 non-emptiness check） | **P0** | 全部 8 项能力 |
| EVAL-BUG-002 | model_correctness 完全依赖外部输入（n/a） | **P0** | Model Construction |
| EVAL-BUG-003 | method_selection 仅方法卡 ID 字符串匹配 | **P0/P1** | Method Selection |
| EVAL-BUG-004 | decomposition_coverage 退化口径 count-ratio 无语义 | P1 | Problem Understanding |
| EVAL-BUG-005 | experiment_validity 仅查 tags，不查结果内容 | P1 | Experiment Validity |
| EVAL-BUG-006 | validation_reliability 中 paper.exists() 直接给 1.0 | P1 | Validation Reliability |
| EVAL-BUG-007 | score_compute.py 关键词匹配可被游戏化 | P1 | 5 维评分卡 |
| EVAL-BUG-008 | fidelity_gate 空 artifact → coverage=1.0 | P1 | Writer Fidelity |
| EVAL-BUG-009 | stc_evaluator 仅字符串包含，无内容校验 | P1 | Structural Coverage |
| EVAL-BUG-010 | 无 execution authenticity check（created_by 可伪造） | P1 | Measurement Integrity |
| EVAL-BUG-011 | benchmark.py bench_score 信任 agent 自报 hits | P1 | Benchmark Scoring |
| EVAL-BUG-012 | weight_profiles 阈值可被 env 运行时覆盖 | P2 | Scoring Weights |

**结论**: 当前 8 项能力指标中，仅 `writing_completeness`（结构计数）和 `innovation`（pattern 引用计数）具备有限的确定性测量效力；其余 6 项均存在测量无效或不可靠问题。**在 evaluator 重设计完成前，任何基于当前指标的能力结论均无效。**

---

## 1. 全量 Evaluator 清单

### 1.1 `core/tools/evaluation/` — 能力指标与评分引擎（10 文件）

| 文件 | 评估什么 | 输入 | 输出 | 类型 | 已知问题 |
|------|---------|------|------|------|---------|
| `e2e_metrics.py` | 八项能力指标（decomposition/method/model/experiment/validation/innovation/writing/e2e） | project_dir + gt.json + response.json | metrics report (0-100) | **混合**：4 项 deterministic, 2 项 external, 2 项 semantic-proxy | EVAL-BUG-001/002/003/004/005/006/010 |
| `score_artifact.py` | 评审判定（加权分 + 最低分 + blocking → verdict） | work/score_card.json + weakness_report.json | verdict (pass/refine/block) | deterministic（基于预计算分卡） | 无 artifact non-emptiness；信任分卡内容 |
| `score_compute.py` | 5 张评分卡自动计算（academic/engineering/judge/reader/adversarial） | paper/main.tex + code/ + figures/ | 5 × score_card_*.json | **semantic-proxy**（关键词/正则匹配） | EVAL-BUG-007；关键词可被游戏化 |
| `aggregate_scores.py` | 5 张分卡 → 聚合 score_card.json | work/score_card_*.json | work/score_card.json | deterministic | 信任分卡分数；无独立校验 |
| `benchmark.py` | 引擎演练/题库健康/国赛复盘/e2e 基线 | rubric + response + project | 各类 report | mixed | EVAL-BUG-011；bench_score 信任 agent 自报 |
| `bench_mmbench.py` | MMBench 数据集导入 + rubric 骨架导出 | MMBench problem JSON | rubric JSON 骨架 | deterministic（格式转换） | 导出的 rubric 无 reference_results；评估仍依赖 agent 自评 |
| `weight_profiles.py` | 题型差异化评审权重（A/B/C/D/E/MCM/ICM） | problem_type | {scorer: weight} | deterministic | EVAL-BUG-012；env 可运行时覆盖 base/multipliers |
| `metrics.py` | 项目度量数字单一真源（agent 数/测试/门禁通过率） | 仓库状态 | docs/METRICS.md | deterministic | 非能力 evaluator，是仓库健康度量 |

### 1.2 `core/validators/` — 结构化校验器（35 文件）

#### 1.2.1 `evidence/evidence_gate.py` — 证据门禁

| 检查项 | 代码 | 评估什么 | 类型 | 问题 |
|--------|------|---------|------|------|
| E1 | 无活跃 claim | fail | deterministic | 正确 |
| E2 | claim 无 supports 边 | fail | deterministic | 正确 |
| E3 | 证据链含失效 artifact | fail | deterministic | 正确 |
| E4 | 实验无 produces 结果 | fail | deterministic | **不查结果内容是否为空** |
| E5 | 结果无实验来源 | weak | deterministic | 正确 |
| E6 | 证据链含 draft 状态 | weak | deterministic | 正确 |
| E7 | claim 覆盖率 < 0.8 | weak | deterministic | 阈值硬编码 |
| E8 | 无 sensitivity/baseline tags | weak | deterministic | **仅查 tags，不查内容** |

**Validity: PARTIALLY_VALID** — 结构检查正确，但 E4/E8 不验证内容非空。

#### 1.2.2 `quality/` — 研究质量七维评估（4 文件）

| 文件 | 评估什么 | 类型 | 问题 |
|------|---------|------|------|
| `contract.py` | 质量判定统一契约（PASS/WEAK/FAIL/UNKNOWN 四态） | deterministic（schema） | 设计良好 |
| `evaluators.py` | 七维检查（problem/model/experiment/evidence/claim/innovation/decision/reproducibility） | deterministic（结构+边检查） | **不查 artifact data 内容非空**；M1 仅查 card_id 存在性 |
| `aggregator.py` | 七维聚合 → QualityReport | deterministic | 设计良好 |

**Validity: PARTIALLY_VALID** — 结构/边检查设计良好，但所有检查均基于 artifact 存在性和图关系，不验证 `data` payload 非空。B0 空壳 artifact 可全 PASS（已实测确认）。

#### 1.2.3 `modules/` — 21 项模块校验器

| 文件 | 评估什么 | 类型 | 问题 |
|------|---------|------|------|
| `formula_checker.py` | 公式语法（括号/LaTeX/连续运算符/空分母） | deterministic | **仅语法，无语义**；不检查公式引用的变量是否已定义 |
| `assumption_validator.py` | 假设一致性（完整性/必要性/矛盾关键词对） | deterministic（关键词） | 矛盾检测仅 8 对关键词，覆盖率极低；不验证假设与模型一致性 |
| `symbol_registry.py` | 符号一致性（同符不同义/同义不同符） | deterministic | 仅从表格提取，不扫描全文公式中的符号使用 |
| `integrity_gate.py` | 产物完整性 | deterministic | — |
| `guardrails.py` | 护栏检查（占位符/AI痕迹/伪造引用） | deterministic（正则） | — |
| `hash_chain.py` | 哈希链验证 | deterministic | 设计良好 |
| `consistency_checker.py` | 跨产物一致性 | deterministic | — |
| `cross_model_checker.py` | 跨模型一致性 | deterministic | — |
| `symbolic_verifier.py` | 符号验证 | deterministic | — |
| `contract_checker.py` | 契约检查 | deterministic | — |
| `output_validator.py` | 输出校验 | deterministic | — |
| `type_system.py` | 类型系统 | deterministic | — |
| `problem_spec_parser.py` | 问题规格解析 | deterministic | — |
| `process_verifier.py` | 流程验证 | deterministic | — |
| `stage_gate.py` | 阶段门禁 | deterministic | — |
| `invariant_tracker.py` | 不变量追踪 | deterministic | — |
| `incremental_checker.py` | 增量检查 | deterministic | — |
| `error_attribution.py` | 错误归因 | deterministic | — |
| `permission_guard.py` | 权限守卫 | deterministic | — |
| `trust_domain.py` | 信任域 | deterministic | — |
| `rule_iterator.py` | 规则迭代器 | deterministic | — |

**Validity: PARTIALLY_VALID** — 模块级语法/结构检查有效，但 formula_checker 不做变量引用校验，assumption_validator 矛盾检测覆盖率不足。

### 1.3 `core/evaluation/` — 前向兼容包

| 文件 | 内容 |
|------|------|
| `__init__.py` | 空壳桥接 |
| `benchmark/__init__.py` | 空壳桥接 |
| `scoring/__init__.py` | 空壳桥接 |

**Validity: N/A** — 仅前向兼容，无独立实现。

### 1.4 `research/P15/scripts/` — Benchmark 健康门禁（4 文件）

| 文件 | 评估什么 | 类型 | 问题 |
|------|---------|------|------|
| `benchmark_completeness.py` | gold standard 8 字段非空检查 | deterministic | 仅查非空，不查内容质量 |
| `coverage_report.py` | family + failure-mode 覆盖 | deterministic | 设计良好 |
| `duplicate_gate.py` | 重复 question_id + content hash | deterministic | 设计良好 |
| `validate_schema.py` | benchmark JSON schema 校验 | deterministic | 设计良好 |

**Validity: VALID** — 这些是 benchmark 数据健康检查，非能力 evaluator，设计正确。

### 1.5 `research/P13-3D/scripts/` — 实验评估脚本（36 文件）

| 文件 | 评估什么 | 类型 | 问题 |
|------|---------|------|------|
| `fidelity_gate.py` | artifact→论文 三仪表（Coverage/Mutation/Semantic） | deterministic（字符串匹配） | EVAL-BUG-008：空 artifact → coverage=1.0；modification/renaming 标 TODO 未实现 |
| `stc_evaluator.py` | 论文对 artifact 元素的结构覆盖率 | deterministic（字符串包含） | EVAL-BUG-009：仅 name/ID 包含匹配，不验证内容正确性 |
| `model_construction.py` | 建模三维评分（structural/mathematical/alignment） | **混合**：structural/alignment 确定性，mathematical 依赖 agent 自报 deductions | 数学正确性完全信任 scorecard 自报 |
| `source_of_truth_gate.py` | MODEL_PAPER_MAP vs frozen artifact 引用校验 | deterministic | 设计良好；precision≥0.95 阈值合理 |
| `input_freeze_gate.py` | writer 输入冻结（hash+schema+frozen） | deterministic | 设计良好；有 hash 验证 |
| `g1_artifact_gate.py` | artifact 门禁 | deterministic | — |
| `g2_contamination_gate.py` | 污染门禁 | deterministic | — |
| `r3_*.py` (8 文件) | R3 实验运行/评分/重算 | mixed | — |
| `r2_*.py` (5 文件) | R2 实验分析 | mixed | — |
| `run_*.py` (6 文件) | 实验运行器 | mixed | — |
| `generate_*.py` (5 文件) | 数据生成 | N/A（非 evaluator） | — |
| `aggregate_results.py` | 结果聚合 | deterministic | — |
| `paired_analysis.py` | 配对分析 | deterministic | — |
| `ranking_ablation.py` | 排序消融 | deterministic | — |
| `validate_stc_calibration.py` | STC 校准验证 | deterministic | — |
| `r3g_corpus_check.py` | 语料检查 | deterministic | — |
| `artifact_persist.py` | artifact 持久化 | N/A | — |
| `create_golden_set.py` | 金标准集创建 | N/A | — |

**Validity: PARTIALLY_VALID** — fidelity_gate 和 stc_evaluator 存在空壳通过问题；model_construction 的 mathematical 维度依赖自报。

---

## 2. 已知问题清单（EVAL-BUG-xxx）

### EVAL-BUG-001 — 空壳 artifact 判全 PASS [P0: 测量无效]

- **路径**: `core/tools/evaluation/e2e_metrics.py`（全文件）, `core/validators/quality/evaluators.py`（全文件）, `core/validators/evidence/evidence_gate.py`（E4）
- **问题描述**: 没有任何 evaluator 检查 artifact 的 `data` payload 是否非空。B0 baseline 注册了 16 个空壳 artifact（`payload=[]`, `data={}`），但：
  - `e2e_metrics.py` 第 109-112 行：`reg.list_by_type("question")` 返回空壳 artifact 仍计入 `len(questions)`
  - `quality/evaluators.py` 第 47-73 行：`problem_quality()` 仅检查 question 是否存在 + motivates 边，不检查 `q.data` 内容
  - `evidence_gate.py` 第 141-148 行：E4 检查实验是否有 `produces` 边，但不检查被 produces 的 result artifact `data` 是否为空
- **证据**: 
  - B0 实测：16 个空壳 artifact，quality_report 七维全 PASS（findings=[]）
  - `e2e_metrics.py` 第 109 行 `questions = [a for a in reg.list_by_type("question")]` — 无 `if a.data` 过滤
  - `e2e_metrics.py` 第 110-111 行 `results = [a for a in reg.list_by_type("result") if a.status not in (...)]` — 无内容检查
- **影响**: 全部 8 项能力指标。空壳 artifact 可产生非零 decomposition/method/experiment 分数。
- **修复建议**: 在 ArtifactRegistry 层增加 `is_empty()` 方法（`data is None or data == {} or payload == []`），所有 evaluator 在计数前过滤空 artifact；在 DAG 节点完成时增加 non-emptiness gate。

### EVAL-BUG-002 — model_correctness 完全依赖外部输入 [P0: 测量无效]

- **路径**: `core/tools/evaluation/e2e_metrics.py` 第 176-180 行
- **问题描述**: 
  ```python
  mc = response.get("model_correctness_pct")
  model_value = round(float(mc), 1) if mc is not None else None
  model_detail = {"source": "response.rubric" if mc is not None else "缺评分响应（n/a）"}
  ```
  model_correctness 100% 来自外部 `response.json` 的 `model_correctness_pct` 字段。没有任何确定性计算。当 response 缺失时为 n/a，当 response 存在时完全信任输入值。
- **证据**: 代码第 177 行直接 `response.get("model_correctness_pct")`，无任何校验、无范围检查、无证据要求。
- **影响**: Model Construction 能力完全不可测量。B0 运行中该指标为 n/a。
- **修复建议**: 按本协议 §4 的 L1-L4 四层设计重写 model_correctness，拆分为 deterministic checks（变量定义/目标方向/约束引用/方程结构/单位一致性）+ semantic judgment（独立 judge）。

### EVAL-BUG-003 — method_selection 仅方法卡 ID 字符串匹配 [P0/P1: 测量无效/不可靠]

- **路径**: `core/tools/evaluation/e2e_metrics.py` 第 64-82 行（`_method_hit`）, 第 138-174 行
- **问题描述**: 
  ```python
  def _method_hit(candidate_ids, card_names, gt_methods):
      gts = [_norm(g) for g in gt_methods]
      for cid in candidate_ids:
          hay = " ".join(filter(None, {_norm(cid), _norm(card_names.get(cid, ""))}))
          for gt, gt_c in zip(gts, gts_compact):
              if gt and (gt in hay or hay in gt):
                  return True
  ```
  仅做归一化字符串包含匹配。不评估：
  1. 方法是否适用于问题类型（如 TOPSIS 用于运动学问题 = wrong family）
  2. 方法是否回答评价目标
  3. 方法是否数学合理
  4. 替代方法是否也可行（gold=TOPSIS, agent=AHP 不能自动判 wrong）
- **证据**: 
  - B0 实测：agent 选了 TOPSIS（评价类方法），2024_A 是运动学问题，method_selection=0%
  - 代码第 78 行 `gt in hay or hay in gt` — 纯字符串包含
  - `_load_card_names()` 第 85-99 行仅提取 card_id + name + family，不提取 applicability 条件
- **影响**: Method Selection 能力。合理的替代方法被判 0 分；错误的方法族只要 ID 字符串碰巧匹配就得分。
- **修复建议**: 按本协议 §5 设计独立的 Method Selection Quality 维度，评估方法适用性而非 ID 匹配。

### EVAL-BUG-004 — decomposition_coverage 退化口径 count-ratio [P1: 测量不可靠]

- **路径**: `core/tools/evaluation/e2e_metrics.py` 第 122-136 行
- **问题描述**: 当无 `response.decomposition_aligned` 时：
  ```python
  aligned = min(len(questions), len(sub_qs))
  decomp_value = round(100.0 * min(int(aligned), len(sub_qs)) / len(sub_qs), 1)
  ```
  这只是 `min(produced, gt) / gt` 的数量比。如果 GT 有 5 个子问题，agent 产出 3 个完全不相关的问题，仍得 3/5=60%。无法区分"未分解"和"分解错误"。
- **证据**: B0 实测 2024_A：GT 有 5 个子问题，agent 产出 1 个空壳 Q001，decomposition=20%（count-ratio），但实际应为 0%（Q001 与任何 GT 子问题都不对齐）。
- **影响**: Problem Understanding 能力。
- **修复建议**: 增加 sub-question semantic alignment（基于关键词/变量/约束的重合度），或要求独立 judge 标注对齐关系。count-ratio 仅作为下限代理。

### EVAL-BUG-005 — experiment_validity 仅查 tags [P1: 测量不可靠]

- **路径**: `core/tools/evaluation/e2e_metrics.py` 第 182-192 行
- **问题描述**:
  ```python
  ROBUSTNESS_TAGS = {"sensitivity", "baseline", "multi_run"}
  robust = [r for r in results if ROBUSTNESS_TAGS & set(r.tags or [])]
  robust_ratio = (len(robust) / len(results)) if results else None
  multi_run = sum(1 for r in results if (r.data or {}).get("runs", 1) >= 5)
  ```
  仅检查 artifact tags 是否包含 "sensitivity"/"baseline"/"multi_run"，不检查：
  1. 结果是否有实际数值（`data` 非空）
  2. 敏感性分析是否真的变化了参数
  3. 基线对比是否有实际对比数据
  4. 多次运行是否有均值/标准差
- **证据**: 一个 `data={}`, `tags=["sensitivity"]` 的空壳 result 会被计入 robust。
- **影响**: Experiment Validity 能力。
- **修复建议**: 检查 result.data 中是否有实际数值字段；sensitivity 需有 parameter_range + output_variance；baseline 需有 baseline_value + comparison_metric。

### EVAL-BUG-006 — validation_reliability 中 paper.exists() 给 1.0 [P1: 测量不可靠]

- **路径**: `core/tools/evaluation/e2e_metrics.py` 第 194-203 行
- **问题描述**:
  ```python
  val_components = [v for v in (support_ratio,) if v is not None]
  paper = project_dir / "paper" / "main.tex"
  if paper.exists():
      val_components.append(1.0)   # 存在论文占位
  ```
  只要 `main.tex` 文件存在就给 1.0 分，不检查论文内容、不检查论文是否引用了 validated result、不检查 claim 是否在论文中出现。
- **证据**: 一个空的 `main.tex`（仅 `\documentclass{}`）会得到 validation_reliability = (support_ratio + 1.0)/2。
- **影响**: Validation Reliability 能力。
- **修复建议**: 检查论文中是否引用了已验证的 result artifact（通过 `\ref` 或数值匹配）；检查 claim 是否在论文中出现。

### EVAL-BUG-007 — score_compute.py 关键词匹配可被游戏化 [P1: 测量不可靠]

- **路径**: `core/tools/evaluation/score_compute.py` 全文件
- **问题描述**: 5 张评分卡全部基于关键词/正则匹配：
  - academic: `_has_keywords(tex, ["推导", "derivation", ...])` → +2.0
  - engineering: `"seed(42)" in code_main` → +3.0
  - judge: `_has_keywords(tex, ["新", "novel", "创新", ...])` → +1.5
  - reader: 章节关键词计数
  - adversarial: Benford 律 + 反模式关键词
  
  Agent 可以通过在论文中堆砌关键词来提高分数，而不需要实际内容质量。例如：在论文中写一句"本文进行了灵敏度分析、交叉验证、鲁棒性测试"即可获得 validation_score +2.5。
- **证据**: 
  - 第 92-100 行：derivation_score 基准 5.0，有"推导"关键词 +2.0，有符号表章节 +1.5，有假设章节 +1.5 → 最高 10.0
  - 第 171 行：`"seed({})".format(seed) in code_main` → 只要代码里出现字符串 "seed(42)" 就 +3.0，不检查是否真的设置了随机种子
- **影响**: 全部 5 维评分卡。分数反映的是关键词密度而非实际质量。
- **修复建议**: 关键词匹配仅作为存在性检查（0/1），不作为程度评分；程度评分需基于内容证据（如实际推导步骤数、实际参数变化范围）。

### EVAL-BUG-008 — fidelity_gate 空 artifact → coverage=1.0 [P1: 测量不可靠]

- **路径**: `research/P13-3D/scripts/fidelity_gate.py` 第 304, 319-320 行
- **问题描述**:
  ```python
  coverage_fidelity = found_elements / total_elements if total_elements > 0 else 1.0
  ...
  if total_elements == 0:
      semantic_fidelity = 1.0
  ```
  当 artifact 为空（无任何元素）时，coverage_fidelity=1.0, semantic_fidelity=1.0。空 artifact 得到最高保真度。
- **证据**: 第 304 行 `if total_elements > 0 else 1.0`；第 319-320 行同理。
- **影响**: Writer Fidelity 测量。空模型 artifact → 论文保真度 100%。
- **修复建议**: 空 artifact 应判 UNKNOWN（无法评估）或 FAIL（无内容可保真），不应给 1.0。

### EVAL-BUG-009 — stc_evaluator 仅字符串包含 [P1: 测量不可靠]

- **路径**: `research/P13-3D/scripts/stc_evaluator.py` 全文件
- **问题描述**: 每个 artifact 元素的覆盖率检查仅为：
  ```python
  mentioned = bool(re.search(rf"{re.escape(var_name)}|{re.escape(var_id)}", paper_text))
  ```
  只要变量名/ID 字符串在论文中出现就算 covered。不检查：
  1. 变量的定义/单位/含义是否在论文中正确表述
  2. 变量是否在公式中被正确使用
  3. 论文是否歪曲了变量含义
- **证据**: 第 38-39 行 `mentioned = bool(re.search(...))`；所有元素类型均用同一模式。
- **影响**: Structural Transmission Coverage。
- **修复建议**: 增加内容级检查（变量定义段落 + 单位匹配 + 公式引用）。

### EVAL-BUG-010 — 无 execution authenticity check [P1: 测量不可靠]

- **路径**: `core/tools/evaluation/e2e_metrics.py` 第 261-287 行（`_measurement_integrity`）
- **问题描述**:
  ```python
  agent = lambda a: str(getattr(a, "created_by", "") or "").startswith("agent")
  agent_created = sum(1 for a in registry.all() if agent(a))
  ```
  Measurement Integrity 仅检查 `created_by` 字段是否以 "agent" 开头。这个字段可以被任意伪造。没有：
  1. 输入 hash 验证（题面/数据是否被篡改）
  2. 执行日志验证（代码是否真的运行过）
  3. 输出 hash 链验证（result 是否由对应 experiment 产生）
- **证据**: 第 267 行 `created_by.startswith("agent")` — 纯字符串前缀检查。
- **影响**: Measurement Integrity。无法区分真实 agent 执行和手工伪造的 artifact。
- **修复建议**: 增加 input_hash（题面+数据的 sha256）、execution_log（命令+退出码+时间戳）、output_hash_chain（result.hash = hash(experiment_id + input_hash + seed)）。

### EVAL-BUG-011 — benchmark.py bench_score 信任 agent 自报 hits [P1: 测量不可靠]

- **路径**: `core/tools/evaluation/benchmark.py` 第 219-299 行
- **问题描述**:
  ```python
  hits = int(ds.get("ground_truth_hits", 0))
  refs = ref_map.get(did, [])
  expected = len(refs)
  ```
  `ground_truth_hits` 由 agent 在 response.json 中自报。bench_score 仅检查 `hits <= expected`，不验证 hits 是否真实。agent 可以自报全部命中。
- **证据**: 第 256 行 `hits = int(ds.get("ground_truth_hits", 0))` — 直接信任输入。
- **影响**: Benchmark Scoring。
- **修复建议**: ground_truth_hits 应由独立 judge 或确定性匹配计算，不接受 agent 自报。

### EVAL-BUG-012 — weight_profiles 阈值可被 env 运行时覆盖 [P2: 测量不完整]

- **路径**: `core/tools/evaluation/weight_profiles.py` 第 54-56 行
- **问题描述**:
  ```python
  base = get("review.weight_profiles.base", default=DEFAULT_BASE)
  multipliers_all = get("review.weight_profiles.multipliers", default=DEFAULT_MULTIPLIERS)
  clamp_range = get("review.weight_profiles.clamp", default=[0.7, 1.5])
  ```
  权重 base/multipliers/clamp 全部从 env config 读取，可在运行时被修改。虽然 env config 是版本控制的，但没有 pre-registration 机制确保评估时使用的权重与协议声明的一致。
- **证据**: 第 54-56 行三个 `get()` 调用均无版本锁定。
- **影响**: Scoring Weights 的可复现性。
- **修复建议**: 在评估报告中记录使用的权重 profile hash；权重变更需经 protocol 修订。

---

## 3. Evaluator 设计原则

### 3.1 核心原则

1. **deterministic > semantic**: 变量是否存在、约束是否引用变量、目标方向是否明确、公式是否有单位、结果是否引用 experiment、claim 是否引用 evidence——这些尽可能由机器判断。semantic evaluation 仅用于确定性无法覆盖的部分。

2. **每个 evaluator 必须声明**:
   - 它测量什么能力（construct）
   - 它不测量什么（exclusion）
   - 置信度（high/medium/low）
   - 局限性（已知盲区）

3. **不允许单一分数代表复杂能力**: 必须拆维度。Model Construction 拆为 L1-L4 四层，每层拆为具体 check。

4. **semantic evaluation 必须有独立 judge**: 不允许 Agent 自评。semantic 部分需由独立 LLM judge（不同 session/不同模型）或 human-in-the-loop 完成。

5. **所有 threshold pre-registered**: 阈值记录在 protocol 中，评估时锁定版本。不允许事后调整阈值以适应结果。

6. **fail-closed by default**: 输入缺失/artifact 为空/无法判断时，应判 FAIL 或 UNKNOWN，不应给满分或默认通过。

7. **artifact non-emptiness 是前置条件**: 所有 evaluator 在评估内容前必须先验证 artifact `data` payload 非空。空 artifact 直接判 FAIL。

8. **可追溯性**: 每个分数必须能追溯到具体的 artifact ID + 字段 + 检查逻辑。不允许黑箱总分。

### 3.2 Deterministic vs Semantic 分类标准

| 类别 | 定义 | 示例 | 置信度 |
|------|------|------|--------|
| **Deterministic-Structural** | 基于 artifact 结构/字段/图关系的存在性检查 | 变量是否定义、约束是否引用变量、claim 是否有 supports 边 | High |
| **Deterministic-Content** | 基于 artifact data 内容的数值/字符串检查 | 公式括号匹配、单位一致性、数值范围、seed=42 | High |
| **Semantic-Judge** | 需要理解含义/合理性/对齐度的判断 | 方法是否适用于问题、模型是否回答了题目、假设是否合理 | Medium（需独立 judge） |
| **External-Input** | 完全依赖外部评分输入 | 当前 model_correctness = response.model_correctness_pct | Low（不可信） |

**重设计目标**: 将当前 External-Input 类指标转为 Deterministic + Semantic-Judge 组合。

---

## 4. Model Construction Evaluator 四层重设计

### 4.1 架构总览

```
Model Construction Score
├── L1 Problem Understanding (权重 20%)
│   ├── sub_question_coverage (D)
│   ├── required_deliverables (D)
│   ├── variable_identification (D)
│   ├── parameter_identification (D)
│   ├── constraint_identification (D)
│   └── evaluation_target_alignment (S)
├── L2 Model Construction (权重 35%)
│   ├── variable_semantics (D)
│   ├── objective_clarity (D)
│   ├── constraint_validity (D)
│   ├── mechanism_description (D)
│   ├── assumption_consistency (D)
│   ├── equation_structure (D)
│   ├── boundary_conditions (D)
│   ├── unit_consistency (D)
│   ├── index_consistency (D)
│   └── problem_alignment (S)
├── L3 Solving (权重 25%)
│   ├── solver_appropriateness (D+S)
│   ├── solution_feasibility (D)
│   ├── convergence (D)
│   ├── numerical_stability (D)
│   ├── repeatability (D)
│   └── global_optimum_evidence (D+S)
└── L4 Validation (权重 20%)
    ├── baseline_comparison (D)
    ├── sensitivity_analysis (D)
    ├── robustness_analysis (D)
    ├── uncertainty_quantification (D)
    ├── counterfactual_validation (S)
    └── failure_case_analysis (S)
```

D = Deterministic, S = Semantic (独立 judge)

### 4.2 L1 Problem Understanding（deterministic 为主）

#### L1.1 sub_question_coverage [Deterministic-Structural]
- **测量**: agent 产出的子问题与 gold standard 的重合度
- **检查**:
  1. agent 产出的 question artifact 数量 ≥ GT sub_questions 数量的 50%
  2. 每个 agent question 的 `data.tokens` / `data.key_entities` 与至少一个 GT sub_question 的关键词重合度 ≥ 0.3（Jaccard）
  3. 无重复子问题（语义去重）
- **通过标准**:
  - PASS: ≥ 80% GT 子问题被覆盖（Jaccard ≥ 0.3）
  - PARTIAL: 50-79% 覆盖
  - FAIL: < 50% 覆盖或无 question artifact
- **证据要求**: 每个覆盖关系记录 `{gt_id, agent_qid, jaccard, matched_keywords}`
- **常见误判**: GT 子问题表述过于抽象导致关键词重合低 → 需 GT 提供 `key_entities` 字段辅助匹配

#### L1.2 required_deliverables [Deterministic-Structural]
- **测量**: 是否包含所有必需交付物类型
- **检查**: Registry 中存在以下类型的非空 artifact：question, model, experiment, result, claim
- **通过标准**:
  - PASS: 全部 5 类存在且非空
  - PARTIAL: 3-4 类存在
  - FAIL: < 3 类或存在空壳
- **证据要求**: `{type: {artifact_id, is_empty}}`

#### L1.3 variable_identification [Deterministic-Content]
- **测量**: 关键变量是否被识别
- **检查**: agent model artifact 的 `data.variables` 中，GT `key_variables` 的命中率
- **通过标准**:
  - PASS: ≥ 80% GT 关键变量被识别（名称/别名匹配）
  - PARTIAL: 50-79%
  - FAIL: < 50%
- **证据要求**: `{gt_var, matched_agent_var, match_type: exact|alias|none}`

#### L1.4 parameter_identification [Deterministic-Content]
- **测量**: 关键参数是否被识别
- **检查**: 同 L1.3，针对 `data.parameters` 和 GT `key_parameters`
- **通过标准**: 同 L1.3

#### L1.5 constraint_identification [Deterministic-Content]
- **测量**: 关键约束是否被识别
- **检查**: agent model artifact 的 `data.constraints` 中，GT `key_constraints` 的命中率（基于约束表达式的变量+运算符匹配）
- **通过标准**:
  - PASS: ≥ 70% GT 关键约束被识别
  - PARTIAL: 40-69%
  - FAIL: < 40%
- **证据要求**: `{gt_constraint, matched_agent_constraint, matched_variables}`

#### L1.6 evaluation_target_alignment [Semantic-Judge]
- **测量**: agent 是否理解评价目标
- **检查**: 独立 judge 对比 agent 的 `problem_interpretation` 与 GT `evaluation_targets`，判断 agent 是否明确了优化方向/评价准则
- **通过标准**:
  - PASS: judge 判定 agent 明确理解 ≥ 80% 评价目标
  - PARTIAL: 理解 50-79%
  - FAIL: < 50% 或无 interpretation
- **证据要求**: judge 输出 `{target_id, understood: bool, rationale}`

### 4.3 L2 Model Construction（deterministic + semantic）

#### L2.1 variable_semantics [Deterministic-Content]
- **测量**: 变量有定义/单位/含义
- **检查**: 每个 `data.variables[]` 必须有 `name`（非空）、`unit`（非空或"无量纲"）、`description`（≥ 10 字符）
- **通过标准**:
  - PASS: ≥ 90% 变量有完整语义
  - PARTIAL: 70-89%
  - FAIL: < 70% 或无 variables
- **证据要求**: `{var_id, has_name, has_unit, has_description}`

#### L2.2 objective_clarity [Deterministic-Content]
- **测量**: 有明确的优化目标，方向明确
- **检查**:
  1. `data.objective` 存在且非空
  2. `data.objective.kind` ∈ {minimize, maximize, satisfy, find}
  3. `data.objective.expression` 引用了已定义的变量
- **通过标准**:
  - PASS: 三项全满足
  - PARTIAL: 满足 2 项
  - FAIL: 满足 ≤ 1 项或无 objective
- **证据要求**: `{objective_exists, kind_valid, expression_refs_defined_vars}`

#### L2.3 constraint_validity [Deterministic-Content]
- **测量**: 约束引用已定义的变量，有数学表达
- **检查**: 每个 `data.constraints[]` 的 `expression` 中出现的变量名必须在 `data.variables` 中定义；`expression` 必须包含至少一个运算符（=, <, >, ≤, ≥, ≠）
- **通过标准**:
  - PASS: ≥ 90% 约束有效
  - PARTIAL: 70-89%
  - FAIL: < 70% 或无 constraints
- **证据要求**: `{constraint_id, refs_undefined_vars: [], has_operator}`

#### L2.4 mechanism_description [Deterministic-Content]
- **测量**: 有机制描述（不是只列方法名）
- **检查**: `data.mechanism[]` 中每个机制有 `name` + `equation` 或 `description`（≥ 30 字符）；不能只有方法卡 ID
- **通过标准**:
  - PASS: ≥ 1 个机制有完整描述，且描述包含数学表达或物理/逻辑推导
  - PARTIAL: 有机制名但描述不足
  - FAIL: 无 mechanism 或仅有方法卡 ID
- **证据要求**: `{mechanism_id, has_name, has_equation, description_length}`

#### L2.5 assumption_consistency [Deterministic-Content + Semantic]
- **测量**: 有假设列表，假设与模型一致
- **检查**:
  - D: `data.assumptions[]` 数量 ≥ 3，每个有 `statement`（≥ 20 字符）
  - S: 独立 judge 判定假设是否与模型方程/约束一致（无矛盾）
- **通过标准**:
  - PASS: D 全满足 + judge 判定无矛盾
  - PARTIAL: D 全满足 + judge 判定有轻微不一致
  - FAIL: D 不满足 或 judge 判定有严重矛盾
- **证据要求**: D: `{assumption_id, statement_length}`; S: judge `{assumption_id, consistent, rationale}`

#### L2.6 equation_structure [Deterministic-Content]
- **测量**: 有方程，方程引用已定义变量
- **检查**:
  1. `data.equations[]` 或 mechanism.equation 数量 ≥ 1
  2. 方程通过 formula_checker 语法检查
  3. 方程中出现的变量 ≥ 50% 在 variables 中定义
- **通过标准**:
  - PASS: 三项全满足
  - PARTIAL: 满足 2 项
  - FAIL: 满足 ≤ 1 项或无方程
- **证据要求**: `{equation_count, syntax_valid, var_coverage}`

#### L2.7 boundary_conditions [Deterministic-Content]
- **测量**: 有边界/初始条件
- **检查**: `data.boundary_conditions` 存在且非空，或 model description 中明确提及边界/初始条件
- **通过标准**:
  - PASS: 有明确的边界/初始条件描述
  - PARTIAL: 有提及但不具体
  - FAIL: 完全缺失
- **证据要求**: `{boundary_conditions_present, specificity}`

#### L2.8 unit_consistency [Deterministic-Content]
- **测量**: 变量和方程有单位，单位一致
- **检查**:
  1. ≥ 80% 变量有 unit 字段
  2. 方程两侧的量纲不冲突（基于 unit 字段的简单量纲检查：如左侧为质量，右侧不能为时间）
- **通过标准**:
  - PASS: 两项全满足
  - PARTIAL: 满足 1 项
  - FAIL: 两项都不满足
- **证据要求**: `{var_unit_coverage, dimension_conflicts: []}`

#### L2.9 index_consistency [Deterministic-Content]
- **测量**: 下标/索引一致
- **检查**: 方程中使用的下标（如 i, j, t）在变量定义中有对应范围声明；无未定义的下标
- **通过标准**:
  - PASS: 无未定义下标
  - PARTIAL: 有 ≤ 2 个未定义下标
  - FAIL: > 2 个未定义下标或无下标声明
- **证据要求**: `{undefined_indices: []}`

#### L2.10 problem_alignment [Semantic-Judge]
- **测量**: 模型回答的问题与题面一致
- **检查**: 独立 judge 对比 model 的 objective/constraints/mechanism 与原题面，判断模型是否在回答题目要求的问题（而非另一个问题）
- **通过标准**:
  - PASS: judge 判定模型直接回答了题目
  - PARTIAL: 模型回答了相关但不完全对齐的问题
  - FAIL: 模型回答了错误的问题或完全偏离
- **证据要求**: judge `{aligned, misalignment_type, rationale}`

### 4.4 L3 Solving（deterministic + semantic）

#### L3.1 solver_appropriateness [Deterministic + Semantic]
- **测量**: 求解方法与模型类型匹配
- **检查**:
  - D: `data.solver` 存在且非空；solver 类型与 model 类型的映射表检查（如 LP→simplex/interior-point, ODE→RK4/finite_element）
  - S: 独立 judge 判定 solver 是否适合该模型的数学结构
- **通过标准**:
  - PASS: D 匹配 + judge 确认
  - PARTIAL: D 匹配但 judge 有保留
  - FAIL: D 不匹配 或 judge 判定不适合
- **证据要求**: D: `{solver, model_type, mapping_match}`; S: judge

#### L3.2 solution_feasibility [Deterministic-Content]
- **测量**: 解可行（满足约束）
- **检查**: result artifact 的 `data.solution` 中，约束满足率 ≥ 95%（基于约束表达式数值验证）
- **通过标准**:
  - PASS: ≥ 95% 约束满足
  - PARTIAL: 80-94%
  - FAIL: < 80% 或无 solution
- **证据要求**: `{constraint_check: {id, satisfied, residual}}`

#### L3.3 convergence [Deterministic-Content]
- **测量**: 数值收敛
- **检查**: result.data 中有 `convergence` 字段或迭代残差序列，最终残差 < 1e-6（或题目指定阈值）
- **通过标准**:
  - PASS: 有收敛证据且残差达标
  - PARTIAL: 有迭代但未明确收敛
  - FAIL: 无收敛信息
- **证据要求**: `{final_residual, iterations, converged}`

#### L3.4 numerical_stability [Deterministic-Content]
- **测量**: 数值稳定
- **检查**: 多次运行（≥ 3 次）结果的相对标准差 < 5%；无 NaN/Inf
- **通过标准**:
  - PASS: 相对标准差 < 5% 且无 NaN/Inf
  - PARTIAL: 相对标准差 5-15%
  - FAIL: > 15% 或有 NaN/Inf
- **证据要求**: `{run_count, mean, std, relative_std, has_nan}`

#### L3.5 repeatability [Deterministic-Content]
- **测量**: seed=42 可复现
- **检查**:
  1. 代码中设置了随机种子且值为 42（`np.random.seed(42)` / `random.seed(42)` / `torch.manual_seed(42)`）
  2. 两次运行结果完全一致（hash 匹配）
- **通过标准**:
  - PASS: 两项全满足
  - PARTIAL: 设置了 seed 但未验证可复现
  - FAIL: 未设置 seed
- **证据要求**: `{seed_set, seed_value, reproducible_hash_match}`

#### L3.6 global_optimum_evidence [Deterministic + Semantic]
- **测量**: 如果宣称全局最优，有证据
- **检查**:
  - D: 如果 claim 中包含"全局最优"/"global optimum"，则 result.data 中必须有 `optimality_proof` 或 `multi_start_results`（≥ 10 个不同初值收敛到同一点）
  - S: 独立 judge 判定证据是否充分
- **通过标准**:
  - PASS: 未宣称全局最优，或宣称且有充分证据
  - PARTIAL: 宣称且有部分证据
  - FAIL: 宣称但无证据
- **证据要求**: `{claims_global_opt, evidence_type, evidence_quality}`

### 4.5 L4 Validation（deterministic + semantic）

#### L4.1 baseline_comparison [Deterministic-Content]
- **测量**: 有基线对比
- **检查**: result.data 中有 `baseline` 字段，包含 `baseline_method` + `baseline_value` + `comparison_metric` + `agent_value`
- **通过标准**:
  - PASS: 四项全有且 agent_value 与 baseline_value 可比较
  - PARTIAL: 有基线但缺少对比指标
  - FAIL: 无基线
- **证据要求**: `{baseline_method, baseline_value, agent_value, metric}`

#### L4.2 sensitivity_analysis [Deterministic-Content]
- **测量**: 有敏感性分析
- **检查**: result.data 中有 `sensitivity` 字段，包含 ≥ 1 个参数的 `parameter` + `range` + `output_variance`（输出变化量）
- **通过标准**:
  - PASS: ≥ 2 个参数有完整敏感性数据
  - PARTIAL: 1 个参数有数据
  - FAIL: 无敏感性分析
- **证据要求**: `{param, range, output_variance, sensitivity_index}`

#### L4.3 robustness_analysis [Deterministic-Content]
- **测量**: 有鲁棒性分析
- **检查**: result.data 中有 `robustness` 字段，包含扰动测试（噪声/参数扰动/数据缺失）下的性能变化
- **通过标准**:
  - PASS: 有 ≥ 1 种扰动测试且性能下降 < 20%
  - PARTIAL: 有扰动测试但性能下降 20-50%
  - FAIL: 无鲁棒性分析或性能下降 > 50%
- **证据要求**: `{perturbation_type, performance_degradation}`

#### L4.4 uncertainty_quantification [Deterministic-Content]
- **测量**: 有不确定性量化
- **检查**: result.data 中有 `uncertainty` 字段，包含 `confidence_interval` 或 `std` 或 `蒙特卡洛结果`
- **通过标准**:
  - PASS: 有明确的不确定性区间或分布
  - PARTIAL: 有标准差但无置信区间
  - FAIL: 无不确定性量化
- **证据要求**: `{uncertainty_type, ci_lower, ci_upper, std}`

#### L4.5 counterfactual_validation [Semantic-Judge]
- **测量**: 有反事实验证
- **检查**: 独立 judge 判定是否有"如果改变 X，则 Y 会怎样"的反事实分析，且分析逻辑合理
- **通过标准**:
  - PASS: 有 ≥ 1 个反事实分析且逻辑合理
  - PARTIAL: 有反事实但分析不充分
  - FAIL: 无反事实验证
- **证据要求**: judge `{counterfactual_present, logic_sound, rationale}`

#### L4.6 failure_case_analysis [Semantic-Judge]
- **测量**: 有失败案例分析
- **检查**: 独立 judge 判定是否讨论了模型在什么情况下会失败/失效，且分析具体
- **通过标准**:
  - PASS: 有具体的失败案例/边界条件分析
  - PARTIAL: 有提及局限性但不具体
  - FAIL: 无失败案例分析
- **证据要求**: judge `{failure_analysis_present, specificity, rationale}`

### 4.6 层级聚合规则

```
layer_score = Σ(check_score × check_weight) / Σ(check_weight)
  where check_score = {PASS: 1.0, PARTIAL: 0.5, FAIL: 0.0}

model_construction_score =
  0.20 × L1 + 0.35 × L2 + 0.25 × L3 + 0.20 × L4
```

**前置条件**: 任一 L2 核心 check（objective_clarity, constraint_validity, equation_structure）为 FAIL 时，整体 model_construction_score 上限为 40/100（不得因其他层高分而掩盖建模本质缺陷）。

---

## 5. Method Selection Quality 独立维度设计

### 5.1 设计原则

- **不再把 method_selection 当 Problem Alignment 的代理变量**
- **gold=TOPSIS, agent=AHP 不能自动判 wrong**——必须判断是否回答同一个问题
- 评估方法是否适合问题，而非方法 ID 是否匹配 GT

### 5.2 四维评估

#### MSQ-1 方法适用性 [Deterministic + Semantic]
- **测量**: 方法是否适合问题类型
- **检查**:
  - D: 方法卡的 `applicability.problem_types` 是否包含当前问题的 family（从 problem_spec 解析）
  - S: 独立 judge 判定方法的数学假设是否与问题条件一致
- **通过标准**:
  - PASS: D 匹配 + judge 确认假设一致
  - PARTIAL: D 匹配但 judge 有保留
  - FAIL: D 不匹配（如评价类方法用于运动学问题）
- **不测量**: 方法是否是 GT 中列出的方法

#### MSQ-2 目标回答性 [Semantic-Judge]
- **测量**: 方法是否回答评价目标
- **检查**: 独立 judge 对比方法的输出类型与 GT `evaluation_targets`，判断方法的输出是否能直接回答评价目标
- **通过标准**:
  - PASS: 方法输出直接回答 ≥ 80% 评价目标
  - PARTIAL: 回答 50-79%
  - FAIL: < 50% 或方法输出类型与目标不匹配

#### MSQ-3 数学合理性 [Deterministic-Content]
- **测量**: 方法是否数学合理
- **检查**:
  - D: 方法卡的 `mathematical_foundations` 中关键假设在 model assumptions 中有对应声明
  - D: 方法的输入维度与 model variables 数量匹配
- **通过标准**:
  - PASS: 两项全满足
  - PARTIAL: 满足 1 项
  - FAIL: 两项都不满足

#### MSQ-4 替代方法可行性 [Semantic-Judge]
- **测量**: 是否考虑了替代方法，且选择理由充分
- **检查**: 独立 judge 评估 agent 的 `candidate_models`（≥ 2 个）和 `selection_reason`，判断：
  1. 是否有至少一个合理的替代方法
  2. 选择理由是否基于问题特征而非随意
- **通过标准**:
  - PASS: ≥ 2 个候选 + 充分选择理由
  - PARTIAL: 有候选但理由不充分
  - FAIL: 仅 1 个候选或无选择理由

### 5.3 与旧 method_selection 的区别

| 维度 | 旧 method_selection | 新 Method Selection Quality |
|------|-------------------|---------------------------|
| 匹配方式 | 方法卡 ID 字符串包含 | 方法适用性 + 目标回答性 + 数学合理性 |
| GT 作用 | GT 方法 = 唯一正确答案 | GT 方法 = 参考方法族，非唯一 |
| 替代方法 | 不评估 | MSQ-4 独立评估 |
| 空壳处理 | 空 card_id → 不命中 → 0% | 空 card_id → FAIL（前置条件） |
| 置信度 | Low（字符串匹配） | Medium（D+S 组合） |

---

## 6. 每个 Evaluator 的 Validity Status

### 6.1 Status 定义

| Status | 定义 |
|--------|------|
| **VALID** | 测量目标明确，deterministic checks 可靠，已知问题不影响核心测量 |
| **PARTIALLY_VALID** | 结构正确但存在内容级盲区（如不查非空），需补充检查 |
| **INVALID** | 测量无效（完全依赖外部输入或空壳通过），需重设计 |
| **NEEDS_REDESIGN** | 设计方向错误（如字符串匹配代替语义判断），需按本协议重写 |

### 6.2 Status 清单

| Evaluator | 路径 | Status | 理由 |
|-----------|------|--------|------|
| e2e_metrics.decomposition_coverage | `e2e_metrics.py:122-136` | PARTIALLY_VALID | count-ratio 退化口径无语义 |
| e2e_metrics.method_selection | `e2e_metrics.py:138-174` | **NEEDS_REDESIGN** | 纯字符串匹配，按 §5 重写 |
| e2e_metrics.model_correctness | `e2e_metrics.py:176-180` | **INVALID** | 完全依赖外部输入，按 §4 重写 |
| e2e_metrics.experiment_validity | `e2e_metrics.py:182-192` | PARTIALLY_VALID | 仅查 tags，需查内容 |
| e2e_metrics.validation_reliability | `e2e_metrics.py:194-203` | PARTIALLY_VALID | paper.exists()=1.0 需修正 |
| e2e_metrics.innovation | `e2e_metrics.py:205-218` | PARTIALLY_VALID | pattern 引用计数合理，但无实验支撑验证 |
| e2e_metrics.writing_completeness | `e2e_metrics.py:220-236` | VALID | 结构计数确定性可靠 |
| e2e_metrics.end_to_end | `e2e_metrics.py:238-244` | **INVALID** | 完全依赖 response.total |
| e2e_metrics.measurement_integrity | `e2e_metrics.py:261-287` | PARTIALLY_VALID | created_by 前缀可伪造 |
| score_artifact.py | `score_artifact.py` | PARTIALLY_VALID | verdict 逻辑正确，但信任分卡输入 |
| score_compute.py (5 卡) | `score_compute.py` | **NEEDS_REDESIGN** | 关键词匹配可游戏化，需改为存在性+内容证据 |
| aggregate_scores.py | `aggregate_scores.py` | VALID | 聚合逻辑正确，有 --verify 防手写 |
| benchmark.py bench_score | `benchmark.py:219-299` | PARTIALLY_VALID | 信任 agent 自报 hits |
| bench_mmbench.py | `bench_mmbench.py` | VALID | 格式转换工具，非能力评估 |
| weight_profiles.py | `weight_profiles.py` | PARTIALLY_VALID | 权重逻辑正确，但 env 可运行时覆盖 |
| evidence_gate.py | `evidence/evidence_gate.py` | PARTIALLY_VALID | E1-E3 正确，E4/E8 不查内容 |
| quality/evaluators.py | `quality/evaluators.py` | PARTIALLY_VALID | 七维结构检查好，但不查 data 非空 |
| quality/contract.py | `quality/contract.py` | VALID | 契约设计良好 |
| quality/aggregator.py | `quality/aggregator.py` | VALID | 聚合逻辑正确 |
| modules/formula_checker.py | `modules/formula_checker.py` | PARTIALLY_VALID | 语法检查正确，无变量引用校验 |
| modules/assumption_validator.py | `modules/assumption_validator.py` | PARTIALLY_VALID | 矛盾检测覆盖率不足 |
| modules/symbol_registry.py | `modules/symbol_registry.py` | PARTIALLY_VALID | 仅表格提取，不扫全文 |
| modules/* (其余 18 个) | `modules/` | PARTIALLY_VALID | 结构/语法级检查有效，需逐一审计内容级覆盖 |
| fidelity_gate.py | `P13-3D/scripts/fidelity_gate.py` | **NEEDS_REDESIGN** | 空 artifact→1.0；modification/renaming 未实现 |
| stc_evaluator.py | `P13-3D/scripts/stc_evaluator.py` | PARTIALLY_VALID | 字符串包含，需内容级检查 |
| model_construction.py | `P13-3D/scripts/model_construction.py` | PARTIALLY_VALID | structural/alignment 好，mathematical 依赖自报 |
| source_of_truth_gate.py | `P13-3D/scripts/source_of_truth_gate.py` | VALID | 引用校验+hash，设计良好 |
| input_freeze_gate.py | `P13-3D/scripts/input_freeze_gate.py` | VALID | hash+schema+frozen，设计良好 |
| P15/scripts/* (4 文件) | `research/P15/scripts/` | VALID | benchmark 数据健康检查，非能力评估 |

### 6.3 汇总统计

| Status | 数量 | 占比 |
|--------|------|------|
| VALID | 8 | 24% |
| PARTIALLY_VALID | 20 | 59% |
| INVALID | 2 | 6% |
| NEEDS_REDESIGN | 4 | 12% |
| **总计** | **34** | 100% |

---

## 7. 实施路线图（research 层优先）

### Phase 3b.1 — 前置条件修复（P0，1 周）
1. 在 ArtifactRegistry 增加 `is_empty()` 方法
2. 在 e2e_metrics.py 所有计数前过滤空 artifact
3. 在 quality/evaluators.py 增加 data non-emptiness 检查
4. 修复 fidelity_gate 空 artifact→1.0 问题

### Phase 3b.2 — Model Construction Evaluator 实现（P0，2 周）
1. 在 `research/P15/measurement_recovery/` 实现 `model_construction_v2.py`
2. 实现 L1-L4 全部 deterministic checks
3. 定义 semantic judge 的 prompt template + 输出 schema
4. 用 B0 空壳 + adversarial test cases 验证

### Phase 3b.3 — Method Selection Quality 实现（P1，1 周）
1. 实现 MSQ-1 至 MSQ-4
2. 方法卡增加 `applicability.problem_types` 字段
3. 验证 gold=TOPSIS, agent=AHP 不自动判 wrong

### Phase 3b.4 — score_compute 重设计（P1，2 周）
1. 关键词匹配改为存在性检查（0/1）
2. 程度评分基于内容证据
3. 5 卡均增加 artifact non-emptiness 前置条件

### Phase 3b.5 — 验证与迁入（P2，1 周）
1. adversarial benchmark 验证所有新 evaluator
2. 与旧 evaluator 并行运行对比
3. 验证通过后考虑迁入 core/

---

## 8. Pre-registered Thresholds

以下阈值在本协议中锁定，评估时不得修改：

| 参数 | 值 | 适用范围 |
|------|-----|---------|
| L1 sub_question Jaccard 阈值 | 0.3 | L1.1 |
| L1 coverage PASS 阈值 | 80% | L1.1-L1.5 |
| L2 variable semantic 完整率 PASS | 90% | L2.1, L2.3 |
| L2 constraint 有效率 PASS | 90% | L2.3 |
| L2 equation var coverage | 50% | L2.6 |
| L3 feasibility PASS | 95% | L3.2 |
| L3 convergence 残差阈值 | 1e-6 | L3.3 |
| L3 stability relative std PASS | 5% | L3.4 |
| L3 seed 值 | 42 | L3.5 |
| L4 robustness 性能下降 PASS | < 20% | L4.3 |
| evidence_gate min_coverage | 0.8 | E7 |
| source_of_truth precision | 0.95 | SOT Gate |
| weight clamp range | [0.7, 1.5] | weight_profiles |
| review pass_score | 6.0 | score_artifact |
| review max_rounds | 4 | score_artifact |

---

*文档结束。本协议为 research 层设计文档，验证后再考虑迁入 core/。*
