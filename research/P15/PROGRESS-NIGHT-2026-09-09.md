# 夜间推进日志 — 2026-09-09（用户睡眠期间）

> 目标（用户指示）：持续让项目更完善；保持 Harness 定位；吸收他项目优点；设计深层实验思考原因；真正解决问题不盲目打补丁；全部记录文档、系统工程。

---

## 1. 会话状态快照

| 项 | 状态 |
|---|---|
| P15-K001 实验 | ✅ 已收口并 push（de15d96），negative result 归档 |
| 三仓库深度审计（Organizer `o_0001iK1w1XA`） | 🔄 运行中（~55%，三子代理证据收集阶段，dossier 未产出） |
| 本轮新增产出 | 4 项（见 §2），未 commit |

## 2. 本轮完成的独立工作（不依赖审计报告）

### 2.1 P15-K001 深度归因 — `research/P15/analysis/reports/P15-K001-ATTRIBUTION.md`
基于 55 个 knowledge_trace 全量实证分析，核心发现：
- **rejected 11 条 = Sham 错位卡 11/11 全部正确拒绝**（如 2019_C 拒 mc-numerical-pde"机理不匹配"、2018_A 拒 mc-dp"不存在离散决策阶段"）→ 外部 Agent 具备真实知识适用性判断，知识注入未产生盲从。
- used 80% / adapted 58% → 知识作为约束被改编应用，符合"constrains, not dictates"哲学。
- Negative result 四层归因：①信息增益 ceiling（LLM 已内化，A 臂基线已 37.7/42）②测量粒度（L2 不测过程与 L3/L4——已按 rubric 修正措辞）③注入剂量（每题 1 卡）④功效（n=11/臂，CI 宽）。
- Sham(Δ=+3.42) > K(Δ=+2.14) → "更多上下文处理效应"与"知识内容效应"必须分离，下一轮需指令长度对齐对照。
- 2 个 FAIL run（06cb0fb3/37f8a88b）均为 2020_B `sub_question_id=Q1` 单子问题覆盖——**真实 coverage 信号，子问题覆盖度是最强区分维度**，应升级为强制 gate。
- **按题效应分解（补充）**：效应全部来自 2020_B（Δ_K=+6.41，DP 卡与序贯决策结构深匹配）；2018_A 弱负（−2.56）；**2019_C 全臂恒定 87.18 零区分度**（实际有效 block 只有 2/3）→ 知识卡效应高度依赖题目×卡结构匹配深度；K002 已加入题目区分度预检。

### 2.2 知识库质量分层 — `research/P15/analysis/reports/KNOWLEDGE_BASE_QUALITY_BASELINE.md`
全量扫描 19 张方法卡字段结构（`card_quality_scan.py` + `.json`）：
- **Tier1（完整建模知识：mechanism+structure_signals+formulations+solvers）仅 3 张**：mc-dp / mc-numerical-pde / mc-queuing-theory
- **Tier3（缺 mechanism/formulations/solvers）16 张**（84%）：只有 requires/risks/validation/anti_patterns + P8 决策字段
- 关键推论：K001 注入的恰是库内最优 3 张 Tier1 卡仍 negative → 排除"注入劣质卡"解释；知识卡显式化内容 ≈ LLM 已内化内容（ceiling）；知识库真正的缺口在 **L1 结构覆盖**（game/network/scheduling）与**知识卡→MODEL_IR 结构化映射**（现为文本自由吸收）。

### 2.3 下一轮实验草案 — `research/P15/protocol/preregistration/P15-K002-DRAFT.md`
**P15-K002 Model Representation Efficacy**（DRAFT v0.1，待审计回填后定稿冻结）：
- 科学问题：**强制的结构化 MODEL_IR 输出契约是否本身提升外部 Agent 的 Model Construction Quality？**
- 设计：F（自由文本）/ S（强制 18 字段 schema）2 臂 × 主检验 3 题 × 5 rep + 泛化 2 题 × 3 rep = 42 runs；指令长度对齐 <10%；强制子问题覆盖 gate；rubric 与 K001 完全一致（跨实验可比）。
- 三种预先声明的结论形态（S>F / S≈F / S<F）分别对应：确立 Model IR 强制价值 / 强化"纯契约无增益"风险 / 结构化有害需重审。
- 直接回应审计风险 "Infrastructure without capability gain"——这是对 Harness 定位最关键的实证。

