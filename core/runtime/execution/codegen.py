"""P0-E7 Code Generation 接入 — 外部 Agent 产出的 code 进入 harness 的登记/执行/校验闭环。

定位（用户裁决 + THREE_LAYER_ARCHITECTURE v3）：
    * 生成侧由外部 Agent（Doubao/GPT/人）承担：MODEL_IR + 题面 → code。
    * core 永久 LLM-free：本模块不生成代码，只负责**登记、执行、校验、归因**。
    * "生成的代码是否执行了 MODEL_IR 声明的模型" 由 fidelity.py 机械回答
      （第二扇门，L2 Fidelity）。

闭环（K002 一个 run 的 harness 侧）：
    code（外部产出）
      → register_code      CODE artifact（sha256 自动计算，solver 绑定）
      → execute_code       EXEC artifact（真实执行，status 只来自执行）
      → verify_fidelity    VR artifact + state/fidelity/<exec_id>.json
      → run_code_pipeline  汇总 {code_id, exec_id, vr_id, fidelity_*}
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from runtime.artifacts.registry import ArtifactNotFound, ArtifactRegistry
from runtime.execution.adapters import (
    ExecutionAdapter, ExecutionPlan, LocalPythonAdapter,
)
from runtime.graph.evidence_graph import EvidenceGraph


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_registry(project_dir: Path) -> ArtifactRegistry:
    """防御加载：registry.json 不存在时按空 registry 处理（冷启动项目）。"""
    reg = ArtifactRegistry(project_dir / "state" / "registry.json")
    if reg.path.exists():
        reg.load()
    return reg


# ---------------------------------------------------------------- 登记

def register_code(project_dir: str | Path, code: str, *,
                  language: str = "python",
                  framework: str | None = None,
                  model_id: str | None = None,
                  solver_id: str | None = None,
                  title: str | None = None,
                  created_by: str = "external_agent",
                  question: str | None = None) -> Any:
    """把外部 Agent 产出的 code 登记为 CODE 一等 artifact。

    data 契约：code / language / framework / model_id / solver_id / sha256。
    code 为空或 language 为空时抛 ValueError（不登记空壳）。
    """
    if not code or not code.strip():
        raise ValueError("code 为空：不登记空代码")
    if not language or not language.strip():
        raise ValueError("language 为空：必须声明实现语言")
    project_dir = Path(project_dir)
    reg = _load_registry(project_dir)
    art = reg.create(
        "code",
        title=title or f"代码实现 {model_id or solver_id or 'unnamed'}",
        question=question,
        data={"code": code, "language": language,
              "framework": framework, "model_id": model_id,
              "solver_id": solver_id,
              "sha256": sha256_text(code)},
        activate=True, created_by=created_by)
    reg.save()
    return art


# ---------------------------------------------------------------- 执行

def execute_code(project_dir: str | Path, code_artifact_id: str, *,
                 inputs: dict[str, Any] | None = None,
                 adapter: ExecutionAdapter | None = None,
                 timeout_seconds: int = 60,
                 result_id: str | None = None,
                 question: str | None = None,
                 created_by: str = "external_agent") -> Any:
    """从 CODE artifact 取代码真实执行，登记 EXEC 一等 artifact。

    - status 只来自真实执行（success/failed/timeout/invalid），无默认 success；
    - executed_by 边：result_id → execution_result（若指定旧 result）；
    - 返回 execution_result artifact。
    """
    project_dir = Path(project_dir)
    reg = _load_registry(project_dir)
    try:
        art = reg.get(code_artifact_id)
    except ArtifactNotFound:
        art = None
    if art is None or art.type != "code":
        raise ValueError(f"code artifact 不存在或类型错误: {code_artifact_id}")
    data = dict(art.data or {})
    code = data.get("code", "")
    if not code.strip():
        raise ValueError(f"code artifact {code_artifact_id} 无代码内容")

    plan = ExecutionPlan(
        model_id=data.get("model_id") or art.artifact_id,
        code=code, inputs=inputs or {}, timeout_seconds=timeout_seconds)
    adapter = adapter or LocalPythonAdapter()
    xr = adapter.execute(plan)

    g = EvidenceGraph(reg, project_dir / "state" / "evidence_graph.json")
    if g.path.exists():
        g.load()
    xart = reg.create(
        "execution_result",
        title=f"执行结果 {code_artifact_id}",
        question=question,
        data=xr.to_dict(),
        activate=True, created_by=created_by)
    if result_id:
        g.add_relation(result_id, "executed_by", xart.artifact_id)
    g.save()
    reg.save()
    return xart


# ---------------------------------------------------------------- 端到端

def run_code_pipeline(project_dir: str | Path, model_ir: dict, code: str, *,
                      language: str = "python",
                      framework: str | None = None,
                      model_id: str | None = None,
                      solver_id: str | None = None,
                      inputs: dict[str, Any] | None = None,
                      adapter: ExecutionAdapter | None = None,
                      experiment_idx: int = 0,
                      question: str | None = None) -> dict:
    """K002 一个 run 的 harness 侧完整闭环：
    register_code → execute_code → verify_fidelity。

    返回 {code_id, exec_id, exec_status, verification_id,
          fidelity_status, fidelity_score, fidelity_report}
    """
    from runtime.execution.fidelity import verify_fidelity

    project_dir = Path(project_dir)
    c = register_code(project_dir, code, language=language,
                      framework=framework, model_id=model_id,
                      solver_id=solver_id, question=question)
    x = execute_code(project_dir, c.artifact_id, inputs=inputs,
                     adapter=adapter, question=question)
    vr = verify_fidelity(project_dir, model_ir, x.artifact_id,
                         experiment_idx=experiment_idx)
    return {"code_id": c.artifact_id,
            "exec_id": x.artifact_id,
            "exec_status": (x.data or {}).get("status"),
            "verification_id": vr["verification_id"],
            "fidelity_status": vr["fidelity_status"],
            "fidelity_score": vr["fidelity_score"],
            "fidelity_report": vr["report_path"]}


def main(argv: list[str] | None = None) -> int:
    """CLI：python -m runtime.execution.codegen <项目> <model_ir.json> <code.py>

    注册 + 执行 + fidelity 校验一次完成；返回 JSON 汇总。
    """
    import argparse
    import json
    ap = argparse.ArgumentParser(
        description="P0-E7：外部 Agent code 进入 harness 的登记/执行/校验闭环")
    ap.add_argument("project")
    ap.add_argument("model_ir", help="MODEL_IR JSON 文件")
    ap.add_argument("code", help="Python 代码文件")
    args = ap.parse_args(argv)
    model_ir = json.loads(Path(args.model_ir).read_text(encoding="utf-8"))
    code = Path(args.code).read_text(encoding="utf-8")
    out = run_code_pipeline(args.project, model_ir, code,
                            model_id=model_ir.get("model_id"))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["fidelity_status"] == "aligned" else 1
