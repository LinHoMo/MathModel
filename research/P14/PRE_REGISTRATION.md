# P14 预注册（v1 freeze）：Model → Experiment / Evidence Transmission Pilot

- Status: **FROZEN v1 (2026-09-07)** · 轨道：`research/`（P14 全程不进 core/）
- 上游：P13-3D **closed**（negative but informative；其 Layer-1/2/3 结论是本项目的出发点）
- 定位：P14 不是 P13-3D 的继续优化版，而是跨向新能力段：让 Harness 把一个数学模型继续变成**可执行、可验证、可追溯的实验链**。

## 1. 研究问题

> Harness 能否把一个冻结的 MODEL_ARTIFACT 变成一条完整实验链，使得模型检验的每个环节——从实验设计到证据支持——都可追溯、可重放、可失效传播？

核心链（六个 canonical entities 的真实流转，本项目的验证对象）：

```text
MODEL_ARTIFACT
      ↓
Experiment Design   (ExperimentSpec)
      ↓
Executable Experiment (Execution)
      ↓
Result
      ↓
Evidence
      ↓
Claim
```

本系统最终必须回答的问题："这个模型如何被实验检验？实验产生什么结果？什么证据支持什么 Claim？哪个 Claim 仍只是推断？实验失败后哪些下游结论自动失效？"

## 2. 本轮成功标准（integrity 能力，不比较效果显著性）

| # | 能力 | 判据 |
|---|---|---|
| 1 | Model → Experiment 1:1 provenance | 每个 ExperimentSpec 解析到唯一 artifact id + sha256 |
| 2 | Experiment → Result deterministic record | seed/环境/输入 hash/执行日志齐备，重放一致 |
| 3 | Result → Evidence explicit binding | evidence 引用 result hash，不引用"印象" |
| 4 | Evidence → Claim traceable support | 每个 claim 列出支持/反驳它的 evidence id 集合 |
| 5 | Failure → downstream invalidation | 实验/证据失效时，受影响下游 claim 集合可计算 |

第一轮刻意不做：Agent 能力对比、效果显著性宣称、大规模 sweep。

## 3. Pilot 规模（刻意小）

```text
3 questions × 1 frozen Model Artifact × 2 experiment-generation conditions
```

PROPOSED（P14.1 runbook 冻结前可调，冻结后不可改）：

- 题目选择规则：覆盖不同模型家族（动态优化 / 离散决策 / 统计判别各一），优先取 P13-3D 中构件质量最好的 arm（盲评与 fidelity 证据）作为冻结 artifact。候选：2020_B（DP/MDP）、2024_B（生产决策/Lambert W）、2022_C（成分数据统计判别）。
- 条件 C0/C1：C0 = 仅 artifact 生成实验设计；C1 = artifact + 验证问题清单脚手架（"模型需要验证什么"的结构化提示）。两条件使用同一执行/评估后端。

## 4. 纪律（继承仓库铁律）

- 全程 `research/` 轨道；发现 core 缺陷 → failure → experiment → intervention → non-regression，不直接改 core/。
- 随机种子 42；六实体间以 hash 链贯穿（id + content sha256 + parent 引用）。
- Negative results 与 integrity 失败同样是合格产出；禁止事后调参。
- 不重开 P13-3D；不改变 `v3.1.x` 核心架构边界。
- P13-3D 遗留的仪器问题（组织质量度量）不阻塞 P14 v1，但 Evidence/Claim 绑定设计应为其留接口。

## 5. 待冻结项（P14.1 runbook 中冻结，冻结前不得执行生成）

- [ ] 3 题最终清单 + 各题冻结 artifact（arm 选定 + sha256）
- [ ] C0/C1 条件操作化定义（prompt 资产冻结）
- [ ] 六实体 JSON schema（对齐 Evidence Graph 现有契约，hash 链字段）
- [ ] 执行后端（Python 沙箱）与失败语义（timeout / 异常 / 数值发散的分类与记录）
- [ ] 验收脚本与门禁清单（对应 §2 五项能力，机器可判）
