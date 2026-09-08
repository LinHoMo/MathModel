# 三仓库深度技术审计综合报告（Cross-Repository Audit Synthesis）

- **日期**: 2026-09-09
- **方法**: 基于三份证据级 dossier（`dossiers/MathModelAgent_dossier.md` / `BZD_dossier.md` / `LinHoMo_dossier.md`）的跨仓库综合。全部关键判断以 dossier 中的文件路径/函数/schema/实测证据为准；本报告只做综合与裁决，不重复证据全文。
- **审计对象**:
  - **BZD** = `BZDmathclub/bzd-math-modeling-skills`（纯 Skill 集合，评审知识蒸馏）
  - **MMA** = `jihe520/MathModelAgent`（LLM 文本接力流水线 + Code Interpreter）
  - **LHM** = `LinHoMo/MathModel`（本项目：LLM-free Harness / Scientific Runtime）
- **证据分级**: IMPLEMENTED / CONTRACT_ONLY / DOC_CLAIM / INSTRUCTIONAL（沿用 dossier 定义）。

---

## 0. Executive Verdict

**一句话总结**：三者分别代表数学建模自动化的三个本质不同的阵营——**BZD 是"评委经验提示词工程"（Knowledge Engineering），MMA 是"LLM 文本接力流水线"（Agent Engineering），LHM 是"可重放可对账的研究运行时"（Scientific Runtime Engineering）**；BZD 与 MMA 都把 Model 当作流转的文本、把"完成"当作成功、无 epistemic state；LHM 是唯一把"模型构造过程"做成可测量对象的系统，但它**尚未证明 formal runtime 提升 Model Construction Quality**——当前它的真实身份是"更好的数学建模研究基础设施"，而非"更好的数学建模系统"。

---

## 1. Real Runtime Reconstruction

### 1.1 MMA（Agent Engineering）

用户输入 → `ModelingRouter.create_modeling_task` → `Flows._process_task` → `MathModelWorkFlow.execute()` 顺序执行四 Agent：
`Coordinator(拆题) → Modeler(建模文本) → Coder(写码+CodeInterpreter 真执行) → Writer(写论文+OpenAlex 检索)` → `UserOutput.write_paper` 字符串拼接 → Redis/WS 推前端。

- 箭头类型：HTTP REST / asyncio task / Python function call / **prompt injection（题面原样塞 user message）** / JSON 字符串解析 / **tool_call → 真实代码解释器**（jupyter_client / E2B 沙箱）/ filesystem artifact（notebook.ipynb、work_dir）。
- **唯一机械反馈回路 = Code Interpreter 的 stdout/stderr/error**；除此之外无任何验证器。
- V3（当前主线）= 8 个 SKILL.md 由 Claude Code/Codex 驱动，无自研 runtime，作者明言"不再做 Harness 层"。
- 关键证据：`tools/local_interpreter.py`、`e2b_interpreter.py`（IMPLEMENTED）；RAG/HIL/Tavily/Fallback/Evaluator 均为死配置（DOC_CLAIM）；测试 ≈ 0（2 个文件，1 个依赖真实云沙箱 API Key）。

### 1.2 BZD（Knowledge Engineering）

**不存在统一 runtime**。全部流程 = SKILL.md 提示词 → 宿主 LLM 自我执行；11 个环节（理解→拆题→题型→候选→选型→构造→编码→验证→找错→评价→写作）中：
- 构造/编码/实验**显式外包**给用户自己的建模 agent（workflow 明言 "pass to the user's modeling agent"）；
- 验证 = 9 个 checker SKILL 全部 INSTRUCTIONAL（无机械验证器）；
- 唯一确定性 = 5 个 Python 脚本（位次插值/竞争校准/字典查询/学校查询/百分位），已实测可执行。
- 箭头类型：prompt injection + Agent message + filesystem artifact（.md 报告）。无 workflow state、无 schema 校验、无 DAG。

### 1.3 LHM（Scientific Runtime Engineering）

`orchestrator.py --execute` → `RuntimeSession` → `WorkflowComposer`（控制流 DAG）→ `WaveExecutor` → `DefaultNodeExecutor.do_<node>` → ArtifactRegistry / EvidenceGraph / DecisionLog / ProjectState（原子写 checkpoint）→ `validate.py` 57 项。

