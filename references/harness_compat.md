# 跨 Harness 行为约定

本文档定义 MathModelSkills 在不同 AI 运行时（Claude Code / Codex CLI / opencode / Cursor / Trae 等）下的统一行为协议。

## 核心原则

1. **状态外置**：所有执行进度、决策历史、中间产物路径写入文件系统（`work/state.json`、`work/decision_log.json`），不依赖模型上下文记忆。
2. **契约优先**：四手之间仅通过契约文件（`MODEL_SPEC.md`、`CODE_DELIVERABLES.md`、`PAPER_SPEC.md`）交互，不共享内部状态。
3. **门禁脚本化**：Self-Check 由 Python 脚本（`gate.py`、`score_artifact.py`、`validate.py`）判定，不依赖模型自评。
4. **入口统一**：任何运行时进入项目根目录，读取 `AGENTS.md` 或 `.codex-plugin/plugin.json` 即可开始执行。

## 状态文件规范

### `work/state.json`（单一事实源）

```json
{
  "version": "1.0",
  "project": "cumcm2024a",
  "created": "2026-09-01T10:00:00Z",
  "updated": "2026-09-01T12:30:00Z",
  "current": {"hand": "modeler", "agent": "method-matcher", "stage": 3},
  "completed": [
    {"hand": "modeler", "agent": "problem-parser", "stage": 1, "timestamp": "...", "output": "work/question_spec.json", "output_hash": "sha256:..."},
    {"hand": "modeler", "agent": "type-classifier", "stage": 2, "timestamp": "...", "output": "work/type_classification.json", "output_hash": "sha256:..."}
  ],
  "failed": [],
  "q_states": {},
  "ai_usage_ledger": {},
  "legacy": {},
  "decision_log_path": "work/decision_log.json"
}
```

### `work/decision_log.json`（决策日志，跨 harness 互通）

```json
{
  "project_name": "cumcm2024a",
  "created_at": "2026-09-01T10:00:00Z",
  "updated_at": "2026-09-01T12:30:00Z",
  "entries": [
    {
      "timestamp": "2026-09-01T10:15:00Z",
      "stage": "modeler/type-classifier",
      "agent": "type-classifier",
      "decision_type": "model_selection",
      "question": "赛题属于哪种题型？",
      "options": [
        {"label": "A: 物理机理", "description": "给出 PDE/ODE，求解物理场"},
        {"label": "B: 实验数据", "description": "给出实测数据，拟合参数/模型"},
        {"label": "C: 数据驱动", "description": "大量观测数据，预测/分类/聚类"},
        {"label": "D: 运筹优化", "description": "决策变量、目标函数、约束条件明确"},
        {"label": "E: 跨学科综合", "description": "多领域知识融合、无标准模型"}
      ],
      "choice": "A",
      "rationale": "题目明确给出热传导 PDE 和边界条件，属于物理机理建模",
      "confidence": 0.95,
      "alternatives_considered": ["B"],
      "time_spent_seconds": 45
    }
  ]
}
```

### `work/STATE.md`（可读镜像，供人工/agent 快速查看）

由 `state.py` 自动渲染，格式见 `state.py:render_md()`。

## 执行协议（五步循环）

所有 harness 统一遵循：

```
1. 读状态    python core/tools/state.py <项目> status
2. 读指令    读 STATE.md 指出的 core/<Hand>/agents/<agent>/SKILL.md
3. 执行      按 SKILL.md Procedure 做，产物写到指定路径
4. 跑门禁    python core/tools/gate.py <项目> <hand> <agent>
5. 推进      PASS → python core/tools/state.py <项目> advance <hand> <agent> --output <产物路径>
             FAIL → 按 SKILL.md ## Iteration 修正后重跑，最多 3 轮
```

## Friendly Mode（友好模式/问答式交互）

### 启用条件
- 环境变量/配置 `runtime.friendly_mode: true`（默认开启）
- 用户未显式指定 `--expert-mode` 或 `--no-friendly`

### 行为规范
1. **所有关键决策点**必须以编号选项呈现：
   - 选题/选模型/verdict/refine/参数选择/模板选择/结构规划/图表类型/引用策略
