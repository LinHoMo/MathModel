# 实例反馈审计与闭环报告 / Projects Feedback Audit

> 目的：以 `projects/` 下三个真实交付实例（cumcm2024a / cumcm2026a / cumcm2026b）
> 为证据，审计实例侧缺陷并把结论**反馈**为 harness 侧修复，形成
> 「前馈（harness → 实例）+ 反馈（实例 → harness）」双向闭环。
> 本文件是这次审计的结论真源；机器数字以 `docs/STATUS.md` 为准。

## 0. 方法与判据

- 判据一：**实例必须能被 harness 自己的工具读取**。harness 的端到端指标工具是
  度量能力的唯一入口；读不动实例 = 反馈环断开（度量不可能发生）。
- 判据二：**实例状态是派生视图**。`runtime/state/reconcile.py` 明确
  「status.json 只能由 registry/graph 重新派生」；实例不得手写流程状态。
- 判据三：**登记类型必须活跃**。退役类型会被登记簿静默跳过，交付物随之丢失。
- 判据四：**不做真值导向**。不为了抬高指标而编造方法选型/创新声明；未闭合项
  如实留空并登记为后续任务。

### 复现命令

```
py -3.12 -m pytest tests -q
py -3.12 src/modeling_harness/cli/validate.py
py -3.12 src/modeling_harness/cli/catalog_check.py --check
py -3.12 src/modeling_harness/cli/catalog_check.py --check-terminology
```

实例侧对账（只读）：

```
py -3.12 -c "import sys;sys.path.insert(0,'src');
from modeling_harness.runtime.state.reconcile import reconcile;
print(reconcile('projects/cumcm2024a'))"
```

## 1. 实例侧发现（审计前实测）

| 编号 | 缺陷 | 证据 | 影响 |
|---|---|---|---|
| F1 | status.json 是**扁平**结构（`problem` / `questions` 挂顶层，无 `state` 包裹） | 三实例 3/3 命中 | 端到端指标工具在取 `state` 键时抛 KeyError，**三个实例全部读不动** |
| F2 | 维度取值非法：`problem.status = "parsed"` 不在 `DIMENSION_STATES` | 三实例 3/3 | 投影与 Runtime 契约不一致；任何严格校验都会拒收 |
| F3 | 登记退役 artifact 类型 `narrative`（模型描述文档） | 三实例各 1 个 `MH-NARRATIVE-0001` | 登记簿加载时静默跳过 → 该交付物在工具视图中消失 |
| F4 | 子问题未落为独立 question artifact：每实例仅登记 1 个容器 artifact | 2024a 容器内含 5 问、2026a/b 各 4 问 | 分解覆盖指标按 artifact 计数 → 2024_A 仅 1/5 = **20.0** |
| F5 | 模型仅登记**指针**（payload 指向模型表示文件），未内联契约字段 | `data` 无 `ir_version`、`model_family` 非结构体 | 结构检查判为 legacy_pointer → 模型结构校验不可用 |
| F6 | payload 路径悬空 | 2024a：题面指向不存在的文件、模型描述与模型表示指向不存在的子目录路径 | 交付物溯源断链 |
| F7 | 实例字段命名不一致（2024a 用带历史后缀的项目名） | 与 2026a/b 命名不同 | 跨实例工具按名字聚合时不一致 |

补充：三个实例由**项目内确定性脚本**直接拼装状态，未经过 Runtime 会话引擎。
这不是错误（脚本是确定性真源），但因此绕过了运行时的状态契约，直接导致 F1–F3。

## 2. harness 侧修复（反馈落地）

| 编号 | 修复 | 位置 | 对应发现 |
|---|---|---|---|
| H1 | 新增**问题理解层**（ADR-0008）：生产路径在无外部注入时从题面确定性派生
子问题 + 问题类型 + 检索特征；移除把任意题硬编码为评价类的回退；无特征时
选型如实 BLOCKED，不冒充 | `docs/decisions/ADR-0008-problem-understanding-layer.md`
+ 运行时问题画像模块 + 会话/处理器接线 | 前馈能力缺口（历史根因） |
| H2 | 新增门禁「实例状态契约」：校验 status.json 为多维投影、维度取值合法、
登记类型全部活跃、payload 路径不悬空 | `src/modeling_harness/cli/validate.py` | F1/F2/F3/F6 |
| H3 | 状态 schema 与 Runtime 对齐：把已退役的 `narrative` / `paper` 从
**必填**维度降级为「容忍读取的历史维度」并注明退役原因 | `src/modeling_harness/schemas/v3/state/status.schema.json` | F3 |
| H4 | 新增投影写出工具：项目脚本先落内容真源，再由 `ProjectState.refresh_from`
派生流程投影（唯一入口），不再手写 status.json | `scripts/state_projection.py` | F1/F2 |
| H5 | 修订 `docs/architecture/RUNTIME_CONTRACTS.md` 治理例外表 + ADR 索引 | 文档 | H1 授权留痕 |

