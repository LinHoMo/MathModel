# Long-term Compatibility Policy（长期兼容政策）

> 建立：2026-09-07（System Hardening P1 / Contract Freeze）
> 约束对象：schema、workflow、artifact、evidence、命令入口（CLI）、legacy 导出。

## 1. 承诺

按优先级排序（前一条优先于后一条）：

1. **旧 Artifact 永远可读**：任何历史版本的 artifact / evidence / status.json 必须能
   被当前版本打开与校验；无法打开 = 一级回归（semantic non-regression，见
   REGRESSION_CONTRACT.md）。
2. **旧项目可以迁移**：`core/runtime/legacy/convert.py` 迁移路径保持可用；至少保留
   一个主版本周期的迁移工具。
3. **CLI 入口不消失**：`core/tools/` 根目录的一级命令（state/gate/validate/orchestrator/
   catalog_check/benchmark/replay 等）是公共接口，改名必须保留转发 shim。
4. **V2 兼容层只读**：`core/legacy/hands/` 不再新增 agent / 语义；仅修 bug。

## 2. Schema 版本化规则

- **新增字段**：一律 additive（可选字段 + 默认值）；禁止删除必填字段或改枚举含义。
- **schema_version 递增时机**：additive 变更 minor 递增；破坏性变更 = 主版本，须
  经 `THREE_LAYER_ARCHITECTURE.md` 例外流程 + 迁移脚本同时提交。
- **v3 是 canonical 视图、V2 schema 是 legacy 视图**（CANONICAL_DOMAIN.md）：
  新语义只允许进 v3；V2 schema 冻结。
- **legacy 导出器保留窗口**：任一 V2 导出器（如 all_results.json 导出、
  `convert.py import/export`）计划下线时，必须先声明 deprecated、保留至少一个
  版本周期、再删除。先例：`V3_MIGRATION_MAP.md` §6「保留导出器一个版本周期」。

## 3. Deprecation / 下线流程

```text
宣告 deprecated（文档 + 输出 warning，仍工作）
   → 保留一个版本周期（此期间 regression 测试必须覆盖）
   → 删除 + 迁移说明写入 docs/decisions/
```

## 4. 测试豁免规则（xfail / skip 的注册规范）

- `xfail` 必须带 `reason` 且指向具体契约条款或 issue；禁止「环境问题」类空话。
- `skip` 必须注册 marker 并给出分类：`requires_runtime`（依赖外部 MMBench /
  Syslab / LaTeX 工具链）、`integration`、`e2e`；分类登记在 `pyproject.toml`。
- 任何断言「这个以前就坏了」的豁免都不成立——历史上失败的用例按根因修复
  （Hardening P3 / P5 强制执行，零失败基线）。

## 5. 运行时行为兼容

- 生命周期语义不变量（terminal immutability、superseded/invalidated 区分、
  audit retention、crash/resume/rerun/invalidate 语义）以
  `core/runtime/contracts.py` + `RUNTIME_CONTRACTS.md` 为唯一真源；改动即主版本级
  变更，禁止局部「顺手加固」。
- 随机性与可复现性：random_seed 42 + ≥5 次多种子运行的口径不得放宽（铁律 P1/P6）。

## 6. 验收

Hardening P5 的 five-axis non-regression 契约（functional / semantic / quality /
data / operational）是本政策机器可判的执行者；任何兼容性声明必须能在
`pytest tests/regression -q` 中兑现。