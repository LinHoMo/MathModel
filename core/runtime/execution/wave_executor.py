#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WaveExecutor — 波次拓扑调度 + 并行节点执行（P6 Runtime Execution）。

WorkflowEngine 是语义核心（retry / on_fail 反馈环 / blocked / 审批 / 局部重跑），
WaveExecutor 在其上加调度层：

    DAG
     ↓  Kahn 分层（layer = 1 + max(上游 layer)）
    Wave 0 / Wave 1 / ...
     ↓  波内并行（executor 是真正的开销所在，落账串行保证引擎状态一致）
    engine.apply_result() 统一走 PASS→validator→completed / FAIL→retry→rollback 语义

崩溃恢复：进度经 engine.save_progress() 落盘，resume 时
WorkflowEngine.load() 恢复 completed/blocked/waiting/retries，从断点继续。
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from .engine import EngineError, NodeResult, WorkflowEngine


class WaveExecutor:
    """按拓扑波次执行 DAG；executor 调用并行，引擎落账串行。"""

    def __init__(self, dag, executor, state=None, validators=None,
                 max_workers: int = 1, max_waves: int = 200):
        self.engine = WorkflowEngine(dag, executor, state=state,
                                     validators=validators)
        self.max_workers = max(1, int(max_workers))
        self.max_waves = max_waves

    # ------------------------------------------------------------ 调度计划

    def waves(self) -> list[list[str]]:
        """静态波次划分（Kahn 分层）。rollback 会让实际执行偏离该计划（重复波）。"""
        layer: dict[str, int] = {}
        for nid in self.engine.dag.nodes:            # dag.nodes 已按拓扑序插入
            deps = self.engine.dag.nodes[nid].depends_on
            layer[nid] = 1 + max((layer[d] for d in deps), default=0)
        bands: dict[int, list[str]] = {}
        for nid, lv in layer.items():
            bands.setdefault(lv, []).append(nid)
        return [sorted(bands[lv]) for lv in sorted(bands)]

    # ------------------------------------------------------------ 执行

    def _run_wave_parallel(self, nodes: list[str]) -> list[tuple[str, NodeResult]]:
        """波内并行调 executor（开销所在），返回 (node_id, result) 列表。"""
        if len(nodes) == 1 or self.max_workers == 1:
            return [(nid, self.engine.executor(nid, self.engine.context_for(nid)))
                    for nid in nodes]
        out: list[tuple[str, NodeResult]] = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(nodes))) as pool:
            futures = {nid: pool.submit(self.engine.executor, nid,
                                        self.engine.context_for(nid))
                       for nid in nodes}
            for nid, fut in futures.items():
                out.append((nid, fut.result()))
        return out

    def run(self) -> dict:
        """循环执行直到 ready 为空；返回 {waves: [...], progress: {...}}。"""
        report: list[dict] = []
        for _ in range(self.max_waves):
            ready = self.engine.ready()
            if not ready:
                break
            approval = [nid for nid in ready if self.engine.needs_approval(nid)]
            parallel = [nid for nid in ready if nid not in approval]

            results: list[tuple[str, NodeResult]] = []
            if parallel:
                results = self._run_wave_parallel(parallel)
                applied = []
                for nid, res in results:
                    try:
                        self.engine.apply_result(nid, res)
                        applied.append({"node": nid, "status": res.status,
                                        "detail": res.reason})
                    except EngineError as e:
                        applied.append({"node": nid, "status": "error",
                                        "detail": str(e)})
            for nid in approval:
                res = self.engine.step(nid)   # 审批节点：进入 waiting
                applied.append({"node": nid, "status": res.status,
                                "detail": res.reason})
            report.append({"wave": len(report), "nodes": ready,
                           "applied": applied})
        else:
            raise EngineError(f"超过 max_waves={self.max_waves}，"
                              "疑似反馈环不收敛")
        return {"waves": report, "progress": self.engine.progress()}
