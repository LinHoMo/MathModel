# P14 Pilot Report — Model → Experiment / Evidence Transmission 正式判定

- 判定日期：2026-09-07 · Run：`P14-20260907-01`
- 依据：`PRE_REGISTRATION.md`（v1 FROZEN）+ `RUNBOOK_P14_1.md`（v1 + v1.1 增补）+ `p14_integrity_gate.py`（G0–G7）
- 实体规模：6 ExperimentSpec / 21 Execution / 21 Result / 21 Evidence / 9 Claim / manifest（21 条 replay 记录）

## 1. 最终判定

> **PASS。** 本 Harness 具备把一个冻结 MODEL_ARTIFACT 转化为可执行实验，并把实验结果转化为**可审计 Evidence 与 Claim 判定**的能力——包括对 Claim 做支持/驳回判定，并把任一判定反向追溯到冻结模型。

### 六项能力判定（判定口径：能力是否成立，而非"实验是否全部成功"）

| # | 能力 | 当前证据 | 判定 |
|---|---|---|---|
| 1 | Model → Experiment 1:1 provenance | 6/6 spec 的 model_artifact_hash 与冻结表及文件实测闭合 | **PASS** |
| 2 | Experiment → Result deterministic record | 21/21 Execution 携带 spec hash/code sha256/seed=42/env 指纹；**21/21 replay match** | **PASS** |
| 3 | Result → Evidence explicit binding | 21/21 Evidence→Result 引用 + hash 一致；每 Execution ≤1 Result | **PASS** |
| 4 | Evidence → Claim traceable support | 9 Claim 全部经 Evidence→Result→Execution→Spec 闭合 | **PASS** |
| 5 | Failure → downstream invalidation | G5 语义全图强制；失效路径由 selftest 注入缺陷与门禁两次抓错实证 | **PASS** |
| 6 | Evidence-aware claim adjudication | 9 Claims：**5 supported / 4 refuted / 0 unresolved**，判定均由实测谓词驱动 | **PASS** |

第 6 项强调：**4 条 Claim 被驳回不是实验失败，而是判定能力真实工作的直接证据。**

## 2. 证据链

正向（生成）：

```text
MODEL_ARTIFACT (frozen, sha256)
      ↓ 1:1 provenance (G1)
ExperimentSpec ×6 (C0×3 + C1×3)
      ↓ deterministic execution record (G2/G3)
Execution ×21 (code_sha256, seed 42, logs)
      ↓ explicit result binding (G3)
Result ×21 (status=valid, replay 21/21)
      ↓ evidence binding (G4)
Evidence ×21 (9 supports + 12 characterizes)
      ↓ traceable support (G4/G5/G7)
Claim ×9 → SUPPORTED ×5 / REFUTED ×4
```

反向（定位，以一条被驳回的 Claim 实测走查）：

```text
P14-CLM005 [refuted]  n* 对 p 的弹性为正？
  └─ P14-EVI008 (supports) ← P14-RES008 (valid, replay OK)
       └─ P14-EXE008 (completed, EXP-2024B-C0-1, code q2024B.py sha256:20c4…)
            └─ P14-SPEC003 (2024_B / C0)
                 └─ 冻结 artifact 2024_B_B1_F.json (sha256 a808a0f7…)
```

任一 Claim 的判定都可以在五步内落到冻结模型与被哈希的实验代码。这是本 Pilot 验证的核心差异能力：**传统 Agent pipeline 的终点通常是 Result；本 Harness 的终点是 Evidence-aware Claim，且反向可定位到冻结模型与代码。**

## 3. 判定三分法与结果清单

状态学（RUNBOOK v1.1 增补，对未来 run 生效）：

```text
SUPPORTED  = Evidence 满足 Claim 的支持条件
REFUTED    = Evidence 与 Claim 的预期关系冲突
UNRESOLVED = 当前 Evidence 不足以支持或驳回（≠ 反证；门禁强制至少绑定 1 条 Evidence）
```

本轮结果（0 UNRESOLVED）：

