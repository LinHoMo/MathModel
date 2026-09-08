# Dead Asset Report — MathModel Repository

> 生成日期：2026-09-08 | 基线 commit：`af1bbd5`（Tier 0 删除后）
> 基于：02_DEBT_LEDGER.md（上一轮审计）+ Tier 0 执行结果 + FILE_INVENTORY.json（1808 文件）
> 原则：删除必须满足 no active reference + no provenance value + no reproducibility value + no historical research value。不能证明则不删除只标记。

---

## 1. 已执行删除（Tier 0，本轮完成）

| ID | 路径 | 数量 | 分类 | 删除理由 | 验证 |
|---|---|---|---|---|---|
| DEBT-001 | `research/P13-3D-R3/prompts/_tmp_*.txt` | 12 | temp-artifact | Grep 全仓库零引用，临时 prompt 导出 | ✅ 文件不存在 |
| DEBT-002 | `core/tools/run_p13_3d.py` | 1 | broken-shim | 目标文件 `core/tools/evaluation/run_p13_3d.py` 不存在（Test-Path=False） | ✅ import 不报错 |
| DEBT-002b | `core/tools/fidelity_gate.py` | 1 | broken-shim | 目标文件不存在 | ✅ 同上 |
| DEBT-003 | `tests/tests/` | 1 目录 | duplicate | 嵌套错误目录，`sample_problem.txt`（18B）是 `tests/fixtures/`（54B）的错误副本 | ✅ pytest 收集不受影响 |
| DEBT-007 | `research/P13-3D/inputs/` | 1 目录 | empty | 0 文件空目录 | ✅ 目录不存在 |
| DEBT-008 | `research/bench-m4-2000c/work/mc_scorecard_v2.json` | 1 | superseded | v2 重复评分卡 | ✅ 文件不存在 |

**合计：17 项删除，零回归（pytest 781 passed / 11 skipped）。**

---

## 2. 标记为 DEAD 但未删除（需进一步验证）

| ID | 路径 | 分类 | 标记理由 | 未删除原因 | 建议动作 |
|---|---|---|---|---|---|
| DEAD-001 | `core/evaluation/`（6 文件，仅 `__init__.py`） | dead-package | V3 前向兼容空壳包，实际逻辑在 `core/tools/evaluation/` | 可能被 import 兼容引用，需 Grep 确认无消费方 | DEFER：确认无引用后合并到 tools/evaluation/ |
| DEAD-002 | `tests/compat/test_runtime_compat.py` | stale-test | V2 多运行时兼容测试，引用 V2 状态文件规范 | 可能仍有 V2 兼容模式消费方 | DEFER：V2 兼容层保留期间不删除 |
| DEAD-003 | `tests/test_tex_to_docx_quick.py` | orphan-script | 非 pytest 格式（无 `def test_`），不会被 pytest 收集 | 可能是手动调试脚本，有参考价值 | MOVE：移到 `scripts/` 或标记为 manual tool |
| DEAD-004 | `docs/IMPROVEMENT_PLAN.md`（21KB） | stale-doc | V2 时代文档，STATUS.md 明确"仅存档不再维护" | 有历史参考价值 | ARCHIVE：移到 `docs/architecture/` |
| DEAD-005 | `docs/TEAM_GUIDE.md`（6.9KB） | stale-doc | 引用 V2 四手结构（Modeler 6 agent 等），未更新 V3 五角色 | 有历史参考价值 | UPDATE：更新为 V3 结构，或 ARCHIVE |
| DEAD-006 | `docs/integration/harness-compat.md` | stale-doc | 引用 V2"四手"契约（MODEL_SPEC.md → CODE_DELIVERABLES.md → PAPER_SPEC.md），未更新 V3 DAG | V2 兼容模式可能仍引用 | UPDATE：更新为 V3 DAG 节点 |
| DEAD-007 | `docs/decisions/2026-09-04-refactor-plan-v2.md`（38KB） | completed-plan | 已完成的重构计划诊断文档 | 有决策记录价值 | ARCHIVE：移到 `docs/architecture/` |
| DEAD-008 | `package.json`（495B） | stale-config | V2 描述，无实际依赖，test 脚本为占位符 | 可能被 npm 工具引用 | DOCUMENT：标记为 legacy，或 DELETE（确认无引用后） |
| DEAD-009 | `adapters/openai.yaml`（8.7KB） | generated-stale | 自动生成但内容含 V2 术语（"4 手 29 agent"）和错误路径（`core/AGENTS.md`） | RC-S3 provider boundary 审计依赖此文件作为声明证据 | REGENERATE：修复生成器模板后重新生成 |
| DEAD-010 | `research/bench-m4-2000c-p131-b/c`（2 目录） | orphan-research | 变体基准，Grep 确认无外部代码引用 | 保留 registry/evidence_graph 研究证据 | ARCHIVE：移到 `research/archives/` |
| DEAD-011 | `research/bench-m4-2000c-p132-a/b/c`（3 目录） | orphan-research | 同上 | 同上 | ARCHIVE：同上 |
| DEAD-012 | `research/bench-p132-2023c/`（1 目录） | orphan-research | 同上 | 同上 | ARCHIVE：同上 |

