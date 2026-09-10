# RUN_PROVENANCE —— 运行溯源与确定性重放（System Hardening P3）

> 建立：2026-09-07 ｜ 代码：`core/runtime/state/runs.py`（记录器）、
> `core/runtime/execution/replay.py`（重放引擎）
> CLI：`python core/tools/replay.py <项目> [verify|list|diff <A> <B>]`
> schema：`core/schemas/v3/run/run_record.schema.json`

## 1. 回答什么问题

科研 Harness 与普通 Agent Framework 的根本区别之一：不仅能运行，还能回答

> **为什么这个 Artifact 是这样产生的？为什么这一次比上一次差？**

每条 RunRecord 提供全链溯源（Run #N → Question → Workflow/Skill/Tool 版本 →
Model/Executor → Input → 产物哈希 → 引擎统计），`replay verify` 用现磁盘状态
重算全部确定性口径，任何漂移逐字段归因。

## 2. RunRecord 字段与口径

| 字段 | 口径 | 归因含义 |
|---|---|---|
| run_id | sha1(project|questions|workflow_version|input_hash)[:12]，幂等派生 | 同配置同输入重跑 = 同一 run |
| parent_run_id | 上一次 run 的 run_id（rerun/resume 链） | — |
| workflow_version / prompt_hash | roles/workflows YAML 组合哈希 | 工作流/角色指令变了 |
| skill_version | core/skills 组合哈希 | 技能指令包变了 |
| tool_version | `catalog-v<ver>@<git头9位>` | 工具链版本 |
| input_hash | inputs/ 组合哈希（空输入 = `<empty-inputs>` 标记哈希） | 题目输入变了 |
| artifact_hash / evidence_hash / decision_log_hash | checkpoint 后落盘文件哈希 | 产物/证据/决策变了 |
| model_provider / model_version / token_cost | 外部 executor 注入（`RuntimeSession(run_meta=...)`）；runtime 零 LLM 时为 null | 执行器/成本 |
| latency / engine | 起止时间、completed/retries/failures | 性能与失败统计 |
| decision | 本轮关键决策摘要（run_meta） | 决策层面差异 |

**诚实性规则**：runtime 本身零 LLM 调用，model_*/token_cost 由外部 executor
填写，没有就记 null——不臆造。

## 3. 确定性重放（verify）

`replay.py verify` 只依赖磁盘与配置，重算：input/workflow/skill/tool 哈希 +
产物三哈希 + `validate.py` 状态对账。判定：

```text
OK   = 全部确定性字段与记录一致 且 状态对账一致
FAIL = 列出每个漂移字段（记录值 vs 当前值 + 归因提示）
```

边界约定：LLM 生成内容本身是**对系统的输入**（其哈希进 payload/artifact），
系统内可保证的是「同输入同配置 → 同确定性口径」；内容变化会被产物哈希
如实捕捉并归因到 artifact/evidence 层。

## 4. 差异归因（diff）

`replay.py diff <A> <B>` 逐字段对比两次 run，附归因：

- `input_hash` → 题目输入变化
- `workflow_version`/`prompt_hash` → 工作流/角色指令变化
- `skill_version` → 技能包变化
- `model_version`/`model_provider` → 换执行器/换模型
- `artifact_hash`/`evidence_hash` → 研究内容本身不同

典型用法：`A/B 对照实验后 diff` 一眼看出「这次变差是因为换了模型、改了指令、
还是题目本身不同」。

## 5. 生命周期与治理

- 记录写入是 **best-effort**（失败打印 stderr 警告，绝不阻断研究主流程）。
- 落盘 `state/runs/<run_id>.json` 原子写；同 run_id 重跑覆盖同文件（幂等）。
- RunRecord 属运行记录层（Canonical Domain 的 Run 实体，P1 预注册），
  不是 artifact、不进 Evidence Graph。
- 持久性承诺见 COMPATIBILITY_POLICY：record 只 additive 加字段，不删旧字段。

## 6. 并发语义（Wave 并行契约，补 STATE_TRUTH.md）

- 波次内节点并行度 ≤ max_workers；跨波次拓扑序保证（wave 划分静态确定）。
- per-question 隔离：`experiment_Qi` 等 per-question 节点按 Question 展开，
  不同 Question 的产物互不写入（测试：双问并行 + reconcile 全绿）。
- 同一 Artifact 的写冲突裁决：Registry 稳定 ID 终身不复用 + 终态不可变
  （RUNTIME_CONTRACTS），并发登记同型 artifact 只会得到不同 ID，无竞态覆盖。
- checkpoint / 落盘为会话级串行（run() 末尾统一 checkpoint），不存在并发写
  同一状态文件。
- 验收用例：`tests/unit/test_run_provenance.py::TestParallelIsolation`。