"""Workflow 执行引擎 — DAG 调度 / 重试 / 反馈环 / blocked / partial rerun。

引擎只负责**控制流**；节点做什么由注入的 executor 决定:
    executor(node_id, context) -> NodeResult

NodeResult:
    status: "pass" | "fail" | "blocked" | "waiting_approval"
    reason / outputs 可选

能力（对应 V3.1 §1.14）:
    * ready 节点计算（依赖满足即 ready，天然并行组）
    * 失败重试（节点级 max_retries，默认 3）
    * 反馈环（重试耗尽 → on_fail 目标回退，受影响下游一并重置）
    * blocked（无 on_fail 可走时阻塞，等待人工/外部恢复）
    * partial rerun（reset_to: 从某节点起重置其下游，已完成的其他分支不动）
    * Per-Qi rerun（reset_question: 只重置某个 Question 的子图）
    * 人工审批点（waiting_approval → approve 后继续）
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .dag import Node, WorkflowDAG


class EngineError(RuntimeError):
    """引擎操作非法。"""


@dataclass
class NodeResult:
    status: str                      # "pass" | "fail" | "blocked" | "waiting_approval"
    reason: str = ""
    outputs: dict = field(default_factory=dict)


PASS = "pass"
FAIL = "fail"
BLOCKED = "blocked"
WAITING = "waiting_approval"


class WorkflowEngine:
    def __init__(self, dag: WorkflowDAG, executor, state=None, validators=None,
                 on_success=None):
        """
        dag: 已按 Question 展开的可执行 DAG
        executor: callable(node_id: str, context: dict) -> NodeResult
        state: 可选 ProjectState（记录 workflow 维度）
        validators: 可选 {node_id 或 node.type -> callable(node_id, result) -> str | None}
                    PASS 结果先过 validator；返回非空字符串视为失败原因
                    （走统一 retry/on_fail 语义，不让节点"自己说完成就算完成"）
        on_success: 可选 callable(node_id, result)，节点最终 PASS 后调用
                    （RuntimeSession 用它把 outputs.evidence 登记进 Evidence Graph）
        """
        problems = dag.validate()
        if problems:
            raise EngineError(f"DAG 非法: {'; '.join(problems)}")
        self.dag = dag
        self.executor = executor
        self.state = state
        self.validators = dict(validators or {})
        self.on_success = on_success
        self.completed: set[str] = set()
        self.retries: dict[str, int] = {}
        self.blocked: dict[str, str] = {}       # node -> reason
        self.waiting: set[str] = set()
        self.log: list[dict] = []               # 执行日志（审计用）
        self.failures: dict[str, str] = {}      # node -> last failure reason

    # ------------------------------------------------------------ 记录

    def _record(self, node_id: str, status: str, detail: str = "") -> None:
        entry = {"node": node_id, "status": status, "detail": detail}
        self.log.append(entry)
        if self.state:
            if status == PASS:
                self.state.workflow_complete(node_id)
            elif status == BLOCKED:
                self.state.workflow_block(node_id, detail)
            elif status == WAITING:
                self.state.workflow_waiting(node_id)

    # ------------------------------------------------------------ 查询

    def ready(self) -> list[str]:
        pending = [nid for nid in self.dag.nodes
                   if nid not in self.completed
                   and nid not in self.blocked
                   and nid not in self.waiting]
        return [nid for nid in pending
                if all(dep in self.completed for dep in self.dag.nodes[nid].depends_on)]

    def progress(self) -> dict:
        return {
            "total": len(self.dag.nodes),
            "completed": sorted(self.completed),
            "blocked": dict(self.blocked),
            "waiting_approval": sorted(self.waiting),
            "retries": dict(self.retries),
            "failures": dict(self.failures),
            "ready": self.ready(),
        }

    def is_finished(self) -> bool:
        return not self.ready() and not self.waiting

    # ------------------------------------------------------------ 执行

    def step(self, node_id: str | None = None) -> NodeResult:
        """执行一个 ready 节点（默认取 ready 列表第一个）。"""
        if node_id is None:
            ready = self.ready()
            if not ready:
                raise EngineError("没有可执行节点（全部完成或阻塞）")
            node_id = ready[0]
        if node_id not in self.dag.nodes:
            raise EngineError(f"未知节点: {node_id}")
        if node_id in self.completed:
            raise EngineError(f"节点已完成: {node_id}")
        if node_id in self.blocked or node_id in self.waiting:
            raise EngineError(f"节点处于 blocked/waiting，需先恢复: {node_id}")
        node = self.dag.nodes[node_id]
        missing = [d for d in node.depends_on if d not in self.completed]
        if missing:
            raise EngineError(f"节点 {node_id} 依赖未满足: {missing}")

        if node.human_approval and node_id not in self.retries:
            # 首次到达人工审批点：挂起等待放行
            self.waiting.add(node_id)
            self._record(node_id, WAITING, "human approval required")
            return NodeResult(WAITING, "human approval required")

        result = self.executor(node_id, self._context(node))
        return self._post_execute(node, result)

    def _post_execute(self, node, result: NodeResult) -> NodeResult:
        """executor 结果 → 状态迁移（PASS 先过 validator 挂钩）。"""
        node_id = node.id
        if result.status == PASS:
            reason = self._run_validator(node_id, result)
            if reason:
                # validator 否决 → 走统一失败语义（retry / on_fail 反馈环）
                result = NodeResult(FAIL, f"validator: {reason}")
            else:
                self.completed.add(node_id)
                self.failures.pop(node_id, None)
                self._record(node_id, PASS, result.reason)
                if self.on_success:
                    try:
                        self.on_success(node_id, result)
                    except Exception as e:   # 登记失败要可见，但不回滚节点
                        self._record(node_id, "evidence-error", str(e))
                return result
        if result.status == FAIL:
            self.failures[node_id] = result.reason or "failed"
            self._handle_failure(node, result.reason)
        elif result.status == BLOCKED:
            self.blocked[node_id] = result.reason or "blocked by executor"
            self._record(node_id, BLOCKED, result.reason)
        elif result.status == WAITING:
            self.waiting.add(node_id)
            self._record(node_id, WAITING, result.reason)
        else:
            raise EngineError(f"executor 返回未知状态: {result.status!r}")
        return result

    def _run_validator(self, node_id: str, result: NodeResult) -> str:
        """查 node_id 与 node.type 两级 validator，返回失败原因（空串/None = 通过）。"""
        node = self.dag.nodes[node_id]
        fn = self.validators.get(node_id) or self.validators.get(node.type)
        if fn is None:
            return ""
        try:
            reason = fn(node_id, result)
        except Exception as e:   # validator 自身抛错 = 判失败（fail-closed）
            return f"validator raised: {e}"
        return str(reason) if reason else ""

    # ------------------------------------------------------------ 并行调度接口（WaveExecutor 消费）

    def needs_approval(self, node_id: str) -> bool:
        """该节点首次执行是否需要人工审批（并行路径须先单独挂起）。"""
        node = self.dag.nodes[node_id]
        return bool(node.human_approval) and node_id not in self.retries

    def context_for(self, node_id: str) -> dict:
        return self._context(self.dag.nodes[node_id])

    def apply_result(self, node_id: str, result: NodeResult) -> NodeResult:
        """并行执行后的串行落账：先做与 step 相同的前置校验，再走统一状态迁移。"""
        if node_id not in self.dag.nodes:
            raise EngineError(f"未知节点: {node_id}")
        if node_id in self.completed:
            raise EngineError(f"节点已完成: {node_id}")
        if node_id in self.blocked or node_id in self.waiting:
            raise EngineError(f"节点处于 blocked/waiting，需先恢复: {node_id}")
        node = self.dag.nodes[node_id]
        missing = [d for d in node.depends_on if d not in self.completed]
        if missing:
            raise EngineError(f"节点 {node_id} 依赖未满足: {missing}")
        if self.needs_approval(node_id):
            # 并行路径误跑到审批节点：丢弃结果，转入等待
            self.waiting.add(node_id)
            self._record(node_id, WAITING, "human approval required")
            return NodeResult(WAITING, "human approval required")
        return self._post_execute(node, result)

    def run(self, max_steps: int = 1000) -> dict:
        """循环执行直到无可执行节点（完成 / 阻塞 / 等待审批）。"""
        steps = 0
        while self.ready() and steps < max_steps:
            self.step()
            steps += 1
        return self.progress()

    def _handle_failure(self, node: Node, reason: str) -> None:
        """失败处理: 重试 ≤ max_retries 轮（总尝试次数 = max_retries，与 V2 Iteration
        『最多 3 轮』语义一致）；耗尽后走 on_fail 反馈环或阻塞。"""
        count = self.retries.get(node.id, 0) + 1
        self.retries[node.id] = count
        if self.state:
            self.state.workflow_record_retry(node.id)
        if count < node.max_retries:
            self._record(node.id, FAIL, f"retry {count}/{node.max_retries}: {reason}")
            return   # 留在 pending，等待重跑
        # 重试耗尽 → 反馈环或阻塞
        if node.on_fail and node.on_fail != node.id:
            self._record(node.id, FAIL, f"exhausted retries → rollback to {node.on_fail}")
            self.rollback_to(node.on_fail)
        else:
            self.blocked[node.id] = f"retries exhausted: {reason}"
            self._record(node.id, BLOCKED, f"retries exhausted: {reason}")

    def _context(self, node: Node) -> dict:
        return {
            "node_id": node.id,
            "node": node.to_dict(),
            "completed": sorted(self.completed),
        }

    # ------------------------------------------------------------ 恢复

    def approve(self, node_id: str) -> None:
        """人工放行 waiting_approval 节点。"""
        if node_id not in self.waiting:
            raise EngineError(f"节点不在等待审批列表: {node_id}")
        self.waiting.discard(node_id)
        self.retries[node_id] = 1   # 已审批过，重跑不再进审批
        if self.state:
            self.state.workflow_approve(node_id)
        self._record(node_id, "approved", "human approval granted")

    def unblock(self, node_id: str, reason: str = "manually unblocked") -> None:
        if node_id not in self.blocked:
            raise EngineError(f"节点不在阻塞列表: {node_id}")
        del self.blocked[node_id]
        self.retries.pop(node_id, None)
        self._record(node_id, "unblocked", reason)

    def reset_to(self, node_id: str) -> set[str]:
        """partial rerun: 重置 node 及其全部下游（其他分支不动）。"""
        if node_id not in self.dag.nodes:
            raise EngineError(f"未知节点: {node_id}")
        affected = {node_id} | self.dag.downstream_of(node_id)
        self.completed -= affected
        for nid in affected:
            self.retries.pop(nid, None)
            self.blocked.pop(nid, None)
            self.waiting.discard(nid)
            self.failures.pop(nid, None)
        if self.state:
            self.state.workflow_reset(sorted(affected))
        self._record(node_id, "reset", f"partial rerun from {node_id} "
                       f"({len(affected)} nodes affected)")
        return affected

    def rollback_to(self, node_id: str) -> set[str]:
        """反馈环入口（on_fail 目标）: 语义同 reset_to。"""
        return self.reset_to(node_id)

    def reset_question(self, question_id: str) -> set[str]:
        """Per-Qi rerun: 只重置 <node>@<qid> 形态的节点及其专属下游。"""
        q_nodes = [nid for nid in self.dag.nodes if nid.endswith(f"@{question_id}")]
        if not q_nodes:
            raise EngineError(f"没有属于 Question {question_id} 的节点")
        affected: set[str] = set()
        for nid in q_nodes:
            affected |= {nid} | self.dag.downstream_of(nid)
        # 下游中属于其他 Question 的实例不动（它们有独立证据链）
        affected = {nid for nid in affected
                    if not any(nid.endswith(f"@{other}") for other in
                               self._other_questions(question_id))}
        self.completed -= affected
        for nid in affected:
            self.retries.pop(nid, None)
            self.blocked.pop(nid, None)
            self.waiting.discard(nid)
            self.failures.pop(nid, None)
        if self.state:
            self.state.workflow_reset(sorted(affected))
        self._record(f"@{question_id}", "reset_question",
                     f"Q-specific rerun ({len(affected)} nodes)")
        return affected

    def _other_questions(self, question_id: str) -> set[str]:
        qids = set()
        for nid in self.dag.nodes:
            if "@" in nid:
                qids.add(nid.split("@", 1)[1])
        qids.discard(question_id)
        return qids

    # ------------------------------------------------------------ 崩溃恢复（P6）

    def save_progress(self, path) -> None:
        """把执行进度落盘（崩溃后可 resume，不必整个 DAG 重跑）。"""
        from pathlib import Path as _P
        import json as _json
        data = {
            "engine_schema": 1,
            "completed": sorted(self.completed),
            "retries": dict(self.retries),
            "blocked": dict(self.blocked),
            "waiting": sorted(self.waiting),
            "failures": dict(self.failures),
        }
        p = _P(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def restore(self, data: dict) -> None:
        """从 save_progress 的数据恢复进度（未知节点拒绝，fail-closed）。"""
        if data.get("engine_schema") != 1:
            raise EngineError(f"进度数据版本不兼容: {data.get('engine_schema')!r}")
        unknown = [n for n in data.get("completed", []) if n not in self.dag.nodes]
        if unknown:
            raise EngineError(f"进度含未知节点: {unknown}")
        self.completed = set(data.get("completed", []))
        self.retries = dict(data.get("retries", {}))
        self.blocked = dict(data.get("blocked", {}))
        self.waiting = set(data.get("waiting", []))
        self.failures = dict(data.get("failures", {}))
        self._record("@resume", "restored",
                     f"{len(self.completed)} completed / "
                     f"{len(self.blocked)} blocked / {len(self.waiting)} waiting")

    @classmethod
    def load(cls, dag, executor, path, state=None, validators=None):
        """从进度文件恢复引擎（配合 resume 流程）。"""
        import json as _json
        from pathlib import Path as _P
        eng = cls(dag, executor, state=state, validators=validators)
        eng.restore(_json.loads(_P(path).read_text(encoding="utf-8")))
        return eng