- **关键事实（自审证据）**：DefaultNodeExecutor **零 LLM**，`features` 默认硬编码 `{"problem_types": ["evaluation"]}`（handlers.py:75-76）；`do_experiment` 创建的 result claim 是字面量占位 `"{qid} 结论"`（**无数值计算**）；`do_model_construction` 只把卡 risks 转 assumptions（**不构造模型**）；model artifact = 选择记录（card_id/family/shortlist）。
- 箭头类型：CLI → DAG（Python 对象）→ filesystem artifact（JSON 原子写）→ typed evidence edges → 门禁（EvidenceGate E1-E4 结构校验）→ 重放/对账。
- 真实认知发生地 = **外部 Agent**（P15-K001 manifest：`generator: claude/claude-manual/console`）；core 36k 行零 LLM SDK import。

**三仓库 runtime 对比裁决**：唯一有"真实代码执行"的是 MMA（Code Interpreter）；唯一有"真实状态/证据/对账"的是 LHM；BZD 两者皆无但知识最密集。

---

## 2. What Is a Model?

| 维度 | MMA | BZD | LHM |
|---|---|---|---|
| Model 载体 | 流转于 Agent 间的 markdown 字符串（`questions_solution` dict） | 三态并存：字典 JSON 记录 / markdown 表 / 论文散文 | V3 = 选择记录 artifact（card_id/family）；legacy = MODEL_SPEC.md 文本；P15 = MODEL IR（typed JSON） |
| typed object? | 否（A2A schema 写好但无 import，CONTRACT_ONLY） | 否（字典是数据不是类型） | **部分**：MODEL IR（P15 实验层）是唯一 typed 可机检对象；V3 runtime 无 typed model |
| assumptions/variables/…/validation | 全部"prompt 要求"（文本，无机械强制） | 字典 15 字段覆盖 13/15（假设/禁忌/缺陷/检验有结构化），但消费是 INSTRUCTIONAL | MODEL IR 覆盖全维度（含 mechanisms/equations/solvers/experiments）；runtime 层仅 family 一维 |
| 修改/比较/追踪/验证/重放/复用/回滚/failure attribution | 仅文本层面；无追踪/无回滚/无归因 | 复用（字典查询）可；追踪/重放/回滚/归因无 | 全生命周期有（invalidate/rerun/lineage/evidence/重放/对账/归因），但**验证是结构性**的 |
| 与论文解耦 | **完全耦合**（Model ≈ 论文素材文本） | 部分（字典独立，但思路表→论文无绑定） | **结构性解耦**（论文 = PaperProjection 对 claim→evidence 的投影大纲；正文仍外部生成） |

**裁决**：LHM 的 MODEL IR 是三者中唯一"模型可作独立语义对象"的表示；但**它只存在于实验层，未成为 runtime 一等对象**——"表示层领先、生产层滞后"是当前最大结构落差。

---

## 3. Model Selection

| 机制 | MMA | BZD | LHM |
|---|---|---|---|
| taxonomy | prompt 内嵌决策树（五大题型→方法表） | 模型字典 5 类 20+ 分组（5713 条） | 19 方法卡 family + legacy METHOD-DECISION-TREE/HMML |
| candidate generation | **无**（单次输出最终模型） | ✅（modeling-ideas 强制 ≥2 候选，INSTRUCTIONAL） | ✅（MethodArena top-k 打分） |
| suitability analysis | 无 | fit-assessment 11 维四档判定（INSTRUCTIONAL） | retriever 特征打分（features 而非题面） |
| decision rule | **cookbook 关键词路由**（预测→ARIMA/GM；评价→AHP/TOPSIS…） | letter 触发启发式检查清单 + 明确反机械套题护栏 | arena 排序取第一（features 驱动） |
| structural vs heuristic | **heuristic routing**（最典型反例） | heuristic 之上加专家规则，但仍是"LLM 主观判定" | 半结构：有打分机制，但 features 不自动从题面推导（默认 evaluation） |

