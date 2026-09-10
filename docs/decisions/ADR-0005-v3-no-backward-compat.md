# ADR-0005: V3 Has No Backward Compatibility with V2 / V3 不向后兼容 V2

- Status / 状态：Accepted
- Date / 日期：2026-09-10
- Context / 上下文：V2 时代遗留的论文链（LaTeX 模板、paper 工具、writer 角色、paper_section 类型）、四手残留、旧研究目录与 V3「问题输入 → MODEL_IR + 模型描述文档」定位冲突，且长期无人维护、增加理解成本。
- Decision / 决策：V3 **不向后兼容 V2**——不包含论文生成（LaTeX/PDF）；v3.2.2 彻底清除 V2 论文链与历史债务（论文链工具 9 个、validate_project.py、LaTeX 模板 27、竞赛 profile 9、V2 schema 4、syslab 技能 101、旧实例 8、docs 25+6）；`core/schemas/v3/` 为唯一 canonical schema；全仓术语以 `docs/ONTOLOGY_TERMINOLOGY.md` 为准。
- Consequences / 后果：旧 V2 工具/文档不再提供兼容路径；历史实验证据按「迁移 ≠ 删除」原则保留（research/P15 数据完整迁移至独立仓库而非删除）；文档中出现已删除项引用即为事实错误（按 AGENTS.md §9 同类事实修正处理）。
- Evidence / 证据：`docs/STATUS.md` 阶段历史「v3.2.2 V2 残留彻底清除」（595 passed，validate 45/0/0，catalog OK）；`CHANGELOG.md` v3.2.2 条目；根 `AGENTS.md`（定位声明「不向后兼容 V2」）。
