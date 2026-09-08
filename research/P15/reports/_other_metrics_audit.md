# P15 其他指标深度审计报告 — innovation / model_correctness / None metrics / measurement integrity

> **审计范围**：B0 基线五题（2018_A, 2019_C, 2020_B, 2022_C, 2024_A）
> **审计性质**：只诊断，不修复
> **审计日期**：2026-09-08
> **数据来源**：`projects/p151-*-b0/state/{registry,decision_log,e2e_metrics_report}.json` + `core/tools/e2e_metrics.py` + `research/P15/measurement_recovery/register_external_artifact.py`

---

## 0. B0 项目 artifact 集基线（五题一致）

每个 B0 项目 registry 中恰好 **5 个 artifact**：

| ID | 类型 | created_by | 说明 |
|---|---|---|---|
| Q001 | question | `problem_understanding` | 问题理解与分解 |
| M001 | model | `model_construction` | 模型构建 |
| D001 | decision | `method_selection` | 方法选择决策 |
| D002 | decision | `solving_strategy` | 求解策略决策 |
| D003 | decision | `validation_plan` | 验证计划决策 |

**无** result / experiment / figure / assumption / claim / paper_section 类型 artifact。
**无** `state/status.json` 文件。
所有 artifact 均通过 `register_external_artifact.py` 注册，`provenance.executor_type = "external_agent"`，`provenance.agent_identity = "doubao"`。

---

## A. innovation = 0（全部五题）

### A.1 指标代码逻辑（e2e_metrics.py L418-431）

```python
pat_refs = [ref.get("id", "") for d in decisions.decisions.values()
            if d.active for ref in (d.knowledge_refs or [])
            if str(ref.get("id", "")).startswith("pat-")]
if pat_refs:
    exp_qs = {e.question for e in reg.list_by_type("experiment")}
    backed = sum(1 for d in decisions.decisions.values()
                 if d.active and any(str(r.get("id", "")).startswith("pat-")
                                     for r in (d.knowledge_refs or []))
                 and d.question in exp_qs)
    innov_value = round(100.0 * backed / len(pat_refs), 1)
else:
    innov_value = 0.0
innov_detail = {"declared_patterns": len(pat_refs)}
```

### A.2 decision_log 实际内容检查（五题逐题验证）

对全部 5 个项目的 `state/decision_log.json` 进行字段级检查：

| 项目 | decisions 数量 | 含 knowledge_refs 字段？ | pat- 引用数 |
|---|---|---|---|
| p151-2018a-b0 | 3 (D001/D002/D003) | **否** | 0 |
| p151-2019c-b0 | 3 (D001/D002/D003) | **否** | 0 |
| p151-2020b-b0 | 3 (D001/D002/D003) | **否** | 0 |
| p151-2022c-b0 | 3 (D001/D002/D003) | **否** | 0 |
| p151-2024a-b0 | 3 (D001/D002/D003) | **否** | 0 |

每个 decision 的字段集为：`decision_id, question, chosen, alternatives, criteria, evidence_ids, reasoning, confidence, reversible, created_by, created_at, status, executor_type, agent_identity`。**`knowledge_refs` 字段完全不存在。**

`e2e_metrics_report.json` 中五题均显示 `"declared_patterns": 0`，与实际检查一致。

### A.3 根因追溯：为什么 decision_log 没有 knowledge_refs？

`register_external_artifact.py` 的 `_update_decision_log()` 函数（L368-428）构建 decision entry 时，字段列表中**不包含** `knowledge_refs`：

```python
decision_entry = {
    "decision_id": artifact_id,
    "question": f"{manifest.node_id} output",
    "chosen": ...,
    "alternatives": alternatives,
    "criteria": criteria,
    "evidence_ids": manifest.payload.get("depends_on", []),
    "reasoning": ...,
    "confidence": ...,
    "reversible": True,
    "created_by": manifest.node_id,
    ...
}
```

即使 manifest payload 中包含创新模式声明，注册管道也不会将其映射到 `knowledge_refs` 字段。

### A.4 前缀不匹配：pat- vs ip-

`core/knowledge/patterns/` 目录下全部 6 个 pattern 文件：

| 文件 | pattern_id |
|---|---|
| ip-cluster-then-model.yaml | `ip-cluster-then-model` |
| ip-combined-weighting.yaml | `ip-combined-weighting` |
| ip-mechanism-data-hybrid.yaml | `ip-mechanism-data-hybrid` |
| ip-pareto-select.yaml | `ip-pareto-select` |
| ip-two-stage-evaluation.yaml | `ip-two-stage-evaluation` |
| ip-uncertainty-overlay.yaml | `ip-uncertainty-overlay` |

