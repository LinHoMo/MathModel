# ADR-0010 — model_families 词表修订 r1（CUMCM 2026 结构对齐）

> 状态：**Accepted** ｜ 日期：2026-09-11 ｜ 相关：`src/modeling_harness/catalog/model_families.yaml`

## 背景

`model_families.yaml` 是受控词表的单一真源，`frozen: true`（K002 于 2026-09-09 冻结），
文件头治理声明规定「任何词表修改须走修订流程」，且「新 family 必须经 Architecture Gate
（定义清晰 / 层级明确 / 跨来源支持 / 可映射真实题 / 与现有不重叠），禁止为覆盖率机械新增」。

`docs/PROJECTS_FEEDBACK_AUDIT.md §4` 自承一处未闭合缺口：「基准的允许结构词表
（几何建模 / 微分方程 / 优化 / 仿真）与方法卡家族词表**无交集**」，导致「方法结构对齐」
指标不可用。

## 动因证据（先度量，后修订）

新增工具 `src/modeling_harness/cli/structure_coverage.py`（只读词表）对三个活跃实例的
`allowed_modeling_structures` 做解析，修订前实测：

| 实例 | 解析率 |
|---|---|
| cumcm2024a | 6/6 |
| cumcm2026a | 3/6 |
| cumcm2026b | 1/7 |
| **合计** | **10/19 = 52.6%** |

`out_of_catalog` 9 项：`mass_transfer`、`moving_boundary`、`effective_property_correlation`、
`computational_geometry`、`convex_polygon_clipping`、`diameter_and_min_enclosing_circle`、
`geometric_dilution_of_precision`、`coverage_path_planning`、`greedy_nearest_neighbor`。

## 决策

按 Architecture Gate 逐条复核后修订（r1）：

| 结构名 | 归位 | Gate 复核 |
|---|---|---|
| `mass_transfer` | `numerical_pde.mechanism` | 定义清晰（第二守恒律）；与 `diffusion` 并列不重叠 |
| `moving_boundary` | `numerical_pde.mechanism` | 定义清晰（自由边界/Stefan）；现有 mechanism 中无 |
| `effective_property_correlation` | `numerical_pde.methods` | 属变物性建模技法，非独立结构 |
| `computational_geometry` | **新增 family** | 平面几何运算（裁剪/凸包/包围圆）；与 `kinematic_geometry`（轨迹/运动）不重叠 |
| `convex_polygon_clipping` / `diameter_and_min_enclosing_circle` | 该 family 的 `methods` | 具体算法 |
| `geometric_dilution_of_precision` | 该 family 的 `mechanism` | 定位精度几何衰减，属该族机理 |
| `coverage_path_planning` | **新增 family** | 几何域上规划完备覆盖；与 `optimization`（通用目标优化）不重叠 |
| `greedy_nearest_neighbor` | 该 family 的 `methods` | 贪心近邻是覆盖路径的具体方法 |

修订后实测解析率 **19/19 = 100%**（工具同一条命令可复现）。

## 后果

- **能力层**：harness 从此能识别 CUMCM 2026 A/B 用到的全部结构 → 「方法结构对齐」由
  「不可用」变为**可计算**（其数值仍取决于实例是否登记方法卡选型，属另一缺口）。
- **未改变**：族命中判定口径（id/alias/mechanism/method/solver 任一命中）、
  `out_of_catalog` 不自动判错、零第三方运行时依赖。
- **不可逆性**：低。词表为数据文件，单 commit 可 revert。

## 备选方案（未采纳）

| 方案 | 未采纳理由 |
|---|---|
| 不修订，只保留度量 | 度量把缺口变可见，但不闭合「无交集」本身 |
| 新增 9 个 family 拉满覆盖率 | 违反「禁止为覆盖率机械新增」；会破坏层级语义 |
| 改由 `out_of_catalog` 兜底不处理 | 指标持续不可用，能力缺口被掩盖 |

## 验证

- 单测：`tests/unit/test_structure_coverage.py`（6 用例，含「2026 结构修订后可解析」）
- 复现：`py -3.12 src/modeling_harness/cli/structure_coverage.py` → 19/19
- 门禁：`catalog_check.py --check` OK，`--check-terminology` OK，validate 48/0/0
