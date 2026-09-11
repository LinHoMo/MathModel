# Task Board / 任务看板

> 本文件是 Agent 任务的唯一登记处（见 AGENTS.md §1 必读顺序第 4 项）。
> 状态真源：`docs/STATUS.md`；本看板登记**任务级**状态（进行中/待办/已完成），两者不重复记账。
> 已裁定项（T-CONF-xxx）关闭时在「已完成」登记裁定结果。

## In Progress / 进行中

| ID | Task | Agent | Status | Acceptance |
|----|------|-------|--------|------------|
| — | 阶段七（新实验模板 P3）待启动；前置：T-CONF-003（K004 已存在，方向确认） | MainAgent | 待确认 | 阶段六已交付，等待用户裁定后进入 |

## Todo / 待办

| ID | Task | Priority | Acceptance | Blocked By |
|----|------|----------|------------|------------|
| T-P3-01 | K005 模板 + K004 protocol 整理（K004 实验已存在于 P15/k004） | P3 | protocol/ 下模板存在；含 6 节 | — |
| T-P3-02 | 新实验方向决策（K 系列 vs Constructor 集成实证） | P3 | 决策记录进 TASKS.md | T-CONF-003 |
| T-CONF-003 | 待确认：K004 已有实验与报告——继续补 K005，还是转向 Constructor 集成实证 | — | 裁定后执行 T-P3-01/02 | 用户 |
| T-CONF-006 | 裁定：`domains/` 标注预定义冻结（README + docstring 声明接入条件），不删除不接入 | 2026-09-10（用户裁定，随 profiles commit） | | |
| T-CONF-007 | 裁定：发行名改为 `modeling-harness`（PyPI 未占用，实测 pip index 无匹配） | pyproject.toml:6（随 profiles commit） | | |
| T-CONF-008 | 裁定：`MATHMODEL_AGENT_API` 保留（外部专名，docstring 提及、代码未读取） | 2026-09-10（用户裁定） | | |
| T-CONF-009 | **待裁定**：P15 冻结校验失效——三项 `*_freeze.py --check` 均 FAIL（K001 19 / K002 20 / K003 4 处漂移）。根因：`research/P15/protocol/frozen_specs*/` 的规格仍记录 src/ 重构前的 `core/...`、`catalog/...` 路径，磁盘已迁至 `src/modeling_harness/...`；叠加 gt.json 治理变更（术语迁移 / `l6_assertions`）。选项 ① 迁移 spec 路径 + 重冻（新 revision、冻结清单变更，须评估是否作废 v1.0 数据）② 维持不重冻 + STATUS 标注 FAIL（已做）。**建议 ①**（路径迁移部分内容未变、可无损重冻；gt.json 变更并入同一次 revision） | — | 用户 |

## Done / 已完成