## 3. 关键结论（供早上汇报）

1. P15-K001 的知识注入机制本身健康（Sham 100% 正确拒绝），negative result 源于信息 ceiling + 测量粒度 + 功效，**不是"知识卡无效"**。
2. 知识库 84% 的卡缺建模机理段——但这不是实验瓶颈（注入的是最优卡），是**长期完善项**。
3. 下一杠杆明确：**Representation（结构化输出契约）**——它强制而非建议，是最可能产生真效应的 Harness 维度，也是验证项目定位的关键实验。
4. **2020_B 效应 = 知识卡防止子问题漏覆盖**（无知识臂 2 个 Q1-only FAIL，知识臂 0）——知识效应真实但极弱（n=1 事件）。

## 3.5 补充进展（继续深挖）

### 3.5.1 2020_B 效应精确定位 — `coverage_corrected.py` 实证
修正 L2.6 计分（满分即 3，不乘权重）后逐 run 重算：
- **Δ_K=+6.41 的全部来源 = 无知识臂（A/E）各 1 个 Q1-only FAIL run（61.5 分），知识/案例臂（B/C/D）0 个 FAIL（全 100）**——1 个稀有事件的臂间 0/1 差异（CI 触 0 的本质）。
- 机制：mc-dp 卡 structure_signals 明确列出 2020_B Q1–Q3 结构 → 真卡臂 Agent 被引导覆盖全部子问题。
- 2019_C 各臂产物哈希全不同（排除机械复制），但评分按 rep 完全同模式（92.3/92.3/76.9）→ 题目级区分度问题。
- **对 K002**：子问题覆盖 gate 是核心机械强制（不是评分项）；知识效应的可测载体是覆盖指标。

### 3.5.2 三仓库审计完成 ✅（Organizer o_0001iK1w1XA）
- 三份证据级 dossier 落盘 `research/REPOSITORY_AUDIT/dossiers/`：MathModelAgent（369 行）/ BZD（298 行）/ LinHoMo（640 行，自审）。
- **综合报告 `CROSS_REPO_AUDIT.md`**（17 节）已生成并 commit：
  - BZD = 评委经验提示词工程（零测试；6.81% 等无出处常数被确定性脚本包装成 IMPLEMENTED——最需警惕的反模式）；吸收：atomic-deduction-scoring / 字典字段设计 / 诚实条款。
  - MMA = LLM 文本接力流水线（Model 非一等对象、cookbook 路由、RAG/HIL 全 DOC_CLAIM）；吸收：Code Interpreter 抽象（execution adapter 参考）/ notebook 留痕 / 反射循环 / 模板。
  - LHM = 研究基础设施优于数学建模系统；六风险全部确认（result 占位、features 硬编码 evaluation、ontology 分叉、execution weakness 最高）。
- **P0 工程项确定**：①result 占位符治理（not_executed 状态）②`catalog/model_families.yaml` 单一词表 ③features 外部必传契约。

### 3.5.3 K002 DRAFT v0.2（审计回填）
- 1.4 审计启示节 + 6 章 P0 并行工程项 + S 臂受控词表 + n=63 修正 + RQ 编号修正 + 局限 5。

### 3.5.4 全量自检 + 收口
- pytest **774 passed / 11 skipped** ✅（50s）；catalog_check ✅；terminology 零残留 ✅；k001_freeze **44 文件无漂移 PASS** ✅。
- K001 状态机 **ANALYSIS → CLOSED** ✅（negative result 按决策门记录，不进 P15.2）。
- 2020_B 效应精确定位（coverage_corrected.py）：Δ_K 全部来自无知识臂 2 个 Q1-only FAIL（n=1 事件）；2018_A 噪声；2019_C 零区分度——K002 覆盖 gate + 区分度预检由此落地。

