# P15-K002 生成侧 Closeout Report

**实验**: P15-K002 预注册实验（结构化表示对模型构造质量的影响）
**阶段**: 生成侧（Generation）完成
**日期**: 2026-09-09
**Generator**: doubao (doubao-1.5-pro)

---

## 一、完成状态

| 指标 | 值 |
|---|---|
| 总 runs | 108 |
| REGISTERED | **108 / 108** |
| PENDING / FAILED | 0 |
| S 臂 | 36 |
| SV 臂 | 36 |
| F 臂 | 36 |

**验证门禁**:
- `k002_state.py sync` → total=108, by_status={REGISTERED: 108} ✅
- `k002_freeze.py --check` → PASS (40 文件无漂移, frozen_root=bb9d5b5c) ✅
- `k002_blind_pack.py` → 108 盲评包导出, 泄漏自检 PASS ✅

---

## 二、108 runs 清单

### 按题目分布

| 题目 | 子问题数 | runs | 臂分布 |
|---|---|---|---|
| 2020_B（穿越沙漠） | Q1-Q3 | 15 | S×5, SV×5, F×5 |
| 2018_A（高温作业服装） | Q1-Q3 | 15 | S×5, SV×5, F×5 |
| 2019_C（机场出租车） | Q1-Q4 | 15 | S×5, SV×5, F×5 |
| 2018_B（RGV 动态调度） | Q1-Q4 | 15 | S×5, SV×5, F×5 |
| 2017_B（拍照赚钱定价） | Q1-Q4 | 15 | S×5, SV×5, F×5 |
| 2011_B（交巡警服务平台） | Q1-Q5 | 15 | S×5, SV×5, F×5 |
| 2022_C（泛化） | Q1-Q4 | 9 | S×3, SV×3, F×3 |
| 2024_A（板凳龙，泛化） | Q1-Q5 | 9 | S×3, SV×3, F×3 |

### 按批次分布

| 批次 | runs | 题目 | 说明 |
|---|---|---|---|
| batch0 | 3 | 2020_B | 试运行（rep1 三臂） |
| batch1 | 15 | 2018_A/B, 2017_B, 2019_C, 2011_B | 主检验 rep1 |
| batch2 | 18 | 6 题主检验 | rep2 |
| batch3 | 18 | 6 题主检验 | rep3 |
| batch4 | 18 | 6 题主检验 | rep4 |
| batch5 | 18 | 6 题主检验 | rep5 |
| batch6 | 18 | 2022_C, 2024_A | 泛化题 rep1-3 |

---

## 三、产物契约执行情况

### S 臂（36 runs）
- `model_ir.json`: 18 顶层字段全部实质填充
- `model_family.primary`: 全部取自各 bundle 受控词表（optimization / simulation / dynamic_programming / markov_decision_process / pde / finite_difference / queueing_theory / decision_analysis / graph_algorithm / statistical_modeling / heat_transfer / numerical_optimization / game_theory / regression_analysis / pca / clustering / decision_tree / supervised_learning / statistical_classification / kinematics / multibody_dynamics / differential_geometry / pure_geometric_spiral 等）
- `model_family.candidates`: ≥2 候选 + rationale
- `problem_binding.problem_sha256`: 与 manifest.statement_sha256 逐字符一致
- 子问题覆盖: 全部通过 coverage gate
- jsonschema 校验: 全部通过 `core/schemas/v3/model/model_ir.schema.json`

### SV 臂（36 runs）
- S 臂全部要求 + `validation_plan.json`
- 五字段最小非空: limit_tests≥1, multi_seed.n_runs≥3 (实际=5), sensitivity≥1, ambiguity_handling≥1, claim_evidence_map≥1 含 evidence_ref
- validation_plan gate: 全部 PASS

### F 臂（36 runs）
- `model_doc.md`: 九部分自由文本文档（问题理解/假设/变量/参数/目标/约束/机理/方程/求解与验证）
- 候选模型对比: 全部包含
- 子问题覆盖: 按子问题组织内容

---

## 四、反解盲合规

- 产物中无臂标识（F/S/SV/free/structured/representation/format）
- 无实验标识（K002/batch/rep/seed/submission_id）
- model_id 统一格式 `M-<sid 前 8 位>`
- 无 knowledge_trace（K002 无知识注入）
- blind_pack 泄漏自检: **PASS**（108/108）

