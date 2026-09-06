# 项目状态

> 更新：2026-09-06（P12 收口 + 方向修正落地）。架构治理见
> `docs/architecture/THREE_LAYER_ARCHITECTURE.md`。

## 当前定位

**数模 Agent**：给一道赛题 → Agent 理解问题 → 找方法 → 建模 → 实验 →
比较 → 验证 → 写出论文。全部资产归位三层：

- **Agent Brain**（29 agent 指令 + 知识层）——研发主战场（P13–P17）；
- **Research Runtime**（`core/runtime/`，P6–P12 产物）——**已冻结**；
- **Guardrails**（validators + gates + 评分链）——**已冻结**（仅修 bug）。

新工作准入走三问门禁（Q1 能力 / Q2 可靠性 / Q3 仅内部语义 → 仅 Q3 不做）；
能力进步以基线 Δscore 度量（八项指标，见 `bench e2e`），不再以
"新增契约/测试数量"度量。

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
| P11 | Scientific Writing（Expression Contract / ParagraphPlan / 红队 W1–W15） | ✅ | `bfd1e84`… |
| P12 | Cross-Question：P12-0 审计 → P12-1 依赖 → P12-2 关系 → **P12-3-lite 上下文 → 全阶段冻结** | ✅ 收口 | `856d369`/`92b9efa`/`0302228` |

P12 取消项：P12-7/8/9/10（见 `CROSS_QUESTION_SYNTHESIS_CONTRACT.md` 不做清单）。

## 当前数字

- 测试：**751 passed / 11 skipped**（`python -m pytest tests -q`）；
- `core/tools/validate.py`：**57/57 通过**；
- 测试数量自此仅用于守住冻结层不回归，**不作为进度度量**。

## 下一步（Capability Roadmap，见 `docs/architecture/CAPABILITY_ROADMAP_P13_P17.md`）

1. **基线已建立（2026-09-06）**：MMBench 2000_C 首跑，8 项指标 7 项可算、
   可得均值 63.0 → 见 `BASELINE_REPORT.md`；此后所有能力改动以 Δscore 验收；
2. P13 数学推理底座：按基线 backlog 顺序攻关（问题语义接入 → 方法卡扩充
   → 论文生成 → 创新模式消费），exit criteria = ≥5 题基线且至少一项指标
   +10 个百分点；
3. P14 模型构建 → P15 实验智能 → P16 竞赛策略 → P17 全量测评。

## 风险与待办

- CUMCM 22 份 rubric 中 13 份 `reference_results` 为空——**不凭记忆伪造
  GT**；诚实补齐方式是每实际解出一题回填一份（见 BASELINE_REPORT §6）；
- 完整 CUMCM 题面语料未导入（现有仅题名索引 + 1 份合成示例）；
- 基线暴露的三个 backlog：问题语义未接入选型、方法卡缺种群动力学家族、
  创新模式卡未被管线消费（详见 BASELINE_REPORT §4/§5）；
- `docs/IMPROVEMENT_PLAN.md` 为 V2 时代文档，仅存档不再维护。