| ID | Task | Commit | Date |
|----|------|--------|------|
| T-REBUILD-01 | 技术层重构（src/ layout、modeling_harness 包、mh CLI、MH_* env、.mh/ 配置、MH- ID、modeling_harness.* schema、迁移脚本） | `1b5e2e7`+`e4add47`+`65be4d8`+`ef2afe8`+`8838fda`+`1cebd09`+`68e90be`+`6ee233c`+`bdaddbc`+`9913a2b`+`86e087e`+`b684856`+`6408f35`+`63f5ddc`+`40d1989`+`1b58fee`+`062c357` | 2026-09-10 |
| T-REBUILD-02 | 终审整改：L1.1 校验真实输入规约（44/1 修复）；schemas/legacy → retired 归档更名；domains/ adapters/ 上提顶层（ADR-0006）；迁移垃圾清理（build/、__pycache__、.pytest_cache、worktree 残留、一次性脚本） | `40d1989`+`1b58fee`+`062c357`（垃圾清理不入库） | 2026-09-10 |
| T-REBUILD-03 | 独立只读终审闭环：CI lint 门禁实跑修复（448 ruff + 4 F821 + L5.4 真实化，validate 假绿→45/0 真绿，CI run 34464939588 ✓）；终审遗留修复（P1-3 schema 品牌残留、P2-2 ids docstring、P2-4 AGENTS catalog 行）；CI 二跑 34465503822 验证 | `fdd6213`+`84d71cd` | 2026-09-10 |
| T-BRAND-01 | 品牌迁移 MathModel → Modeling-Harness（品牌层替换 + 发行名 + MIGRATION.md + CHANGELOG 条目 + GitHub 改名/description/topics） | `9809047`+`6663d02`+`550f9ef`；GitHub 已改名 | 2026-09-10 |
| T-P0-01 | 重写 research/README.md（仅 ENGINEERING/ 与 P15/） | `d3c4f83` | 2026-09-10 |
| T-P0-02 | 创建 research/P15/README.md（K 系列状态+实验地图+报告索引） | `d3c4f83` | 2026-09-10 |
| T-P0-03 | 清理 docs/architecture/ 论文残留（6 文件 14 处） | `d3c4f83` | 2026-09-10 |
| T-P0-04 | 修复 pyproject.toml markers（COMPATIBILITY_POLICY/Syslab/LaTeX） | `d3c4f83` | 2026-09-10 |
| T-P0-05 | 修复数字不一致（58→45；五组→六组） | `d3c4f83` | 2026-09-10 |
| T-P0-06 | 清理 .gitignore LaTeX 段 + main.aux 残留 | `d3c4f83` | 2026-09-10 |
| T-P0-07 | VS001 报告核验：两份为不同实验，保留正文 | `d3c4f83` | 2026-09-10 |
| T-P1-01 | LICENSE（MIT，LinHoMo） | `b34cb4e` | 2026-09-10 |
| T-P1-02 | .python-version（3.12） | `b34cb4e` | 2026-09-10 |
| T-P1-03 | CI 添加与修复（push main；pyyaml/jsonschema/ripgrep） | `b34cb4e`+`e19a24a`+`18e49ea` | 2026-09-10 |
| T-P1-04 | CONTRIBUTING.md（个人仓库声明，不接受 PR） | `b34cb4e` | 2026-09-10 |
| T-P1-05 | v3.2.2 tag + GitHub Release | `b34cb4e`（tag 锚点） | 2026-09-10 |
| T-P0-08 | 重写 AGENTS.md（中英双语，323 行，12 节） | `0a1e425` | 2026-09-10 |
| T-P0-09 | 创建 TASKS.md（本文件） | `0a1e425` | 2026-09-10 |
| T-P0-10 | 创建 prompts/（6 文件） | `0a1e425` | 2026-09-10 |
| T-P1-06 | 创建 docs/README.md 文档索引（33 链接全通） | `0a1e425` | 2026-09-10 |
| T-P1-07 | 创建 ADR 体系（7 文件） | `0a1e425` | 2026-09-10 |
| T-P1-08 | CONTRIBUTING.md 补分层依赖说明 | `0a1e425` | 2026-09-10 |
| T-P1-09 | core/runtime/README.md（23 行，12 子域） | `71a0310` | 2026-09-10 |
| T-P1-10 | core/tools/README.md（25 行，15 CLI） | `71a0310` | 2026-09-10 |
| T-P1-11 | core/knowledge/README.md（32 行，含历史目录说明） | `71a0310` | 2026-09-10 |
| T-P1-12 | catalog/README.md（21 行，双视图） | `71a0310` | 2026-09-10 |
| T-P1-13 | tests/README.md（20 行，分层+夹具） | `71a0310` | 2026-09-10 |
| T-P1-14 | 14 份 architecture 文档补版本头（Version/Status/Updated） | `71a0310` | 2026-09-10 |
| T-P2-06 | AGENTS.md 七处修正（六要素/去硬编码/CI 门禁/§5 禁令/§7.1 文档纪律） | `117aecb` | 2026-09-10 |
| T-P2-07 | 代码内断裂引用修复（e2e_metrics/benchmark/catalog_check） | `0eddf45` | 2026-09-10 |
| T-P2-08 | 顶层 9 个 V2 schema 归档 legacy/ + 双 README | `596e756` | 2026-09-10 |
| T-P2-09 | fixture 处置：删 sample_paper_project，保留 sample_incomplete + README | `fdfa2ec` | 2026-09-10 |
| T-P2-03 | paper-cases → cases 更名（T-CONF-004 裁定：更名保留，117 文件） | `514bb17` | 2026-09-10 |
| T-CONF-005 | 裁定：VS001 两份报告保留，不删除不合并 | 阶段一裁定（无 commit） | 2026-09-10 |
| T-CONF-001 | 裁定：P15 **保留在主树**（撤销移出决策；K001–K004 为 Constructor 实验证据） | 用户裁定 + `ae8ca2a` | 2026-09-10 |
| T-CONF-004 | 裁定：paper-cases 更名 cases 保留（建模知识，非论文产物） | `514bb17` | 2026-09-10 |
| T-P2-04 | pyproject version 1.0.0 → 3.2.2（T-CONF-002 裁定：改） | `528b277` | 2026-09-10 |
| T-P2-05 | 发布流程文档 docs/RELEASE.md（4 节） | `531dd22` | 2026-09-10 |
| T-P2-10 | AGENTS.md 冻结 v1.0 + CHANGELOG 记录 | `7d03bfc` | 2026-09-10 |
| T-CONF-002 | 裁定：pyproject version 改为 3.2.2（与 tag 一致） | `528b277` | 2026-09-10 |
| T-INST-01 | `projects/cumcm2024a-harness` 2024_A 全问建模交付（弦长约束刚性链模型；Q1–Q5 真实执行；model_ir.json + model.md + all_results.json + state 五件套；独立复核碰撞判定一致到 1e-6） | `e62ab07` | 2026-09-10 |
| T-INST-02 | `projects/cumcm2026a` 2026_A 药材烘干全问建模交付（径向耦合传热传质 PDE + Landau 移动边界；Q1/Q2 过程场、Q3 57.4222 h、Q4 64.7806 h 终半径 1.2721 cm；空间/时间收敛 + 温度敏感性实测入台账；四件套 + state） | `e62ab07` | 2026-09-10 |
| T-INST-03 | `projects/cumcm2026b` 2026_B 干扰源定位清除全问建模交付（楔形交会凸多边形 + 最小包围圆 + Thales 覆盖判据 + GDOP 第二点 + 同心环覆盖 + 交会-归航清除；30 组演练清除比例 1.0000，Q3 7150.10 s / Q4 15088.79 s；覆盖漏检率 0.0000 / 0.00025；四件套 + state） | `e62ab07` | 2026-09-10 |
| T-FB-01 | 反馈修复 harness：validate.py 图表引用改逐行围栏状态机（原 `content.count` 比较会把任何合法 Mermaid 块误判为未闭合）；`new_project.py` README 模板与两题 `model/README.md` 去内部路径泄漏（L5.4） | `e62ab07` | 2026-09-10 |
| T-FF-01 | 前馈沉淀知识：方法卡 `mc-moving-boundary-pde` / `mc-bearing-triangulation` / `mc-coverage-search`（24→27）+ 失败卡 5 条（17→22）+ playbook 2026A/2026B（12→14）；`knowledge/README.md`、`playbooks/INDEX.md` 规模数字同步 | `e62ab07` | 2026-09-10 |
| T-HANDOFF-01 | 交付交接文档：`projects/cumcm2026a/HANDOFF.md` + `projects/cumcm2026b/HANDOFF.md`（实例级：建模骨架/结果/结构性发现/踩坑/验证/局限/门禁/最短路径）+ `docs/HANDOFF.md`（跨题 harness 层：四件套门禁口径/本轮修复清单/前馈沉淀规模/P0-P2 backlog/工作序）；修复两篇实例交接触发 L5（禁用词举例自伤、内部路径后缀）；`.rivet/` 入 `.gitignore`；`docs/README.md` 登记 + `docs/STATUS.md` 同步 | `6a50eb7` | 2026-09-10 |
| T-FEEDBACK-01 | 实例反馈闭环（ADR-0008）：三交付实例可读、可对账、可度量——registry 子问题由 1/1/1 → 5/4/4（每问独立 artifact），`MH-MODEL_IR-0001` 内联 MODEL_IR 契约字段，narrative → deliverable，payload 路径全解析，状态投影由 `ProjectState.refresh_from` 派生（唯一入口 `scripts/state_projection.py`）。harness 反馈：「实例状态契约」门禁（validate 46/0/0，覆盖扁平投影/非法维度值/退役类型/路径悬空），schema 对齐（narrative/paper 从必填降为历史容忍）。2024_A 分解覆盖 20.0→100.0，模型结构检查 legacy_pointer→PASS，三实例 reconcile ok=True。报告 `docs/PROJECTS_FEEDBACK_AUDIT.md`；未闭合项如实登记（方法结构对齐词表缺口 / 2026 真值卡缺失） | 628 passed，validate 46/0/0 | 2026-09-10 |
| T-INST-04 | 赛题材料归位：A/B 题 PDF + 附件（A 题附件1/2/3 xlsx、B 题附件1/2 docx）复制入各自 `inputs/`，作为唯一输入真源留痕 | 目录实测 | 本轮 |
| T-INST-05 | A 题 v1.1 精细适配：附件1 实测温湿度（241 行）插值驱动边界替代指数趋近+阶跃；附件2 实测半径（145 行）驱动问题4 移动边界，产出实测/守恒双解对照。Q3 57.1722 h、Q4 实测 52.3111 h vs Landau 64.5667 h；收敛+敏感性实测入台账 | solve_a v1.1 实跑，validate 46/0/0 | 本轮 |
| T-FB-02 | harness 数值追溯改进：`check_numeric_traceability` 增补题面输入为合法溯源目标（结果→all_results.json、题面常数→inputs/problem.txt），消除物理常数误报（升级边界条件不再误压低追溯比例）；`tests/unit/test_numeric_traceability.py` 3 单测锁定语义 | 631 passed，validate 46/0/0 | 本轮 |
| T-INST-06 | B 题真实模拟器协议构建（v1.2）：按《B 题附件2·模拟器通信接口说明》实现 `SimulatorHTTP`（4 指令 / arena_id / position / measure_result / svd_deg / clear_result，时间服务端计算）+ 规范忠实 `MockSimulatorServer`；策略适配真实 API（**不返回信号强度** → 纯示向度交会 + 越界检测归航，失联回退最近可测点处理定向盲区）。Mock 演练各 5 组：Q3/Q4 清除比例均 1.0000（Q3 虚拟 12918.09 s / Q4 22592.91 s）。**未接官方评测机**（需 GUI 登录） | 端到端 Mock 验证，validate 46/0/0 | 本轮 |
| T-ANALYSIS-01 | 模型质量与创新性判据草案（DRAFT，待评审）：针对"有理论基础、无创新构建与规范产出"的系统性缺口，立**独立于 harness 自身打分**的可操作判据（S1 假设最小性 / S2 验证覆盖 / S3 不变量 / S4 溯源 + E1 样本外 / E2 基线 delta / E3 稳健性），含反模式清单、与现有 L3/L4 门禁的关系、κ 处置、以及**判据自身的证伪条件** | `docs/architecture/MODEL_QUALITY_CRITERIA.md` | 本轮 |
| T-GOV-01 | 治理加固：新增 L4 门禁「参数来源」（`check_parameter_provenance`）——声称 `problem_given` 的数值参数须能在题面原文匹配（仅允许 ×10^k 单位换算）；非批准词表的 `source` 拒绝。首跑揪出 `cumcm2024a:P15` 错标（4.5 m 半径实为直径 9 m 推导，改标 `derived`）。TDD：先写 5 单测（RED）再实现（GREEN） | 636 passed，validate 47/0/0 | 本轮 |
| T-GOV-02 | 模型质量判据（标准层）+ G3 校准参数门禁：判据升 FROZEN；新增 `check_calibration_parameters`（非豁免参数须有 `calibration_anchor_ref` + 台账 `calibration_sensitivity`）；A 题 P08/P12 补锚定、`solve_a` 参数化时间常数 + τ 扫描产出敏感性证据。TDD 6 单测；真实数据 RED 命中；反向验收（注入→拦→字节级还原） | 642 passed，validate 48/0/0，catalog OK，术语 OK | 本轮 |
| T-CAP-01 | 能力层：结构可识别性 + 词表修订 r1。新增 `cli/structure_coverage.py`（结构解析 + 覆盖率度量，只读词表），把「方法结构对齐」由不可用变可算：修订前 10/19=52.6% → 按 Architecture Gate 复核修订（ADR-0010）后 19/19=100%。TDD 6 单测 | 648 passed，validate 48/0/0，catalog OK，术语 OK | 本轮 |
| T-CAP-02 | 能力层：方法卡登记与族挂卡。2026 相关族挂卡（numerical_pde/computational_geometry/coverage_path_planning）；2026 A/B 实例 `model_family.cards` 登记选型；`structure_coverage` 新增「方法卡登记率」度量（0/3 → 2/3，2024a 未登记如实暴露）。TDD 3 单测 | 651 passed，validate 48/0/0，catalog OK，术语 OK | 本轮 |
| T-THEORY-01 | 理论基座缺口审查与优化方案（REVIEW，只读审查 + 提案）：10 维度分析（正向认识论/创新/简约/测量/因果/证据语义/泛化/学习/预测范式/实验文化）+ 两条主线 + 三阶段路线图 + Innovation Space 提案 + K 系列下一梯队实验设计（E1–E8）。未修改代码/schema/runtime；立项须走任务卡 + ADR。产出 `docs/THEORY_FOUNDATION_REVIEW.md`；方案待用户裁定（建议 T-CONF 4 项） | 交付审查文档；四件套待跑 | 2026-09-11 |
| T-THEORY-02 | 标准层 G4 证据义务矩阵门禁：MODEL_IR 顶层 opt-in `evidence_obligations`（EV1–EV5，前缀规避 Evidence Gate E1–E9）；声明层须有机械证据支撑否则 FAIL；实例级粒度 | 单测 10 + 实例反向验收 | 本轮 |
| T-THEORY-03 | 标准层 G5 复杂度预算门禁：参数付租（id/符号归一化/名称/值信号）；修复 2026b P13/P14 真实误报（字符串值 + 浮点格式）并固化回归（值拆分、int↔float、分隔符变体）；消息报 param/used/eq/mech | 单测 9 | 本轮 |
| T-THEORY-04 | 标准层 R4 创新声明契约门禁 + R3 结构距离工具（`cli/innovation_metrics.py`，声明优先/一阶二值回退） | 单测 12 | 本轮 |
| T-THEORY-05 | 三实例合规声明（evidence_obligations + innovation）+ registry sha256 同步 + 反向验收（注入非法层 E9/移除论证 → FAIL，还原 → PASS） | validate 51/0/0 | 本轮 |
| T-THEORY-06 | 文档同步：判据 v1.1（G4/G5/R3/R4 定义 + 局限披露）+ 审查文档落地状态与 §9 遗留项 + STATUS/CHANGELOG/TASKS + 四件套 | 683 passed，validate 51/0/0，catalog OK，术语 OK | 本轮 |
| T-THEORY-07 | 标准层 v1.2（REVIEW §9.1/9.2/9.5 落地）：used_in 显式引用契约（七类 ref 硬校验/越界拒绝）+ 双级门禁（显式破损硬 FAIL、启发式降 WARN）+ G4 evidence_refs 对象形态 + 三实例 46 参数显式化（scripts/_gen_used_in.py 机器扫描+人工抽审）+ 门禁金标准（fixtures/param_usage_gold.json，FP=FN=0）+ 失败卡 fm-gate-heuristic-false-positive（22→23）+ 判据 v1.2/ONTOLOGY #15–20/REVIEW 勾销 | 700 passed，validate 52/0/0，catalog OK，术语 OK，金标准 FP=FN=0 | 本轮 |
| T-THEORY-08 | 创新短板专项（第二步，本轮）：§9.3 R3 连续结构距离（本体图 O + 连续 sim + 声明审计 WARN + `--json`）✅；§9.4 G4 子问题粒度（下钻 sub_question_binding + 显式 opt-in 保护历史实例 + 证据独立性提示）✅；§9.7 工具打磨（G5 死参数信号明细自解释 + artifacts/data/*.csv 语料扩展，金标准 FP/FN=0 守护）✅。**§9.6 符号映射表（声明符号↔代码标识符）不在本轮选定范围，仍 OPEN**。 | 714 passed，validate 52/0/0，catalog OK，术语 OK，金标准 FP=FN=0；三实例反向验收（注入 scope→FAIL→还原→PASS） | 本轮 |
| T-DOC-01 | 文档漂移与仓库卫生（handoff 诊断 backlog）：README v3 域数七→八、tests 分层 regression→research/runtime；tests/README 计数按实测重算（76 文件/698 函数/719 passed）；schemas/README 归档名 legacy→retired；STATE_TRUTH §1.1 如实标注 Event Log 无独立实现；.gitignore 忽略 cumcm2026b 本地模拟器目录（含 .exe + sqlite）。**核验否决两条 handoff 误判**：README:29「V3.1」是架构版本非漂移；AGENTS.md 无 Stack 块（该块是 .rivet-config.json 的系统注入，非 AGENTS.md 内容） | `a83d7e5`（719 passed，validate 52/0/0） | 本轮 |
| T-GOV-03 | 门禁可信度：`validate.py` L4 三处 fail-open 加固（`check_parameter_provenance` / `check_evidence_obligations` / `check_parsimony_budget` 在 model_ir.json 解析失败时由 `except: continue` 静默放行改为阻塞）。TDD：独立探针复现 RED（修复前 HEAD 三处均 ok=True）→ 工作区三处 ok=False（消息指名实例与原因）；保留「无 model_ir.json / 无活跃实例 → 跳过」既有语义；新增 `tests/unit/test_validate_fail_closed.py`（4 例）。同类残留（`check_calibration_parameters` L847、`check_innovation_declaration` L1464）如实登记未修 | `7f9670b`（719 passed，validate 52/0/0，ruff 全过） | 本轮 |
| T-GOV-04 | 承接 T-GOV-03 的同类残留：`check_calibration_parameters` / `check_dead_param_scan` / `check_innovation_declaration` 三处解析失败由静默放行改为写 problems（block / WARN 软层）；`test_validate_fail_closed.py` 的 `_CHECKS` 3→6 | `711808d`（726 passed，validate 52/0/0） | 本轮 |
| T-ENV-01 | env loader 死路径清理：移除 `_PROFILES_DIR` / `available_profiles()` / `profile_name()` 与 profile 差量合并块（全仓 grep 零生产调用方；`test_env.py:53` 本就断言该目录不存在）；示例键 paper.*→code.* | `b5a0634`（726 passed） | 本轮 |
| T-CAP-03 | competition 语义透传：`RuntimeSession(competition=...)` → `compose_executable` + `DefaultNodeExecutor(competition_type=...)`，竞赛包由 `cp-cumcm` 硬编码改为「显式 cp-<type> 优先 → 缺省回退」；新增 7 例零 mock 集成测试 | `7a38ede`（726 passed） | 本轮 |
| T-INST-07 | cumcm2026b 产物确定性（重跑反馈发现的四源）：①`ProjectState.refresh_from` set 迭代→有序去重；②`_utcnow` 增 `MH_STATE_NOW` 注入钩子；③`build_state` 时钟经 env 注入并回写同源；④`resultB.xlsx` 归一 core.xml.modified + 固定 zip entry date_time。另统一 `all_results.json` 多写方为 merge 语义。固定时钟实测：state/ 两次字节一致、resultB.xlsx 两次 sha256 一致 | `6acebf2`+`d5e1bd2`（726 passed，validate 52/0/0） | 本轮 |
| T-FF-02 | 前馈沉淀（重跑反馈）：失败卡 3 张 23→26——`fm-state-projection-nondeterminism` / `fm-shared-aggregate-overwrite` / `fm-console-encoding-gbk`；`knowledge/README.md` 计数同步 | `4b42a7e`（知识测试 18 passed，load_knowledge failures=26） | 本轮 |
| T-DOC-02 | 交接文档核验（只读，无 commit）：**否决 handoff 两条误判**——README:29「V3.1」是架构版本非包版本漂移；AGENTS.md 无 Stack 块（该块是 .rivet-config.json 系统注入）。**纠正计数同步范围**——失败卡计数仅 `knowledge/README.md` 一处（先例 6a62ea2 只改 README + 新卡），`playbooks/INDEX.md` 并无该计数。另发现 handoff 卡点 1 的修法不足以达成其自设验收（`_utcnow` 是未被覆盖的第三源） | 核验记录 | 本轮 |

| T-SEL-01 | 候选选型 objective-first（ADR-0014）：`runtime/execution/handlers.py::_rank_candidates` 排序键在原 `constraint_violation_max` 之前插入 `objective_value`（按 `objective_direction` 归一），弥补 ADR-0013 只覆盖 `comparison.py::compare_models` 的缺口（P1-M3 生产选型路径此前不读目标值，两个都合规的候选由 mir_id 字典序决胜）；`SELECTION_CRITERIA` 登记目标值判据；选型 reasoning 报目标值依据（不可得时显式标注回退验证质量）。TDD：新测试 `tests/unit/test_selection_objective_rank.py` 首跑 5 failed → 实现后 8 passed；mypy 无净新增（对照 HEAD worktree 基线 42 errors） | 860 passed，catalog OK，术语 OK，ruff 全绿；validate 53/1（数值追溯 FAIL 系既有，HEAD worktree 同现） | 本轮 |

| T-SEL-02 | 候选机制策略对象化 + 信息感知第三候选（M-SELECT-002）：候选由裸点集升级为 `{name, points, sweeper?}` 规格对象，`solve_b_http.dog_strategy_http` 新增 `sweeper` 接入点（缺省 None 行为不变）；新增 AIFIX 候选（复用 RING 几何、单变量对照「何时 engage」）；`select_best` N-候选选择器。**等价性证据**：重构后 RING−SPIRAL 配对差与 M-SELECT-001 逐位相同（Q3 −535.0±1166.2、Q4 +2029.2±756.5）。**结果（如实，含负结果）**：AIFIX 与 RING 不可分（Q3 −91.2±404.7 s / Q4 +485.9±1348.8 s，均落 95% CI 内）——交错扫描未显示统计可辨优势。M-SELECT 数字经 `all_results.json` 台账并入通道（同 solve_b_http 的 real_protocol_mock 惯例）变为可溯源，validate 由 53/1 转 **54/0** | 860 passed + 项目测试 46 passed，validate 54/0/0，catalog OK，术语 OK，ruff 全绿 | 本轮 |

| T-SEC-01 | ExecutionResult 来源豁免收紧（ADR-0015）：`runtime/artifacts/registry.py::_check_exec_auth` 的 `legacy_unverified` 豁免由 payload **内自授权**改为 **registry 实例显式开启**（`ArtifactRegistry(path, allow_legacy_unverified=True)`）；默认实例即便 payload 带该键也照常校验 execution_token。5 处测试夹具改为构造器声明豁免（语义不变，非篡改测试）。TDD：新测试 `tests/unit/test_registry_legacy_gate.py` 首跑 3 failed → 实现后 4 passed | 864 passed（860+4），ruff 全绿 | 本轮 |

| T-DOC-03 | 文档卫生（本会话收口）：① `docs/STATUS.md` 当前数字按机器实测更新（pytest 792→**864 passed**、项目级校验 53→**54 通过 / 0 失败**），并新增本会话阶段历史行；② 修正 `docs/architecture/V3.1_ARCHITECTURE.md` 两处实现漂移——§1.8 role 数「五个（含 writer）」→ **四个**（writer 随 v3.2.2 论文链删除）、§1.4 profile 路径 `workflows/competition/` → **`profiles/competition/`**（实现在 profiles 包）；③ `research/P15/README.md` 加历史引用说明（`p151-*` 项目目录已按用户指令删除，残留审计引用**保留原文不回改**，需原始产物回溯 git 历史） | validate 54/0/0，catalog OK，术语 OK | 本轮 |

| T-VERIFY-01 | 全项目校验（含工作区未提交改动）：pytest **864 passed** / validate **54 通过-0 失败-0 警告** / catalog OK / 术语 OK / doctor **就绪 13-警告 0-阻塞 0** / ruff（CI 口径 `src/modeling_harness scripts`）All checks passed。**校验发现并据实修正一处假 PASS**：STATUS.md 的 K001/K002/K003 冻结校验原标 PASS，实测三项均 FAIL（19/20/4 处漂移，根因 = src/ 重构后冻结 spec 路径未迁移）；已改为 FAIL + 根因说明，并登记 T-CONF-009 待裁定。冻结校验不在 CI 范围（`.github/workflows/ci.yml` 只跑四件套 + lint），不影响 CI 绿 | 见上（均为本轮实测输出） | 本轮 |

| T-MODEL-01 | 候选多样性落位（ADR-0016）Step 1：**修确定性与保真缺陷** —— `Candidate.from_dict` / `InnovationCandidate.from_dict` 与 `as_dict()` 对称；`handlers.do_experiment_design` 的重建路径由手写字段子集改为 `Candidate.from_dict(top)`。此前漏传 `innovations`，使 `planner.plan_from_candidate` 的创新专用分支恒空转（`decision_rule=gain > cost` / `failure_detection=inno.risk[0]` 永不生成，创新要求降级为普通「候选方案要求」）。TDD：新测试 `tests/unit/test_candidate_plan_fidelity.py` 首跑 5 failed → 实现后 5 passed | 869 passed（864+5），ruff（CI 口径）All checks passed | 本轮 |

| T-MODEL-02 | 候选多样性落位（ADR-0016）Step 2：**落选候选不得静默丢弃** —— 新增 `ExperimentPlanner.extra_entries_from_candidates(candidates, plan)`，把落选候选（含 innovation）的 `required_experiments` 与创新要求转成 `候选方案要求[<cand_id>]` / `创新验证[<pattern_id>]` 条目并入计划；`do_experiment_design` 由「只取 `cands[0]`」改为消费全部候选，并把候选池落进决策 `alternatives`（含 `executed: False` 与 `novelty_level`，**如实标注未执行**）。**探针修正**：原计划的「给 arena 候选造 MIR 进执行」被探针否决——`_skeleton_mir` 明确不编造 variables/equations（`construction_status=pending_model_spec`、不可执行），硬造只会得到一批执行必 FAIL 的假候选；真正多候选执行只对有 MODEL_IR 的通道（P1-M3 / 项目实例）成立。TDD：新测试 `tests/unit/test_candidate_pool_not_dropped.py` 首跑 4 failed → 4 passed | 873 passed（869+4），ruff（CI 口径）全绿，mypy 无净新增（42，与基线一致） | 本轮 |

| T-MODEL-03 | 候选多样性落位（ADR-0016）Step 3：**目标值差距落账** —— 新增 `runtime/modeling/comparison.py::objective_gaps(chosen_metrics, others)`（复用 `baseline_comparison` 按 `objective_direction` 判优；只对双方都有有限 `objective_value` 的候选产出 gap，任一侧缺失如实标 `comparable=False` + reason，不猜）；`do_model_selection_decision` 的 decision data 增 `objective_gaps`。**刻意不产出上界/下界**——组合/路径型问题的界需问题特定松弛，core 不编造（ADR-0016 决策 4）；「离上限还有多远」在 core 层如实**不可算**，须由问题实例提供。TDD：新测试 `tests/unit/test_objective_gaps.py` 首跑 ImportError（RED）→ 7 passed | 880 passed（873+7），validate 54/0/0，catalog OK，术语 OK，ruff 全绿，mypy 无净新增（42） | 本轮 |