2. **选项格式**：
   ```
   请选择：
   1. 选项 A - 描述
   2. 选项 B - 描述
   3. 选项 C - 描述
   4. 让我决定 (推荐 1)
   输入数字 (1-4)：
   ```
3. **兜底选项**：每个问题必须提供 "让我决定 (推荐 X)"，X 为推荐项编号
4. **记录决策**：每次选择后调用 `python core/tools/state.py <项目> decision-add ...` 写入 `decision_log.json`
5. **专家模式**：用户输入 `expert` 或设置 `--expert-mode` 时，跳过问答，直接按推荐执行并记录

### 实现要求
- 各 agent SKILL.md 顶层声明 `interaction_mode: friendly`
- 交互逻辑在 agent 执行层实现（如 Python 包装器），不在 SKILL.md 中硬编码

## Harness 适配细节

| 能力 | Claude Code | Codex CLI | opencode | Cursor | 通用 Python |
|------|-------------|-----------|----------|--------|-------------|
| 读文件 | Read tool | read tool | read tool | read tool | `open()` |
| 写文件 | Write tool | write tool | write tool | write tool | `open()` |
| 运行命令 | Bash tool | bash tool | bash tool | terminal | `subprocess` |
| 状态持久化 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 交互输入 | 用户回复 | 用户回复 | 用户回复 | 用户回复 | `input()` |
| 并行执行 | 支持 | 支持 | 支持 | 受限 | `threading` |

### 运行时检测建议
```python
import os, sys
RUNTIME = os.environ.get("MATHMODEL_RUNTIME", "generic")
# Claude Code: 无特定环境变量，可检测 CLAUDE_CODE=1
# Codex CLI: OPENAI_AGENTS_SDK=1
# opencode: OPENCODE=1
```

## 产物路径约定

所有产物路径**相对于项目根目录**，使用 POSIX 风格（正斜杠）：

```
projects/<项目>/
├── inputs/                    # 赛题文件（用户放置）
├── work/                      # 中间产物、状态、日志
│   ├── state.json
│   ├── STATE.md
│   ├── decision_log.json
│   ├── question_spec.json
│   ├── type_classification.json
│   ├── literature_evidence.json
│   ├── method_candidates.json
│   ├── model_draft.md
│   ├── model_dag.json
│   ├── assumption_validation.json
│   ├── template_plan.json
│   ├── test_report.json
│   ├── result_validation.json
│   ├── guardrails_report.json
│   ├── paper_structure.json
│   ├── consistency_report.json
│   ├── score_card.json
│   ├── weakness_report.json
│   ├── revision_plan.json
│   └── execution_report.json
├── code/                      # 代码产物
│   ├── main.py
│   └── *.py
├── figures/                   # 结果数据
│   └── all_results.json
├── paper/                     # 论文源文件
│   ├── main.tex
│   ├── references.bib
│   └── figures/
└── output/                    # 最终交付物
    ├── MODEL_SPEC.md
    ├── CODE_DELIVERABLES.md
    └── PAPER_SPEC.md
```

## 环境变量配置

统一由 `core/env/config.yaml` + `core/env/loader.py` 管理。

运行时可通过环境变量覆盖：
```bash
export MATHMODEL_COMPETITION=cumcm
export MATHMODEL_LANGUAGE=zh
export MATHMODEL_STRICT_MODE=true
export MATHMODEL_FRIENDLY_MODE=true
export MATHMODEL_COMPILE_PDF=auto
```

## 错误处理与回退

1. **单步失败**：在本手内回退到对应 agent，不向下游推进
2. **3轮仍失败**：按 SKILL.md `## Iteration` 回退到上游手
3. **跨 harness 继续**：新 harness 读取 `state.json` + `decision_log.json` 即可无缝续跑
4. **产物不一致**：运行 `python core/tools/state.py <项目> sync` 从文件系统反推进度

## 版本兼容

| 组件 | 版本策略 |
|------|----------|
| `state.json` schema | 语义化版本，向后兼容，`version` 字段标识 |
| `decision_log.json` schema | 同左 |
| `AGENTS.md` / SKILL.md | 行为变更需同步更新 `catalog.yaml` |
| Python 工具脚本 | 零依赖，Python 3.10+ 稳定 API |

---

*文档版本：1.0 | 更新：2026-09-01 | 维护：MathModelSkills 核心团队*