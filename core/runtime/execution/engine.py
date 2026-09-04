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
    def __init__(self, dag: WorkflowDAG, executor, state=None):
        """
        dag: 已按 Question 展开的可执行 DAG
        executor: callable(node_id: str, context: dict) -> NodeResult
        state: 可选 ProjectState（记录 workflow 维度）
        """
        problems = dag.validate()
        if problems:
            raise EngineError(f"DAG 非法: {'; '.join(problems)}")
        self.dag = dag
        self.executor = executor
        self.state = state
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
        if result.status == PASS:
            self.completed.add(node_id)
            self.failures.pop(node_id, None)
            self._record(node_id, PASS, result.reason)
        elif result.status == FAIL:
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
