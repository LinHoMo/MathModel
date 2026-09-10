# P15-K005 预注册实验：Constructor × Runtime 2×2 析因 benchmark（P3-1）

> 状态：DRAFT v1.0 ｜ 日期：2026-09-10 ｜ 继承：P2-2（Constructor Adapter）、
> P2-1（L6 判定）、P1-3（Constructor Protocol）
> 关联：`ROADMAP.md → P3-1`；目录 `research/P15/benchmark/constructor_independent/`

## 1. 研究问题（RQ）

LinHoMo Runtime 对**任意外部 Constructor** 的建模终态质量贡献多少？
（Constructor-independent 增益，分离"Agent 本身能力"与"Runtime 带来的增益"。）

## 2. 设计（2×2 析因）

| 因子 | 水平 |
|---|---|
| Constructor（C） | C1 = 裸 Doubao（通用 Agent）｜ C2 = MathModelAgent |
| Runtime（R） | R0 = 裸（Constructor 自产自证）｜ R1 = Constructor + LinHoMo Runtime（执行/验证/修订闭环） |

- **单元**：6 题 × 5 rep = 30 单元/臂；总 runs = 30 × 4 臂 = **120**
- **块配对**：同一 (题, rep) 的 4 臂由**同一批题面输入**驱动（配对控制题面难度）
- **执行**：R1 臂走 Runtime 主 DAG（P0-1 注入通道 → L6 判定 → revision 闭环）；
  R0 臂 = Constructor 独立产出终态（不经过 Runtime 验证/修订）
- **主终点**：L6 终态（`validate_against_gt`，`problem_cards/*/gt.json#l6_assertions` v1.0）
- **次终点**：执行成功率、首次失败率、修正轮数、M1→M2 谱系、replay 成功

## 3. 假设（预注册）

- H1（Runtime 主效应）：R1 − R0 的 L6 配对差分 > 0（CI 下界 > 0）
- H2（Constructor 主效应）：C2 − C1 的 L6 差分（描述性报告，不判显著性——
  样本 2 Constructor 非随机抽样）
- H3（交互）：Runtime 增益对不同 Constructor 方向一致（交互项报告，不判显著）

## 4. 统计

- 配对差分（同 (题, rep) 块内 R1−R0）→ bootstrap 95% CI（10000 次）
- 析因分解：主效应/交互项点估计（R 型：`Δ = (R1−R0) 全样本`；报告不夸大）
- **negative result 如实报告**（K001/K002 同纪律）

## 5. 预注册 Gate

- G1 映射：120 runs → (题, rep, 臂, Constructor) 双射可审计
- G2 词表：Constructor 产物契约校验（MODEL_IR 必填字段，P1-4 schema）
- G3 执行真实性：R1 臂全部 subprocess（execution_id + 哈希）
- G4 L6 判定一致性：判定函数固定（validate_against_gt v1.0）
- G5 功效：n=30 配对 × bootstrap CI 如实报告

## 6. 数据收集状态（如实标注）

- **runner 框架**：`research/P15/benchmark/constructor_independent/`（本目录）
  ——消费 Constructor 产物目录（P2-2 adapter 契约）→ Runtime 主 DAG → L6。
- **正式 runs 数据**：**BLOCKED / 待外部 Constructor 会话执行**——裸 Doubao 与
  MathModelAgent 的 120 个真实建模产物需外部 Constructor 逐题生成；
  **禁止伪造/回填 runs**（The Agent Is Not The State）。数据就绪后按本协议
  执行并出报告（K005_REPORT.md）。

## 7. 范围与限制

- 6 题 = CUMCM 冻结题（2018_A/B、2019_C、2020_B、2022_C、2024_A）
- L6 判定为数学必然/题面客观边界断言（非答案数值）：测量"可机械判定的
  终态正确性"，不测量盲评论文质量（后者属 K001/K002 层）
