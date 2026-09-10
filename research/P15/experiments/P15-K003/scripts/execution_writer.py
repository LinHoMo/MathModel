# -*- coding: utf-8 -*-
"""P15-K003 execution_result 唯一写入者（audit FIX-4.2/4.3）。

治理目标：
- FIX-4.2：rebuild 可复现——给定 Artifact Registry + run 目录，重写全部
  per-run execution_result.json / fidelity_report.json，幂等且可回溯到
  本脚本 commit hash（脚本随实验冻结）。
- FIX-4.3：执行权限分离——execution_result 只能由本模块（execution
  substrate 侧）写入；generator/runner 不直接拼写 execution_result.json。
  本模块从 registry 读 EXEC 真实字段，registry 读不到 → status="invalid"
  壳守卫（绝不写默认数值冒充真实，延续 FIX-1.6 语义）。

用法:
    py -3.12 execution_writer.py rebuild <runs_root> <project_dir> [--registry <path>]
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_exec_data(project_dir: str | Path, exec_id: str) -> dict | None:
    """从 Artifact Registry 读 EXEC 真实字段（registry 是唯一真源）。"""
    from modeling_harness.runtime.artifacts.registry import ArtifactRegistry
    try:
        reg = ArtifactRegistry(Path(project_dir) / "state" / "registry.json")
        reg.load()
        art = reg.get(exec_id)
        if art is None:
            return None
        return dict(art.data or {})
    except Exception:
        return None


def build_execution_result(project_dir: str | Path, exec_id: str,
                           code_id: str, model_id: str,
                           utc: str | None = None) -> dict:
    """由 registry EXEC 构造 execution_result（真实字段，禁止默认值冒充）。"""
    utc = utc or utc_now_iso()
    exec_data = load_exec_data(project_dir, exec_id)
    if exec_data is None:
        return {
            "model_id": model_id,
            "status": "invalid",
            "error": f"registry 无 execution_result {exec_id}（无法生成真实产物）",
            "code_id": code_id,
            "exec_id": exec_id,
            "executed_at": utc,
        }
    return {
        "model_id": model_id,
        "status": exec_data.get("status", "unknown"),
        "returncode": exec_data.get("returncode"),
        "outputs": exec_data.get("outputs", {}),
        "stdout_tail": (exec_data.get("stdout") or "")[-2000:],
        "stderr": exec_data.get("stderr", ""),
        "duration_ms": exec_data.get("duration_ms"),
        "code_hash": exec_data.get("code_hash", ""),
        "environment_hash": exec_data.get("environment_hash", ""),
        "code_id": code_id,
        "exec_id": exec_id,
        "executed_at": utc,
    }


def write_run_execution(run_dir: str | Path, project_dir: str | Path,
                        exec_id: str, code_id: str, model_id: str,
                        fidelity: dict | None = None) -> dict:
    """写入单个 run 的 execution_result.json（+可选 fidelity_report.json）。

    本函数是 execution_result.json 的唯一写入路径。返回写入的 execution_result。
    """
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    result = build_execution_result(project_dir, exec_id, code_id, model_id)
    (run_dir / "execution_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if fidelity is not None:
        (run_dir / "fidelity_report.json").write_text(
            json.dumps(fidelity, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def rebuild_all(runs_root: str | Path, project_dir: str | Path,
                registry_path: str | Path | None = None,
                exec_id_key: str = "exec_id",
                code_id_key: str = "code_id",
                model_id_key: str = "model_id",
                dry_run: bool = False) -> dict:
    """FIX-4.2：从 registry 重建全部 run 的 execution_result.json（幂等）。

    每个 run 目录需含 manifest.json（exec_id/code_id/model_id 来源）。
    返回 {run: {"ok": bool, "status": str, "error": str | None}}。
    重建不修改 registry，只重写 run 目录下的产物文件。
    """
    runs_root = Path(runs_root)
    out: dict = {}
    if not runs_root.exists():
        return {"error": f"runs 目录不存在: {runs_root}"}
    for run_dir in sorted(runs_root.iterdir()):
        if not run_dir.is_dir():
            continue
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.exists():
            out[run_dir.name] = {"ok": False, "status": "skip",
                                 "error": "无 manifest.json"}
            continue
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            out[run_dir.name] = {"ok": False, "status": "error",
                                 "error": f"manifest 解析失败: {e}"}
            continue
        exec_id = (m.get("execution") or {}).get(exec_id_key) \
            or m.get(exec_id_key) or ""
        code_id = (m.get("execution") or {}).get(code_id_key) \
            or m.get(code_id_key) or ""
        model_id = (m.get("execution") or {}).get(model_id_key) \
            or m.get(model_id_key) or m.get("model_id") or ""
        if not exec_id:
            out[run_dir.name] = {"ok": False, "status": "skip",
                                 "error": "manifest 无 exec_id"}
            continue
        if dry_run:
            out[run_dir.name] = {"ok": True, "status": "dry_run",
                                 "exec_id": exec_id}
            continue
        try:
            res = write_run_execution(run_dir, project_dir, exec_id,
                                      code_id, model_id)
            out[run_dir.name] = {"ok": True, "status": res.get("status"),
                                 "exec_id": exec_id}
        except Exception as e:
            out[run_dir.name] = {"ok": False, "status": "error",
                                 "error": str(e)}
    return out


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "rebuild":
        runs_root, project_dir = sys.argv[2], sys.argv[3]
        report = rebuild_all(runs_root, project_dir)
        n_ok = sum(1 for v in report.values() if v.get("ok"))
        n_err = sum(1 for v in report.values() if not v.get("ok"))
        print(json.dumps({"total": len(report), "ok": n_ok,
                          "not_ok": n_err}, ensure_ascii=False, indent=2))
        for k, v in report.items():
            if not v.get("ok"):
                print(f"  {k}: {v.get('error')}", file=sys.stderr)
        return 0 if n_err == 0 else 1
    print("用法: py -3.12 execution_writer.py rebuild <runs_root> <project_dir>")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
