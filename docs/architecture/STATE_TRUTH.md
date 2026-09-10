# STATE_TRUTH —— 状态单一真源决策表（System Hardening P2）
> Version: v1.0 | Status: Active | Updated: 2026-09-07

> 建立：2026-09-07 ｜ 代码真源：`src/modeling_harness/runtime/state/reconcile.py`（对账器）
> CLI：`python src/modeling_harness/cli/validate.py <项目>`（registry/graph/state 对账）
> 原则：回答「系统当前到底是什么状态」**只能有一个答案**。

## 1. 真源分层（谁是真源、谁是投影）

```text
Event Log（节点执行事件，NodeResult）
        │ 派生
        ▼
Content Truth（研究内容真源，各文件原子写: mkstemp + os.replace）
  ├── state/registry.json          Artifact 生命周期真源
  ├── state/evidence_graph.json    关系/失效传播真源
  └── state/decision_log.json      决策记录真源
        │ refresh_from（ProjectState 唯一派生入口）
        ▼
Process Projection（流程状态投影，禁止反向手写）
  └── state/status.json            多维状态：questions/models/evidence/…
        │
Resume Truth（断点续跑真源，原子写）
  └── state/engine_progress.json   引擎 completed/blocked/retries
```

## 2. 决策表：谁写 / 谁读 / 谁重建 / 冲突裁决

| 文件 | 类型 | 写入者 | 读取者 | 重建方式 | 冲突裁决 |
|---|---|---|---|---|---|
| `registry.json` | 内容真源 | 处理器 / handlers（经 ArtifactRegistry） | graph、state 派生、validators、论文投影 | 不可从投影重建；丢失 = 产物丢失（payload 文件仍在时可 re-create） | 以 registry 为准 |
| `evidence_graph.json` | 内容真源 | `_register_evidence` / `invalidate` / `declare_*` | state 派生（coverage）、失效传播、claim 检查 | 不可从投影重建 | 以 graph 为准 |
| `decision_log.json` | 内容真源 | 决策记录 API | knowledge 运营、评审 | 不可从投影重建 | 以 log 为准 |
| `status.json` | 流程投影 | **仅** `ProjectState.refresh_from` 派生后 save | 人类/agent 读状态、调度、reconcile | **永远可重建**：`refresh_from(registry, graph)` 重新派生 | 投影跟随内容；不一致时重建投影，禁止手改投影 |
| `engine_progress.json` | 续跑真源 | `WorkflowEngine.save_progress`（原子写） | `resume()` 断点续跑 | 丢失 = 重跑 DAG（功能不坏，成本高） | 与 workflow 投影矛盾时以 progress 为准（reconcile 报差异） |
| `work/state.json`（V2） | legacy 状态 | `validate.py` 对账 | legacy 29 步协议 | 由产物反推（`validate.py`） | legacy 模式无多维投影，`state.py sync` 单文件自检 |
| 运行时内存 | 会话态 | RuntimeSession | 执行中 | 永远以磁盘为准 | 磁盘是跨进程真源；每次操作后 checkpoint |

## 3. 现状审计结论（P2 摸底）

- `ProjectState.save` / `ArtifactRegistry.save` / `EvidenceGraph.save` 均为
  原子写（mkstemp + os.replace）；P2 补齐了 `engine.save_progress` 的原子写，
  至此**四个持久化文件全部原子落盘**，不存在半截文件。
- `checkpoint()` 顺序 = registry → graph → decisions → refresh_from → status：
  中途崩溃的窗口期会造成「内容已新、投影未新」——这正是 `reconcile` 检测的
  目标场景，恢复口径 = `resume()`/`checkpoint()` 重新派生投影（见
  `tests/unit/test_crash_consistency.py` 故障注入证明）。
- 历史遗留：`legacy` 记录四套旧状态文件（checkpoint.json / audit_log.json /
  audit_chain.json / final_audit_log.json）只读保留、不算真源（validate.py 已接管，
  其哈希只用于追溯）。

## 4. 对账器契约（reconcile.py）

- 只读：绝不修改任何文件，绝不静默；不一致时输出 problems + 字段级 diff + 恢复建议。
- 比较范围：questions 集合 / models.candidates/selected / per-question 挂载
  （models/experiments/claims）/ evidence 聚合计数（graph_version、
  claims_supported、claims_total）/ engine_progress 存在性 / D1 依赖双写。
- **不比较**：workflow / run / review / narrative / paper / question 状态机字段
  ——这些由会话/引擎所有，不为内容派生，多了会造成假阳性。
- 模式：`v3`（对账）/ `legacy`（单文件，无投影可对）/ `empty`。
- 退出码：OK=0，FAIL=1（可接入 CI 与 Regression Gate）。

## 5. 双真源问题档案（状态数字层面）

文档口径（README/STATUS/METRICS）曾并存 228/16、574/11、751/11、758/11 四套
测试数字。自 Hardening P0 起：数字只来自三条机器命令（pytest / validate /
catalog_check）+ commit hash（见 HARDENING_PROGRAM.md §3 基线表）；本文件约束
的是**项目目录内**的运行时状态真源，两者共同构成「无双真源」验收（RC 第 4 条）。

## 6. 并发语义（Wave 并行契约，Hardening P3 补录）

- 波次内并行度 ≤ max_workers；跨波次严格拓扑序（波次划分由 WorkflowDAG 静态确定）。
- per-question 隔离：`experiment_Qi` 等节点按 Question 展开，不同 Question 产物
  互不写入；验收用例 `tests/unit/test_run_provenance.py::TestParallelIsolation`
  （双问并行 → 产物各归其问 → reconcile 全绿）。
- 同一 Artifact 写冲突裁决：Registry 稳定 ID 终身不复用（artifact_id 唯一分配）
  + 终态不可变（RUNTIME_CONTRACTS），并发登记同型产物只可能得到不同 ID，
  无覆盖竞态。
- 落盘串行化：checkpoint / save_progress 由会话主线程在 run() 末尾统一执行，
  不存在并发写同一状态文件。