# V3 Implementation Report — MathModel V2 → V3.1 全量迁移实施报告

> 日期：2026-09-04
> 范围：47 节任务书「MathModel V3 — Full Architecture Migration & Implementation Mission」全部阶段（P0-P5）
> 配套文档：`V3_BASELINE_AUDIT.md`（基线事实）/ `V3.1_ARCHITECTURE.md`（目标架构）/ `V3_MIGRATION_MAP.md`（迁移映射）/ `V3_FINAL_AUDIT.md`（最终审计）

---

## 1. 一句话总结

V2 的 29 agent 线性流水线已完整升级为 V3.1 Cognitive Workflow Runtime：**Artifact Registry（Stable ID）→ Typed Evidence Graph（失效传播）→ Workflow DAG（反馈环/Per-Qi）→ 5 Role → 前置 Critics → Knowledge 层（方法卡/失败记忆/决策日志）→ Writing 倒置投影**；V2 全链路保留为 legacy 模式，542 项测试零强制中断通过。

## 2. 新增代码地图（全部为真实可运行模块）

```
core/
├── runtime/                    # V3 运行时
│   ├── artifacts/              # P0: ids / artifact / lifecycle / registry
│   ├── state/                  # P1: 多维状态（status.json + STATE.md 镜像）
│   ├── graph/                  # P1: evidence_graph（14 关系 + kill/reval/dirty 传播）
│   ├── execution/              # P1: yamlio / dag / composer / engine
│   ├── legacy/                 # P1: convert（29 步 ↔ V3 状态双向；all_results 双向）
│   ├── knowledge/              # P2: cards / retriever（打分规则显式可测试）
│   ├── decisions/              # P2: log（失效决策降权）
│   ├── modeling/               # P3: selection（MethodArena）/ planner（ExperimentPlanner）
│   ├── roles.py                # P3: 5 Role 加载 + validate_dag_roles
│   ├── writing/                # P4: director / projection / narrative_critic / judge_critic
│   └── adapters/               # P5: manifest / cloud_sandbox / runtime_compat 桥接
├── validators/
│   └── evidence/evidence_gate.py   # P3: E1-E8（双向证据闭包）
├── skills/critics/             # P3-P4: model / experiment / narrative / judge 四个 critic skill
├── roles/*.yaml                # P3: 5 角色定义
├── workflows/                  # P1: base + stages×5 + competition profiles
├── knowledge/
│   ├── methods/cards/          # P2: 16 方法卡
│   ├── failures/               # P2: 10 失败记忆
│   └── patterns/               # P2: 6 创新模式
├── schemas/v3/                 # P0-P2: 11 个 v3 schema
├── evaluation/                 # P4-P5: scoring / benchmark 桥接（稳定 import 面）
└── tools/
    ├── knowledge.py            # P2: 知识层 CLI
    └── catalog_check.py        # P4: 双视图三方一致性校验
```

## 3. 核心设计决策（实施中确立）

1. **门禁由脚本判定，不是复选框**——29 个 agent 的 Self-Check 复选框模型可以勾完继续，等于没有门禁；V3 所有判定（gate/evidence-gate/critics）输出结构化 findings，verdict 可被脚本聚合。
2. **证据闭包必须双向遍历**——evidence_chain 只走 in-edge 会漏判：实验 `uses` 出边指向的数据死亡时，下游主张也必须判死（E3 修复教训）。
3. **时序错配 -4 惩罚**——纯时序方法（arima/grey）不得进入非时序问题的推荐列表；-2 惩罚不足时单标签命中 +3 仍存活。
4. **失效决策不删除，降权**——Decision Log 的 invalidated 决策保留 superseded_note 供回溯；双推翻（A 推翻 B、B 又推翻 A）拒绝。
5. **UNKNOWN 优先于瞎判**——JudgeCritic 四态：信息不足（无 claim/无投影/缺证据报告）必须 UNKNOWN，不得输出伪造的 PASS/FAIL。
6. **叙事是投影不是终点**——论文大纲由 ResearchDirector 从 Evidence Graph 蒸馏的 StoryArc 投影生成；死主张不得进入任何章节。
7. **桥接优先于搬移**——evaluation/scoring、benchmark、adapters 用动态加载 + 单实例复用桥接，core/tools CLI 消费面零改动，P5 不制造断链风险。

## 4. 测试与质量账

| 指标 | 值 |
|---|---|
| 测试总数 | 553（542 passed / 10 skipped / 1 pre-existing fail） |
| V2 基线 | 382 passed |
| V3 净增 | +160（unit 146 / regression 10 / manifest 双视图 4） |
| 提交数 | 7（1 docs + P0-P5 各 1） |
| catalog_check | 三方一致（roles/DAG/validators） |
| doctor | 就绪 20 / 警告 0 / 阻塞 0 |
| 回归测试 | R1-R8 全过（脚手架/状态机/门禁/双视图/编排器/校验入口） |

## 5. 使用方式速记

```bash
# V3（默认）
python core/tools/new_project.py demo --competition cumcm --problem <赛题>
python core/tools/orchestrator.py demo            # V3 DAG 波次计划（13 波/15 节点）
python core/tools/knowledge.py recommend --types evaluation,coupling --sample 200

# V2 legacy（保留）
python core/tools/orchestrator.py demo --legacy   # 29 步流水线
python core/tools/state.py demo init && python core/tools/state.py demo status

# 一致性门禁
python core/tools/catalog_check.py --check
python core/tools/doctor.py
```

## 6. 下一步（超出 47 节任务书范围，建议排期）

1. **WaveExecutor 实装**：orchestrator V3 从干跑转实际执行（逐波次调用节点 SKILL.md，产出登记 registry，门禁失败触发 on_fail 反馈环）——引擎/状态/门禁已就绪，纯装配工作。
2. **修复 test_delivery_gates AI 披露用例**（P0 前已知失败）。
3. **metrics.py 历史基线死引用清理**（archives/cumcm2024a）。
4. **legacy 退役评估**：V3 执行器稳定跑通 2-3 个真实赛题后，评估 29 手降级时间表（checkpoint schema / all_results 导出器 / evaluation 桥接转正一并处理）。
