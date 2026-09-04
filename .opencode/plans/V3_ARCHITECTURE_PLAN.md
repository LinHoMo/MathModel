# MathModel v3 Architecture Refactoring Plan

> **Date**: 2026-09-04
> **Status**: DRAFT — 待用户确认后执行
> **Scope**: 从 "四手线性流水线" 升级为 "认知核心 + 证据图谱 + DAG 工作流 + 竞赛知识图谱"

---

## 0. Executive Summary

### 现状诊断

MathModel v2 的核心问题不是 Agent 不够多，而是：

1. **Paper 被当作最终 Artifact**，而不是建模过程的"投影层"
2. **线性 Pipeline** 不支持建模过程中必然出现的回退、并行、局部重跑
3. **MODEL_SPEC.md 太粗**，无法支撑 Evidence Graph 这种关系型结构
4. **Reviewer 太晚出现**，论文写完才审，浪费大量返工成本
5. **知识库是文档库**，不是决策知识库——Agent 无法真正"选择"方法
6. **29 Agent 线性排列**，没有 DAG 依赖关系，无法支持 Per-Qi 状态

### v3 核心变更

| 维度 | v2 (当前) | v3 (目标) |
|------|-----------|-----------|
| 架构模式 | 四手线性流水线 | 认知核心 + 执行层 + 论文投影层 |
| 状态模型 | STATE.md (29步线性) | 多维 State (Problem/Model/Experiment/Evidence/Workflow) |
| 证据链 | all_results.json (线性) | Evidence Graph (关系型) |
| 工作流 | 固定29步顺序 | DAG + Feedback Loop + Per-Qi 状态 |
| 知识库 | 文档库 (Markdown) | 决策知识库 (Method Card + Pattern + Failure Memory) |
| 审查层 | 仅 Reviewer (末尾) | Validator → Critic → Reviewer (三层) |
| Agent 数 | 29 (线性) | ~18 (DAG 节点) + 可组合 Capability Skills |

---

## 1. 新架构：认知核心 + 执行层 + 论文投影层

### 1.1 架构总览

```
                         ┌─────────────────────────┐
                         │    Problem Understanding │
                         │    题目认知模型           │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │    Modeling Strategy      │
                         │    建模决策空间           │
                         └────────────┬────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                │                     │                     │
     ┌──────────▼──────────┐ ┌───────▼────────┐ ┌─────────▼────────┐
     │  Mathematical Model │ │ Computational  │ │ Evidence Model   │
     │  数学模型            │ │ Model 计算模型  │ │ 证据模型         │
     └──────────┬──────────┘ └───────┬────────┘ └─────────┬────────┘
                │                     │                     │
                └─────────────────────┼─────────────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │    Evidence Graph        │
                         │    证据图谱              │
                         └────────────┬────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │    Narrative Model       │
                         │    论文叙事模型           │
                         └────────────┬────────────┘
                                      │
                              ┌───────▼───────┐
                              │     Paper      │
                              │   论文投影     │
                              └───────┬───────┘
                                      │
                              ┌───────▼───────┐
                              │  Multi Review  │
                              │  三层审查      │
                              └───────────────┘
```

### 1.2 核心对象：Evidence Graph

这是 v3 最重要的新概念。取代 v2 的线性文件依赖。

```json
{
  "claim_id": "C17",
  "statement": "优化后方案使系统效率提高 18.7%",
  "problem": "Q2",
  "model": "M2",
  "experiment": "E23",
  "input": {
    "dataset": "dataset_v3.csv",
    "parameters": {"alpha": 0.5, "beta": 0.3}
  },
  "code": {
    "file": "q2_optimization.py",
    "function": "solve_problem_2",
    "commit_hash": "abc123"
  },
  "metric": {
    "name": "efficiency",
    "value": 0.187,
    "unit": "ratio",
    "uncertainty": 0.021,
    "baseline": {
      "model": "M0",
      "value": 0.158
    }
  },
  "evidence": {
    "figure": "fig_q2_efficiency.png",
    "table": "tab_q2_comparison",
    "sensitivity": "sens_q2_alpha.json"
  },
  "paper_location": {
    "section": "4.2",
    "paragraph": 3,
    "sentence": "具体数值见表 X"
  },
  "verification": {
    "multi_run_cv": 0.045,
    "cross_validation": true,
    "sensitivity_tested": true
  }
}
```

### 1.3 新目录结构

