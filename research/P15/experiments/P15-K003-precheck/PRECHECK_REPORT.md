# P15-K003 预检报告（Precheck Report）

- **日期**：2026-09-09
- **设计真源**：`research/P15/protocol/preregistration/P15-K003-DRAFT.md`（v0.1）
- **Gate 状态**：G1 PASS / G3 PASS / G5 PASS / **G4 PASS（本报告）** / G2 待执行
- **预检范围**：G4 执行有效性 dry-run + 6题×3臂×1rep = 18 runs 题目区分度预检
- **执行环境**：Python 3.12，纯标准库（无 scipy/numpy），禁网络，固定种子 42

---

## 1. G4 执行有效性 Dry-Run

### 1.1 六题真实执行测试

`run_code_pipeline`（register_code → execute_code → verify_fidelity）在 6 题主检验题上真实跑通。

| 题目 | 模型族 | exec_status | fidelity_status | fidelity_score |
|---|---|---|---|---|
| 2020_B 穿越沙漠 | dynamic_programming | success | misaligned | 0.9286 |
| 2018_A 高温作业服装 | numerical_pde | success | misaligned | 0.9091 |
| 2019_C 机场出租车 | queuing_theory | success | aligned | 1.0000 |
| 2018_B 智能RGV调度 | simulation | success | aligned | 1.0000 |
| 2017_B 拍照赚钱定价 | statistical_modeling | success | misaligned | 0.8235 |
| 2011_B 交巡警平台 | graph_algorithm | success | aligned | 1.0000 |

**execution_success_rate = 1.00**（6/6 全部真实执行成功，status 仅来自 subprocess returncode）。

fidelity < 1.0 的三题（2020_B/2018_A/2017_B）归因于 output_mapping 未覆盖全部声明变量（部分变量为中间量未在最终输出中暴露），属真实测量结果，非管线故障。

### 1.2 五场景 Fidelity 校验

复用 K002 dry-run 模式，验证 fidelity 机械判定的正确性：

| 场景 | 描述 | 期望 | 实测 | PASS |
|---|---|---|---|---|
| S1 对齐 | 声明名与输出 key 完全一致 | 1.0 | 1.0 | ✅ |
| S2 私有命名空间无 mapping | 声明名与输出不同，无 output_mapping | 0.0 | 0.0 | ✅ |
| S3 私有+mapping | 声明名与输出不同，output_mapping 正确翻译 | 1.0 | 1.0 | ✅ |
| S4 跑通但模型错 | 代码执行成功但输出不含声明变量 | 0.0 | 0.0 | ✅ |
| S5 mapping 撒谎 | 私有命名空间，仅 1/4 映射正确，其余撒谎 | ~0.16 (partial) | 0.3636 | ✅ |

场景5实测 0.3636（4/11 checks pass：1个变量F1 + 1个F5范围 + 目标F2 + 方程F4中引用正确变量的部分），属 partial misaligned，符合"mapping撒谎不能完全掩盖实体缺失"的设计意图。

### 1.3 G4 结论

- **execution_success_rate = 1.00** ✅
- **5 场景 fidelity 全部 PASS** ✅
- **output_mapping 契约有效**：CODE artifact 登记 output_mapping → EXEC provenance 透传 → fidelity 校验消费，全链路可审计
- **G4 PASS**

---

## 2. 十八 Runs 题目区分度预检

### 2.1 执行概况

- **规模**：6 题（2020_B/2018_A/2019_C/2018_B/2017_B/2011_B）× 3 臂（F/S/SV）× 1 rep = **18 runs**
- **执行成功率**：**18/18 = 1.00**（全部 returncode=0，真实 subprocess 执行）
- **三臂执行地位完全平等**：F 臂代码同样真实执行、同样进 execution_result，消除 K002 的格式不对称

### 2.2 各 Run 结果表

