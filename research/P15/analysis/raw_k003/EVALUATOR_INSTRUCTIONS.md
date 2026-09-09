# P15-K003 正式盲评 — Evaluator Instructions

> 版本：v1.0（2026-09-09）
> 判据真源：`research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md` v1.1 + `research/P15/experiments/P15-K003-precheck/g2/ANCHORED_PROTOCOL_v1.2a.md`
> 本文件是上述两份判据的**执行摘要与操作流程**，不替代原文；遇歧义以原文为准。

---

## 0. 你的角色与隔离纪律

你是 P15-K003 正式盲评的独立 Evaluator。你与另外两名 Evaluator（B、C）**互不可见、互不通信**，各自独立完成全部 66 份匿名盲评包的评分。

**严禁行为（违反即实验作废）：**
- 不得打开或搜索 `research/P15/experiments/P15-K003/key/condition_map.json`（臂分组映射）
- 不得打开或搜索 `research/P15/experiments/P15-K003/runs/`（原始 submission 目录）
- 不得打开或搜索 `research/P15/experiments/P15-K003/real_execution_results.json`
- 不得与其他 Evaluator 讨论评分、交换意见、对比结果
- 不得修改 `bundles/` 下任何文件

**你唯一可读取的评分对象：** `research/P15/experiments/P15-K003/bundles/BUNDLE_001` 至 `BUNDLE_066/`

你不知道每份包属于哪个臂（F/S/SV），也不需要知道——评分只按 rubric 逐维判断内容质量。

---

## 1. 盲评包结构

每份 `BUNDLE_xxx/` 包含以下文件（全部匿名化，ID 已替换为 `model_BUNDLE_xxx` / `CODE_BUNDLE_xxx` / `EXEC_BUNDLE_xxx`）：

| 文件 | 存在性 | 说明 |
|---|---|---|
| `problem_statement.txt` | 必有 | 题目原文 |
| `model_ir.json` 或 `model_doc.md` | 必有其一 | 模型表示文件（结构化 JSON 或叙述式 Markdown） |
| `validation_plan.json` | 部分有 | 验证计划（仅 SV 臂有，但你不应据此推断臂） |
| `run_model.py` | 必有 | 求解代码（固定 ABI `def solve(inputs) -> dict`） |
| `execution_result.json` | 必有 | **真实执行结果**（harness subprocess 执行，含 outputs/code_hash/duration_ms/status） |
| `fidelity_report.json` | 必有 | 声明-输出保真度校验（fidelity_status / fidelity_score / checks 列表） |

**关键：`execution_result.json` 是真实执行产物**，不是声明。`status=success` + `returncode=0` + 非空 `outputs` 表示代码真实跑通。

---

## 2. 评分维度与满分（22 维，总分 42）

| 层级 | 维度 | 满分 | 关键? |
|---|---|---|---|
| L1 Problem Understanding (9) | L1.1 显式条件提取 | 2 | ★ |
| | L1.2 隐式条件识别 | 2 | |
| | L1.3 交付要求识别 | 2 | ★ |
| | L1.4 歧义点标注 | 1 | |
| | L1.5 问题类型判定 | 2 | ★ |
| L2 Model Construction (15) | L2.1 变量声明完备性 | 2 | ★ |
| | L2.2 参数声明完备性 | 2 | ★ |
| | L2.3 假设合理性 | 2 | |
| | L2.4 目标正确性 | 2 | ★ |
| | L2.5 约束完备性 | 2 | ★ |
| | L2.6 机理正确性 | 3 | ★★ |
| | L2.7 方程结构完整性 | 2 | |
| L3 Solving (9) | L3.1 求解策略匹配 | 2 | ★ |
| | L3.2 代码可执行性 | 2 | ★ |
| | L3.3 结果收敛性 | 2 | |
| | L3.4 可复现性 | 2 | ★ |
| | L3.5 结果合理性 | 1 | |
| L4 Validation (9) | L4.1 对照基线 | 2 | ★ |
| | L4.2 灵敏度分析 | 2 | ★ |
| | L4.3 极限/边界检验 | 1 | |
| | L4.4 验证目标正确性 | 2 | ★ |
| | L4.5 证据-主张对应 | 2 | ★ |

**L2.6 权重 3 满分 3，不要再乘权重。** L1.4 / L3.5 / L4.3 满分 1（二档或三档见判据）。

---

## 3. 评分流程（每份包严格按此顺序）

### Step 1：读题面
读 `problem_statement.txt`，理解题目要求、子问题、交付物。

### Step 2：读模型表示
- 若有 `model_ir.json`：通读全部字段（variables / parameters / assumptions / objective / constraints / mechanisms / equations / model_family / candidates / validation_targets 等）
- 若有 `model_doc.md`：通读全文，提取对应内容
- 若有 `validation_plan.json`：读 limit_tests / sensitivity / validation_targets