```
core/
├── cognition/                    # 认知层：问题理解 → 建模策略 → 证据构建
│   ├── problem/                  # 问题认知
│   │   ├── problem_understanding.py
│   │   ├── question_decomposition.py
│   │   └── constraint_extraction.py
│   ├── modeling/                 # 建模决策
│   │   ├── model_selection_arena.py
│   │   ├── assumption_registry.py
│   │   └── symbol_registry.py
│   ├── experiment/               # 实验设计
│   │   ├── experiment_planner.py
│   │   ├── baseline_designer.py
│   │   └── sensitivity_planner.py
│   ├── evidence/                 # 证据构建
│   │   ├── evidence_graph.py
│   │   ├── claim_builder.py
│   │   └── evidence_validator.py
│   └── narrative/                # 叙事模型
│       ├── research_director.py
│       ├── narrative_model.py
│       └── story_arc.py
│
├── agents/                       # 执行 Agent（DAG 节点）
│   ├── analyst/                  # 分析师
│   │   ├── problem-parser/
│   │   ├── type-classifier/
│   │   └── literature-searcher/
│   ├── modeler/                  # 建模师
│   │   ├── method-matcher/
│   │   ├── model-builder/
│   │   ├── dag-builder/
│   │   └── assumption-validator/
│   ├── experimenter/             # 实验员
│   │   ├── code-implementer/
│   │   ├── test-runner/
│   │   └── result-verifier/
│   ├── critic/                   # 批评者（前置）
│   │   ├── model-critic/
│   │   ├── experiment-critic/
│   │   └── narrative-critic/
│   └── writer/                   # 撰写者
│       ├── section-writer/
│       ├── figure-generator/
│       └── reference-curator/
│
├── workflows/                    # 工作流定义（DAG）
│   ├── competition/              # 竞赛工作流
│   │   ├── cumcm.yaml
│   │   ├── mcm.yaml
│   │   └── diangong.yaml
│   ├── modeling/                 # 建模工作流
│   │   ├── standard.yaml
│   │   ├── quick.yaml
│   │   └── championship.yaml
│   └── evidence/                 # 证据工作流
│       ├── evidence_gate.yaml
│       └── paper_projection.yaml
│
├── knowledge/                    # 知识系统（升级）
│   ├── fundamentals/             # 基础理论
│   ├── methods/                  # 方法卡片
│   │   ├── cards/                # Method Card (YAML)
│   │   ├── decision_trees/
│   │   └── combinations/
│   ├── competition/              # 竞赛知识
│   │   ├── rules/
│   │   ├── rubrics/
│   │   └── judge_insights/
│   ├── cases/                    # 案例库
│   │   ├── winning_papers/       # 蒸馏后的获奖论文结构
│   │   ├── problem_solutions/
│   │   └── innovation_patterns/
│   ├── empirical/                # 经验数据
│   ├── failures/                 # 失败记忆
│   │   ├── wrong_models/
│   │   ├── hallucinated_data/
│   │   └── reviewer_rejections/
│   └── validation/               # 验证模块
│
├── schemas/                      # 结构化输出 Schema（升级）
├── runtime/                      # 运行时配置
└── tools/                        # 工具脚本（保留+升级）
```

---

## 2. State Model: 多维状态

### 2.1 v2 状态 vs v3 状态

**v2**: 单一 `state.json` + `STATE.md`，29 步线性进度

**v3**: 多维状态，按认知对象组织

### 2.2 v3 State Schema

```json
{
  "schema_version": 3,
  "project": "cumcm2024a",
  "competition": "cumcm",
  "problem_type": "A",
  
  "state": {
    "run": {
      "status": "in_progress",
      "current_phase": "experiment",
      "current_question": "Q2",
      "started_at": "2026-09-04T10:00:00Z",
      "elapsed_hours": 12.5
    },
    
    "problem": {
      "status": "complete",
      "questions": ["Q1", "Q2", "Q3", "Q4"],
      "constraints_extracted": true,
      "ambiguities_resolved": true
    },
    
    "models": {
      "status": "complete",
      "candidates": ["M1", "M2", "M3"],
      "selected": "M2",
      "assumptions_registered": true,
      "symbols_registered": true
    },
    
    "experiments": {
      "status": "in_progress",
      "by_question": {
        "Q1": {"status": "complete", "experiments": ["E11", "E12"]},
        "Q2": {"status": "running", "experiments": ["E21"]},
        "Q3": {"status": "pending", "experiments": []},
        "Q4": {"status": "pending", "experiments": []}
      }
    },
    
    "evidence": {
      "status": "partial",
      "claims_built": 5,
      "claims_total": 12,
      "evidence_graph_version": 3
    },
    
    "narrative": {
      "status": "pending",
      "research_story_ready": false
    },
    
    "paper": {
      "status": "pending",
      "sections_written": 0,
      "sections_total": 8
    },
    
    "review": {
      "status": "pending",
      "rounds_completed": 0,
      "verdict": null
    }
  },
  
  "workflow": {
    "current_node": "experiment_q2",
    "dag_version": "v3",
    "completed_nodes": ["problem_understanding", "model_selection", "experiment_q1"],
    "blocked_nodes": [],
    "retry_counts": {"experiment_q2": 1}
  }
}
```

### 2.3 Per-Qi 状态

每个子问题独立跟踪：

```json
{
  "questions": {
    "Q1": {
      "status": "complete",
      "model": "M2-Q1",
      "experiments": ["E11", "E12"],
      "evidence": ["C1", "C2", "C3"],
      "score": 8.2,
      "last_updated": "2026-09-04T14:00:00Z"
    },
    "Q2": {
      "status": "in_progress",
      "model": "M2-Q2",
      "experiments": ["E21"],
      "evidence": ["C4", "C5"],
      "score": null,
      "retry_count": 1,
      "failure_reason": "sensitivity_analysis_failed",
      "last_updated": "2026-09-04T15:30:00Z"
    },
    "Q3": {
      "status": "pending",
      "model": null,
      "experiments": [],
      "evidence": [],
      "score": null
    },
    "Q4": {
      "status": "pending",
      "model": null,
      "experiments": [],
      "evidence": [],
      "score": null
    }
  }
}
```

---

## 3. Workflow DAG

### 3.1 v3 工作流定义

不再固定 29 步顺序，而是 DAG + 条件边 + 反馈环。

