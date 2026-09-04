"""Workflow DAG 模型 — 节点 / 依赖 / 条件边 / 反馈环 / Per-Qi 展开。

节点类型（7 种，与 V3.1 §1.14 一致）:
    reasoning / generation / execution / validation / critique / projection / assembly

关键机制:
    * 依赖边: depends_on（节点完成后下游才 ready）
    * 条件边: on_fail（节点失败且重试耗尽时回退到的目标节点 = 反馈环）
    * per_question: 该节点按 Question 展开为 <node>@<QID> 实例
    * 门禁: validation/critique 节点绑定 validator 名（引擎 fail-closed）
    * 人工审批: human_approval 节点进入 waiting_approval
"""

from __future__ import annotations

NODE_TYPES = ("reasoning", "generation", "execution", "validation",
              "critique", "projection", "assembly")

_ALLOWED_NODE_FIELDS = frozenset({
    "type", "role", "depends_on", "per_question", "on_fail", "max_retries",
    "validator", "human_approval", "parallel_group", "inputs", "outputs",
    "description", "gate_type", "questions", "_stage",   # _stage: composer 内部标记
})


class DAGError(ValueError):
    """Workflow DAG 定义非法。"""


class Node:
    def __init__(self, node_id: str, **fields):
        self.id = node_id
        unknown = set(fields) - _ALLOWED_NODE_FIELDS
        if unknown:
            raise DAGError(f"节点 {node_id} 含未支持字段: {sorted(unknown)}")
        self.type = fields.get("type", "reasoning")
        if self.type not in NODE_TYPES:
            raise DAGError(f"节点 {node_id} 类型非法: {self.type!r}")
        self.role = fields.get("role", "")
        self.depends_on = list(fields.get("depends_on") or [])
        self.per_question = bool(fields.get("per_question", False))
        self.on_fail = fields.get("on_fail") or None
        self.max_retries = int(fields.get("max_retries", 3))
        self.validator = fields.get("validator") or None
        if self.on_fail == node_id:
            raise DAGError(f"节点 {node_id} 的 on_fail 不能指向自身")
        if self.validator and self.type not in ("validation", "critique"):
            raise DAGError(
                f"节点 {node_id} 绑定 validator 但类型是 {self.type}（应为 validation/critique）")
        self.human_approval = bool(fields.get("human_approval", False))
        self.parallel_group = fields.get("parallel_group") or None
        self.inputs = list(fields.get("inputs") or [])
        self.outputs = list(fields.get("outputs") or [])
        self.description = fields.get("description", "")
        self.gate_type = fields.get("gate_type") or None
        self._fields = dict(fields)
        self.stage = fields.get("_stage") or None   # composer 内部标记（可空）

    def to_dict(self) -> dict:
        d = {"type": self.type}
        if self.role:
            d["role"] = self.role
        if self.depends_on:
            d["depends_on"] = list(self.depends_on)
        if self.per_question:
            d["per_question"] = True
        if self.on_fail:
            d["on_fail"] = self.on_fail
        if self.max_retries != 3:
            d["max_retries"] = self.max_retries
        if self.validator:
            d["validator"] = self.validator
        if self.human_approval:
            d["human_approval"] = True
        if self.parallel_group:
            d["parallel_group"] = self.parallel_group
        if self.description:
            d["description"] = self.description
        if self.gate_type:
            d["gate_type"] = self.gate_type
        if self.inputs:
            d["inputs"] = list(self.inputs)
        if self.outputs:
            d["outputs"] = list(self.outputs)
        return d

    def instance(self, question_id: str) -> "Node":
        """per_question 节点按 Question 实例化（id 变为 <node>@<qid>，依赖同步展开）。"""
        if not self.per_question:
            raise DAGError(f"节点 {self.id} 不是 per_question 节点")
        fields = dict(self._fields)
        fields["depends_on"] = [expand_ref(d, question_id) for d in self.depends_on]
        if self.on_fail:
            fields["on_fail"] = expand_ref(self.on_fail, question_id)
        return Node(f"{self.id}@{question_id}", **fields)


def expand_ref(ref: str, question_id: str) -> str:
    """引用展开: 含 '*' 的 per_question 引用替换为 @qid 形态。"""
    if "*" in ref:
        return ref.replace("*", "") + "@" + question_id
    return ref


