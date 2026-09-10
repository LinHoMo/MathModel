# tests — 测试分层说明

> 跑法：`py -3.12 -m pytest tests -q`（当前基线：**595 passed**）。
> 测试环境依赖（与 AGENTS.md §6 一致）：`pytest` / `pyyaml` / `jsonschema` / `ripgrep` / `ruff`。

## 分层（实测）

| 层 | 目录 | 测试文件 | test 函数 | 职责 |
|---|---|---|---|---|
| unit | `tests/unit/` | 35 | 412 | 单模块行为（schema、契约、领域） |
| integration | `tests/integration/` | 23 | 128 | 跨模块协作（runtime 子域联动） |
| e2e | `tests/e2e/` | 1 | 4 | 端到端引擎演练 |
| research | `tests/research/` | 3 | 17 | 研究实验回归 |
| runtime | `tests/runtime/` | 2 | 13 | runtime 契约回归 |
| **合计** | | 64 | 574 | 595 passed（含参数化展开） |

## 夹具 / Fixtures

- `tests/fixtures/projects/`：标准项目夹具。
- `tests/fixtures/scaffolds/`：脚手架快照。
- `tests/fixtures/sample_incomplete_project/`：不完整项目（校验负例）。
- 历史 `sample_paper_project/` 已删除（T-CONF-005，V2 论文链残留，零引用）。

## 铁律

- **不得为通过测试而修改测试语义**（AGENTS.md §5）。
- 依赖缺失以 CI 为准（`.github/workflows/ci.yml`），不以本地残留为准。
- 测试失败必须如实报告根因，禁止静默跳过掩盖失败。
