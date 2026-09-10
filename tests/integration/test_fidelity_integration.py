# -*- coding: utf-8 -*-
"""P0-1 验收：Fidelity Layer 接入生产 DAG（真实 subprocess + 结构映射）。

验收语义（ROADMAP P0-1）：
  * aligned  → model_execution PASS（真实 subprocess + fidelity 均过）
  * misaligned（声明变量/目标在输出中不可解析）→ model_execution FAIL，
    不得被 C8 数值验证"救回"
  * crash/timeout → 执行失败真实传播，不产生 fidelity 报告
  * fidelity 不注册 verified_by VR（避免 C8 _active_vr_of 幂等复用跳过真实
    数值验证）；C8 仍必须真实注册 VR

LLM-free：MODEL_IR 与 CODE 由测试注入（等同外部 Model Constructor 产物）。
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "tests" / "integration"))

from _real_session import MINIMAL_VALIDATION_SPEC, _minimal_mir  # noqa: E402

from runtime.execution.adapters import LocalPythonAdapter  # noqa: E402
from runtime.execution.session import RuntimeSession  # noqa: E402

LOOP_NODES = [
    "problem_analysis",
    "literature_search",
    "model_selection",
    "model_construction",
    "model_critique",
    "assumption_check",
    "code_generation",
    "model_execution",
    "model_validation",
]


def _make(tmp_path, mir, code, name="proj", questions=("Q001",)):
    s = RuntimeSession(
        Path(tmp_path) / name, list(questions), max_workers=1,
        execution_adapter=LocalPythonAdapter(),
        external_model_irs={"Q001": mir},
        external_code={"Q001": code},
        validation_specs={"Q001": dict(MINIMAL_VALIDATION_SPEC)})
    return s


def _step_to(session, node):
    """按 DAG 顺序步进到指定节点（含），返回 {node: result}。"""
    results = {}
    for nid in LOOP_NODES:
        results[nid] = session.engine.step(nid)
        if nid == node:
            break
    return results


def _continue_to(session, node):
    """从当前状态继续步进到指定节点（跳过已完成/阻塞节点）。"""
    results = {}
    for nid in LOOP_NODES:
        if nid in session.engine.completed \
                or nid in session.engine.blocked \
                or nid in session.engine.waiting:
            continue
        results[nid] = session.engine.step(nid)
        if nid == node:
            break
    return results


# 声明变量 y，代码输出 y（aligned）—— 与 _minimal_mir 的变量/参数匹配
OK_CODE = '''def solve(inputs):
    a = float(inputs["a"]); x = float(inputs["x"]); b = float(inputs["b"])
    return {"y": a * x + b, "ok": True, "a": a, "x": x, "b": b}


if __name__ == "__main__":
    import json
    data = json.load(open("input.json", encoding="utf-8"))
    print(json.dumps(solve(data), ensure_ascii=False))
'''


# 声明变量 y，但代码输出 total_cost（misaligned：声明的 y 在输出中不可解析）
MISALIGNED_CODE = '''def solve(inputs):
    a = float(inputs["a"]); x = float(inputs["x"]); b = float(inputs["b"])
    return {"total_cost": a * x + b, "ok": True}


if __name__ == "__main__":
    import json
    data = json.load(open("input.json", encoding="utf-8"))
    print(json.dumps(solve(data), ensure_ascii=False))
'''


CRASH_CODE = '''def solve(inputs):
    raise RuntimeError("boom")


if __name__ == "__main__":
    import json
    data = json.load(open("input.json", encoding="utf-8"))
    print(json.dumps(solve(data), ensure_ascii=False))
'''


class TestFidelityInDag:
    """fidelity 接入生产 DAG 的 5 条验收。"""

    def test_aligned_execution_passes(self, tmp_path):
        s = _make(tmp_path, _minimal_mir("Q001"), OK_CODE)
        results = _step_to(s, "model_execution")
        r = results["model_execution"]
        assert r.status == "pass", f"aligned 应 pass，实际 {r.status}: {r.reason}"
        # fidelity 报告落盘（state/fidelity/<exec_id>.json）
        execs = [a for a in s.registry.list_by_type("execution_result")]
        assert execs
        fid_dir = Path(tmp_path) / "proj" / "state" / "fidelity"
        rep = fid_dir / f"{execs[0].artifact_id}.json"
        assert rep.exists(), "fidelity 报告应落盘"
        rep_data = json.loads(rep.read_text(encoding="utf-8"))
        assert rep_data["fidelity_status"] == "aligned"
        assert rep_data["fidelity_score"] == 1.0

    def test_misaligned_execution_fails(self, tmp_path):
        s = _make(tmp_path, _minimal_mir("Q001"), MISALIGNED_CODE)
        results = _step_to(s, "model_execution")
        r = results["model_execution"]
        assert r.status == "fail", f"misaligned 应 fail，实际 {r.status}: {r.reason}"
        assert "fidelity misaligned" in r.reason
        # F1 变量可观测：y 在输出中不可解析
        execs = [a for a in s.registry.list_by_type("execution_result")]
        assert execs and execs[0].data["status"] == "success"
        # 失败传播：model_validation 因依赖未满足不执行（不救回）
        with pytest.raises(Exception):
            _step_to(s, "model_validation")

    def test_crash_execution_fails_without_fidelity(self, tmp_path):
        """执行失败真实传播（stderr 尾部），不进入 fidelity 判 aligned。"""
        s = _make(tmp_path, _minimal_mir("Q001"), CRASH_CODE)
        results = _step_to(s, "model_execution")
        r = results["model_execution"]
        assert r.status == "fail", f"crash 应 fail，实际 {r.status}: {r.reason}"
        # stderr 尾部真实包含 boom（reason 截断 300 字符，直接查 EXEC data）
        execs = [a for a in s.registry.list_by_type("execution_result")]
        assert execs
        stderr = "".join(execs[0].data.get("stderr") or "")
        assert "boom" in stderr
        fid_dir = Path(tmp_path) / "proj" / "state" / "fidelity"
        reps = list(fid_dir.glob("*.json")) if fid_dir.exists() else []
        assert reps == [], "失败执行不应产生 fidelity 报告"

    def test_fidelity_does_not_register_verified_by(self, tmp_path):
        """fidelity 不注册 verified_by VR：C8 数值验证不被幂等复用跳过。"""
        s = _make(tmp_path, _minimal_mir("Q001"), OK_CODE)
        _step_to(s, "model_execution")
        execs = [a for a in s.registry.list_by_type("execution_result")]
        assert execs
        fid_rels = [r for r in s.graph.relations
                    if r["from"] == execs[0].artifact_id
                    and r["relation"] == "verified_by"]
        assert fid_rels == [], "fidelity 不应注册 verified_by 边"
        # C8 数值验证仍真实执行并注册 VR
        results = _continue_to(s, "model_validation")
        vrs = [a for a in s.registry.list_by_type("verification_result")]
        assert vrs, "C8 数值验证应产生 VR"
        vr_rels = [r for r in s.graph.relations
                   if r["from"] == execs[0].artifact_id
                   and r["relation"] == "verified_by"]
        assert len(vr_rels) == 1, "C8 数值验证应注册 verified_by 边"
        assert results["model_validation"].status == "pass"

    def test_verify_fidelity_register_vr_switch(self, tmp_path):
        """verify_fidelity 的 register_vr 开关：False 不注册 VR，True 注册。"""
        from runtime.execution.fidelity import verify_fidelity

        s = _make(tmp_path, _minimal_mir("Q001"), OK_CODE)
        _step_to(s, "model_execution")
        execs = [a for a in s.registry.list_by_type("execution_result")]
        exec_id = execs[0].artifact_id
        proj = Path(tmp_path) / "proj"
        mir = _minimal_mir("Q001")
        # False：不注册 VR（verification_id == ""）
        out0 = verify_fidelity(proj, mir, exec_id, register_vr=False,
                               registry=s.registry)
        assert out0["verification_id"] == ""
        assert out0["fidelity_status"] == "aligned"
        # True：注册 VR（verification_id 非空）——validate_execution 从磁盘读
        # registry，先 checkpoint 落盘
        s.checkpoint()
        out1 = verify_fidelity(proj, mir, exec_id, register_vr=True,
                               registry=s.registry)
        assert out1["verification_id"].startswith("VR")
        # VR 注册在磁盘 registry（validate_execution 新建实例读写磁盘）
        from runtime.artifacts.registry import ArtifactRegistry
        disk = ArtifactRegistry(proj / "state" / "registry.json")
        disk.load()
        vr = disk.get(out1["verification_id"])
        assert vr is not None
        assert (vr.data or {}).get("provenance", {}).get("engine") == \
            "execution.fidelity"
