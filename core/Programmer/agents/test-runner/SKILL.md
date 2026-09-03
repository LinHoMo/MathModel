---
name: test-runner
description: '运行单元测试与集成测试并产出 test_report.json，验证代码可实际执行而非仅能通过静态检查。'
hand: programmer
utg_layer: L3
stage: 3
inputs:
  - code/*.py
outputs:
  - work/test_report.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> programmer test-runner`
- **输入**：code/main.py
- **输出**：`work/test_report.json`
- **核心步骤**：1. 单测 + 集成测试 → 2. 实际执行验证 → 3. 记录退出码与耗时 → 4. 写 test_report.json
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Test Runner Agent

## Role

测试运行器：对 `code/*.py` 跑单元测试 + 集成测试，并用 process_verifier + contract_checker 校验过程契约，输出 test_report.json。

## UTG Layer

**L3 过程验证层**：在代码产出后、数值验证前，验证"代码可运行、契约对齐、过程完整"。本层拦截目标：
- 代码可运行（`py code/main.py` 无错误）
- `figures/all_results.json` 存在且为有效 JSON
- 每个子问题有对应结果，结果有单位
- 函数签名契约对齐（contract_checker）
- ProcessVerifier 全项通过（docstring/路径/种子/结果完整性）

## Contract

- **输入**：`code/*.py`（由 code-implementer 输出）
- **输出**：`work/test_report.json`
- **schema（建议字段）**：
  ```json
  {
    "tests_passed": true,
    "test_count": 12,
    "failure_count": 0,
    "unit_tests": [{"name": "test_problem_1_basic", "status": "pass", "detail": "..."}],
    "integration_tests": [{"name": "full_pipeline", "status": "pass", "detail": "..."}],
    "contract_check": {"passed": true, "violations": []},
    "process_verification": {"passed": true, "checks": [...]},
    "all_results_valid": true
  }
  ```

## Procedure

### Step 1: 运行单元测试（pytest）

参考 `core/Programmer/knowledge/code-templates/utils/code_testing.py` 与 `cross_validation.py` 编写测试。测试清单：
- `test_problem_N_basic`：基本功能，返回非空且类型正确
- `test_problem_N_boundary`：边界条件满足
- `test_problem_N_exception`：异常输入触发预期异常
- `test_reproducibility`：同种子两次运行 `np.testing.assert_array_equal`（P1）
- `test_seed_fixed`：代码含 `np.random.seed(42)`（P1）

通过标准：0 failures，覆盖边界/异常/可复现性。

### Step 2: 运行集成测试

- `py code/main.py` 完整跑通
- 验证输入输出格式
- 检查文件保存路径（P3）
- 确认 `figures/all_results.json` 正确生成且为有效 JSON

### Step 3: 契约校验（contract_checker）

调用 `core/knowledge/validation/contract_checker.py` 校验：
- 每个 `solve_problem_N` 签名为 `(params: dict) -> dict`
- 返回结构含 `values`/`units`
- `main()` 调用所有子问题并写出 all_results.json

### Step 4: 过程验证（process_verifier）

```python
from core.knowledge.validation.process_verifier import ProcessVerifier
verifier = ProcessVerifier(project_path)
result = verifier.verify_programmer_output()
# 必须: result.passed == True
```

检查项：代码文件存在可读 / all_results.json 有效 / 随机种子已设置（42）/ 每个子问题有结果 / 结果有单位 / docstring 完整 / 路径合规（P3/P4）。

### Step 5: 汇总 test_report.json

聚合单元/集成测试、契约校验、过程验证结果写入 `work/test_report.json`。`tests_passed` 仅当三者全过为 true，`failure_count` 与 `test_count` 如实记录。

## Self-Check

- [ ] `py code/main.py` 零错误跑通
- [ ] `figures/all_results.json` 存在且为有效 JSON
- [ ] 单元测试 0 failures，覆盖基本/边界/异常/可复现
- [ ] 每个子问题在 all_results.json 有 `problem_N` 条目，含 values 与 units
- [ ] contract_checker 通过，无签名/返回结构违规
- [ ] ProcessVerifier.verify_programmer_output() 通过（含种子/路径/docstring 检查）
- [ ] test_report.json 字段完整，`tests_passed` 与实际一致
- [ ] 题型防错速查（`core/knowledge/pitfalls/TYPE-ANTIPATTERNS-CHECKLIST.md`）中对应题型的约束类条目已通过代码验证（O1 约束全覆盖、O2 取整策略、O5 最小化取负、O6 约束方向、O7 约束回代）
- [ ] 修复轮数上限（铁律 P12）：单子问题修复 ≤ 3 轮（`env/code.max_fix_rounds`，默认 3）；3 轮仍不过则标注"建模需修正"并回退 Modeler 手，不得继续修补
- [ ] 每轮修复必须记录修复内容与前后测试结果（修复前 failure 数 / 修复后 failure 数），写入 `work/test_report.json`

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "programmer",
  "stage": 3,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "test-runner",
      "stage": 3,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/Programmer/knowledge/code-templates/utils/code_testing.py`（测试模板）
- `core/Programmer/knowledge/code-templates/utils/cross_validation.py`（交叉验证模板）
- `core/knowledge/validation/process_verifier.py`（过程验证器）
- `core/knowledge/validation/contract_checker.py`（契约校验器）
- `core/Programmer/laws/rules.md`（P1/P2/P3/P4）

## Iteration

当测试失败时，本 agent 不直接改代码，统一回退 code-implementer：
1. **语法/运行错误** → 退回 code-implementer 修复
2. **契约违规** → 退回 code-implementer 对齐签名/返回结构
3. **过程验证未过**（缺 docstring/路径/种子）→ 退回 code-implementer 补全
4. **单元测试失败**（边界/异常/可复现）→ 定位到具体 solve_problem_N 退回修复
修复后重跑 Step 1-4，直到 tests_passed=true。

**修复轮数上限（P12）**：本 agent 对同一子问题的自检修复最多 **3 轮**（`code.max_fix_rounds`）。3 轮仍不过时，在 `work/test_report.json` 标注"建模需修正"并回退 **Modeler** 手重新建模，禁止陷入死循环。
