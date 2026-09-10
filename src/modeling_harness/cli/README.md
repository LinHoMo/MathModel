# src/modeling_harness/tools — CLI 工具导航

> 全部零第三方依赖，Windows 下用 `py -3.12` 运行。CI 仅使用带 ⚙ 标记的工具。

## CLI 清单（15）

| 工具 | 一句话说明 | 最小调用 | CI |
|---|---|---|---|
| `validate.py` | 项目级 45 项校验（registry/graph/state 对账） | `py -3.12 src/modeling_harness/cli/validate.py [<项目>]` | ⚙ |
| `catalog_check.py` | catalog 双视图一致性 + 术语 lint | `--check` / `--check-terminology` | ⚙ |
| `benchmark.py` | 引擎演练 / 题库健康 / 国赛复盘基准 | `--competition <赛题>` | |
| `new_project.py` | 新项目脚手架（创建目录并导入赛题） | `<项目名>` | |
| `doctor.py` | 环境预检（本地手动，CI 不跑） | `[--project <项目>]` | |
| `replay.py` | 运行重放校验 / 差异归因（Hardening P3） | `<项目> [verify\|list\|diff <A> <B>]` | |
| `knowledge.py` | Knowledge 检索（方法卡推荐） | `recommend --types <题型>` | |
| `diagram_gen.py` | 科学图表生成（SVG 输出） | `flowchart --nodes A,B --edges A->B -o fig.svg` | |
| `scholar_fetch.py` | 学术文献检索 + BibTeX 导出 | `bibtex <关键词>` | |
| `env_doctor.py` | 环境诊断与修复 | `[--fix] [--json]` | |
| `gen_runtime_manifest.py` | 从 catalog.yaml 生成 runtime manifest（Codex 入口） | `[--check\|--verify]` | |
| `e2e_metrics.py` | 八项能力指标可计算实现（Capability Baseline P13.0） | 库 / 指标调用 | |
| `constructor_loader.py` | 加载外部 Constructor 产物（MODEL_IR + code + validation_specs） | `--constructor-dir <dir>` | |
| `cloud_sandbox.py` | 云执行沙箱（e2b / daytona / local 后端） | `run <file> [--provider <后端>]` | |
| `metrics.py` | 指标计算工具库（accuracy / f1 / rmse 等）+ 度量生成 | `--write` 生成 docs/METRICS.md | |

## 约定

- 修改 catalog 相关工具后必须跑 `catalog_check.py --check` 与 `--check-terminology`。
- 新增工具先在本表登记；CLI 行为变化同步更新 `docs/README.md` 与 `AGENTS.md` 速查（如引用）。