| Claim | 判定 | 实测 |
|---|---|---|
| CLM001 M3 策略安全到达率 ≥ 0.90 | **SUPPORTED** | P_safe_mc = 1.0/1.0/1.0 |
| CLM002 O1 双口径最优策略一致（≥0.95） | **REFUTED** | policy_overlap_ratio = 0.577 |
| CLM003 极端坏天气下 C1 存在违反风险 | **REFUTED** | c1_violation_worst = 0（r0 富余使约束不触界） |
| CLM004 M1 泊松近似有效域 ≥ n=100 | **SUPPORTED** | approx_valid_boundary = 1000（全 N） |
| CLM005 n* 对 p 弹性为正 | **REFUTED** | elasticity_p = −0.464（(N−n)·P(miss) 权衡反转） |
| CLM006 超几何 gap 随 N 单调收敛 | **REFUTED** | gaps = [4.0, 19.5, 17.9] 非单调 |
| CLM007 CLR 对下游性能非负贡献 | **SUPPORTED** | 1.000 vs 0.950（+5.0pp） |
| CLM008 判别准确率满足 85% 标准 | **SUPPORTED** | CV 1.000 ± 0.000 |
| CLM009 ≤10% 噪声衰减 ≤ 10pp | **SUPPORTED** | 衰减 0.000 |

## 4. 禁止过度宣称（Mandatory）

本 Pilot 验证的是 **Model → Experiment → Evidence 链路的完整性、可追溯性、确定性与 Claim 判定能力**；它**不**证明：

1. Harness 能自动设计高质量科研实验；
2. 生成的实验具有普适科学有效性；
3. 以下任何数字可升级为一般性科学结论——全部严格限定在 P14-20260907-01 场景基线（executor-defined、随代码 sha256 冻结）内：
   - `P_safe = 1.0`：pilot 场景 r0=40 资源富余，仅说明该场景下 MDP 策略行为，不代表真实沙漠穿越的安全水平；
   - `n* 对 p 弹性 −0.464`：是 M2 成本结构在 N=1000/c_def=50 场景下的局部性质，且实验使用 M1 的二项精确式；
   - `超几何 gap 非单调`：仅测 N∈{50,100,200} 三点，不构成对收敛性的统计结论；
   - `CLR +5pp`：在**合成成分数据**（RandomState 42，3 类 Dirichlet）上测得，不是真实玻璃数据（仓库无 2022_C 附件）；阈值判定（CV=1.0）受合成数据可分性影响。
4. C0 与 C1 的对照**不构成效果结论**（PREREG 明确 out of scope）；本轮 C1 相对 C0 的差异仅为 checklist 驱动的组织性实验增补。

## 5. 威胁与局限

- Claim 谓词与阈值由执行体作者定义（构建器内嵌），门禁只强制"判定必须与谓词和数据一致"，不判定谓词本身的科学合理性；
- 2020_B/2024_B 的场景基线为 executor-defined（真实题目参数未入库）；2022_C 使用合成数据集；
- Evidence 解释文本由模板嵌入实测数值生成，模板为作者一次性定义；
- G5 失效传播在本轮正式图中未触发（无失败执行）——语义正确性由 selftest（9 类注入缺陷）与门禁开发期两次抓错实证；
- 单评委、单轮、无评分者信度（本轮无 PQ 类主观评分，全部为机械谓词）。

## 6. 协议增补记录

- RUNBOOK v1.1（P14.4 收口修订）：Claim 状态新增 `UNRESOLVED`（含门禁强制：unresolved 必须绑定 ≥1 Evidence；禁止把证据不足误用作反证）；schema 与 gate 同步；selftest 9/9 PASS；本轮 run 回归 GATE PASS（状态不受影响）。

## 7. 正式状态

```text
P13-3D   CLOSED（negative but informative）
P14.1    CLOSED
P14.2    PASS
P14.3    PASS
P14.4    PASS（本报告）—— P14 第一轮 pilot 收口
RC-S1    GREEN / READY（16 波认知执行等配额开关）
RC-S2    BLOCKED（等用户科研问题）
RC-S3    PASS（boundary 级）
```

后续轮次的候选方向（均须新一轮预注册，不改本轮判定）：真实附件数据接入后重测 2022_C；C0/C1 对照升级为带效果判定的正式实验；组织质量仪器（relation/organization preservation）。
