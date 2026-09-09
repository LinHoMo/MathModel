# P15-K003 G2 — Anchored Scoring Protocol v1.2

> 适用范围：**P15-K003 正式盲评校准（G2 Instrument validity）**
> 上级文件：`research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md` v1.1
> 继承：`MODEL_CONSTRUCTION_RUBRIC_ANCHOR_K002.md` v1.1a 的二档制、格式中立、证据要求
> 性质：**K003 专属判据澄清**。维度集、权重、PASS 阈值、满分结构**一律不变**
>   （L1=9 / L2=15 / L3=9 / L4=9；L3.5 与 L4.3 满分 1；L1.4 满分 1；L2.6 权重 3）

---

## 0. K003 与 K002 的本质区别（评分者必读）

K002 是**纯表示实验**：产物只有表示文件（model_doc.md / model_ir.json），**没有代码、没有执行结果**。因此 K002 的 L3/L4 评分对象是"求解与验证的**设计**完备性"。

**K003 是构造+执行一体化实验**：每份盲评包包含：
- `problem_statement.txt`（题面）
- 表示文件（`model_doc.md` 或 `model_ir.json`，SV 臂额外有 `validation_plan.json`）
- `run_model.py`（真实可执行代码，固定 ABI `def solve(inputs: dict) -> dict`）
- `execution_result.json`（**真实 subprocess 执行结果**：status / outputs / returncode / duration_ms / code_hash / environment_hash）
- `fidelity_report.json`（**真实 fidelity 校验**：MODEL_IR 声明 → 输出映射的确定性检查）

**因此 K003 的 L3 评分对象是真实执行事实，不是"设计完备性"。** 这是 v1.2 相对 v1.1a 的核心修订。

---

## 1. 评分总则

### 1.1 层级依赖
- L1 FAIL → L2-L4 评分仅作参考，整体判定 FAIL
- L2 FAIL（尤其 L2.6 机理=0）→ L3-L4 评分仅作参考

### 1.2 维度与档位
- 22 个维度，每维度 0/1/2 三档（L2.6 为 0/1/2/3 四档；L1.4/L3.5/L4.3 为 0/1 二档）
- 每维度评分**必须附带 evidence**（非空字符串，引用盲评包中的具体字段/文件/数值）
- 不允许无证据评分

### 1.3 格式中立（沿用 v1.1 §0.4 + v1.1a §5）
- 结构化产物（model_ir.json）：字段齐全且内容正确 = 满分，不因"未展开叙述"扣分
- 叙述式产物（model_doc.md）：明确表达对应内容 = 满分，不因"篇幅长"额外加分
- **产物长度不作为评分依据**
- 每个维度先问"这个维度的信息在产物中是否可查"，再按判据打分

### 1.4 L3 判据核心修订（v1.2 唯一新增）
**L3 各维度评分对象 = 盲评包中的真实 execution_result.json / fidelity_report.json 数值。**
- **禁止**以"声明执行/声称验证"作为 L3 评分依据
- 无执行产物（execution_result.status ≠ success）→ L3 相关维度按实际执行状态评分，不按声明补位
- execution_result 中的 status / outputs / returncode / duration_ms 是 L3 的一手证据
- fidelity_report 中的 fidelity_score / checks[] 是 L3.3/L3.5 的一手证据

---

## 2. L1: Problem Understanding（9 分，5 维度）

| 维度 | 满分 | 关键? |
|---|---|---|
| L1.1 显式条件提取 | 2 | ★ |
| L1.2 隐式条件识别 | 2 | |
| L1.3 交付要求识别 | 2 | ★ |
| L1.4 歧义点标注 | 1 | |
| L1.5 问题类型判定 | 2 | ★ |

### L1.1 显式条件提取（0/1/2）
- 0：题面关键参数/数字未提取或错误率 >30%
- 1：提取了大部分但有遗漏（错误率 10%-30%）
- 2：题面中所有数字、参数、约束被完整提取且正确（错误率 <10%）
- **证据**：表示文件中的 variables/parameters/assumptions vs 题面原文逐条对照

### L1.2 隐式条件识别（0/1/2）
- 0：未识别任何隐式条件
- 1：识别了部分但有明显遗漏
- 2：识别了主要隐式条件并显式说明推导依据
- **证据**：assumptions 列表中的 type=projection/mechanism_assumption 项

