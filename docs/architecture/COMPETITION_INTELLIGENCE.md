# Competition Intelligence — P8 设计与实施报告

> P8 目标：把 Knowledge Layer 从"可检索的知识文件集合"升级为**参与研究决策的
> Competition Intelligence Layer**。成功标准不是知识库变大，而是——
> **知识开始改变研究决策**。

## 1. 架构位置

```text
Problem → ProblemProfile
              ↓
   CompetitionIntelligence（core/runtime/knowledge/intelligence.py，纯确定性 API）
   ├── recommend_methods()      方法推荐（9 维可拆分评分 + 解释）
   ├── generate_candidates()    候选方案（baseline/improved/hybrid/innovation）
   ├── find_failure_risks()     失败风险（Failure Memory → risk penalty → 强制验证）
   ├── find_innovation_patterns() 创新模式 → InnovationCandidate（hypothesis 态）
   ├── build_experiment_plan()  候选 → 结构化实验计划（purpose/hypothesis/decision_rule）
   ├── explain_decision()       Decision Trace（决策 ↔ 知识版本 ↔ 失败 ↔ 验证）
   └── get_competition_pack() / conflict_report()
              ↓
   Model Arena → Experiment Planner → Workflow DAG → Artifacts → Evidence Graph
              → Validators → Research State → Paper Projection
```

硬约束回执：不新增 Agent；不新增顶层目录（pack 落 `core/knowledge/competition/`）；
不改 P7 生命周期契约；不做论文语言优化；知识文件数量不变（16 卡/10 失败/6 模式），
只升级结构。

## 2. 核心机制

### 2.1 维度化推荐（P8-3）

`RecommendationScore`：fit / data / interpretability / robustness / complexity /
innovation / competition / evidence_cost / risk_penalty 九维，`score == sum(维度)`
恒等（测试锚定）。legacy 标签分并入 fit。每条推荐带 `reasoning()`：
命中/缺失/违反/必做实验，一条字符串说清"为什么推荐、为什么靠后"。

### 2.2 Capability Matching（P8-2 阶段语义）

Method Card 的 `applicability{positive, negative, required_conditions}` 由
可判定条件键白名单（`_KNOWN_CONDITIONS`：temporal_dependency / small_sample_friendly /
high_dimensional_features / interpretability_required / large_sample …）映射到
ProblemProfile 特征——正条件命中加分、负条件命中降权、硬前提不满足记 violation。

### 2.3 Failure Memory 决策闭环（P8-5）

```text
FailureMemory(severity) → risk_penalty(high=-6/medium=-3/low=-1) → 排序变化
                        ↘ severity=high → required_experiments 注入
                          failure-guard[fm-id]:recovery 动作（P8-6 Recovery Pattern）
```
失败记忆改变推荐与实验需求，而不是被删除（Knowledge 本身不因实验否定而 invalid——
被否定的是 Decision / Candidate / Artifact，P8-14）。

### 2.4 Candidate Arena（P8-4）

每问题生成四类候选：baseline（top1 方法基线）/ improved（+兼容方法与推荐增强）/
hybrid（top1×top2 消融对照）/ innovation（主方法 × 创新模式）。排序确定性：
score 降序 + candidate_id 升序（CI-10）。Competition Pack 只读修饰：
recommended +5 / high_risk −8 并注入结构化风险（CI-08：不改状态）。

### 2.5 Innovation → Evidence（P8-6）

`InnovationCandidate` 由 Pattern 生成，携带 expected_benefit / novelty_level /
implementation_cost / competition_fit / **required_evidence + validation_protocol**。
`status="hypothesis"`——没有实验证据之前不得进入 Research State（CI-03）。
`to_experiment_requirements()` 把创新反向翻译成实验条目。

### 2.6 实验计划（P8-7/P8-9）

`ExperimentEntry`：experiment_id / purpose（为什么做）/ hypothesis / baseline /
metrics / decision_rule（**ACCEPT / REJECT / REFINE 四态**，拒绝"看起来不错"）/
priority / cost / expected_information_gain（P8-14 时间预算基础）。生成通道：
① 基线对照（永远第一条）② 卡片 evidence_requirements.minimum ③ high 级失败防线
④ recommended ⑤ 组合消融 ⑥ 创新验证。

