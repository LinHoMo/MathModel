# 项目状态

> 更新：2026-09-07（System Hardening P0 收口）。治理见
> `docs/architecture/THREE_LAYER_ARCHITECTURE.md`，硬化总纲见
> `docs/architecture/HARDENING_PROGRAM.md`。
> **本文件是状态数字的唯一出处：所有数字来自机器命令实测并绑定 commit hash，
> 禁止人工转述其他来源的数字。**

## 当前定位

**Scientific / Mathematical Modeling Harness**：面向数学模型构建、验证与
模型—论文传输的可信 Harness。给一道赛题（或研究问题）→ 建立 Research State →
Workflow DAG → Artifact / Evidence 登记 → 验证门禁 → 论文投影。**Source of
truth = Artifact Registry + Evidence Graph + Research State；Agent / LLM 只是
Executor（GPT / Claude / DeepSeek / MathModelAgent / 人工均可插拔）。**

资产归位三层，自 2026-09-07 起**架构冻结**（不再接受架构革命）：

- **Agent Brain**（角色指令 + 知识层）——研发主战场；
- **Research Runtime**（`core/runtime/`）——冻结（System Hardening 例外经
  `HARDENING_PROGRAM.md` P0–P3 授权）；
- **Guardrails**（validators + gates + 评分链）——冻结（同受硬化计划授权）。

能力进步以基线 Δscore 度量（八项指标，`bench e2e`），不以"新增契约/测试数量"度量。

## 阶段历史

| 阶段 | 内容 | 状态 | 锚点 |
|---|---|---|---|
| V2 P0–P5 | 诚信基线 / rubric / 引用 / 图表 / 知识层 / 定位 | ✅ | `5967940`… |
| V3.1 迁移 | Artifact / Evidence Graph / DAG / Knowledge / Modeling / Writing | ✅ | `1140e96`…`4487cd8` |
| P6 | Runtime Execution（RuntimeSession / 失效传播 / resume） | ✅ | `938227c` |
| P7 | Runtime Integrity & Contract Freeze（rerun/recompute/审计） | ✅ | `4fbea67` |
| P8 | Competition Intelligence（方法卡检索进入决策） | ✅ | `258ea02`… |
| P9 / P9.5 | Research Quality + 红队 | ✅ | `530cd93`… |
| P10 | Paper Intelligence（Finding Graph / Narrative IR） | ✅ | `97d7e7c`… |
| P11 | Scientific Writing（Expression Contract / ParagraphPlan / 红队） | ✅ | `bfd1e84`… |
| P12 | Cross-Question：P12-0 审计 → P12-1 依赖 → P12-2 关系 → P12-3-lite 上下文 → 全阶段冻结 | ✅ 收口 | `856d369`/`92b9efa`/`0302228` |
| P13-3 | Model Construction（3C）→ Model→Paper Transmission（3D/R2/R3） | ✅ | `82eb4fc`/`0036338`/`efc22df` |
| **Hardening P0–P2** | Architecture Freeze + Contract Freeze（Canonical Domain）+ State Truth（reconcile 对账器 / crash 一致性） | ✅ | `9d98e86`/`efc8041` |
| **Hardening P3** | Deterministic Replay / Run Provenance / 并发契约（RunRecord + replay verify/diff + 双问并行隔离） | ✅ | `55df19c` |
| **Hardening P4** | Legacy Isolation：四手降级 `core/legacy/hands/` + 实验目录/脚本迁出 products（validate 57/57 达成） | ✅ | `5a6b051` |
| **Hardening P5** | Regression Gate：零失败基线（781/11，skip 全部分类）+ 五轴 Non-regression 契约 5/5（15 passed） | ✅ | → |

## 当前数字（机器实测，Python 3.12.10）

| 项 | 实测输出 | 生成命令 |
|---|---|---|
| 单元/集成/端到端测试 | **781 passed / 11 skipped / 0 failed（skip 全部分类）** | `py -3.12 -m pytest tests -q` |
| 五轴 Non-regression | **5/5 全绿（15 passed）** | `py -3.12 -m pytest tests/regression -q` |
| 项目级校验 | **57 通过 / 0 失败 / 0 警告** | `py -3.12 core/tools/validate.py` |
| catalog 三方一致 | **OK** | `py -3.12 core/tools/catalog_check.py --check` |

说明：

- Hardening P4 已把研究实验移出 `projects/`（现居 `research/`），库级校验交付
  子集回归 57/57；此前两条「研究实验误报」随迁移消除（记录见
  HARDENING_PROGRAM §3.1 基线注释）。
- **双真源问题档案**：历史文档出现过 228/16、574/11、751/11 三套测试数字与本表
  758/11 并存。自 Hardening P0 起，全部状态数字以本表口径为准；系统内状态真源
  收口（Event Log → Projection → status.json + `state.py reconcile`）在 Hardening
  P2 完成。
- 单项目门禁/校验（`gate.py` / `validate_project.py`）按活跃实例判定；归档参考
  样例 `archives/cumcm2024anew` 为部分样例，不保证全绿。
- Windows 本机 `py` 默认解释器（3.14/3.13）安装损坏，统一用 `py -3.12`。

## 下一步（System Hardening P0–P6，见 `HARDENING_PROGRAM.md`）

```text
Architecture Freeze（P0 ✅）→ Contract Freeze（P1 Canonical Schema + 兼容政策）
→ State Truth + Crash Consistency（P2）→ Deterministic Replay / Concurrency /
Observability（P3）→ Legacy Isolation（P4）→ Regression Gate（P5 零失败基线 +
五轴 Non-regression）→ Release Candidate（P6 九条终验收）
```

终验收九条：旧能力全部保留 ＋ 新能力全部可用 ＋ 新旧边界明确 ＋ 不存在双真源 ＋
可以恢复 ＋ 可以重放 ＋ 可以审计 ＋ 可以验证 ＋ 可以长期扩展。

## 风险与待办

- CUMCM 22 份 rubric 中 13 份 `reference_results` 为空——不凭记忆伪造 GT；每实际
  解出一题回填一份（见 BASELINE_REPORT §6）。
- 完整 CUMCM 题面语料未导入（现有仅题名索引 + 1 份合成示例）。
- 基线暴露的三个 backlog：问题语义未接入选型、方法卡缺种群动力学家族、创新模式卡
  未被管线消费（BASELINE_REPORT §4/§5）——属能力路线图 P13–P17，不在硬化计划内。
- `docs/IMPROVEMENT_PLAN.md` 为 V2 时代文档，仅存档不再维护；`docs/METRICS.md`
  由 `core/tools/metrics.py --write` 机器生成，禁止手改。
- RC 后方向（不属 Hardening 计划）：Provider 插拔工程化、Runtime/Regression/
  Provider/Failure-Injection/Recovery/Cross-domain 基准实验线。