# External-Agent Execution Interface

> **架构边界声明**：Harness ≠ Agent。本项目只做 Harness，不做 Agent。真正的认知工作（读题/建模/求解/写结论）由外部 Agent（Doubao/GPT/Claude/人）在 harness 之下完成。`core/runtime` 永远不 import openai/anthropic 或内嵌 LLM 执行器。"整个 core 零 LLM 调用"不是缺陷，是设计要求。

## 1. 两类执行器区分

| executor_type | 来源 | 用途 | 能力评分 | Gate 退出码 |
|---|---|---|---|---|
| `dry_run` | DefaultNodeExecutor 确定性桩 | 流程演练、测量链路自检 | **永远 INVALID** | 2 (INVALID/SYNTHETIC) |
| `synthetic` | mock_llm_executor 模拟生成 | 模拟数据、管道测试 | **永远 INVALID** | 2 (INVALID/SYNTHETIC) |
| `external_agent` | 仓库外真实 Agent 产出并登记 | 真实建模/求解/写作 | 正常评分 | 0/1/2 (按检查结果) |

### 注入点

- **Run record**：`projects/<项目>/state/runs/*.json` 顶层 `executor_type` 字段 + `provenance.executor_type`
- **Artifact metadata**：`projects/<项目>/state/registry.json` 中每个 artifact 的 `provenance.executor_type` 字段

### 旧项目标注

```powershell
# B0 旧项目（DefaultNodeExecutor 确定性桩）
py -3.12 research/P15/measurement_recovery/mark_executor_type.py \
    --project p151-2024a --type dry_run

# mock B0-R2（mock executor 生成）
py -3.12 research/P15/measurement_recovery/mark_executor_type.py \
    --project p151-2024a-r2 --type synthetic

# 查看当前标注
py -3.12 research/P15/measurement_recovery/mark_executor_type.py \
    --project p151-2024a --list
```

## 2. ExternalArtifactManifest 契约

每个由外部 Agent 提交的节点产物必须附带 manifest，通过 `register_external_artifact.py` 登记。**外部 Agent 不得直接手写 registry.json。**

### 字段说明

| 字段 | 类型 | 必填 | 校验规则 |
|---|---|---|---|
| `executor_type` | string | 是 | 必须为 `external_agent` |
| `agent_identity` | string | 是 | `doubao` / `gpt` / `claude` / `human` / `other` |
| `model_version` | string | 是 | 非空；human 时填 `N/A` |
| `input_sha256` | string | 是 | 64位十六进制；必须与冻结题面 hash 匹配，不匹配直接拒绝（退出码2） |
| `node_id` | string | 是 | DAG 节点 ID，如 `model_construction` |
| `dag_position` | int | 是 | >= 0（0-indexed） |
| `prompt_or_skill_version` | string | 是 | 非空 |
| `artifact_schema_version` | string | 是 | 非空 |
| `started_at` | string | 是 | ISO 8601 |
| `finished_at` | string | 是 | ISO 8601，且 >= started_at |
| `latency_seconds` | float | 是 | > 0；< 1s 触发警告（疑似模板初始化） |
| `submitted_at` | string | 是 | ISO 8601 |
| `payload` | object | 是 | 非空 dict，过 artifact-type-specific schema |
| `reproducibility` | object | 否 | `seed` / `temperature` / `parameters` |

### 三层 Gate

1. **Schema 层**：JSON Schema 校验（`external_artifact_manifest.schema.json`）
2. **Non-empty / Structural 层**：必需字段非空、格式正确、latency > 0、payload 非空
3. **Semantic / Hash 绑定层**：`input_sha256` 与项目冻结题面匹配；artifact provenance 与 run record 绑定

### 2024_A 题面 hash

```
9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e
```

## 3. 提交入口（CLI）

### 用法

```powershell
py -3.12 research/P15/measurement_recovery/register_external_artifact.py \
    --project p151-2024a-r3 \
    --manifest path/to/manifest.json \
    [--input-sha256 9baf81fb...] \
    [--dry-run]
```

### 功能

1. 读取 manifest JSON
2. 校验 manifest（调用 `external_artifact_manifest.validate`）
3. 校验 `input_sha256` 与项目冻结题面匹配（省略时自动检测）
4. 将 artifact 写入项目 `registry.json`（正确的 artifact 格式，含完整 provenance）
5. 创建 run record（`executor_type=external_agent`，含 agent_identity、latency 等）
6. 更新 `evidence_graph.json`（添加 based_on 关系）
7. 更新 `decision_log.json`（model/decision 类型 artifact 添加决策记录）
8. 输出登记结果

