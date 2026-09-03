# 国赛复盘基准（CUMCM Bench）

> 让引擎的产出**对齐真实评委口径**，用脚本化方式回答：
> “这份论文在真实国赛评分中大概能拿几分？缺了哪些必给分点？参考结果命中了几个？”

## 设计原则

1. **本库不自带 LLM 调用**。所有打分由 agent runtime 读 SKILL.md 主观产出 JSON，再由零依赖脚本重算校验。
2. **rubric 来自真实评分规则**。优先官方评分细则，次选评委评阅概述，否则通用规则兜底。
3. **参考结果可命中**。rubric 中给出 `reference_results`（如碰撞时间 412.4738 秒），脚本自动核对 ground_truth 命中数。

## 文件布局

```
core/knowledge/bench/cumcm/            # rubric JSON 文件（每题一个）
  GENERIC-RUBRIC.json                  # 跨题通用结构（备用参考）
  rubric_2024a.json                    # 官方评分细则
  rubric_2025a.json
  rubric_2023c.json
  rubric_2021a.json                    # 评委评阅概述提炼
  ...

core/schemas/
  bench_rubric.schema.json             # rubric 文件结构
  bench_result.schema.json             # 响应文件结构

core/tools/
  benchmark.py                         # 含 bench list/run/score/report + 原有 pipeline/library
  bench_mmbench.py                     # MMBench 外部题库适配器（111 题）
```

## rubric 来源标记

| source | 含义 | 那一年 |
|---|---|---|
| `official_rubric` | 官方评分细则/出题人评阅综述原件 | 2023C, 2024A, 2025A, 2025B, 2025C |
| `judge_insights` | 评委评阅概述 + 常见扣分点提炼 | 2021ABCDE, 2022ABCE, 2023ABDE, 2024BDE |
| `inferred` | 题目已确认但 PDF 待补全 | 2025D |
| `mmbench_import` | 从 LLM-MM-Agent MMBench 临时导入（待官方 rubric 覆盖） | — |

## 命令速查

### 1. 列出当前可用 rubric
```bash
python core/tools/benchmark.py bench list
python core/tools/benchmark.py bench list --json   # 机器可读
```

### 2. 生成 agent 评分模板（不调用 LLM）
```bash
python core/tools/benchmark.py bench run --rubric core/knowledge/bench/cumcm/rubric_2024a.json
```
输出步骤提示并写 `projects/_bench_<年><题>/bench_response_template.json`。Agent runtime 按提示读 SKILL.md 主观打分后写 `bench_response.json`。

### 3. 重算校验打分 JSON
```bash
python core/tools/benchmark.py bench score \
    --rubric core/knowledge/bench/cumcm/rubric_2024a.json \
    --response projects/<项目>/bench_response.json
```
脚本自动校验：
- 每维度得分不超满分（超则截断，报 issue）
- 总分一致性（声明 vs 重算合计）
- ground_truth 命中数不可超过参考结果数

EXIT 0 = 通过，EXIT 1 = 维度越界或总分不一致。

### 4. 生成可读报告
```bash
python core/tools/benchmark.py bench report \
    --rubric core/knowledge/bench/cumcm/rubric_2024a.json \
    --response projects/<项目>/bench_response.json
```

## 与现有评分卡的分工

| 工具 | 层级 | 用途 |
|---|---|---|
| `aggregate_scores.py` | 评审手 | 5 维评分卡（academic/engineering/judge/reader/adversarial） |
| `benchmark.py bench score` | 复盘基准 | 按官方 rubric 计算**数值分**（0–100） |
| `weakness_report.json` | reviewer weakness-hunter | 反模式缺陷扫描 |

bench 不替代 aggregate_scores：aggregate_scores 是"评我们的流程产出质量"，bench 是"如果这份论文交上真实国赛，按官方细则能拿几分"。

## MMBench 外部题库

```bash
python core/tools/bench_mmbench.py path               # 打印 MMBench 根路径
python core/tools/bench_mmbench.py list [--json]       # 列出 111 题
python core/tools/bench_mmbench.py export --year 2024 --topic A --out core/knowledge/bench/imported
```

`export` 生成通用结构 rubric（source=mmbench_import），待官方 rubric 覆盖。
MMBench 根默认 `<项目根>/../_mm_analysis/LLM-MM-Agent/MMBench`，可由 `MMBENCH_ROOT` 环境变量覆盖。

## 验收标准

对 cumcm2024a（9 页半成品）跑完整 bench 流程：
1. `bench list` 返回 count ≥ 22（当前覆盖 2021–2025 年国际/国赛题）
2. `bench run` 生成 7 维度模板
3. 手写一份响应（模仿 9 页半成品能拿到的分）→ `bench score` 不计为高分（应 < 60 分，体现"半成品低于通过线"）
4. 若打高分即基准失效 → 调低 rubric 维度满分或加严 assessment_points

## Aggregator 迭代规则

当 scorer-* 主观打分频繁触发 bench_score 截断（维度越界 / 总分不一致）：
1. 在对应 scorer SKILL.md 的 Self-Check 中加入"bench_score 预检"提示
2. 多次同维度越界 → 在 aggregate_scores.py 加该维度的 clamp 规则
3. ground_truth_hits 造假（hit > expected）→ 直接标 blocking