**裁决**：三者**均无真正的 structural model selection**（无基于题目结构的计算式选择、无基准比较）。MMA 是最坏的 cookbook；BZD 有最丰富的专家规则但有自律性风险；LHM 有打分机制但输入（features）与题面脱节——**这是 K002/RQ5 之后必须修的公共缺口：特征提取与词表收敛**。

---

## 4. Model Construction

| 机制 | MMA | BZD | LHM |
|---|---|---|---|
| 构造方式 | Modeler 单次 prompt 输出文本（无迭代、无草案评审） | LLM 自由生成表格（modeling-ideas）+ 事后 checker 审查 | V3 **不构造**（只转 risks 到 assumptions）；legacy Actor-Critic 环（INSTRUCTIONAL） |
| assumption validation | 无机械实现 | 事后 checker（INSTRUCTIONAL） | legacy assumption_validator（结构校验）；P15 盲评语义裁决 |
| constraint checking | 无 | prompt 要求（INSTRUCTIONAL） | 结构门禁；语义靠外部 |
| code execution | **有**（最强点：反射循环 + 真实解释器） | 无（外包） | **无**（experiment 节点只建台账，result 占位） |

**裁决**：构造质量在三个仓库中都**不依赖任何机械保障**——MMA 靠反射循环碰代码错误，BZD 靠自律，LHM 靠外部 Agent + 结构门禁。**LHM 的 execution weakness（Risk 5）在跨仓库对比中最刺眼**：它甚至没有 MMA 那样的 code interpreter 参考实现。

---

## 5. Knowledge → Capability（结合 P15-K001）

### 5.1 三仓库的 Knowledge 地位

| 仓库 | 知识在哪 | 注入/消费机制 | 因果证据 |
|---|---|---|---|
| MMA | prompt 字符串 / 静态 markdown（V3） | 无检索无注入点；LLM 自行参考 | **无**（无 benchmark/ablation） |
| BZD | 5 类（SKILL/references/字典/calibrations/CSV） | 检索脚本（字典）+ prompt 要求"完整阅读" | **无**（learning-protocol 自证"非统计训练"） |
| LHM | 19 方法卡 + 治理哲学 + HMML | V3 检索进台账（不进入模型内容）；P15 全卡文本注入（实验操作） | **P15-K001 唯一实测**：Δ_K=+2.14 CI[+0.00,+6.41] negative |

### 5.2 P15-K001 裁决（LHM 独有资产）

- **证明**：预注册+盲评+冻结+泄漏扫描的实验基础设施可行；知识注入**不造成盲从**（Sham 11/11 拒绝）；知识被实质消费（22/33 使用、21 调整、11 拒绝）；主终点测量可信。
- **未证明**：知识注入提升构造质量（CI 下界=0）；Knowledge Causal Effect 未与"更多上下文"分离（Δ_Sham=+3.42 > Δ_K）。
- **五层区分**：Ontology（结构合理）/ Utilization（被消费）/ Causal Effect（未证实）/ Measurement Validity（有天花板与粒度问题：2019_C 全 87.18 零变异）/ Power（block=3 不足）。

**裁决**：BZD/MMA 的"知识→能力"是 DOC_CLAIM；LHM 是唯一能给出**可信否定结论**的系统——negative result 本身是稀缺资产（绝大多数同类项目只有无法证伪的宣称）。

---

## 6. Verification / Evidence / Reproducibility

| 维度 | MMA | BZD | LHM |
|---|---|---|---|
| 验证器 | 无（唯一反馈=代码 stderr） | 无机械验证器（checker 全 INSTRUCTIONAL） | EvidenceGate E1-E4（结构）+ validate.py 57 项（存在性/结构/数值追溯）+ gate.py 29 步门禁 |
| 证据生命周期 | 无 | 无（calibration 记录格式有，无代码消费） | ✅ 完整（registration→typed edges→invalidation→retraction→coverage） |
| epistemic state | **无**（DataRecorder 只记 token） | 无 | **部分**（Registry/Graph/DecisionLog 真源 + STATE_TRUTH；但模型置信度/不确定度无字段） |
| 何时知道错了 | 仅代码崩溃/编译失败 | 仅 LLM 自律 | 结构门禁捕捉"形式非法"；**内容错误靠外部评审**（P15 FAIL runs 由盲评发现） |
| 测试 | ≈0（2 文件） | **零测试** | 774 passed / 11 skipped（9,203 行） |
| 可复现 | 无 seed 固定 | 5 脚本确定性；LLM 层无 | seed=42 全局 + replay.py + 原子写 + 对账 |
| 论文数值追溯 | 无 | 无 | ✅ validate.py 强制解析到 validated result artifact |