```yaml
# core/workflows/modeling/standard.yaml
schema_version: 3
name: standard_modeling
description: 标准建模工作流（含 Critic 前置 + Evidence Gate）

nodes:
  # Phase 1: Problem Understanding
  problem_understanding:
    type: reasoning
    agent: analyst/problem-parser
    inputs: [inputs/*]
    outputs: [state/problem.json, state/questions.json]
    
  problem_decomposition:
    type: reasoning
    agent: analyst/type-classifier
    inputs: [state/problem.json]
    outputs: [state/type_classification.json]
    depends_on: [problem_understanding]
    
  literature_search:
    type: knowledge
    agent: analyst/literature-searcher
    inputs: [state/problem.json, state/type_classification.json]
    outputs: [state/literature_evidence.json]
    depends_on: [problem_decomposition]
    
  # Phase 2: Modeling Strategy
  model_candidates:
    type: generation
    agent: modeler/method-matcher
    inputs: [state/type_classification.json, state/literature_evidence.json]
    outputs: [state/model_registry.json]
    depends_on: [literature_search]
    
  model_construction:
    type: reasoning
    agent: modeler/model-builder
    inputs: [state/model_registry.json]
    outputs: [state/mathematical_model.json]
    depends_on: [model_candidates]
    
  model_dag:
    type: structuring
    agent: modeler/dag-builder
    inputs: [state/mathematical_model.json]
    outputs: [state/model_dag.json]
    depends_on: [model_construction]
    
  # Phase 2.5: Critic (前置！)
  model_critic:
    type: validation
    agent: critic/model-critic
    inputs: [state/mathematical_model.json, state/model_dag.json]
    outputs: [state/model_critique.json]
    depends_on: [model_dag]
    on_fail: model_construction  # 反馈环
    
  # Phase 3: Experiment (per-Qi)
  experiment_design:
    type: planning
    agent: experimenter/experiment-planner
    inputs: [state/mathematical_model.json, state/model_dag.json]
    outputs: [state/experiment_plan.json]
    depends_on: [model_critic]
    
  experiment_q1:
    type: execution
    agent: experimenter/code-implementer
    inputs: [state/experiment_plan.json, state/mathematical_model.json]
    outputs: [artifacts/code/q1/, artifacts/results/q1/]
    depends_on: [experiment_design]
    per_question: true
    
  experiment_q2:
    type: execution
    agent: experimenter/code-implementer
    inputs: [state/experiment_plan.json, state/mathematical_model.json]
    outputs: [artifacts/code/q2/, artifacts/results/q2/]
    depends_on: [experiment_design]
    per_question: true
    
  experiment_q3:
    type: execution
    agent: experimenter/code-implementer
    inputs: [state/experiment_plan.json, state/mathematical_model.json]
    outputs: [artifacts/code/q3/, artifacts/results/q3/]
    depends_on: [experiment_design]
    per_question: true
    
  experiment_q4:
    type: execution
    agent: experimenter/code-implementer
    inputs: [state/experiment_plan.json, state/mathematical_model.json]
    outputs: [artifacts/code/q4/, artifacts/results/q4/]
    depends_on: [experiment_design]
    per_question: true
    
  # Phase 3.5: Evidence Gate
  evidence_gate:
    type: validation
    agent: critic/experiment-critic
    inputs: [artifacts/results/*, state/experiment_plan.json]
    outputs: [state/evidence_graph.json, state/evidence_gate_report.json]
    depends_on: [experiment_q1, experiment_q2, experiment_q3, experiment_q4]
    gate_type: evidence  # 没有真实证据不允许写论文
    
  # Phase 4: Narrative
  research_director:
    type: reasoning
    agent: cognition/narrative/research-director
    inputs: [state/evidence_graph.json, state/model_registry.json, knowledge/competition/rubrics/]
    outputs: [state/research_story.json]
    depends_on: [evidence_gate]
    
  # Phase 5: Paper Projection
  paper_outline:
    type: projection
    agent: writer/section-writer
    inputs: [state/research_story.json, state/evidence_graph.json]
    outputs: [artifacts/paper/outline.json]
    depends_on: [research_director]
    
  paper_sections:
    type: generation
    agent: writer/section-writer
    inputs: [artifacts/paper/outline.json, state/evidence_graph.json]
    outputs: [artifacts/paper/sections/]
    depends_on: [paper_outline]
    per_section: true
    
  paper_figures:
    type: generation
    agent: writer/figure-generator
    inputs: [state/evidence_graph.json, artifacts/paper/outline.json]
    outputs: [artifacts/paper/figures/]
    depends_on: [paper_outline]
    
  paper_references:
    type: generation
    agent: writer/reference-curator
    inputs: [artifacts/paper/sections/, knowledge/]
    outputs: [artifacts/paper/references.bib]
    depends_on: [paper_sections]
    
  paper_assembly:
    type: assembly
    agent: writer/paper-assembler
    inputs: [artifacts/paper/sections/, artifacts/paper/figures/, artifacts/paper/references.bib]
    outputs: [artifacts/paper/main.tex]
    depends_on: [paper_sections, paper_figures, paper_references]
    
  # Phase 6: Review (三层)
  consistency_check:
    type: validation
    agent: validator/consistency-checker
    inputs: [artifacts/paper/main.tex, state/evidence_graph.json]
    outputs: [state/consistency_report.json]
    depends_on: [paper_assembly]
    
  guardrails_check:
    type: validation
    agent: validator/guardrails-checker
    inputs: [artifacts/paper/main.tex, artifacts/paper/references.bib]
    outputs: [state/guardrails_report.json]
    depends_on: [paper_assembly]
    
  narrative_critic:
    type: validation
    agent: critic/narrative-critic
    inputs: [artifacts/paper/main.tex, state/evidence_graph.json, knowledge/failures/]
    outputs: [state/narrative_critique.json]
    depends_on: [consistency_check, guardrails_check]
    
  final_review:
    type: validation
    agent: writer/final-validator
    inputs: [artifacts/paper/main.tex, state/consistency_report.json, state/guardrails_report.json, state/narrative_critique.json]
    outputs: [artifacts/paper/main.pdf]
    depends_on: [narrative_critic]
    on_fail: paper_sections  # 反馈环

edges:
  - from: model_critic
    to: model_construction
    condition: on_fail
    label: "模型质量不达标 → 重新建模"
    
  - from: evidence_gate
    to: experiment_design
    condition: on_fail
    label: "证据不足 → 补充实验"
    
  - from: final_review
    to: paper_sections
    condition: on_fail
    label: "论文质量不达标 → 重写章节"

per_question_nodes:
  - experiment_q1
  - experiment_q2
  - experiment_q3
  - experiment_q4
  
parallel_groups:
  - [experiment_q1, experiment_q2, experiment_q3, experiment_q4]
  - [paper_figures, paper_references]
  - [consistency_check, guardrails_check]
```

