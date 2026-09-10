# tests/fixtures — 测试夹具

> 本目录存放测试夹具（fixture）。夹具不是交付项目实例，validate 扫描时整个 `tests/` 目录被排除（见 `core/tools/validate.py` `_is_research_scan_path`）。

## 目录说明

| 目录 | 用途 | 状态 |
|---|---|---|
| `projects/` | 标准项目夹具（3 文件） | 使用中 |
| `scaffolds/` | 脚手架快照（4 文件） | 使用中 |
| `sample_incomplete_project/` | 不完整项目负例（20 文件，含 inputs/state/work 等目录骨架，`paper/` 仅 `.gitkeep` 占位） | 使用中 |

## 历史处置

- `sample_paper_project/`：V2 论文链时代的历史样例（含 `paper/main.tex` LaTeX 残留）。
  **T-CONF-005 裁定（2026-09-10）：已删除**——全仓零代码引用（唯一提及为 validate.py 排除注释与历史实验文档），
  V3 不含论文生成，无保留价值。
- 迁移 ≠ 删除原则仍适用于实验数据；fixture 属测试资产，删除按 T-CONF 裁定执行。
