# 三仓库审计 → 行动整合计划

- **状态**：FINAL，审计已完成（2026-09-09）
- **上游**：`FINAL_REPORT.md`（18 节综合裁决）+ 三份 dossier（证据档案，全代码级）
- **本文件作用**：把审计结论转化为 LinHoMo 的可执行行动——吸收什么、回应什么、下一轮实验怎么定。不是重复报告，是决策清单。

---

## 0. 审计一句话结论

**BZD = 最深的"评委"（评审知识 + 5713 条字典 + 原子扣分公式，但知识→能力零因果证据）；MathModelAgent = 最快的"流水线"（真实 Code Interpreter 是唯一机械反馈回路，但 Model 只是流转字符串）；LinHoMo = 最诚实的"实验室"（唯一有预注册受控实验与负结果，但 runtime 零计算、知识因果未证实）。**

三者互补于「评审知识 — 执行基质 — 认知架构」三个象限。LinHoMo 的下一战不在知识库、不在 schema，而在**把计算接回 runtime、把表示变成一等对象、用受控实验证明这两件事提升了模型构造质量**。

---

## 1. 六风险逐条回应与行动项

| # | 风险 | 审计裁决 | 行动项 | 归属 |
|---|---|---|---|---|
| R5 | **Execution weakness**（认知架构强于执行基质） | 成立，跨仓库对比中最明显短板。V3 runtime 不做任何数值计算，result artifact 是占位符 `"{qid} 结论"` | **P0 工程：实验节点从"建台账"变"真执行"**——引入 MathModelAgent 式 Code Interpreter adapter（local jupyter + E2B 双实现 + notebook 留痕），result artifact 携带真实数值；EvidenceGate 从"边存在性"升级为"claim↔result 数值对账" | P1 工程（与实验分离执行） |
| R1 | **Formalized nonsense**（schema 合法但模型错误） | 防护网防"形式非法"，不防"内容错误"；P15 FAIL runs 结构合法只有人类 evaluator 发现 | 校验报告必须标注"结构校验/语义校验"边界；K002 的 validation_plan 字段规格（已写）就是机械化的语义自证尝试 | K002 执行中兑现 |
| R2 | **Over-formalization**（变成科研流程管理系统） | 部分成立，项目已自警（THREE_LAYER_ARCHITECTURE） | **红线 1**：新增代码若永远在"记录/校验/投影"而从不"计算/求解/执行"即越界 | 工程纪律 |
| R4 | **False confidence**（契约完善→错误安全感） | 真实存在且有反例（2019_C 评分饱和、RQ5 词表错位、REGISTERED≠正确） | 报告口径纪律：禁止把 validate.py PASS 表述为"模型正确性验证通过"；负面观测照实写（已在 K001 报告实践） | 写作纪律 |
| R6 | **Ontology weakness**（family/mechanism/method/solver 未完全分离） | RQ5 实证：`discrete_recurrence` vs `dynamic_programming` 同一思想两种命名 | **K002 前置：统一枚举注册表 `catalog/model_families.yaml`**，受控词表在实验前收敛；族命中改"primary OR secondary OR mechanism OR solver" | K002 前置 |
| R3 | **Infra without capability gain**（基建增多质量未升） | 当前证据不足以定罪（实验测的是知识注入不是基础设施），但方向需警惕 | 任何"新增 X 提升了系统"的宣称必须附因果实验或标注为推断；K001 negative 作为一切能力宣称的基准 | 实验纪律 |

---

## 2. 可吸收清单（不污染 core 语义）

### 2.1 从 BZD 吸收（进入 knowledge / reviewer / competition 层，不进 runtime core）

| 吸收项 | 进入位置 | 状态 |
|---|---|---|
| 原子扣分公式 + rubric 构造（`problem_earned=max(0,0.90×w−Σdeductions)`、90% 评委封顶、格式系数确定性映射） | reviewer policy / judge-critic 规则层 | 记录为设计参考，P1 评审层演进时采用 |
| `award_position.py` 锚点插值 + 学校/赛区/教师与质量分严格分离 | competition methodology 层（独立数据资产） | 记录；不引入无来源经验值 |
| model-dictionary 字段设计（假设/禁忌点/缺陷/检验方法） | 知识卡 schema 措辞规范对照 | 记录；现有卡已含 risks/known_failures/validation |
| **不吸收**：硬编码经验值（6.81%、30–50%、advisor_multiplier）——"DOC_CLAIM 包装成 IMPLEMENTED"是审计中最危险模式，与 LinHoMo 证据纪律直接冲突 | — | 明确拒绝 |

### 2.2 从 MathModelAgent 吸收（进入 execution adapter，补 R5）

