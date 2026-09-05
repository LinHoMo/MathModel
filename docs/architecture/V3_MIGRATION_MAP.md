# V3 Migration Map — V2 → V3.1 迁移映射

> 生成日期：2026-09-04
> 依据：`V3_BASELINE_AUDIT.md`（事实）+ `V3.1_ARCHITECTURE.md`（目标）
> 规则：每个迁移项标注 [保留] / [迁移] / [转换] / [降级] / [删除(legacy)] / [新增]；阶段列给出落地时机。

---

## 1. Directory Migration（路径）

| Old Path | New Path | 动作 | 阶段 |
|---|---|---|---|
| `core/Modeler|Programmer|Writer|Reviewer/agents/*/SKILL.md` | `core/agents/<role>/<name>/SKILL.md`（重组后子集） | 迁移（被吸收的 agent） | P3-P4 |
| `core/<Hand>/agents/`（未被吸收部分） | `core/legacy/hands/`（原位保留亦可） | 保留为 legacy | P5 评估 |
| `core/validators/modules/`（42 个 .py） | `core/validators/`（结构化收编）+ 原 core/validators/modules 保留软链/转发 | 迁移 | P1 |
| `core/schemas/*.json`（13 个 V2 schema） | 原位保留（V2 兼容） | 保留 | — |
| —（新增） | `core/schemas/v3/artifact|question|claim|decision|workflow|evidence|method_card|failure|pattern/*.schema.json` | 新增 | P0-P2 |
| —（新增） | `core/runtime/{artifacts,state,graph,execution,decisions,knowledge,legacy,adapters}/` | 新增 | P0-P1 |
| —（新增） | `core/workflows/{base.yaml, stages/*.yaml, competition/*.yaml}` | 新增 | P1 |
| —（新增） | `core/roles/*.yaml`（5 个 Role） | 新增 | P3 |
| —（新增） | `core/skills/critics/{model,experiment,narrative,judge}-critic/` | 新增 | P3-P4 |
| —（新增） | `core/validators/evidence/evidence_gate.py` | 新增 | P3 |
| `core/tools/score_compute|aggregate_scores|score_artifact|weight_profiles.py` | `core/evaluation/scoring/`（原位或转发） | 迁移 | P4 |
| `core/tools/benchmark.py / bench_mmbench.py` | `core/evaluation/benchmark/` | 迁移 | P5 |
| `core/tools/gen_runtime_manifest.py / cloud_sandbox.py / test_runtime_compat.py` | `core/runtime/adapters/` | 迁移 | P5 |
| `references/harness_compat.md` | `docs/integration/harness-compat.md` | 迁移 | P5 |
| `REFACTOR_PLAN.md` | `docs/decisions/2026-09-04-refactor-plan-v2.md` | 迁移（归档决策记录） | P5 |
| `problem_cumcm2024A.txt` | `examples/problems/cumcm2024A.txt` | 迁移 | P5 |
| `_v.txt` / `texput.log` / `archify-skill/` | — | 删除（垃圾/空目录） | P5 |
| `projects/testproj/` | `tests/fixtures/projects/testproj/` | 迁移（fixture 化） | P5 |
| `archives/`（4 个幽灵脚手架文件） | `tests/fixtures/scaffolds/`（确认无历史价值）或删除 | 迁移 | P5 |

## 2. Agent Migration（29 → Role/Node/Capability/Validator）

### 2.1 保留为 DAG 节点（agent 定义重组到 core/agents/）

| V2 Agent (hand) | V3 Role | V3 DAG 节点 | 变化 |
|---|---|---|---|
| problem-parser (M) | analyst | problem_analysis | 节点产出 Q artifacts（注册 Registry） |
| type-classifier (M) | analyst | problem_analysis（合并） | 并入 problem_analysis，capability: type-classification |
| literature-searcher (M) | analyst | literature_search | 产出 literature evidence + Method Card 关联 |
| method-matcher (M) | modeler | model_selection | 改为消费 KnowledgeRetriever + Decision Log |
| model-builder (M) | modeler | model_construction | 产出 M artifacts + assumes/solved_by 边 |
| dag-builder (M) | modeler | model_construction（合并） | model_dag 作为 model artifact 的 payload |
| assumption-validator (M) | modeler | assumption_check（critic 前哨） | 产出 A artifacts + validation 记录 |
| spec-auditor (M) | — | validator：structural | 降级为 P0 validator（MODEL_SPEC 护栏检查保留为脚本） |
| template-selector (P) | experimenter | experiment_design（合并） | capability: template-selection |
| code-implementer (P) | experimenter | experiment_Qi（per_question 展开） | per-Qi 执行，产出 CODE/E artifacts |
| test-runner (P) | experimenter | experiment_Qi（内含） | capability: testing |
| result-verifier (P) | experimenter | evidence_build | 升级：产出 R/F/T artifacts + graph 边 |
| guardrails-checker (P) | — | validator：security | 降级为 validator（与 Writer 版合并） |
| hash-auditor (P) | — | validator：integrity | 降级为 validator（hash_chain.py 已存在） |
| structure-planner (W) | writer | paper_projection（outline 阶段） | 从 Research Narrative + Graph 投影大纲 |
| section-writer (W) | writer | paper_sections | per_section，claim appears_in 回写 graph |
| figure-generator (W) | writer | paper_figures | F artifacts 关联 |
| reference-curator (W) | writer | paper_references | citation validator 配合 |
| consistency-checker (W) | — | validator：evidence/consistency | 降级为 validator（数值一致性查 graph 而非 all_results.json） |
| guardrails-checker (W) | — | validator：security（与 P 版合并） | 降级合并 |
| final-validator (W) | — | validator：paper/delivery | 降级为交付门禁 |