### 3.2 DAG 执行引擎

```python
# core/workflows/engine.py (概念)

class WorkflowEngine:
    def __init__(self, workflow_yaml, state):
        self.dag = DAG(workflow_yaml)
        self.state = state
        
    def get_ready_nodes(self):
        """返回所有依赖已满足但未执行的节点"""
        ready = []
        for node in self.dag.nodes:
            if node.status == "pending":
                if all(dep.status == "complete" for dep in node.depends_on):
                    ready.append(node)
        return ready
    
    def execute_node(self, node):
        """执行单个节点"""
        agent = load_agent(node.agent)
        inputs = {k: self.state.load(v) for k, v in node.inputs}
        outputs = agent.execute(inputs)
        for path, data in outputs.items():
            self.state.save(path, data)
        node.status = "complete"
        
    def handle_failure(self, node, error):
        """处理失败：重试 or 回退"""
        if node.retry_count < MAX_RETRIES:
            node.retry_count += 1
            return "retry"
        elif node.on_fail:
            self.rollback_to(node.on_fail)
            return "rollback"
        else:
            return "block"
    
    def get_per_question_status(self, qi):
        """获取单个子问题的状态"""
        return self.state.get(f"experiments.by_question.{qi}")
```

---

## 4. Evidence Graph Schema

### 4.1 核心对象

```json
{
  "schema_version": 3,
  "evidence_graph": {
    "version": 1,
    "project": "cumcm2024a",
    
    "nodes": {
      "claims": [
        {
          "id": "C1",
          "type": "claim",
          "statement": "...",
          "question": "Q1",
          "model": "M2",
          "experiment": "E11",
          "strength": "strong",
          "evidence": ["E11", "fig_1_1", "tab_1"]
        }
      ],
      
      "experiments": [
        {
          "id": "E11",
          "type": "experiment",
          "question": "Q1",
          "model": "M2",
          "code_file": "q1_optimization.py",
          "function": "solve_problem_1",
          "inputs": {"dataset": "data_q1.csv"},
          "outputs": {"efficiency": 0.87, "cost": 12345},
          "validation": {
            "multi_run_cv": 0.03,
            "sensitivity_tested": true,
            "baseline_compared": true
          }
        }
      ],
      
      "figures": [
        {
          "id": "fig_1_1",
          "type": "figure",
          "file": "paper/figures/fig_1_1.png",
          "data_source": "E11",
          "caption": "...",
          "referenced_by": ["C1", "C2"]
        }
      ],
      
      "tables": [
        {
          "id": "tab_1",
          "type": "table",
          "file": "paper/tables/tab_1.tex",
          "data_source": "E11",
          "caption": "...",
          "referenced_by": ["C1"]
        }
      ]
    },
    
    "edges": [
      {"from": "C1", "to": "E11", "type": "supported_by"},
      {"from": "C1", "to": "fig_1_1", "type": "illustrated_by"},
      {"from": "E11", "to": "M2", "type": "uses_model"},
      {"from": "E11", "to": "data_q1.csv", "type": "uses_data"}
    ],
    
    "coverage": {
      "total_claims": 12,
      "supported_claims": 10,
      "unsupported_claims": 2,
      "coverage_ratio": 0.83
    }
  }
}
```

### 4.2 Evidence Gate