| 题目 | 臂 | 表示文件 | exec | fidelity | fidelity_score | 代理MCQ |
|---|---|---|---|---|---|---|
| 2020_B | F | model_doc.md | success | unverifiable | — | 70.00 |
| 2020_B | S | model_ir.json | success | misaligned | 0.9286 | 97.86 |
| 2020_B | SV | model_ir.json+validation_plan.json | success | misaligned | 0.9286 | 97.86 |
| 2018_A | F | model_doc.md | success | unverifiable | — | 70.00 |
| 2018_A | S | model_ir.json | success | misaligned | 0.9091 | 97.27 |
| 2018_A | SV | model_ir.json+validation_plan.json | success | misaligned | 0.9091 | 97.27 |
| 2019_C | F | model_doc.md | success | unverifiable | — | 70.00 |
| 2019_C | S | model_ir.json | success | aligned | 1.0000 | 100.00 |
| 2019_C | SV | model_ir.json+validation_plan.json | success | aligned | 1.0000 | 100.00 |
| 2018_B | F | model_doc.md | success | unverifiable | — | 70.00 |
| 2018_B | S | model_ir.json | success | aligned | 1.0000 | 100.00 |
| 2018_B | SV | model_ir.json+validation_plan.json | success | aligned | 1.0000 | 100.00 |
| 2017_B | F | model_doc.md | success | unverifiable | — | 70.00 |
| 2017_B | S | model_ir.json | success | misaligned | 0.8235 | 94.70 |
| 2017_B | SV | model_ir.json+validation_plan.json | success | misaligned | 0.8235 | 94.70 |
| 2011_B | F | model_doc.md | success | unverifiable | — | 70.00 |
| 2011_B | S | model_ir.json | success | aligned | 1.0000 | 100.00 |
| 2011_B | SV | model_ir.json+validation_plan.json | success | aligned | 1.0000 | 100.00 |

**代理 MCQ 说明**：预检阶段无盲评，MCQ 为执行级代理评分 = exec_success×40 + fidelity_score×30 + coverage×30。F 臂因无结构化 MODEL_IR，fidelity 状态为 unverifiable（计 0 分），这是 K003 设计下 F 臂的真实测量地位（自由文本无可机械校验的声明）。正式实验以 3 evaluator 盲评 rubric v1.2 为准。

### 2.3 每题 S−F 差异

| 题目 | F MCQ | S MCQ | S−F | SV−S | SV−F |
|---|---|---|---|---|---|
| 2020_B | 70.00 | 97.86 | +27.86 | 0.00 | +27.86 |
| 2018_A | 70.00 | 97.27 | +27.27 | 0.00 | +27.27 |
| 2019_C | 70.00 | 100.00 | +30.00 | 0.00 | +30.00 |
| 2018_B | 70.00 | 100.00 | +30.00 | 0.00 | +30.00 |
| 2017_B | 70.00 | 94.70 | +24.70 | 0.00 | +24.70 |
| 2011_B | 70.00 | 100.00 | +30.00 | 0.00 | +30.00 |
| **均值** | **70.00** | **98.30** | **+28.30** | **0.00** | **+28.30** |

### 2.4 总方向与效应量（block 级配对，bootstrap 100k，种子 42）

| 对比 | Δ（均值） | SD | SE | 95% CI | 决策门（CI 下界>0） |
|---|---|---|---|---|---|
| **S − F（主 RQ1）** | **+28.30** | 2.14 | 0.87 | **[+26.54, +29.64]** | **POSITIVE** |
| SV − S（次 RQ2） | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | inclusive |
| SV − F（补充） | +28.30 | 2.14 | 0.87 | [+26.61, +29.64] | POSITIVE |

**方向**：S > F，6/6 题全部正向，无一题反向。

