# CONSTRUCTOR INTEGRATION PLAN — 外部 Constructor 集成方案

> **基于 GitHub 真实代码研究**（MathModelAgent / Pi / BZD）+ LinHoMo 本地能力审计。
> 原则：不 fork，只做 Adapter/Protocol/Plugin；Runtime 不信任外部 Agent 的 execution_result/fidelity/validation。

---

## 1. 外部项目能力分析

### 1.1 MathModelAgent（jihe520/MathModelAgent）

| 维度 | 结论 |
|---|---|
| URL | https://github.com/jihe520/MathModelAgent |
| 架构 | 4-agent 串行编排：Coordinator→Modeler→Coder→Writer；FastAPI + Redis + WebSocket |
| 能力 | model construction / code generation / execution（本地 Jupyter + E2B 双解释器）/ paper generation（17 套 LaTeX/Typst 模板）/ workflow orchestration / knowledge retrieval（OpenAlex）/ reviewer（弱） |
| 哲学 | **Agent 是主体**，Runtime 只是编排骨架 + 解释器基座 |
| 执行证据 | **强**：jupyter_client 真实内核、E2B AsyncSandbox、错误反思循环（max_retries） |
| Evidence/Validation | **弱**：无 Artifact Registry / Evidence Graph / 哈希链 / replay |
| 输出格式 | Agent 间 JSON（自由文本 questions_solution）+ Markdown 报告 + 代码 + TeX/Typst |
| Capability Level | **C3**（MODEL_IR + code，但其 JSON 非 MODEL_IR schema；需适配器解析） |
| 可接入性 | 不可 import（全套产品）；可经 API/CLI 作 External Solver/Worker |

### 1.2 Pi（earendil-works/pi，前 badlogic/pi-mono，~90k star）

| 维度 | 结论 |
|---|---|
| URL | https://github.com/earendil-works/pi |
| 架构 | TypeScript agent harness：agent-loop + drive（retry/recovery/checkpoint）+ session JSONL + 6 工具（bash/read/write/edit/image/edit-diff）+ effect-gate + 多 provider LLM |
| 能力 | execution（bash/文件真实执行）/ code generation / debugging / workflow orchestration / reasoning；**无数学建模领域能力** |
| 哲学 | **Runtime 是主体**（Agent harness）；README 明示"无内置权限系统"，靠容器化 |
| 执行证据 | **强**：bash/read/write/edit 真实作用于文件系统；effect-gate 副作用门控 |
| Evidence/Validation | session JSONL/SQLite 可重放（transcript 级）；**无领域级** artifact/evidence/数值校验 |
| 输出格式 | AgentEvent 事件流 + 文件系统变更 + 自然语言；skills 为 Markdown（YAML frontmatter） |
| Capability Level | **C3**（通用代码 + 真实执行，但无模型 IR） |
| 可接入性 | TypeScript 库/CLI；可经子进程/stdio 作 Worker；不可直接 import |

### 1.3 BZD（BZDmathclub/bzd-math-modeling-skills）

| 维度 | 结论 |
|---|---|
| URL | https://github.com/BZDmathclub/bzd-math-modeling-skills |
| 架构 | 纯 Skill 提示层 + 少量确定性 Python 脚本；Codex/Claude Code 可加载 |
| 能力 | reviewer（百分制评审 + 位次估算）/ reasoning/planning（modeling-ideas）/ knowledge retrieval；**无执行、无代码生成** |
| 哲学 | **Agent 是主体，Skill 是知识**；工作流控制器只路由不执行，明示"不声称代码运行过" |
| 执行证据 | **仅脚本级**：award_position.py（锚点插值）、score_percentile.py、competition_context.py |
| Evidence/Validation | 弱-中：有"无法核验"状态、calibration 记录、低分保底复评；无 artifact/evidence/replay |
| 输出格式 | Markdown 报告 + HTML 评审报告 + 脚本 JSON；无 IR |
| Capability Level | **C0**（text only） |
| 可接入性 | 不可作 Constructor；rubric/校准/自查清单可作为知识资产导入 |
| 经验常数 | `national_probability_ceiling = 0.0681`（competition_context.py）——**禁止进入确定性评分** |

---

## 2. 集成定位裁决

### 2.1 MathModelAgent

| 定位 | 判定 | 理由 |
|---|---|---|
| Constructor Adapter | ⚠️ 低优先 | 输出自由文本 JSON，非 MODEL_IR；包装成本 > 收益 |
| **Worker Agent** | ✅ | 可整体委派"构造+求解+写作"子任务，Runtime 消费最终产物并重新执行验证 |
| **Reference Baseline** | ✅ | 唯一可比的端到端基线（"3 天→1 小时"） |
| **External Solver** | ✅ | CoderAgent + 双解释器是现成求解器；Runtime 给出 MODEL_IR→prompt→取回代码，**不信其自报数值** |
| Optional Backend | ◐ | E2B/本地 Jupyter 可映射到 ExecutionAdapter 槽位，但非必须 |
| Demo Agent | ✅ | 桌面版产品形态可作对比展示 |