### 2.2 删除/转换（不保留为 agent）

| V2 Agent | 去向 | 理由 |
|---|---|---|
| scorer-academic | evaluation/scoring（脚本）+ judge-critic 输入 | Skill+Rubric，非 agent |
| scorer-engineering | 同上 | 同上 |
| scorer-judge | **critic：judge-critic**（PASS/WEAK/FAIL/UNKNOWN） | 升级为 critic，输出判定而非分数 |
| scorer-reader | critic：narrative-critic 输入 | 合并 |
| scorer-adversarial | critic：experiment-critic / weakness 检查 | 前置 |
| weakness-hunter | critic 各节点共享 capability: weakness-hunting | 前置 |
| revision-planner | **Workflow DAG 反馈环**（引擎职责） | 回退逻辑代码化 |
| revision-executor | **Workflow DAG 重跑**（引擎职责） | 同上 |

### 2.3 新增

| 新增 | 类型 | 阶段 |
|---|---|---|
| model-critic | critic 节点（model_construction 后，on_fail 反馈环） | P3 |
| experiment-critic | critic 节点（evidence_build 后，Evidence Gate 守门） | P3 |
| narrative-critic | critic 节点（paper_sections 后） | P4 |
| judge-critic | critic 节点（paper_review，终审） | P4 |
| research-director | reasoning 节点（evidence_gate 后，产出 N artifacts） | P4 |

**数量账**：29 agent → 5 Role × ~19 个常驻 DAG 节点 + 7 个 validator（非 agent）+ 2 个引擎内建机制（回退/重跑）。scorer 5→0（转 evaluation 脚本），guardrails 2→1（validator），hash-auditor/revision-* 3→0（validator/引擎）。

## 3. Schema Migration（13 → 13 + v3 子树）

| V2 Schema | 去向 |
|---|---|
| question_spec | 保留（legacy）+ v3/question/question.schema.json（新增 Q artifact contract 扩展） |
| model_spec | 保留（legacy 契约文件）+ v3/model/model.schema.json |
| code_deliverables | 保留 legacy；数值真源迁移到 Registry R artifacts |
| checkpoint | 保留 legacy（P5 评估删除） |
| literature_evidence | 保留 + v3/evidence/literature.schema.json |
| model_dag | 保留（model payload 格式） |
| decision_log | **升级**：新增 reversible/invalidated_by/consequences/criteria/evidence_ids → v3/decision/decision.schema.json |
| reproducibility | 保留 → validators/integrity 消费 |
| score_card ×1 + bench_rubric + bench_result | 保留 → evaluation 消费 |
| citation | 保留 → validators/paper 消费 |
| paper_spec | 保留 legacy；V3 中 paper 是 deliverable artifact |
| —（新增） | v3/artifact/artifact.schema.json（统一 Contract）+ v3/artifact/registry.schema.json + lifecycle 定义 + v3/evidence/graph.schema.json + v3/workflow/dag.schema.json + v3/knowledge/{method_card,failure,pattern}.schema.json |

## 4. Tool Migration

| V2 Tool | V3 去向 | 动作 |
|---|---|---|
| state.py | runtime/state/（多维状态）+ legacy 29-step 接口保留 | 转换（P1） |
| gate.py / gatelib.py | validators/（断言库收编），gate CLI 保留入口 | 迁移（P1-P3） |
| validate.py / validate_project.py | validators/structural + competition | 迁移（P5） |
| writing_check.py / citation_check.py / text_cleanup.py | validators/paper | 迁移（P5） |
| orchestrator.py | runtime/execution/engine.py（DAG）；orchestrator CLI 转发引擎，legacy 模式保留 | 转换（P1 桥接，P4 切换） |
| new_project.py | 生成 V3 workspace（state/ + artifacts/ + input/...），保留 legacy 布局开关 | 转换（P1） |
| score_*.py ×4 + weight_profiles.py | evaluation/scoring | 迁移（P4） |
| benchmark.py / bench_mmbench.py | evaluation/benchmark | 迁移（P5） |
| metrics.py / retrospect.py / reflection_bank.py / distill_empirical.py | evaluation + knowledge 运营 | 迁移（P5） |
| freeze_numbers.py | validators/evidence（数值冻结→registry 版本钉扎） | 转换（P3） |
| render_ai_usage.py / repro_checklist.py | validators/competition | 迁移（P5） |
| doctor.py / env_doctor.py / check_matlab_env.py | tools/（保留） | 保留 |
| scholar_fetch.py / diagram_gen.py / tex_to_docx.py / docx_post_processor.py | tools/（保留） | 保留 |
| cloud_sandbox.py / gen_runtime_manifest.py / test_runtime_compat.py | runtime/adapters | 迁移（P5） |

