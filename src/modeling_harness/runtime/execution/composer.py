"""Workflow Composition — base + stages + competition profile → 可执行 DAG。

组合规则（V3.1 §1.4 / 任务书 §11）:
    base.yaml       声明 stage 顺序（骨架）
    stages/*.yaml   每个 stage 声明节点（节点间用 depends_on 串联）
    competition/*   赛事 profile: 覆盖参数 / 追加 / 移除节点

最终:
    base workflow + competition profile + project state（Question 列表）
    → 展开后的 executable WorkflowDAG
"""

from __future__ import annotations

from pathlib import Path

from .dag import DAGError, Node, WorkflowDAG
from .yamlio import YamlSyntaxError, load_file, loads


class ComposeError(ValueError):
    """Workflow 组合非法。"""


class WorkflowComposer:
    def __init__(self, workflows_dir: str | Path):
        self.dir = Path(workflows_dir)
        if not self.dir.is_dir():
            raise ComposeError(f"workflows 目录不存在: {self.dir}")

    # ------------------------------------------------------------ 加载

    def load_base(self) -> dict:
        path = self.dir / "base.yaml"
        if not path.exists():
            raise ComposeError(f"缺少 base.yaml: {path}")
        base = load_file(path)
        if "stages" not in base:
            raise ComposeError("base.yaml 必须声明 stages 列表")
        return base

    def load_stage(self, stage_name: str) -> dict:
        path = self.dir / "stages" / f"{stage_name}.yaml"
        if not path.exists():
            raise ComposeError(f"stage 文件不存在: {path}")
        stage = load_file(path)
        if not stage.get("nodes"):
            raise ComposeError(f"stage {stage_name} 未声明任何节点")
        return stage

    def load_competition(self, competition: str) -> dict:
        path = self.dir / "competition" / f"{competition}.yaml"
        if not path.exists():
            raise ComposeError(f"competition profile 不存在: {path}")
        return load_file(path)

    # ------------------------------------------------------------ 组合

    def compose(self, competition: str | None = None) -> WorkflowDAG:
        """组合模板 DAG（未展开 Question；展开用 dag.expand_questions）。"""
        base = self.load_base()
        stages = list(base["stages"])

        profile: dict = {}
        if competition:
            profile = self.load_competition(competition)
            # profile 可调整 stage 列表（insert / remove）
            for remove in profile.get("remove_stages", []):
                if remove in stages:
                    stages.remove(remove)
            for ins in profile.get("insert_after", []):
                after, name = ins.get("after"), ins.get("stage")
                if name and after in stages:
                    stages.insert(stages.index(after) + 1, name)

        dag = WorkflowDAG(
            name=base.get("name", "base"),
            description=base.get("description", ""))
        prev_stage_last: list[str] = []   # 上一 stage 的收尾节点（跨 stage 依赖）
        for stage_name in stages:
            stage = self.load_stage(stage_name)
            self._merge_stage(dag, stage, stage_name, prev_stage_last)
            # 本 stage 收尾 = 无出边节点（下游在本 stage 内不被引用）
            stage_nodes = set()
            for nid, node in dag.nodes.items():
                if node.stage == stage_name:
                    stage_nodes.add(nid)
            if stage_nodes:
                referenced = {d for nid in stage_nodes
                              for d in dag.nodes[nid].depends_on}
                prev_stage_last = sorted(stage_nodes - referenced)
            else:
                prev_stage_last = []

        # 赛事覆盖: 追加 / 移除节点
        for node_id, fields in (profile.get("add_nodes") or {}).items():
            if node_id in dag.nodes:
                raise ComposeError(f"赛事 profile 追加了已存在节点: {node_id}")
            dag.add_node(Node(node_id, **fields))
        for node_id in (profile.get("remove_nodes") or []):
            if node_id not in dag.nodes:
                raise ComposeError(f"赛事 profile 移除了不存在的节点: {node_id}")
            del dag.nodes[node_id]
            # 清理悬空依赖
            for nid, node in dag.nodes.items():
                node.depends_on = [d for d in node.depends_on if d != node_id]
                if node.on_fail == node_id:
                    node.on_fail = None

        problems = dag.validate()
        if problems:
            raise ComposeError(f"组合后的 DAG 非法: {'; '.join(problems)}")
        return dag

    def _merge_stage(self, dag: WorkflowDAG, stage: dict, stage_name: str,
                     cross_deps: list[str]) -> None:
        """把一个 stage 的节点并入 DAG: stage 内 depends_on 跨 stage 引用上一收尾。"""
        for node_id, fields in (stage.get("nodes") or {}).items():
            if node_id in dag.nodes:
                raise ComposeError(f"跨 stage 节点重复: {node_id}（stage {stage_name}）")
            f = dict(fields)
            deps = list(f.get("depends_on") or [])
            external = [d for d in deps if "*" in d or (
                d.replace("*", "") not in stage.get("nodes", {}) and d not in dag.nodes)]
            # 跨 stage 依赖: 展开 * 引用保留（expand_questions 处理），普通外部引用校验存在
            for d in external:
                if "*" not in d and d not in dag.nodes:
                    raise ComposeError(
                        f"节点 {node_id}（stage {stage_name}）引用了不存在的跨 stage 节点: {d}")
            if not deps and cross_deps:
                # stage 首节点自动依赖上一 stage 收尾（骨架串联）
                f["depends_on"] = list(cross_deps)
            f["_stage"] = stage_name
            dag.add_node(Node(node_id, **f))

    # ------------------------------------------------------------ 入口

    def compose_executable(self, question_ids: list[str],
                           competition: str | None = None) -> WorkflowDAG:
        """组合 + 按 Question 展开 = 可执行 DAG。"""
        dag = self.compose(competition)
        return dag.expand_questions(question_ids)