**全部使用 `ip-` 前缀**，而 innovation 指标代码检查 `startswith("pat-")`。在整个 `core/` 目录中，`pat-` 仅出现在 e2e_metrics.py 的第 421 行和第 425 行（即 innovation 检查本身），无任何 pattern 定义使用此前缀。

这意味着：**即使 decision_log 中有 knowledge_refs 且引用了 patterns 库中的 pattern，其 id 也是 `ip-*` 而非 `pat-*`，innovation 仍会判定为 0。**

### A.5 B0 model/decision artifact 是否引用了任何 pattern？

- M001 (model) payload 包含 `model_type`, `model_family`, `assumptions`, `variables`, `objective`, `constraints` 等字段，但**无 pattern 引用字段**。
- D001-D003 (decision) 的 `chosen` 字段包含方法描述文本（如"采用多体刚体链运动学递推 + 阿基米德螺线参数化"），但**无结构化的 knowledge_refs / pattern_refs**。
- B0 manifest 中未要求 agent 声明创新模式引用。

### A.6 归因结论

| 候选原因 | 判定 | 依据 |
|---|---|---|
| a. Agent 真的没有声明任何创新模式 | **部分成立** | B0 manifest 格式未要求 pattern 引用，agent 无渠道声明 |
| b. 指标定义只检查 pat- 前缀，而 pattern 库使用 ip- 前缀 | **成立（测量缺陷）** | 6/6 patterns 使用 ip-，代码检查 pat- |
| c. B0 阶段本就不要求创新声明 | **不成立** | B0 包含 method_selection 和 solving_strategy 决策，理论上可声明创新模式；但注册管道不捕获此字段 |

**最终归因：measurement_failure（双重缺陷）**

1. **结构缺陷**：`register_external_artifact.py` 的 decision_log 写入路径不包含 `knowledge_refs` 字段，导致即使 agent 声明了创新模式也无法被指标读取。
2. **前缀缺陷**：指标代码检查 `pat-` 前缀，但 pattern 库统一使用 `ip-` 前缀，二者不一致。

**指标设计评价**：当前 innovation 指标将"未声明创新"和"声明了但无实验支撑"混为一谈——两者都输出 0.0。合理设计应区分：
- `declared_patterns = 0` → 应输出 `None`（未声明，不适用）而非 0.0
- `declared_patterns > 0` 但 `backed = 0` → 才是真正的 0.0（声明了但无证据）

---

## B. model_correctness = None（全部五题）

### B.1 指标代码逻辑（e2e_metrics.py L356-393）

- 外部评分 `model_correctness_pct` 为 null/n/a/缺失 → `value = None`（UNAVAILABLE）
- 同时执行 structural check：检查 model artifact 的 `objective` / `constraints` / `variables` 字段
- structural check 结果记入 detail，但不影响 value

### B.2 五题 structural check 逐题结果

| 项目 | value | structural_pass | M001.objective | M001.constraints | M001.variables | models_checked |
|---|---|---|---|---|---|---|
| p151-2018a-b0 | None | **PASS** | true | true | true | 1 |
| p151-2019c-b0 | None | **PASS** | true | true | true | 1 |
| p151-2020b-b0 | None | **PASS** | true | true | true | 1 |
| p151-2022c-b0 | None | **PASS** | true | true | true | 1 |
| p151-2024a-b0 | None | **PASS** | true | true | true | 1 |

**五题全部 structural PASS**，M001 均包含完整的 objective、constraints、variables 三要素。

以 2024_A 为例，M001 payload 包含：
- `objective`: 明确的优化/求解目标
- `constraints`: 刚体约束、螺线约束、速度约束等
- `variables`: 9+ 个定义完整的变量（含 symbol/definition/unit）

### B.3 structural PASS 能说明什么？

structural check 仅验证 model artifact 具有**基本结构完整性**（三要素字段非空），**不能**说明：
- 模型公式是否正确
- 假设是否合理
- 变量定义是否无矛盾
- 模型是否能产出正确结果

它是一个**最低门槛的完整性检查**，类似于"论文有摘要、有正文、有参考文献"，不代表内容质量。

### B.4 归因结论

