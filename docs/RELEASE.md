# Release Process / 发布流程

> 本文件定义本仓库的版本发布规则。状态真源：`docs/STATUS.md`（机器实测数字）；
> 变更日志：`CHANGELOG.md`；本文件仅约定**流程**，不记账。

## 1. 版本号规则 / Versioning

- 版本号 = git tag（当前：`v3.2.2`），语义化 `MAJOR.MINOR.PATCH`。
- `pyproject.toml` 的 `version` 字段必须与最新 tag 一致（当前 3.2.2）；不一致视为待修事实错误。
- 本仓库为个人研究仓库，不做 PyPI 发布；版本号仅用于 release 对齐与回滚锚点。
- 内部文档协议（如 AGENTS.md v1.0）使用独立版本，不占软件版本号。

## 2. Tag 规则 / Tagging

- 发布必须使用 **annotated tag**：`git tag -a vX.Y.Z -m "<版本主题>"`。
- tag 必须指向四件套全绿、且已推送的 commit（禁止对未验证 commit 打 tag）。
- 推送 tag：`git push origin vX.Y.Z`。
- 示例（v3.2.2 实践）：
  `git tag -a v3.2.2 -m "v3.2.2 V2 paper-chain & legacy debt complete removal"`

## 3. Release Notes 规则 / Release Notes

- release notes 从 `CHANGELOG.md` 对应版本条目（`## vX.Y.Z` 到 `## vX.Y.Z-1` 区间）提取，不另行编写。
- 发布命令（gh 已认证）：
  `gh release create vX.Y.Z --title "vX.Y.Z" --notes-file <(sed -n '/## vX.Y.Z/,/## vX.Y.Z-1/p' CHANGELOG.md)`
- 未认证时：只推 tag，手动创建 Release 并粘贴 CHANGELOG 条目文本。

## 4. CI 通过要求 / CI Gate

- 发布前置（缺一不可）：
  1. 本地四件套全绿：`validate.py`（45/0/0）+ `catalog_check.py --check` + `--check-terminology` + `pytest tests -q`
  2. 推送后 GitHub Actions CI 全绿（本地通过 ≠ CI 通过，见 AGENTS.md §7）
- CI 未全绿禁止打 tag / 发布；tag 发布后若 CI 失败，先修后补发（不删 tag 历史）。
- 每次 release 需在 `TASKS.md` 记录 commit 锚点。
