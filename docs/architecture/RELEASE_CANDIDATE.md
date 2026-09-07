# RELEASE_CANDIDATE — System Hardening 九条终验收（P6）

> 建立：2026-09-07 ｜ 判定依据：九条全部有机器/文档证据 → 打 RC tag。
> 总纲：`HARDENING_PROGRAM.md`；执行主线：Architecture Freeze → Contract Freeze
> → Runtime Hardening → Replay/Recovery/Consistency → Legacy Isolation →
> Regression Gate → Release Candidate。

## 九条验收 → 证据映射

| # | 验收 | 证据（机器/文档） | 状态 |
|---|---|---|---|
| 1 | 旧能力全部保留 | functional 轴（V2 R1–R8 全 PASS，`pytest tests/regression -q`）+ legacy 冒烟（`state.py init/status`、`orchestrator --legacy` 干跑） | ✅ |
| 2 | 新能力全部可用 | V3 全链测试（776+ 用例含 runtime/replay/provenance）+ `state.py reconcile` + `replay.py` verify/diff CLI 实测 | ✅ |
| 3 | 新旧边界明确 | `core/legacy/README.md`（兼容层声明）+ `COMPATIBILITY_POLICY.md` + 五层目录树（README/AGENTS） | ✅ |
| 4 | 不存在双真源 | reconcile 对账器 + 状态数字单一口径（STATUS.md 机器表：pytest/validate/catalog 三条命令 + commit） | ✅ |
| 5 | 可以恢复 | `tests/unit/test_crash_consistency.py` 故障注入全绿（崩溃窗口 → resume → reconcile） | ✅ |
| 6 | 可以重放 | `replay.py` 同输入双跑 verify OK、drift 检出/归因实测（run_record 幂等派生） | ✅ |
| 7 | 可以审计 | hash_chain（`verify_chain()`）+ RunProvenance（RUN_PROVENANCE.md + state/runs/*.json） | ✅ |
| 8 | 可以验证 | `validate.py` 57/57 + `catalog_check.py --check` 三方一致 + 五轴回归 15 passed | ✅ |
| 9 | 可以长期扩展 | `COMPATIBILITY_POLICY.md`（additive/窗口/退役流程）+ HARDENING_PROGRAM §5 完成后路线（Executor 插拔为 RC 后方向） | ✅ |

## 终检命令序列（全部机器化，输出即证据）

```powershell
py -3.12 -m pytest tests -q            # 781 passed / 11 skipped / 0 failed（skip 全分类）
py -3.12 core/tools/validate.py        # 57 通过 / 0 失败 / 0 警告
py -3.12 core/tools/catalog_check.py --check   # OK（三方一致）
py -3.12 -m pytest tests/regression -q # 15 passed（五轴 5/5）
py -3.12 core/tools/replay.py <项目>   # verify OK；diff 归因可用
```

## 终检序列实测输出（2026-09-07 终检）

```text
pytest tests -q                        → 781 passed / 11 skipped / 0 failed
core/tools/validate.py                 → 57 通过 / 0 失败 / 0 警告
core/tools/catalog_check.py --check    → OK（三方一致）
pytest tests/regression -q             → 15 passed（五轴 5/5）
legacy 冒烟（state init/status + orchestrator --legacy 干跑）→ 正常
replay.py verify（同输入双跑）          → OK；state.py reconcile → OK
```

## 判定

九条全部有证据 → **Release Candidate**：`v3.1.0-rc1`。RC 后的可插拔化/基准实验线
见 HARDENING_PROGRAM §5，不属本次收口范围。