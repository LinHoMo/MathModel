# catalog — 元数据双视图真源

> 根目录 `catalog.yaml` 是 v5 双视图真源（roles / nodes / validators 三方对齐），
> `catalog/` 目录存放各视图与衍生元数据。一致性由 `src/modeling_harness/cli/catalog_check.py` 强制。

## 文件说明

| 文件 | 用途 |
|---|---|
| 根 `catalog.yaml` | **双视图真源**：v3.roles ↔ src/modeling_harness/roles/*.yaml 文件对齐；catalog_check 的读取对象 |
| `catalog/v3.yaml` | v3 视图（与 catalog.yaml 双视图对照） |
| `catalog/model_families.yaml` | 模型族元数据（测试与检索消费） |
| `catalog/protocol_tools.yaml` | 协议工具清单（validate 描述为 45 项校验，见 STATUS.md 实测） |
| `catalog/external_skills.yaml` | 外部技能登记 |

## 修改协议

1. 修改 catalog 元数据后**必须**运行：
   ```powershell
   py -3.12 src/modeling_harness/cli/catalog_check.py --check
   py -3.12 src/modeling_harness/cli/catalog_check.py --check-terminology
   ```
2. `--check` 失败 = 双视图不一致（阻塞交付）；`--check-terminology` 失败 = 旧术语残留（阻塞交付）。
3. 数字口径以 `docs/STATUS.md` 机器实测为准，禁止在 catalog 中回填未实测数字。
