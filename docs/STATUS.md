# 项目状态

> 更新：2026-09-09（K002 FROZEN + P1 Model Construction Loop 进行中）。治理见
> `docs/architecture/THREE_LAYER_ARCHITECTURE.md`，硬化总纲见
> `docs/architecture/HARDENING_PROGRAM.md`。
> **本文件是状态数字的唯一出处：所有数字来自机器命令实测并绑定 commit hash，
> 禁止人工转述其他来源的数字。**

## 当前定位

**Scientific / Mathematical Modeling Harness**：面向数学模型构建、验证与
模型—论文传输的可信 Harness。给一道赛题（或研究问题）→ Model Construction →
Model Artifact → Execution → Validation → Evidence Graph → Revision →
Research State → 论文投影。**Source of truth = Artifact Registry + Evidence
Graph + Research State；Agent / LLM 只是 Executor（GPT / Claude / DeepSeek /
MathModelAgent / 人工均可插拔，The Agent Is Not The State）。**

资产归位三层，自 2026-09-07 起**架构冻结**（不再接受架构革命）：

- **Agent Brain**（角色指令 + 知识层）——研发主战场；
- **Research Runtime**（`core/runtime/`）——冻结（System Hardening 例外经
  `HARDENING_PROGRAM.md` P0–P3 授权）；
- **Guardrails**（validators + gates + 评分链）——冻结（同受硬化计划授权）。

能力进步以基线 Δscore 度量（八项指标，`bench e2e`），不以"新增契约/测试数量"度量。
**infra 不冒充 capability**：新基础设施必须回答"它改变了哪个可测量的 Model
Construction 行为？"。

## 阶段历史

| 阶段 | 内容 | 状态 | 锚点 |
|---|---|---|---|
| V2 P0–P5 | 诚信基线 / rubric / 引用 / 图表 / 知识层 / 定位 | ✅ | `5967940`… |
| V3.1 迁移 | Artifact / Evidence Graph / DAG / Knowledge / Modeling / Writing | ✅ | `1140e96`…`4487cd8` |
| P6–P12 | Runtime Execution / Integrity / Competition Intelligence / Research Quality / Paper Intelligence / Scientific Writing / Cross-Question | ✅ | `938227c`…`0302228` |
| P13-3 | Model Construction（3C）→ Model→Paper Transmission | ✅ | `82eb4fc`/`0036338`/`efc22df` |
| Hardening P0–P6 | Architecture/Contract Freeze + State Truth + Replay + Legacy Isolation + Regression Gate + Release Candidate | ✅ | `9d98e86`…`v3.1.0（RC）` |
| P15.0/P15.1 | CUMCM Benchmark Freeze + B0 Alignment Baseline | ✅ | `8751c45`（tag `p15.0-benchmark-freeze`）/ `af1bbd5`（tag `p15.1-b0-baseline`） |
| **P15-K001** | 2×2×rep 预注册（Knowledge × Case + Sham），55 runs，盲评 + DATA FREEZE + 配对分析 | ✅ CLOSED | Δ_K=+2.14 CI[+0.00,+6.41] → **negative result**；`de15d96` |
| **P15-K002** | Model Representation Efficacy（F/S/S+V 三臂），rubric v1.1 测量校准 + 预检区分度验证 + 五 Gate | 🔒 **FROZEN**（38 文件哈希锁定） | `0cf4d5f` |
| **P1** | Model Construction Loop：Gap Audit（11 环节）→ P1 计划 v2（C1–C10）→ VS-001 垂直切片 | 🔄 进行中 | `554e4ff`/`1534fa5` |

## 当前数字（机器实测，Python 3.12.10，截至 2026-09-09）

| 项 | 实测输出 | 生成命令 |
|---|---|---|
| 单元/集成/端到端测试 | **882 passed / 4 skipped / 0 failed（skip 全部分类）** | `py -3.12 -m pytest tests -q` |
| 项目级校验 | **57 通过 / 0 失败 / 0 警告** | `py -3.12 core/tools/validate.py` |
| catalog 三方一致 | **OK** | `py -3.12 core/tools/catalog_check.py --check` |
| 术语零残留 | **OK**（production 零残留，无行内豁免） | `py -3.12 core/tools/catalog_check.py --check-terminology` |
| K001 冻结校验 | **PASS（44 文件）** | `py -3.12 research/P15/scripts/k001_freeze.py --check` |
| K002 冻结校验 | **PASS（38 文件）** | `py -3.12 research/P15/scripts/k002_freeze.py --check` |

说明：

- **双真源问题档案**：历史文档出现过 228/16、574/11、751/11、774/11、855/4 多套
  测试数字与本表并存。自 Hardening P0 起，全部状态数字以本表口径为准；旧数字
  一律作废（P1 进行期间 pytest 计数随 Organizer 提交演进，以每次 commit 时实测为准）。
- K001 冻结基线于 2026-09-09 因术语治理迁移（`allowed_model_families` →
  `allowed_modeling_structures`，5 题 gt.json）重冻——评分数据独立冻结于 DATA
  FREEZE（165 文件）未受影响，漂移原因记录于 `GOVERNANCE_REPORT §7.1`。
- Windows 本机 `py` 默认解释器（3.14/3.13）安装损坏，统一用 `py -3.12`。

## 下一步

```text
P1（Model Construction Loop，进行中）：
  C1 MODEL_IR 升入 core ✅（1534fa5）→ C5 Method→Instantiation → C6 Code 节点
  → C7 Execution 接线 → C8 Validation L0-L2 → C9 门禁硬化 → C10 e2e 闭环测试
  → VS-001 验收（M1 → FAIL → M2 → PASS，replay 可重现）

K002 正式实验（P1 闭环打通后执行）：
  run_order 生成 → 108 runs（主检验 45 + 泛化 15，F/S/S+V）→ 盲评（rubric v1.1）
  → 配对分析（Representation Effect）→ 决策门

P16+（K002 之后）：
  Candidate Arena（基于 Evidence 的选择）→ Knowledge-guided Construction
  （BZD 知识接入）→ Capability Validation（Δscore 基准）
```

## 风险与待办

- **K002 测量边界**：v1.1 重评证实 L2 区分度恢复（E4 候选对比为唯一区分要素）；
  S 臂若 candidates 缺失将系统性失分——模板已加字段，正式实验须守。
- **P1 闭环铁律**：`execution_status=success` 不得推出 `model_status=correct`；
  `ExecutionResult.status` 只能来自真实执行状态，禁止 handler 默认生成。
- CUMCM 22 份 rubric 中 13 份 `reference_results` 为空——不凭记忆伪造 GT。
- 完整 CUMCM 题面语料未导入（现有仅题名索引 + 已 verified 的 K001/K002 题面）。
