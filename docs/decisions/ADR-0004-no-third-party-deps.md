# ADR-0004: Zero Runtime Dependencies / 运行时零依赖

- Status / 状态：Accepted
- Date / 日期：2026-09-10
- Context / 上下文：core 保持零第三方运行时依赖是定位红利（可信 Harness 可审计、可移植）。阶段二 CI 暴露：**测试环境**实际依赖 `pyyaml`、`jsonschema`、`ripgrep`（本地长期残留掩盖了这一点），必须显式区分「运行时零依赖」与「测试环境依赖」。
- Decision / 决策：
  - core 运行时零第三方依赖：core 的 import 只能来自标准库与 core 自身；禁止新增任何第三方运行时依赖。
  - 测试环境依赖（CI 已验证，见 `.github/workflows/ci.yml`）：`pytest`、`pyyaml`、`jsonschema`、`ripgrep`、`ruff`。
  - 判断依赖以 CI 为准，不以本地环境为准；新增测试依赖必须同步 CI 并在汇报中单列。
- Consequences / 后果：core 保持可移植可审计；测试环境的依赖清单显式化，避免「本地能跑 CI 不能跑」；违反零依赖的 PR/提交将被 AGENTS.md §5 门禁拦截。
- Evidence / 证据：CI 运行记录（run 34450689331 失败于 `import yaml`、run 34451008924 失败于 `import jsonschema` / 缺 `rg`、run 34451162232 全绿）；`.github/workflows/ci.yml`；根 `AGENTS.md` §6（环境与依赖）。