```python
class EvidenceGate:
    """证据门禁：没有真实证据不允许写最终论文"""
    
    def check(self, evidence_graph, experiment_results):
        violations = []
        
        # 1. 每个 claim 必须有 experiment 支撑
        for claim in evidence_graph.claims:
            if not claim.experiment:
                violations.append(f"Claim {claim.id} lacks experiment")
        
        # 2. 每个 experiment 必须有 real results
        for exp in evidence_graph.experiments:
            if not exp.outputs:
                violations.append(f"Experiment {exp.id} has no results")
        
        # 3. 每个 claim 必须有 figure/table evidence
        for claim in evidence_graph.claims:
            if not claim.evidence:
                violations.append(f"Claim {claim.id} has no visual evidence")
        
        # 4. Sensitivity analysis 必须覆盖关键参数
        for exp in evidence_graph.experiments:
            if not exp.validation.sensitivity_tested:
                violations.append(f"Experiment {exp.id} lacks sensitivity analysis")
        
        # 5. Baseline comparison 必须存在
        for exp in evidence_graph.experiments:
            if not exp.validation.baseline_compared:
                violations.append(f"Experiment {exp.id} lacks baseline comparison")
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "coverage": self.compute_coverage(evidence_graph)
        }
```

---

## 5. Method Card Schema

### 5.1 从 Markdown 到结构化 YAML

当前 `knowledge/methodology/*.md` 是人类可读的文档。v3 升级为机器可读的 Method Card。

```yaml
# core/knowledge/methods/cards/topsis.yaml
method_id: topsis
name: TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)
version: 1.0

category:
  - multi_criteria_decision
  - ranking

best_for:
  - ranking
  - evaluation
  - selecting_best_alternative

requires:
  - multiple_alternatives: true
  - multiple_indicators: true
  - indicator_direction_known: true

assumptions:
  - "指标方向已知（成本型/效益型）"
  - "权重已确定或可通过客观方法计算"
  - "方案间独立"

strengths:
  - "计算简单，易于解释"
  - "不需要效用函数"
  - "可以处理定量指标"

weaknesses:
  - "对归一化方法敏感"
  - "对权重敏感"
  - "无法处理定性指标（需先量化）"

competition_usage:
  common: true
  innovation_level: low
  typical_problem_types: ["C", "E"]
  typical_sub_problems: ["综合评价", "方案比选"]

good_combinations:
  - method_id: entropy_weight
    reason: "客观赋权 + 相对优劣排序"
  - method_id: ahp
    reason: "主观赋权 + 相对优劣排序"
  - method_id: grey_relational
    reason: "不确定性处理 + 排序"

bad_combinations:
  - method_id: dea
    reason: "DEA 是效率评价，与 TOPSIS 排序逻辑冲突"

validation:
  - sensitivity_weight: "权重变化 ±20% 观察排名稳定性"
  - ranking_stability: "多次运行排名变化 < 2 位"
  - comparison_with_baselines: "与加权求和法对比"

paper_evidence:
  required:
    - weight_table: "权重来源与数值"
    - ranking_table: "最终排序结果"
    - sensitivity_analysis: "权重敏感性分析"
  optional:
    - normalization_comparison: "不同归一化方法对比"
    - real_world_validation: "与实际决策对比"

code_template: core/Programmer/knowledge/code-templates/evaluation/entropy_topsis.py

references:
  - author: "Hwang, C.L. & Yoon, K."
    title: "Multiple Attribute Decision Making"
    year: 1981
    doi: "10.1007/978-3-642-48318-9"

tags: ["评价", "排序", "多准则", "经典方法", "低创新"]
```

### 5.2 Method Card Registry

```python
class MethodRegistry:
    """方法卡片注册表"""
    
    def __init__(self, cards_dir):
        self.cards = {}
        for card_file in Path(cards_dir).glob("*.yaml"):
            card = yaml.safe_load(card_file.read_text())
            self.cards[card["method_id"]] = card
    
    def search(self, problem_type, sub_problem_type=None):
        """根据题型搜索候选方法"""
        candidates = []
        for card in self.cards.values():
            score = 0
            if problem_type in card["competition_usage"].get("typical_problem_types", []):
                score += 3
            if sub_problem_type in card["best_for"]:
                score += 2
            if card["competition_usage"]["common"]:
                score += 1
            if score > 0:
                candidates.append((score, card))
        return sorted(candidates, key=lambda x: -x[0])
    
    def get_combinations(self, method_id):
        """获取方法组合建议"""
        card = self.cards[method_id]
        return card.get("good_combinations", [])
    
    def get_validation_checks(self, method_id):
        """获取验证检查项"""
        card = self.cards[method_id]
        return card.get("validation", [])
```

---

## 6. Failure Memory Schema

### 6.1 从 pitfalls/ 到 structured failure-memory/

```yaml
# core/knowledge/failures/wrong_models/F001.yaml
failure_id: F001
category: wrong_model
problem_type: optimization
severity: major

mistake: "GA 声称全局最优"
why_failed: "启发式算法没有全局最优性证明"
symptoms:
  - "没有 baseline 对比"
  - "单次随机种子"
  - "没有收敛性分析"

reviewer_attack: "The authors claim optimality without evidence that this is a global optimum."

fix:
  - "与 MILP 对比"
  - "多次运行报告方差"
  - "弱化措辞为 'near-optimal'"

related_antipatterns: ["AP-03", "AP-15"]
related_papers: ["A028", "B015"]
```

### 6.2 Failure Memory 查询

