# Three-Arm Experiment Protocol — 方法卡有效性实验（P15.2 前置）

> 状态：DRAFT v0.1（待 B0-R2 完成后定稿） ｜ 定位：验证 Model Construction Knowledge 是否真正改善模型构造
> 前置：B0-R2（校准后基线）必须已完成，测量仪器有效（execution/artifact/evaluator 三真）
> 对应治理条款：Research-layer calibration ≠ Agent capability intervention；三臂实验只回答 instrument 效度问题

---

## 1. 研究问题

> Method Cards（Model Construction Knowledge Units）是否真正改善 Agent 的模型构造质量？

不是问"卡多不多"，而是问：

| 问题 | 对应指标 |
|---|---|
| 卡是否帮助识别正确的问题结构？ | structure identification accuracy |
| 卡是否帮助构造更完整/更恰当的模型？ | construction alignment / construction quality |
| 卡是否防止乱用方法？ | applicability precision（anti-pattern 触发率） |
| 卡是否帮助验证与失败诊断？ | validation utility |

## 2. 三臂设计

固定条件（全部相同）：**同一题目、同一 LLM、同一 token 预算、同一评估器**。

| 臂 | 条件 | 含义 |
|---|---|---|
| **A: LLM alone** | 无知识库接入，纯提示词做题 | 基线：LLM 自由建模能力 |
| **B: LLM + cards** | 接入 Model Construction Knowledge（19 卡含 structure_signals） | 知识约束/先验是否提升构造 |
| **C: LLM + cards + cases** | B + 实例化建模案例（Case/Experience 层） | 案例先验是否进一步增益 |

## 3. 题目选择（建议）

从已冻结的 5 题中选 3 题，覆盖三个不同 model construction regime：

| 题 | regime | 对应卡 |
|---|---|---|
| 2020_B | 离散序贯决策 | mc-dp |
| 2018_A | 连续时空场 | mc-numerical-pde |
| 2019_C | 随机服务系统 | mc-queuing-theory |

（2024_A 因 B0 测量历史污染，建议等其 Fresh B0 稳定后再纳入；2022_C 数据决策类暂无专属卡，可作 out_of_catalog 观察臂）

## 4. 执行协议

每题 × 3 臂 × 3 次重复 = 9 次运行/题，3 题共 27 次。

```
题目 i
├── A 臂（alone）: 3 次重复（seeds 42/43/44）
├── B 臂（+cards）: 3 次重复
└── C 臂（+cards+cases）: 3 次重复
```

- 每次运行独立生成：question artifact → model artifact → experiment artifact → result artifact → evidence artifact → claim
- 全部走 execution_gate（executor_type=external_agent，latency>0，payload 非空）
- 全部走同一 evaluator（e2e_metrics，固定版本 hash）

## 5. 指标与判定

### 5.1 主指标

| 指标 | 定义 | 判定 |
|---|---|---|
| structure identification | Agent 识别的问题结构是否与 gold allowed_modeling_structures 对齐 | 对齐=1，部分=0.5，错=0 |
| construction alignment | model artifact 的变量/约束/目标/机理是否覆盖 gold key_variables/key_constraints | 覆盖比例 |
| construction quality | jsonschema 结构完整 + mechanism 明确 + 无 anti-pattern 触发 | 0-100 |
| decomposition coverage | 语义对齐覆盖（非 artifact 计数） | 0-1 |
| evidence validity | claim→evidence→result→experiment 链完整率 | 0-1 |

### 5.2 判定规则

```
A < B 且 A < C：方法卡有增益
B ≈ C > A：cases 无额外增益（知识已足够）
B < C：cases 有增量价值
B ≤ A 且 C ≤ A：方法卡无增益 → 仪器效度存疑 → STOP 检查知识质量
```

### 5.3 反证检查（必须主动找）

- 是否存在"卡误导"案例（B/C 臂因卡而错误构造，A 臂反而正确）？
- 是否存在 out_of_catalog 正确建模被知识库压制？→ 检查 LLM 是否被允许 REJECT 卡

## 6. 统计要求

- 每次运行固定 seed（42/43/44），报告均值 ± 标准差
- 三臂差异用非参数检验（配对样本量小，不假设正态）
- 差异阈值：≥10 分或 ≥0.1 覆盖率才报"有增益"，否则报"无显著差异"
- **禁止**事后调 threshold 使结果"好看"

## 7. 混淆控制

| 混淆源 | 控制 |
|---|---|
| token 预算差异 | 三臂固定相同 max_tokens 上限 |
| prompt 差异 | 三臂用同一 base prompt，仅 B/C 追加知识注入段 |
| 题目顺序效应 | 随机化题目顺序 |
| LLM 随机性 | 固定 seed + 3 重复 |
| evaluator 漂移 | 冻结 e2e_metrics commit hash，实验期间不改 |

## 8. 输出

- `research/P15/experiments/three_arm/protocol.md`（本文件）
- 每次运行 manifest（走 register_external_artifact 契约）
- `research/P15/reports/THREE_ARM_REPORT.md`：三臂对比表 + 增益判定 + 反证案例 + 仪器效度结论

## 9. 完成标准

1. 27 次运行全部真实执行（无空壳、无 latency≈0）
2. 三臂对比表产出，含均值±std
3. 明确回答"方法卡是否真正有用"（含反证）
4. 若 B≤A：停止扩卡，先修知识质量（进入 P1 复审循环）

## 10. 与路线图的关系

```
B0-R2（校准后基线）
   ↓
三臂实验（方法卡效用验证）   ← 本协议
   ↓
判定：卡有用？ 
   ├─ 是 → 决定 P1 卡（game-theory/network-flow/milp/ode）是否扩
   └─ 否 → 修知识质量 → 重跑三臂
   ↓
P15.2 Model Construction 主能力程序
```
