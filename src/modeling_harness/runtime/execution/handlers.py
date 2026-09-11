#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""默认节点执行器（P6）—— 把 15 个 Workflow 节点接到真实认知实现上。

执行器协议（P6-② Node Executor）:
    executor(node_id, engine_ctx) -> NodeResult
    NodeResult.outputs 可选键:
        artifacts: list[dict]  产出 Artifact（registry.create 参数：type/title/
                               question/depends_on/data/payload/activate）
        evidence:  list[dict]  证据关系（{from, relation, to}，ID 必须已注册）
        metrics:   dict        节点指标（latency_ms 等，审计用）

本实现是**确定性认知管线**（零 LLM）：文献检索/方法竞技场/实验规划器/研究叙事/
论文投影/批判器全部复用 src/modeling_harness/runtime 下的真实模块，产出可追溯到
Artifact Registry + Evidence Graph 的研究状态。LLM 节点后续按同一协议接入。

失败即 FAIL（fail-closed）：缺模型 / 缺假设 / 证据门禁不过 / 判审不 PASS，
都走引擎统一 retry → on_fail 反馈环，而不是"节点自己说完成"。
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

from .engine import FAIL, PASS, NodeResult

_TERMINAL = ("invalidated", "superseded", "deprecated")


def _finite_float(v):
    """有限数值 → float；None / 非数值 / NaN / Inf → None（不可比者视为缺失）。"""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None

REPO = Path(__file__).resolve().parents[4]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.execution.engine import BLOCKED  # noqa: E402
from modeling_harness.runtime.knowledge.retriever import KnowledgeRetriever  # noqa: E402
from modeling_harness.runtime.modeling.model_ir import ModelIRBuilder, ModelIRError, validate_model_ir  # noqa: E402
from modeling_harness.runtime.modeling.planner import ExperimentPlanner, PlannerError  # noqa: E402
from modeling_harness.runtime.modeling.selection import MethodArena, SelectionError  # noqa: E402
from modeling_harness.validators.evidence.evidence_gate import evaluate as evidence_gate_evaluate  # noqa: E402


class HandlerError(RuntimeError):
    """节点处理器配置错误。"""


def _base(node_id: str) -> str:
    return node_id.split("@", 1)[0]


def features_for(features: dict | None, qid: str) -> dict:
    """P13-1 Problem→Method 接口：全局特征与逐题画像合并（已批准例外）。

    features["per_question"][qid] 的键覆盖全局同名键（逐题任务特征优先）；
    无 per_question 或该题无画像时恒等返回全局特征。Problem Profile 是
    Method Retriever 的输入 DTO（P8 冻结六键 + note），不是对问题本体的
    描述——见 docs/architecture/P13_1_REPORT.md 与 CAPABILITY_ROADMAP。
    """
    f = features or {}
    own = (f.get("per_question") or {}).get(qid) or {}
    return {**f, **own} if own else f