### 退出码

| 退出码 | 含义 |
|---|---|
| 0 | 成功 |
| 1 | manifest 校验失败 |
| 2 | input hash 不匹配（错题面，直接拒绝） |
| 3 | 其他错误（项目不存在、IO 错误等） |

### 示例

```powershell
# 使用示例 manifest 登记（2024_A model_construction 节点）
py -3.12 research/P15/measurement_recovery/register_external_artifact.py \
    --project p151-2024a-r3 \
    --manifest research/P15/measurement_recovery/example_external_manifest.json

# 预检（不写入）
py -3.12 register_external_artifact.py \
    --project p151-2024a-r3 --manifest manifest.json --dry-run
```

## 4. Execution Authenticity Gate 判据更新

### executor_type 检测优先级

1. run record 顶层 `executor_type`
2. run record `provenance.executor_type`
3. 遗留字段推断（`mock_execution=true` / `execution_mode=mock` → synthetic；`model_provider=null` → dry_run）
4. registry artifact provenance 多数投票

### 对 synthetic/dry_run 执行

- 报告头部明确标注：`EXECUTOR_TYPE: SYNTHETIC / NOT A CAPABILITY RESULT`
- EAG-EX（executor_type 标注检查）PASS
- 所有 13 项 capability 检查标记为 **SKIPPED**（不是 PASS 也不是 FAIL）
- Overall verdict = **INVALID**
- 退出码 = **2**（即使所有检查都 PASS）
- `capability_result: false`

### 对 external_agent 执行

- 正常执行所有 13 项 EAG 检查
- 额外增加 3 项专属检查：
  - **EAG-14**：`agent_identity` 非空
  - **EAG-15**：`model_version` 非空（human 时 N/A）
  - **EAG-16**：artifact `input_sha256` 与 run record `input_hash` 绑定
- `capability_result: true`
- 退出码按检查结果：0=PASS, 1=FAIL, 2=INVALID

### 对 executor_type 缺失（旧项目）

- EAG-EX FAIL，警告 "executor_type 未标注，无法确认执行真实性"
- 建议运行 `mark_executor_type.py` 标注
- 正常执行 13 项 EAG 检查
- Overall verdict = **UNKNOWN**

### 运行示例

```powershell
# 对旧 B0（dry_run）验证
py -3.12 research/P15/measurement_recovery/execution_gate.py \
    --project projects/p151-2024a
# → Executor Type: dry_run, *** SYNTHETIC ***, SKIPPED=13, exit 2

# 对 mock B0-R2（synthetic）验证
py -3.12 execution_gate.py --project projects/p151-2024a-r2
# → Executor Type: synthetic, *** SYNTHETIC ***, SKIPPED=13, exit 2

# 对 external_agent 项目验证
py -3.12 execution_gate.py --project projects/p151-2024a-r3
# → Executor Type: external_agent, 17 checks (13+EAG-EX+EAG-14/15/16)
```

## 5. 外部 Agent 完整工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Agent Workflow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. 读题                                                          │
│     ├─ 获取冻结题面（inputs/cumcm2024A.txt）                     │
│     └─ 计算 input_sha256 = 9baf81fb...                          │
│                                                                   │
│  2. 逐节点产出（DAG 顺序）                                         │
│     ├─ problem_analysis      → problem artifact                  │
│     ├─ literature_search      → decision artifact                │
│     ├─ model_selection        → model artifact                   │
│     ├─ model_construction     → model artifact (含完整规格)       │
│     ├─ experiment_design      → decision artifact                │
│     ├─ experiment_execution   → experiment artifact              │
│     ├─ result_analysis        → result artifact                  │
│     ├─ evidence_build         → claim artifact                   │
│     └─ paper_sections         → paper_section artifacts          │
│                                                                   │
│  3. 每个节点产出后，构造 ExternalArtifactManifest                  │
│     ├─ 填写 executor_type=external_agent                         │
│     ├─ 填写 agent_identity / model_version                       │
│     ├─ 绑定 input_sha256（题面 hash）                             │
│     ├─ 填写 node_id / dag_position                               │
│     ├─ 填写 started_at / finished_at / latency_seconds           │
│     └─ payload = 实际产物内容                                     │
│                                                                   │
│  4. 通过 register_external_artifact.py 登记                        │
│     ├─ manifest 校验（schema + non-empty + latency）              │
│     ├─ input_sha256 与冻结题面匹配校验                            │
│     ├─ 写入 registry.json（含完整 provenance）                     │
│     ├─ 创建 run record                                            │
│     ├─ 更新 evidence_graph / decision_log                         │
│     └─ 退出码 0=成功, 1=校验失败, 2=hash不匹配, 3=其他错误        │
│                                                                   │
│  5. Gate 校验                                                      │
│     └─ execution_gate.py --project <项目>                         │
│         ├─ executor_type=external_agent                           │
│         ├─ 13 项 EAG + 3 项 external_agent 专属检查               │
│         └─ Artifact Integrity L1+L2                               │
│                                                                   │
│  6. Evaluator 测量                                                 │
│     └─ 仅当 executor_type=external_agent 且 gate PASS 时          │
│        才进入能力评分（capability scoring）                         │
│        synthetic/dry_run 永远 INVALID，不产出能力分                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## 6. 6c Real B0-R3 执行计划