### 2.2 Pi

| 定位 | 判定 | 理由 |
|---|---|---|
| **Optional Backend / 执行基座** | ✅ | 通用 coding agent，bash/文件工具真实执行，可作"本地 worker 执行环境" |
| **Worker Agent** | ✅ | 委派通用编码/数据预处理子任务；经 CLI/stdio 桥接 TS↔Python |
| **Reference Baseline（harness 架构）** | ✅ | session JSONL/fork/checkpoint/recovery/effect-gate 是 LinHoMo runtime 会话机制参照系 |
| Constructor Adapter | ❌ | 无数学建模能力 |
| 复用代码 | ❌ | TS 生态；只借架构思想，不 fork |

### 2.3 BZD

**不是 Constructor**，是 **Knowledge + Reviewer 资产**。最值得吸收：

1. **Rubric 方法论**（rubric-construction.md）：从赛题独立推导 100 分细则、原子扣分、`max(0, 0.90w − Σdeductions)`——可判定的评审结构
2. **Failure memory**（calibrations/*.md，16 道国赛）：负向锚点 + 可迁移教训→方法卡 known_failures/anti_patterns 素材
3. **低分保底复评**（low-score-safeguard.md）：`max(ordinary, min(35, bottom_up))` 双向评分→评分鲁棒性设计
4. **竞赛环境校准与质量评分分离**（competition_context.py）：地区/学校调整与论文质量严格分离——与 LinHoMo 哲学一致
5. **自查清单**（abstract-checker / problem-analysis-checker / symbol-notation-checker / AI 痕迹审计）→ guardrails/validators 输入

**不需要吸收**：model-dictionary.json（5713 条）——LinHoMo MethodCard 字段更丰富（30+ 字段），是更强的 superset。

---

## 3. LinHoMo 已有 vs 应复用 vs 必须自控

| 能力 | 判定 | 证据 |
|---|---|---|
| MODEL_IR 18 字段 schema + builder | ✅ 已有 | `core/runtime/modeling/model_ir.py` |
| 真实执行 + ExecutionResult 一等产物 | ✅ 已有 | `core/runtime/execution/adapters.py`（subprocess、hash、六态） |
| Artifact Registry / Evidence Graph / State / DAG | ✅ 已有 | `core/runtime/artifacts/` + `graph/` + `state/` |
| 候选生成/排序 | ✅ 已有 | `core/runtime/modeling/candidates.py`（TEST-ONLY） |
| 方法卡知识层（30+ 字段） | ✅ 已有 | `core/runtime/knowledge/cards.py` + `core/knowledge/` |
| 哈希链 / replay / 数值冻结 / 引用核验 | ✅ 已有 | `core/validators/modules/hash_chain.py` + `replay.py` + `freeze_numbers.py` |
| **17 套竞赛论文模板（LaTeX/Typst）** | 🔄 应复用 | MathModelAgent skills/5writing/templates/ |
| **12 套科研图表模板** | 🔄 应复用 | MathModelAgent mathmodel-figure-templates/ |
| **评审 rubric 方法论 + 16 道校准记录** | 🔄 应复用 | BZD bzd-review-paper/references/ |
| **AI 痕迹审计 / 合规声明** | 🔄 应复用 | BZD bzd-paper-aigc-auditor/ |
| 多 provider LLM 抽象 | 🔄 参考 | Pi packages/ai/src/providers/ |
| session checkpoint/recovery/effect-gate | 🔄 参考 | Pi harness/runtime/drive/ + effect-gate.ts |
| **确定性评分白名单** | 🔒 必须自控 | BZD 6.81% 等经验常数禁止进入 |
| MODEL_IR 生成与 schema 校验 | 🔒 必须自控 | 外部输出一律视为声明，由 ModelIRBuilder fail-closed 重建 |
| ExecutionResult.status / 执行复跑 | 🔒 必须自控 | Runtime 自己重新执行，不信任 Agent 的 execution_result |
| Evidence Graph 写入 / claim 支撑 | 🔒 必须自控 | 只有 active/validated/published 可支撑 claim |
| Artifact 生命周期 / 哈希链 | 🔒 必须自控 | 终态不可复用 |
| 数值冻结与论文投影 | 🔒 必须自控 | 论文数值必须解析到 validated Artifact |

---

## 4. Constructor Protocol 设计

### 4.1 目录结构

```
core/runtime/constructors/
├── __init__.py
├── protocol.py          # ConstructorAdapter ABC + ConstructionBundle schema（零第三方依赖）
├── adapter.py           # BaseConstructorAdapter：文本解析、C-level 协商、raw_output 留痕
├── registry.py          # ConstructorRegistry：注册/查询/健康探测/能力协商
└── adapters/
    ├── __init__.py
    ├── local.py         # LocalAgentAdapter（自研最小 Constructor，P0）
    ├── openai.py        # OpenAIAdapter（LLM→MODEL_IR，P0）
    ├── claude.py        # ClaudeAdapter（LLM→MODEL_IR，P0）
    ├── mathmodel_agent.py  # MathModelAgentAdapter（经 API/CLI，P1）
    └── pi.py            # PiAdapter（子进程 worker 通道，P2）
```

### 4.2 接口定义（protocol.py）

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ConstructionBundle:
    """外部 Constructor 的统一输出。一律视为【声明】，不包含任何已验证数值。"""
    adapter: str                          # 来源适配器名
    capability_level: int                 # 实际达到的 C0-C5
    problem_interpretation: dict          # L1：problem_binding + 歧义清单 + 跨问依赖
    model_candidates: list[dict]          # 多候选 + 比较理由（对齐 candidates.py Candidate）
    selected_model: str                   # 推荐主线 candidate_id
    model_ir: Optional[dict]              # C2+：须过 ModelIRBuilder.from_dict 校验，否则 None
    code: Optional[str]                   # C3+：生成代码（是否执行由 Runtime 决定）
    experiment_plan: list[dict]           # L3：solvers/experiments/validations 设计
    reasoning_metadata: dict              # 溯源：prompts、tokens、轨迹、confidence
    revision_request: Optional[dict]      # C5：构造器请求修订什么/为何
    raw_output: str                       # 原始输出全文（审计留痕，解析失败可人工回看）
    provenance: dict                      # adapter 版本、输入哈希、时间戳
    trust: dict = field(default_factory=lambda: {"execution_status": "not_executed"})

class ConstructorAdapter(ABC):
    name: str
    capability_level: int                 # 0..5
    supports: tuple[str, ...]             # ("construction","codegen","execution","revision",...)

    @abstractmethod
    def construct(self, problem: dict, context: dict) -> ConstructionBundle:
        """输入赛题 + 上下文（方法卡检索结果、历史 artifact、约束），返回结构化 bundle。"""

    def negotiate(self, required_level: int) -> bool:
        """能力协商：required_level ≤ capability_level 才允许进入对应通道。"""
        return required_level <= self.capability_level

    def request_revision(self, bundle: ConstructionBundle, feedback: dict) -> ConstructionBundle:
        """C5 专属：接受评审反馈并产出修订 bundle（其余适配器抛 NotSupported）。"""
        raise NotImplementedError(f"{self.name} 不支持 revision（C5）")

    def health(self) -> dict:
        """探测可用性（API key / 子进程 / 沙箱）。"""
        return {"status": "unknown"}
```

### 4.3 信任规则（写进 registry.py）

1. Runtime **不信任** bundle 内任何 `execution_result` / `fidelity` / `validation` 字段——统一丢弃
2. 代码若存在则交给 `ExecutionAdapter` 复跑，以新 `ExecutionResultData` 为准
3. `model_ir` 必须过 schema（18 required 字段）校验；解析/校验失败 → fail-closed 降级（保留 raw_output，标记 C0 待人工）
4. `BZD 经验常数禁止进入确定性评分`——知识导入时打 provenance 标签（empirical vs official）
5. `trust.execution_status` 恒为 `not_executed`，直到 Runtime 复跑后更新

### 4.4 C0-C5 Capability Levels

| Level | 定义 | MathModelAgent | Pi | BZD | Local/OpenAI/Claude |
|---|---|---|---|---|---|
| C0 | text only | — | — | ✅ 当前 | — |
| C1 | model description | ✅ 部分（自由文本方案） | — | — | ✅ |
| C2 | MODEL_IR | ✗（A2A JSON 非 schema） | ✗ | ✗ | ✅ |
| C3 | MODEL_IR + code | ✅ 总体 | ✅ 总体（无 IR） | ✗ | ✅ |
| C4 | executable model | ◐（解释器可执行但无映射契约） | ◐（可执行任何代码） | ✗ | ✅ |
| C5 | revision-capable | ✗ | ◐（retry 非模型级修订） | ✗ | ✅ |

**接入策略**：
- C0（BZD）：不接 Constructor 通道；接入 knowledge/reviewer 消费管线
- C1（MMA Modeler 层）：BaseConstructorAdapter 内置文本→MODEL_IR 解析器，缺字段标 unresolved
- C3（MMA 全流程 / Pi）：Runtime 取 code 后自己执行；Pi 作为 worker 时文件系统操作由 Runtime 通过产物哈希对账
- C5：仅 LocalAgentAdapter / OpenAIAdapter / ClaudeAdapter 通过 request_revision 闭环实现

---

## 5. 适配器实现优先级

| 优先级 | 适配器 | 理由 | 预计工作量 |
|---|---|---|---|
| **P0** | `LocalAgentAdapter` | 自研最小 Constructor（LLM + 方法卡检索 + ModelIRBuilder + 自身 ExecutionAdapter），无外部依赖，先打通 C0→C5 全链路与信任规则 | M |
| **P0** | `OpenAIAdapter` / `ClaudeAdapter` | 通用 LLM 文本→MODEL_IR 解析管线，覆盖绝大多数场景；与 Local 共享解析器 | M |
| **P1** | `MathModelAgentAdapter` | 需其后端运行（FastAPI/API key），先做 External Solver/Worker 通道；价值在模板与端到端基线 | L |
| **P2** | `PiAdapter` | 子进程桥接，作通用 worker/执行基座；依赖沙箱边界方案 | L |
| **P3（非 adapter）** | BZD 知识导入 | 实现为 `core/runtime/knowledge/packs/` 的 bzd 数据包 + reviewer rubric 资产 | M |

---

## 6. 集成风险与对策

| 风险 | 严重度 | 对策 |
|---|---|---|
| **信任边界穿透**：外部 Agent 自带"执行+自报成功"回路，若 Runtime 误信其 execution_result/数值，Evidence Graph 被污染 | 高 | bundle 一律声明级、status 恒 not_executed、Runtime 复跑、数值以 ExecutionResultData 为准（已写入 4.3 信任规则） |
| **输出格式异构与漂移**：MMA 自由文本 JSON、Pi 文件系统变更、BZD Markdown；外部项目持续迭代破坏脆解析 | 中 | raw_output 全文留痕 + 解析失败 fail-closed 降级 C0 + 能力协商 + conformance 测试 |
| **经验常数污染确定性评分**：BZD 0.0681 概率上限、位次锚点、地区系数若混入 score_compute/validate | 中 | provenance 标签（empirical/official）+ 评分白名单；评审位次估算与论文质量评分严格分离 |
| **许可风险**：BZD 与 MathModelAgent 均未声明开源许可证（Pi 为 MIT） | 中 | 导入模板/知识前确认合规；只做 Adapter 不 fork 降低法律风险 |
| **Constructor 依赖导致 Runtime 不可独立测试** | 低 | LocalAgentAdapter 作为无外部依赖的 baseline，保证 regression test 可离线运行 |

---

## 7. 实施步骤

### Phase 1：Protocol 层（P0，1-2 周）
1. 创建 `core/runtime/constructors/` 目录结构
2. 实现 `protocol.py`（ConstructorAdapter ABC + ConstructionBundle）
3. 实现 `adapter.py`（BaseConstructorAdapter：文本→MODEL_IR 解析器 + C-level 协商 + raw_output 留痕）
4. 实现 `registry.py`（注册/查询/健康探测）
5. 实现 `LocalAgentAdapter`（最小 Constructor，打通全链路）
6. 单元测试 + 集成测试（ConstructionBundle → Runtime 复跑 → VR → Evidence）

### Phase 2：通用 LLM 适配器（P0，1 周）
1. 实现 `OpenAIAdapter` / `ClaudeAdapter`（共享 BaseConstructorAdapter 解析器）
2. Constructor-independent benchmark 的 R0 臂（裸 Constructor）可用

### Phase 3：MathModelAgent 集成（P1，2 周）
1. 实现 `MathModelAgentAdapter`（经其 API/CLI，External Solver/Worker 通道）
2. 导入 17 套论文模板 + 12 套图表模板（作为模板资产，不复制其代码）
3. 端到端测试：MMA 构造 → LinHoMo 复跑 → 验证 → 修订

### Phase 4：Pi 集成（P2，2 周）
1. 实现 `PiAdapter`（子进程/stdio 桥接 TS↔Python）
2. 沙箱边界方案（Pi 无内置权限系统，需 Runtime 侧限制）
3. 参考其 session checkpoint/recovery 设计改进 RuntimeSession

### Phase 5：BZD 知识导入（P3，1 周）
1. rubric 方法论 → `core/runtime/knowledge/packs/bzd_review.yaml`
2. 16 道校准记录 → 方法卡 known_failures/anti_patterns
3. AI 痕迹审计 → guardrails 输入
4. 所有经验常数打 provenance=empirical 标签，禁入确定性评分

---

*本方案基于 GitHub 真实代码研究（非 README 转述）。所有外部项目判断标注 URL + 文件路径。*