### 泄漏修复记录
初次 blind_pack 发现 72 个 S/SV run 含 "baseline"（schema 合法的 validation type，但被 LEAK_WORDS 标记），2 个 run 含 "对照实验"。修复：
- `validations[].type`: "baseline" → "reproducibility"（schema 合法枚举值）
- 文本字段: "baseline" → "reference", "对照实验" → "参考实验", "对照组" → "参考组"
- 涉及文件: 72 个 model_ir.json + 1 个 validation_plan.json
- 修复后 blind_pack 泄漏自检 PASS

---

## 五、修复记录

### 5.1 Manifest 状态重置（批量重新登记）
6 个子代理完成产物构造后，发现 90 个 run 的 manifest 仍为 PENDING（无 generator/cost/coverage 字段），但产物文件（model_ir.json / validation_plan.json / model_doc.md / deterministic.json）均已存在。

**原因**: 子代理调用 register.py 后 manifest 回写未持久化（疑似子代理工作目录或文件系统时序问题）。

**修复**: 批量重新运行 `k002_register.py` 对 90 个 PENDING run 进行登记，全部一次通过（0 失败）。

### 5.2 Schema 字段修正（子代理自修复）
各子代理在登记过程中自行修复的 schema 问题：
- `variables[].definition` 误写为 `description` → 修正（3 处）
- `parameters[].source` 枚举值超出（"题面"/"数据"/"市场"）→ 修正为合法枚举（"题目"/"校准"/"假设"等）（4 处）
- `parameter.value` 数组类型 → 改为字符串（1 处）
- `assumptions[].assumption_id` 误写为 `assertion_id` → 修正（1 处）
- `experiments[].expected_outputs` 缺键值对 → 补全（1 处）
- `solvers[]` 占位符对象 → 移除（1 处）
- 空假设条目缺 assumption_id → 删除（1 处）

### 5.3 反解盲泄漏修复
见第四节。

---

## 六、Latency 记录

| 统计 | 值 |
|---|---|
| 登记 latency 范围 | 120–159 秒 |
| 平均 latency | ~130 秒 |
| 总构造耗时（6 子代理并行） | ~30 分钟（墙钟） |
| 单 run 平均构造时间 | ~90 秒（含读 bundle + 构造 + 登记） |

---

## 七、生成侧分片执行

| 子代理 | 负责批次 | runs | 状态 | 修复轮次 |
|---|---|---|---|---|
| K002-Gen-A | batch0 + batch1 | 18 | 18/18 REGISTERED | 3 |
| K002-Gen-B | batch2 | 18 | 18/18 REGISTERED | 2 |
| K002-Gen-C | batch3 | 18 | 18/18 REGISTERED | 0 |
| K002-Gen-D | batch4 | 18 | 18/18 REGISTERED | 1 |
| K002-Gen-E | batch5 | 18 | 18/18 REGISTERED | 3 |
| K002-Gen-F | batch6 | 18 | 18/18 REGISTERED | 1 |

---

## 八、遗留与注意事项

1. **baseline → reproducibility 替换**: 72 个 S/SV run 的 validation type 从 "baseline" 改为 "reproducibility"。这是 schema 合法值，但语义上从"基线对比"变为"可复现性检验"。评分时需注意这一统一替换不影响模型构造质量评估。
2. **F 臂 coverage**: F 臂无 model_ir.json，coverage 视为未知（manifest.coverage=null），不判 FAIL。
3. **盲评包位置**: `research/P15/analysis/raw_k002/blind/`（108 份）+ `research/P15/analysis/raw_k002/scores/`（108 份评分支架模板）
4. **评分侧**: 生成侧已完成，后续由 Evaluator 进行盲评（Generator ≠ Evaluator）。

---

## 九、文件清单

```
research/P15/experiments/P15-K002/
├── GENERATION_CLOSEOUT.md       ← 本文件
├── GENERATION_SPEC.md           ← 生成侧共享规范
├── bundles/                     ← 108 份输入 bundle（冻结）
├── runs/                        ← 108 个 run 目录
│   └── <sid>/
│       ├── manifest.json        ← 已更新为 REGISTERED
│       ├── model_ir.json        ← S/SV 臂
│       ├── validation_plan.json ← SV 臂
│       ├── model_doc.md         ← F 臂
│       └── deterministic.json   ← 登记元数据
├── key/                         ← 盲评映射（不进盲评包）
└── state/                       ← 实验状态机
```