**裁决**：Verification/Reproducibility 维度 LHM 碾压式领先；但"内容正确性验证"三仓库**全部缺失**——这是 Formalism 的天花板，也是 P15 盲评必须存在的原因。

---

## 7. Engineering Architecture

| 维度 | MMA | BZD | LHM |
|---|---|---|---|
| 形态 | FastAPI+Redis+Vue 全栈（V2）+ SKILL 集合（V3） | 纯目录约定（SKILL+references+scripts+assets） | 五层（core/legacy/benchmark/research/instance）+ 零第三方依赖 |
| 调度 | 顺序函数调用（硬编码 4 Agent） | 无调度（宿主 LLM 自我路由） | Workflow DAG + WaveExecutor（确定性波次） |
| 状态 | 对话历史 + work_dir 文件 | 无 | **多真源持久状态**（Event Log→Content Truth→Projection→Resume） |
| 扩展性 | 配置驱动但 workflow 硬编码 | 加目录=加能力（低耦合但无质量门） | 加卡/加节点/加模板均有清晰路径 |
| 重复/债务 | 死配置/死 schema 多（RAG/HIL/A2A） | **49 个重复文件**（191 blob 中） | 已多次治理（REPOSITORY_AUDIT + 结构清理） |
| 工程成熟度 | 中（前端+后端完整但测试≈0） | 低（零测试零 CI） | 高（测试+校验+冻结+对账全套） |

---

## 8. Software Philosophy

- **MMA**：**B. Agent Engineering**。第一性对象 = LLM+prompt+工具调用的工作流；"完成"=四段 Agent 顺序跑完 + 论文编译通过。作者自述放弃自研 Harness（"不再做 Harness 层"）。
- **BZD**：**A. Knowledge Engineering**。第一性对象 = 专家评审经验蒸馏成的提示词知识；Agent 是宿主 LLM 不是组件；边缘附确定性脚本。
- **LHM**：**C. Scientific Runtime Engineering（叠加 A 的知识资产）**。第一性对象 = 可重放/可对账/可判审的认知过程运行时；Agent 是**外部 executor**（provenance 记录 model_provider/version/cost）；Model 是 artifact；状态是 persistent state。

**裁决**：三者哲学互斥且各自自洽。LHM 的哲学与用户锁定定位（LLM-free Harness，认知外部化）完全一致；MMA/BZD 的哲学决定了它们**不可能**回答"Agent 能力是否真实存在"——这正是 LHM 存在的理由。

---

## 9. Scientific Philosophy

- **MMA**：默认"跑通=有效"；无证伪设计；README 与实现的系统性落差（DOC_CLAIM 列表最长）。
- **BZD**：有最诚实的方法论条款（learning-protocol：禁止宣称 statistically trained、无法核验时标"无法核验"），但校准数值来源不透明（硬编码先验被确定性脚本放大）。
- **LHM**：唯一有"预注册 + 决策门 + 负面结果报告"的科学纪律的系统；STATE_TRUTH 数字口径纪律（只信机器命令+commit hash）；但 Risk 4（false confidence）真实存在——"全绿"的脚手架可能让人误以为"推理正确"。

---

## 10. Strongest Critique of BZD

**知识如何转化成 capability？它没有证明。**
- 全部核心能力（打分/判题/选型/诊断）依赖 LLM 自律执行自然语言规则（INSTRUCTIONAL 无机械强制）；同一论文两次评审一致性无任何保障。
- "基于 16 道题蒸馏"是 DOC_CLAIM——learning-protocol 自证"非统计训练"；**零测试、零 benchmark、零 ablation**。
- **最危险的模式**：`competition_context.py` 中 `national_probability_ceiling=0.0681`、`advisor_multiplier=1.2/0.8` 等无出处常数被**确定性脚本包装成 IMPLEMENTED 输出**——DOC_CLAIM 穿上 IMPLEMENTED 的外衣，比 README 吹牛更隐蔽。
- 知识表示仍靠 Agent 自行解释（权重和=100 只在 prompt 里要求，无代码断言）。
- **其价值**：评审规则化（atomic-deduction-scoring）、字典字段设计、诚实条款、反机械套题护栏——这些是"可搬走的资产"，不是"可复制的系统"。

