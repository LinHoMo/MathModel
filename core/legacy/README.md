# core/legacy — V2 兼容层（只读）

V2 四手（Modeler / Programmer / Writer / Reviewer，共 29 agent）线性流水线的
**兼容层**：被 V3 认知工作流运行时（5 Role × DAG 15 节点）取代，保留仅供
`state.py` / `gate.py` / `orchestrator.py --legacy` 的 legacy 模式使用。

- 结构真源：`catalog.yaml` hands 节（路径 + UTG 层映射，`catalog_check.py --check`
  三方一致强制）。
- 治理：**冻结只读**——不再新增 agent / 语义，仅修 bug（THREE_LAYER_ARCHITECTURE +
  COMPATIBILITY_POLICY）。
- 迁移蓝图：`docs/architecture/V3_MIGRATION_MAP.md`（本层即其中「未被吸收部分
  原位保留」的落点）。
- 执行协议：根 `AGENTS.md`「V2 兼容模式」章节。

```text
core/legacy/hands/
├── Modeler/     # 建模手（8 agent）
├── Programmer/  # 编程手（6 agent）
├── Writer/      # 撰写手（7 agent）
└── Reviewer/    # 评审手（8 agent）
```