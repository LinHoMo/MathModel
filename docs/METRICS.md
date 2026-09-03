# 项目度量（单一真源 · 脚本自动生成）

> **本文件由 `core/tools/metrics.py --write` 自动生成，禁止手改。**
> 最近扫描时间: `2026-09-03T13:10:30+00:00Z`
> 生成脚本: `core/tools/metrics.py`

---

## 概览

| 指标 | 值 |
|------|-----|
| 手（hands）数 | 4 |
| agent 数 | 29 |
| tools 脚本数 | 28 |
| tools 总行数 | 13735 |
| `known_competitions()` | 9 |
| methodology .md 数 | 53 |

## 测试

| 指标 | 值 |
|------|-----|
| pytest 通过 | 0 |
| pytest EXIT | 1 |

## 全链路门禁（cumcm2024a）

| 指标 | 值 |
|------|-----|
| gate.py 通过 | 81 |
| gate.py 硬失败 | 5 |
| gate.py 软失败 | 0 |
| gate.py EXIT | 1 |

## 项目校验（cumcm2024a）

| 指标 | 值 |
|------|-----|
| validate_project 通过 | 38 |
| validate_project 警告 | 9 |
| validate_project 硬失败 | 8 |
| validate_project EXIT | 1 |

## 库级校验

| 指标 | 值 |
|------|-----|
| validate.py 通过 | 0 |
| validate.py 警告 | 1 |
| validate.py 失败 | 1 |
| validate.py EXIT | 1 |

## 追溯率（四口径，待实测对比）

追溯率四口径不在 P0 合并，需独立实测；仅公示以下脚本可计算

准绳: `freeze_numbers.py`。其他口径需独立实测后补全对比表。

---

## agent 详单

| 手 | agents |
|-----|--------|
| modeler | problem-parser, type-classifier, literature-searcher, method-matcher, model-builder, dag-builder, assumption-validator, spec-auditor |
| programmer | template-selector, code-implementer, test-runner, result-verifier, guardrails-checker, hash-auditor |
| writer | structure-planner, section-writer, figure-generator, reference-curator, consistency-checker, guardrails-checker, final-validator |
| reviewer | scorer-academic, scorer-engineering, scorer-judge, scorer-reader, scorer-adversarial, weakness-hunter, revision-planner, revision-executor |

---

*文件末尾*