H2 是本次最有价值的结构性反馈：它在修复后以硬门禁形式存在，**同类缺陷今后无法
再次静默进入交付**。

## 3. 实例侧修复与实测对照

| 指标 / 检查 | 修复前 | 修复后 |
|---|---|---|
| 端到端指标工具可读性 | 三实例全部 KeyError | 三实例全部可算 |
| 状态对账（reconcile） | 无法执行（投影缺 state） | 三实例 **ok = True，problems 为空** |
| 登记退役类型告警 | 三实例各 1 条 | **0 条**（告警视为错误的严格模式下通过） |
| 子问题 artifact 数（2024a / 2026a / 2026b） | 1 / 1 / 1 | **5 / 4 / 4** |
| 分解覆盖（2024_A，对照基准 5 问） | **20.0** | **100.0** |
| 模型结构检查 | legacy_pointer（不可评估） | **PASS**（三实例） |
| 空壳 artifact 排除数 | 存在空壳计入 | **0**（无可评分空壳） |
| 交付物溯源 | 存在悬空路径 | 全部路径可解析 |
| validate 门禁 | 45 通过 | **46 通过 / 0 失败 / 0 警告** |
| 测试套件 | 600 passed | **628 passed** |

前馈产物：三实例各写入 `artifacts/data/problem_understanding.json`（问题理解层确定性派生的
子问题 + 类型 + 检索特征快照），作为生产路径的检索输入留痕。该快照派生的子问题
数与登记簿中登记的子问题数一致（5/4/4），构成一条独立的一致性信号。

## 4. 仍未闭合（如实声明）

| 项 | 现状 | 原因 | 建议 |
|---|---|---|---|
| 方法结构对齐 | 不可用（未做方法卡选型） | 实例未登记方法卡 `card_id`；且基准的允许结构词表
（几何建模 / 微分方程 / 优化 / 仿真）与方法卡家族词表**无交集** | 补登记方法卡选型，
或为方法卡目录补齐上述家族；这是**知识库缺口**而非实例缺陷 |
| 实验有效性 | 0.0 | 结果未打稳健性标签、未登记多种子运行记录 | 实例脚本补稳健性证据；或明确指标口径为「有则计」 |
| 创新性 | 0.0 | 未声明创新模式 | 由建模者声明，不代填 |
| 2026_A / 2026_B 分解与方法指标 | 不可算 | 基准题库暂无这两题的真值卡 | 补真值卡后可度量 |
| `engine_progress.json` | 不写入 | 实例非引擎运行，不虚报节点完成（保持如实） | 若改由会话引擎运行则自动产生 |

## 5. 结论

1. 三个实例此前**不可被 harness 度量**，反馈环在度量入口处即断开；根因是实例
   绕过运行时状态契约（F1–F3）与子问题未落为实体（F4）。
2. 修复后实例可读、可对账、可度量；分解覆盖由 20.0 提升到 100.0，模型结构检查
   由不可评估变为 PASS。
3. harness 侧新增硬门禁（H2）+ 投影写出唯一入口（H4）+ schema 对齐（H3），把
   本次发现固化为**结构性防护**，同类缺陷不再复发。

## 6. 附录：修复后机器实测完整输出

### 6.1 四件套门禁输出

| 门禁 | 实测输出 | 命令 |
|---|---|---|
| 项目级校验 | **46 通过 / 0 失败 / 0 警告**（含新增「实例状态契约」：3 个活跃实例一致） | `py -3.12 src/modeling_harness/cli/validate.py` |
| catalog 三方一致 | **OK** | `py -3.12 src/modeling_harness/cli/catalog_check.py --check` |
| 术语零残留 | **OK**（production 零残留） | `py -3.12 src/modeling_harness/cli/catalog_check.py --check-terminology` |
| 测试套件 | **628 passed / 0 failed**（600 基线 + 28 新增） | `py -3.12 -m pytest tests -q` |

