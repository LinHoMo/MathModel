# src/modeling_harness/schemas/retired — V2 Schema 归档

> 本目录存放 V2 时代的 schema，**仅供历史审计，不做运行时真源**。
> 阶段五（2026-09-10）扫描确认：全仓无任何路径形式引用（`src/modeling_harness/schemas/<name>.schema.json` 非 v3 零命中），故从顶层移入本目录。
> 2026-09-10 目录由 `legacy/` 更名为 `retired/`（消除"legacy"兼容歧义；validate L1.1 已改为校验活跃项目真实输入规约，不再引用本目录）。

## 归档清单（9）

| 文件 | 原归属（见 CANONICAL_DOMAIN.md legacy 投影） |
|---|---|
| `question_spec.schema.json` | Problem/Question 的 legacy 投影 |
| `model_spec.schema.json` / `model_artifact.schema.json` / `model_dag.schema.json` | Model 的 legacy 投影 |
| `decision_log.schema.json` | Decision 的 legacy 视图（V3 已升级为 `v3/decision/`） |
| `reproducibility.schema.json` | Run 的 legacy 视图 |
| `bench_result.schema.json` / `bench_rubric.schema.json` | evaluation 层评估资产 |
| `checkpoint.schema.json` | session checkpoint 的 legacy 视图（P2 后由事件投影取代） |

## 规则

- 只读归档；迁移 ≠ 删除，不清理本目录内容。
- 代码不得新增对 `retired/` 的引用；需要 schema 一律用 `v3/`。
