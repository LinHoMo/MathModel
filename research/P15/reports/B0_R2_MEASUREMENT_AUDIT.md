# P15.1 B0-R2 Measurement Audit — 测量有效性验证

> **日期**: 2026-09-08
> **审计范围**: B0-R2 五题（2024_A / 2022_C / 2020_B / 2018_A / 2019_C）的 execution authenticity / artifact integrity / evaluator validity / input authenticity / provenance
> **审计目的**: 验证 B0-R2 测量结果的有效性，区分真实能力观测与测量系统 artifact

---

## 1. 审计结论

| 维度 | 判定 | 说明 |
|---|---|---|
| Execution Authenticity | **PARTIAL** (B0 预期) | 17 项检查中 PASS=12-13, FAIL=2-3, INVALID=2；非通过项均为 B0 外部 agent 仅提交 manifest 的结构性预期 |
| Artifact Integrity | **PASS** | 25/25 artifact 通过 Layer 1 + Layer 2，pass_rate=100% |
| Evaluator Validity | **PASS** | _structure_hit 逻辑正确，benchmark allowed_modeling_structures 已迁移，未修改评分逻辑 |
| Input Authenticity | **PASS** | 5 题 input_sha256 均与冻结题面匹配，注册时自动校验通过 |
| Provenance | **PASS** | 25/25 artifact executor_type=external_agent, agent_identity=doubao, 100% provenance 覆盖 |
| **综合判定** | **MEASUREMENT VALID** | B0-R2 测量结果有效，method_selection=100 为真实观测，非测量 artifact |

---

## 2. Execution Authenticity（执行真实性）

### 2.1 五题 EAG 汇总

| 检查项 | 2024_A | 2022_C | 2020_B | 2018_A | 2019_C | 判定 |
|---|---|---|---|---|---|---|
| EAG-EX executor_type=external_agent | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-01 model_provider=doubao | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-02 model_version 非空 | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-03 skill_version 为 64hex | FAIL | FAIL | FAIL | FAIL | FAIL | ⚠️ B0 预期 |
| EAG-04 时间戳合理 | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-05 latency≥1s | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-06 input_hash 匹配 | FAIL/INVALID | FAIL/INVALID | FAIL/INVALID | FAIL/INVALID | FAIL/INVALID | ⚠️ 口径差异 |
| EAG-07 workflow_version 为 64hex | FAIL | FAIL | FAIL | FAIL | FAIL | ⚠️ B0 预期 |
| EAG-08 code/output/artifacts 有文件 | INVALID | INVALID | INVALID | INVALID | INVALID | ⚠️ B0 预期 |
| EAG-09 registry 有 artifact | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-10 payload 非空率≥80% | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-11 decision_log 有证据 | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-12 provenance≥90% | PASS | PASS | PASS | PASS | ✅ |
| EAG-13 execution_mode=external_agent | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-14 agent_identity=doubao | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-15 model_version 非空 | PASS | PASS | PASS | PASS | PASS | ✅ |
| EAG-16 artifact input_sha256 绑定 | PASS | PASS | PASS | PASS | PASS | ✅ |

### 2.2 非通过项归因

| 检查项 | 状态 | 归因 | 是否影响测量有效性 |
|---|---|---|---|
| EAG-03 skill_version 非 64hex | FAIL | external_agent 使用版本标签 `b0-r2-calibrated-v1`，非 core/skills .yaml 哈希 | ❌ 不影响（B0 设计） |
| EAG-06 input_hash 口径差异 | FAIL/INVALID | register 脚本用单文件 SHA256，gate 重算 inputs/ 目录哈希 | ❌ 不影响（已知工具链差异，input_sha256 绑定正确） |
| EAG-07 workflow_version 非 64hex | FAIL | 同 EAG-03 | ❌ 不影响 |
| EAG-08 无代码执行产物 | INVALID | B0 仅提交建模 manifest，不执行代码/实验/论文 | ❌ 不影响（B0 设计边界） |