---

## 3. 标记为 ACTIVE 但有问题（非 dead，需修复）

| ID | 路径 | 问题 | 严重度 | 修复动作 |
|---|---|---|---|---|
| ACTIVE-001 | `examples/problems/cumcm2024A.txt` | 内容错误（防空导弹 ≠ 板凳龙），P0 输入污染 | 🔴 P0 | 替换为真实题面（待 Input Authenticity Recovery） |
| ACTIVE-002 | `projects/p151-2024a/inputs/cumcm2024A.txt` | 同上（项目副本） | 🔴 P0 | 从真源重新复制 |
| ACTIVE-003 | `core/tools/evaluation/e2e_metrics.py` | 无 non-emptiness check，method_selection 字符串匹配，model_correctness 依赖外部输入 | 🔴 P0 | 重设计 evaluator（待 Evaluator Audit） |
| ACTIVE-004 | `research/P15/benchmark/CUMCM-Bench-v2.json` | 2024_A 题面与实际输入不一致，4/5 题 input_file=null | 🔴 P0 | 修复题面引用，补全 input_file |
| ACTIVE-005 | `research/P15/benchmark/manifests/p151-2024a-run.json` | latency=0.06s, provider=null, 空壳 artifact | 🔴 P0 | 废弃此 B0，建立 P15.1-2024A-B0-R2 |
| ACTIVE-006 | `core/knowledge/bench/`（136 文件） | benchmark 语料越界驻留 runtime knowledge | 🟠 P1 | MOVE 到 `research/benchmarks/corpus/` |
| ACTIVE-007 | `projects/p151-2024a/` + `projects/rcs1-2024a/` | 两个项目 state 文件大小完全相同，均停留在 init 阶段 | 🟠 P1 | 标记为 fixture，不作为真实运行实例 |
| ACTIVE-008 | `core/runtime/adapters/` | Provider boundary 实现不完整（空包） | 🟡 P2 | 不影响核心流程，后续完善 |
| ACTIVE-009 | `~72 个 fixture-existence 测试` | 纯 `os.path.exists` 测试拉低测试质量信号 | 🟡 P2 | 标记或合并，不删除 |

---

## 4. 绝对不能删除（Research Evidence ≠ Garbage）

以下文件即使不被 runtime import，也具有科研证据价值，**禁止删除**：

| 路径 | 价值 |
|---|---|
| `research/P13-3D/`（106 文件） | P13-3D 首轮实验完整证据链（negative but informative） |
| `research/P13-3D-R2/`（130 文件） | R2 复现实验冻结 output |
| `research/P13-3D-R3/`（195 文件，已删 12 个 tmp） | R3 真实 Writer 对照实验（prompts/golden_set/real_evaluation/real_papers） |
| `research/P14/`（134 文件） | P14 pilot PASS 完整证据（21/21 replay match + hash manifest） |
| `research/RC-SMOKE/`（4 文件） | RC-S1/S3 PASS 证据 |
| `core/knowledge/bench/e2e/`（114 文件） | P13 实验固化语料（10 真题三臂 artifact + 盲评矩阵） |
| `research/bench-m4-2000c/`（主目录） | regression test 引用的基线（`test_non_regression_contract.py` 消费） |
| `docs/architecture/`（48 文件） | P0-P15 各阶段研究报告与架构文档 |
| `archives/cumcm2024anew/`（10 文件） | 历史基线参考（validate.py 显式排除出实时校验） |

---

## 5. 统计总览

| 类别 | 数量 |
|---|---|
| 已删除（Tier 0） | 17 项 |
| 标记 DEAD 待处理 | 12 项 |
| ACTIVE 但需修复 | 9 项（4 P0 / 2 P1 / 3 P2） |
| 绝对不能删除（Research Evidence） | 10 类 |
| 仓库总文件数（排除缓存） | 1808 |

**删除率**：17 / 1808 = 0.94%。严格遵守"不因为看起来没用就删除"原则。

---

*报告生成时间：2026-09-08 | 下一步：等待 Input/Execution/Evaluator/Capability 四个子代理完成测量恢复工作，然后整合为 MEASUREMENT_RECOVERY_REPORT.md 和 CAPABILITY_VALIDATION_ROADMAP.md*
