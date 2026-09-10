# Constructor 集成实证（T-CONF-003 落地）

- 实验：`research/P15/constructor_integration/`
- 日期：2026-09-10
- 关联决策：T-CONF-003「K 系列 vs Constructor 集成实证方向」——K 系列继续走
  Constructor 产物注入方向；本实验为其最小闭环证据。

## 目的

验证 **LLM-free Harness 承载外部认知 Agent（Doubao / GPT / MMA）建模产出的
端到端链路**：外部 Agent 在 harness 之外完成认知工作（建模决策），只把结构化
产物交给 harness；harness 负责承载、真实执行、验证并登记证据。

## 链路（机器实测）

```
research/P15/constructor_integration/mma_out/   ← 外部 Agent 产物目录
  ├── model_ir.json        （合法三层 MODEL_IR，过 model_ir.schema.json 18 required）
  ├── code.py              （可执行模型，subprocess 真实运行）
  ├── output_mapping.json  （输出映射）
  └── specs.json           （数值验证规格：y == 7.0，tolerance 1e-9）
        │  MathModelAgentAdapter.construct()（目录加载通道；未配置→如实抛错，禁止伪造）
        ▼
   ConstructionBundle（question / model_ir / code / output_mapping / validation_spec / constructor）
        │  apply_bundle(session, bundle)（注入 harness shared 状态）
        ▼
   engine.step(LOOP_NODES) —— 主链 9 节点（problem_analysis → model_validation）
        │
        ▼
   ExecutionResult（artifact 真实登记；status 只来自真实执行）
```

## 结果（2026-09-10 实测，py -3.12 run_demo.py）

- 未配置通道：`ConstructorNotConfigured` 如实报错（禁止 fallback/伪造）✓
- construct → ConstructionBundle：`question=Q001, constructor=mathmodel-agent` ✓
- 引擎主链 9 节点全 pass：problem_analysis / literature_search / model_selection /
  model_construction / model_critique / assumption_check / code_generation /
  **model_execution（真实 subprocess）** / **model_validation** ✓
- ExecutionResult：`status=success, outputs={'y': 7.0, 'ok': True, 'a': 2.0, 'x': 3.0, 'b': 1.0}`
  —— 数值来自真实执行，非伪造 ✓

## 与 K 系列的关系

- K001/K002（model_family 判定源）定义"外部 Constructor 产物"应携带的
  model_family 受控词；本实验的 model_family `algebraic_linear` 在受控表内。
- 本实验确认：Constructor 契约（ConstructionBundle）**不暴露 execution/fidelity/
  PASS 写入权限**（见 test_constructor_protocol.py 的 `test_constructor_has_no_fact_writer`），
  证据写入只归 harness 的 execution substrate。

## 运行方式

```powershell
py -3.12 research/P15/constructor_integration/run_demo.py
```

退出码 0 = 链路闭环；断言失败 = 非 0 退出（本脚本不修改 src/ 下任何代码）。

## 限制

- 本实验为最小闭环（单题 Q001、单模型、确定性数值），不构成对 2024A 赛题的
  完整建模；完整建模仍由外部认知 Agent 在 harness 约束下完成。
- `mma_out/` 中 model_ir.json / code.py / output_mapping.json / specs.json
  由 run_demo.py 生成（样例资产，可复现）。