## 3.5.5 审计行动整合（AUDIT_ACTION_PLAN.md，已 commit）
- 六风险 → 行动项映射落盘：R5（execution weakness）→ P0 工程（experiment 节点真执行 + EvidenceGate 数值对账）；R6（ontology）→ K002 前置词表收敛；R1/R2/R4/R3 → 报告口径纪律 + K001 negative 作能力宣称基准。
- 可吸收清单（不污染 core）：BZD → 原子扣分公式/rubric 构造（reviewer 层）；MMA → Code Interpreter 抽象 + notebook 留痕（execution adapter，P1 工程）。明确拒绝：硬编码经验值（6.81%）、cookbook 路由、死配置。
- **K002 定稿裁决**：以三臂（F/S/S+V）为主，不扩 6 臂（K001 已测知识/Sham 臂，边际信息低；3 臂功效更高）；吸收审计 4 强制修正——block≥6（题目数 3→6，待定稿确认）、L3/L4 终点、族命中 primary OR secondary OR mechanism OR solver、词表先收敛。
- 四条红线写入：不变成 process management / schema 不冒充正确性 / infra 不冒充 capability / 不丢 LLM-free 定位。

## 4. 待办（审计报告回来后）

1. ~~三仓库审计报告回填~~ → ✅ AUDIT_ACTION_PLAN.md（六风险回应 + 吸收清单 + K002 裁决 + 红线）。
2. P15-K002 定稿：按行动计划 §3 的 4 强制修正 → PREREGISTERED → FROZEN（哈希锁定）。**待用户确认：题目数扩到 6+（block≥6）与 3 臂 vs 6 臂裁决**。
3. 知识卡升级（P1 工程项）：16 张 Tier3 卡补 mechanism/formulations/solvers，与实验分离。
4. L1 结构覆盖扩展（game/network/scheduling）过 Architecture Gate。
5. ~~全量自检 + commit + push~~ → ✅ 自检全绿（pytest 774/11、catalog OK、terminology 零残留、freeze PASS），10 个 commit 待 push。


---

## 追加：治理 v1.2 收口 + K002 预检 CLOSEOUT（2026-09-09 凌晨）

### 治理 v1.2（commit 8b23608 + 05c0ac1，已 push）
- 真正迁移（非注释兼容）：5 题 gt.json allowed_model_families→allowed_modeling_structures（旧字段删除）；
  e2e_metrics 输出键 method_selection→structure_alignment、detail 键同步、删 _method_hit 字符串兜底与 _load_card_names；
  k002_gen_bundles 删字段回退；catalog_check 删 # legacy compat 行内豁免。
- 校验范围统一：validate.py 新增 RESEARCH_PROJECT_PREFIXES + _is_research_scan_path，iter_repo 与 _live_project_dirs 共用排除语义；57/0 全绿。
- 引用路径：活跃文档 8 文件 22 处批量迁移 core/tools/evaluation/*→core/tools/*；删空目录；
  抓出测试真实缺陷 test_e2e_metrics.py sys.path 指向已删目录（单文件运行挂）。
- 新契约：P15-EXPERIMENT-CONTRACT-v2.md（八层节点标准 + 通信协议 + 扩展指引）。
- 历史文档：23 份 ARCHIVAL-NOTE + PRE_REGISTRATION v1 标 SUPERSEDED。
- 验证：pytest 855/4、catalog --check OK、--check-terminology OK、validate.py 57/0。

### K002 预检 CLOSEOUT（commit 384ee8c，已 push；Organizer o_0001iAuITsS finished）
- 12 runs（6 题 × {F,S}）全 GENERATED；主盲评 12/12；G2 三评估者 3×5 评分全落盘。
- 区分度：零区分度 0/6（全保留，不触发 STOP）；但 S<F 方向一致（6/6，Δ=-1~-3）→
  格式不对称风险（JSON vs MD 呈现给评估者）→ 协议新增盲评呈现层统一声明。
- L2 结构维度全 15/15 满分（饱和）→ MCQ_primary 保持 L2 口径（与 K001 可比），差异实测在 L3/非强制字段。
- G2：逐对 Cohen κ 平均 0.879（18/22=1.0）、加权 Fleiss 0.424（惩罚 B 的 +3 系统偏移）；
  分歧可归因（B 尺度偏移 + 天花板效应）→ G2 PASS（带校准条件：黄金样例锚定 + 离群评估者检测）。
- 产物：PRECHECK_REPORT.md、precheck_closeout.json、g2_kappa.json、analysis_summary.json。
- 下一步（待用户确认）：K002 PREREGISTERED → FROZEN（hash 锁定），或按 AUDIT_ACTION_PLAN §3 先做 4 强制修正。
