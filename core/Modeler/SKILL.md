---
name: modeler
description: "建模手编排器：串联 8 个建模 agent（问题分析 → 题型识别 → 文献检索 → 方法匹配 → 模型建立 → DAG构建 → 假设验证 → 规格审计），产出 MODEL_SPEC.md。数学建模流程的第一阶段，从赛题到可实现的建模方案。"
---

# Modeler Skill（手级编排器）

## Role

数学建模师（Modeler）：负责问题分析、模型选型、数学建模。本手按 UTG 六层机制拆分为 6 个串联 agent，本文件为手级编排器，负责串联调度、阶段门禁与回退控制，自身不再承载单流程逻辑。

## Contract

- **输入**：项目根 `inputs/` 目录下的赛题文件（PDF/Word/TXT）。
  - `inputs/` 位于项目根（如 `projects/你的项目/inputs/`）。
  - PDF/Word/TXT 用 `Read` 工具直接读取；扫描版 PDF 需 OCR 或图片描述。
- **输出**：`output/MODEL_SPEC.md`（模型规格说明书），交付 Programmer 手。
- **中间产物**：全部写入 `work/` 目录，供下游 agent 与审计消费。

## Agent Orchestra

本手由 8 个 agent 串联组成，顺序固定：

```
problem-parser → type-classifier → literature-searcher → method-matcher → model-builder → dag-builder → assumption-validator → spec-auditor
```

| 序号 | agent | utg_layer | stage | 职责 | 输出 |
|------|-------|-----------|-------|------|------|
| 1 | problem-parser | L1 | 1 | 赛题结构化解析，消除歧义 | work/question_spec.json |
| 2 | type-classifier | L1 | 2 | 题型识别 A/B/C/D/E + 推荐方法方向 | work/type_classification.json |
| 3 | literature-searcher | L1.5 | 1.5 | 文献检索与证据提取，支撑模型选择 | work/literature_evidence.json |
| 4 | method-matcher | L2 | 3 | 方法匹配，从知识库选 ≥2 候选模型 | work/method_candidates.json |
| 5 | model-builder | L3 | 4 | 建立数学模型（公式/符号/边界条件） | work/model_draft.md |
| 6 | dag-builder | L3.5 | 4.5 | 构建子模型依赖 DAG，指导并行与级联 | work/model_dag.json + work/model_dag.svg |
| 7 | assumption-validator | L4 | 5 | 假设四维评分验证 | work/assumption_validation.json |
| 8 | spec-auditor | L5+L6 | 6 | MODEL_SPEC 护栏检查 + 哈希审计 | output/MODEL_SPEC.md + work/audit_log.json |

每个 agent 的详细契约见 `core/Modeler/agents/<name>/SKILL.md`。编排器只负责按 stage 顺序调用、检查阶段门禁、触发本手内回退。

## Stage Gates

每个 agent 输出后必须通过对应自检（详见各 agent SKILL.md 的 `## Self-Check`），任一失败在本手内回退，不向 Programmer 交付：

| stage | agent | 门禁通过条件 | 失败回退目标 |
|-------|-------|-------------|-------------|
| 1 | problem-parser | question_spec.json 符合 core/schemas/question_spec.schema.json；validate() valid==true | 自身重解析 |
| 2 | type-classifier | topic_type 落在枚举内；confidence >= medium | 回退 stage 1 补 domain_keywords |
| 1.5 | literature-searcher | literature_evidence.json 符合 schema；selected_count ∈ [5,8] 或 skipped=true；无未来文献；覆盖所有子问题 | 自身重检索（消耗额度）或标记 skipped |
| 3 | method-matcher | 每个子问题候选数 >= get("modeling.min_candidate_models")；候选有实质差异；有文献证据支撑 | 回退 stage 2 复核方向，或 stage 1.5 补证据 |
| 4 | model-builder | 公式语法通过 FormulaChecker；SymbolRegistry 无冲突；每子问题有 formulas/boundary_conditions | 自身重推导 |
| 4.5 | dag-builder | model_dag.json 符合 schema；节点=子问题；边=数据/参数依赖；无环；SVG 可渲染 | 回退 stage 4 补完依赖信息 |
| 5 | assumption-validator | 每个假设 composite_score >= get("modeling.assumption_score_threshold")；无矛盾 | 回退 stage 4 修正假设/模型 |
| 6 | spec-auditor | MODEL_SPEC 符合 core/schemas/model_spec.schema.json；Guardrails.has_errors()==False；HashChain.verify_chain()==True | 回退 stage 4 修正文本/字段 |

