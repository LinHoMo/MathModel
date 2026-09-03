---
name: guardrails-checker
description: '运行时护栏：检测禁用词、占位符、AI 痕迹与内部术语泄露，防止工程脏话流入论文。'
hand: programmer
utg_layer: L5
stage: 5
inputs:
  - code/*.py
outputs:
  - work/guardrails_report.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> programmer guardrails-checker`
- **输入**：code/ 与 output/
- **输出**：`work/guardrails_report.json`
- **核心步骤**：1. 扫禁用词 → 2. 扫占位符 → 3. 扫 AI 痕迹 → 4. 写 guardrails_report.json
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Guardrails Checker Agent

## Role

护栏检查器：对 `code/*.py` 做运行时护栏审查——禁用词、占位符、AI 痕迹、内部路径、权限越界，输出 guardrails_report.json。

## UTG Layer

**L5 运行时护栏层**：在产物交付前拦截"污染源"，确保代码干净、可发布、无越权。本层拦截目标：
- 无禁用词（以 `core/Writer/knowledge/writing/forbidden-words.md` 的**统一禁用词表**为准：中文 AI 套话 + 元叙述"参赛者/参赛队伍/我们团队" + 英文 `delve`/`pivotal`/`tapestry`/`underscore`/`noteworthy`/`It is worth noting that`/`Importantly,`/`Notably,` + 正则 `随着.{0,12}的快速发展`）
- 无占位符（`[在此处填写]`、`your_xxx`、`placeholder`、`待补充`、`待续写`、`这里补`、`待完善` 等）
- 无 AI 痕迹（"作为 AI"、"我无法"、特定模型自指语句）
- 无内部路径泄露（绝对路径、用户名、内部目录）
- 无权限越界（网络下载、写系统目录、执行 shell、删除非产物文件）
- 随机种子已固定（P1）、异常处理已覆盖（P5）、数据校验已覆盖（P8）

## Contract

- **输入**：`code/*.py`
- **输出**：`work/guardrails_report.json`
- **schema（建议字段）**：
  ```json
  {
    "passed": true,
    "forbidden_words": [{"file": "code/model.py", "line": 12, "word": "TODO", "severity": "error"}],
    "placeholders": [{"file": "...", "line": 0, "snippet": "..."}],
    "ai_traces": [{"file": "...", "line": 0, "snippet": "..."}],
    "internal_paths": [{"file": "...", "line": 0, "path": "..."}],
    "permission_violations": [{"file": "...", "line": 0, "action": "subprocess", "severity": "error"}],
    "seed_fixed": true,
    "exception_handling": true,
    "data_validation": true,
    "summary": "all checks passed"
  }
  ```

## Procedure

### Step 1: 护栏扫描（guardrails）

调用 `core/knowledge/validation/guardrails.py`：
```python
from core.knowledge.validation.guardrails import Guardrails
g = Guardrails()
for py_file in Path("code").glob("*.py"):
    content = py_file.read_text(encoding="utf-8")
    g.validate_output(content)
# 检查: g.has_errors() == False
```
覆盖：禁用词、占位符、AI 痕迹、内部路径。

### Step 2: 权限守卫（permission_guard）

调用 `core/knowledge/validation/permission_guard.py`，拦截：
- `subprocess` / `os.system` / `exec` / `eval` 执行外部命令
- 写系统目录（`/etc`、`C:\Windows`、用户主目录外）
- 网络下载（`urllib.request`、`requests.get` 写盘）未经许可
- 删除非产物文件（`os.remove` 非 figures/tables/code 内）

### Step 3: 信任域校验（trust_domain）

调用 `core/knowledge/validation/trust_domain.py`，确认代码只引用知识库内可信模板/工具，不引入未授权外部依赖。

### Step 4: 增量检查（incremental_checker）

调用 `core/knowledge/validation/incremental_checker.py`，对本次新增/修改的代码段做增量护栏复查，避免回归。

### Step 5: 确认 P1/P5/P8 落地

- 种子固定：所有 .py 中 `np.random.seed(42)` 存在（P1）
- 异常处理：数据加载/文件 IO 有 try-except（P5）
- 数据校验：编码/列名/形状/缺失值检查存在（P8）

### Step 6: 汇总 guardrails_report.json

聚合所有发现写入 `work/guardrails_report.json`，`passed` 仅当无 error 级别发现。

### Step 7: 运行可执行门禁

运行 `py core/tools/validate_project.py --project <项目路径>`，确认本 agent 对接的 [HARD] 检查全部 PASS。任一 HARD 失败按 ## Iteration 回退修正后重跑。WARN 项记录到 work/guardrails_report.json 但不阻塞。

## Self-Check

### HARD 项（必须 PASS，任一失败阻塞交付）

- [ ] [HARD] `code/*.py` 无占位符（TODO/FIXME/TBD/XXX/待补/示例数据/模板数据）→ core/tools/validate_project.py: check_placeholders
- [ ] [HARD] 代码输出无禁用词（统一禁用词表，见 `core/Writer/knowledge/writing/forbidden-words.md`）→ core/tools/validate_project.py: check_forbidden_words
- [ ] [HARD] 代码无 AI 痕迹/内部路径（"作为AI"/绝对路径/用户名/内部目录）→ core/tools/validate_project.py: check_forbidden_words（含内部路径检测）
- [ ] [HARD] 代码语法正确（py_compile 全部通过）→ core/tools/validate_project.py: check_python_syntax
- [ ] [HARD] 代码在 `code/` 目录下，不在根目录 → core/tools/validate_project.py: check_code_in_code_dir
- [ ] [HARD] 项目根目录无散落产物（.py/.xlsx/.csv/.png/.pdf 等）→ core/tools/validate_project.py: check_directory_structure
- [ ] [HARD] 无权限越界（subprocess/系统目录写/未授权网络下载/误删）→ core/knowledge/validation/permission_guard.py
- [ ] [HARD] 种子固定 `np.random.seed(42)` 存在（P1）→ core/tools/validate_project.py: check_reproducibility

### WARN 项（记录但不阻塞）

- [ ] [WARN] 代码注释率充足（>50 行文件注释率 >=10%）→ core/tools/validate_project.py: check_code_comments
- [ ] [WARN] 无未使用 import（启发式检查）→ core/tools/validate_project.py: check_imports
- [ ] [WARN] 异常处理覆盖文件 IO 与数据加载（P5）
- [ ] [WARN] 数据校验覆盖编码/列名/形状/缺失值（P8）

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "programmer",
  "stage": 5,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "guardrails-checker",
      "stage": 5,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/knowledge/validation/guardrails.py`（禁用词/占位符/AI 痕迹/路径扫描）
- `core/knowledge/validation/permission_guard.py`（权限守卫）
- `core/knowledge/validation/trust_domain.py`（信任域）
- `core/knowledge/validation/incremental_checker.py`（增量检查）
- `core/Programmer/laws/rules.md`（P1/P5/P8）

## Iteration

当护栏检查发现 error 级别问题时，本 agent 不改代码，统一回退 code-implementer：
1. **禁用词/占位符/AI 痕迹** → 退回 code-implementer 清理对应行
2. **内部路径泄露** → 替换为相对路径（P3），退回 code-implementer
3. **权限越界** → 移除 subprocess/系统写/未授权网络调用，退回 code-implementer
4. **信任域外依赖** → 替换为知识库内模板，退回 code-implementer
5. **种子/异常/数据校验缺失** → 退回 code-implementer 补全
修复后重跑 Step 1-5，直到 passed=true。
