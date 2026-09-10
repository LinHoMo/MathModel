# P2-2: Fidelity Measurement Study 报告

**日期**: 2026-09-10
**数据**: P15-K003 66 runs（FROZEN 数据，不再生成）
**脚本**: `research/P15/analysis/p2_2_fidelity_study.py`（LLM-free，确定性统计）
**产物**: `research/P15/experiments/P15-K003/analysis/p2_2_fidelity_study.json`

---

## 1. 结论速览

| 指标 | 值 |
|---|---|
| 可测 runs | **44**（S/SV 结构化臂 22+22；F 臂无 MODEL_IR 不产生 fidelity） |
| fidelity 均值 / 中位数 | **0.808 / 0.929** |
| aligned（≥0.6） | **36/44（81.8%）** |
| misaligned（<0.6） | **8/44（18.2%）**，**全部集中在 2022_C 与 2024_A**（两题 8 runs 全部 misaligned，score=0.2） |
| Fidelity vs 盲评 L2（Pearson / Spearman） | **+0.051 / +0.254（无显著正相关）** |
| 负相关维度 | L2.6（r=-0.479）、L2.4（r=-0.453） |

---

## 2. Fidelity 分布

```
0.0-0.2  ██ 0
0.2-0.4  ████████ 8   ← 全部 2022_C/2024_A
0.4-0.6  0
0.6-0.8  0
0.8-1.0  ██████████████████████████████████ 36
```

**双峰分布**：要么高保真（0.8-1.0），要么低保真（0.2）。无中间态——fidelity 是**分类性**信号（mapping 是否对上），不是连续渐变。

按题：2011_B/2018_B/2019_C 全部 1.0（最优）；2017_B 0.82；2018_A 0.91；2020_B 0.93；**2022_C 与 2024_A 全部 0.2**。

---

## 3. Misaligned 案例归因（8/8 = 2022_C + 2024_A）

两题 F1 检查失败形态**完全相同**：MODEL_IR 声明的输出字段是中文名
（"二氧化硅含量"/"氧化钙含量"/"氧化铅含量"/"分类标签"），而 `run_model.py`
实际输出的 key 是英文/缩写（如 `SiO2`/`K2O`/`PbO`/`label`）。

**根因**：这两题是"材料成分/分类"型问题，Constructor 在 MODEL_IR 用中文
语义变量名，代码用英文变量名——**output_mapping 缺失或未命中**，不是模型
数学错误（exec_status 全部 success）。

**结论**：F1（output_key_exists）抓的是**表示层词汇一致性**，不是数学保真。
低 fidelity 在该体系里 = "变量名/输出 key 契约未对齐"，而非"代码没实现声明的模型"。
这与 K001 RQ5 词表错位是**同一类病根**（字符串词汇 vs 结构化身份分离问题）。

---

## 4. Fidelity vs 盲评 L2：正交性（本 Study 最重要的发现）

- 全局相关：Pearson +0.051 / Spearman +0.254 —— **不显著**。
- 维度级：L2.6（模型表达充分性）r=**-0.479**、L2.4（目标/依赖结构）r=**-0.453**。

**解释**：盲评 L2 测的是 MODEL_IR **文档结构完整度**（字段齐全、表达规范）；
fidelity 测的是 **声明与代码实现的一致性**（机械可判）。两者正交：
一份"结构完美"的 MODEL_IR 可以完全没被代码实现（fidelity=0.2 的 2022_C
文档得分并不低），一份朴素 MODEL_IR 可以 1.0 保真。

**K003 主结论的机械佐证**：盲评（尤其 L2）奖励的是"表示格式"，而 fidelity
奖励的是"表示-实现一致性"——后者才是 LinHoMo 独有的、不可被格式欺骗的指标。
这也解释了为何 K003 中 S/SV 的盲评优势未转化为执行质量优势。

---

## 5. 后续建议

1. **Fidelity 进 benchmark 主指标**（P2-1/P2-4 候选）：作为盲评之外的
   确定性机械维度（构造有效性 L2），不依赖评估者。
2. **output_mapping 契约前置**：2022_C/2024_A 的问题可通过在 Constructor
   协议层强制 output_mapping（C4 级别）消除——P1-1 ConstructionBundle
   的 output_mapping 字段正是为此设计。
3. **词汇身份分离**（RQ5 病根）：模型 ontology 与字符串词汇分离
   （Concept/Mechanism/Family/Model/Method/Solver/Implementation 分层），
   输出 key 用结构化引用而非自然语言名称。
4. 负相关维度（L2.6/L2.4）值得单独立项：盲评维度权重是否需要校准，
   或 L2 与 L3（执行）分开报告。

---

## 6. 缺口声明

- 44/66 runs 可测（F 臂 22 runs 无 MODEL_IR，fidelity 定义域仅限结构化臂）。
- 相关分析为描述性（无因果推断）；n=44 功效有限。
- 盲评 κ 低（L1.1 A-B 0.0）已知，L2 维度相关以均值代理存在测量噪声。