---

## 11. Strongest Critique of MathModelAgent

**它把数学建模等价成 LLM workflow completion。**
- Model 自始至终是流转文本，`A2A.py` typed schema 写好却无 import（CONTRACT_ONLY）——**契约存在但运行时不使用**，这是"形式化装饰"的典型反例。
- 系统**何时知道自己错了**？只有代码崩溃/编译失败时。模型选错、假设错误、约束违反而不崩溃、数值系统性偏差——**永远无感知**；"数值一致性"只是 round(4) 子串搜索（WARN 级）。
- **无 epistemic state**：无置信度、无不确定性、无"未验证"标记。
- README 与实现落差巨大：RAG（ChromaDB+Rerank）、HIL（6 决策动作）、Tavily、四层容错、litellm——全 DOC_CLAIM；测试 ≈ 0 且非确定性。
- **其价值**：Code Interpreter 抽象层（base/factory/local/e2b）、notebook 全量留痕、Provider 抽象与 tool_call 修复、反射循环模式、V3 阶段文件级解耦、writing_check.sh 机械门禁——**这些是 execution layer 的优质参考**，不是 core semantics 的来源。

---

## 12. Strongest Critique of LinHoMo

**它是否已证明 formal scientific runtime 提升 Model Construction Quality？——没有。**
- P15-K001（唯一直接测量）Δ_K=+2.14 CI[+0.00,+6.41]：知识注入未证实；**runtime 本身对质量的影响从未被因果测量**（无"裸 LLM vs 带 harness"对比臂）。
- 六大风险全部成立（自审证据）：
  1. **Formalized nonsense**（Risk 1）：V3 experiment 节点产**无数值占位 result**（claim=`"{qid} 结论"`），EvidenceGate E4 只查"有 produces 边"——**错误数值也能 PASS**；FAIL runs 在 schema 上合法，只有盲评发现。
  2. **Over-formalization**（Risk 2）：36k 行绝大多数是过程管理，数学构造/求解不在 runtime 内；项目自己承认"会得到科研操作系统而非数模 Agent"。
  3. **Infra without capability gain**（Risk 3）：尚无证据证明 runtime 提升质量；只有证据证明它提升**测量质量与过程可信度**。
  4. **False confidence**（Risk 4）：2019_C 全臂 87.18 零变异、RQ5 A=0、55/55 REGISTERED——都容易被误读；缓解靠口径纪律而非机制免疫。
  5. **Execution weakness**（Risk 5，**最高风险**）：runtime 不做数值计算；无 code interpreter；29 agent 无运行时互操作（文件流转+gate）；"多 Agent 协作"= 文件顺序流转。
  6. **Ontology weakness**（Risk 6）：`discrete_recurrence` vs `dynamic_programming` 词表分叉（RQ5 实证）；runtime 层 model artifact 只有 family 单串；表示层领先、生产层滞后。
- **结论**：它是"更好的数学建模研究基础设施"（证据充分），不是"更好的数学建模系统"（证据不足）。**下一步必须回答：如何让 formal runtime 变得对质量有因果贡献，或诚实接受"研究基础设施"身份并把质量杠杆交给外部认知层。**

---

## 13. Comparative Scorecard