### L1.3 交付要求识别（0/1/2）
- 0：未识别交付要求
- 1：识别了主要交付物但规格有遗漏
- 2：完整识别所有交付要求（文件格式、精度、时间范围、特定输出）
- **证据**：表示文件中对题目要求交付物的描述 vs 题面中的交付动词

### L1.4 歧义点标注（0/1，二档制）
- 0：题面有歧义但未标注，或标注了但无处理方案
- 1：标注了歧义并给出合理假设/处理方案；无题面歧义时默认 1 分
- **证据**：assumptions 中的歧义声明

### L1.5 问题类型判定（0/1/2）
- 0：问题类型判定错误
- 1：判定部分正确（综合题只识别一个类型）
- 2：问题类型/建模范式判定正确
- **证据**：model_family.primary（S/SV臂）或 model_doc 中的方法描述（F臂）

**L1 PASS = 总分 ≥6.3 且 L1.1/L1.3/L1.5 不全为 0**

---

## 3. L2: Model Construction（15 分，7 维度）

| 维度 | 满分 | 关键? |
|---|---|---|
| L2.1 变量声明完备性 | 2 | ★ |
| L2.2 参数声明完备性 | 2 | ★ |
| L2.3 假设合理性 | 2 | |
| L2.4 目标正确性 | 2 | ★ |
| L2.5 约束完备性 | 2 | ★ |
| L2.6 机理正确性 | 3 | ★★ |
| L2.7 方程结构完整性 | 2 | |

### L2.1 变量声明完备性（0/1/2）
- 0：关键变量未声明（缺失率 >30%）
- 1：大部分变量已声明但有遗漏或类型未区分
- 2：所有关键变量已声明，区分类型，有单位/定义/取值范围
- **证据**：variables[]（S/SV臂）或 model_doc 变量节（F臂）

### L2.2 参数声明完备性（0/1/2）
- 0：方程中引用的参数 >30% 未声明
- 1：大部分参数已声明但有未声明参数
- 2：所有参数已声明，每个有来源（题面/校准/文献/假设/推导）和取值
- **证据**：parameters[]（S/SV臂）或 model_doc 参数节（F臂）

### L2.3 假设合理性（0/1/2）
- 0：无假设声明，或假设与题面矛盾
- 1：有假设但部分不合理
- 2：假设集显式、合理、可检验，区分类型
- **证据**：assumptions[]

### L2.4 目标正确性（0/1/2）
- 0：目标与题目要求完全不一致
- 1：目标部分正确，或与机制/约束存在明显冲突
- 2：目标与题目一致，输出类型匹配，满足目标-机制-约束三角一致性
- **证据**：objectives[]（S/SV臂）或 model_doc 目标节（F臂）

### L2.5 约束完备性（0/1/2）
- 0：关键约束缺失或方向错误
- 1：大部分约束已形式化但有遗漏
- 2：所有关键约束已形式化，方向正确
- **证据**：constraints[]（S/SV臂）或 model_doc 约束节（F臂）

### L2.6 机理正确性（0/1/2/3，核心维度）
四要素：E1 机理-题面一致 / E2 机理-方程一致 / E3 机理-目标约束一致 / E4 候选对比充分
- 0：机理完全错误（E1 不满足）
- 1：机理家族正确（E1）但 E2/E3 有缺陷
- 2：E1+E2+E3 全满足，但无候选对比或对比仅表面（E4 不满足）
- 3：四要素全满足
- **证据**：mechanisms[] + equations[]（S/SV臂）或 model_doc 机理节（F臂）

### L2.7 方程结构完整性（0/1/2）
- 0：无方程或不可求解
- 1：有方程但结构不完整（缺边界/初始条件），或符号未声明
- 2：方程结构完整（控制方程+边界+初始），符号集⊆变量/参数声明集，可求解
- **证据**：equations[]（S/SV臂）或 model_doc 方程节（F臂）

**L2 PASS = 总分 ≥10.5 且 L2.1/L2.2/L2.4/L2.5/L2.6 不全为 0；若 L2.6=0 整体 L2=FAIL**

---