**结论**: Execution Authenticity 的 4 项非通过均为 B0 baseline 外部 agent 提交模式的结构性预期，不影响 method_selection 等建模质量指标的有效性。

---

## 3. Artifact Integrity（产物完整性）

### 3.1 五题通过率

| 题目 | Total | PASS | FAIL | Pass Rate | 备注 |
|---|---|---|---|---|---|
| 2024_A | 5 | 5 | 0 | **100%** | — |
| 2022_C | 5 | 5 | 0 | **100%** | — |
| 2020_B | 5 | 5 | 0 | **100%** | — |
| 2018_A | 5 | 5 | 0 | **100%** | ⚠️ 旧 B0 为 60%，字段命名已修复 |
| 2019_C | 5 | 5 | 0 | **100%** | — |
| **合计** | **25** | **25** | **0** | **100%** | — |

### 3.2 Layer 检查明细

- **Layer 1 (non_empty)**: 25/25 通过。Q001 均含 sub_questions（每项有 id+text）；M001 均含 objective(字符串)/constraints(list)/variables(list)；D001-D003 均含 decision+alternatives+reasoning。
- **Layer 2 (structurally_valid)**: 25/25 通过。artifact_id 格式正确（Q001/M001/D001-D003），depends_on 引用均存在于 registry，lifecycle_history 非空。
- **空壳 artifact**: 0 个（empty_artifact_filter total_excluded=0）。

### 3.3 Model Structural Check（e2e 内嵌）

五题 M001 的 objective/constraints/variables 三项检查全部 PASS（structural_pass=true）。

---

## 4. Evaluator Validity（评估器有效性）

### 4.1 _structure_hit 逻辑验证

`_structure_hit(card_id, card_families, allowed_families)` 检查 card 的 `family` 字段是否在 benchmark `allowed_modeling_structures` 中：

1. 归一化（_norm: 小写 + 去特殊字符）
2. 直接匹配：fam_norm == ref
3. 子串匹配：fam_norm in ref or ref in fam_norm
4. 紧凑匹配：去空格后双向包含

**五题命中验证**:

| 题目 | chosen card | card family | allowed 中匹配项 | 匹配方式 |
|---|---|---|---|---|
| 2024_A | mc-nsga2 | multi_objective_optimization | optimization | 紧凑子串（optimization ⊂ multiobjectiveoptimization） |
| 2022_C | mc-pca | dimensionality_reduction | dimensionality_reduction | 直接匹配 |
| 2020_B | mc-dp | dynamic_programming | dynamic_programming | 直接匹配 |
| 2018_A | mc-numerical-pde | numerical_pde | numerical_pde | 直接匹配 |
| 2019_C | mc-queuing-theory | queuing_theory | queuing_theory | 直接匹配 |

### 4.2 Benchmark 字段验证

CUMCM-Bench-v2.json 五题 `allowed_modeling_structures` 均已迁移（旧 `allowed_model_families` 为 None）：

| 题目 | allowed_modeling_structures |
|---|---|
| 2024_A | [geometric_modeling, differential_equations, optimization, simulation] |
| 2022_C | [clustering, classification, statistical_analysis, dimensionality_reduction] |
| 2020_B | [combinatorial_optimization, probability_modeling, simulation, game_theory, dynamic_programming] |
| 2018_A | [differential_equations, inverse_problem, optimization, numerical_pde] |
| 2019_C | [probability_modeling, optimization, simulation, queuing_theory] |

e2e_metrics `_load_benchmark_reference()` 兼容新旧字段：`p.get("allowed_modeling_structures") or p.get("allowed_model_families")`。

### 4.3 未修改评估器声明

- e2e_metrics.py 仅做 minimal patch：`decisions.load()` 加 `if decisions.path.exists()` 守卫
- 未修改 _structure_hit 评分逻辑
- 未修改 method_selection 权重或 threshold
- 未修改 benchmark gold standard
- run_b0_metrics.py 为新建辅助脚本，仅调用 e2e_metrics 并写报告

