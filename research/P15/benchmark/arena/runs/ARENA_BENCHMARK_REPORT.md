# Candidate Arena Benchmark 报告

> 候选池：`C:\Users\Lin\Desktop\Programs\MathModel\research\P15\experiments\P15-K003\runs` ｜ 生成：2026-09-10T03:40:19+00:00 ｜ 模式：`arena_benchmark`（真实 subprocess 重跑，机械选型）

## 汇总

- 题目数：8
- 候选总数：44
- 有选型决策：8
- 如实不选型（UNSELECTED）：0

## 逐题结果

### 2011_B

| 候选 | 臂 | exec_status | valid | cvm | l6 | fidelity | 选型 |
|---|---|---|---|---|---|---|---|
| 0a01718b | SV | success | True | 0.0 | passed | 1.0 | ✓ |
| 8a0f3939 | S | success | True | 0.0 | passed | 1.0 | ✓ |
| 911f5bf6 | SV | success | True | 0.0 | passed | 1.0 | ✓ |
| cba5d544 | S | success | True | 0.0 | passed | 1.0 | ✓ |
| d10cf9a6 | SV | success | True | 0.0 | passed | 1.0 | ✓ |
| d694cc37 | S | success | True | 0.0 | passed | 1.0 | ✓ |

**决策**：选择 M-2011B-GRAPH
- 依据：exec_status=success
- 依据：valid=True
- 依据：l6=passed
- 依据：cvm=0.0
- 依据：fidelity=1.0

### 2017_B

| 候选 | 臂 | exec_status | valid | cvm | l6 | fidelity | 选型 |
|---|---|---|---|---|---|---|---|
| 10422e69 | SV | success | False | 0.0 | passed | 0.8889 | ✓ |
| 22a34ef9 | S | success | False | 0.0 | passed | 0.8889 | ✓ |
| 497caeb2 | S | success | False | 0.0 | passed | 0.8889 | ✓ |
| 8b075022 | SV | success | False | 0.0 | passed | 0.8889 | ✓ |
| d7469d1f | SV | success | False | 0.0 | passed | 0.8889 | ✓ |
| fd79250a | S | success | False | 0.0 | passed | 0.8889 | ✓ |

**决策**：选择 M-2017B-LOGIT
- 依据：exec_status=success
- 依据：valid=False
- 依据：l6=passed
- 依据：cvm=0.0
- 依据：fidelity=0.8889
- 依据：（无候选通过数值验证，在存活候选中选择约束违反最小者——如实标注降级选型）

### 2018_A

| 候选 | 臂 | exec_status | valid | cvm | l6 | fidelity | 选型 |
|---|---|---|---|---|---|---|---|
| 09f28cd1 | SV | success | False | 0.0 | passed | 0.9231 | ✓ |
| 35e757a8 | SV | success | False | 0.0 | passed | 0.9231 | ✓ |
| 4367031a | SV | success | False | 0.0 | passed | 0.9231 | ✓ |
| c495cd73 | S | success | False | 0.0 | passed | 0.9231 | ✓ |
| cd1d7e02 | S | success | False | 0.0 | passed | 0.9231 | ✓ |
| f43ad9a1 | S | success | False | 0.0 | passed | 0.9231 | ✓ |

**决策**：选择 M-2018A-PDE
- 依据：exec_status=success
- 依据：valid=False
- 依据：l6=passed
- 依据：cvm=0.0
- 依据：fidelity=0.9231
- 依据：（无候选通过数值验证，在存活候选中选择约束违反最小者——如实标注降级选型）

### 2018_B

| 候选 | 臂 | exec_status | valid | cvm | l6 | fidelity | 选型 |
|---|---|---|---|---|---|---|---|
| 1db7f2aa | S | success | True | 0.0 | passed | 1.0 | ✓ |
| 44781f3e | SV | success | True | 0.0 | passed | 1.0 | ✓ |
| 7e867777 | SV | success | True | 0.0 | passed | 1.0 | ✓ |
| 9bc2dd39 | S | success | True | 0.0 | passed | 1.0 | ✓ |
| c5c91a4e | S | success | True | 0.0 | passed | 1.0 | ✓ |
| fc38fd1c | SV | success | True | 0.0 | passed | 1.0 | ✓ |