| 候选原因 | 判定 |
|---|---|
| measurement gap（没有语义评分器） | **成立** | model_correctness_pct 依赖外部人工/LLM 评分，B0 未执行此评分 |
| B0 阶段限制（不做实验所以无法评分） | **成立** | 语义正确性通常需要实验结果对照验证，B0 不含实验执行 |
| capability_failure | **不成立** | model artifact 存在且结构完整，structural 全 PASS |

**最终归因：measurement_gap + not_applicable（混合）**

- `value=None` 的直接原因是外部评分缺失（measurement_gap）。
- 但 B0 阶段本就不包含模型验证实验，即使有语义评分器也缺乏实验证据支撑评分（not_applicable）。
- structural check 全 PASS 表明 model artifact 的**结构完整性无问题**，这是 B0 阶段能确认的最高限度。

---

## C. experiment_validity = None（全部五题）

### C.1 指标代码逻辑（e2e_metrics.py L395-405）

```python
robust = [r for r in results if ROBUSTNESS_TAGS & set(r.tags or [])]
robust_ratio = (len(robust) / len(results)) if results else None
multi_run = sum(1 for r in results if (r.data or {}).get("runs", 1) >= 5)
exp_components = [v for v in (robust_ratio,) if v is not None]
exp_value = round(100.0 * sum(exp_components) / len(exp_components), 1) if exp_components else None
```

### C.2 五题结果

| 项目 | results 数量 | with_robustness_tags | multi_run_ge5 | value |
|---|---|---|---|---|
| p151-2018a-b0 | 0 | 0 | 0 | None |
| p151-2019c-b0 | 0 | 0 | 0 | None |
| p151-2020b-b0 | 0 | 0 | 0 | None |
| p151-2022c-b0 | 0 | 0 | 0 | None |
| p151-2024a-b0 | 0 | 0 | 0 | None |

`results` 为空列表 → `robust_ratio = None` → `exp_components = []` → `exp_value = None`。

### C.3 归因结论

**B0 registry 中无任何 result 类型 artifact**（五题一致）。B0 最小 artifact 集为 question + model + decision，不含 experiment_execution 和 result_analysis 节点。

**最终归因：not_applicable（B0 阶段限制）**

- B0 基线仅覆盖 problem_understanding → model_construction → method_selection → solving_strategy → validation_plan 五个节点。
- 实验设计（experiment_design）、实验执行（experiment_execution）、结果分析（result_analysis）均为下游节点，不在 B0 范围内。
- D003 (validation_plan) 仅声明了验证策略（如"刚体约束守恒验证""敏感性分析"），但未执行。
- **不应视为 capability_failure**：agent 按 B0 协议只交付了约定范围内的 artifact。

---

## D. validation_reliability = None（全部五题）

### D.1 指标代码逻辑（e2e_metrics.py L407-416）

```python
claims_total = int(st.get("evidence", {}).get("claims_total", 0) or 0)
claims_supported = int(st.get("evidence", {}).get("claims_supported", 0) or 0)
support_ratio = (claims_supported / claims_total) if claims_total else None
val_components = [v for v in (support_ratio,) if v is not None]
paper = project_dir / "paper" / "main.tex"
if paper.exists():
    val_components.append(1.0)
val_value = round(100.0 * sum(val_components) / len(val_components), 1) if val_components else None
```

### D.2 五题 status.json 检查

| 项目 | status.json 存在？ | evidence.claims_total | evidence.claims_supported | paper/main.tex | value |
|---|---|---|---|---|---|
| p151-2018a-b0 | **否** | 0 (默认) | 0 (默认) | 否 | None |
| p151-2019c-b0 | **否** | 0 (默认) | 0 (默认) | 否 | None |
| p151-2020b-b0 | **否** | 0 (默认) | 0 (默认) | 否 | None |
| p151-2022c-b0 | **否** | 0 (默认) | 0 (默认) | 否 | None |
| p151-2024a-b0 | **否** | 0 (默认) | 0 (默认) | 否 | None |

`_load_project()` 调用 `ProjectState(sdir / "status.json")`，文件不存在时 `st` 为空 dict → `claims_total = 0` → `support_ratio = None` → `val_components = []`（无 paper）→ `value = None`。

### D.3 归因结论

**最终归因：not_applicable（B0 阶段限制）**

- claims 由 `evidence_build` 节点生成，该节点在实验执行之后，不在 B0 范围内。
- `status.json` 由 V3 runtime 的状态机维护，B0 通过外部注册管道提交 artifact，不经过 runtime 状态机，因此不产生 status.json。
- paper/main.tex 由 writer hand 生成，远在 B0 之后。
- D003 (validation_plan) 声明了验证计划但未执行，无 claims 产出。
- **不应视为 capability_failure**。

