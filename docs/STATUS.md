# 项目状态

> 更新：2026-09-08（仓库清理 + P15 研究基础设施）。治理见
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
| **Hardening P5** | Regression Gate：零失败基线（781/11，skip 全部分类）+ 五轴 Non-regression 契约 5/5（15 passed） | ✅ | `2ea318c` |
| **Hardening P6** | Release Candidate：九条终验收全部有证据（终检序列全绿） | ✅ | `v3.1.0（RC 收口：P13-3D 关闭 · P14 pilot PASS · RC smoke S1/S3 PASS）` |
| **P15.0** | CUMCM Benchmark Freeze（36 题 × 7 gold fields，5 脚本，4 基线问题卡，schema + 3 catalog 索引） | ✅ | `8751c45`（tag `p15.0-benchmark-freeze`） |
| **P15.1** | B0 Alignment Baseline（2024_A B0 首轮 + B0-R2 改进轮，decomposition_coverage = UNRESOLVED） | ✅ | `af1bbd5`（tag `p15.1-b0-baseline`） |
| **仓库清理** | `.claude/` → `core/skills/syslab/`（101 files）+ `archives/` → `tests/fixtures/` + `package.json` 移除 + `.opencode/` → `docs/architecture/` + P0 测量修复 + P15 研究基础设施 + 仓库审计 | ✅ | `691bdd0`…`b6540e3`（3 commits，non-regression 781/11 不变） |
| **core/tools 统一** | 7 个子目录内联为独立文件 + 删除子目录（37 files）+ core/evaluation/ 空壳删除 + adapters 迁移 + AI 配置 V2→V3 + 测试修正 | ✅ | `7f29443`…`9199f03`（4 commits，non-regression 774/11） |

## 当前数字（机器实测，Python 3.12.10）

| 项 | 实测输出 | 生成命令 |
|---|---|---|
| 单元/集成/端到端测试 | **774 passed / 11 skipped / 0 failed（skip 全部分类）** | `py -3.12 -m pytest tests -q` |
| 项目级校验 | **53 通过 / 4 失败 / 0 警告**（4 失败为项目产物问题） | `py -3.12 core/tools/validate.py` |
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
  样例 `tests/fixtures/sample_incomplete_project` 为部分样例，不保证全绿。
- Windows 本机 `py` 默认解释器（3.14/3.13）安装损坏，统一用 `py -3.12`。

## 下一步

```text
P15.2 Model Construction（真实 B0 执行，需 4 道题原始题面）→
P15.3 Formal Consistency → P15.4 Computational Solving →
P15.5 Validation → P15.6 Model→Paper Transmission →
P15.7 Competition Model Construction Benchmark
```

## 风险与待办

- **P15.2 阻塞**：2022_C / 2020_B / 2018_A / 2019_C 四道题缺原始题面+数据附件，需用户提供。
- CUMCM 22 份 rubric 中 13 份 `reference_results` 为空——不凭记忆伪造 GT。
- 完整 CUMCM 题面语料未导入（现有仅题名索引 + 1 份合成示例）。
- `core/tools/` 松散文件现在是唯一实现（子目录已删除），AGENTS.md 命令路径无需变更。