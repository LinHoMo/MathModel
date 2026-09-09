# Test Coverage Gap Fix — 11 skipped 审查与修复（2026-09-09）

## 背景（用户质询"793/11 全绿，11 skipped 什么情况"）

全绿不代表无空洞。逐一核对 11 个 skipped 后确认：**7 个是 fixture 驱动的
功能性覆盖空洞（从未真正执行断言），4 个是有意跳过（设计意图明确）**。

## 分类与处置

| # | 测试 | skip 原因（修复前） | 性质 | 处置 |
|---|---|---|---|---|
| 1-6 | `tests/unit/test_aggregate_scores.py`（6 个） | `work/score_card.json` 缺失 | **功能空洞**：aggregate_scores.py 的聚合/verify 行为从未被测试 | **修复**：补 5 张 scorer 分卡 + weakness_report.json fixture，score_card.json 由 aggregate_scores.py 生成（非手写），`--verify` EXIT 0 |
| 7 | `tests/unit/test_gate_paper_thresholds.py`（1 个） | `paper/main.tex` 缺失 | **功能空洞**：gate 拦截不达标论文的版面阈值断言从未执行 | **修复**：新建 `sample_paper_project` fixture（故意不达标 main.tex），测试指向它 |
| 8-10 | `tests/e2e/test_pipeline.py`（3 个） | MODEL_SPEC/CODE_DELIVERABLES/PAPER_SPEC 缺失 | **legacy 冻结占位**：V2 流水线已冻结，产物不再重建 | **显式化**：加注释声明是 legacy 冻结的显式占位（非空洞），V3 产物断言在 integration 层 |
| 11 | `tests/integration/test_workflow_execution.py`（1 个） | 当前 workflow 无人工审批节点 | **feature conditional**：无审批节点的 workflow 无需测审批分支 | 保持（设计意图明确） |

## Fixture 原则（本次立下的）

- **sample_incomplete_project**：只补 `work/` 评分输入；`output/` 与 `paper/` 保持缺失，
  不破坏其 e2e "incomplete" 语义。
- **score_card.json 必须由 aggregate_scores.py 生成**（generated_by 字段校验 + --verify
  重算一致），任何手写 score_card 都是被测对象本身要拦截的违规。
- 新 fixture `sample_paper_project` 只含故意不达标的论文（版面指标缺失），用于验证拦截路径。

## 结果

- pytest：**793/11 → 800/4**（+7 个测试从静默跳过变为真实执行并通过）
- 剩余 4 个 skip 全部有显式理由（3 legacy 占位 + 1 feature conditional）
- catalog / terminology / freeze 自检全绿（见对应 commit）
