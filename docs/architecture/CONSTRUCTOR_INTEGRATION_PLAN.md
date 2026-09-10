# CONSTRUCTOR_INTEGRATION_PLAN — 外部 Constructor 集成方案

> 日期：2026-09-10 ｜ 状态：**DESIGN FROZEN**

---

## 1. 集成原则

1. **禁止 Fork**：不 fork MathModelAgent/Pi/任何外部项目
2. **Adapter > Integration**：通过统一 Protocol 接入，不修改外部代码
3. **Runtime 不信任 Agent**：外部 Constructor 的输出是"输入"，Runtime 重新执行验证
4. **Capability Levels**：按 C0-C5 分级接入，不同级别有不同集成深度

## 2. Constructor Protocol 设计

### 2.1 ConstructionBundle（标准输出）

```python
@dataclass
class ConstructionBundle:
    # 必填
    model_ir: dict              # MODEL_IR JSON（通过 validate_model_ir）
    code: str                   # 可执行 Python 代码
    output_mapping: dict        # {声明名或符号: 代码输出 key}

    # 可选（有则更好）
    problem_interpretation: dict  # 问题理解结构化
    model_candidates: list[dict]  # 候选模型列表
    selected_model: str           # 选中模型 ID
    experiment_plan: dict         # 实验计划
    reasoning_metadata: dict      # 推理元数据

    # Revision 时
    revision_request: dict | None  # {diagnosis_id, changes, rationale}
```

### 2.2 ConstructorAdapter（抽象接口）

```python
class ConstructorAdapter(ABC):
    name: str
    capability_level: int  # C0-C5

    @abstractmethod
    def construct(self, problem: str, context: dict) -> ConstructionBundle:
        """从问题构造模型。"""

    def revise(self, diagnosis: dict, context: dict) -> ConstructionBundle:
        """基于失败诊断修订模型。默认抛 NotImplementedError。"""
        raise NotImplementedError(f"{self.name} 不支持 revision")

    def available(self) -> bool:
        """后端是否可用。"""
        return True
```

## 3. 各外部 Agent 集成分析

### 3.1 MathModelAgent

**能力评估**：
| 能力 | 级别 | 说明 |
|---|---|---|
| Model Construction | C0 | 自由文本，无 MODEL_IR |
| Code Generation | C3 | 有代码，无 output_mapping |
| Execution | C4 | E2B/Jupyter 真实执行 |
| Debugging | 有 | Error reflection + retry |
| Paper Generation | 有 | Typst 输出 |

**集成方案**：
- **作为 Constructor Adapter**（不是核心 Agent）
- **需要包装层**将 MathModelAgent 的自由文本输出转为 MODEL_IR
- **Capability Level**: C3（需要增加 output_mapping 才能到 C4）
- **不 fork**：通过 CLI/API 调用

**包装器需要做的事**：
1. 解析 MathModelAgent 的 ModelerAgent 输出 → 提取 variables/objectives/constraints
2. 生成 output_mapping（将模型符号映射到代码输出 key）
3. 填充 experiment_plan（从 MathModelAgent 的实验计划中提取）

### 3.2 Claude Code

**能力评估**：
| 能力 | 级别 | 说明 |
|---|---|---|
| Reasoning | 强 | 长时自主编码 |
| Code Generation | C3 | 有代码 |
| Execution | 需外部 | 无内置沙箱 |
| Revision | 支持 | 可消费诊断 |

**集成方案**：
- 通过 CLAUDE.md 指令让 Claude 输出 MODEL_IR 格式
- **Capability Level**: C4（如果提供 output_mapping 指令）
- **不 fork**：通过 API 调用

### 3.3 OpenAI Code Interpreter

**能力评估**：
| 能力 | 级别 | 说明 |
|---|---|---|
| Execution | 强 | 沙箱 Python VM |
| Code Generation | C3 | 有代码 |
| Auto-retry | 有 | 读错误自动修复 |

**集成方案**：
- 作为 **Execution Backend**（不是 Constructor）
- 替换 LocalPythonAdapter 的沙箱版本
- **不 fork**：通过 Responses API + Containers 调用

### 3.4 Pi

**集成方案**：**不集成。** 无建模能力，无代码执行，无 API。

## 4. 集成优先级

| 优先级 | 任务 | 说明 |
|---|---|---|
| P0 | Constructor Protocol 设计 | `core/runtime/constructors/protocol.py` |
| P0 | Fidelity Layer 集成 | `fidelity.py` → `handlers.py` |
| P1 | MathModelAgent Adapter | 包装器将自由文本转 MODEL_IR |
| P1 | 接入 4 个 dead code 模块 | diagnosis/comparison/knowledge_guided/revision |
| P2 | E2B Backend | 替换 LocalPythonAdapter 的沙箱版本 |
| P2 | Claude Code Adapter | CLAUDE.md 指令模板 |
| P3 | OpenAI CI Backend | Responses API 集成 |

## 5. Constructor-Independent Benchmark 设计

```text
同一个 LinHoMo Runtime
+
不同 Constructor:
  Constructor A = MathModelAgent
  Constructor B = Claude Code
  Constructor C = Reference Constructor (minimal, LLM-free)
  Constructor D = Human

比较：
  裸 Constructor (raw output)
  vs
  Constructor + LinHoMo Runtime (经过 Execution → Fidelity → Validation → Evidence)

这样可以区分：
  Agent 本身能力
  vs
  LinHoMo Runtime 带来的增益
```

## 6. 不应该做的事

- 不 fork MathModelAgent
- 不把 MathModelAgent 当核心 Agent
- 不让外部 Agent 直接操作 Artifact Registry
- 不让外部 Agent 跳过 Validation
- 不为了集成而降低 LinHoMo 的验证标准


---

## 附录：引用文件路径映射（审计可追溯性）

本文档中的模块引用使用简写（handlers.py:837 表示 837 行）。完整真实路径如下（已逐行核对）：

| 简写 | 真实路径 | 核对结果 |
|---|---|---|
| handlers.py | core/runtime/execution/handlers.py（1737 行） | L817/837/843/876/1423 全部吻合 |
| engine.py | core/runtime/execution/engine.py（417 行） | L96/281/349 吻合（L281/L349 重复 unblock 属实） |
| session.py | core/runtime/execution/session.py（298 行） | L96 吻合 |
| idelity.py | core/runtime/execution/fidelity.py（227 行） | 存在 |
| codegen.py | core/runtime/execution/codegen.py | 存在 |
| integrity_gate.py | core/validators/modules/integrity_gate.py（428 行） | L118/161/172/255/345 全部吻合 |
| indings.py | core/runtime/writing/findings.py（212 行） | L121/147/157 吻合 |
| selection.py | core/runtime/modeling/selection.py（141 行） | L60/80/108/120 吻合（chosen=recs[0] 属实） |
| comparison.py | core/runtime/modeling/comparison.py | L22 吻合 |
| knowledge_guided.py / diagnosis.py / 
evision.py / candidates.py / model_ir.py | core/runtime/modeling/ | 存在（生产零调用见正文） |