### 目标

用真实外部 Agent（Doubao）完成 2024_A 题的完整建模流程，产出可测量的能力结果。

### 执行 Agent

- **Primary**: Doubao（doubao-1.5-pro 或最新版本）
- **备选**: GPT-4o / Claude 3.5（用于交叉验证）

### 执行步骤

1. **项目初始化**
   ```powershell
   py -3.12 core/tools/new_project.py p151-2024a-r3 \
       --competition cumcm --problem projects/p151-2024a/inputs/cumcm2024A.txt
   ```

2. **冻结题面 hash**
   ```
   input_sha256 = 9baf81fb40f82f776998540524a6f2fe45f232af621343e9ae30e5dd97dbd53e
   ```

3. **逐节点执行与登记**（DAG 顺序，每个节点一个 manifest）
   - 外部 Agent 读取题面 + 对应 SKILL/prompt
   - 产出节点产物
   - 构造 manifest（含真实 latency、agent_identity、model_version）
   - 通过 `register_external_artifact.py` 登记
   - 确认退出码 0

4. **Gate 校验**
   ```powershell
   py -3.12 research/P15/measurement_recovery/execution_gate.py \
       --project projects/p151-2024a-r3 --json b0r3_gate_report.json
   ```
   预期：executor_type=external_agent，EAG-14/15/16 PASS

5. **能力测量**
   - 仅当 gate PASS 后进入 evaluator
   - 对比 B0（dry_run）和 B0-R2（synthetic）的 INVALID 结果
   - B0-R3 应产出真实能力分数

### 测量对比矩阵

| 项目 | executor_type | Gate Verdict | 能力评分 | 用途 |
|---|---|---|---|---|
| B0 (p151-2024a) | dry_run | INVALID/SYNTHETIC | 不产出 | 流程演练基线 |
| B0-R2 (p151-2024a-r2) | synthetic | INVALID/SYNTHETIC | 不产出 | mock 数据对照 |
| B0-R3 (p151-2024a-r3) | external_agent | PASS/FAIL/INVALID | 真实分数 | 真实能力测量 |

## 7. 文件清单

| 文件 | 说明 |
|---|---|
| `external_artifact_manifest.py` | Manifest 数据类 + validate() + 序列化 + hash 绑定 |
| `external_artifact_manifest.schema.json` | JSON Schema 定义 |
| `example_external_manifest.json` | 示例 manifest（2024_A model_construction） |
| `register_external_artifact.py` | 外部 Agent 产物登记 CLI（唯一 sanctioned 入口） |
| `mark_executor_type.py` | executor_type 批量标注工具（旧项目兼容） |
| `execution_gate.py` | Execution Authenticity Gate（v2.0，含 executor_type 判据） |
| `EXTERNAL_AGENT_EXECUTION_INTERFACE.md` | 本文档 |

## 8. 设计决策

1. **不在 core 里造 LLM 执行器**：harness 保持 LLM-free，外部 Agent 通过 manifest + CLI 接入
2. **executor_type 作为一等公民**：run record 和 artifact provenance 双重标注，gate 强制检测
3. **synthetic 永远不进入能力评分**：不是"分数低"，而是"不适用"，用 SKIPPED + INVALID 明确区分
4. **input_sha256 硬绑定**：题面不对直接拒绝（退出码2），防止 Agent 在错题面上工作
5. **唯一登记入口**：外部 Agent 不得直接写 registry.json，必须通过 register_external_artifact.py
6. **minimal patch to core**：所有新代码在 research/P15/measurement_recovery/，不修改 v3.1.x core architecture
7. **向后兼容**：旧项目通过 mark_executor_type.py 标注，未标注时 gate 给出 UNKNOWN 警告而非崩溃
