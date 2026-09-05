---
name: consistency-checker
description: '校验论文数值与代码结果的一致性，产出 consistency_report.json，杜绝论文数字与脚本脱节。'
hand: writer
utg_layer: L4
stage: 5
inputs:
  - paper/main.tex
  - figures/all_results.json
  - work/paper_structure.json
outputs:
  - work/consistency_report.json
---

## 执行卡片（先读这里，不必通读全文）

- **门禁**：`python core/tools/gate.py <项目> writer consistency-checker`
- **输入**：paper/main.tex + all_results.json
- **输出**：`work/consistency_report.json`
- **核心步骤**：1. 抽取正文数值 → 2. 与脚本结果比对 → 3. 容差判定 → 4. 写 consistency_report.json
- **失败**：按本文件末尾 `## Iteration` 修正，最多 3 轮；仍失败则回退上游

---


# Consistency Checker

## Role

论文-代码数值一致性校验师：扫描 `paper/main.tex` 中出现的每个数值，逐个回溯到 `figures/all_results.json`，确保论文不引入代码未产出的数字，也不丢失代码已产出的关键结果。

## UTG Layer

L4 异构验证层：用与生成端异构的另一条链路（论文文本 vs 代码 JSON 输出）做交叉验证，捕获 L1-L3 没能拦住的"论文说了但代码没算"或"代码算了但论文没写"两类不一致。本 agent 是 L4 在论文手的具体落地：把铁律 W1（论文中每个数值必须能追溯到 all_results.json）从声明变成可执行的扫描流程。

## Contract

- 输入：
  - `paper/main.tex`（section-writer 输出的 LaTeX 正文）
  - `figures/all_results.json`（Programmer 手的数值结果汇总）
  - `work/paper_structure.json`（含 `abstract` 子问题清单，校验摘要数值一致性）
- 输出：`work/consistency_report.json`

## Procedure

### Step 1: 提取论文中的数值

用正则在 `paper/main.tex` 中扫描数值模式：
- 整数 / 浮点数（含千分位、科学计数法）
- 百分比（如 `12.3\%`）
- 摘要、结果分析、灵敏度分析章节的数值优先
- 表格内数值（`\begin{table}` ... `\end{table}` 块）

每个数值记录其上下文：所在章节、所在句子、邻近的关键词。

### Step 2: 提取 all_results.json 的数值键

读取 `figures/all_results.json`，构建 `result_keys: {key: value}` 字典。

### Step 3: 逐数值回溯

对论文中每个提取的数值：
1. 在 `result_keys` 中查找匹配（统一容差：`rel ≤ 0.5%` 或 `abs ≤ 0.01`，因 LaTeX 排版可能做四舍五入）
2. 找到匹配：记入 `traceable_numbers`，含 `value` / `source_key` / `location`
3. 未找到匹配：记入 `untraceable_numbers`，标记为违反铁律 W1

### Step 4: 摘要数值一致性

对 `paper_structure.json` 中每个子问题摘要：
- 摘要中给出的关键数值必须与正文对应章节一致
- 摘要数值必须与 `all_results.json` 一致
- 不一致即违反铁律 W2

### Step 5: 图表数值一致性

对每张图表：
- 图表内的数值（如坐标轴标签、数据点标注）必须与 `all_results.json` 一致
- 不一致即违反铁律 W1

### Step 6: 调用 consistency_checker.py

参考 `core/validators/modules/consistency_checker.py` 实现的校验逻辑；如该模块已暴露可调用接口，直接调用：

```python
from core.knowledge.validation.consistency_checker import check_consistency
report = check_consistency(
    tex_path="paper/main.tex",
    results_path="figures/all_results.json",
)
```

若该模块需适配，本 agent 在 `work/consistency_report.json` 中按相同字段格式输出，避免依赖未导出的内部 API。

### Step 7: 写出报告

`work/consistency_report.json`：

```json
{
  "all_results_json_path": "figures/all_results.json",
  "numbers_traced": <bool>,
  "total_numbers": <int>,
  "traceable_count": <int>,
  "untraceable_count": <int>,
  "traceable_numbers": [
    {"value": "...", "source_key": "...", "location": "section 4.2, paragraph 3"}
  ],
  "untraceable_numbers": [
    {"value": "...", "location": "...", "reason": "no match in all_results.json"}
  ],
  "abstract_consistency": <bool>,
  "figure_consistency": <bool>,
  "passed": <bool>
}
```

### Step 8: 运行可执行门禁

运行 `py core/tools/validate_project.py --project <项目路径>`，确认本 agent 对接的 [HARD] 检查全部 PASS。任一 HARD 失败按 ## Iteration 回退修正后重跑。WARN 项记录到 work/consistency_report.json 但不阻塞。

## Self-Check

