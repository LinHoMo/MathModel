# P1-M4 — Knowledge-guided Construction（知识引导建模）报告

- 仓库：`C:\Users\Lin\Desktop\Programs\MathModel`；日期：2026-09-09
- 前置：VS-001（可执行模型闭环）+ M3（候选竞技场 + evidence-based selection）已交付
- 依据：`STRATEGY_P1_VS001.md` §10（BZD = knowledge/reviewer substrate，只吸收
  applicability/assumptions/failure modes/validation obligations，经验数值不得当 truth）

## 目标回顾

最后再接 BZD 知识，形成 `Problem → Knowledge Retrieval → Candidate Models →
Execution → Validation → Evidence → Selection` 全链。可测量：知识是否提升建模能力
（义务完备度差异），使 K002 测量有意义。

## 7 条验收证据

| # | 验收 | 证据 |
|---|---|---|
| ① | 知识卡→候选义务映射真实可跑（validations 来自方法卡，溯源 card_id） | `candidates.map_card_obligations`：card.validation/required_conditions+prerequisites/risks/requires → 候选 validations/assumptions/risks/dependencies，每项带 `source_card`；单测 `test_map_card_obligations_source_card` / `test_generate_candidates_populates_obligations`；e2e 断言 GUIDED MIR001 的 sourced validations 每项 `source_card ∈ {mc-bzd-model-fit, mc-bzd-validation-obligations}` 且 obligation 文本等于方法卡 validation |
| ② | BZD 试点卡 3-5 张落盘、yaml 合法、retriever 可检索、source=BZD | 5 张卡 `core/knowledge/methods/cards/mc-bzd-{model-fit,failure-modes,validation-obligations,judging-criteria,sensitivity}.yaml`，均 `source_type: BZD` + source_refs 出处；`KnowledgeRetriever` 加载全绿，`recommend({"problem_types":["knowledge_guide"]})` 全部命中；不污染其他查询（evaluation 查询无 BZD 卡） |
| ③ | 对比 demo 真实跑通 + 对比表入报告 | `research/P15/m4_run/`：双候选各真 subprocess（EXEC001/EXEC002 rc=0, status=success, body_spacing=1.65）+ 数值验证（VR001/VR002 均 passed, cv=0.0, robustness=1.0）；对比表见下节 |
| ④ | 新增测试 + 全量不回归 | pytest **910 passed / 4 skipped**（897 基线 +13 新增，零回归）；catalog_check OK；validate **57/0** |
| ⑤ | LLM-free：知识只产生候选/义务/约束，core 不判 PASS；候选外部注入 | 候选 MODEL_IR/Code 由 `m4_fixtures.py` 手写注入（GUIDED 义务由 BZD 卡机械映射）；EXEC provenance.adapter=local_python（e2e test_06）；core 无 LLM 调用 |
| ⑥ | 禁越界 | 仅改 `core/runtime/modeling/candidates.py` + `__init__.py`、`core/runtime/execution/handlers.py`、`core/knowledge/methods/cards/` 5 张新卡、`research/P15/m4_run/`、计划与报告；未新增 Agent/Skill/论文模块/无关 schema；K002/frozen_specs/preregistration/raw_k002 全程未触碰 |
| ⑦ | 按序 commit（feat(p1-m4):）+ 报告，不 push | 见 commit 列表；未 push |

## BZD 试点卡清单（5 张）

| card_id | 主题 | source | requires/risks/validation 字段 |
|---|---|---|---|
| `mc-bzd-model-fit` | 模型适配判断（problem features → method applicability） | BZD（提取自 P15 三仓库审计材料，2026-09-09） | 2/3/3 ✓ |
| `mc-bzd-failure-modes` | 常见失败模式/扣分点 | BZD（同上） | 2/4/4 ✓ |
| `mc-bzd-validation-obligations` | 验证义务/论文自查 | BZD（同上） | 2/3/4 ✓ |
| `mc-bzd-judging-criteria` | 评委评审规则 | BZD（同上） | 2/4/3 ✓ |
| `mc-bzd-sensitivity` | 敏感性分析义务 | BZD（同上） | 2/3/3 ✓ |

## 对比 demo 结果摘要（2024_A Q1，共用正确求解器 C2_CODE）

| 指标 | 知识引导 GUIDED（MIR001） | 无引导 UNGUIDED（MIR002） |
|---|---|---|
| model_id | M2024A-Q1-GUIDED | M2024A-Q1-UNGUIDED |
| validations 项数 | 8（其中 7 项带 source_card ∈ BZD 卡；1 项为建模者自身 VAL001） | 1（VALBASE01，无知识来源） |
| assumptions 项数 | 5（2 项带 source_card ∈ BZD 卡） | 1（ASSU-BASE-01） |
| risks 项数 | 6（全部带 source_card ∈ BZD 卡） | 0 |
| **义务完备度合计** | **19** | **2** |
| dependencies | 6（2 结构依赖 + 4 条 BZD requires 结构化声明） | 2（仅结构依赖） |
| knowledge_refs | [{mc-bzd-model-fit}, {mc-bzd-validation-obligations}] | [] |
| EXEC | EXEC001 rc=0 success, body_spacing=1.65 | EXEC002 rc=0 success, body_spacing=1.65 |
| VR | VR001 passed, mathematical_valid=True, cv=0.0, robustness=1.0 | VR002 passed, mathematical_valid=True, cv=0.0, robustness=1.0 |
| 选型 | D002 chosen=MIR001（两候选 cv 平局 → 确定性 tie-break，confidence=0.6，如实呈现） |