### 2.7 Decision Trace（P8-8/P8-13）

Decision 绑定 `knowledge_refs:[{id, version}]` + failure_refs +
required_validation + score_breakdown。`explain_decision()` 输出完整链路并显式
标注 `reproducible`：知识升级后历史决策记录不变、当前版本不同则标志翻 False
（不静默，CI-07）。

### 2.8 冲突检测（P8-12）

`detect_knowledge_conflicts()` 三条显式规则：
C1 单侧 incompatible × 单侧 compatible（high）/ C2 推荐方法 × high 级失败记忆
（medium）/ C3 pattern 引用缺失卡（medium）。能发现、能记录、resolution_status
显式 open——不自动解决，阻止 silent contradiction。

## 3. 最终审计十问（任务书 §三十一）

1. **CI 是否真的改变 Model Selection？** 是——A1/A2 测试：同一评价题改小样本，
   排序变化且变化由 `small_sample_friendly` 命中/violation 解释。
2. **Failure Memory 是否真的改变决策？** 是——risk_penalty 改变排序；high 级
   失败注入 failure-guard 实验条目（测试断言）。
3. **Competition Pack 是否真的改变决策？** 是——cumcm pack 对 metaheuristics/
   deep_learning 族 −8 并注入评委风险；测试比对有无 pack 的分差。
4. **Innovation Pattern 是否进入 Experiment Planning？** 是——innovation 候选
   的 required_evidence + validation_protocol 全部落进 plan.entries。
5. **Experiment Planning 是否产生 Decision Rule？** 是——每条 entry 均带
   ACCEPT/REJECT/REFINE 规则（测试逐条断言）。
6. **Decision 是否进入 DecisionLog？** 是——select_and_record 写入并携带全部
   追踪字段。
7. **Knowledge Version 能否重现历史 Decision？** 是——CI-07：决策存登记时版本，
   升级后 reproducible 显式翻 False，记录不变。
8. **Evidence Graph 能否否定曾推荐的方法？** 是——CI-06：R001 失效 → 支撑它的
   C001 被传播判死（P7 invalidation 语义）。
9. **Knowledge → Recommendation → Decision → Experiment → Evidence → Validation
   闭环是否成立？** 成立——闭环每一跳都有对应消费代码与测试。
10. **去掉所有 LLM，CI 是否仍工作？** 是——`intelligence.py` 是纯确定性计算层
    （规则 + 结构化知识），零 Agent 依赖；V3 `--execute` 即证明。

## 4. 变更清单（对应交付物 1–14）

| # | 交付物 | 位置 |
|---|--------|------|
| 1 | 审计 | `docs/architecture/COMPETITION_INTELLIGENCE_AUDIT.md` |
| 2 | 设计/实施报告 | 本文档 |
| 3 | Method Card schema | `core/schemas/v3/knowledge/method_card.schema.json`（32 属性） |
| 4 | Failure Memory schema | `failure.schema.json`（20 属性） |
| 5 | Innovation Pattern schema | `pattern.schema.json`（17 属性） |
| 6 | Competition Pack schema | `competition_pack.schema.json`（新建） |
| 7 | Capability Matching | `core/runtime/knowledge/retriever.py` |
| 8 | Candidate Arena | `core/runtime/modeling/candidates.py`（新建） |
| 9 | Planner 集成 | `core/runtime/modeling/planner.py` |
| 10 | Decision Trace | `core/runtime/decisions/log.py` + `modeling/selection.py` |
| 11 | 冲突检测 | `core/runtime/knowledge/packs.py` |
| 12 | 知识版本化 | contracts §决策绑定 + CI-07 测试 |
| 13 | 测试 | `tests/unit/test_competition_intelligence.py`（21 项） |
| 14 | 实施报告 | 本文档 §3 |

## 5. 验收测试指标（P8-22）

| 指标 | 结果 |
|---|---|
| pytest | 0 failed（608 passed, 11 skipped） |
| validate.py | 57/57，0 warning |
| catalog_check | 双视图一致 OK |
| doctor | 0 blocking |
| V3 dry-run | PASS（15 波计划合法） |
| V3 execute | PASS（15/15 节点，state 五件套落盘） |
| CI 测试 | 21 项全 PASS |