### Step 3：读代码与执行结果
- 读 `run_model.py`：理解求解策略、算法选择、seed 设置
- 读 `execution_result.json`：**这是 L3 的核心证据**。检查 status、returncode、outputs 内容、duration_ms、code_hash
- 读 `fidelity_report.json`：fidelity_status（aligned/misaligned/unverifiable/failed）、fidelity_score、checks 通过情况

### Step 4：逐维评分（L1 → L2 → L3 → L4）
按 §4 的维度判据逐维打分，每维记录简短证据指针。

### Step 5：计算层总分与终点
- L1_total = L1.1+...+L1.5（满分 9）
- L2_total = L2.1+...+L2.7（满分 15）
- L3_total = L3.1+...+L3.5（满分 9）
- L4_total = L4.1+...+L4.5（满分 9）
- MCQ_primary = (L2_total + L3_total + L4_total) / 33 × 100
- VAL_primary = L4_total / 9 × 100

### Step 6：写评分 JSON
输出到 `research/P15/analysis/raw_k003/scores/evaluator_<你的ID>/BUNDLE_xxx.json`

---

## 4. 维度判据要点（rubric v1.1 + 锚定 v1.2a 摘要）

### L1 问题理解

**L1.1 显式条件提取（0/1/2）**：题面数字、参数、约束是否完整提取。错误率 <10%→2，10-30%→1，>30%→0。

**L1.2 隐式条件识别（0/1/2）**【锚定 §2.2】：隐式条件 = 题面未直接陈述但建模必须依赖的前提（随机性假设、分布假设、简化假设、边界条件假设）。≥2 类+依据→2；仅 1 类或无依据→1；无→0。**不要求**识别季节/经验/政策等外部未建模因素。

**L1.3 交付要求识别（0/1/2）**：文件格式、精度、时间范围、特定时刻输出是否完整识别。

**L1.4 歧义点标注（0/1 二档）**【锚定 §2.1】：必须有**显式的歧义声明**（"题面未给定 X"/"X 存在歧义"）+ 处理方案，两者缺一不可。单纯参数赋值 ≠ 歧义标注。题面确实无歧义时默认 1 分。

**L1.5 问题类型判定（0/1/2）**：问题数学类型/建模范式是否正确。完全错误→0，部分正确→1，正确且与 gold family 有交集→2。

### L2 模型构建

**L2.1 变量声明完备性（0/1/2）**：关键变量是否声明并区分类型（状态/决策/观测/常量）。缺失率 <10%→2。

**L2.2 参数声明完备性（0/1/2）**：方程引用的参数是否全部声明，每个有来源和取值。

**L2.3 假设合理性（0/1/2）**：假设集显式、合理、可检验，区分类型。

**L2.4 目标正确性（0/1/2）**【v1.1 三角一致性】：目标与题目一致 + 目标-机制-约束三角一致（机制可产生目标量，约束不使目标恒无解/恒平凡）。

**L2.5 约束完备性（0/1/2）**：关键约束形式化且方向正确。

**L2.6 机理正确性（0/1/2/3，权重 3）**【v1.1 四要素 + 锚定 §2.4】：
- E1 机理-题面一致（机理家族与问题物理/现实一致）
- E2 机理-方程一致（方程数学形式与机理描述结构匹配；**不要求**符号与教科书定义完全一致，符号标注问题在 L2.1 扣分）
- E3 机理-目标/约束一致
- E4 候选对比充分（≥2 候选 + 明确选择依据）
- 0：E1 不满足（机理完全错误）
- 1：E1 满足但 E2/E3 有缺陷
- 2：E1+E2+E3 满足，E4 不满足
- 3：四要素全满足

**L2.7 方程结构完整性（0/1/2）**【v1.1 符号一致性】：控制方程+边界/初始条件完整，方程符号集 ⊆ 变量/参数声明集，可求解。

### L3 求解（**评分对象 = 真实 ExecutionResult，禁止以声明评分**）

**L3.1 求解策略匹配（0/1/2）**：代码中的求解算法与模型类型/口径是否匹配（读 run_model.py 判断）。

**L3.2 代码可执行性（0/1/2）**：以 `execution_result.json` 为准。status=success + returncode=0 + outputs 非空→可执行。有警告/部分输出缺失→1。崩溃无结果→0。

**L3.3 结果收敛性（0/1/2）**【锚定 §2.3，按 fidelity_status 分情况】：
- **aligned/misaligned**（有 fidelity_score）：≥0.8 且无 NaN/Inf→2；0<score<0.8 或部分缺失→1；score=0 或 NaN/Inf→0
- **unverifiable**（fidelity_score=null，以 outputs 真实数值完整性判定）：所有声称输出字段存在、有限值、合理范围→2；部分缺失或异常→1；NaN/Inf/空值/退化解→0
- **failed**：0 分
- **退化解**：路径为空、索引负/超范围、关键输出为零且与题面矛盾、n_states_explored=1 → 0 分