| 吸收项 | 进入位置 | 状态 |
|---|---|---|
| Code Interpreter 抽象层（base_interpreter + factory + local/e2b 双实现） | **execution adapter（最高优先级，直补 R5）** | P1 工程项，待排期 |
| notebook 全量留痕（每次执行追加 code cell + output） | experiment evidence 记录，挂 Evidence Graph produces 边 | P1 工程项 |
| 反射循环（异常→反思→重试带上限） | external executor 自愈参考 | 设计参考 |
| **不吸收**：cookbook 关键词路由、markdown 报告充当 Model、死配置（RAG/HIL/Tavily/Fallback）、round(4) 子串"数值一致性" | — | 明确拒绝 |

---

## 3. P15-K002 定稿裁决（DRAFT v0.1 → 定稿方向）

**现状**：`research/P15/protocol/preregistration/P15-K002-DRAFT.md` 为三臂设计（F 自由文本 / S MODEL_IR / S+V MODEL_IR+Validation Plan），63 runs，双主终点（MCQ_primary=L2、VAL_primary=L4）。

**审计报告 §16 建议 6 臂**（A Baseline / B 知识注入 / C Sham / D MODEL_IR / E Structured+Evidence / F Critic）。

**裁决（本计划采用）**：**以三臂（F/S/S+V）为主设计，吸收审计的 4 个强制修正，不扩成 6 臂**。理由：

1. **K001 已测量过知识（Δ_K=+2.14 贴零）与 Sham（+3.42 跨零）**——B/C 两臂的边际信息已由 K001 提供（虽然未分离，但那是功效问题不是设计问题）。K002 要回答的是全新问题：**表示/证据是否有效**。
2. 同样 run 预算下，3 臂每臂 n 翻倍 → 功效提升，直接回应 K001 "block=3 功效不足"的根因。
3. 若 S/S+V 显著优于 F，表示/证据效应成立；若否，则 harness 能力增益承诺被证伪——两种结果都干净。知识/上下文假说留给后续（如需可加第 4 臂 BZD 式知识注入）。

**K002 必须满足的 4 个审计强制修正**：
- [ ] **block ≥ 6**：题目数从 3 扩到 ≥6（K001 block=3 最小 p=0.25 是功效失败根因；block=6 → 2^6=64 置换，最小 p≈0.016）。需新增 ≥3 道高质量题（不进 5 题校准样本？—— 待定稿时定：K002 用独立 6 题还是校准 5 题 + 新题）。
- [ ] **终点扩展**：L2（结构完备）+ L3（可执行性/可解性）+ L4（数值正确性，针对有标准答案子问题）。
- [ ] **族命中修复**：primary OR secondary OR mechanism OR solver 任一命中即算族命中（修复 RQ5 词表错位）。
- [ ] **受控词表先收敛**：`catalog/model_families.yaml` 统一枚举注册表，模型生成侧与评分侧共用。

**下一动作（待用户确认后）**：DRAFT v0.1 按上述修正 → v1.0 PREREGISTERED → FROZEN（哈希锁定，沿用 k001_freeze 纪律）→ 生成侧分片执行。

---

## 4. 四条红线（写入本计划即生效）

1. **不变成 research process management system**：新增代码若永远在记录/校验/投影而从不计算/求解/执行，即越过红线。
2. **schema validity 不冒充 mathematical correctness**：校验报告必须标注结构/语义边界。
3. **infrastructure growth 不冒充 capability gain**：能力证据只能是受控实验的 Δ；K001 negative 是后续一切能力宣称的基准。
4. **不丢失 LLM-free Harness 定位**：core 保持零 LLM 确定性；LLM 只在 external executor 层以 provenance 记录方式参与。

**附加（RQ5 教训）**：受控词表分叉必须通过统一枚举注册表收敛，否则"词表对齐度量"反复污染指标解读。

---

## 5. 状态与下一步

| 项 | 状态 |
|---|---|
| 三仓库审计（dossier + FINAL_REPORT） | ✅ 完成，已 commit（bdb11ee） |
| 审计行动整合（本文件） | ✅ 完成 |
| 全量自检（pytest 774/11、catalog_check OK、terminology OK、freeze PASS） | ✅ 完成 |
| K002 定稿（DRAFT→v1.0 FROZEN） | ⏸ 待用户确认裁决方向 |
| 统一词表注册表 catalog/model_families.yaml | ⏸ K002 前置，待排期 |
| Code Interpreter adapter（R5 修复） | ⏸ P1 工程，待排期 |
| P15-K001 状态机推 CLOSED | ⏸ 等用户验收 |
