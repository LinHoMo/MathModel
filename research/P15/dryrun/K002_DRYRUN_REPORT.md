# P0-E8：K002 Dry-Run — G4（Execution validity）预检报告

- 日期：2026-09-09
- 状态：**完成**（判定语义 5/5 符合，执行级终点可测量）
- 关联：P15-K002-DRAFT v0.5 §7.5 Measurement Gate G4；THREE_LAYER_ARCHITECTURE v3 L2 Fidelity

## 1. 目的

K002 冻结前的 G4 预检：确认「执行级终点」在**真实 MODEL_IR** 上可测量、可区分、
防作弊。不跑 K002 正式实验，只用 1 道真实题（2019_C）走完
`run_code_pipeline`（外部 code → 登记 → 执行 → fidelity 校验）并校准测量语义。

## 2. 素材

- MODEL_IR：`research/P15/experiments/P15-K001/runs/02f06b90-…/model_ir.json`
  （2019_C 蓄车池 M/M/c 排队 + 阈值 DP，32 项声明：16 变量 / 2 目标 /
   4 约束 / 10 方程）
- 外部 code 五场景（外部 Agent 侧产出，harness 侧零 LLM）：
  A 符号命名空间 + mapping；X 私有命名空间、无 mapping；XM 私有命名空间 + mapping；
  B 跑通但模型不对；C mapping 撒谎

## 3. 发现的三个真实测量问题（已修复）

| # | 问题 | 现象 | 修复 |
|---|---|---|---|
| 1 | `value_range` 形态不统一 | 生产 MODEL_IR 中 value_range 是字符串（非 schema 声明的 object）→ `fidelity_checks_from_ir` 崩溃 | 仅当 value_range 为 dict 且含 min/max 时生成 F5 范围检查；str/null 跳过（不因形态误报） |
| 2 | 命名空间错位 | 中文声明名（'期望等待时间'）vs 代码英文输出（wait_time）→ 忠实实现被判 misaligned（K001 RQ5 词表错位在执行层的翻版） | 引入 **output_mapping 契约**：{声明名/符号 → 代码输出 key}，外部 Agent 交付 code 时显式声明，存 CODE artifact（可审计），经 EXEC provenance 透传 fidelity |
| 3 | F4 检查 name=None | equation 无 expression 时检查名 None | 用 equation_id/objective_id/constraint_id 作名 |

## 4. 判定语义验证（5 场景，全部符合预期）

| 场景 | exec | fidelity | score | 语义 |
|---|---|---|---|---|
| A  符号命名空间 + mapping | success | **aligned** | 1.0 (32/32) | 忠实实现，全声明可观测 |
| X  私有命名空间、无 mapping | success | **misaligned** | 0.0 (0/32) | 跨命名空间不可验证 → 如实失败（不猜） |
| XM 私有命名空间 + mapping | success | **aligned** | 1.0 (32/32) | mapping 解决翻译，不掩盖缺失 |
| B  跑通但模型不对 | success | **misaligned** | 0.0 (0/32) | 「真执行+假模型」防线 |
| C  mapping 撒谎（key 不存在） | success | **misaligned** | 0.16 (5/32) | 防谎报：mapping 声明不豁免实体缺失 |

关键：mapping 是**可审计的显式声明**（存于 CODE artifact，K002 盲评/测量层可查），
它只解决命名空间翻译，绝不豁免实体缺失（C 场景证明）。

## 5. G4 预检指标（dry-run 样本 n=5）

- `execution_success_rate` = 5/5 = 1.00 —— 可测量，无歧义
- `model_fidelity`（aligned 率）= 2/5 = 0.40 —— 可测量，区分度好
  （0.0 / 0.16 / 1.0 三档清晰分离）
- `evidence_completeness`：以 fidelity checks 的声明覆盖为机械定义
  （32 项声明 → passed/total 可归因到具体声明项）

## 6. K002 契约推论（将写入冻结规格）

1. **外部 Agent 交付 code 必须同时交付 `output_mapping`**（声明名/符号 → 输出 key），
   随 code 登记入 CODE artifact；不交 mapping 时 fidelity 按「无翻译」如实判定。
2. `model_fidelity` 终点 = fidelity checks 通过率（0-1），与盲评 L2 分开报告；
   两者分别测「代码是否执行声明模型」与「模型构造质量」。
3. 执行级终点全链路机械可测：execution_success_rate / invalid_model_rate /
   correction_count（重跑次数）/ model_fidelity / evidence_completeness。
4. 遗留（不属于本 dry-run 范围）：K002 正式题目集 + 区分度预检（G2）待独立执行。

## 7. 产物

- `research/P15/analysis/k002_dryrun_v2.py`（dry-run 脚本，含五场景 code）
- `research/P15/dryrun/k002-dryrun-2019C/`（5 个项目：CODE/EXEC/VR/fidelity 报告）
- `research/P15/dryrun/k002-dryrun-2019C/summary.json`（指标汇总）
- 回归保护：`tests/integration/test_execution_fidelity.py`（+4：value_range str /
  mapping 翻译 / mapping 撒谎 / F4 id 命名）