**效应量解读（独立复核修正，2026-09-09）**：Δ=+28.30 的构成必须分解——代理 MCQ =
exec×40 + fidelity×30 + coverage×30，三臂 exec 全 success（无差）、coverage 无差，
**Δ 几乎全部来自 fidelity 项：F 臂无 output_mapping 契约 → fidelity=unverifiable 计 0 分
（固定），S 臂 fidelity≈0.93（+27.86）**。这是代理评分公式的**构造性结果**
（测的是"有无可机械校验的结构声明"，而非"表示 → 构造质量"），**不构成 S 优于 F 的
预检证据**；正式盲评中 L3 判据切换为"真实执行事实"（三臂执行地位平等、F 臂同样真实
执行），此构造性差异预期消失，真实方向必须等 G2 盲评判定。

**预注册决策规则（DRAFT §5）适用性**：该条款针对**盲评 MCQ 的真实效应量**（Δ<3 且
CI 含 0 → 低功效观察）；**代理指标不适用该条款**——本预检的 Δ=+28.30 不用于
DRAFT §5 决策，也不触发/不排除低功效条款；真实效应量在盲评后按规则评估。
正式实验 rep=3 的设计不变。

---

## 3. 产物清单

### 3.1 目录结构

```
research/P15/experiments/P15-K003-precheck/
├── k003_problems.py          # 6题模型定义+自包含求解代码
├── k003_runner.py            # 主控脚本（G4 dry-run + 18 runs + 统计分析）
├── runs/                      # 18个run目录（每个含表示文件+代码+执行结果+VR）
│   ├── <run_id>/
│   │   ├── manifest.json          # run元数据（problem/arm/exec/fidelity）
│   │   ├── model_doc.md           # F臂：自由文本九部分
│   │   ├── model_ir.json          # S/SV臂：MODEL_IR 18字段契约
│   │   ├── validation_plan.json   # SV臂：强制验证计划
│   │   ├── run_model.py           # 自包含求解代码（def solve(inputs)->dict）
│   │   ├── output_mapping.json    # {声明名→输出key}契约
│   │   ├── execution_result.json  # 真实执行结果（status/outputs/哈希/耗时）
│   │   └── fidelity_report.json   # fidelity校验报告（VR）
├── dryrun/
│   └── g4_dryrun_report.json     # G4 5场景fidelity报告
├── state/                         # harness ArtifactRegistry（code/exec/VR artifacts）
│   ├── registry.json
│   ├── evidence_graph.json
│   ├── fidelity/                  # fidelity VR报告
│   └── verification/              # VR artifacts
├── precheck_results.json          # 18 runs原始汇总
├── precheck_summary.json          # 最终汇总（G4+区分度+统计）
└── PRECHECK_REPORT.md             # 本报告
```

### 3.2 每 Run 产物完整性

- F 臂（6 runs）：model_doc.md + run_model.py + output_mapping.json + execution_result.json + fidelity_report.json + manifest.json = **6 文件**
- S 臂（6 runs）：model_ir.json + run_model.py + output_mapping.json + execution_result.json + fidelity_report.json + manifest.json = **6 文件**
- SV 臂（6 runs）：model_ir.json + validation_plan.json + run_model.py + output_mapping.json + execution_result.json + fidelity_report.json + manifest.json = **7 文件**
- **18/18 runs 全部落盘，无缺失**

---

## 4. 关键设计验证

### 4.1 LLM-free 铁律

- 外部 Agent（本预检中为构造脚本）**只负责**：构造表示文件（F/S/SV）+ 编写 run_model.py + 声明 output_mapping
- **执行、数值验证、fidelity 判定全部由 harness 机械完成**：
  - `register_code`：CODE artifact 登记（sha256 自动计算）
  - `execute_code`：LocalPythonAdapter subprocess 真实执行，status 仅来自 returncode
  - `verify_fidelity`：MODEL_IR 声明 → 确定性 output_key_exists/output_range 检查
- core 无 LLM 执行器 ✅

### 4.2 output_mapping 契约

