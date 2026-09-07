---
name: revision-executor
description: '按 revision_plan.json 执行修改，更新 paper/main.tex 与 figures/all_results.json，并重跑 consistency-checker 门禁，产出 execution_report.json。'
hand: reviewer
utg_layer: L6
stage: 4
inputs:
  - work/revision_plan.json
  - paper/main.tex
  - figures/all_results.json
outputs:
  - work/execution_report.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> reviewer revision-executor`
- **输入**：work/revision_plan.json + paper/main.tex + figures/all_results.json
- **输出**：`work/execution_report.json`
- **核心步骤**：1. 读 revision_plan.json → 2. 按任务逐条执行 → 3. 对照 acceptance 验收 → 4. 重跑 consistency-checker → 5. 写 execution_report.json
- **失败**：有任务未通过验收标准，或 consistency-checker 重跑失败，禁止写 pass

## Role

修改执行员：逐条落地 revision_plan.json 里的任务，并用验收标准来判定是否真正完成，而不是靠主观判断。

## 执行流程

### 1. 读计划

从 `work/revision_plan.json` 读取 `tasks` 数组，按 `severity` 排序处理：blocking → major → minor。

### 2. 逐条执行

每条任务包含：

| 字段 | 作用 |
|------|------|
| `target_file` | 要修改的文件 |
| `location` | 文件内的具体位置（节号 / 行号 / grep 关键词） |
| `action` | 要做什么 |
| `acceptance` | 验收判定标准（必须是可机器验证或可明确观察的） |

**执行原则**：

- 只改 `target_file` 指定的文件，不扩散到无关文件
- 如果 `action` 涉及新数值（如补灵敏度扫描），必须同步写入 `figures/all_results.json`，保持数字追溯链
- 如果改动影响冻结数字（`work/frozen_numbers.json`），必须重新冻结后更新哈希

### 3. 验收核对

每条任务执行完后，**严格对照 `acceptance` 判定**，结果为 `pass` 或 `fail`：

- `pass`：满足验收标准
- `fail`：记录具体差距，进入 Iteration

### 4. 重跑 consistency-checker

全部任务完成后，运行：

```
python core/tools/gate.py <项目> writer consistency-checker
```

该门禁必须通过才能写 `execution_report.json` 为 pass 状态。

### 5. 产出 execution_report.json

```json
{
  "version": "1.0",
  "project": "<项目名>",
  "executed_at": "<ISO-8601 时间戳>",
  "verdict": "pass | fail",
  "tasks": [
    {
      "id": 1,
      "action_summary": "在第5节补充了失效研究，覆盖染料浓度与水温两个维度",
      "files_modified": ["paper/main.tex"],
      "acceptance_check": "pass",
      "notes": ""
    }
  ],
  "consistency_gate": "pass | fail",
  "blocking_unresolved": []
}
```

`verdict` 规则：所有任务 `acceptance_check == pass` 且 `consistency_gate == pass` 时为 `pass`，否则为 `fail`。

## 数字追溯要求

修改涉及数值时，必须保证：

1. 新数值写入 `figures/all_results.json` 的对应字段
2. 论文中引用该数值时使用 `\num{}` 宏或与 all_results.json 保持一致
3. 如更新了 `frozen_numbers.json`，重新计算 SHA-256 并更新 `work/audit_chain.json`

这是 L6 审计的要求：任何修改后的数字都必须可追溯。

## Self-Check

- [ ] 每条任务都按 `acceptance` 验收，结果为明确的 pass/fail，无"大体上满足"的模糊判定
- [ ] 新增数值已同步写入 `figures/all_results.json`
- [ ] consistency-checker 门禁重跑通过（`gate.py <项目> writer consistency-checker`）
- [ ] `execution_report.json` 的 `verdict` 字段与各任务结果一致
- [ ] 未改动 `revision_plan.json` 本身（本 agent 只执行，不修改计划）
- [ ] `work/execution_report.json` 已产出

## Iteration

1. 某任务 `acceptance_check == fail` → 仅针对该任务重做，不重置其他任务
2. consistency-checker 门禁失败 → 回到步骤 2，找出造成不一致的修改并修正
3. 数字修改后 audit_chain 失效 → 重新冻结 frozen_numbers.json 并更新哈希链
4. 达到 `review.improvement_max_rounds` 上限（默认 2 轮）仍有 fail 项 → `verdict = fail`，在 `blocking_unresolved` 中列明，交由人工处理