**如实结论（不预设"知识必胜"）**：义务完备度差异可测量（19 vs 2，引导候选声明了方法卡
的验证义务/风险/适配前提，全部可溯源），但两候选共用同一正确求解器 → 执行/验证数值
完全一致（均 PASS）→ 选型平局。这恰好是"知识影响建模声明（义务），数值裁决由执行/
验证负责"的体现——知识不改变物理，但让建模者的义务声明可被审计。

## 修改清单（commit 级）

| commit | 改动文件 | 内容 |
|---|---|---|
| `ad2ce5b` | `core/runtime/modeling/candidates.py`、`core/runtime/modeling/__init__.py`、`core/knowledge/methods/cards/mc-bzd-*.yaml`（5 张新增）、`core/runtime/execution/handlers.py` | 知识义务映射（map_card_obligations/_merge_obligations + Candidate 字段 validations/dependencies/assumptions + generate_candidates 填充）；BZD 试点卡 5 张；共享 code 多候选独立执行链（execute_code 按候选 MIR 执行、EXEC.data.model_id 定位）+ 候选→VR 证据归位修复（_candidate_vr_table 按 model_id） |
| `ec4544a` | `tests/runtime/test_knowledge_obligation_mapping.py`（新增）、`tests/integration/test_p1_m4_guided_vs_unguided.py`（新增） | 义务映射单测 6 项 + 引导 vs 无引导 e2e 7 项 |
| `62ccbb7` | `research/P15/m4_run/`（m4_fixtures/m4_driver 复用/run_m4_demo + project 落盘 + m4_summary.json）、`research/P15/analysis/P1_MODEL_CONSTRUCTION_IMPLEMENTATION_PLAN.md` | 对比 demo 落盘（registry/evidence_graph/status/replay_report/m4_summary）+ 计划标记 M4 完成 |
| 本报告（当前 commit） | `research/P15/analysis/P1_M4_REPORT.md` | 本报告 |

## 验证数字

| 检查 | 结果 |
|---|---|
| `py -3.12 -m pytest tests -q` | **910 passed, 4 skipped**（98.4s） |
| `py -3.12 core/tools/catalog_check.py --check` | **OK** |
| `py -3.12 core/tools/validate.py` | **57 通过, 0 失败, 0 警告** |
| `py -3.12 -m pytest tests/runtime/test_knowledge_obligation_mapping.py tests/integration/test_p1_m4_guided_vs_unguided.py -q` | **13 passed** |
| 复跑 M3/VS-001 e2e | 15 passed（handler 修改向后兼容） |

## Replay 复现

```powershell
py -3.12 research/P15/m4_run/run_m4_demo.py   # 自清理重建 project/ + m4_summary.json
py -3.12 -m pytest tests/integration/test_p1_m4_guided_vs_unguided.py -q
```

`m4_summary.json` 实测：EXEC001/EXEC002 重放均 `ok=true, outputs_match=true, deviation=[]`
（零偏差）。demo 落盘：`research/P15/m4_run/project/state/{registry.json,evidence_graph.json,status.json}` + `artifacts/exec/{input.json,output.json}`。

## 主要困难与解决

1. **共享 code 去重破坏候选独立链**：M4 双候选设计上共用同一正确求解器，而 M3 的
   `_register_code` 按 code_hash 去重 → 只有 1 个 EXEC/VR。解决：`execute_code` 改为按
   候选 MIR 逐个执行（EXEC.data.model_id 记录所属候选），同 code 文本可共享 CODE
   artifact 但 EXEC/VR 每候选独立；`_candidate_vr_table` 同步改为按 EXEC.model_id 归位
   （不再沿共享 CODE 的边反查，消除歧义）。
2. **MODEL_IR 契约与"义务缺失"形态**：契约要求 validations/assumptions 非空且带 id。
   "无引导"落地为"极少"（1 条通用验证 + 1 条通用假设，无 source_card/knowledge_refs），
   而非空数组——如实量化"不声明验证义务"。
3. **CRLF 文件 Edit 失败**：Windows 下 Write 产出 CRLF 测试文件，native Edit 匹配失败；
   用 LF 补丁脚本做文本替换。

## 偏差记录

- 任务书"无引导候选 validations=[] 或极少"：落地为"极少"（MODEL_IR 契约不允许空数组），
  报告 §对比表已如实标注。
- `map_card_obligations` 的 assumptions 来源采用 required_conditions + prerequisites
  （方法卡无独立 assumptions 字段）；risks 同时进候选 risks（结构化记录）。
- 选型平局（两候选均 PASS、cv 相同）时按确定性 tie-break 选 MIR001（创建序），
  confidence=0.6——如实呈现，未伪造"知识必胜"差异。