回退规则：回退到指定 stage 后，从该 stage 重新执行并向后流，所有下游产物重新生成。

## Env Bindings

本手读取的 env 参数（通过 `core/env/loader.py` 的 `get(key, default)` 读取）：

| 参数 | 默认值 | 读取 agent | 作用 |
|------|--------|-----------|------|
| `modeling.min_candidate_models` | 2 | method-matcher | 每个子问题最少候选模型数（M1） |
| `modeling.assumption_score_threshold` | 6.0 | assumption-validator | 假设综合评分通过阈值（M2） |
| `modeling.literature_search_enabled` | true | literature-searcher | 文献检索总开关 |
| `modeling.literature_max_searches` | 5 | literature-searcher | 最大检索次数（硬上限） |
| `modeling.literature_target_count` | 7 | literature-searcher | 目标入选文献数 |
| `modeling.literature_score_threshold` | 6.0 | literature-searcher | 入选最低评分 |
| `modeling.literature_chinese_ratio` | 0.5 | literature-searcher | 中文文献最低占比 |

```python
from core.env.loader import get
min_n = get("modeling.min_candidate_models", default=2)
threshold = get("modeling.assumption_score_threshold", default=6.0)
lit_enabled = get("modeling.literature_search_enabled", default=True)
max_searches = get("modeling.literature_max_searches", default=5)
```

其余 env 参数（paper/code/runtime）由 Programmer/Writer 手消费，本手不读取。

## UTG Layer Mapping

UTG 六层由本手 8 个 agent 承载（L1.5/L3.5 为细化层）：

| UTG 层 | 机制 | 承载 agent | 对应铁律 |
|--------|------|-----------|---------|
| L1 | 形式化规约（消除输入歧义 + 结构化输出） | problem-parser + type-classifier | M1/M4/M7（结构） |
| L1.5 | 形式化规约 + 外部知识注入 | literature-searcher | M1（证据支撑选型） |
| L2 | 工具调用（候选对比必须结构化） | method-matcher | M1 |
| L3 | 过程验证（推导链/符号/边界） | model-builder | M3/M4/M5/M6 |
| L3.5 | 过程验证 + 依赖结构化 | dag-builder | M3/M7（依赖可视化） |
| L4 | 异构验证（假设量化评分） | assumption-validator | M2 |
| L5 | 运行时护栏（禁用词/占位符/AI 痕迹） | spec-auditor | M7（可读性） |
| L6 | 事后哈希审计（中间产物篡改检测） | spec-auditor | 全链可信 |

## Laws

详见 `core/Modeler/laws/rules.md`。M1-M7 完整保留，分布于各 agent 的 Self-Check 与 Stage Gates 中执行：

### M1: 模型选择必须比较至少2个候选方法
- 防御层次：L1 结构化输出
- 比较至少两个可信的模型家族后再选择
- 物理约束和业务约束优先级高于拟合好看
- 计算方便不能成为删除关键机制的理由
- 启发式算法不能直接宣称全局最优
- 承载：method-matcher（候选 >= `min_candidate_models`）

### M2: 每个假设必须有量化验证
- 防御层次：L2 工具调用
- 关键假设必须通过四维评分：物理合理性（30%）+ 数学一致性（25%）+ 数据支撑度（25%）+ 影响程度（20%）
- 综合评分 ≥ 阈值（默认 6.0）才能通过
- 验证方法选择恰当，判断标准明确
- 承载：assumption-validator

### M3: 数学推导必须从基本定律到最终模型，每步有依据
- 防御层次：L3 过程验证
- 推导链路完整：基本定律→数学模型→边界条件→求解方法→验证
- 每一步都要有数学依据，跳步推导必须补充完整
- 承载：model-builder

### M4: 符号定义必须完整，含量纲，全文一致
- 防御层次：L1 结构化输出
- 一个符号只表示一个物理量，全文使用同一符号，使用国际通用符号，所有符号都要在符号表中定义
- 承载：model-builder（SymbolRegistry）

### M5: 边界条件必须明确列出
- 防御层次：L3 过程验证
- 初始位移、初始速度、固定边界、自由边界、周期边界条件、所有约束条件
- 承载：model-builder

