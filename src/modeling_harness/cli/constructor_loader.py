# -*- coding: utf-8 -*-
"""P0-1（终审 ROADMAP）：orchestrator 注入通道——从 <project>/constructor/
或 --constructor-dir 加载外部 Constructor 产物（MODEL_IR + code +
validation_specs），使默认 `orchestrator --execute` 能跑通完整链路。

目录约定（统一节点标准，P15-EXPERIMENT-CONTRACT-v2）：
  <dir>/model_ir.json        单题（Q001）或 {qid: MODEL_IR} 映射
  <dir>/code.py              单题代码（Q001）
  <dir>/code/<QID>.py        按题代码（优先于单文件）
  <dir>/specs.json           validation_specs（{qid: spec} 或单题）

缺省 constructor_dir = <project>/constructor/。目录不存在 → 返回空 bundle，
行为与现状一致（无 external 注入，model_construction 如实 BLOCKED）。
"""
import json
from pathlib import Path


def _load_json_text(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[V3][WARN] 读取 {path} 失败: {exc}", file=__import__("sys").stderr)
        return None


def load_constructor_bundle(project_dir: Path,
                            constructor_dir: Path | None = None) -> dict:
    """加载外部 Constructor 产物 bundle。

    返回 {"external_model_irs": {qid: dict},
          "external_code": {qid: str},
          "validation_specs": {qid: dict}}；
    无 constructor 目录 → 全部为空 dict（不改变既有行为）。
    """
    if constructor_dir is None:
        constructor_dir = project_dir / "constructor"
    cdir = Path(constructor_dir)
    bundle: dict = {"external_model_irs": {},
                    "external_code": {}, "validation_specs": {}}
    if not cdir.exists():
        return bundle

    # 1) MODEL_IR：单题对象或 {qid: MODEL_IR} 映射
    mir_path = cdir / "model_ir.json"
    if mir_path.exists():
        data = _load_json_text(mir_path)
        if isinstance(data, dict):
            if any(str(k).startswith("Q") for k in data) and \
                    all(isinstance(v, dict) for v in data.values()):
                bundle["external_model_irs"] = data
            else:
                bundle["external_model_irs"] = {"Q001": data}

    # 2) code：按题目录优先，其次单文件（Q001）
    code_dir = cdir / "code"
    if code_dir.exists():
        for cpy in sorted(code_dir.glob("Q*.py")):
            try:
                bundle["external_code"][cpy.stem] = \
                    cpy.read_text(encoding="utf-8")
            except OSError as exc:
                print(f"[V3][WARN] 读取 {cpy} 失败: {exc}",
                      file=__import__("sys").stderr)
    elif (cdir / "code.py").exists():
        try:
            bundle["external_code"]["Q001"] = \
                (cdir / "code.py").read_text(encoding="utf-8")
        except OSError as exc:
            print(f"[V3][WARN] 读取 code.py 失败: {exc}",
                  file=__import__("sys").stderr)

    # 3) validation_specs：{qid: spec} 或单题
    specs_path = cdir / "specs.json"
    if specs_path.exists():
        data = _load_json_text(specs_path)
        if isinstance(data, dict):
            if any(str(k).startswith("Q") for k in data) and \
                    all(isinstance(v, dict) for v in data.values()):
                bundle["validation_specs"] = data
            else:
                bundle["validation_specs"] = {"Q001": data}
    return bundle