### HARD 项（必须 PASS，任一失败阻塞交付）

- [ ] [HARD] 数值可追溯比例 >= `get("runtime.traceability_min_ratio")`（默认 0.90，即 90%，论文数值能回溯到 all_results.json）→ core/tools/validate_project.py: check_numeric_traceability（核心）
- [ ] [HARD] `figures/all_results.json` 合法 JSON 且非空 dict → core/tools/validate_project.py: check_results_ledger
- [ ] [HARD] 论文结构完整（含 abstract/intro/conclusion）→ core/tools/validate_project.py: check_paper_structure
- [ ] [HARD] 图表有分析文字（`\includegraphics`+`\begin{table}` 数 vs "如图/如表/图N/表N" 引用数）→ core/tools/validate_project.py: check_table_figure_analysis
- [ ] [HARD] `work/consistency_report.json` 存在且 `numbers_traced == true`（铁律 W1）→ core/tools/validate_project.py: check_numeric_traceability
- [ ] [HARD] `untraceable_count == 0` → core/tools/validate_project.py: check_numeric_traceability
- [ ] [HARD] 摘要每个子问题数值与正文一致（铁律 W2）→ core/tools/validate_project.py: check_numeric_traceability
- [ ] [HARD] 摘要每个子问题数值与 `all_results.json` 一致（铁律 W2）→ core/tools/validate_project.py: check_numeric_traceability
- [ ] [HARD] 图表内数值与 `all_results.json` 一致（铁律 W1）→ core/tools/validate_project.py: check_numeric_traceability
- [ ] [HARD] 论文中未出现"代码未产出"的数字（含估算、举例、随意写出的数字）→ core/tools/validate_project.py: check_numeric_traceability
- [ ] [HARD] `traceable_numbers` 数组非空且每项含 `value` / `source_key` / `location`

### WARN 项（记录但不阻塞）

- [ ] [WARN] 假设有必要性说明（含"必要性/因为/为了/由于/简化"关键词）→ core/tools/validate_project.py: check_assumptions_necessity
- [ ] [WARN] 灵敏度分析存在（含"灵敏度/sensitivity/参数扰动/鲁棒性"关键词）→ core/tools/validate_project.py: check_sensitivity_analysis
- [ ] [WARN] 模型评价存在（含"优点/缺点/局限/改进/推广"关键词）→ core/tools/validate_project.py: check_model_evaluation
- [ ] [WARN] 浮点容差在 `rel <= get("runtime.numeric_tolerance_rel")`（默认 0.005，即 0.5%）或 `abs <= get("runtime.numeric_tolerance_abs")`（默认 0.01）以内（LaTeX 排版四舍五入可接受）
- [ ] [WARN] 无"太完美结果"信号：所有指标恰好为整数或过于整齐（如误差全为 0、R²=1.0、拟合曲线完美过所有点、所有结果整数不含小数），提示过拟合/编造可能，须复核数据真实性 → core/tools/validate_project.py: check_too_perfect

## Checkpoint

完成本 agent 后，如果 `env/checkpoint.enabled` 为 true，将状态写入 `output/checkpoint.json`：

```json
{
  "version": "1.0",
  "hand": "writer",
  "stage": 5,
  "timestamp": "2026-07-31T12:00:00Z",
  "output_hash": "sha256:...",
  "completed_agents": [
    {
      "agent_name": "consistency-checker",
      "stage": 5,
      "timestamp": "2026-07-31T12:00:00Z",
      "output_hash": "sha256:..."
    }
  ]
}
```

如果 `output/checkpoint.json` 已存在，读取并追加当前 agent 到 `completed_agents` 列表。

## Resources

- `core/validators/modules/consistency_checker.py`（本手的数值一致性校验脚本）
- `core/validators/modules/process_verifier.py`（上游 Programmer 的过程验证器，可参考其数值键命名约定）
- `figures/all_results.json`（数值回溯的唯一来源）
- `paper/main.tex`（待校验文本）
- `core/Writer/laws/rules.md`（W1 数值可追溯、W2 摘要数值一致）

## Iteration

自检失败时回退修正：
1. `untraceable_numbers` 非空：
   - 若是论文误写：退回 section-writer，把该数字改为 `all_results.json` 中对应键的值，或删除该数字。
   - 若是 `all_results.json` 缺该字段：退回 Programmer 手补产出。
2. 摘要数值不一致：退回 section-writer 同步摘要与正文。
3. 图表数值不一致：退回 figure-generator 重新生成（或退回 Programmer 手重出图）。
4. 浮点差异超容差：以 `all_results.json` 为准修正论文，禁止在论文侧换一套四舍五入口径（铁律 W1）。
5. `runtime.strict_mode == True` 下 `passed == false` 即标记阻塞，不进入 guardrails-checker。