## 4. L3: Solving（9 分，5 维度）—— **v1.2 核心：真实执行事实**

| 维度 | 满分 | 关键? | 评分对象（v1.2） |
|---|---|---|---|
| L3.1 求解策略匹配 | 2 | ★ | solvers[]声明 + execution_result 真实执行 |
| L3.2 代码可执行性 | 2 | ★ | **execution_result.status（真实，仅来自 returncode）** |
| L3.3 结果收敛性 | 2 | | **execution_result.outputs + fidelity_report 真实数值** |
| L3.4 可复现性 | 2 | ★ | **code_hash / environment_hash / duration_ms（真实）** |
| L3.5 结果合理性 | 1 | | **fidelity_report + outputs 数值范围（真实）** |

### L3.1 求解策略匹配（0/1/2）
- 0：求解策略与模型不匹配，或代码未实现声明的求解器
- 1：策略基本匹配但有口径问题（步长/精度设置不当）
- 2：求解策略与模型类型完全匹配，代码实现与声明一致
- **证据**：表示文件中的 solvers[] + run_model.py 中的实际求解实现 + execution_result 确认执行了该求解器
- **v1.2 修订**：必须交叉验证"声明的求解器"与"代码实际实现"与"execution_result 真实执行"三者一致

### L3.2 代码可执行性（0/1/2）—— **纯机械判定**
- 0：execution_result.status ≠ "success"（代码崩溃/超时/无效，returncode ≠ 0）
- 1：execution_result.status = "success" 但 outputs 不完整（部分输出缺失或只有 stdout_tail）
- 2：execution_result.status = "success" 且 outputs 包含所有声明的输出字段（结构化 JSON 输出）
- **证据**：execution_result.json 中的 status / returncode / outputs
- **v1.2 修订**：**只看 execution_result 真实状态，禁止以"代码看起来能跑"评分**

### L3.3 结果收敛性（0/1/2）—— **真实数值判定**
- 0：execution_result.outputs 中含 NaN/Inf/空值，或 fidelity_report 显示输出与声明完全不匹配（fidelity_score=0）
- 1：输出有值但 fidelity_score < 0.8（部分声明变量不可观测），或数值有异常波动
- 2：输出完整且 fidelity_score ≥ 0.8（声明变量可观测），数值在合理范围内
- **证据**：execution_result.outputs + fidelity_report.json 中的 fidelity_score / checks[]
- **v1.2 修订**：**以 fidelity_report 的真实检查结果为一手证据，不看声明**

### L3.4 可复现性（0/1/2）—— **真实哈希判定**
- 0：execution_result 中无 code_hash 或 environment_hash（执行未记录环境）
- 1：有 code_hash 和 environment_hash，但未固定随机种子（代码中无 seed 设置），或 duration_ms 异常（>60s 可能非确定性）
- 2：code_hash + environment_hash 齐全，代码固定随机种子（seed=42 或等价），duration_ms 合理（<30s），输出确定性可复现
- **证据**：execution_result.json 中的 code_hash / environment_hash / duration_ms + run_model.py 中的 seed 设置
- **v1.2 修订**：**以真实哈希和耗时为证据，不看"声称可复现"**

### L3.5 结果合理性（0/1，二档制）—— **真实数值判定**
- 0：execution_result.outputs 中的数值明显不合理（负概率、负密度、超物理范围），或 fidelity_report checks 中范围检查失败
- 1：输出数值在物理/逻辑合理范围内，fidelity_report 范围检查通过或无范围检查
- **证据**：execution_result.outputs 数值 + fidelity_report checks[] 中的 output_range 检查结果

**L3 PASS = 总分 ≥6.3 且 L3.1/L3.2/L3.4 不全为 0**

---

## 5. L4: Validation（9 分，5 维度）

| 维度 | 满分 | 关键? |
|---|---|---|
| L4.1 对照基线 | 2 | ★ |
| L4.2 灵敏度分析 | 2 | ★ |
| L4.3 极限/边界检验 | 1 | |
| L4.4 验证目标正确性 | 2 | ★ |
| L4.5 证据-主张对应 | 2 | ★ |