**L3.4 可复现性（0/1/2）**【v1.1 格式中立】：检查代码中 seed 是否固定（应为 42）、是否有多 seed 运行记录。多 seed（≥5）方差 <10% 或 replay match ≥95%→2；方差 10-20% 或 replay 80-95%→1；方差 >20% 或无 seed 固定→0。S 臂结构化产物由 experiments[].reproducibility 字段机械支撑；SV 臂由 validation_plan.multi_seed 支撑。

**L3.5 结果合理性（0/1）**：outputs 数值在物理/逻辑合理范围、量级正确。明显不合理（负概率、负密度等）→0。

### L4 验证

**L4.1 对照基线（0/1/2）**【锚定 §2.5】：对照基线 = 独立于模型的外部参照（零模型、随机基线、文献基准、贪婪/启发式基线、真实数据对比）。**模型内部自洽检验（稳定性/单调性/决策一致性/边界条件）不构成对照基线**。有基线+对比结果→2；有基线无结果或过简→1；无→0。

**L4.2 灵敏度分析（0/1/2）**：有参数扰动分析且扰动了敏感参数，报告弹性系数/鲁棒性边界→2；有但扰动了不敏感参数→1；无→0。SV 臂 validation_plan.sensitivity 字段可作证据。

**L4.3 极限/边界检验（0/1）**【v1.1】：≥2 类检验（极端参数+边界值/退化情形）且结果与主张关联→1；1 类或未关联→0；无→0。SV 臂 validation_plan.limit_tests 可作证据。

**L4.4 验证目标正确性（0/1/2）**：验证了模型的核心主张（与 evaluation_targets 对应），而非无关目标。全部核心主张→2；部分→1；完全无关→0。

**L4.5 证据-主张对应（0/1/2）**【锚定 §2.6，证据严格覆盖原则】：每条 claim 必须有可解析到具体字段/数值的 evidence，状态为 supported/refuted，不允许 unresolved。主张"扫描发现切换点"但扫描区间未跨过临界值 = 无证据支撑 = unsupported。所有 claim 有证据→2；存在 unresolved→1；存在 unsupported→0。

---

## 5. 格式中立规则（v1.1 §0.4，必读）

- 结构化 `model_ir.json` 与叙述式 `model_doc.md` **评分等价**
- 结构化产物：字段齐全且内容正确 = 满分，**不要求**叙述性展开
- 叙述式产物：明确表达对应内容 = 满分，**不额外加分**
- 每维评分先判断内容是否可查（字段 or 叙述），再按判据打分
- **不因格式差异扣分或加分**

---

## 6. 输出 JSON Schema

每份包输出一个 JSON 文件，路径：
`research/P15/analysis/raw_k003/scores/evaluator_<A|B|C>/BUNDLE_xxx.json`

```json
{
  "bundle_id": "BUNDLE_001",
  "evaluator": "A",
  "rubric_version": "MODEL_CONSTRUCTION_RUBRIC-v1.1",
  "anchored_protocol": "v1.2a",
  "scores": {
    "L1.1": 2,
    "L1.2": 1,
    "L1.3": 2,
    "L1.4": 1,
    "L1.5": 2,
    "L2.1": 2,
    "L2.2": 1,
    "L2.3": 2,
    "L2.4": 2,
    "L2.5": 1,
    "L2.6": 2,
    "L2.7": 1,
    "L3.1": 2,
    "L3.2": 2,
    "L3.3": 1,
    "L3.4": 0,
    "L3.5": 1,
    "L4.1": 0,
    "L4.2": 1,
    "L4.3": 0,
    "L4.4": 1,
    "L4.5": 0
  },
  "layer_totals": {
    "L1": 8,
    "L2": 11,
    "L3": 6,
    "L4": 2
  },
  "MCQ_primary": 57.58,
  "VAL_primary": 22.22,
  "notes": "简短评分依据：L3.4=0 因代码未固定 seed 且无多 seed 记录；L4.1=0 因仅有内部自洽检验无外部基线；..."
}
```

**要求：**
- 22 个维度全部出现，不得遗漏
- 分数为整数，不得超出各维满分
- layer_totals 必须与 scores 求和一致
- MCQ_primary / VAL_primary 保留 2 位小数
- notes 至少 1 句，说明关键扣分点

---

## 7. 评分纪律

1. **逐份独立评分**：每份包读完所有文件后再打分，不跨包参考
2. **证据驱动**：每个分数必须能在包内文件中找到依据，notes 中写明关键扣分点
3. **L3 必须看 execution_result**：禁止仅凭 model_ir/model_doc 中的"声明执行"给 L3 高分
4. **不推断臂**：即使你猜到某包可能属于 F/S/SV，也不得据此调整评分
5. **不评估"哪个臂更好"**：你没有臂映射，只按 rubric 逐维评分
6. **一次性完成**：66 份包按 BUNDLE_001 → BUNDLE_066 顺序评分，完成后不修改已评分文件
7. **LLM-free 评分**：评分是你的认知判断，不使用脚本自动打分

---

*本指令基于 rubric v1.1 + 锚定协议 v1.2a 编写。G2 校准 mean κ=0.712（13/22 维 ≥0.6），本正式盲评使用相同判据。*