```python
class FailureMemory:
    """失败记忆库"""
    
    def __init__(self, failures_dir):
        self.failures = []
        for f in Path(failures_dir).rglob("*.yaml"):
            self.failures.append(yaml.safe_load(f.read_text()))
    
    def query(self, problem_type=None, category=None, symptom=None):
        """查询相关失败案例"""
        results = []
        for f in self.failures:
            score = 0
            if problem_type and problem_type in f.get("problem_type", ""):
                score += 2
            if category and category == f.get("category"):
                score += 3
            if symptom and symptom in f.get("symptoms", []):
                score += 1
            if score > 0:
                results.append((score, f))
        return sorted(results, key=lambda x: -x[0])
    
    def get_reviewer_attacks(self, model_type):
        """获取评审可能的攻击点"""
        attacks = []
        for f in self.failures:
            if model_type in f.get("related_antipatterns", []):
                attacks.append(f["reviewer_attack"])
        return attacks
```

---

## 7. Agent Mapping: v2 29 Agent → v3 Roles

### 7.1 映射表

| v2 Agent | v3 Role | 变化 | 说明 |
|----------|---------|------|------|
| problem-parser | analyst/problem-parser | 保留 | 基本不变 |
| type-classifier | analyst/type-classifier | 保留 | 增加 family mapping |
| literature-searcher | analyst/literature-searcher | 保留 | 增加 Method Card 关联 |
| method-matcher | modeler/method-matcher | 升级 | 改为从 Method Card Registry 选择 |
| model-builder | modeler/model-builder | 保留 | 增加 Critic 前置 |
| dag-builder | modeler/dag-builder | 保留 | 基本不变 |
| assumption-validator | modeler/assumption-validator | 保留 | 基本不变 |
| spec-auditor | validator/spec-auditor | 合并 | 合并到 Validator 层 |
| template-selector | experimenter/template-selector | 保留 | 基本不变 |
| code-implementer | experimenter/code-implementer | 升级 | 改为 per-Qi 执行 |
| test-runner | experimenter/test-runner | 保留 | 基本不变 |
| result-verifier | experimenter/result-verifier | 升级 | 增加 Evidence Graph 构建 |
| guardrails-checker (P) | validator/guardrails-checker | 合并 | 两处 guardrails 合并 |
| hash-auditor | validator/hash-auditor | 合并 | 合并到 Validator 层 |
| structure-planner | writer/structure-planner | 升级 | 改为从 Research Story 生成大纲 |
| section-writer | writer/section-writer | 升级 | 改为从 Evidence Graph 投影 |
| figure-generator | writer/figure-generator | 保留 | 基本不变 |
| reference-curator | writer/reference-curator | 保留 | 基本不变 |
| consistency-checker | validator/consistency-checker | 合并 | 合并到 Validator 层 |
| guardrails-checker (W) | validator/guardrails-checker | 合并 | 两处 guardrails 合并 |
| final-validator | writer/final-validator | 保留 | 基本不变 |
| scorer-academic | **新增: critic/model-critic** | 新增 | 前置到建模阶段 |
| scorer-engineering | **删除** | 删除 | 合并到 result-verifier |
| scorer-judge | **新增: critic/judge-critic** | 新增 | 可在多个阶段调用 |
| scorer-reader | **删除** | 删除 | 合并到 narrative-critic |
| scorer-adversarial | **新增: critic/adversarial-critic** | 新增 | 前置到 Evidence Gate |
| weakness-hunter | **新增: critic/weakness-hunter** | 保留 | 提前到 Evidence Gate |
| revision-planner | **删除** | 删除 | 由 DAG 自动处理回退 |
| revision-executor | **删除** | 删除 | 由 DAG 自动处理回退 |

### 7.2 新 Agent 清单

```
v3 Agent Count: ~18 (vs v2's 29)

analyst/ (3)
  ├── problem-parser
  ├── type-classifier
  └── literature-searcher

modeler/ (4)
  ├── method-matcher
  ├── model-builder
  ├── dag-builder
  └── assumption-validator

experimenter/ (4)
  ├── template-selector
  ├── code-implementer
  ├── test-runner
  └── result-verifier

critic/ (4)
  ├── model-critic          (NEW: 前置到建模阶段)
  ├── experiment-critic     (NEW: Evidence Gate)
  ├── narrative-critic      (NEW: 论文叙事审查)
  └── weakness-hunter       (从 Reviewer 提前)

writer/ (5)
  ├── structure-planner
  ├── section-writer
  ├── figure-generator
  ├── reference-curator
  └── final-validator

validator/ (4)
  ├── spec-auditor
  ├── consistency-checker
  ├── guardrails-checker    (合并 P+W 两处)
  └── hash-auditor
```

### 7.3 关键变化说明

**删除 11 个 Agent，新增 4 个，总计从 29 降到 ~18**

删除原因：
- 5 个 scorer-* → 合并为 critic/ 层（不再每人一个 Agent）
- 2 个 guardrails-checker → 合并为 1 个
- 1 个 hash-auditor → 合并到 validator/
- 1 个 revision-planner → DAG 自动处理
- 1 个 revision-executor → DAG 自动处理
- 1 个 scorer-engineering → 合并到 result-verifier

新增原因：
- model-critic: 前置审查，避免垃圾模型进入实验
- experiment-critic: Evidence Gate 守门
- narrative-critic: 论文叙事质量审查
- judge-critic: 竞赛评分视角（可选）

---

## 8. 知识系统升级

### 8.1 新知识目录