| 能力维度 | BZD | MMA | LHM | 依据 |
|---|---|---|---|---|
| Modeling Knowledge | **Very Strong**（5713 条字典+评阅细则） | Weak（prompt 决策树） | Moderate（19 卡，3 Tier1） | dossier §6 |
| Modeling Theory | Moderate（专家规则） | Weak（cookbook） | Moderate（治理哲学+失败分类） | — |
| Model Representation | Moderate（字典 15 字段） | Weak（文本） | **Strong**（MODEL IR typed，仅实验层） | dossier §3 |
| Model Selection | Moderate（专家规则，自律） | Weak（cookbook） | Moderate（打分机制，features 脱节） | dossier §4 |
| Model Construction | Weak（外包） | Moderate（Code Interpreter 反馈） | Weak（runtime 不构造） | dossier §5 |
| Verification | Weak（零机械） | Weak（文本门禁为主） | **Very Strong**（结构门禁+57 项+重放） | dossier §6 |
| Evidence | Weak | Weak | **Very Strong**（typed graph+失效传播） | dossier §6 |
| Reproducibility | Moderate（5 脚本） | Weak | **Very Strong**（seed/原子写/对账/冻结） | dossier §6 |
| Execution | Weak（外包） | **Strong**（真实解释器） | Weak（台账占位） | dossier §2/§5 |
| E2E automation | Moderate（评审端到端） | **Very Strong**（题→PDF） | Weak（默认路径零内容） | — |
| Scientific Experimentation | Weak（零实验） | Weak | **Very Strong**（P15-K001 预注册实验） | dossier §10 |
| Software Architecture | Weak（无框架） | Moderate（全栈） | **Very Strong**（五层+零依赖） | dossier §8 |
| Engineering maturity | Weak（零测试零 CI） | Moderate（全栈但测试≈0） | **Very Strong**（774 tests+校验链） | dossier §7 |
| Scientific credibility | Moderate（诚实条款） | Weak（DOC_CLAIM 落差） | **Strong**（负面结果可报告） | dossier §9 |

**综合**：LHM 在 8/14 维度领先（均为"基础设施/测量/验证"类），MMA 在 2 项（执行/E2E）领先，BZD 在 1 项（知识量）领先。**没有任何仓库全面领先——它们优化的第一性目标不同。**

---

## 14. What LinHoMo Should Borrow

### 14.1 从 MMA（execution layer / adapter 参考，不污染 core semantics）

1. **Code Interpreter 抽象层**（`base_interpreter.py` + `interpreter_factory.py` + local/e2b 双实现）：统一 execute_code 契约 + 可插拔后端 + 中文绘图字体注入 + 附件/产物双向同步——作为外部 executor 的**参考实现**（不是进 core，而是作为 adapter 模板/参考文档）。
2. **notebook 全量留痕**（`notebook_serializer.py`）：每次执行追加 code cell + output、按段落留存输出供下游引用——"实验证据留痕"的朴素形态，可直接借鉴到 external artifact 登记。
3. **反射循环模式**（coder_agent + reflection prompt + MAX_CHAT_TURNS + MAX_JSON_RETRIES）：外部 executor 的"自愈"协议参考。
4. **V3 阶段边界文件级解耦**（ANALYSIS_MODELING_REPORT / RESULTS_REPORT / figures / paper）：印证了 LHM 的模型-论文分离方向（虽然 MMA 的模型仍是 markdown）。
5. **writing_check.sh 机械门禁模式**（占位符/泄漏/章节/图片/caption FAIL/WARN 分级、引擎自适应）——可迁移的 verifier 模式。
6. **17 套 Typst/LaTeX 竞赛模板**——内容资产整体价值高（转 LaTeX 的工作量大且已完成）。
7. **Provider 抽象 + tool_call 修复**：LLM routing 的干净样板。

### 14.2 从 BZD（knowledge / reviewer policy / benchmark 参考）

1. **评审打分规则化形式主义**（`atomic-deduction-scoring.md` + `rubric-construction.md`）：90% 封顶、原子检查点 1/2/3 分扣减、格式质量系数确定性映射、低分保底复评——**这是三仓库最强的 reviewer policy**，可直接进 LHM 的 evaluator 设计（替代/补充当前 rubric 的主观打分）。
2. **确定性位次/校准脚本**（award_position / competition_context / score_percentile）：锚点插值 + clamp 公式 + "学校/赛区/教师与质量分严格分离"——评审公平性边界设计。
3. **模型字典字段设计**（5713 条 × 假设/禁忌点/缺陷/检验方法/资料声明）："假设-失败条件-验证"三元结构是方法卡的成熟 schema 参照（LHM 的 mc-* 卡已含 anti_patterns/known_failures，可对照补齐）。
4. **learning-protocol 诚实条款**：禁止宣称 statistically trained、跨案例≥2 才提升、无法核验时标"无法核验"——直接强化 LHM 的证据纪律。
5. **反机械套题护栏**：BZD 明文禁止"题号决定模型"——与 LHM 的 out_of_catalog 不自动判错同源，可互相印证。