---

## E. writing_completeness = None / end_to_end = None（全部五题）

### E.1 writing_completeness（e2e_metrics.py L433-449）

```python
wc_value = None
wc_detail = {"main_tex": paper.exists()}
if paper.exists():
    # 统计 figures/tables/equations/references 并计算完成率
```

五题 `paper/main.tex` 均不存在 → `value = None`，`detail.main_tex = false`。

### E.2 end_to_end（e2e_metrics.py L451-457）

```python
total = response.get("total") or {}
e2e_value = None
if total.get("max_score"):
    e2e_value = round(100.0 * float(total.get("awarded", 0)) / float(total["max_score"]), 1)
```

五题 `response` 中无 `total.max_score`（B0 未执行 rubric 评分）→ `value = None`。

### E.3 归因结论

| 指标 | 归因 | 理由 |
|---|---|---|
| writing_completeness | **not_applicable** | B0 不包含论文写作，main.tex 不存在是预期状态 |
| end_to_end | **not_applicable** | end_to_end 需要完整 pipeline 产出 + rubric 人工/LLM 评分，B0 仅覆盖前 5 个节点 |

**这两个指标在 B0 阶段应明确标记为"超出 B0 范围（out_of_scope）"**，而非简单的 None。当前 None 语义模糊——既可能表示"测量失败"也可能表示"不适用"，建议在 B0 报告中显式区分。

---

## F. measurement_integrity（provenance-based realization v1）

### F.1 指标代码逻辑（e2e_metrics.py L484-510）

```python
agent = lambda a: str(getattr(a, "created_by", "") or "").startswith("agent")
agent_created = sum(1 for a in registry.all() if agent(a))
total = len(registry.all())
```

判据：`created_by.startswith("agent")` → 视为"agent 真实登记的产物"。

### F.2 五题 overall_real_artifact

| 项目 | numerator (agent-created) | denominator (total) | value |
|---|---|---|---|
| p151-2018a-b0 | 0 | 5 | 0.0 |
| p151-2019c-b0 | 0 | 5 | 0.0 |
| p151-2020b-b0 | 0 | 5 | 0.0 |
| p151-2022c-b0 | 0 | 5 | 0.0 |
| p151-2024a-b0 | 0 | 5 | 0.0 |

分类型 realization（五题一致）：
- experiment_realization: 0/0 = None（无 experiment artifact）
- validation_realization: 0/0 = None（无 claim artifact）
- writing_realization: 0/0 = None（无 paper_section artifact）

### F.3 created_by 实际值检查（以 2024a-b0 为例，五题一致）

| Artifact | created_by | startswith("agent")? |
|---|---|---|
| Q001 | `problem_understanding` | 否 |
| M001 | `model_construction` | 否 |
| D001 | `method_selection` | 否 |
| D002 | `solving_strategy` | 否 |
| D003 | `validation_plan` | 否 |

**5/5 artifact 的 created_by 均为角色名（node_id），无一以 "agent" 开头。**

### F.4 根因追溯

`register_external_artifact.py` L201：

```python
"created_by": manifest.node_id,
```

外部注册管道将 `created_by` 设为 manifest 的 `node_id`（即角色名如 `problem_understanding`），而非 `agent_xxx` 格式。

但 artifact 的 `provenance` 字段中**确实包含**完整的执行来源信息：
```json
"provenance": {
    "executor_type": "external_agent",
    "agent_identity": "doubao",
    "model_version": "...",
    "node_id": "method_selection",
    ...
}
```

### F.5 归因结论

**最终归因：measurement_failure（判据设计缺陷）**

v1 判据 `created_by.startswith("agent")` 存在以下问题：

1. **仅适用于内部 V3 runtime**：内部 runtime 可能以 `agent_<role>` 格式设置 created_by，但外部注册管道使用 `node_id`（角色名）。
2. **忽略 provenance 字段**：artifact 的 provenance 中明确记录了 `executor_type: "external_agent"` 和 `agent_identity: "doubao"`，这些是比 created_by 前缀更可靠的来源证据，但 v1 判据完全不读取。
3. **0/5 = 0% 的结论具有误导性**：实际上 5/5 artifact 都是由 agent (doubao) 真实产出的，只是 created_by 字段格式不符合判据预期。