```
core/knowledge/
├── fundamentals/                # 基础理论（从 methodology/ 迁移+扩充）
│   ├── modeling-theory/
│   ├── statistics/
│   ├── optimization/
│   ├── machine-learning/
│   └── simulation/
│
├── methods/                     # 方法卡片（从 methodology/ 升级）
│   ├── cards/                   # YAML Method Cards
│   ├── decision_trees/          # 决策树（保留+扩充）
│   ├── combinations/            # 方法组合推荐
│   └── anti_patterns/           # 方法反模式
│
├── competition/                 # 竞赛知识（从 problems/ + review/ 升级）
│   ├── rules/                   # 竞赛规则（按年份+竞赛类型）
│   ├── rubrics/                 # 评分细则（结构化）
│   ├── judge_insights/          # 评委洞察（扩充）
│   └── competition_profiles/    # 竞赛画像
│
├── cases/                       # 案例库（从 paper-cases/ 升级）
│   ├── winning_papers/          # 蒸馏后的获奖论文结构
│   ├── problem_solutions/       # 问题解决方案
│   └── innovation_patterns/     # 创新模式
│
├── empirical/                   # 经验数据（从 paper-cases/ 提取）
│   ├── statistics.json          # 经验统计
│   ├── paper_distributions.json # 论文分布
│   └── model_distributions.json # 方法分布
│
├── failures/                    # 失败记忆（从 pitfalls/ 升级）
│   ├── wrong_models/            # 错误模型选择
│   ├── hallucinated_data/       # 数据伪造
│   ├── invalid_results/         # 无效结果
│   └── reviewer_rejections/     # 评审拒绝案例
│
└── validation/                  # 验证模块（保留）
```

### 8.2 Innovation Patterns

```yaml
# core/knowledge/cases/innovation_patterns/P001.yaml
pattern_id: P001
name: hybrid_model
description: "混合模型：结合两种以上方法"
example_problems: ["A028", "B015", "C038"]
typical_combinations:
  - ["optimization", "simulation"]
  - ["statistics", "mechanism"]
  - ["ML", "traditional"]
innovation_level: medium
competition_advantage: "展示方法广度"
writing_tip: "强调互补性而非堆砌"
```

---

## 9. Config 拆分

### 9.1 从单一 config.yaml 到分层配置

```yaml
# core/runtime/rules/cumcm.yaml
competition: cumcm
rules:
  max_pages: 25
  min_words: 18000
  min_figures: 6
  min_tables: 4
  min_equations: 15
  min_references: 10
  anonymous: true
  ai_disclosure: true
  format: xelatex
  language: zh

# core/runtime/heuristics/modeling.yaml
modeling:
  min_candidate_models: 2
  assumption_score_threshold: 6.0
  sensitivity_range: 0.20
  sensitivity_steps: 10
  multi_run_count: 5
  cv_threshold: 0.10

# core/runtime/heuristics/writing.yaml
writing:
  abstract_min_words: 400
  abstract_max_words: 600
  paragraph_min_sentences: 3
  figure_analysis_required: true
  claim_calibration: true

# core/runtime/defaults/runtime.yaml
runtime:
  language: zh
  template: auto
  strict_mode: true
  traceability_min_ratio: 0.90
  numeric_tolerance_rel: 0.005
  numeric_tolerance_abs: 0.01
  random_seed: 42
```

---

## 10. 迁移策略

### 10.1 渐进迁移原则

**不破坏现有功能，不一次性重写。**

每个 P 阶段都是独立可运行的版本。

### 10.2 P0 — 架构基础 (Week 1-2)

**目标**: 引入 State Model + Evidence Graph + Workflow DAG

| Commit | 内容 | 影响范围 |
|--------|------|----------|
| P0-1 | `core/schemas/evidence_graph.schema.json` | 新增文件 |
| P0-2 | `core/schemas/workflow_dag.schema.json` | 新增文件 |
| P0-3 | `core/schemas/research_story.schema.json` | 新增文件 |
| P0-4 | `core/schemas/model_registry.schema.json` | 新增文件 |
| P0-5 | `core/schemas/experiment_plan.schema.json` | 新增文件 |
| P0-6 | `core/workflows/engine.py` — DAG 执行引擎 | 新增文件 |
| P0-7 | `core/cognition/evidence/evidence_graph.py` | 新增文件 |
| P0-8 | `core/cognition/evidence/claim_builder.py` | 新增文件 |
| P0-9 | `core/cognition/narrative/research_director.py` | 新增文件 |
| P0-10 | `core/workflows/modeling/standard.yaml` — 标准工作流 | 新增文件 |
| P0-11 | 更新 `state.py` 支持 v3 多维状态 | 修改 core/tools/state.py |
| P0-12 | 更新 `gate.py` 支持 Evidence Gate | 修改 core/tools/gate.py |

**验证**: 新旧状态可以共存，`state.py init` 自动检测 v2/v3

### 10.3 P1 — 知识系统 (Week 3-4)

**目标**: Method Card + Failure Memory + Innovation Patterns

| Commit | 内容 | 影响范围 |
|--------|------|----------|
| P1-1 | `core/knowledge/methods/cards/` — 20 个核心 Method Cards | 新增文件 |
| P1-2 | `core/knowledge/methods/registry.py` — Method Card 注册表 | 新增文件 |
| P1-3 | `core/knowledge/failures/` — 20 个 Failure Memory | 新增文件 |
| P1-4 | `core/knowledge/failures/memory.py` — Failure Memory 查询 | 新增文件 |
| P1-5 | `core/knowledge/cases/innovation_patterns/` — 10 个创新模式 | 新增文件 |
| P1-6 | `core/runtime/rules/cumcm.yaml` — CUMCM 规则 | 新增文件 |
| P1-7 | `core/runtime/rules/mcm.yaml` — MCM 规则 | 新增文件 |
| P1-8 | `core/runtime/heuristics/` — 启发式配置 | 新增文件 |
| P1-9 | 更新 `loader.py` 支持新配置路径 | 修改 core/env/loader.py |

