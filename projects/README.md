# projects/ — 用户运行实例

本目录只放**用户运行实例**：由 `python core/tools/new_project.py <项目名>` 创建，
是引擎在校验下跑出来的真实交付项目。

- 研究实验一律进 `research/`（带实验专属脚本，生命周期独立）。
- 测试 fixture 统一放在 `tests/fixtures/`。
- 库模式（本目录为空）下 `validate.py` 的论文交付类检查自动跳过。

五层分工见 README「目录结构」与 `docs/architecture/HARDENING_PROGRAM.md`。