## 5. State Migration

| V2 | V3 |
|---|---|
| `work/state.json` completed[]（29 步三元组） | legacy 保留；runtime/legacy/convert.py 映射到 status.json 多维状态 |
| `current`（由 completed 推导） | workflow.current_nodes（ready 集合，多节点并行） |
| `q_states`（雏形） | questions 维度（一等实体，Per-Qi 执行单元） |
| `ai_usage_ledger` | 保留，迁移至 state/ai_usage.json（合规台账） |
| `work/STATE.md` 镜像 | 保留（渲染自 status.json + registry 摘要） |
| 29-step PIPELINE 硬编码 | workflows/*.yaml DAG + 引擎（PIPELINE 保留于 legacy） |

## 6. all_results.json → Registry + Evidence Graph

- **读方向**（P1 legacy 适配）：`runtime/legacy/convert.py import_results()` 把 all_results.json 每个顶层键转成 R artifact + produces 边，figures/tables 关联 visualized_by 边；writing_check / consistency validator 改为可选消费 graph（`--source graph|legacy`）。
- **写方向**（P1）：`export_results()` 从 graph 导出 all_results.json 兼容文件，V2 工具链零改动可继续消费，直到 P5。
- **终态**（P5 后）：数值一致性以 graph 为真源；all_results.json 停止生成（保留导出器一个版本周期）。

## 7. Workflow Step → DAG Node

| V2 顺序步 | V3 节点 | per_question | 反馈环 |
|---|---|---|---|
| M1-M8（problem→spec） | problem_analysis → literature_search → model_selection → model_construction → **model_critique** → assumption_check | 否 | model_critique.on_fail→model_construction |
| P1-P6（template→hash） | experiment_design → **experiment_Qi** → evidence_build → **evidence_gate** | Qi 展开 | evidence_gate.on_fail→experiment_design |
| W1-W7（structure→final） | research_direction → paper_projection(outline→sections∥figures∥references→assembly) → **paper_review** | sections 展开 | paper_review.on_fail→paper_sections |
| R1-R8（scorers→revision） | 删除：judge-critic 前置至 paper_review；回退由引擎承担；scoring 转脚本 | — | — |

## 8. Knowledge Migration

| V2 | V3 |
|---|---|
| methodology/ 54 md | 保留（human-readable）；METHOD-DECISION-TREE.json → methods/ 种子 |
| — | methods/cards/*.yaml（P2 首批 12-16 张高频卡：topsis/entropy/ahp/ga/sa/tsne...） |
| _negative/ 8 + pitfalls/ 3 | failures/*.yaml（P2 首批 ~10 条结构化失败记忆） |
| — | patterns/*.yaml（P2 首批 ~6 个创新模式） |
| problems/ + review/ + playbooks/ | competition/（保留 + profile 化） |
| paper-cases/ 117 | cases/（保留） |
| bench/ 22 | evaluation/benchmark/fixtures |
| empirical/ | empirical/（保留，retriever 消费） |
| data-sources/ | sources/（保留） |

## 9. Test Migration

| V2 测试 | 处置 |
|---|---|
| test_openai_manifest（==29） | P4 更新断言为 catalog v5 双视图（nodes/roles），29 断言改为 legacy 子集断言 —— **intentional change** |
| test_evals_and_runtime（29 evals 文件） | 同上 |
| test_state / test_gate_* | 保留（legacy 路径）+ 新增 v3 对应测试 |
| 其余 unit | 保留 |
| integration test_references / test_structure | P5 更新路径引用 |
| —（新增） | tests/unit/test_artifacts / test_lifecycle / test_registry / test_state_v3 / test_evidence_graph / test_invalidation / test_dag_engine / test_workflow_compose / test_legacy_convert / test_method_cards / test_failure_memory / test_decision_log / test_evidence_gate；tests/integration/test_v2_v3_bridge；tests/regression/test_v2_capability_regression；tests/e2e/test_v3_pipeline |

## 10. 每阶段验收命令（独立可运行）

```bash
# P0: python -m pytest tests/unit/test_artifacts.py tests/unit/test_registry.py tests/unit/test_lifecycle.py
# P1: + test_state_v3 / test_evidence_graph / test_invalidation / test_dag_engine / test_workflow_compose / test_legacy_convert
#     python core/tools/state.py <p> status  # V2 仍工作
# P2: + test_method_cards / test_failure_memory / test_decision_log
# P3: + test_evidence_gate; python core/tools/orchestrator.py <p> --dry-run（DAG 干跑）
# P4: + judge/narrative critic 单测; catalog v5 --check 通过
# P5: python -m pytest tests -q 全绿; validate.py; 最终审计脚本 docs/architecture/V3_FINAL_AUDIT.md
```