### 10.4 P2 — 建模质量 (Week 5-6)

**目标**: Model Selection Arena + Experiment Planner + Critic 前置

| Commit | 内容 | 影响范围 |
|--------|------|----------|
| P2-1 | `core/cognition/modeling/model_selection_arena.py` | 新增文件 |
| P2-2 | `core/cognition/experiment/experiment_planner.py` | 新增文件 |
| P2-3 | `core/cognition/experiment/baseline_designer.py` | 新增文件 |
| P2-4 | `core/agents/critic/model-critic/SKILL.md` | 新增文件 |
| P2-5 | `core/agents/critic/experiment-critic/SKILL.md` | 新增文件 |
| P2-6 | 更新 `method-matcher` 使用 Method Card Registry | 修改 agent SKILL |
| P2-7 | 更新 `code-implementer` 支持 per-Qi 执行 | 修改 agent SKILL |
| P2-8 | 更新 `result-verifier` 构建 Evidence Graph | 修改 agent SKILL |

### 10.5 P3 — 论文质量 (Week 7-8)

**目标**: Research Director + Narrative Model + Paper Projection

| Commit | 内容 | 影响范围 |
|--------|------|----------|
| P3-1 | `core/agents/critic/narrative-critic/SKILL.md` | 新增文件 |
| P3-2 | 更新 `section-writer` 从 Evidence Graph 投影 | 修改 agent SKILL |
| P3-3 | 更新 `structure-planner` 从 Research Story 生成 | 修改 agent SKILL |
| P3-4 | 更新 `consistency-checker` 使用 Evidence Graph | 修改 agent SKILL |
| P3-5 | 更新 `final-validator` 支持新状态 | 修改 agent SKILL |
| P3-6 | 更新 `orchestrator.py` 使用 DAG 引擎 | 修改 core/tools/orchestrator.py |
| P3-7 | 更新 `score_compute.py` 使用新评分模型 | 修改 core/tools/score_compute.py |
| P3-8 | 更新 `validate.py` 支持新 schema | 修改 core/tools/validate.py |

### 10.6 P4 — 清理 (Week 9)

**目标**: 移除旧代码，更新文档

| Commit | 内容 | 影响范围 |
|--------|------|----------|
| P4-1 | 移除 v2 29 Agent SKILL.md 中被替换的 | 删除文件 |
| P4-2 | 更新 AGENTS.md 为 v3 架构 | 修改文档 |
| P4-3 | 更新 README.md 为 v3 架构 | 修改文档 |
| P4-4 | 更新 ARCHITECTURE.md 为 v3 架构 | 修改文档 |
| P4-5 | 更新 catalog.yaml 为新 Agent 清单 | 修改文件 |
| P4-6 | 更新所有测试 | 修改 tests/ |

---

## 11. 验证计划

### 11.1 每个 P 阶段的验证

```bash
# P0 验证
python core/tools/validate.py                    # 全链路校验
python core/tools/state.py cumcm2024anew init    # 状态初始化
python core/workflows/engine.py --dry-run        # DAG 引擎干跑

# P1 验证
python -c "from core.knowledge.methods.registry import MethodRegistry; r = MethodRegistry('core/knowledge/methods/cards'); print(r.search('C'))"
python -c "from core.knowledge.failures.memory import FailureMemory; m = FailureMemory('core/knowledge/failures'); print(m.query(problem_type='optimization'))"

# P2 验证
python core/tools/orchestrator.py cumcm2024anew --dry-run  # 编排器干跑

# P3 验证
python -m pytest tests/ --tb=short               # 全量测试
```

### 11.2 最终验证

```bash
# 完整端到端测试（使用 cumcm2024anew 项目）
python core/tools/orchestrator.py cumcm2024anew --max-rounds 4
python core/tools/validate.py
python core/tools/score_compute.py cumcm2024anew
python core/tools/validate_project.py cumcm2024anew
```

---

## 12. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| DAG 引擎过于复杂 | 高 | 从最简 DAG 开始，逐步增加条件边 |
| Evidence Graph 构建成本高 | 中 | 先手动标注 3 个案例，验证可行性 |
| Method Card 覆盖不足 | 中 | 先覆盖 20 个高频方法，后续扩充 |
| 新旧状态不兼容 | 高 | state.py 自动检测 v2/v3，双模式运行 |
| Agent 数减少导致质量下降 | 中 | Critic 前置补偿，不是删除而是重组 |

---

## 13. 参考来源

| 来源 | 吸收内容 |
|------|----------|
| `LinHoMo/MathModel` (v2) | Contract、Validator、工程化分层、可追溯 |
| `jihe520/MathModelAgent` | Skill 化、模块化 Workflow、多模型、HIL |
| `yushui2022/MathModel-Skill` | Workflow Guard、断点恢复、Evidence Gate、JSON Contract |
| `handsomeZR-netizen/mathmodel-skill` | Per-Qi 状态、部分重跑、Competition Pack、Dim Weights |
| `zhanwen/MathModel` | 竞赛知识资产：历年题、优秀论文、算法、模板 |