### M6: 启发式算法不能直接宣称全局最优
- 防御层次：L4 异构验证
- 除非有证明、精确求解对照或足够可信的稳定性验证；必须说明算法局限性；必须进行灵敏度分析
- 承载：model-builder + spec-auditor 复核

### M7: MODEL_SPEC.md 必须包含所有子问题的完整建模方案
- 防御层次：L1 + L3 结构化输出 + 过程验证
- 每个子问题都有完整建模方案，包含问题理解、模型假设、符号定义、模型建立、代码实现要求、验证要求
- 承载：spec-auditor（schema + 护栏）

### M8: 模型复杂度必须匹配问题规模与数据可得性
- 防御层次：L3 过程验证
- 禁止为小规模问题套用大模型（如 5 个决策变量用深度强化学习）
- 禁止在数据不足时强行用高参数模型（参数量 > 样本量/10）
- 模型选择须在 MODEL_SPEC 中显式论证：为何该复杂度必要、有何简化替代、对结果影响几何
- 承载：model-builder + spec-auditor 复核

### M9: 关键结果必须可解释、可追溯、可复现
- 防御层次：L4 + L6 异构验证 + 事后审计
- 核心输出（最优解/预测值/评价指标）须给出：数学表达式、代码实现位置、all_results.json 键路径、灵敏度范围
- 黑盒模型（NN/集成/强化学习）必须提供：特征重要性、SHAP/部分依赖图、反事实解释
- 承载：model-builder + assumption-validator + spec-auditor

## Knowledge

> 路径约定：无前缀的 `core/knowledge/` 指项目根共享知识库；`core/Modeler/knowledge/` 指本手私有知识库。

- `core/knowledge/methodology/` - 50 个方法论文档 + 选型决策树 + INDEX（method-matcher / model-builder 消费）
- `core/Modeler/knowledge/domain/` - 43 个领域知识文档（type-classifier / method-matcher 消费）
- `core/Modeler/knowledge/problem-types/` - 5 个题型专项文档 A/B/C/D/E（type-classifier 消费，含题型识别决策树）
- `core/knowledge/paper-cases/` - 116 篇论文拆解 + METHOD-MAPPING.md + INNOVATION-TAGS.md（method-matcher 消费）
- `core/validators/modules/` - problem_spec_parser.py / symbol_registry.py / formula_checker.py / assumption_validator.py / scholar_fetch.py（各 agent 工具调用）
- `core/knowledge/cookbooks/` - 8 大类算法手册（优化/ML/评价/机理/统计/网络/聚类/博弈），method-matcher 消费
- `core/knowledge/playbooks/` - 12 个端到端例题（国赛 9 + 美赛 3），含拆题→代码→论文全流程
- `core/Modeler/knowledge/paper-bridge.md` - MODEL_SPEC 到论文章节的映射规则与数值占位符协议
- `core/Modeler/laws/rules.md` - 建模手铁律（M1-M9）
- `core/schemas/question_spec.schema.json` - 赛题规约 Schema（problem-parser 输出契约）
- `core/schemas/model_spec.schema.json` - 模型规格 Schema（spec-auditor 输出契约）
- `core/schemas/literature_evidence.schema.json` - 文献证据 Schema（literature-searcher 输出契约）
- `core/Modeler/agents/` - 8 个子 agent 的 SKILL.md（UTG 各层实体）

## Output Contract

输出 `output/MODEL_SPEC.md`，格式见 `core/Modeler/templates/MODEL_SPEC_TEMPLATE.md`，由 spec-auditor 最终渲染。

**输出有效性条件**（全部满足才算输出成功，由 Stage Gates 保证）：
1. MODEL_SPEC.md 存在且非空
2. 包含 5 个必要章节（问题理解/模型假设/符号说明/模型选型/模型建立）
3. 符合 `core/schemas/model_spec.schema.json` 全部 required 字段
4. 假设综合评分均 >= `get("modeling.assumption_score_threshold")`（默认 6.0）
5. 符号表至少 1 个符号，全文一致（SymbolRegistry 无冲突）
6. 候选模型至少 `get("modeling.min_candidate_models")` 个（默认 2）
7. 每个子问题有完整建模方案（method/formulas/boundary_conditions/solution_approach）
8. 护栏检查通过（Guardrails.has_errors()==False：无禁用词、无占位符、无 AI 痕迹）
9. 哈希链完整（HashChain.verify_chain()==True，audit_log.json 已生成）