### L4.1 对照基线（0/1/2）
- 0：无任何对照基线
- 1：有基线但选择不当或未报告对比结果
- 2：有合理对照基线（零模型/随机/文献/贪婪启发式）并报告对比结果
- **证据**：validation_plan.limit_tests / validations[]（SV臂）或 model_doc 验证节（F/S臂）
- **注意**：SV 臂由 validation_plan.json 机械支撑；S/F 臂无此字段 → 如实按产物判定，不豁免

### L4.2 灵敏度分析（0/1/2）
- 0：无灵敏度分析
- 1：有灵敏度分析但扰动了不敏感参数，或未报告弹性系数
- 2：有灵敏度分析，扰动敏感参数，报告弹性系数和鲁棒性边界
- **证据**：validation_plan.sensitivity（SV臂）或 validations[] / model_doc（S/F臂）

### L4.3 极限/边界检验（0/1，二档制）
- 0：完全没有极限或边界检验
- 1：有 ≥1 类极限/边界/退化情形检验
- **证据**：validation_plan.limit_tests（SV臂）或 validations[] / model_doc（S/F臂）

### L4.4 验证目标正确性（0/1/2）
- 0：验证了与模型主张无关的目标
- 1：验证了部分核心主张但有遗漏
- 2：验证了模型所有核心主张，验证指标与题面 evaluation_targets 对应
- **证据**：validation_plan.validation_targets（SV臂）或 validations[] / claims[]（S/F臂）

### L4.5 证据-主张对应（0/1/2）
- 0：存在 unsupported claim（主张无证据或证据与主张矛盾）
- 1：大部分主张有证据但有 unresolved 或引用不可解析
- 2：所有 Claim 有 ≥1 条 Evidence 支持，判定为 supported/refuted（无 unresolved）
- **证据**：claims[].evidence_refs（S/SV臂）或 model_doc 主张-证据对应（F臂）+ execution_result/fidelity_report 作为真实证据

**L4 PASS = 总分 ≥6.3 且 L4.1/L4.2/L4.4/L4.5 不全为 0**

---

## 6. 评分输出契约

每名 evaluator 对每份校准包输出一个 JSON 文件：

```json
{
  "evaluator_id": "A",
  "rubric_version": "MODEL_CONSTRUCTION_RUBRIC-v1.2-k003",
  "calib_id": "CALIB_01",
  "L1": {
    "total": 0,
    "pass": false,
    "dimensions": {
      "L1.1": {"score": 0, "evidence": "..."},
      "L1.2": {"score": 0, "evidence": "..."},
      "L1.3": {"score": 0, "evidence": "..."},
      "L1.4": {"score": 0, "evidence": "..."},
      "L1.5": {"score": 0, "evidence": "..."}
    }
  },
  "L2": {"total": 0, "pass": false, "dimensions": {"L2.1": {...}, ...}},
  "L3": {"total": 0, "pass": false, "dimensions": {"L3.1": {...}, ...}},
  "L4": {"total": 0, "pass": false, "dimensions": {"L4.1": {...}, ...}},
  "overall": {"total": 0, "pass": false, "note": "..."}
}
```

- 22 维度逐维 score + evidence（evidence 非空，引用盲评包具体字段/数值）
- L3 维度的 evidence **必须引用 execution_result.json 或 fidelity_report.json 中的真实字段/数值**
- 文件命名：`g2/evaluator_<A|B|C>/<calib_id>.json`

---

## 7. 评分纪律

1. **独立评分**：evaluator 之间互不可见、互不通信、不参考其他 evaluator 的评分
2. **证据优先**：每个维度必须有 evidence，无证据不得评分
3. **L3 真实执行**：L3 只看 execution_result.json / fidelity_report.json 的真实数值，禁止以声明补位
4. **格式中立**：不因 model_doc.md 篇幅短或 model_ir.json 字段多而偏向任何一臂
5. **不猜测臂归属**：盲评包已匿名化，evaluator 不得尝试推断该包属于 F/S/SV 哪一臂
6. **一次性完成**：对 8 份校准包一次性评分完成，不中途修改已评分的包

---

*本协议是 K003 G2 Instrument validity 的评分操作手册。维度集/权重/PASS 阈值/满分结构与 rubric v1.1 一致，仅澄清 K003 真实执行条件下的 L3 判据和二档制继承。*
