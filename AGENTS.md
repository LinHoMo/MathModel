# MathModel Harness — AGENTS

面向数学模型构建与验证的**可信 Harness**。核心是 V3 认知工作流运行时
（Artifact Registry + Evidence Graph + Workflow DAG + 验证门禁）。

> **Source of truth = Artifact Registry + Evidence Graph。**
> Agent / LLM 只是 Executor。

## 核心定位

**问题输入 → 数学建模产出（MD/Mermaid 文本）**

产出物：MODEL_IR（JSON）+ 模型描述文档（MD/Mermaid）。
不包含论文生成（LaTeX/PDF）、不向后兼容 V2。

## 目录结构

| 目录 | 说明 |
|---|---|
| `core/` | 引擎本体：runtime / roles / workflows / validators / schemas / tools / skills / knowledge / env |
| `core/tools/` | CLI 工具：validate.py / catalog_check.py / benchmark.py / new_project.py 等 |
| `core/workflows/` | DAG 模板（stages/）+ WorkflowComposer |
| `core/roles/` | 4 角色：analyst / modeler / experimenter / critic |
| `core/validators/` | 门禁：evidence-gate / research-quality / model-critic / assumption-checker |
| `research/` | 研究实验与基准测试 |
| `projects/` | 用户运行实例（仅 `new_project.py` 创建） |

## 执行协议

**每次只推进一步。**

### V3 模式（唯一模式）

```
1. 读状态    python core/tools/validate.py <项目>    # 项目级校验
2. 看计划    python core/tools/catalog_check.py      # 一致性检查
3. 执行      按 core/roles/*.yaml 与 core/skills/ 指令执行
4. 验证      python core/tools/validate.py            # 58 项校验
```

### 命令速查

| 命令 | 作用 |
|---|---|
| `python core/tools/new_project.py <项目名>` | 创建新项目脚手架 |
| `python core/tools/validate.py` | 项目级 58 项校验 |
| `python core/tools/catalog_check.py --check` | catalog 三方一致性 |
| `python core/tools/knowledge.py recommend --types <题型>` | 方法卡检索 |
| `python core/tools/score_compute.py <项目>` | 自动化评分卡 |
| `python core/tools/diagram_gen.py flowchart --nodes "A,B" --edges "A->B" -o fig.svg` | 科学图表生成 |
| `python core/tools/scholar_fetch.py bibtex <关键词>` | 学术文献检索 |

## 不可违反的规则

- **所有数值可追溯到已验证的 Result Artifact**
- **无占位符 / AI 痕迹 / 伪造引用**
- **随机种子固定为 42**：多种子运行 ≥5 次，报告均值与标准差
- **schema / 哈希链全绿**：结构化输出通过 schema 校验

## 修改后必做

```bash
python core/tools/validate.py                         # 58 项校验
python core/tools/catalog_check.py --check            # 双视图一致
python -m pytest tests -q                             # 基线测试
```

任一项失败按对应 `## Iteration` 回退修正后重跑。
