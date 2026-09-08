# MathModel 项目状态快照

> 更新：2026-09-08（仓库清理 + core/tools 统一完成）
> **本文件是会话交接的存档版本，当前无活跃交接任务。**

## 当前状态

- **版本**：v3.1.1（`9199f03`）
- **测试**：774 passed / 11 skipped / 0 failed
- **catalog_check**：OK（v3 双视图一致）
- **validate.py**：53 通过 / 4 失败（项目产物问题，非代码）

## 已完成的工作

1. v3.1.0 发布（RC 收口，`b004cd1`）
2. P15.0 Benchmark Freeze（`8751c45`，tag `p15.0-benchmark-freeze`）
3. P15.1 B0 Alignment Baseline（`af1bbd5`，tag `p15.1-b0-baseline`）
4. 仓库清理：技能迁移 + 归档 + V2 残余移除 + P0 修复（`691bdd0`…`b6540e3`）
5. core/tools 统一：子目录内联 + 空壳删除 + AI 配置 V2→V3（`7f29443`…`9199f03`）

## 下一步

- **P15.2 Model Construction**：需要用户提供 4 道题原始题面（2022_C / 2020_B / 2018_A / 2019_C）
- 其余 P15.3–P15.7 按 PRE_REGISTRATION.md 推进

## 关键文件

| 文件 | 作用 |
|------|------|
| `AGENTS.md` | 唯一真源入口 |
| `docs/STATUS.md` | 状态数字唯一出处 |
| `CHANGELOG.md` | 版本变更记录 |
| `research/P15/PRE_REGISTRATION.md` | P15 预注册协议 |
| `research/P15/model_representation/MODEL_IR_SPEC.md` | Model IR 设计规范 |