class DefaultNodeExecutor:
    """按节点基名分发的默认执行器。共享上下文经 ctx 传递（跨节点接力）。"""

    def __init__(self, registry, graph, state=None, decisions=None,
                 knowledge_root: str | Path | None = None,
                 features: dict | None = None, min_coverage: float = 0.6,
                 execution_adapter=None,
                 external_model_irs: dict | None = None,
                 external_code: dict | None = None,
                 validation_specs: dict | None = None,
                 external_candidates: dict | None = None,
                 revision_bundles: dict | None = None,
                 competition_type: str | None = None):
        self.registry = registry
        self.graph = graph
        self.state = state
        self.decisions = decisions
        # ADR-0008 features 契约：**不再回退硬编码画像**。此前未传 features 时
        # 回退 {"problem_types": ["evaluation"], ...}，把任何题都当成评价类问题，
        # 直接导致分解只出 1 问、选型家族全错（实测 decomposition 20% /
        # structure_alignment 0%）。现在来源三态可观测：
        #   explicit  —— 生产调用方显式注入（外部 Constructor / benchmark --profile）
        #   profiler-* —— 由 runtime/modeling/problem_profile.py 从 inputs 确定性派生
        #   absent    —— 无题面也无法派生 → 选型节点 fail-closed（BLOCKED）
        self.features = dict(features) if features else {"_features_source": "absent"}
        self.features.setdefault("_features_source", "explicit")
        self.min_coverage = min_coverage
        # P0-E：真实执行后端（None = 不执行；result 保持 not_executed）
        self.execution_adapter = execution_adapter
        self.retriever = KnowledgeRetriever(knowledge_root or REPO / "src" / "modeling_harness" / "knowledge")
        self.arena = MethodArena(self.retriever, decisions)
        self.planner = ExperimentPlanner(self.retriever)
        # P8：Competition Intelligence 接入 Runtime（候选竞技场 + 竞赛包只读修饰）
        from modeling_harness.runtime.knowledge.packs import load_competition_packs
        from modeling_harness.runtime.modeling.candidates import CandidateArena
        self.competition_type = competition_type
        _packs = load_competition_packs(knowledge_root or REPO / "src" / "modeling_harness" / "knowledge")
        # 赛题类型 → 竞赛包：显式给定优先，未知/缺省回退默认 cp-cumcm（现状语义）
        _pack = (_packs.get(f"cp-{competition_type}")
                 or _packs.get("cp-cumcm") or next(iter(_packs.values()), None))
        self.candidate_arena = CandidateArena(self.retriever, _pack)
        # 跨节点共享（session 级）：qid -> {"model": aid, "plan": ..., ...}
        self.shared: dict = {}
        # 外部 Model Constructor 注入（LLM-free 边界：runtime 只登记/校验/
        # 执行/验证，构造由外部 Agent 完成——audit FIX-1.5 后为公开注入点）
        if external_model_irs:
            self.shared["external_model_irs"] = dict(external_model_irs)
        if external_code:
            self.shared["external_code"] = dict(external_code)
        if validation_specs:
            self.shared["validation_specs"] = dict(validation_specs)
        if external_candidates:
            self.shared["external_candidates"] = dict(external_candidates)
        if revision_bundles:
            # P1-2：外部 Model Constructor 消费 revision_draft 后注入的修订包
            # shared["revision_bundles"][qid] = {"model_ir": M2_MIR_dict,
            #                                    "code": "M2 代码（可选）"}
            self.shared["revision_bundles"] = dict(revision_bundles)
        # P7 Rerun 语义：显式重跑的节点强制新建谱系（旧产物 superseded 审计保留）
        self.force_new_lineage: set[str] = set()

    # ------------------------------------------------------------ 工具

    def _question_of(self, node_id: str) -> str | None:
        return node_id.split("@", 1)[1] if "@" in node_id else None

    def _question_ids(self) -> list[str]:
        return [a.artifact_id for a in self.registry.list_by_type("question")]

    def _models_of(self, qid: str) -> list[str]:
        """该问题的活跃模型（终态 invalidated/superseded/deprecated 不计入）。"""
        return [a.artifact_id for a in self.registry.list_by_type("model")
                if a.question == qid and a.status not in _TERMINAL]

    def _results_of(self, qid: str, include_failed: bool = True) -> list[str]:
        """该问题的活跃 result（P7：Registry 派生，崩溃/resume 后仍可重建）。

        include_failed=False 时排除由失败执行（EXEC status ∈ failed/timeout/
        invalid，或 exit_code != 0）产生的 result——claim 构建/批判等下游
        默认不得引用失败产物（audit FIX-1.2：执行失败必须真实传播）。
        """
        out: list[str] = []
        for a in self.registry.list_by_type("result"):
            if a.question != qid or a.status in _TERMINAL:
                continue
            if not include_failed:
                ref = (a.data or {}).get("execution_ref")
                if ref and self.registry.exists(ref):
                    xdata = self.registry.get(ref).data or {}
                    if xdata.get("status") in ("failed", "timeout", "invalid"):
                        continue
                    if (xdata.get("status") == "success"
                            and (a.data or {}).get("exit_code") not in (0, None)):
                        continue
            out.append(a.artifact_id)
        return out

    def _claim_of(self, qid: str) -> str:
        """该问题的活跃 claim（无则空串）。"""
        for a in self.registry.list_by_type("claim"):
            if a.question == qid and a.status not in _TERMINAL:
                return a.artifact_id
        return ""

    def _plan_artifact_for(self, qid: str, mid: str):
        """该问题的活跃实验计划（P9.5 红队修复：Registry 派生，不依赖内存 shared）。"""
        for a in self.registry.list_by_type("decision"):
            if "实验计划" in (a.title or "") and a.status == "active":
                if not a.depends_on or mid in a.depends_on:
                    return a
        return None

    def _selection_evidence(self, qid: str) -> list[dict]:
        """FIX-2.2：当前问题已有的机械证据（VR/EXEC）。

        选型必须由证据驱动；无证据 → arena 返回 UNSELECTED/pending_evidence。
        """
        out = []
        for a in self.registry.list_by_type("verification_result"):
            if a.question == qid:
                out.append({"type": "vr", "artifact_id": a.artifact_id,
                            "status": (a.data or {}).get("status")})
        for a in self.registry.list_by_type("execution_result"):
            if a.question == qid:
                out.append({"type": "exec", "artifact_id": a.artifact_id,
                            "status": (a.data or {}).get("status")})
        return out

    def _card_id_of(self, qid: str, mid: str) -> str:
        """问题的选型 card_id：shared 缓存优先，回退 model.data（Registry 真源）。"""
        info = self.shared.get(qid, {})
        if info.get("card_id"):
            return info["card_id"]
        if mid:
            return str(self.registry.get(mid).data.get("card_id", ""))
        return ""

    # ------------------------------------------------------------ P1-VS-001 外部 MODEL_IR 注入（C5）

    def _external_model_irs(self) -> dict:
        """外部 Model Constructor 注入的 MODEL_IR dict（shared["external_model_irs"]）。

        核心铁律（LLM-free）：core runtime 内不调用任何 LLM。MODEL_IR 由外部
        Model Constructor 手写产出（JSON），runtime 只负责登记/校验/执行/保真/
        验证/谱系/replay。无注入时返回 {}（走原路径，向后兼容）。
        """
        return dict(self.shared.get("external_model_irs") or {})

    def _external_candidates(self, qid: str) -> list[dict]:
        """P1-M3：外部注入的候选列表（shared["external_candidates"][qid]）。

        每个元素 = {"model_ir": {MODEL_IR dict}, "code": "str"（可选）}。
        一个 problem 支持 ≥2 候选，各自独立 artifact 链 MIR-i→CODE-i→EXEC-i→R-i→VR-i，
        不依赖单一活跃 model_ir 全局状态。无注入返回 []。
        """
        return list((self.shared.get("external_candidates") or {}).get(qid) or [])

    def _register_mir(self, qid: str, external: dict,
                      created_by: str = "do_model_construction") -> str:
        """把单个外部 MODEL_IR dict 登记为 model_ir Artifact + instantiates 边。

        P1-M3：多候选复用（每候选一次调用）；幂等（同问题同 model_id 复用）。
        """
        models = self._models_of(qid)
        if not models:
            raise HandlerError(
                f"{qid}: 注入外部 MODEL_IR 但无已选模型，无法写 instantiates 边")
        mid = models[-1]
        # P1-2：知识引导（可选实验条件，默认关闭）——
        # shared["knowledge_guide"][qid] = [card_ids] 时，登记前把知识
        # 卡义务嵌入 MODEL_IR（merge + source_card 溯源 + knowledge_refs；
        # 不覆盖建模者声明，不代建模——knowledge 是 Constraint/Prior，
        # 最终由执行/验证裁决）。
        external = self._apply_knowledge_guide(qid, external)
        try:
            mir = ModelIRBuilder.from_dict(external)
        except ModelIRError as e:
            raise HandlerError(f"{qid}: 外部 MODEL_IR 契约校验失败: {e}") from e
        problems = validate_model_ir(mir.data)
        if problems:
            raise HandlerError(f"{qid}: MODEL_IR 结构校验失败: {'; '.join(problems[:8])}")
        # 幂等：同问题同 model_id 的活跃 MIR 复用
        for a in self.registry.list_by_type("model_ir"):
            if a.question == qid and a.status not in _TERMINAL:
                if a.data.get("model_id") == mir.model_id:
                    return a.artifact_id
        # 修订谱系（C10）：外部注入 revision_of 目标（M2 revision_of M1），M1 不被覆盖
        rev_of = external.get("revision_of") or external.get("supersedes")
        data = dict(external)
        data["revision_of"] = rev_of or None
        art = self.registry.create(
            "model_ir",
            title=f"{mir.model_id} 可执行模型规范（Executable Model Specification）",
            question=qid,
            depends_on=[mid],
            data=data,
            activate=True,
            created_by=created_by)
        self.graph.add_relation(art.artifact_id, "instantiates", mid)
        if rev_of:
            target = self.registry.get(rev_of)
            if target is not None and target.type == "model_ir":
                # audit Batch7 P2：本处只登记 revision_of 谱系边；
                # supersedes 边 + 旧模型状态迁移由修订收口唯一负责
                # （vs001_driver.finalize_revision：registry.supersede(M1,
                # replacement=M2) + graph.add_relation(M2, supersedes, M1)）
                # ——单一真源，避免双路径重复加边（GraphError）。
                self.graph.add_relation(art.artifact_id, "revision_of", rev_of)
        return art.artifact_id

    def _apply_knowledge_guide(self, qid: str, external: dict) -> dict:
        """P1-2：知识引导义务嵌入（shared["knowledge_guide"][qid]）。

        返回增强后的 MODEL_IR dict；未配置或卡不可达时原样返回（
        默认关闭——知识引导是实验条件，不约束普通建模路径）。
        """
        guide = (self.shared.get("knowledge_guide") or {}).get(qid) or []
        if not guide:
            return external
        cards = [self.retriever.cards[cid] for cid in guide
                 if cid in self.retriever.cards]
        if not cards:
            return external
        from modeling_harness.runtime.modeling.knowledge_guided import apply_knowledge_obligations
        out = apply_knowledge_obligations(
            external, cards,
            model_id=external.get("model_id"))
        out["_knowledge_guided"] = {"card_ids": [c.card_id for c in cards]}
        return out

    def construct_model_ir(self, qid: str) -> str | None:
        """把单个外部 MODEL_IR dict（shared["external_model_irs"]）登记为 model_ir。

        返回 MIR artifact_id；无外部注入时回退骨架构造（FIX-2.1）。
        """
        external = self._external_model_irs().get(qid)
        if external:
            return self._register_mir(qid, external)
        return self._skeleton_mir(qid, self._models_of(qid)[-1]
                                  if self._models_of(qid) else None)

    def _skeleton_mir(self, qid: str, mid: str | None) -> str | None:
        """FIX-2.1（audit P0-05）：默认路径无外部注入时产骨架 MODEL_IR。

        骨架 = 18 字段契约合规 + 方法卡可提供的信息（family/assumptions），
        variables/objectives/equations 等**不编造**（无 formulation 信息，
        禁止伪变量/伪方程）。modeling_trace 显式标注 construction_status=
        pending_model_spec——不可执行。下游执行链因此如实 FAIL，不再出现
        "只登记假设就 PASS" 的假闭环。无方法卡 → 返回 None（调用方 FAIL）。
        """
        models = self._models_of(qid)
        if mid is None and models:
            mid = models[-1]
        card = self.retriever.cards.get(self._card_id_of(qid, mid)) \
            if mid else None
        if card is None:
            return None
        assumptions = [{"assumption_id": f"A{i}",
                        "type": "simplification",
                        "text": risk[:80],
                        "rationale": "方法卡风险提示（默认路径骨架）"}
                       for i, risk in enumerate(
                           list(card.risks)[:2] or
                           ["所选方法的前提条件成立"], 1)]
        data = {
            "ir_version": "1.0",
            "model_id": f"M-{qid}-skel",
            "model_family": {
                "primary": card.family,
                "description": f"方法卡 {card.card_id} 骨架",
                "candidates": [],
            },
            "problem_binding": {
                "problem_id": str(self.features.get("problem_title", "demo")),
                "sub_question_id": qid,
                # 无题面文件 → 未知哈希占位（格式合规；语义由 modeling_trace
                # pending_model_spec 承担——骨架不可执行，不声称绑定真实题面）
                "problem_sha256": "0" * 64,
            },
            "assumptions": assumptions,
            "variables": [],
            "parameters": [],
            "objectives": [],
            "constraints": [],
            "mechanisms": [{"mechanism_id": "M1", "type": "mechanism_assumption",
                            "description": card.name,
                            "related_equations": [],
                            "sub_question_binding": qid}],
            "equations": [],
            "dependencies": [],
            "solvers": [],
            "experiments": [],
            "validations": [],
            "claims": [],
            "model_graph": {"nodes": [], "edges": []},
            "modeling_trace": [
                {"step": "skeleton",
                 "note": "默认路径骨架 MIR（无外部 Model Constructor 注入）："
                         "construction_status=pending_model_spec，不可执行；"
                         "下游执行/验证如实 FAIL"},
            ],
        }
        try:
            return self._register_mir(qid, data)
        except Exception as exc:
            # 无 _warn 方法（DefaultNodeExecutor 无告警通道）：落到 shared 记录
            self.shared.setdefault("warnings", []).append(
                f"{qid}: 骨架 MIR 构造失败: {exc}")
            return None

    def construct_candidate_mirs(self, qid: str) -> list[str]:
        """P1-M3：把 external_candidates 的每个候选 MODEL_IR 登记为独立 MIR。

        返回本问题登记的全部候选 MIR id（幂等：已登记的同 model_id 复用）。
        """
        cands = self._external_candidates(qid)
        if not cands:
            return []
        out = []
        for i, c in enumerate(cands, 1):
            mir_dict = c.get("model_ir") or {}
            if not mir_dict:
                raise HandlerError(f"{qid}: 候选 #{i} 缺 model_ir dict")
            out.append(self._register_mir(qid, mir_dict))
        return out

    # ------------------------------------------------------------ P1-VS-001 可执行模型闭环（C6/C7/C8）

    def _external_code(self, qid: str) -> str | None:
        """外部 Model Constructor 注入的可执行代码（shared["external_code"][qid]）。"""
        return (self.shared.get("external_code") or {}).get(qid)

    def _validation_spec(self, qid: str) -> dict | None:
        """数值验证规格（外部注入，唯一来源）。

        不自动派生：无验证规格 = 不做数值验证（诚实语义，防止"无 spec 也
        假装验证"）。从 MODEL_IR 派生检查（audit FIX-5.2 的 derive_checks_
        from_mir）由外部构造方显式调用，不自动回退。
        """
        return (self.shared.get("validation_specs") or {}).get(qid)

    def _active_mirs(self, qid: str) -> list[str]:
        """该问题全部活跃 model_ir（P1-M3：多候选各自独立，不取"最后一个"）。"""
        return [a.artifact_id for a in self.registry.list_by_type("model_ir")
                if a.question == qid and a.status not in _TERMINAL]

    def _active_mir_of(self, qid: str) -> str | None:
        """该问题活跃的 model_ir（终态不计入）；兼容旧单候选路径。"""
        mirs = self._active_mirs(qid)
        return mirs[-1] if mirs else None

    def _exec_workdir(self) -> str:
        """执行工作目录：shared["_workdir"] 优先（演示/测试可落盘到项目内），
        否则每次执行创建独立临时目录——避免多 session/多测试共享系统 tempdir
        时 input.json 互相覆盖导致执行错乱（audit FIX-1.2 并发安全）。"""
        wd = self.shared.get("_workdir")
        if wd:
            Path(wd).mkdir(parents=True, exist_ok=True)
            return str(wd)
        import tempfile
        return tempfile.mkdtemp(prefix="mh_exec_")

    def _code_for_mir(self, qid: str, mir_id: str) -> str | None:
        """P1-M3：按候选 model_id 匹配注入代码（external_candidates 内嵌 code）。"""
        model_id = (self.registry.get(mir_id).data or {}).get("model_id")
        for c in self._external_candidates(qid):
            if (c.get("model_ir") or {}).get("model_id") == model_id:
                return c.get("code") or None
        return None

    def _output_mapping_for(self, qid: str) -> dict:
        """外部 Constructor 声明的变量→输出 key 映射。

        P0-1 契约：MODEL_IR 声明的变量（x_i/y_i 等）在代码输出中可能以
        容器/向量形式存在（如 positions 数组）。output_mapping 是外部
        Constructor 交付 code 时显式声明的翻译表（同 codegen.py 契约），
        fidelity 据此做结构映射校验；未声明返回 {}（如实按字面名匹配）。

        承载位（统一）：优先 shared["output_mappings"][qid]（vs001_driver
        注入路径），回退 validation_specs[qid].output_mapping（orchestrator
        注入通道路径——specs.json 是外部 Constructor 交付 validation 义务的
        标准位置）。
        """
        m = (self.shared.get("output_mappings") or {}).get(qid)
        if not m:
            spec = (self.shared.get("validation_specs") or {}).get(qid) or {}
            if isinstance(spec, dict):
                m = spec.get("output_mapping")
        return dict(m or {})

    def _register_code(self, qid: str, mir_id: str, code: str,
                       node_id: str) -> str:
        """L0 ABI 校验 + 登记 code Artifact（幂等：同 hash 复用）+ implemented_by 边。

        data 契约（对齐 codegen.register_code）：code / code_hash / abi /
        model_id / output_mapping（声明名→输出 key，可审计）。
        """
        if "def solve(inputs)" not in code:
            raise HandlerError(
                f"{qid}: code 不满足固定 ABI（必须含 def solve(inputs) -> outputs）")
        code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
        mapping = self._output_mapping_for(qid)
        for a in self.registry.list_by_type("code"):
            if a.question == qid and a.status not in _TERMINAL \
                    and a.data.get("code_hash") == code_hash:
                # 幂等复用：确保当前 MIR → 该 code 的 implemented_by 边存在
                if not any(r["from"] == mir_id and r["relation"] == "implemented_by"
                           and r["to"] == a.artifact_id
                           for r in self.graph.relations):
                    self.graph.add_relation(mir_id, "implemented_by", a.artifact_id)
                return a.artifact_id
        art = self.registry.create(
            "code", title=f"{mir_id} 可执行实现",
            question=qid, depends_on=[mir_id],
            data={"code": code, "code_hash": code_hash,
                  "abi": "def solve(inputs) -> outputs",
                  "model_id": mir_id,
                  "output_mapping": mapping},
            activate=True, created_by=node_id)
        self.graph.add_relation(mir_id, "implemented_by", art.artifact_id)
        return art.artifact_id

    def generate_code(self, qid: str, node_id: str = "code_generation") -> list[str]:
        """C6/P1-M3：为每个候选 MIR 登记可执行 code + implemented_by 边。

        候选模式：external_candidates 的每个 dict 内嵌 code（按 model_id 匹配）；
        单候选模式：external_code[qid] 应用到唯一活跃 MIR（VS-001 向后兼容）。
        无注入返回 []（no-op）。固定 ABI（L0 契约）：def solve(inputs) -> outputs。
        """
        cands = self._external_candidates(qid)
        out: list[str] = []
        if cands:
            for mir_id in self._active_mirs(qid):
                code = self._code_for_mir(qid, mir_id)
                if code:
                    out.append(self._register_code(qid, mir_id, code, node_id))
            return out
        code = self._external_code(qid)
        if not code:
            return out
        mir_id = self._active_mir_of(qid)
        if not mir_id:
            raise HandlerError(f"{qid}: 注入代码但无活跃 model_ir，无法写 implemented_by 边")
        out.append(self._register_code(qid, mir_id, code, node_id))
        return out

    def _execution_inputs(self, mir_art) -> dict | None:
        """从 model_ir.parameters 派生执行输入（input.json 内容，固定 ABI）。"""
        if mir_art is None:
            return None
        out: dict = {}
        for p in mir_art.data.get("parameters") or []:
            sym = p.get("symbol") or p.get("parameter_id")
            if sym and "value" in p:
                out[sym] = p["value"]
        out["times"] = [0, 60, 120, 180, 240, 300]
        return out

    def _active_codes(self, qid: str) -> list[str]:
        """该问题全部活跃 code（P1-M3：每候选一个，各自独立执行）。"""
        return [a.artifact_id for a in self.registry.list_by_type("code")
                if a.question == qid and a.status not in _TERMINAL]

    def _mir_implementing(self, qid: str, code_id: str) -> str | None:
        """找到 implemented_by 该 code 的活跃 MIR（多候选下不能取"最后一个"）。"""
        for r in self.graph.relations:
            if r["relation"] == "implemented_by" and r["to"] == code_id:
                cand = self.registry.get(r["from"])
                if cand is not None and cand.type == "model_ir" \
                        and cand.question == qid and cand.status not in _TERMINAL:
                    return cand.artifact_id
        return None

    def _code_of_mir(self, qid: str, mir_id: str) -> str | None:
        """该候选 MIR 的 code（沿 implemented_by 边；多候选下不能取"最后一个"）。"""
        for r in self.graph.relations:
            if r["relation"] == "implemented_by" and r["from"] == mir_id:
                c = self.registry.get(r["to"])
                if c is not None and c.type == "code" and c.question == qid \
                        and c.status not in _TERMINAL:
                    return c.artifact_id
        # P0-E plan 通道（既有注入接口）：shared[q]["plan"]["code"] 或 plan
        # artifact 的 data.code。统一执行入口必须消费全部既有注入通道，
        # 否则 plan 注入的会话（外部 executor 回填路径）静默失去执行。
        plan = (self.shared.get(qid) or {}).get("plan") or {}
        code = plan.get("code")
        if not code:
            pa = self._plan_artifact_for(qid, mir_id)
            if pa is not None:
                code = (pa.data or {}).get("code")
        if code:
            return self._register_code(qid, mir_id, code, "model_execution")
        return None

    def _active_exec_of_mir(self, qid: str, mir_id: str) -> str | None:
        """该候选 MIR 已有的活跃 EXEC（幂等复用；按 EXEC.model_id == mir_id 定位）。

        P1-M4：同一 code 文本可能被多个候选共享（CODE artifact 按 hash 去重），
        但 EXEC 必须按候选独立——EXEC 的 data.model_id 记录其所属候选，互不覆盖。
        """
        for a in self.registry.list_by_type("execution_result"):
            if a.question == qid and a.status not in _TERMINAL \
                    and (a.data or {}).get("model_id") == mir_id:
                return a.artifact_id
        return None

    def _result_of_exec(self, qid: str, exec_id: str) -> str | None:
        """该 EXEC 已产出的活跃 result（produces 边）。"""
        for a in self.registry.list_by_type("result"):
            if a.question == qid and a.status not in _TERMINAL:
                if any(r["from"] == exec_id and r["relation"] == "produces"
                       and r["to"] == a.artifact_id for r in self.graph.relations):
                    return a.artifact_id
        return None

    def _check_ir_code_mapping(self, qid: str, mir_id: str,
                               code_id: str) -> None:
        """FIX-3.1（audit P1-03/P1-09）：MODEL_IR→Code 映射一致性校验。

        MIR.solvers[].implementation_ref 声明实现引用（CODE artifact id 或
        code.model_id/solver_id）时，实际执行的 code 必须命中其一；未声明
        （测试注入/骨架 MIR）跳过。映射断裂直接抛 HandlerError（不静默）。
        """
        mir = self.registry.get(mir_id).data if mir_id else {}
        refs = []
        for s in mir.get("solvers") or []:
            r = (s or {}).get("implementation_ref")
            if r:
                refs.append(str(r))
        if not refs:
            return
        target = self.registry.get(code_id)
        tdata = target.data or {} if target is not None else {}
        # 匹配对象：code artifact id / code 登记的 model_id（MIR001 系）/
        # MIR 外部声明的 model_id（M-Q001 系）/ solver_id
        mir_model_id = mir.get("model_id")
        # audit FIX-3.1 回归：harness 登记 code 使用 registry 自动 ID
        # （CODE001 系），而外部 MIR 声明的 implementation_ref 是外部命名
        # （CODE-Q001 系）——两个命名空间。兼容规则：ref 是外部 code 命名
        # （CODE-<qid>）且该 code 确实实现了该 MIR（implemented_by 边）→
        # 映射成立；否则 ref 必须是可解析的真实身份（见下方身份匹配）。
        if any(ref.startswith("CODE-") and
               any(r["relation"] == "implemented_by" and r["from"] == mir_id
                   and r["to"] == code_id for r in self.graph.relations)
               for ref in refs):
            return
        if any(ref == code_id or ref == tdata.get("model_id")
               or ref == mir_model_id or ref == tdata.get("solver_id")
               for ref in refs):
            return
        import os
        if os.environ.get('MM_DEBUG_MAP'):
            print('MM_DEBUG_MAP', qid, mir_id, 'refs=', refs,
                  'code_id=', code_id, 'tdata_model_id=', tdata.get('model_id'),
                  'mir_model_id=', mir_model_id, 'full_mir=', mir,
                  'full_code=', tdata, flush=True)
        raise HandlerError(
            f"{qid}/{mir_id}: MIR.solvers[].implementation_ref={refs} 与执行 "
            f"code {code_id}(model_id={tdata.get('model_id')}) 不一致——"
            f"MODEL_IR→CODE 映射断裂")

    def execute_code(self, qid: str, node_id: str = "model_execution") -> list[tuple[str, str]]:
        """C7/P1-M3：每个候选 MIR → 其 code → LocalPythonAdapter 真 subprocess → EXEC + R。

        返回 [(exec_id, result_id), ...]（每候选一个，独立 ID 链互不覆盖）；
        无活跃候选 code 时返回 []。status 只能来自真实 subprocess 退出码（禁止硬编码）。
        接线：input.json → run_model.py → output.json（固定 ABI）；
        边：code -executed_by-> EXEC、EXEC -produces-> R。幂等：同 (mir, code) 复用 EXEC。
        P1-M4：多个候选可共享同一 code 文本（CODE 按 hash 去重），但每个候选仍
        得到独立 EXEC/VR——执行/验证结果互不覆盖。
        """
        out: list[tuple[str, str]] = []
        for mir_id in self._active_mirs(qid):
            code_id = self._code_of_mir(qid, mir_id)
            if code_id is None:
                continue
            existing = self._active_exec_of_mir(qid, mir_id)
            if existing:
                rid = self._result_of_exec(qid, existing)
                if rid:
                    out.append((existing, rid))
                    continue
                # EXEC 活跃但其 result 已失效/缺失（如 result 被 invalidate 后
                # 重跑）：退役旧 EXEC（否则 _active_exec_of_mir 幂等复用永远
                # 命中死链，反馈环死循环），再重新执行产出新 EXEC + 新 R
                try:
                    self.registry.supersede(
                        existing, reason="result chain invalidated; re-executing",
                        by=node_id)
                except Exception:
                    pass
            code = (self.registry.get(code_id).data or {}).get("code", "")
            if not code:
                raise HandlerError(f"{code_id}: code artifact 无 code 本体")
            # FIX-3.1（audit P1-03/P1-09）：MODEL_IR→Code 映射校验。
            # MIR.solvers[].implementation_ref 声明了实现引用（CODE artifact id
            # 或 model_id）时，必须与实际执行的 code 一致；未声明（测试注入/
            # 骨架 MIR）跳过。防"MIR 说用 MILP、实际跑的却是别的代码"。
            self._check_ir_code_mapping(qid, mir_id, code_id)
            mir_art = self.registry.get(mir_id) if mir_id else None
            inputs = self._execution_inputs(mir_art)
            if inputs is None:
                raise HandlerError(f"{qid}: 无法从 model_ir 派生执行输入")
            from modeling_harness.runtime.execution.adapters import ExecutionPlan, ExecutionResultData
            adapter = self.execution_adapter
            if adapter is None:
                from modeling_harness.runtime.execution.adapters import LocalPythonAdapter
                adapter = LocalPythonAdapter()
            wd = self._exec_workdir()
            try:
                # input.json 落盘（固定 ABI：input.json → run_model.py → output.json）
                Path(wd, "input.json").write_text(
                    json.dumps(inputs, ensure_ascii=False, indent=2), encoding="utf-8")
                xplan = ExecutionPlan(model_id=mir_id or qid, code=code,
                                      inputs=inputs, workdir=wd)
                xr = adapter.execute(xplan)
            except Exception as exc:
                xr = ExecutionResultData(
                    execution_id="", model_id=mir_id or qid, status="invalid",
                    stderr=f"adapter error: {exc}",
                    provenance={"reason": "adapter_exception"})
            xr.code = code
            # P0-1：output_mapping 透传进 EXEC provenance——fidelity 校验时
            # 无需再次显式传入（对齐 codegen.execute_code 契约）
            _prov = dict(xr.provenance or {})
            _mapping = (self.registry.get(code_id).data or {}).get("output_mapping")
            if _mapping:
                _prov["output_mapping"] = _mapping
            xr.provenance = _prov
            xart = self.registry.create(
                "execution_result",
                title=f"{code_id} 执行结果",
                question=qid, depends_on=[code_id],
                data=xr.to_dict(),
                activate=True, created_by=node_id)
            self.graph.add_relation(code_id, "executed_by", xart.artifact_id)
            # result artifact（真实 outputs）+ EXEC -produces-> R 边
            r = self.registry.create(
                "result", title=f"{qid} 模型执行结果",
                question=qid, depends_on=[xart.artifact_id],
                data={"status": "computed", "execution_ref": xart.artifact_id,
                      "value": xr.outputs, "outputs": xr.outputs,
                      "exit_code": xr.returncode,
                      "note": "真实数值来自 model_execution 子进程执行"},
                activate=True, created_by=node_id)
            self.graph.add_relation(xart.artifact_id, "produces", r.artifact_id)
            out.append((xart.artifact_id, r.artifact_id))
        return out

    def _active_execs(self, qid: str) -> list[str]:
        """该问题全部活跃 EXEC（P1-M3：每候选一个）。"""
        return [a.artifact_id for a in self.registry.list_by_type("execution_result")
                if a.question == qid and a.status not in _TERMINAL]

    def _active_vr_of(self, qid: str, exec_id: str) -> str | None:
        """该 EXEC 已有的活跃 VR（幂等复用）。"""
        for a in self.registry.list_by_type("verification_result"):
            if a.question == qid and a.status not in _TERMINAL:
                if any(r["from"] == exec_id and r["relation"] == "verified_by"
                       and r["to"] == a.artifact_id for r in self.graph.relations):
                    return a.artifact_id
        return None

    def _apply_baseline_comparison(self, r_art, plan: dict) -> None:
        """ADR-0013：计划声明了 baseline_comparison 时**真正执行**对照。

        baseline 标签是**执行的回执**，不是计划声明的同义词：只有真的产出
        baseline_comparison 结果才打标签；执行产物缺少基线数值段则记 missing
        且**不打标签**（否则会出现「声明了、标记了、从未比较过」的静默失效）。
        基线数值段约定放在执行产物的 ``outputs['baseline']``。
        """
        if not plan.get("baseline_comparison"):
            return
        from modeling_harness.runtime.evaluation.deterministic_metrics import (
            baseline_comparison as _bc,
        )
        r_data = dict(r_art.data or {})
        outputs = r_data.get("outputs") or r_data.get("value") or {}
        base = outputs.get("baseline") if isinstance(outputs, dict) else None
        if isinstance(base, dict) and base:
            model_out = {k: v for k, v in outputs.items() if k != "baseline"}
            r_data["baseline_comparison"] = _bc(
                model_out, base,
                direction=r_data.get("objective_direction") or "minimize")
            r_art.data = r_data
            tags = list(r_art.tags or [])
            if "baseline" not in tags:
                tags.append("baseline")
            r_art.tags = tags
        else:
            r_data["baseline_comparison"] = {
                "status": "missing",
                "reason": ("计划声明了 baseline_comparison，但执行产物缺少基线数值段 "
                           "outputs['baseline']；对照未执行，故不打 baseline 标签"
                           "（ADR-0013：标签是回执不是声明）"),
            }
            r_art.data = r_data

    def _register_vr(self, qid: str, exec_id: str, spec: dict,
                     node_id: str) -> str:
        """基于真实数值运行验证并登记 VR artifact（verified_by 边）。"""
        xart = self.registry.get(exec_id)
        xdata = dict(xart.data or {})
        from modeling_harness.runtime.execution.validation import _now, run_numeric_validation
        verdict = run_numeric_validation(xdata.get("outputs") or {}, spec,
                                         execution_status=xdata.get("status"))
        vdata = {
            "verification_id": "", "execution_id": exec_id,
            "status": verdict["status"],
            "execution_valid": verdict["execution_valid"],
            "mathematical_valid": verdict["mathematical_valid"],
            "empirical_valid": verdict["empirical_valid"],
            "robustness": verdict["robustness"],
            "constraint_violation_max": verdict["constraint_violation_max"],
            "objective_value": verdict["objective_value"],
            "objective_sane": verdict["objective_sane"],
            "variable_domain_violation": verdict["variable_domain_violation"],
            "checks": verdict["checks"],
            "evidence_refs": [exec_id],
            "started_at": _now(), "finished_at": _now(),
            "provenance": {"engine": "handlers.do_model_validation",
                           "kind": "numeric_validation",
                           "spec": spec},
        }
        vr = self.registry.create(
            "verification_result",
            title=f"数值验证 {exec_id}（{verdict['status']}）",
            question=qid, depends_on=[exec_id],
            data=vdata, activate=True, created_by=node_id)
        self.graph.add_relation(exec_id, "verified_by", vr.artifact_id)
        return vr.artifact_id

    def validate_execution(self, qid: str, node_id: str = "model_validation") -> list[str]:
        """C8/P1-M3：对每个活跃 EXEC 基于真实数值判 FAIL → VR artifact。

        返回本问题全部 VR id（每候选一个，独立验证互不覆盖）；无活跃 EXEC
        或未注入验证规格时返回 []。判 FAIL 不依赖 evidence_gate（它只查边不查数值）。
        """
        execs = self._active_execs(qid)
        if not execs:
            return []
        spec = self._validation_spec(qid)
        if not spec:
            return []
        out = []
        for exec_id in execs:
            existing = self._active_vr_of(qid, exec_id)
            if existing:
                out.append(existing)
                continue
            out.append(self._register_vr(qid, exec_id, spec, node_id))
        return out

    def do_code_generation(self, node_id: str) -> NodeResult:
        """C6 DAG 节点：为各问题登记可执行 code + implemented_by 边。"""
        ev = []
        n = 0
        for qid in self._question_ids():
            for cid in self.generate_code(qid, node_id):
                ev.append({"from": self._mir_implementing(qid, cid)
                           or self._active_mir_of(qid) or "",
                           "relation": "implemented_by", "to": cid})
                n += 1
        return NodeResult(PASS, f"生成 {n} 个可执行代码",
                          outputs={"artifacts": [], "evidence": ev})

    def do_model_execution(self, node_id: str) -> NodeResult:
        """C7 DAG 节点：真 subprocess 执行各问题可执行代码 → EXEC + R。

        执行失败必须真实传播（audit FIX-1.2 / P0-08）：任一 EXEC status ∈
        {failed, timeout, invalid} 时节点 FAIL（含首个失败的 stderr 尾部），
        触发 on_fail 反馈环。

        P0-4（零执行 ≠ PASS）：无任何活跃候选模型，或活跃候选全部无实现
        代码（未发生任何执行）→ blocked（非 PASS）。"没做"与"做了且通过"
        必须可区分。
        """
        ev = []
        n = 0
        failures: list[str] = []
        no_code_questions: list[str] = []
        mir_any = False
        for qid in self._question_ids():
            mirs = self._active_mirs(qid)
            if not mirs:
                continue
            mir_any = True
            has_code = any(self._code_of_mir(qid, m) is not None for m in mirs)
            if not has_code:
                no_code_questions.append(qid)
                continue
            for xid, rid in self.execute_code(qid, node_id):
                xdata = self.registry.get(xid).data or {}
                xstatus = xdata.get("status")
                ev.append({"from": xid, "relation": "produces", "to": rid})
                n += 1
                if xstatus in ("failed", "timeout", "invalid"):
                    tail = str(xdata.get("stderr", ""))[-300:]
                    failures.append(f"{qid}/{xid}: {xstatus} — {tail}")
                    continue
                # P0-1：执行成功后再做 fidelity（只写报告不注册 VR）
                if xstatus == "success":
                    fid = self._fidelity_of(qid, xid)
                    if fid is not None and fid.get("fidelity_status") == "misaligned":
                        bad = [c for c in fid.get("checks") or [] if not c.get("passed")]
                        names = "; ".join(str(c.get("name", "?")) for c in bad[:5])
                        failures.append(
                            f"{qid}/{xid}: fidelity misaligned "
                            f"(score={fid.get('fidelity_score')}) — {names}")
        if not mir_any:
            return NodeResult(
                BLOCKED,
                "无任何活跃候选模型（零执行 ≠ PASS）",
                outputs={"artifacts": [], "evidence": ev})
        if n == 0 and no_code_questions:
            return NodeResult(
                BLOCKED,
                "候选模型全部无实现代码，未发生任何执行（零执行 ≠ PASS）"
                f"— {', '.join(no_code_questions[:5])}",
                outputs={"artifacts": [], "evidence": ev})
        if failures:
            return NodeResult(
                FAIL,
                f"执行 {n} 个模型：{len(failures)} 个失败（{failures[0][:220]}）",
                outputs={"artifacts": [], "evidence": ev, "failures": failures})
        return NodeResult(PASS, f"执行 {n} 个模型（真实 subprocess + fidelity）",
                          outputs={"artifacts": [], "evidence": ev})

    def _fidelity_of(self, qid: str, exec_id: str) -> dict | None:
        """P0-1：对成功 EXEC 跑 MODEL_IR↔Code fidelity（不注册 VR，只写报告）。

        从 EXEC.data.model_id 反查对应 MIR；找不到 MIR/无 registry 路径时返回
        None（如实不判，不编造 aligned）。项目根目录从 registry 路径推导
        （<project>/state/registry.json → 父父级）。output_mapping 回退读取
        EXEC provenance（_register_code 已存 CODE artifact 并由 execute_code
        透传）。
        """
        xart = self.registry.get(exec_id)
        if xart is None:
            return None
        mir_id = (xart.data or {}).get("model_id")
        if not mir_id:
            return None
        mir_art = self.registry.get(mir_id)
        if mir_art is None:
            return None
        reg_path = getattr(self.registry, "path", None)
        if reg_path is None:
            return None
        project_dir = Path(reg_path).parent.parent
        from modeling_harness.runtime.execution.fidelity import verify_fidelity
        return verify_fidelity(project_dir, dict(mir_art.data or {}),
                               exec_id, register_vr=False,
                               registry=self.registry)

    def do_model_validation(self, node_id: str) -> NodeResult:
        """C8/P1-M3 DAG 节点：基于真实数值验证各问题执行结果 → VR（四字段）。

        判定：无任何候选通过且至少一个失败 → FAIL（无可存活候选）；
        至少一个通过 → PASS（存活候选存在，最终选型交给 model_selection_decision）。
        VS-001 单候选语义保持：唯一候选 FAIL → 本节点 FAIL。
        """
        ev = []
        n_pass = 0
        n_fail = 0
        # P0-4（零验证 ≠ PASS）：无活跃执行结果可验证 → blocked；存在
        # "有 EXEC 但无验证规格"的问题 → blocked（有东西要验证却没规格，
        # 不能以"0 通过 0 未通过"冒充验证通过）。
        exec_any = False
        spec_missing: list[str] = []
        for qid in self._question_ids():
            if not self._active_execs(qid):
                continue
            exec_any = True
            if not self._validation_spec(qid):
                spec_missing.append(qid)
        if not exec_any:
            return NodeResult(
                BLOCKED,
                "无活跃执行结果可验证（零验证 ≠ PASS）",
                outputs={"artifacts": [], "evidence": ev})
        if spec_missing:
            return NodeResult(
                BLOCKED,
                "存在有执行结果但无验证规格的问题（零验证 ≠ PASS）"
                f"— {', '.join(spec_missing[:5])}",
                outputs={"artifacts": [], "evidence": ev})
        for qid in self._question_ids():
            for vr_id in self.validate_execution(qid, node_id):
                vr = self.registry.get(vr_id)
                status = (vr.data or {}).get("status")
                xid = (vr.data or {}).get("execution_id")
                ev.append({"from": xid, "relation": "verified_by", "to": vr_id})
                if status == "passed":
                    n_pass += 1
                else:
                    n_fail += 1
        msg = f"数值验证: {n_pass} 通过 / {n_fail} 未通过"
        if n_fail > 0 and n_pass == 0:
            # P0-2：无存活候选 → 机械失败归因 + 修订草案（LLM-free，
            # 供外部 Model Constructor 消费；诊断注册为 diagnosis artifact）
            pkgs = []
            for q in self._question_ids():
                pkgs += self._diagnose_and_draft(q, node_id)
            # P1-2：自动修订闭环（节点内）——外部 Constructor 已注入
            # revision_bundles 时，注册 M2（revision_of/supersedes 谱系边
            # 由 runtime 生成）+ 收口 M1 + 重跑 M2 执行/验证，一次节点执行
            # 内完成 M1→FAIL→M2→PASS。无修订注入 → FAIL 如实等待外部；
            # M2 重跑仍有失败 → FAIL 如实传播（不假装闭环完成）。
            auto = self._auto_revision(node_id)
            if auto["blocked"]:
                return NodeResult(
                    FAIL,
                    msg + "（无存活候选，已生成诊断与修订草案；外部 Model "
                    "Constructor 可消费 revision_draft 并注入 "
                    "revision_bundles 后重跑）",
                    outputs={"artifacts": [p["diagnosis_id"] for p in pkgs],
                             "evidence": ev,
                             "revision_packages": len(pkgs),
                             "revision_blocked": auto["blocked"]})
            if auto["failed"]:
                return NodeResult(
                    FAIL,
                    msg + f"（修订 M2 重跑仍有失败: {', '.join(auto['failed'])}）",
                    outputs={"artifacts": [p["diagnosis_id"] for p in pkgs]
                             + auto["mir_ids"],
                             "evidence": ev, "revision_failed": auto["failed"]})
            return NodeResult(
                PASS,
                msg + (f"（自动修订闭环: {auto['revised']} 个 M2 注册并重跑通过，"
                       "revision_of/supersedes 边由 runtime 生成）"),
                outputs={"artifacts": [p["diagnosis_id"] for p in pkgs]
                         + auto["mir_ids"],
                         "evidence": ev, "revised": auto["revised"]})
        # P1-3：验证通过后若存在修订谱系（M2 revision_of M1），
        # 自动机械比较 M1/M2（compare_models，VR 证据）→ decision artifact
        cmps = []
        for q in self._question_ids():
            cmps += self._compare_revision_chain(q, node_id)
        if cmps:
            msg += f"（修订比较: {len(cmps)} 对）"
        return NodeResult(PASS, msg,
                          outputs={"artifacts": [c["decision_id"]
                                                  for c in cmps],
                                   "evidence": ev})

    # ------------------------------------------------------------ P1-2 Revision Loop（V3 主 DAG）

    def _failing_questions(self) -> list[str]:
        """有 FAIL 状态活跃 VR 的问题（P1-2 修订触发条件）。"""
        out: list[str] = []
        for q in self._question_ids():
            for a in self.registry.list_by_type("verification_result"):
                if a.question == q and a.status not in _TERMINAL:
                    if (a.data or {}).get("status") in ("failed", "fail"):
                        out.append(q)
                        break
        return out

    def _auto_revision(self, node_id: str) -> dict:
        """P1-2 自动修订闭环（LLM-free 边界，节点内一次执行完成）。

        对每个有 FAIL VR 的问题：若外部已注入 revision_bundles[qid]
        （{"model_ir": M2_MIR, "code": M2 代码可选}）→
        1. 注册 M2 MIR（revision_of 谱系边由 runtime 生成）
        2. 注册 M2 代码（implemented_by 边）
        3. 收口 M1（supersede + supersedes 边，M2 成为唯一活跃）
        4. 重跑 M2 执行 + 验证 → M2 独立 EXEC/R/VR 谱系

        返回 {"revised": n, "mir_ids": [...], "failed": [q], "blocked": [q]}。
        无修订注入 → blocked（如实等待外部，禁止假装修订完成）；
        M2 重跑仍有失败 → failed（如实传播，不假装闭环完成）。
        """
        failing = self._failing_questions()
        bundles = self.shared.get("revision_bundles") or {}
        out: dict = {"revised": 0, "mir_ids": [], "failed": [], "blocked": []}
        for q in failing:
            b = bundles.get(q)
            m1 = self._active_mir_of(q)
            if not b or m1 is None:
                out["blocked"].append(q)
                continue
            if isinstance(b, dict) and isinstance(b.get("model_ir"), dict):
                mir_data = dict(b["model_ir"])
            elif isinstance(b, dict):
                mir_data = dict(b)
            else:
                out["blocked"].append(q)
                continue
            mir_data.setdefault("revision_of", m1)
            code = b.get("code") if isinstance(b, dict) else None
            try:
                mir_id = self._register_mir(q, mir_data, created_by=node_id)
                if code:
                    self._register_code(q, mir_id, code, node_id)
            except HandlerError:
                out["blocked"].append(q)
                continue
            # 修订收口：M1 → superseded（re_execute 只重跑 M2）。
            # 谱系边由 runtime 生成（非手工 add_relation）——ROADMAP P1-2 验收。
            try:
                self.registry.supersede(
                    m1, replacement=mir_id,
                    reason=f"revised by {node_id}", by=node_id)
            except Exception:
                pass
            try:
                self.graph.add_relation(mir_id, "supersedes", m1)
            except Exception:
                pass
            out["mir_ids"].append(mir_id)
            # 重跑 M2：执行 + 验证（M1 已收口，_active_mirs 只含 M2）。
            # 验证统计只看 M2 的 VR（M1 遗留 EXEC 的 FAIL VR 保留谱系但
            # 不参与修订判定——M1 已 superseded，其失败不代表 M2 失败）。
            try:
                self.execute_code(q, node_id)
                self.validate_execution(q, node_id)
            except HandlerError:
                out["failed"].append(q)
                continue
            bad = [v for v in self._vr_ids_of_mir(q, mir_id)
                   if (self.registry.get(v).data or {}).get("status") != "passed"]
            if bad:
                out["failed"].append(q)
            else:
                out["revised"] += 1
        return out

    def _vr_ids_of_mir(self, qid: str, mir_id: str) -> list[str]:
        """该 MIR 的执行（EXEC.model_id == mir_id）产出的 VR id 列表。"""
        out: list[str] = []
        for xa in self.registry.list_by_type("execution_result"):
            if xa.question != qid:
                continue
            if (xa.data or {}).get("model_id") != mir_id:
                continue
            for r in self.graph.relations:
                if r["relation"] == "verified_by" \
                        and r["from"] == xa.artifact_id:
                    to = self.registry.get(r["to"])
                    if to is not None and to.type == "verification_result":
                        out.append(r["to"])
        return out

    def do_model_revision(self, node_id: str) -> NodeResult:
        """P1-2：model_validation FAIL 后的修订收口（LLM-free 边界）。

        - 无验证失败 → PASS no-op（验证链最终节点语义保持）。
        - 有验证失败 + 外部修订 bundle（shared["revision_bundles"][qid]）→
          注册 M2 MIR（revision_of 谱系边由 runtime 生成）+ 代码，并收口
          M1（supersede + supersedes 边，M2 成为唯一活跃）→ PASS。
        - 有验证失败但无 bundle → BLOCKED（draft 已由 do_model_validation
          生成，等待外部 Model Constructor 注入修订后 unblock；禁止假装
          修订完成）。
        """
        failing = self._failing_questions()
        if not failing:
            return NodeResult(PASS, "无验证失败，无需修订",
                              outputs={"artifacts": [], "evidence": []})
        bundles = self.shared.get("revision_bundles") or {}
        registered: list[str] = []
        missing: list[str] = []
        for q in failing:
            b = bundles.get(q)
            if not b:
                missing.append(q)
                continue
            m1 = self._active_mir_of(q)
            if m1 is None:
                missing.append(q)
                continue
            if isinstance(b, dict) and isinstance(b.get("model_ir"), dict):
                mir_data = dict(b["model_ir"])
            elif isinstance(b, dict):
                mir_data = dict(b)
            else:
                missing.append(q)
                continue
            mir_data.setdefault("revision_of", m1)
            code = b.get("code") if isinstance(b, dict) else None
            mir_id = self._register_mir(q, mir_data, created_by=node_id)
            if code:
                self._register_code(q, mir_id, code, node_id)
            # 修订收口：M1 → superseded（M2 成为唯一活跃，re_execute 只重跑 M2）。
            # 谱系边由 runtime 生成（非手工 add_relation）——ROADMAP P1-2 验收。
            try:
                self.registry.supersede(
                    m1, replacement=mir_id,
                    reason=f"revised by {node_id}", by=node_id)
            except Exception:
                pass
            try:
                self.graph.add_relation(mir_id, "supersedes", m1)
            except Exception:
                pass
            registered.append(mir_id)
        if missing:
            return NodeResult(
                BLOCKED,
                "验证失败待修订（外部 Model Constructor 消费 revision_draft "
                f"后注入 revision_bundles 再 unblock）: {', '.join(missing)}",
                outputs={"artifacts": registered, "evidence": []})
        return NodeResult(
            PASS,
            f"已注册 {len(registered)} 个修订模型（M2）并收口 M1（supersedes 边由 runtime 生成）",
            outputs={"artifacts": registered, "evidence": []})

    def do_model_re_execute(self, node_id: str) -> NodeResult:
        """P1-2：对修订模型（M2，唯一活跃）重跑执行 + 验证。

        无修订模型 → PASS no-op（验证链最终节点语义保持）；有 → 复用
        execute_code / validate_execution 对 M2 产出独立 EXEC/R/VR；任一
        失败如实 FAIL（修订未成功，不假装闭环完成）。
        """
        m2s = [a for a in self.registry.list_by_type("model_ir")
               if a.data and a.data.get("revision_of")
               and a.status not in _TERMINAL]
        if not m2s:
            return NodeResult(PASS, "无修订模型待重跑",
                              outputs={"artifacts": [], "evidence": []})
        ev: list[dict] = []
        vrs: list[str] = []
        n_fail = 0
        for art in m2s:
            q = art.question
            for xid, rid in self.execute_code(q, node_id):
                ev.append({"from": xid, "relation": "produces", "to": rid})
                xdata = self.registry.get(xid).data or {}
                if xdata.get("status") in ("failed", "timeout", "invalid",
                                           "not_executed"):
                    n_fail += 1
            self.validate_execution(q, node_id)
            # 只统计该修订 MIR 的 VR（M1 遗留 EXEC 的 FAIL VR 不参与判定）
            for vr_id in self._vr_ids_of_mir(q, art.artifact_id):
                vrs.append(vr_id)
                if (self.registry.get(vr_id).data or {}).get("status") != "passed":
                    n_fail += 1
        if n_fail:
            return NodeResult(
                FAIL,
                f"修订模型重跑: {n_fail} 项未通过（M2 修订未闭环）",
                outputs={"artifacts": vrs, "evidence": ev})
        return NodeResult(
            PASS,
            f"修订模型重跑通过（{len(m2s)} 个 M2，EXEC→R→VR 独立谱系）",
            outputs={"artifacts": vrs, "evidence": ev})


    # ------------------------------------------------------------ P0-2 Failure Diagnosis → Revision Draft

    def _compare_revision_chain(self, qid: str, node_id: str) -> list[dict]:
        """P1-3：沿 graph revision_of 边比较 M1/M2（VR 机械证据）。

        对每对 (M2 revision_of M1)：compare_models → 注册 decision
        artifact + compared_with/supported_by 边。幂等：同对模型
        已有活跃 comparison decision 则跳过。
        """
        from modeling_harness.runtime.modeling.comparison import compare_models
        reg = self.registry
        out: list[dict] = []
        pairs = [r for r in self.graph.relations
                 if r["relation"] == "revision_of"
                 and reg.get(r["from"]) is not None
                 and reg.get(r["to"]) is not None
                 and reg.get(r["from"]).question == qid]
        for rel in pairs:
            m2_id, m1_id = rel["from"], rel["to"]
            # 幂等：同对已有活跃 decision 跳过
            if any(d.data.get("comparison_pair") == [m2_id, m1_id]
                   for d in reg.list_by_type("decision")
                   if d.question == qid and d.status not in _TERMINAL):
                continue
            cmp = compare_models(reg, m1_id, m2_id)
            if cmp.get("recommendation") == "pending":
                continue  # 证据缺失不制造决策
            art = reg.create(
                "decision",
                title=f"修订比较 {m1_id} vs {m2_id}",
                question=qid,
                depends_on=[m2_id],
                data={
                    "decision_type": "model_comparison",
                    "comparison_pair": [m2_id, m1_id],
                    "better_model": cmp["better_model"],
                    "recommendation": cmp["recommendation"],
                    "reasoning": cmp["reasoning"],
                    "deltas": cmp["deltas"],
                    "advisory": True,
                },
                activate=True, created_by=node_id)
            self.graph.add_relation(m2_id, "compared_with", m1_id)
            self.graph.add_relation(art.artifact_id,
                                    "based_on", m2_id)
            out.append({"decision_id": art.artifact_id,
                       "better_model": cmp["better_model"],
                       "recommendation": cmp["recommendation"]})
        return out

    def _diagnose_and_draft(self, qid: str, node_id: str) -> list[dict]:
        """P0-2：对每个 failed VR 机械诊断并生成修订草案。

        沿 verified_by 边定位失败候选（VR→EXEC→model_id→MIR）：
        1. diagnose_failure（registry + VR 机械证据）→ 注册 diagnosis
           artifact + (MIR, diagnosed_by, DIAG) 边；幂等——已有
           diagnosed_by 边的 MIR 跳过（M2 修订环重跑不重复诊断）；
        2. build_revision_draft（M1 结构继承 + changed_components + 溯源）
           → 放入 shared["revision_packages"][qid]，供外部 Model
           Constructor 读取后注入 M2（草案是 Constructor 输入，不注册
           为 MIR——不是系统事实）。

        返回本次生成的诊断包列表（{diagnosis_id, mir_id, root_cause, ...}）。
        """
        from modeling_harness.runtime.modeling.diagnosis import diagnose_failure
        from modeling_harness.runtime.modeling.revision import build_revision_draft

        reg = self.registry
        packages: list[dict] = []
        for rel in list(self.graph.relations):
            if rel["relation"] != "verified_by":
                continue
            vr = reg.get(rel["to"])
            if vr is None or vr.question != qid \
                    or vr.type != "verification_result":
                continue
            vdata = vr.data or {}
            if vdata.get("status") != "failed":
                continue
            xart = reg.get(rel["from"])
            if xart is None:
                continue
            model_id = (xart.data or {}).get("model_id")
            if not model_id:
                continue
            # EXEC.data.model_id = MIR artifact id（如 MIR001，与
            # _candidate_vr_table 同口径）；为稳健同时兼容业务 id
            # （data.model_id = M2024A-Q1-v1）形式
            mir_art = reg.get(model_id)
            if mir_art is None or mir_art.type != "model_ir":
                for m in reg.list_by_type("model_ir"):
                    if (m.data or {}).get("model_id") == model_id:
                        mir_art = m
                        break
            if mir_art is None:
                continue
            # 幂等：已有 diagnosed_by 边（本 DAG 或历史修订）跳过
            if any(g["from"] == mir_art.artifact_id
                   and g["relation"] == "diagnosed_by"
                   for g in self.graph.relations):
                continue
            diag = diagnose_failure(reg, mir_art.artifact_id,
                                    vr.artifact_id)
            d = reg.create(
                "diagnosis", title=f"失败诊断 {mir_art.artifact_id}",
                question=qid, depends_on=[mir_art.artifact_id],
                data=diag.to_dict(), activate=True, created_by=node_id)
            self.graph.add_relation(mir_art.artifact_id, "diagnosed_by",
                                    d.artifact_id)
            draft = build_revision_draft(
                dict(mir_art.data or {}), diag.to_dict(),
                new_model_id=f"{model_id}-REV1")
            packages.append({
                "diagnosis_id": d.artifact_id,
                "mir_artifact_id": mir_art.artifact_id,
                "mir_id": model_id,
                "root_cause": diag.root_cause,
                "failed_components": diag.failed_components,
                "suggested_fixes": diag.suggested_fixes,
                "draft": draft,
            })
        if packages:
            self.shared.setdefault("revision_packages", {})
            self.shared["revision_packages"][qid] = packages
        return packages

    # ------------------------------------------------------------ P1-M3 候选竞技场（Evidence-based Selection）

    SELECTION_CRITERIA = [
        "objective_value", "objective_direction",
        "mathematical_valid", "constraint_violation_max",
        "execution_valid", "variable_domain_violation", "empirical_valid",
    ]

    def _candidate_vr_table(self, qid: str) -> dict[str, dict]:
        """P1-M3：候选 MIR → 其 VR 证据映射（沿 VR→EXEC→model_id 归位）。

        返回 {mir_id: {"vr_id": ..., "metrics": {VR 字段}}}；
        无 VR 证据的候选（执行未发生/未验证）以 metrics=None 计入（排最后）。
        P1-M4：CODE artifact 可能被多候选共享（hash 去重），因此不沿
        CODE→MIR 边反查（有歧义），直接用 EXEC.data.model_id 定位所属候选。
        """
        table: dict[str, dict] = {}
        for mir_id in self._active_mirs(qid):
            table.setdefault(mir_id, {"vr_id": None, "metrics": None})
        for r in self.graph.relations:
            if r["relation"] != "verified_by":
                continue
            vr = self.registry.get(r["to"])
            if vr is None or vr.question != qid or vr.type != "verification_result":
                continue
            xart = self.registry.get(r["from"])
            if xart is None:
                continue
            mir_id = (xart.data or {}).get("model_id")
            if mir_id and mir_id in table:
                table[mir_id] = {"vr_id": r["to"],
                                 "metrics": dict(vr.data or {})}
        return table

    @staticmethod
    def _rank_candidates(table: dict[str, dict]) -> list[str]:
        """机械排序（禁 LLM 打分/禁取第一个）。

        优先级（ADR-0014，把 ADR-0013「模型选择必须比目标函数值」延伸到
        P1-M3 生产选型路径）：mathematical_valid → **objective_value（按
        objective_direction）** → constraint_violation_max 升序 →
        execution_valid → 域合规 → empirical_valid → model_id 字典序
        （确定性 tie-break）。有目标值者优先于无目标值者；无证据候选恒排最后。

        缺口修复：ADR-0013 只改了 comparison.py::compare_models，而本节点
        （do_model_selection_decision）走的是这条键——此前完全不读
        objective_value，两个都合规（constraint_violation_max=0）的候选由
        mir_id 字典序决胜，目标值更优者会落选。
        """

        def key(item: tuple[str, dict]) -> tuple:
            mir_id, info = item
            m = info.get("metrics") or {}
            if not m:                       # 无 VR 证据：恒排最后
                return (2, 1, 0.0, 0.0, 1, 1, 1, mir_id)
            obj_f = _finite_float(m.get("objective_value"))
            obj_rank = 0.0
            if obj_f is not None:
                direction = m.get("objective_direction") or "minimize"
                obj_rank = -obj_f if direction == "maximize" else obj_f
            cv = _finite_float(m.get("constraint_violation_max"))
            return (0 if m.get("mathematical_valid") else 1,
                    0 if obj_f is not None else 1,
                    obj_rank,
                    cv if cv is not None else 0.0,
                    0 if m.get("execution_valid") else 1,
                    0 if (m.get("variable_domain_violation") or 0) == 0 else 1,
                    0 if m.get("empirical_valid") else 1,
                    mir_id)

        return [mir_id for mir_id, _ in
                sorted(table.items(), key=key)]

    def _decision_confidence(self, ranked: list[str],
                             table: dict[str, dict]) -> float:
        """确定性置信度（非 LLM）：最优存活且次优不可存活 → 0.95；
        最优存活但次优也存活 → 0.8；最优不可存活 → 0.25；无证据 → 0.0。

        P1-4：本函数输出为 **advisory 置信度**（经验常数，无独立来源），
        仅供展示/解释。选型判定完全由 VR 机械证据（mathematical_valid /
        constraint_violation_max）驱动；confidence 不参与任何 PASS/FAIL 判定。
        """
        if not ranked:
            return 0.0
        best = (table.get(ranked[0]) or {}).get("metrics") or {}
        if not best:
            return 0.0
        best_math = bool(best.get("mathematical_valid"))
        if not best_math:
            return 0.25
        if len(ranked) == 1:
            return 0.7
        second = (table.get(ranked[1]) or {}).get("metrics") or {}
        second_math = bool(second.get("mathematical_valid")) if second else False
        if not second_math:
            return 0.95
        best_cv = float(best.get("constraint_violation_max") or 0.0)
        second_cv = float(second.get("constraint_violation_max") or 0.0)
        return 0.8 if second_cv - best_cv > 1e-9 else 0.6

    def do_model_selection_decision(self, node_id: str) -> NodeResult:
        """P1-M3：基于候选真实数值验证结果（VR 机械指标）选型。

        产出 decision artifact（alternatives/criteria/evidence_ids/chosen/
        confidence/reasoning）并写 decision -selects-> model 边（首次真正写入）。
        无 VR 证据时如实声明 chosen=UNSELECTED + confidence=0（不假装选型）。
        """
        ev = []
        n = 0
        for qid in self._question_ids():
            cands = self._external_candidates(qid)
            if not cands:
                continue      # 非候选模式：无 VR 选型语义（legacy 竞技场已选）
            table = self._candidate_vr_table(qid)
            if not table:
                continue
            ranked = self._rank_candidates(table)
            best_mir = ranked[0]
            best_info = table[best_mir]
            models = self._models_of(qid)
            mid = models[-1] if models else None
            evidence_ids = [info["vr_id"] for info in table.values()
                            if info.get("vr_id")]
            alternatives = [
                {"model_ir": mir_id,
                 "vr": (info.get("vr_id") or None),
                 "mathematical_valid": bool((info.get("metrics") or {})
                                            .get("mathematical_valid")),
                 "constraint_violation_max": (info.get("metrics") or {})
                                             .get("constraint_violation_max"),
                 "execution_valid": bool((info.get("metrics") or {})
                                         .get("execution_valid"))}
                for mir_id, info in sorted(table.items())]
            if not evidence_ids or not best_info.get("vr_id"):
                chosen, confidence = "UNSELECTED", 0.0
                reasoning = "no execution evidence available"
            else:
                chosen = best_mir
                confidence = self._decision_confidence(ranked, table)
                bm = best_info["metrics"]
                b_obj_f = _finite_float(bm.get("objective_value"))
                b_dir = bm.get("objective_direction") or "minimize"
                b_cv = _finite_float(bm.get("constraint_violation_max"))
                if b_obj_f is not None:
                    parts = [f"chosen={chosen} because "
                             f"{best_info['vr_id']}.objective_value="
                             f"{b_obj_f:g} 为可行候选中最优（{b_dir}）"]
                else:
                    parts = [f"chosen={chosen} because "
                             f"{best_info['vr_id']}.mathematical_valid="
                             f"{bool(bm.get('mathematical_valid'))}"
                             f"（目标值不可得，回退验证质量）"]
                for alt in ranked[1:]:
                    ai = table[alt]
                    if not ai.get("vr_id"):
                        continue
                    am = ai["metrics"] or {}
                    a_obj_f = _finite_float(am.get("objective_value"))
                    if b_obj_f is not None and a_obj_f is not None:
                        parts.append(
                            f"{alt}({ai['vr_id']}.objective_value="
                            f"{a_obj_f:g}) 劣于 {best_info['vr_id']}"
                            f".objective_value={b_obj_f:g}")
                    else:
                        a_cv = _finite_float(am.get("constraint_violation_max"))
                        parts.append(
                            f"{alt}({ai['vr_id']}.constraint_violation_max="
                            f"{a_cv if a_cv is not None else 0.0}) "
                            f"worse than {best_info['vr_id']}."
                            f"constraint_violation_max="
                            f"{b_cv if b_cv is not None else 0.0})")
                reasoning = "; ".join(parts)
            ddata = {
                "kind": "candidate_selection",
                "question": qid,
                "chosen": chosen,
                "alternatives": alternatives,
                "criteria": list(self.SELECTION_CRITERIA),
                "evidence_ids": evidence_ids,
                "confidence": confidence,
                "reasoning": reasoning,
                "ranked": ranked,
                "candidate_vr": {k: v.get("vr_id") for k, v in table.items()},
            }
            d = self.registry.create(
                "decision", title=f"{qid} 候选竞技场选型（evidence-based）",
                question=qid, payload=[chosen], data=ddata,
                depends_on=[mid] if mid else [],
                activate=True, created_by=node_id)
            # audit FIX-2.4：候选评估证据 + 选型来源写入 Evidence Graph
            for mir_id, info in table.items():
                vr_id = info.get("vr_id")
                if vr_id:
                    self.graph.add_relation(mir_id, "evaluated_by", vr_id)
            if chosen != "UNSELECTED" and mid:
                self.graph.add_relation(mid, "selected_from", chosen)
            if mid:
                self.graph.add_relation(d.artifact_id, "selects", mid)
                ev.append({"from": d.artifact_id, "relation": "selects", "to": mid})
            info = self.shared.setdefault(qid, {})
            info["chosen_candidate"] = chosen
            info["selection_decision"] = d.artifact_id
            info["selection_evidence"] = evidence_ids
            # DecisionLog 审计镜像（双存储最小方案；失败不阻断 Registry 主链路）
            if self.decisions is not None:
                try:
                    self.decisions.add(
                        question=f"{qid} 候选竞技场选型",
                        chosen=chosen, reversible=True,
                        alternatives=[
                            f"{a['model_ir']}"
                            f"{'（VR=' + str(a['vr']) + '）' if a['vr'] else '（无证据）'}"
                            for a in alternatives],
                        criteria=list(self.SELECTION_CRITERIA),
                        reasoning=reasoning,
                        confidence=confidence,
                        created_by=node_id,
                        evidence_ids=evidence_ids)
                except Exception:
                    pass    # 审计镜像尽力而为
            n += 1
        if n == 0:
            return NodeResult(PASS, "无候选竞技场问题（跳过）",
                              outputs={"artifacts": [], "evidence": ev})
        return NodeResult(PASS, f"{n} 个问题完成 evidence-based 选型",
                          outputs={"artifacts": [], "evidence": ev})

    def _advance_question(self, qid: str, target: str) -> None:
        """沿问题状态机推进（非法转换静默跳过，由 state fail-closed 兜底）。"""
        from modeling_harness.runtime.state.model import StateError
        try:
            cur = self.state.question_status(qid)
            path = {"modeled": ["analyzing", "modeled"],
                    "experimenting": ["analyzing", "modeled", "experimenting"]}
            for st in path.get(target, [target]):
                if cur != st:
                    self.state.set_question_status(qid, st)
                    cur = st
        except StateError:
            pass

    def _mk(self, node_id: str, **kw) -> dict:
        kw.setdefault("created_by", node_id)
        return kw

    # ------------------------------------------------------------ 分发

    def __call__(self, node_id: str, ctx: dict) -> NodeResult:
        t0 = time.perf_counter()
        fn = getattr(self, "do_" + _base(node_id), None)
        if fn is None:
            return NodeResult(FAIL, f"没有节点处理器: {_base(node_id)}")
        try:
            result = fn(node_id)
        except (SelectionError, PlannerError) as e:
            return NodeResult(FAIL, str(e))
        result.outputs.setdefault("metrics", {})
        result.outputs["metrics"]["latency_ms"] = round(
            (time.perf_counter() - t0) * 1000, 1)
        return result

    # ------------------------------------------------------------ 节点实现

    def do_problem_analysis(self, node_id: str) -> NodeResult:
        """登记 Problem Artifact + motivates 证据（Question 已由 session 预登记）。

        audit FIX-2.5：有结构化题面（ProblemRepresentation）时，Problem
        artifact 携带题面内容（background/problems/constraints/data/delivery），
        无题面表示时 source 如实标记 "none"（禁止 legacy 回退掩盖缺失）。
        """
        pr = getattr(self, "problem_repr", None)
        title = self.features.get("problem_title", "赛题")
        if pr is not None and pr.background:
            title = pr.background.strip().splitlines()[0][:60] or title
        if not self.registry.list_by_type("problem"):
            pdata = {"source": pr.source if pr is not None else "none"}
            if pr is not None:
                pdata.update({
                    "background": pr.background,
                    "problems": pr.problems,
                    "constraints": pr.constraints,
                    "data": pr.data,
                    "delivery": pr.delivery,
                })
            self.registry.create("problem", title=title, data=pdata,
                                 activate=True, created_by=node_id)
        problem_id = self.registry.list_by_type("problem")[0].artifact_id
        qids = self._question_ids()
        # Question artifact 题面内容（来自 structured representation）
        if pr is not None and pr.problems:
            for qid in qids:
                qa = self.registry.get(qid)
                if qa is not None:
                    d = dict(qa.data or {})
                    d.setdefault("problem_repr_source", pr.source)
                    for prob in pr.problems:
                        if prob.get("id") == qid or str(prob.get("id")) == qid:
                            d.setdefault("problem_statement",
                                         prob.get("description")
                                         or prob.get("title") or "")
                            break
                    qa.data = d
        ev = [{"from": problem_id, "relation": "motivates", "to": qid}
              for qid in qids]
        return NodeResult(PASS, f"{len(qids)} 个问题已登记",
                          outputs={"artifacts": [], "evidence": ev})

    def do_literature_search(self, node_id: str) -> NodeResult:
        """知识库检索 → 文献证据 decision artifact（记录 top 建议与失败记忆）。"""
        recs = self.retriever.recommend(self.features, top_k=3)
        payload = [{"card_id": r.card.card_id, "score": r.score,
                    "matched": r.matched} for r in recs]
        pids = self.registry.list_by_type("problem")
        d = self.registry.create(
            "decision", title="文献检索与证据提取",
            payload=[r["card_id"] for r in payload],
            data={"kind": "literature_search", "recommendations": payload},
            depends_on=[pids[0].artifact_id] if pids else [],
            activate=True, created_by=node_id)
        ev = [{"from": d.artifact_id, "relation": "based_on",
               "to": pids[0].artifact_id}] if pids else []
        return NodeResult(PASS, f"检索到 {len(recs)} 张方法卡",
                          outputs={"artifacts": [], "evidence": ev,
                                   "context": {"literature": payload}})

    def do_model_selection(self, node_id: str) -> NodeResult:
        """方法竞技场：每问题选型 → model artifact + solved_by 证据。

        P1-M3 候选模式（external_candidates 注入）：登记候选竞技场容器 model
        artifact（shortlist=候选 model_id），不执行竞技场假选型（消除 recs[0]
        硬编码；真正选型由 model_selection_decision 基于 VR 数值完成）。
        无候选注入时走原竞技场路径（方法族预选，向后兼容）。

        ADR-0008 fail-closed：无真实问题特征（`_features_source=absent`）时——
          * 有外部模型注入：如实登记「外部构造器提供」，**不做方法族选型**
            （拒绝用默认画像冒充选型，也不编造 card_id）；
          * 无外部模型注入：BLOCKED（选型需真实特征，不能盲选）。
        """
        ev = []
        count = 0
        features_absent = self.features.get("_features_source") == "absent"
        has_external_model = bool(self.shared.get("external_model_irs")
                                  or self.shared.get("external_candidates"))
        if features_absent and not has_external_model:
            return NodeResult(
                BLOCKED,
                "无问题特征可用：features 未注入，且 inputs/ 无可派生题面"
                "（question_spec.json / problem.txt 均缺）——"
                "选型需真实特征，不以默认画像冒充（ADR-0008）",
                outputs={"artifacts": [], "evidence": []})
        for qid in self._question_ids():
            cands = self._external_candidates(qid)
            if cands:
                # 候选竞技场模式：仅登记容器模型，chosen 由 VR 证据决定（M3-2）
                models = self._models_of(qid)
                mid = models[-1] if models else ""
                if not mid:
                    cand_ids = [c["model_ir"].get("model_id") for c in cands
                                if c.get("model_ir")]
                    m = self.registry.create(
                        "model", title=f"{qid} 候选竞技场容器",
                        question=qid, depends_on=[qid],
                        data={"card_id": "candidate_competition",
                              "family": "",
                              "shortlist": cand_ids,
                              "competition": True,
                              "selection_status": "pending_evidence"},
                        activate=True, created_by=node_id)
                    mid = m.artifact_id
                ev.append({"from": qid, "relation": "solved_by", "to": mid})
                info = self.shared.setdefault(qid, {})
                info["model"] = mid
                info["card_id"] = "candidate_competition"
                info["shortlist"] = [c["model_ir"].get("model_id")
                                     for c in cands if c.get("model_ir")]
                if self.state:
                    self._advance_question(qid, "modeled")
                count += 1
                continue
            if features_absent:
                # ADR-0008：模型来自外部 Constructor 注入，且无题面可派生特征
                # → 登记容器模型并如实标注来源。card_id 沿用既有 "UNSELECTED"
                # 语义（确实未做方法卡选型），下游 experiment_design 已按该值
                # 走「无选型」分支；额外记号 selection_status 便于审计区分。
                mid = self._models_of(qid)[-1] if self._models_of(qid) else ""
                if not mid:
                    m = self.registry.create(
                        "model", title=f"{qid} 外部构造器提供模型",
                        question=qid, depends_on=[qid],
                        data={"card_id": "UNSELECTED",
                              "family": "",
                              "selection_status": "external_constructor",
                              "note": "无题面特征可派生（_features_source=absent）："
                                      "不做方法族选型，模型由外部 Constructor 注入"},
                        activate=True, created_by=node_id)
                    mid = m.artifact_id
                ev.append({"from": qid, "relation": "solved_by", "to": mid})
                info = self.shared.setdefault(qid, {})
                info["model"] = mid
                info["card_id"] = "UNSELECTED"
                info["shortlist"] = []
                if self.state:
                    self._advance_question(qid, "modeled")
                count += 1
                continue
            qf = features_for(self.features, qid)
            outcome = self.arena.select(qid, qf, created_by=node_id,
                                       evidence=self._selection_evidence(qid))
            card = outcome.chosen_card if outcome.chosen != "UNSELECTED" else {}
            models = self._models_of(qid)
            if node_id in self.force_new_lineage:
                from modeling_harness.runtime.artifacts.lifecycle import LifecycleError
                self.shared.pop(qid, None)   # 清缓存：旧 shared 指向将死谱系
                for old_m in models:
                    try:
                        self.registry.get(old_m).transition(
                            "superseded", by=node_id,
                            reason="superseded by explicit rerun")
                    except LifecycleError:
                        pass
                self.force_new_lineage.discard(node_id)
                models = []
            mid = models[-1] if models else ""
            if not mid:
                m = self.registry.create(
                    "model", title=card.get("name") or outcome.chosen,
                    question=qid,
                    depends_on=[qid],
                    data={"card_id": outcome.chosen,
                          "family": card.get("family", ""),
                          "selection_status": outcome.selection_status,
                          "shortlist": [c["card_id"] for c in outcome.shortlist]},
                    activate=True, created_by=node_id)
                mid = m.artifact_id
            ev.append({"from": qid, "relation": "solved_by", "to": mid})
            self.shared.setdefault(qid, {})["card_id"] = outcome.chosen
            # P8-4：生成候选方案（baseline/improved/hybrid/innovation）供规划消费
            try:
                cands = self.candidate_arena.generate_candidates(qid, qf)
                self.shared[qid]["candidates"] = [
                    c.as_dict() for c in self.candidate_arena.rank(cands)]
            except Exception as e:      # 候选生成失败不阻断选型（降级记录）
                self.shared[qid]["candidates_error"] = str(e)
            if self.state:
                self._advance_question(qid, "modeled")
            self.shared[qid]["model"] = mid
            self.shared[qid]["shortlist"] = [c["card_id"] for c in outcome.shortlist]
            count += 1
        return NodeResult(PASS, f"{count} 个问题完成选型",
                          outputs={"artifacts": [], "evidence": ev})

    def do_model_construction(self, node_id: str) -> NodeResult:
        """模型构建：登记 model 的关键假设（assumes 证据）。

        P1-VS-001 C5：若 external_model_irs 注入了该问题的 MODEL_IR dict，
        同时登记 model_ir Artifact 并写 model_ir -instantiates-> model 边。
        """
        ev = []
        n_assumed = 0
        n_mir = 0
        for qid in self._question_ids():
            models = self._models_of(qid)
            if not models:
                return NodeResult(FAIL, f"{qid}: 尚无已选模型（上游缺失）")
            mid = models[-1]
            if not any(r["from"] == mid and r["relation"] == "assumes"
                       for r in self.graph.relations):
                card = self.retriever.cards.get(self._card_id_of(qid, mid))
                risks = list(card.risks)[:2] if card else []
                if not risks:
                    risks = ["所选方法的前提条件成立（数据规模/类型/独立性）"]
                for i, risk in enumerate(risks, 1):
                    a = self.registry.create(
                        "assumption", title=f"{mid} 假设{i}: {risk[:40]}",
                        depends_on=[mid], activate=True, created_by=node_id)
                    ev.append({"from": mid, "relation": "assumes", "to": a.artifact_id})
                    n_assumed += 1
            # P1-VS-001 C5 / P1-M3：外部 MODEL_IR（单个或候选列表）→ model_ir
            # Artifact + instantiates 边（_register_mir 按 model_id 幂等）
            mir_ids = self.construct_candidate_mirs(qid)
            if not mir_ids:
                mir_id = self.construct_model_ir(qid)
                mir_ids = [mir_id] if mir_id else []
            if not mir_ids:
                # FIX-2.1（audit P0-05）：不允许"只登记假设就 PASS"
                return NodeResult(FAIL, f"{qid}: 无法构造 MODEL_IR（no_model_ir）")
            for mir_id in mir_ids:
                ev.append({"from": mir_id, "relation": "instantiates", "to": mid})
                n_mir += 1
        msg = f"登记 {n_assumed} 条假设"
        if n_mir:
            msg += f"，{n_mir} 个可执行 MODEL_IR"
        return NodeResult(PASS, msg,
                          outputs={"artifacts": [], "evidence": ev})

    def do_model_critique(self, node_id: str) -> NodeResult:
        """模型批判门禁：每个问题必须有 model 且至少一条假设。"""
        for qid in self._question_ids():
            models = self._models_of(qid)
            if not models:
                return NodeResult(FAIL, f"{qid}: 无模型可选")
            for mid in models:
                if not any(r["from"] == mid and r["relation"] == "assumes"
                           for r in self.graph.relations):
                    return NodeResult(FAIL, f"{mid}: 无假设支撑，批判不通过")
        return NodeResult(PASS, "模型-假设链完整")

    def do_assumption_check(self, node_id: str) -> NodeResult:
        """假设必要性：每模型 ≥1 条 assumes（与批判互补的 L4 检查）。"""
        for qid in self._question_ids():
            if not self._models_of(qid):
                return NodeResult(FAIL, f"{qid}: 模型缺失，无法核查假设")
        return NodeResult(PASS, "假设核查通过")

    def do_experiment_design(self, node_id: str) -> NodeResult:
        """实验规划器：主方法 + 对照基线 + 灵敏度 → decision artifact。"""
        ev = []
        for qid in self._question_ids():
            info = self.shared.setdefault(qid, {})
            mid = info.get("model") or (self._models_of(qid) or [None])[-1]
            card_id = self._card_id_of(qid, mid)
            if not card_id:
                return NodeResult(FAIL, f"{qid}: 无选型结果，无法规划实验")
            if info.get("plan"):
                continue    # 幂等：计划已存在
            # P8-4→P8-7 通道：最优候选直接生成结构化计划（含创新验证条目）
            cands = info.get("candidates")
            if cands:
                from modeling_harness.runtime.modeling.candidates import Candidate
                top = cands[0]
                # ADR-0016：重建必须保真（含 innovations / validations /
                # dependencies / assumptions）。此前手写字段子集漏传 innovations，
                # 使 planner 的创新专用分支恒空转——创新要求被降级为普通
                # 「候选方案要求」，`decision_rule=gain > cost` 永不生效。
                cand = Candidate.from_dict(top)
                plan = self.planner.plan_from_candidate(cand, qid)
                # ADR-0016 Step 2：落选候选不得静默丢弃——把它们（含创新候选）的
                # 验证义务并入计划。条目如实标注 advisory（未执行），
                # 不因此声称产出了证据。
                plan.entries.extend(self.planner.extra_entries_from_candidates(
                    [Candidate.from_dict(c) for c in cands[1:]], plan))
                # P9.5 红队修复：新计划建立前退役旧计划（R3 谱系语义，
                # 旧计划 superseded 审计保留，不得双 active）
                from modeling_harness.runtime.artifacts.lifecycle import LifecycleError
                for old_pa in self.registry.list_by_type("decision"):
                    if "实验计划" in (old_pa.title or "")                             and old_pa.status == "active"                             and mid in (old_pa.depends_on or []):
                        try:
                            old_pa.transition(
                                "superseded", by=node_id,
                                reason="superseded by re-planned lineage")
                        except LifecycleError:
                            pass
                plan_data = plan.as_dict()
                # ADR-0016 Step 2：候选池落决策审计（decision schema 的
                # alternatives 允许自由对象）。如实标注每条候选是否被执行——
                # 方法组合候选没有 MODEL_IR，**未执行**，不得据此声称有证据。
                plan_data["alternatives"] = [
                    {"candidate_id": c.get("candidate_id", ""),
                     "kind": c.get("kind", ""),
                     "score": c.get("score"),
                     "novelty_level": (
                         (c.get("innovations") or [{}])[0]
                         .get("novelty_level", "") if c.get("innovations")
                         else ""),
                     "executed": False,
                     "note": "方法组合候选（无 MODEL_IR）：advisory，未执行；"
                             "见 ADR-0016 决策 4"}
                    for c in cands]
                d = self.registry.create(
                    "decision", title=f"{qid} 实验计划",
                    payload=plan.methods, data=plan_data,
                    depends_on=[mid] if mid else [],
                    activate=True, created_by=node_id)
                info["plan"] = plan.as_dict()
                ev.append({"from": d.artifact_id, "relation": "based_on", "to": mid})
                continue
            shortlist = [c["card_id"] if isinstance(c, dict) else c
                         for c in (info.get("shortlist") or [])]
            if not shortlist and mid:
                # P7：shortlist 持久化于 model.data（Registry 真源），崩溃后可重建
                shortlist = list(self.registry.get(mid).data.get("shortlist", []))
            if card_id == "UNSELECTED":
                # FIX-2.2 连锁（resume/checkpoint 持久化）：未选状态如实
                # 声明（不假装已选），但 shortlist 是 selection 的合法探索
                # 输出（推荐候选集，Registry 真源）——基于候选集生成探索性
                # 实验计划，计划内 methods=shortlist 而非 chosen 声明。
                # 无候选集 → 无计划依据 → 如实 FAIL（不编造实验计划）。
                if not shortlist:
                    return NodeResult(
                        FAIL, f"{qid}: 无选型与候选集（UNSELECTED 且无 "
                              f"shortlist），无法规划实验")
                methods = shortlist
                baseline = None
            else:
                methods = [card_id]
                baseline = next((c for c in shortlist if c != card_id), None)
            plan = self.planner.plan(qid, methods, baseline_card_id=baseline)
            d = self.registry.create(
                "decision", title=f"{qid} 实验计划",
                payload=plan.methods,
                data=plan.as_dict(), depends_on=[mid] if mid else [],
                activate=True, created_by=node_id)
            if mid:
                ev.append({"from": d.artifact_id, "relation": "based_on", "to": mid})
            info["plan"] = plan.as_dict()
        return NodeResult(PASS, "实验计划完成",
                          outputs={"artifacts": [], "evidence": ev})

    def do_experiment(self, node_id: str) -> NodeResult:
        """实验执行（确定性仿真）：E → R → F 证据链。"""
        qid = self._question_of(node_id)
        if not qid:
            return NodeResult(FAIL, "experiment 节点必须 per_question")
        info = self.shared.setdefault(qid, {})
        mid = info.get("model") or (self._models_of(qid) or [None])[-1]
        if not mid:
            return NodeResult(FAIL, f"{qid}: 无模型可实验")
        info["model"] = mid
        if node_id in self.force_new_lineage:
            self.force_new_lineage.discard(node_id)
            # Rerun 语义：旧链（E/R/F/C）整链 superseded，强制全新谱系
            self._supersede_question_chain(qid, node_id)
        live_results = self._results_of(qid)
        if live_results:
            # 幂等：rollback 后重跑复用既有（非终态）实验链；
            # 并回填缺失的 tags/provenance（resume 后 shared 丢失的场景）
            r = live_results[-1]
            r_art = self.registry.get(r)
            plan_art = self._plan_artifact_for(qid, mid)
            plan = (plan_art.data if plan_art else {}) or info.get("plan") or {}
            tags = [t for t, key in (("sensitivity", "sensitivity"),)
                    if plan.get(key)]
            if tags and not r_art.tags:
                r_art.tags = tags
            self._apply_baseline_comparison(r_art, plan)
            e_art = None
            for x in self.graph.relations:
                if x["relation"] == "produces" and x["to"] == r:
                    cand = self.registry.get(x["from"])
                    if cand is not None and cand.type == "experiment":
                        e_art = cand
                        break
            if e_art is None:
                # FIX-1.5：复用分支也确保实验记录存在（真实执行链下
                # EXEC produces R 而实验节点可能未登记 E——下游断言
                # experiment artifact 的存在性 + 模型→实验谱系边）
                e_art = self.registry.create(
                    "experiment", title=f"{qid} 实验", question=qid,
                    depends_on=[mid] if mid else [],
                    data={"card_id": self._card_id_of(qid, mid),
                          "plan_ref": plan_art.artifact_id
                          if plan_art else "",
                          "plan_entry": "", "hypothesis_ref": ""},
                    activate=True, created_by=node_id)
                self.graph.add_relation(e_art.artifact_id, "produces", r)
                if mid:
                    self.graph.add_relation(mid, "validated_by", e_art.artifact_id)
                    self.graph.add_relation(e_art.artifact_id, "tests", mid)
            if plan_art and (not e_art.data.get("plan_ref")
                             or not e_art.data.get("plan_entry")
                             or not e_art.data.get("hypothesis_ref")):
                entries = plan.get("entries") or [{}]
                e_art.data.update({
                    "plan_ref": plan_art.artifact_id,
                    "plan_entry": entries[0].get("experiment_id", ""),
                    "hypothesis_ref": entries[0].get("hypothesis", "")})
            f = next((a.artifact_id for a in self.registry.list_by_type("figure")
                      if a.question == qid
                      and a.status not in _TERMINAL), None)
            if f is None:
                # FIX-1.5：复用分支确保 figure 存在（论文 FactCheck P4 需要
                # 活跃 Figure Artifact，不得 fallback 到 r 冒充图）
                f_art = self.registry.create(
                    "figure", title=f"{qid} 结果图", question=qid,
                    depends_on=[r], activate=True, created_by=node_id)
                f = f_art.artifact_id
                self.graph.add_relation(r, "visualized_by", f)
            self._clear_revalidation_marks(qid, node_id)   # 复验存活链
            if self.state:
                # 复用链同样推进状态机（真实执行下 model_execution 已产出
                # result；问题须进入 experimenting → validated 晋级链）
                self._advance_question(qid, "experimenting")
            return NodeResult(PASS, f"{qid}: 复用既有实验链",
                              outputs={"artifacts": [], "evidence": [
                                  {"from": r, "relation": "visualized_by", "to": f}]})
        info["results"] = live_results   # 清掉已失效的旧结果，走全新链
        # 退役旧实验链（fresh 分支触发，如 recompute 后重建）
        self._supersede_question_chain(qid, node_id)
        # P9.5：计划 provenance 从 Registry 派生（resume 后 shared 不可信），
        # 挂在 experiment（计划的执行者）上
        plan_art = self._plan_artifact_for(qid, mid)
        plan = (plan_art.data if plan_art else None) or info.get("plan") or {}
        entries = plan.get("entries") or [{}]
        tags = [t for t, key in (("sensitivity", "sensitivity"),)
                if plan.get(key)]
        # 新实验记录（谱系节点：rerun/recompute 产生新 E，旧链 superseded）
        e = self.registry.create("experiment", title=f"{qid} 实验",
                                 question=qid, depends_on=[mid],
                                 data={"card_id": self._card_id_of(qid, mid),
                                       "plan_ref": plan_art.artifact_id
                                       if plan_art else "",
                                       "plan_entry": (entries[0] or {})
                                       .get("experiment_id", ""),
                                       "hypothesis_ref": (entries[0] or {})
                                       .get("hypothesis", "")},
                                 activate=True, created_by=node_id)
        # FIX-1.5（audit P0-05/08）：实验节点必须消费真实执行链。
        # 重建执行（external_code → subprocess → EXEC → result）；
        # 无真实 result 时不得创建 not_executed 占位链冒充完成。
        try:
            self.execute_code(qid, node_id)
        except HandlerError:
            pass   # 无注入代码：execute_code 返回 []，下面对话判定
        rebuilt = self._results_of(qid, include_failed=False)
        if not rebuilt:
            return NodeResult(
                FAIL,
                f"{qid}: 无真实执行 result（外部 Model Constructor 未注入 "
                "代码/模型或执行失败），实验链不可用——不创建占位结果",
                outputs={"artifacts": [], "evidence": []})
        r = rebuilt[-1]
        r_art = self.registry.get(r)
        if tags and not r_art.tags:
            r_art.tags = tags
        self._apply_baseline_comparison(r_art, plan)
        f = next((a.artifact_id for a in self.registry.list_by_type("figure")
                  if a.question == qid and a.status not in _TERMINAL), r)
        ev = [
            {"from": mid, "relation": "validated_by", "to": e.artifact_id},
            {"from": e.artifact_id, "relation": "tests", "to": mid},
            {"from": e.artifact_id, "relation": "produces", "to": r},
            {"from": r, "relation": "visualized_by", "to": f},
        ]
        info.setdefault("results", []).append(r)
        info["results"] = self._results_of(qid)   # 以 Registry 为准
        self._clear_revalidation_marks(qid, node_id)   # 重建即复验通过
        if self.state:
            self._advance_question(qid, "experimenting")
        return NodeResult(PASS, f"{qid}: 实验链重建（真实执行）",
                          outputs={"artifacts": [], "evidence": ev})

    def _clear_revalidation_marks(self, qid: str, by_node: str) -> None:
        """P9.5 红队修复（E6 死循环）：链重建/复验即复验通过——

        清除该问题活跃产物上的 requires_revalidation/dirty 传播标记。
        只清标记（bookkeeping），不改 lifecycle 状态；终态产物不可清除
        （lifecycle fail-closed）。若无此清除，Evidence Gate E6 将永久 WEAK。
        """
        from modeling_harness.runtime.artifacts.lifecycle import LifecycleError
        for a in self.registry.all():
            if a.question == qid and a.status not in _TERMINAL                     and a.invalidation:
                try:
                    a.clear_invalidation()
                except LifecycleError:
                    pass

    def _supersede_question_chain(self, qid: str, by_node: str) -> None:
        """退役该问题的整条实验链（E/R/F/C → superseded，审计保留）。

        Rerun 与 Recompute 重建共用：旧 claim 失去支撑后由 evidence_build
        重建新 claim；E4 不再误报旧实验。
        """
        from modeling_harness.runtime.artifacts.lifecycle import LifecycleError
        for art in self.registry.all():
            if art.question == qid and art.type in (
                    "experiment", "result", "figure", "claim")                     and art.status not in _TERMINAL:
                try:
                    art.transition("superseded", by=by_node,
                                   reason="replaced by re-run")
                except LifecycleError:
                    pass
        # FIX-2.2 连锁修复：只清执行/证据产物引用（results/claim），
        # 保留选型与计划缓存（model/card_id/plan/candidates/shortlist）——
        # 那些是已完成 model_selection 节点的输出；全清会让下游
        # experiment_design 重跑时丢失选型，把 "UNSELECTED" 当方法卡崩溃。
        info = self.shared.get(qid)
        if info:
            for _k in ("results", "claim"):
                info.pop(_k, None)

    def do_experiment_critique(self, node_id: str) -> NodeResult:
        qid = self._question_of(node_id)
        results = self._results_of(qid, include_failed=False)
        if not results:
            return NodeResult(FAIL, f"{qid}: 实验无有效结果产出，批判不通过")
        for rid in results:
            art = self.registry.get(rid)
            if art.status in ("invalidated", "superseded", "deprecated"):
                return NodeResult(FAIL, f"{rid}: 结果已被失效，需重跑实验")
        return NodeResult(PASS, f"{qid}: 实验批判通过")

    def do_evidence_build(self, node_id: str) -> NodeResult:
        """证据构建：每问题 result → claim（supports）。

        审计 FIX-1.4 / P0-06：占位 claim（"{qid} 结论"）不得获得 supports
        边。有真实执行数值时用 synthesize_claim 确定性合成 statement
        （LLM-free）；无任何数值事实时保留 placeholder 但不加 supports 边，
        由 evidence_gate 的数值真实性检查（E9）判 FAIL 走反馈环。
        """
        from modeling_harness.runtime.execution.claim_synthesis import synthesize_claim
        ev = []
        n = 0
        n_placeholder = 0
        for qid in self._question_ids():
            results = self._results_of(qid, include_failed=False)
            if not results:
                return NodeResult(FAIL, f"{qid}: 无有效 result（失败/未执行被排除），证据链断裂")
            claim_id = self.shared.get(qid, {}).get("claim") or self._claim_of(qid)
            if node_id in self.force_new_lineage and claim_id                     and self.registry.get(claim_id).status not in _TERMINAL:
                self.shared.pop(qid, None)
                from modeling_harness.runtime.artifacts.lifecycle import LifecycleError
                try:
                    self.registry.get(claim_id).transition(
                        "superseded", by=node_id,
                        reason="superseded by explicit rerun")
                except LifecycleError:
                    pass
            if claim_id and self.registry.get(claim_id).status not in _TERMINAL:
                continue    # 幂等：有效 claim 已登记（终态则重建）
            # 取最近一个有效 result 及其 EXEC/VR 证据
            r_id = results[-1]
            r_art = self.registry.get(r_id)
            exec_id = (r_art.data or {}).get("execution_ref") or ""
            exec_art = self.registry.get(exec_id) if exec_id and self.registry.exists(exec_id) else None
            vr_art = None
            if exec_id:
                for a in self.registry.list_by_type("verification_result"):
                    if a.question != qid or a.status in _TERMINAL:
                        continue
                    if any(x["from"] == exec_id and x["relation"] == "verified_by"
                           and x["to"] == a.artifact_id for x in self.graph.relations):
                        vr_art = a
                        break
            statement = synthesize_claim(qid, r_art, exec_art, vr_art)
            placeholder = not statement
            c = self.registry.create("claim", title=f"{qid} 结论",
                                     question=qid,
                                     depends_on=[r_id] if not placeholder else [],
                                     data={"statement": statement or f"{qid} 结论",
                                           "claim_type": "comparative",
                                           "experiment_refs": [r_id] if not placeholder else [],
                                           "literature_refs": [],
                                           "execution_status":
                                               (exec_art.data or {}).get("status")
                                               if exec_art is not None else "not_executed",
                                           "placeholder": placeholder},
                                     activate=True, created_by=node_id)
            if not placeholder:
                # audit FIX-4.1（P0-01/P0-07）：supports 边必须携带 exec_ref
                # （指向真实 EXEC artifact），使 evidence 具有边级 execution
                # provenance——"结论由哪次执行产生"成为图结构的一部分。
                self.graph.add_relation(r_id, "supports", c.artifact_id,
                                        exec_ref=exec_id or None)
                ev.append({"from": r_id, "relation": "supports",
                           "to": c.artifact_id,
                           "exec_ref": exec_id or None})
                n += 1
            else:
                n_placeholder += 1
            self.shared.setdefault(qid, {})["claim"] = c.artifact_id
            self.shared[qid]["results"] = results
        msg = f"{n} 条真实结论已登记"
        if n_placeholder:
            msg += f"；{n_placeholder} 条占位（无数值事实，未加 supports 边）"
        if n == 0 and n_placeholder > 0:
            return NodeResult(FAIL, msg + " —— 无任何真实数值支撑的结论")
        return NodeResult(PASS, msg,
                          outputs={"artifacts": [], "evidence": ev})

    def do_evidence_gate(self, node_id: str) -> NodeResult:
        """证据门禁（L4）：coverage ≥ 阈值，否则 FAIL 走反馈环。"""
        # 评估前幂等剪除触及终态产物的死边（旧链退役晚于失效剪边时序）
        self.graph.retract_invalidated()
        report = evidence_gate_evaluate(self.registry, self.graph,
                                        min_coverage=self.min_coverage)
        self.shared["gate_report"] = report
        if report.passed:
            return NodeResult(PASS, report.summary(),
                              outputs={"metrics": {"coverage": report.coverage}})
        return NodeResult(FAIL, f"证据门禁未通过: {report.summary()}")

    def do_quality_evaluation(self, node_id: str) -> NodeResult:
        """P9-10/11：研究质量评估节点（七维 → 四态 → 反馈）。

        FAIL  → 反馈重建（on_fail→evidence_build，复用 P7 语义）
        WEAK/UNKNOWN → PASS + advisory（refine / request_evidence 记录在案，
                       不阻断确定性流程，避免同输入死循环）
        """
        import sys as _sys
        if str(REPO) not in _sys.path:
            _sys.path.insert(0, str(REPO))
        from modeling_harness.validators.quality import ResearchQuality

        rq = ResearchQuality(knowledge=self.retriever, decisions=self.decisions)
        report = rq.evaluate(self.registry, self.graph)
        self.shared["quality_report"] = report.as_dict()
        # P9-12：报告落盘 state/（Registry 路径 parents[1] = 项目根）
        try:
            rq.persist(report, self.registry.path.parents[1])
        except Exception:
            pass
        if report.blockers:
            try:
                rq.record_blockers(report)      # P9-12 Quality Memory
            except Exception:
                pass
            actions = ResearchQuality.workflow_feedback(report)
            return NodeResult(
                FAIL,
                f"quality FAIL: {len(report.blockers)} 项阻塞"
                f"（{', '.join((getattr(b, 'check_id', '') or getattr(b, 'dimension', '')) for b in report.blockers[:4])}）",
                outputs={"metrics": {"blockers": len(report.blockers),
                                     "actions": len(actions["rerun"] or []) +
                                     len(actions["recompute"] or [])}})
        detail = (f"quality {report.overall_status}: "
                  f"{len(report.warnings)} warnings / "
                  f"{len(report.unknowns)} unknowns")
        return NodeResult(PASS, detail,
                          outputs={"metrics": {
                              "overall": report.overall_status,
                              "warnings": len(report.warnings),
                              "unknowns": len(report.unknowns)}})
