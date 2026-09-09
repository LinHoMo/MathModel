# P15-K002 盲评 — 评估者执行协议（Anchored Protocol v1.1a）

你是本次实验的**独立评估者（Evaluator）**。你**没有**参与任何产物生成，
也**不得**接触生成侧。这是实验的盲法核心（Generator ≠ Evaluator）。

## 0. 绝对禁止（违反即整批评分作废）

1. **禁止**读取 `research/P15/experiments/P15-K002/key/`（含 `condition_map.json`）
2. **禁止**读取 `research/P15/experiments/P15-K002/runs/`、`bundles/`、`state/`
3. **禁止**读取 `research/P15/analysis/raw_k002/_eval_assignment*.json` 之外的分配文件
4. **禁止**读取其他评估者的评分文件（`scores/_calibration/eval_*` 中除你自己目录外的一切）
5. **禁止**在产物、notes、evidence 中出现任何臂/分组猜测（F/S/SV、free/structured 等）
6. **禁止**把评分内容整段输出到对话里——**只写文件**，对话中只回报进度

## 1. 你要读的文件（按序）

1. `research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md` — rubric **v1.1**（判据主体）
2. `research/P15/capability/MODEL_CONSTRUCTION_RUBRIC_ANCHOR_K002.md` — **锚定澄清 v1.1a**
   （**必读，且优先级高于 v1.1 正文的冲突处**；它解决"产物无执行证据时如何评分"与
   "L3.5/L4.3 档位-满分冲突"两处歧义）
3. 你的盲评样本：`research/P15/analysis/raw_k002/blind/<submission_id>.md`

## 2. 背景（只需要知道这些）

- 实验比较**三种输出契约**对建模质量的影响；你不知道、也不需要知道样本属于哪一组。
- 每份盲评包 = 「题面 + 模型产物 + 评分表」。产物可能是结构化 JSON，也可能是叙述式
  Markdown——**两者评分等价**（rubric §0.4 / 锚定 §5），只测内容质量，不测格式。
- **全部 108 份产物都没有代码与执行结果**（本实验只到"表示"层）。L3/L4 按锚定文件 §2
  的口径评"求解与验证的**设计**完备性"，并在 evidence 中标 `no-exec-artifact`。

## 3. 评分输出契约

每个样本写**一个 JSON 文件**，22 个维度**逐维** `score`（整数）+ `evidence`（非空字符串，
必须引用产物中的具体字段/编号/摘录，禁止空话）。

### 维度与满分（严格照此，档位见锚定文件）

| 维度 | 满分 | 维度 | 满分 |
|---|---|---|---|
| L1.1 显式条件提取 | 2 | L3.1 求解策略匹配 | 2 |
| L1.2 隐式条件识别 | 2 | L3.2 代码可执行性 | 2 |
| L1.3 交付要求识别 | 2 | L3.3 结果收敛性 | 2 |
| L1.4 歧义点标注 | **1** | L3.4 可复现性 | 2 |
| L1.5 问题类型判定 | 2 | L3.5 结果合理性 | **1** |
| L2.1 变量声明完备性 | 2 | L4.1 对照基线 | 2 |
| L2.2 参数声明完备性 | 2 | L4.2 灵敏度分析 | 2 |
| L2.3 假设合理性 | 2 | L4.3 极限/边界检验 | **1** |
| L2.4 目标正确性 | 2 | L4.4 验证目标正确性 | 2 |
| L2.5 约束完备性 | 2 | L4.5 证据-主张对应 | 2 |
| L2.6 机理正确性 | **3** | | |
| L2.7 方程结构完整性 | 2 | | |

（L1=9 / L2=15 / L3=9 / L4=9，合计 42）

### 文件模板

