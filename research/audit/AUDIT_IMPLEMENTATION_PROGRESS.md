# AUDIT IMPLEMENTATION PROGRESS — 2026-09-09

> 证据级实施进度记录（The Agent Is Not The State）。每个 Batch 的状态以
> git commit hash 为准，不依据声称。数字以实跑为准（同仓最新基线）。

## 基线（Batch 0 审计后，commit 2647671）

- SYSTEM VERDICT：MODEL CONSTRUCTION LOOP = **NOT REAL**
- 24 环节：REAL 8 / GAP 11 / FAKE 3 / PARTIAL 1 / STRUCTURAL 1
- P0 发现 12 项、总发现 108 项

## Batch 1 — P0 Scientific Integrity ✅

- `80f9885 fix(audit): batch1 P0 integrity`
- FIX-1.1 ExecutionResult schema 门禁 / 1.2 失败传播 / 1.3 evidence_gate E9 /
  1.4 claim 合成 / 1.5 测试夹具真实化 / 1.6 K003 runner 契约修复
- 附带修复：_exec_workdir 并发、execute_code 幂等死链、engine.is_finished、
  fact_check、e2e_metrics 测试真实产物
- 回归：922 passed / 4 skipped → 后续基线 942/947

## Batch 2 — MODEL_IR + Candidate + Selection ✅

- `6406719 fix(audit): batch2 model IR skeleton + evidence-driven selection (FIX-2.1/2.2)`
- `784a444 fix(audit): merge concurrent FIX-2.3/2.4/2.5 + repair`
- FIX-2.1 骨架 MODEL_IR（18 字段合规，pending_model_spec 显式不可执行）
- FIX-2.2 Selection 无证据 → UNSELECTED（不硬编码 recs[0]）
- FIX-2.3 code_mapping / 2.4 evaluated_by+selected_from 边 / 2.5 problem repr 读题面
- Repair：m4/vs001 implementation_ref 错位修复（全量非确定性根因之一）
- 回归：939 passed / 4 skipped

## Batch 3 — Code → Execution 接通 ✅

- `8f7b188 fix(exec): FIX-3.1 MODEL_IR->Code mapping validation`
- FIX-3.1：MIR.solvers[].implementation_ref 必须命中实际执行 code；映射断裂抛
  HandlerError（不静默）；test_ir_code_mapping 3 例
- FIX-3.2（统一执行管线）：与 3.1 同步落地于 execute_code 单入口

## Batch 4 — ExecutionResult + Evidence 硬化 ✅

- `ff44183 fix(evidence): FIX-4.1 require execution provenance on evidence edges`
- `d91aecd fix(k003): FIX-4.2/4.3/4.4 execution result governance`
- FIX-4.1：supports 边携带 exec_ref（边级 provenance）；E9 边优先→data 回退
  weak→皆无 fail；healthy fixtures 升级
- FIX-4.2：scripts/execution_writer.py（rebuild_all 幂等，registry 驱动）
- FIX-4.3：execution_result 单写路径收敛（runner 不伪造字段）
- FIX-4.4：submission_id 改 uuid4（原 sha256 可逆 → 盲评不盲，修复）
- 回归：947 passed / 4 skipped

## Batch 5 — Validation 真实化 ⏳（进行中）

- `886edb3 fix(validation): FIX-5.1 validator smoke + FIX-5.2 derive checks`
- FIX-5.1：validate.py 真实 import + 冒烟 21 个 validator modules（57→58 项）
- FIX-5.2：derive_checks_from_mir（output_field_exists）；无 spec=无验证诚实语义
- 回归：951 passed / 4 skipped；validate 58/0
- FIX-5.3（L2 mathematical 接线）/ FIX-5.4（jsonschema 接入 registry）：进行中

## Batch 6-10 — 待实施/复核

- Batch 6 Revision Loop（FIX-6.1~6.4）— 未 commit
- Batch 7 E2E 真实案例（FIX-7.1）— 未 commit
- Batch 8 测试可信度（FIX-8.1~8.3）— 未 commit
- Batch 9 实验体系（FIX-9.1~9.4）— 未 commit
- Batch 10 最终架构（FIX-10.1~10.4）— 未 commit（STATUS.md 数字已随各批同步）

## 关键处置记录

- m3/m4 全量非确定性失败根因：m4/vs001 fixtures 的 implementation_ref 曾指向
  registry 内部编号（CODE001/CODE002），全量顺序下编号偏移 → 错位；修复为
  指向外部 model_id（784a444）。
- K003 盲评 ID：uuid4 不可逆（d91aecd FIX-4.4），盲评匿名性恢复。
- 并发注意：本仓库存在并行实施进程（commit 间隔 8-24 分钟），主代理复核
  每个 commit 并记录于此；工作区修改避免与并行进程同文件重叠。
