---
name: programmer
description: "编程手编排器：串联 6 个编程 agent（模板选择 → 代码实现 → 测试 → 结果验证 → 护栏 → 哈希审计），消费 MODEL_SPEC.md 产出 CODE_DELIVERABLES.md 与 figures/all_results.json。"
---

# Programmer Skill

## Role

程序员（Programmer）：负责代码实现、测试验证、结果输出。本文件为手级编排器，按 UTG 六层机制串联 6 个 agent 完成交付，不再内联单一流程。

## Contract

读取 `MODEL_SPEC.md`（上游建模手输出），输出 `output/CODE_DELIVERABLES.md`（代码交付物清单）供 Writer 读取。

## Agent Orchestra

本手由 6 个 agent 串联完成，每个 agent 承载 UTG 一层，输出后自检通过方可进入下一 stage：

| 序号 | agent | utg_layer | stage | 职责 | 输出 |
|------|-------|-----------|-------|------|------|
| 1 | template-selector | L1 | 1 | 根据 MODEL_SPEC 选代码模板，输出结构化计划 | work/template_plan.json |
| 2 | code-implementer | L2 | 2 | 实现代码，类型制导 | code/*.py |
| 3 | test-runner | L3 | 3 | 单元测试 + 集成测试 + 契约/过程验证 | work/test_report.json |
| 4 | result-verifier | L4 | 4 | 数值验证 + 灵敏度 + 跨方法交叉验证 | work/result_validation.json |
| 5 | guardrails-checker | L5 | 5 | 运行时护栏（禁用词/占位符/AI痕迹/权限） | work/guardrails_report.json |
| 6 | hash-auditor | L6 | 6 | 哈希链 + 错误归因 + 规则迭代，输出交付物 | output/CODE_DELIVERABLES.md + work/audit_chain.json |

串联顺序：template-selector → code-implementer → test-runner → result-verifier → guardrails-checker → hash-auditor。各 agent 定义见 `core/Programmer/agents/<name>/SKILL.md`。

## Stage Gates

每个 agent 输出后须满足的自检通过条件，任一失败在本手内回退到对应 agent：

- **stage 1（template-selector）**：template_plan.json 为有效 JSON；每子问题有 template_path 指向真实模板；函数签名 `solve_problem_N(params: dict) -> dict`；file_plan 路径以 `code/` 开头。
- **stage 2（code-implementer）**：`py code/main.py` 可启动；含 `np.random.seed(42)`；每个 solve_problem_N 返回 `{values,units,validation}`；`figures/all_results.json` 生成；type_system 自校验通过。
- **stage 3（test-runner）**：单元/集成测试 0 failures；contract_checker 通过；ProcessVerifier.verify_programmer_output() 通过；all_results.json 有效且每子问题有结果与单位。
- **stage 4（result-verifier）**：与 MODEL_SPEC 预期误差 < 5%；约束满足；灵敏度分析完成；多次运行 CV ≤ 10%（P6）；cross_model_checker 与 symbolic_verifier 通过。
- **stage 5（guardrails-checker）**：无禁用词/占位符/AI 痕迹/内部路径；无权限越界；种子固定（P1）、异常处理（P5）、数据校验（P8）覆盖。
- **stage 6（hash-auditor）**：所有产物哈希入链；stage_gate L1-L5 全部放行；CODE_DELIVERABLES.md 符合 `core/schemas/code_deliverables.schema.json`；数值与 all_results.json 一致（P2）；运行说明完整（P9）。

## Env Bindings

本手通过 `core/env/loader.py` 读取可调参数（agent 内通过 `from core.env.loader import get` 引用）：

| 参数 | 点号路径 | 默认值 | 消费 agent | 用途 |
|------|----------|--------|-----------|------|
| 随机种子 | `code.random_seed` | 42 | template-selector / code-implementer | 固定 `np.random.seed(42)`（P1） |
| 多次运行次数 | `code.multi_run_count` | 5 | result-verifier | 启发式算法多次运行稳定性（P6） |

## UTG Layer Mapping

UTG 六层防御由以下 agent 承载（与 `core/Programmer/laws/rules.md` 的层次映射一致）：

| UTG 层 | 机制 | 承载 agent | 拦截目标 |
|--------|------|-----------|---------|
| L1 | 结构化输出 | template-selector | template_plan.json 字段缺失/路径歧义 |
| L2 | 文法与类型制导 | code-implementer | 语法错误/类型不匹配/签名不符 |
| L3 | 过程验证 | test-runner | 代码不可运行/契约不齐/结果缺失 |
| L4 | 异构验证 | result-verifier | 数值错误/不稳定/约束违反 |
| L5 | 运行时护栏 | guardrails-checker | 禁用词/占位符/AI痕迹/权限越界 |
| L6 | 事后验证 | hash-auditor | 产物篡改/规则违反/schema 不符 |

## Laws

详见 `core/Programmer/laws/rules.md`

### P1: 代码必须设置随机种子，保证可复现
- **防御层次**: L5 运行时护栏
- 必须包含 `np.random.seed(42)` 或等效设置
- 随机算法要多次独立运行（≥5次），报告均值和标准差
- 保存环境、输入、参数、代码入口和输出哈希

### P2: 所有数值必须可追溯到 figures/all_results.json
- **防御层次**: L1 结构化输出
- 所有论文会引用的数值必须能追溯到 `figures/all_results.json`
- 不要在论文阶段重新估算或换一套四舍五入口径
- 结果文件应记录：关键参数、核心数值、约束检查、灵敏度或鲁棒性结果

### P3: 代码文件必须放在 code/ 目录，图表放在 figures/，表格放在 tables/
- **防御层次**: L3 过程验证
- 代码中所有文件保存操作必须使用目录前缀的相对路径
- 不得直接写文件名
- 不得创建无产物的空目录

### P4: 每个代码文件必须有模块docstring和函数docstring
- **防御层次**: L3 过程验证
- 模块级docstring说明文件用途
- 函数docstring说明参数、返回值、异常
- 关键代码块添加注释

### P5: 必须处理异常情况（文件不存在、数据格式错误等）
- **防御层次**: L5 运行时护栏
- try-except捕获异常
- 提供有意义的错误信息
- 优雅降级处理

### P6: 启发式算法必须多次运行（≥5次），报告均值和标准差
- **防御层次**: L2 工具调用
- 随机算法结果具有随机性
- 多次运行评估稳定性
- 若标准差/均值 > 10%，说明优化不稳定，须增加种群或迭代次数

### P7: 优化问题必须先保证可行解，再优化目标值
- **防御层次**: L2 工具调用
- 硬约束过多导致可行域为空时，不得直接报"无解"
- 改为软惩罚：f = 原目标 + λ·Σ(max(0, -约束)²)
- 优化变量上界必须等于物理可行域上界

### P8: 数据读取后必须检查编码、列名、形状、缺失值
- **防御层次**: L5 运行时护栏
- 检查文件编码（UTF-8/GBK等）
- 检查列名是否正确
- 检查数据形状
- 检查缺失值和异常值

### P9: CODE_DELIVERABLES.md 必须包含所有代码文件的运行说明
- **防御层次**: L1 结构化输出
- 每个代码文件的功能说明
- 运行命令
- 预计运行时间
- 依赖包列表

## Knowledge

- `core/knowledge/methodology/` - 12个方法论文档（数值/优化/统计/时序/ML）
- `core/Programmer/knowledge/code-templates/` - 46个代码模板（15个子目录）
- `core/knowledge/validation/` - 验证模块（contract_checker / cross_model_checker / error_attribution / guardrails / hash_chain / incremental_checker / invariant_tracker / output_validator / permission_guard / process_verifier / rule_iterator / stage_gate / symbolic_verifier / trust_domain / type_system）
- `core/Programmer/agents/` - 6 个 UTG agent（template-selector / code-implementer / test-runner / result-verifier / guardrails-checker / hash-auditor）
- `core/Programmer/laws/rules.md` - 编程手铁律（P1-P9）
- `core/schemas/code_deliverables.schema.json` - 结构化输出Schema（L1）
- `core/env/loader.py` - 环境变量加载器（`get("code.random_seed")` / `get("code.multi_run_count")`）

## Output Contract

输出 `output/CODE_DELIVERABLES.md`（由 hash-auditor 生成），格式见 `core/Programmer/templates/CODE_DELIVERABLES_TEMPLATE.md`，字段须符合 `core/schemas/code_deliverables.schema.json`。

**输出有效性条件**（全部满足才算输出成功）：
1. CODE_DELIVERABLES.md 存在且非空，符合 schema
2. 代码文件存在且可运行（`py code/main.py` 无错误）
3. all_results.json 存在且为有效JSON
4. 随机种子已设置（seed=42）
5. 每个子问题有对应的结果，结果有单位标注
6. 测试全部通过（0 failures）
7. 护栏检查通过（无禁用词、无占位符、无AI痕迹、无权限越界）
8. 多次运行 CV ≤ 10%（P6）
9. 哈希链完整，stage_gate L1-L6 全部放行

## Iteration

任一 stage gate 失败时在本手内回退：
- L1 失败 → 回 template-selector 重选模板
- L2 失败 → 回 code-implementer 修复实现/类型/签名
- L3 失败 → 回 code-implementer 修复后重跑 test-runner
- L4 失败 → 回 code-implementer 修正算法/参数/种群后重跑 L3-L4
- L5 失败 → 回 code-implementer 清理护栏问题后重跑 L3-L5
- L6 失败 → schema 不符就地补；数值不一致/产物篡改回退到对应 agent

循环直到 6 层全绿且 CODE_DELIVERABLES.md 通过 schema 校验。
