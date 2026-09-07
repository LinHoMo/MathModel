# HARDENING_PROGRAM — System Hardening（P0–P6）

> 启动：2026-09-07 ｜ 状态：**P0 执行中** ｜ 总纲锚点：user 裁决「工程落地 ≈75–80%，进入
> System Hardening；不再大改架构」。
> 主线路径：**Architecture Freeze → Contract Freeze → Runtime Hardening →
> Replay/Recovery/Consistency → Legacy Isolation → Regression Gate → Release Candidate**。
> 终验收九条：旧能力全部保留 ＋ 新能力全部可用 ＋ 新旧边界明确 ＋ 不存在双真源 ＋
> 可以恢复 ＋ 可以重放 ＋ 可以审计 ＋ 可以验证 ＋ 可以长期扩展。

## 1. 架构冻结声明

自本计划批准之日起，以下资产进入**架构冻结**（高于既有「Research Runtime / Guardrails
语义冻结」的治理等级：不接受任何架构革命、新 schema 语义层、新 Agent 家族）：

- `core/` 的五层结构（product / legacy / research 工具 / benchmark 工具 / instance 工具）
- V3 认知工作流运行时（Registry / Evidence Graph / State / Workflow DAG / Roles / Validators）
- 三层治理与 Δscore 判据（`THREE_LAYER_ARCHITECTURE.md`）

本计划是冻结期内唯一允许的工程活动（例外登记见 THREE_LAYER_ARCHITECTURE.md）。

## 2. 九项收口 → 阶段映射

| # | 🟡 项 | 阶段 | 验收 |
|---|---|---|---|
| 1 | Canonical schema | P1 | domain 模块 + CANONICAL_DOMAIN.md（16 个 V2 schema 投影齐） |
| 2 | Long-term compatibility policy | P1 | COMPATIBILITY_POLICY.md |
| 3 | State single source of truth | P2 | STATE_TRUTH.md + `state.py reconcile` 对账报告 |
| 4 | Crash consistency | P2 | `test_crash_consistency.py` 全绿 |
| 5 | Deterministic replay | P3 | `replay.py` 双跑 diff 为空 |
| 6 | Concurrency guarantees | P3 | wave 冲突用例全绿 |
| 7 | Observability | P3 | RunRecord schema + `runs.py` + RUN_PROVENANCE.md |
| 8 | Legacy/V3 physical isolation | P4 | grep 旧路径零命中 + catalog_check 绿 |
| 9 | Regression / non-regression contracts | P5 | 0 failed / 0 未分类 skip + 五轴单命令全绿 |

## 3. 基线（机器实测，此为该数字的唯一出处）

> 解释器：本机 `py` 默认 3.14 / 3.13 安装损坏（Unable to create process），
> 全部命令用 `py -3.12`（Python 3.12.10）执行。其余机器可用 `python`。

| 命令 | 实测输出 | commit |
|---|---|---|
| `py -3.12 -m pytest tests -q` | **758 passed / 11 skipped / 0 failed** | efc22df |
| `py -3.12 core/tools/validate.py` | **55 通过 / 2 失败 / 0 警告** | efc22df |
| `py -3.12 core/tools/catalog_check.py --check` | **OK（三方一致）** | efc22df |

### 3.1 基线注释（双真源问题档案）

- 历史文档出现过四套测试数字：README「228 passed / 16 failed」（V2 时代残留）、
  用户实测「574 passed / 11 skipped」、STATUS「751 passed / 11 skipped」、本基线
  「758 passed / 11 skipped」。**自本基线起，任何状态的数字必须来自本表口径
  （机器命令 + commit hash），禁止人工转述。**
- validate.py 的 2 条失败均为**研究实验误报**：`projects/P13-3D-R3` 实验语料
  （`_scratch_*.md` / pilot_batchA / real_papers）被当作交付论文扫描出禁用词，
  以及库模式无用户 .tex。修复归属 P4（实验目录移出 `projects/` + validate 扫描
  规则修正），P4 后此二项应转绿，validate 回到 57/57。

## 4. 阶段验收注册

- [x] P0 Architecture Freeze —— baseline 固化 + 治理登记 + 定位文档（本文件 + README/AGENTS/STATUS/METRICS）
- [x] P1 Contract Freeze
- [x] P2 State Truth + Crash Consistency
- [x] P3 Deterministic Replay / Concurrency / Observability
- [x] P4 Legacy Isolation
- [x] P5 Regression Gate
- [ ] P6 Release Candidate

## 5. RC 后方向备忘（不属本计划）

Provider 插拔工程化（Executor 可插拔：GPT/Claude/DeepSeek/MathModelAgent/MMA/Human）、
Runtime / Provider / Regression / Failure-Injection / Recovery / Cross-domain 基准实验线。
历史路径迁移映射（P4 已完成）：`projects/bench-*|P13-3D* → research/<同名>`；
实验专属脚本 → `research/P13-3D/scripts/`；四手 → `core/legacy/hands/`。
恢复指令：`research/P13-3D/RESUME_R3G_PROMPT.md`（路径已同步更新）。