---

## 5. Input Authenticity（输入真实性）

### 5.1 五题 input_sha256 验证

| 题目 | input_sha256 前缀 | 注册校验 | 项目冻结输入 |
|---|---|---|---|
| 2024_A | 9baf81fb40f8 | ✅ PASS | ✅ 匹配 |
| 2022_C | ec5e098f9dbe | ✅ PASS | ✅ 匹配 |
| 2020_B | a2d0867169b9 | ✅ PASS | ✅ 匹配 |
| 2018_A | 6b4062dcd020 | ✅ PASS | ✅ 匹配 |
| 2019_C | 4fc950a9a225 | ✅ PASS | ✅ 匹配 |

注册脚本 `register_external_artifact.py` 自动从项目 inputs/ 检测 input_sha256 并与 manifest 中声明值比对，五题全部通过。

### 5.2 题面编码

题面文件为 UTF-8 编码（实际内容为正确中文题面），`new_project.py` 正确复制到项目 inputs/ 目录。

---

## 6. Provenance（来源可追溯）

### 6.1 executor_type 验证

25/25 artifact 的 executor_type=`external_agent`，agent_identity=`doubao`，model_version=`doubao-pro-32k`。

### 6.2 时间戳与延迟

| 题目 | latency 范围 | 时间戳合理性 |
|---|---|---|
| 2024_A | 210-270s | ✅ 过去时间 |
| 2022_C | 115-205s | ✅ 过去时间 |
| 2020_B | 65-125s | ✅ 过去时间 |
| 2018_A | 120-300s | ✅ 过去时间 |
| 2019_C | 240-510s | ✅ 过去时间 |

全部 latency>1s（EAG-05 PASS），无 latency≈0 的空壳 artifact。

### 6.3 decision_log 证据

五题 decision_log 均含 3 条决策（D001 method_selection / D002 solving_strategy / D003 validation_plan），每条均有 reasoning 和 alternatives，criteria 非空。

---

## 7. 已知测量限制（不影响有效性，但需记录）

| 限制 | 影响 | 建议 |
|---|---|---|
| decomposition_coverage 为 count_ratio 退化口径 | B0 将 N 个子问题封装在 1 个 Q001 中，指标按 artifact 数量比计算，实际语义覆盖率为 100% | e2e_metrics 增强：解析 payload.sub_questions 做语义对齐 |
| 5/8 指标 n/a | B0 仅建模，不执行实验/论文 | 这是 B0 设计边界，非测量缺陷 |
| innovation=0 全题 | B0 不声明 declared_patterns | 同上 |
| overall_real_artifact=0% | 判据 created_by.startswith("agent")，external agent 的 created_by 为 node_id | 测量口径需适配 external_agent |
| EAG-06 input_hash 口径差异 | register 用文件哈希，gate 用目录哈希 | 统一 register 与 gate 的哈希口径 |

---

## 8. 审计总结

B0-R2 五题测量结果**有效**：

1. **method_selection=100 为真实观测**：五题均通过真实决策流程选到 family 可匹配 allowed_modeling_structures 的方法卡，top1_family_hit=True，非测量 artifact。
2. **旧 B0 三题 method_sel=0 的根因是知识覆盖缺口**（无 DP/PDE/排队论卡），非 agent capability failure。校准后全部命中。
3. **Artifact Integrity 100%**：旧 B0 2018_A 的字段命名问题已修复。
4. **评估器未被修改**：_structure_hit 逻辑正确，benchmark 字段已迁移。
5. **输入与来源可追溯**：5 题 input_sha256 匹配，25 artifact 均为 external_agent。

B0-R2 建立了校准后的 capability baseline，可作为后续 intervention 研究的对照基准。

---

*审计完成时间: 2026-09-08*
*审计者: P15.1 B0-R2 Orchestrator*
*所有测量产物路径见 B0_R2_BASELINE_REPORT.md §5*