class WorkflowDAG:
    """DAG 容器: 校验 / 查询 / Per-Qi 展开。"""

    def __init__(self, name: str = "", nodes: dict[str, Node] | None = None,
                 description: str = ""):
        self.name = name
        self.description = description
        self.nodes: dict[str, Node] = {}
        for nid, node in (nodes or {}).items():
            self.add_node(node)

    def add_node(self, node: Node) -> Node:
        if node.id in self.nodes:
            raise DAGError(f"节点重复: {node.id}")
        self.nodes[node.id] = node
        return node

    # ------------------------------------------------------------ 校验

    def validate(self) -> list[str]:
        problems: list[str] = []
        for nid, node in self.nodes.items():
            for dep in node.depends_on:
                if "*" in dep:
                    # per_question 引用（如 experiment*）在 expand_questions 后才解析;
                    # 模板 DAG 只校验基名存在
                    if dep.replace("*", "") not in self.nodes:
                        problems.append(f"节点 {nid} 的 per_question 依赖 {dep} 无法解析")
                    continue
                if dep not in self.nodes:
                    problems.append(f"节点 {nid} 依赖不存在的节点: {dep}")
            if node.on_fail and node.on_fail.replace("*", "") not in self.nodes:
                problems.append(f"节点 {nid} 的 on_fail 指向不存在: {node.on_fail}")
            if node.on_fail == nid:
                problems.append(f"节点 {nid} 的 on_fail 不能指向自身")
            if node.validator and node.type not in ("validation", "critique"):
                problems.append(
                    f"节点 {nid} 绑定 validator 但类型是 {node.type}（应为 validation/critique）")
        problems += [f"DAG 存在依赖环: {c}" for c in self.find_cycles()]
        return problems

    def find_cycles(self) -> list[list[str]]:
        """依赖环检测（白/灰/黑 DFS；on_fail 反馈环不算依赖环）。"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {nid: WHITE for nid in self.nodes}
        cycles: list[list[str]] = []
        stack: list[str] = []

        def dfs(nid: str) -> None:
            color[nid] = GRAY
            stack.append(nid)
            for dep in self.nodes[nid].depends_on:
                if dep not in self.nodes:
                    continue
                if color[dep] == GRAY:
                    i = stack.index(dep)
                    cycles.append(stack[i:] + [dep])
                elif color[dep] == WHITE:
                    dfs(dep)
            stack.pop()
            color[nid] = BLACK

        for nid in self.nodes:
            if color[nid] == WHITE:
                dfs(nid)
        return cycles

    # ------------------------------------------------------------ 查询

    def ready_nodes(self, completed: set[str]) -> list[str]:
        """依赖全部完成的未完成节点（并行组内按字典序稳定输出）。"""
        ready = []
        for nid, node in self.nodes.items():
            if nid in completed:
                continue
            if all(dep in completed for dep in node.depends_on):
                ready.append(nid)
        return sorted(ready)

    def downstream_of(self, node_id: str) -> set[str]:
        """沿 depends_on 反向可达的下游（不含自身）。"""
        seen: set[str] = set()
        frontier = [node_id]
        while frontier:
            cur = frontier.pop()
            for nid, node in self.nodes.items():
                if cur in node.depends_on and nid not in seen:
                    seen.add(nid)
                    frontier.append(nid)
        return seen

    def per_question_nodes(self) -> list[str]:
        return sorted(nid for nid, n in self.nodes.items() if n.per_question)

    def expand_questions(self, question_ids: list[str]) -> "WorkflowDAG":
        """把 per_question 节点按 Question 列表展开成实例 DAG（模板节点移除）。"""
        expanded = WorkflowDAG(
            name=f"{self.name}:expanded",
            description=self.description)
        qids = list(question_ids)
        for nid, node in self.nodes.items():
            if node.per_question:
                for qid in qids:
                    expanded.add_node(node.instance(qid))
            else:
                # 非 per_question 节点的 per_question 依赖（带 *）展开为全部实例
                fields = dict(node._fields)
                new_deps: list[str] = []
                for dep in node.depends_on:
                    if "*" in dep:
                        base = dep.replace("*", "")
                        base_node = self.nodes.get(base)
                        if base_node is not None and base_node.per_question:
                            new_deps += [f"{base}@{qid}" for qid in qids]
                        else:
                            new_deps.append(base)
                    else:
                        new_deps.append(dep)
                fields["depends_on"] = new_deps
                if node.on_fail and "*" in node.on_fail:
                    fields["on_fail"] = node.on_fail.replace("*", "")
                expanded.add_node(Node(nid, **fields))
        problems = expanded.validate()
        if problems:
            raise DAGError(f"展开后 DAG 非法: {'; '.join(problems)}")
        return expanded

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "nodes": {nid: n.to_dict() for nid, n in sorted(self.nodes.items())},
        }

    # ------------------------------------------------------------ 构造

    @classmethod
    def from_dict(cls, d: dict) -> "WorkflowDAG":
        dag = cls(name=d.get("name", ""), description=d.get("description", ""))
        for nid, fields in (d.get("nodes") or {}).items():
            dag.add_node(Node(nid, **fields))
        return dag