### 14.3 不该进 core 的东西（明确排除清单）

- MMA 的 cookbook 模型选择（prompt 决策树）——LHM 要 structural selection 就应把 taxonomy/候选/评分做成数据与算法。
- MMA 的 markdown 报告充当 Model——LHM 已有 MODEL IR。
- MMA 的 writing_check.sh "数值一致性"子串搜索——LHM 已有 validate.py 数值追溯，更强。
- BZD 的校准数值（6.81% 等无出处常数）——DOC_CLAIM 包装成 IMPLEMENTED 的反模式，禁止复制。
- BZD 的 49 个重复文件/无测试/无 CI 的工程卫生——不可接受。
- BZD/MMA 的"评审/完成 = 论文编译通过"的成功定义——与 LHM 的科学裁决哲学冲突。

---

## 15. What LinHoMo Must NOT Become

1. **不能成为 research process management system**（Over-formalization）：36k 行过程管理 + 占位 result 的现状已经是这个方向的滑坡；必须给 experiment 节点**真实内容出口**（外部 executor 的产物登记 + 数值真实落盘），把"台账"变成"证据"。
2. **不能成为"越来越多的 schema/contract/graph/validator 但质量不提升"的系统**（Infra without capability）：每个新契约必须回答"它让哪个能力声明变得可裁决"，否则不进。
3. **不能靠形式化产生错误安全感**（False confidence）：REGISTERED ≠ 正确、全绿 ≠ 推理严谨；报告的每一个"PASS"必须写清它是"结构 PASS"还是"语义 PASS"。
4. **不能把 agent 数量/卡数量/文档数量当 KPI**（用户已锁定：方法卡数量不是 KPI）。
5. **不能退化为 RAG 数模专家系统**（cookbook routing + 卡检索器）：LLM 是建模者，知识是约束，证据是裁决——这条治理哲学不能被工程便利侵蚀。
6. **不能在 core 里建 LLM 执行器**（用户锁定偏好）：认知永远外部化；但 execution 的证据登记必须真实（result 占位符是当前最大失信点）。

---

## 16. Next Experimental Priority

**基于审计证据的下一轮实验裁决**：

### 16.1 结论：P15-K002（Model Representation Efficacy）方向正确，但需按审计证据回填

- K001 证明：知识注入未证实效应（Δ_K CI 触 0）、Sham 未分离、测量有天花板。K002 转向 Representation（结构化契约强制）是**有证据支持的方向**——因为 K001 的 22 维盲评分布显示 L2 结构维度已饱和、弱环全在未强制字段（L4.3/L3.4/L1.4），Representation 强制正是对准这些弱环。
- 审计启示回填（写入 K002 定稿）：
  1. **ontology 收敛先行**：`catalog/model_families.yaml` 单一注册表（合并 model_ir.schema 枚举 + allowed_model_families + 方法卡 family），杜绝 discrete_recurrence/dynamic_programming 分叉；K002 的 method-family 终点改为"任一次级/机制/solver 命中即算命中"。
  2. **result 占位符治理**：K002 的 S/V 臂产物必须含**真实数值**（S+V 臂 validation_plan 已有此设计）；同时把"result 占位"作为 P1 工程项修 core（experiment 节点未执行时应标记 `status=not_executed`，不得用假占位 claim）。
  3. **features 硬编码治理**：V3 默认 `evaluation` 是测量污染源；K002 后把 features 契约改为"外部必传 + 缺失即 BLOCKED"。
  4. **execution adapter 参考**：以 MMA 的 Code Interpreter 抽象为模板写 `docs/architecture/EXTERNAL_EXECUTOR_REFERENCE.md`（吸收点 1-3），供外部 executor 实现参考，不建 core 执行器。

### 16.2 优先级排序（基于六风险）