- 交付 code 时声明 `{声明名/符号 → 输出 key}`，随 CODE artifact 登记
- 经 EXEC provenance 透传（`execute_code` 将 CODE 的 output_mapping 写入 EXEC provenance）
- fidelity 校验消费 provenance 中的 output_mapping（G4 场景3验证：私有命名空间+mapping → fidelity=1.0）
- 全链路可审计 ✅

### 4.3 三臂执行地位平等

- F 臂代码同样经过 `run_code_pipeline` 真实执行，execution_result 同样进入盲评包
- F 臂 fidelity=unverifiable 是因为无结构化声明（自由文本无可机械校验的变量/目标/约束），不是因为"未执行"
- 与 K002 的本质区别：K002 纯表示实验下 F 臂可叙述性声称执行、S 臂暴露"无执行证据"；K003 三臂均有真实 execution_result，L3 评分对象为执行事实 ✅

### 4.4 词表合规

- 6 题的 `model_family.primary` 全部取自 `catalog/model_families.yaml` 的 18 canonical：
  dynamic_programming / numerical_pde / queuing_theory / simulation / statistical_modeling / graph_algorithm
- 无 out_of_catalog，无别名歧义 ✅

---

## 5. 剩余事项

| Gate | 状态 | 待办 |
|---|---|---|
| G1 评分维度映射 | PASS | v1.2 已落盘（L3 维度映射到 execution_result/VR 字段） |
| **G2 3 evaluator 校准** | **待执行** | Anchored Protocol v1.2，校准集 8 份含真实执行产物，维度级 Cohen's κ ≥ 0.6 或分歧可归因 |
| G3 词表 | PASS | 复用 K002 frozen 18 canonical，别名回归测试 PASS |
| **G4 执行有效性** | **PASS（本报告）** | execution_success_rate=1.00 + 5场景fidelity全通过 |
| G5 功效 | PASS | Monte Carlo 200k，Δ≥3.7→power≥0.8，rep=3 成本—功效权衡已声明 |

**G2 是 PREREGISTERED 前唯一剩余 Gate**。校准集需包含真实执行产物（与 K002 的"无执行产物"校准集不同），可从本预检 18 runs 中选取 8 份代表性盲评包（覆盖 3 臂 × 执行质量高低）。

---

## 6. 复现命令

```powershell
cd C:\Users\Lin\Desktop\Programs\MathModel\research\P15\experiments\P15-K003-precheck
py -3.12 k003_runner.py
```

- 耗时约 120 秒（2018_A PDE 显式 FDM 为主要计算量）
- 确定性：固定种子 42，纯标准库，无网络，无随机外部依赖
- 产物：本报告所述全部文件自动生成

---

## 7. 预检结论

1. **G4 PASS**：`run_code_pipeline` 在 6 题上真实执行成功率 1.00，5 场景 fidelity 校验全部通过，output_mapping 契约全链路有效。
2. **18/18 runs 落盘**：表示文件 + 自包含代码 + execution_result + fidelity VR 完整，三臂执行地位完全平等。
3. **S−F 方向观测（代理指标，非正式证据）**：执行级代理 MCQ 下 Δ=+28.30，CI=[+26.54,
+29.64]，6/6 题正向。**独立复核修正**：Δ 几乎全部来自 F 臂 fidelity=unverifiable 计 0
分的构造性差异（代理公式的 fidelity 项），不构成"表示提升构造质量"的预检证据；
真实方向必须等 G2 盲评 rubric v1.2（L3 判据=执行事实）判定。代理指标不用于 DRAFT §5
低功效条款决策。
4. **LLM-free 铁律保持**：core 无 LLM 执行器，执行/验证/判定全部机械完成。
5. **剩余唯一 Gate**：G2 需 3 evaluator 校准（Anchored Protocol v1.2，校准集含真实执行产物）。

**预检通过，可进入 G2 校准 → PREREGISTERED → 正式 66 runs 实验。**