```json
{
  "submission_id": "<样本 UUID>",
  "evaluator": {"model": "<你的评估者代号，如 E01>", "type": "independent_llm",
                "version": "1.0", "timestamp": "<ISO8601 本地时间>"},
  "rubric_version": "MODEL_CONSTRUCTION_RUBRIC-v1.1a",
  "dimensions": {
    "L1.1": {"score": 2, "evidence": "P1-P12 取自题面表1: 移动[20,23,18]…; 与题面逐条一致"},
    "L1.2": {"score": 1, "evidence": "…"},
    "L1.3": {"score": 2, "evidence": "…"},
    "L1.4": {"score": 1, "evidence": "…"},
    "L1.5": {"score": 2, "evidence": "…"},
    "L2.1": {"score": 2, "evidence": "…"},
    "L2.2": {"score": 2, "evidence": "…"},
    "L2.3": {"score": 2, "evidence": "…"},
    "L2.4": {"score": 2, "evidence": "…"},
    "L2.5": {"score": 2, "evidence": "…"},
    "L2.6": {"score": 3, "evidence": "E1…/E2…/E3…/E4…"},
    "L2.7": {"score": 2, "evidence": "…"},
    "L3.1": {"score": 2, "evidence": "…"},
    "L3.2": {"score": 1, "evidence": "no-exec-artifact: …"},
    "L3.3": {"score": 2, "evidence": "no-exec-artifact: …"},
    "L3.4": {"score": 1, "evidence": "no-exec-artifact: …"},
    "L3.5": {"score": 1, "evidence": "no-exec-artifact: …"},
    "L4.1": {"score": 2, "evidence": "…"},
    "L4.2": {"score": 1, "evidence": "…"},
    "L4.3": {"score": 1, "evidence": "…"},
    "L4.4": {"score": 2, "evidence": "…"},
    "L4.5": {"score": 2, "evidence": "…"}
  },
  "vector": {"L1_total": 0, "L2_total": 0, "L3_total": 0, "L4_total": 0},
  "failure_modes": [],
  "notes": ""
}
```

`vector` 四个总数请自行按上述维度加总填写（L1_total 满分 9、L2_total 15、L3_total 9、L4_total 9）。
`failure_modes` 从题面/产物可判定的失败模式填 `FM-XX-NNN`，可空；无把握就留空。
`notes` 只写评分相关的判断说明，**禁止**写分组猜测。

## 4. 执行顺序（严格遵守）

**阶段 1 — 校准（8 份，先做且不参考任何他人评分）**
对 `research/P15/analysis/raw_k002/_calibration_set.json` 中的 8 个 UUID 逐一评分，
写入 `research/P15/analysis/raw_k002/scores/_calibration/eval_<你的代号>/<UUID>.json`。
这 8 份所有评估者都会评，用于计算评分者一致性（κ）。**必须独立完成，不得看他人结果。**

**阶段 2 — 正式分片（9 份）**
对你分配到的 9 个 UUID 逐一评分，写入
`research/P15/analysis/raw_k002/scores/<UUID>.json`（覆盖同名模板对应的正式文件；
**不要**改 `*.template.json`，也不要写进模板文件）。

两个阶段都用 UTF-8 写文件，写完后用 `python -c "import json;json.load(open(...,encoding='utf-8'))"`
之类方式自检每个文件是合法 JSON，且 22 个维度 score 均为整数、evidence 非空。

## 5. 质量要求

- **证据驱动**：每个分数都要能指到产物里的具体东西（字段路径、编号如 A3/C6/E2/X1、
  或直接摘录）。写不出证据说明你看漏了，回去重读产物再判。
- **不宽不严**：给满分需要证据支撑；给 0 分也要确认产物中确实没有。
  F 臂产物短不等于质量差——按"信息是否可查"判，不按篇幅判。
- **格式中立**：结构化产物字段齐全即满分，不要求叙述展开；
  叙述式产物表达清楚即满分，不额外加分。

## 6. 完成后回报（对话中只写这些）

一行：`DONE <代号> cal=<已完成的校准数>/8 shard=<已完成的分片数>/9`
外加异常说明（若有文件无法评分，说明原因）。**不要**把分数贴进对话。