| 优先 | 工作 | 回答的风险 | 证据 |
|---|---|---|---|
| P0 | K002 定稿+执行（Representation + Validation Plan 强制） | Risk 3（capability gain） | K001 维度分布 + Δ_K |
| P0 | result 占位符修复（experiment 节点 `not_executed` 状态） | Risk 1（formalized nonsense） | handlers.py do_experiment |
| P0 | `catalog/model_families.yaml` 单一注册表 | Risk 6（ontology） | RQ5 词表错位 |
| P1 | features 外部必传契约 | Risk 5（execution） | handlers.py:75-76 |
| P1 | EXTERNAL_EXECUTOR_REFERENCE.md（吸收 MMA） | Risk 5（execution） | MMA dossier §11.1 |
| P1 | evaluator 吸收 BZD atomic-deduction 规则化 | Risk 4（false confidence） | BZD dossier §11.1 |
| P2 | 16 张 Tier3 卡补 mechanism | Knowledge 深度 | KNOWLEDGE_BASE_QUALITY_BASELINE |
| P2 | L1 结构覆盖（game/network/scheduling）过 Gate | Knowledge 广度 | audit L1-L4 |

### 16.3 下一个"最干净的实验"设计（候选，与 K002 一致）

- 三臂：F（自由）/ S（MODEL IR 结构化）/ S+V（IR + Validation Plan 强制），63 runs，双主终点 MCQ+VAL；
- 对照组含"等长自由文本指令"（对齐"更多上下文"——K001 Sham 教训）；
- same model / fixed token budget / fixed tools / 独立盲评；
- 题目区分度预检（K001 per-block 教训：2019_C 零变异必须预检剔除）；
- 子问题覆盖 gate 机械强制（K001 2020_B 教训）。

---

## 17. Final Strategic Judgment

**对三者最终的定位裁决**：

- **BZD**：最好的"评委知识蒸馏"，但**无法回答"Agent 会不会建模"**——它连可执行模型都没有，且无任何因果证据。它的价值在知识资产，不在系统。
- **MMA**：最好的"题→PDF 自动化流水线"，但**把建模等价成 workflow completion**，Model 无独立语义、系统永远不知道自己错了。它的价值在 execution substrate（Code Interpreter/notebook/模板），不在认知。
- **LHM**：唯一"可测量、可审计、可证伪"的建模研究运行时——**P15-K001 的 negative result 就是它存在意义的证明**（它能产出可信的否定结论，而 BZD/MMA 只有无法证伪的宣称）。但它**尚未证明 formal runtime 提升 Model Construction Quality**；当前它是"更好的数学建模研究基础设施"。

**核心判断**：如果三者同时面对 20 道题（same LLM/token/tools/evaluator）：
- 选对模型：BZD 的知识密度 + LHM 的检索打分可能持平，MMA cookbook 最差（推断，无实验证据）；
- 构造正确模型：三者都依赖同一 LLM 的认知——**无显著差异可预测**（推断）；
- 发现模型错了：**LHM 有盲评/归因/失效传播机制（已有证据），BZD/MMA 无**（证据）；
- 可复现结果：LHM 碾压（seed/冻结/重放/对账，证据）；BZD 5 脚本可复现；MMA 无；
- 盲评下更高 MCQ：**无证据可预测**——这正是 LHM 下一轮实验（K002）要回答的问题。

**最终判断**：LHM 最接近"Mathematical Modeling Computing System"的雏形（唯一把建模过程当作可观察、可结构化、可验证对象的系统），但**它现在的真实身份是"数学建模的科学测量基础设施"**——这不是贬义，而是它区别于 BZD/MMA 的护城河。下一步不是"变得更像 MMA/BZD"（补算法/补自动化），而是**让测量基础设施证明自己：K002 测 Representation，同时修复 result 占位符与 ontology 分叉，让"形式化"与"真实内容"首次对齐**。只有到那时，"研究基础设施"才可能被证明也是"更好的数学建模系统"。

---

*证据来源：`dossiers/MathModelAgent_dossier.md`（369 行）/ `BZD_dossier.md`（298 行）/ `LinHoMo_dossier.md`（640 行）；P15-K001 正式报告与分析归因。所有三级证据标签均可在 dossier 中定位到文件路径。*