**v1 判据合理性评价**：作为"provenance-based realization"的初版，`startswith("agent")` 是一个过于脆弱的字符串匹配判据。更合理的 v2 判据应：
- 检查 `provenance.executor_type in ("agent", "external_agent", "llm")`
- 或检查 `created_by` 非空且 `provenance.agent_identity` 非空
- 或白名单匹配已知角色名集合

---

## G. empty_artifact_filter（artifact integrity）

### G.1 五题结果

| 项目 | total_excluded | registry_empty_total | question 空壳 | result 空壳 | model 空壳 |
|---|---|---|---|---|---|
| p151-2018a-b0 | 0 | 0 | 0 | 0 | 0 |
| p151-2019c-b0 | 0 | 0 | 0 | 0 | 0 |
| p151-2020b-b0 | 0 | 0 | 0 | 0 | 0 |
| p151-2022c-b0 | 0 | 0 | 0 | 0 | 0 |
| p151-2024a-b0 | 0 | 0 | 0 | 0 | 0 |

### G.2 分析

`_is_empty_artifact()` 判据：payload 为 None/[] 且 data 为 None/{}/或 data 内嵌 payload=[]。

B0 五题的全部 25 个 artifact（5 题 × 5 artifact）均通过非空检查：
- Q001: payload 包含 title, problem_type, sub_questions, key_variables 等
- M001: payload 包含 model_type, assumptions, variables, objective, constraints 等
- D001-D003: payload 包含 decision/chosen, alternatives, criteria, reasoning 等

**无空壳 artifact**。

### G.3 归因结论

**artifact integrity 在 B0 阶段不是问题维度。** 所有 artifact 均有实质内容，空壳过滤无需排除任何 artifact。这表明 `register_external_artifact.py` 的 manifest 验证（要求 payload non-empty）有效防止了空壳注册。

---

## 6. 总结归因表

| 指标 | 五题值 | 归因分类 | 核心原因 | 严重程度 |
|---|---|---|---|---|
| **innovation** | 0.0 | **measurement_failure** | ① decision_log 注册管道不含 knowledge_refs 字段；② 代码检查 `pat-` 前缀但 pattern 库使用 `ip-` 前缀 | 高 |
| **model_correctness** | None | **measurement_gap + not_applicable** | 外部语义评分缺失；B0 无实验无法验证正确性；structural check 全 PASS | 中 |
| **experiment_validity** | None | **not_applicable** | B0 不含实验执行节点，无 result artifact | 低 |
| **validation_reliability** | None | **not_applicable** | 无 status.json（外部注册不经过 runtime 状态机）；无 claims；无 paper | 低 |
| **writing_completeness** | None | **not_applicable** | B0 不含论文写作，无 main.tex | 低 |
| **end_to_end** | None | **not_applicable** | B0 未完成全流程，无 rubric 评分 | 低 |
| **measurement_integrity** | 0.0 | **measurement_failure** | v1 判据 `created_by.startswith("agent")` 不适用于外部注册（created_by 为角色名）；provenance 字段未被利用 | 高 |
| **empty_artifact_filter** | 0 排除 | **无问题** | 全部 25 个 artifact 均有实质内容 | — |

### 归因分类定义

- **measurement_failure**：指标定义/实现与实际数据格式不匹配，导致指标值不能反映真实能力。需要修复指标代码或注册管道。
- **measurement_gap**：指标依赖的外部输入（如人工评分）缺失，无法计算。需要补充评分流程。
- **not_applicable**：指标评估的能力维度不在 B0 阶段范围内。应在报告中显式标记为 out_of_scope，而非 None。
- **capability_failure**：Agent 在其应交付的范围内未能产出合格 artifact。本次审计中**无**此类归因。

### 关键发现

1. **B0 无 capability_failure**：所有 B0 约定范围内的 artifact（question/model/decision）均已交付且结构完整、非空壳。
2. **两个 measurement_failure 需优先修复**：
   - innovation 的双重缺陷（knowledge_refs 缺失 + pat-/ip- 前缀不匹配）
   - measurement_integrity 的 created_by 判据不适用于外部注册
3. **五个 None 指标中四个是 not_applicable**：experiment_validity, validation_reliability, writing_completeness, end_to_end 均超出 B0 范围，建议在 B0 报告模板中显式标记 `out_of_scope` 而非依赖 None 语义。
4. **model_correctness 的 structural check 是 B0 阶段唯一有意义的模型质量信号**，五题全 PASS，建议在 B0 报告中将其从 detail 提升为显式指标（如 `model_structural_completeness`）。

---

*审计完成。未修改任何源码、registry、decision_log 或项目文件。*