**决策**：选择 M-2018B-DES
- 依据：exec_status=success
- 依据：valid=True
- 依据：l6=passed
- 依据：cvm=0.0
- 依据：fidelity=1.0

### 2019_C

| 候选 | 臂 | exec_status | valid | cvm | l6 | fidelity | 选型 |
|---|---|---|---|---|---|---|---|
| 3e4fde2e | S | success | True | 0.0 | passed | 1.0 | ✓ |
| 5e84f606 | SV | success | True | 0.0 | passed | 1.0 | ✓ |
| 8227a3c9 | SV | success | True | 0.0 | passed | 1.0 | ✓ |
| d7be89bd | S | success | True | 0.0 | passed | 1.0 | ✓ |
| de42ece2 | SV | success | True | 0.0 | passed | 1.0 | ✓ |
| df1716ae | S | success | True | 0.0 | passed | 1.0 | ✓ |

**决策**：选择 M-2019C-QUEUE
- 依据：exec_status=success
- 依据：valid=True
- 依据：l6=passed
- 依据：cvm=0.0
- 依据：fidelity=1.0

### 2020_B

| 候选 | 臂 | exec_status | valid | cvm | l6 | fidelity | 选型 |
|---|---|---|---|---|---|---|---|
| 0cd422af | S | success | True | 0.0 | passed | 0.9375 | ✓ |
| 67c7b237 | SV | success | True | 0.0 | passed | 0.9375 | ✓ |
| 9928a110 | S | success | True | 0.0 | passed | 0.9375 | ✓ |
| cd7358e9 | SV | success | True | 0.0 | passed | 0.9375 | ✓ |
| d689acb0 | SV | success | True | 0.0 | passed | 0.9375 | ✓ |
| e9d8fbe5 | S | success | True | 0.0 | passed | 0.9375 | ✓ |

**决策**：选择 M-2020B-DP
- 依据：exec_status=success
- 依据：valid=True
- 依据：l6=passed
- 依据：cvm=0.0
- 依据：fidelity=0.9375

### 2022_C

| 候选 | 臂 | exec_status | valid | cvm | l6 | fidelity | 选型 |
|---|---|---|---|---|---|---|---|
| 09a80448 | S | success | False | 0.0 | passed | 0.2941 | ✓ |
| 3b6c64b4 | SV | success | False | 0.0 | passed | 0.2941 | ✓ |
| c5c70405 | S | success | False | 0.0 | passed | 0.2941 | ✓ |
| d1c242bf | SV | success | False | 0.0 | passed | 0.2941 | ✓ |

**决策**：选择 M-2022C-stats
- 依据：exec_status=success
- 依据：valid=False
- 依据：l6=passed
- 依据：cvm=0.0
- 依据：fidelity=0.2941
- 依据：（无候选通过数值验证，在存活候选中选择约束违反最小者——如实标注降级选型）

### 2024_A

| 候选 | 臂 | exec_status | valid | cvm | l6 | fidelity | 选型 |
|---|---|---|---|---|---|---|---|
| 1db4196e | SV | success | False | 0.0 | passed | 0.2727 | ✓ |
| 1dbb1df6 | SV | success | False | 0.0 | passed | 0.2727 | ✓ |
| ac2de074 | S | success | False | 0.0 | passed | 0.2727 | ✓ |
| de79e4d6 | S | success | False | 0.0 | passed | 0.2727 | ✓ |

**决策**：选择 M-2024A-kinematics
- 依据：exec_status=success
- 依据：valid=False
- 依据：l6=passed
- 依据：cvm=0.0
- 依据：fidelity=0.2727
- 依据：（无候选通过数值验证，在存活候选中选择约束违反最小者——如实标注降级选型）

## 验证语义说明

- `valid` = 通用确定性检查（FIX-5.2：MODEL_IR 声明变量/目标键出现在真实
  执行输出 + output_mapping 输出键解析）——**结构级检查，不是数值正确性**；
- `cvm`（constraint_violation_max）与 `fidelity_score` 为机械判定（VR/
  fidelity 管线）；
- `l6` = ground-truth 断言判定（`problem_cards/*/gt.json#l6_assertions`：
  feasibility / objective_finite / 输出非负等数学必然与题面客观边界，
  非答案数值）；无断言 → `unverifiable`（不编造分数）；
- 选型决策只基于上表机械证据，无证据不选型（UNSELECTED 如实报告）。
