# ADR-0015: ExecutionResult 的来源豁免开关必须放在 registry 实例上，而非 payload 里

- Status / 状态：Accepted
- Date / 日期：2026-09-11
- Context / 上下文：

  P0-3 为 ExecutionResult 建立了来源鉴别：success EXEC 必须携带 adapter 用进程级
  HMAC secret 签发的 `execution_token`，Agent/Handler 无 secret 即无法伪造
  （The Agent Is Not The State）。历史 EXEC 与测试桩不追溯重算，走一条豁免路径。

  但这条豁免的实现有结构缺陷：`runtime/artifacts/registry.py::_check_exec_auth`
  的短路判断是 `if data.get("legacy_unverified"): return` —— **豁免开关写在被检查
  的数据本身里**。这意味着任何能构造 artifact data 的代码都可以自加该键绕过 token
  校验：鉴权器让被鉴权对象自己举证自己无害，与「Agent 不是状态来源」直接冲突。

  风险面是**注入面**而非既有后门：全仓无生产写入点使用该键（只有测试夹具），
  但机制上它是可被自授权的。

- Decision / 决策：

  1. **豁免开关从 payload 上移到 registry 实例**：
     `ArtifactRegistry(path, allow_legacy_unverified=False)`。只有显式开启的实例
     才承认 payload 的 `legacy_unverified` 声明；默认实例即便 payload 带该键，
     也照常要求有效 `execution_token`。
  2. `_check_exec_auth(data, allow_legacy=False)` 增加显式参数，由
     `_create_locked` 传入 `self.allow_legacy_unverified`。
  3. **测试夹具改为构造器显式声明豁免**（语义不变，不属篡改测试）：4 个文件 5 处
     使用该键的夹具由 `ArtifactRegistry(path)` 改为
     `ArtifactRegistry(path, allow_legacy_unverified=True)`。
  4. 读取路径（`load` / `Artifact.from_dict`）不校验来源的既有语义保持不变——
     历史数据不被追溯重算。

- Consequences / 后果：

  正面：
  - success EXEC 的来源鉴别不再可被数据自授权绕过；
  - 豁免成为**构造期的显式意图**，代码审查可见（grep `allow_legacy_unverified`）；
  - 生产路径完全不变（默认 False，且无生产写入点使用该键）。

  负面 / 约束：
  - 需要豁免的使用者必须显式传参，不能只靠 payload 标记；
  - 修改 `runtime/artifacts/registry.py` 须引用本 ADR。

- Evidence / 证据：

  - 缺口（RED 锁定）：`tests/unit/test_registry_legacy_gate.py` —— 首跑 3 failed
    （默认实例接受 payload 豁免键）/ 1 passed；实现后 4 passed。
  - 触发点：`runtime/artifacts/registry.py::_check_exec_auth`（改动前
    `if data.get("legacy_unverified"): return` 短路 token 校验）。
  - 夹具牵连（4 文件 5 处）：`tests/unit/test_evidence_gate.py`、
    `tests/unit/test_k003_governance.py`、`tests/unit/test_candidate_evidence_edges.py`、
    `tests/integration/test_evidence_has_provenance.py`。
    `tests/unit/test_execution_result_schema_gate.py` 的两处该键用 `Artifact(...)`
    直构（不经 create 的 auth 路径），无需改动。
  - 全量回归：864 passed（改动前 860 + 本 ADR 新增测试 4）。