### 6.2 八项指标完整输出（按实例）

「不可算」= 该指标的先决输入缺失（真值卡 / 方法卡选型 / 外部评分），如实为 None，
不参与均值；结构与详情一并列出以便复核。

| 指标 | cumcm2024a | cumcm2026a | cumcm2026b |
|---|---|---|---|
| 分解覆盖 decomposition | **100.0**（基准 5 问，产出 5 问） | 不可算（无真值卡；产出 4 问） | 不可算（无真值卡；产出 4 问） |
| 方法结构对齐 | 不可算（未做方法卡选型；词表无交集） | 不可算（同左） | 不可算（同左） |
| 模型正确性 model_correctness | 不可算（外部评分缺失）· **结构检查 PASS** | 同左 | 同左 |
| 实验有效性 experiment_validity | 0.0（5 结果，0 稳健性标签，0 多种子） | 0.0（4 结果，0/0） | 0.0（4 结果，0/0） |
| 验证可靠性 validation_reliability | **100.0**（8/8 声明被支撑，模型表示在场） | **100.0**（5/5） | **100.0**（5/5） |
| 创新性 innovation | 0.0（未声明创新模式） | 0.0 | 0.0 |
| 写作完整性 writing_completeness | **100.0**（模型表示 + 描述文档 + Mermaid 全在场） | **100.0** | **100.0** |
| 端到端 end_to_end | 不可算（无评分 rubric） | 不可算 | 不可算 |

结构检查明细（三实例一致）：`structural_pass = True`，参与检查的模型 =
`MH-MODEL-0001` + `MH-MODEL_IR-0001`（内联契约字段），objectives / constraints /
variables 三字段全部非空；空壳 artifact 排除数 = 0（全登记簿 0 空壳）。

### 6.3 逐问覆盖（子问题是否全部登记）

| 实例 | 已登记子问题（全部 validated） | 每问挂载 |
|---|---|---|
| cumcm2024a | **Q1–Q5（5/5 问全写）** | 每问 1 实验 + 声明（Q1:2 / Q2:2 / Q3:1 / Q4:2 / Q5:1，共 8） |
| cumcm2026a | **Q1–Q4（4/4 问全写）** | 每问 1 实验 + 声明（Q1:2 / Q2:1 / Q3:1 / Q4:1，共 5） |
| cumcm2026b | **Q1–Q4（4/4 问全写）** | 每问 1 实验 + 声明（Q1:1 / Q2:1 / Q3:2 / Q4:1，共 5） |

每个子问题都有独立 question artifact（题面语义 ID Q1..Qn）、实验、结果与支撑声明；
`reconcile` 三实例 `ok = True` 且问题清单为空（投影与内容真源逐项一致）。

### 6.4 适配后的实例目录结构

与 `new_project.py` 的标准布局（inputs / state / artifacts / model + 项目根交付物）
逐项一致；前馈快照落在 `artifacts/data/`（Artifact 落盘区），不引入布局外目录：

```
projects/cumcm<年份><题号>/
├── inputs/                    # 赛题原文（唯一输入）
│   └── problem.txt
├── state/                     # runtime 状态（由 scripts/state_projection.py 派生）
│   ├── registry.json          #   Artifact 登记簿（含 Q1..Qn 与 MH-MODEL_IR-0001）
│   ├── evidence_graph.json    #   证据关系
│   ├── decision_log.json      #   决策记录
│   ├── status.json            #   流程投影（refresh_from 派生，唯一入口）
│   └── runs/
├── artifacts/
│   ├── data/
│   │   └── problem_understanding.json   # 前馈快照（问题理解层确定性派生）
│   ├── code/                  # 建模与状态构建脚本
│   └── results/               # 结果文件（xlsx 等）
├── model/                     # 交接文档与附加说明（README.md）
├── HANDOFF.md                 # 实例交接（根）
├── model_ir.json              # MODEL_IR（根，契约交付物）
├── model.md                   # 模型描述文档（根，含 Mermaid）
└── all_results.json           # 结果台账（根）
```
4. 方法结构对齐、实验有效性、创新性仍为真实缺口，已在 §4 登记为后续任务，
   不通过编造声明来掩盖。
