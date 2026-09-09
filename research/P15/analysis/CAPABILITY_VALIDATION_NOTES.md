# Capability Validation 记录（P1 改造后能力度量现状）

> 日期：2026-09-09 ｜ 关联：P1 三里程碑、治理 v1.2、P15-EXPERIMENT-CONTRACT-v2
> 状态：**环境受限如实记录 + P1 产物可度量性已打通**；Δscore 八项指标待 MMBENCH 语料就位后补。

## 1. 背景与目标

用户指令：P1 改造完成后做 Capability Validation，以 Δscore（八项能力指标，`bench e2e`）
度量"P1 改造改变了哪个可测量的 Model Construction 行为"（infra 不冒充 capability）。

## 2. 执行路径与限制

| 步骤 | 结果 |
|---|---|
| MMBENCH 语料（八项指标评分链输入） | **仓库外**（`MMBENCH_ROOT` 环境变量未设置，本机无 mmbench 语料）；`bench_mmbench.py` 死路径已修复（环境变量优先 + 仓库内约定目录 fallback） |
| 八项指标执行前提 | 需 benchmark 上下文：gt（问题/结构映射）+ allowed_modeling_structures + 外部评分——P1 demo 项目（vs001/m3/m4_run）为演示产物，无 gt 文件 → 8 项中 6 项 UNAVAILABLE（如实，不伪造） |
| **P1 产物可度量性（本次打通）** | e2e_metrics 的 model structural check 原读旧扁平字段（objective 单数）且只收集 type=model → 对 P1 的 MODEL_IR（type=model_ir、objectives 复数）判 FAIL/漏检。已修复：收集 model+model_ir、字段以 MODEL_IR 契约为准（复数）、旧式指针 artifact 标记 legacy_pointer 不误判 |

## 3. P1 产物度量结果（vs001 demo，可复现）

```
structural_pass: True          # MIR001/MIR002（MODEL_IR 契约）objectives/constraints/variables 全 True
models_checked: 2              # MIR001, MIR002
legacy_pointer_skipped: 1      # M001（旧式指针，N/A 不判 FAIL）
```

命令：`py -3.12 -c "import sys; sys.path.insert(0,'core/tools'); import e2e_metrics as em; print(em.compute_e2e_metrics('research/P15/vs001_run/project')['metrics']['model_correctness'])"`

## 4. P1 改造可用的能力证据（代理指标，非八项 Δscore）

| 证据 | 数值 | 位置 |
|---|---|---|
| VS-001 闭环验收 | **7/7**（M1 FAIL→M2 PASS + Replay 零偏差） | `P1_VS001_REPORT.md` |
| M3/M4 固化测试 | **14 passed**（e2e 级） | `tests/integration/test_p1_m3_competition.py` + `test_p1_m4_guided_vs_unguided.py` |
| MODEL_IR 契约可消费性 | structural PASS（本次修复） | 本文件 §3 |
| 全仓回归 | **910 passed / 4 skipped**、catalog OK、validate 57/0 | `docs/STATUS.md` |

## 5. 结论与后续

- **结论**：P1 改造的能力证据目前以"闭环成功 + 契约可消费 + 测试固化"体现；
  八项 Δscore 需 MMBENCH 语料（外部资源）就位后执行 `bench e2e metrics` 补齐。
- **不伪造**：6/8 项 UNAVAILABLE 如实记录（demo 项目无 gt/benchmark 上下文），
  不虚报能力值。
- **后续**：MMBENCH_ROOT 就位 → 对 P1 项目跑八项指标 → 与 B0-R2 基线对比出 Δscore。
