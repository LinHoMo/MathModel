# P15-K001 执行进度

- 生成时间：2026-09-08
- protocol_version：`1.0`
- 预注册：`research/P15/protocol/preregistration/P15-K001-v1.0.md`
- 状态机：`state/status.json`（`k001_state.py show`）

## 当前阶段

```
DESIGN → REVIEW → PREREGISTERED → FROZEN → PREFLIGHT(PASS) → [RUNNING] → VALIDATION → ANALYSIS → CLOSED
```

## 完成项

| 项 | 状态 | 载体 |
|---|---|---|
| 三臂协议标记 SUPERSEDED | ✅ | `experiments/three_arm/protocol.md`（正文保留） |
| 2×2+Sham 预注册 | ✅ | `protocol/preregistration/P15-K001-v1.0.md` |
| 3 个 schema | ✅ | `protocol/schemas/` |
| 冻结资产（题面/知识/案例/Sham/prompt） | ✅ | `protocol/frozen_specs/` + `hashes.json`（44 文件） |
| 案例资产 10 份（5 结构 + 5 解答） | ✅ | `cases/`，泄漏扫描全绿 |
| 55 个 bundle + 执行顺序 + 盲评密钥 | ✅ | `bundles/`、`run_order.json`、`key/condition_map.json` |
| 工具链 7 个脚本 | ✅ | `scripts/k001_*.py`、`analysis/scripts/paired_analysis.py` |
| PREFLIGHT 7 项门禁 | ✅ 全绿 | `k001_preflight.py` |
| Batch 0（2020_B × 5 臂 × rep1） | ✅ 5/5 已登记 | `runs/<sid>/` |
| 盲评导出与去标识自检 | ✅ 通过 | `analysis/raw/blind/`、`analysis/raw/scores/*.template.json` |

## 运行计数

| 批次 | 内容 | 计划 | 已完成 |
|---|---|---|---|
| batch0 | 2020_B × 5 臂 × rep1 | 5 | **5** |
| batch1 | 2018_A / 2019_C × 5 臂 × rep1 | 10 | 0 |
| batch2 | 主检验三题 × 5 臂 × rep2 | 15 | 0 |
| batch3 | 主检验三题 × 5 臂 × rep3 | 15 | 0 |
| batch4 | 2022_C / 2024_A × 5 臂 × rep1（泛化观察） | 10 | 0 |
| **合计** | | **55** | **5** |

## 已暴露并修复的仪器缺陷（记录在案，均为 FROZEN 前的工具修正）

1. **符号抽取器把 LaTeX/英文噪声算作未声明符号** → 重写 `extract_symbols`：
   去说明块 → 去 LaTeX 命令 → 去花括号/上标 → 提标识符；并支持 `w_t → w` 的下标主干匹配。
   修复前未声明率虚高至 74%，修复后真实率 0–11%。
2. **盲评包通过 `model_id` 泄漏臂别** → 产物 `model_id` 全部 neutralize 为 `m-<题>-<8位hex>`，
   并去掉描述中的「结构案例 / 知识卡 / armX / sham」等词；`k001_blind_pack.py` 的
   `LEAK_WORDS` 已扩充并强制拦截。
3. **状态机 run 计数增量漂移** → 改为从 manifests 重算（`k001_state.py sync`）。

## 下一步（阻塞点）

**盲评需要独立评估者，Generator 不得自评。**

- 盲评包已就绪：`analysis/raw/blind/<sid>.md`（仅含 submission_id + 题面 + MODEL_IR + 评分表）
- 评分支架已就绪：`analysis/raw/scores/<sid>.template.json`
- 需要：用**与生成模型不同**的模型（本地 `opencode` / `claude` CLI 指定其他模型，或手工贴给其他模型）
  按 `capability/MODEL_CONSTRUCTION_RUBRIC.md` 逐维打分，把结果写成
  `analysis/raw/scores/<sid>.json`（去掉 `.template` 后缀）
- 人工抽样：≥20%（≥11 份，覆盖全部 5 臂）复核，报告 κ / ICC

评分齐备后：

```bash
py -3.12 research/P15/analysis/scripts/paired_analysis.py --freeze   # DATA FREEZE
py -3.12 research/P15/analysis/scripts/paired_analysis.py            # 分析报告
```

## 执行约定（后续批次不得变更）

- 严格按 `protocol/frozen_specs/run_order.json` 的 `seq` 顺序推进
- 每个 bundle 是生成侧唯一输入，执行 agent 不得自行检索外部资料
- 每个 run 的 `model_id` 必须 neutral，不得出现 arm / sham / 案例来源等字样
- B/C/D/E 臂必须填写 `knowledge_trace`
- `k001_freeze.py --check` 必须保持 PASS，否则 v1.0 数据作废
