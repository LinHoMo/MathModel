#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k002_register.py — 登记 P15-K002 一次模型构造运行的产物

外部 Agent 产出 `runs/<sid>/` 产物后调用本脚本登记：
  1. F 臂：宽松登记（自由文本，可选 model_ir.json）
  2. S / SV 臂：MODEL_IR 必需，校验顶层字段 + problem_sha256 绑定 + jsonschema
  3. coverage gate（K001 教训落点）：model_ir.problem_binding.sub_question_id 必须
     覆盖该题全部子问题（缺任一 → COVERAGE_FAIL，不进主终点，单独报告）
  4. validation_plan gate（SV 臂强制）：limit_tests/multi_seed.n_runs≥3/
     sensitivity/ambiguity_handling/claim_evidence_map 非空机械校验
     （字段非空 ≠ 内容正确；内容质量由盲评判断）
  5. latency > 0、executor 身份记录

用法:
    py -3.12 research/P15/scripts/k002_register.py \
        --submission-id <sid> --latency 134 --agent-identity doubao \
        --model-version "doubao-pro" [--model-ir path/to/model_ir.json] \
        [--validation-plan path/to/validation_plan.json] [--prompt-tokens N] \
        [--completion-tokens N]

退出码：0 = 登记成功；2 = COVERAGE_FAIL（记录但不进主终点）；1 = 校验失败（作废）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema  # 真实 jsonschema 校验（S/SV 臂产物必须通过 MODEL_IR 契约）

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k002_common as K  # noqa: E402

# MODEL_IR 契约 schema（唯一真源 = core；research/P15 旧版已 SUPERSEDED）：
# S/SV 臂产物必须通过（docstring 承诺的 jsonschema，此处真实执行）
MODEL_IR_SCHEMA = K.ROOT / "src/modeling_harness/schemas/v3/model/model_ir.schema.json"

REQUIRED_TOP = [
    "ir_version", "model_id", "model_family", "problem_binding", "assumptions",
    "variables", "parameters", "objectives", "constraints", "mechanisms",
    "equations", "dependencies", "solvers", "experiments", "validations",
    "claims", "model_graph", "modeling_trace",
]

# validation_plan gate：SV 臂五个强制字段的最小非空判定
VP_REQUIRED = {
    "limit_tests": lambda v: isinstance(v, list) and len(v) > 0,
    "multi_seed": lambda v: (isinstance(v, dict) and v.get("n_runs", 0) >= 3),
    "sensitivity": lambda v: isinstance(v, list) and len(v) > 0,
    "ambiguity_handling": lambda v: isinstance(v, list) and len(v) > 0,
    "claim_evidence_map": lambda v: (isinstance(v, list) and len(v) > 0
                                     and all(isinstance(c, dict)
                                             and c.get("evidence_ref")
                                             for c in v)),
}


def check_coverage(ir: dict, expected: list) -> tuple:
    """coverage gate：返回 (覆盖到的子问题集, 缺失集)。"""
    pb = ir.get("problem_binding") or {}
    sid = pb.get("sub_question_id")
    covered = set()
    if sid:
        covered.add(str(sid))
    for obj in (ir.get("objectives") or []) + (ir.get("claims") or []) \
            + (ir.get("validations") or []) + (ir.get("mechanisms") or []):
        b = obj.get("sub_question_binding") if isinstance(obj, dict) else None
        if isinstance(b, str):
            covered.add(b)
        elif isinstance(b, list):
            covered.update(str(x) for x in b)
    missing = [q for q in expected if q not in covered]
    return covered, missing


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="登记 P15-K002 单次运行产物")
    ap.add_argument("--submission-id", required=True)
    ap.add_argument("--latency", type=float, required=True, help="秒，必须 > 0")
    ap.add_argument("--agent-identity", default="doubao",
                    choices=["doubao", "gpt", "claude", "human", "other"])
    ap.add_argument("--model-version", default="unknown")
    ap.add_argument("--provider", default="unknown")
    ap.add_argument("--model-ir", default=None, help="JSON 文件路径（S/SV 臂必需）")
    ap.add_argument("--validation-plan", default=None, help="JSON 文件路径（SV 臂必需）")
    ap.add_argument("--prompt-tokens", type=int, default=None)
    ap.add_argument("--completion-tokens", type=int, default=None)
    args = ap.parse_args(argv)

    sid = args.submission_id
    run_dir = K.RUNS / sid
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"[FAIL] 未找到 manifest，submission_id 无效: {sid}")
        return 1
    manifest = K.read_json(manifest_path)
    arm = manifest["arm"]
    pid = manifest["problem_id"]

    # 子问题期望列表：从 gt.json 读（冻结题面）
    gt = K.read_json(K.PROBLEM_CARDS / pid / "gt.json")
    expected_sqs = gt["sub_questions"]

    errors, warnings = [], []
    ir = None

    if arm in ("S", "SV"):
        ir_path = Path(args.model_ir) if args.model_ir else run_dir / "model_ir.json"
        if not ir_path.exists():
            print(f"[FAIL] {arm} 臂未找到产物 model_ir.json: {ir_path}")
            return 1
        try:
            ir = json.loads(ir_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[FAIL] model_ir.json 不是合法 JSON: {e}")
            return 1
        missing = [k for k in REQUIRED_TOP if k not in ir]
        if missing:
            errors.append(f"MODEL_IR 缺顶层字段: {missing}")
        # 真实 jsonschema 校验（MODEL_IR 契约，core 真源；与模板承诺对齐）
        try:
            schema = json.loads(MODEL_IR_SCHEMA.read_text(encoding="utf-8"))
            verrors = sorted(
                jsonschema.Draft202012Validator(schema).iter_errors(ir),
                key=lambda e: list(e.path),
            )
            for ve in verrors[:5]:
                errors.append(
                    f"MODEL_IR schema 不通过: "
                    f"{'/'.join(str(p) for p in ve.path) or '(root)'} {ve.message[:120]}"
                )
        except Exception as e:
            errors.append(f"MODEL_IR schema 校验异常: {e}")
        pb = ir.get("problem_binding") or {}
        if pb.get("problem_sha256") != manifest["statement_sha256"]:
            errors.append(f"problem_sha256 不匹配（产物 {pb.get('problem_sha256')} "
                          f"≠ 冻结 {manifest['statement_sha256']}）")
        if pb.get("problem_id") not in (None, pid):
            errors.append(f"problem_id 不匹配: {pb.get('problem_id')} ≠ {pid}")
    elif arm == "F":
        # F 臂自由文本：宽松登记；若有 model_ir.json 也记录（不强制）
        f_ir = run_dir / "model_ir.json"
        if f_ir.exists():
            try:
                ir = json.loads(f_ir.read_text(encoding="utf-8"))
                warnings.append("F 臂提交了 model_ir.json（自愿，不强制）")
            except Exception:
                pass

    if args.latency <= 0:
        errors.append("latency 必须 > 0（latency≈0 视为空壳产物）")

    # ---- coverage gate（全部臂；F 臂无 model_ir 时覆盖视为未知 → 不判 FAIL）----
    coverage = None
    if ir is not None:
        covered, missing_sq = check_coverage(ir, expected_sqs)
        coverage = {"expected": expected_sqs,
                    "covered": sorted(covered), "missing": missing_sq,
                    "complete": len(missing_sq) == 0}
        if missing_sq:
            warnings.append(f"coverage 缺失子问题: {missing_sq} → COVERAGE_FAIL")

    # ---- validation_plan gate（SV 臂强制）----
    vp = None
    if arm == "SV":
        vp_path = Path(args.validation_plan) if args.validation_plan \
            else run_dir / "validation_plan.json"
        if not vp_path.exists():
            errors.append(f"SV 臂缺少 validation_plan.json: {vp_path}")
        else:
            try:
                vp = json.loads(vp_path.read_text(encoding="utf-8"))
            except Exception as e:
                errors.append(f"validation_plan.json 不是合法 JSON: {e}")
            if vp:
                for field, ok in VP_REQUIRED.items():
                    if field not in vp or not ok(vp.get(field)):
                        errors.append(f"validation_plan.{field} 不满足最小非空要求")

    if errors:
        print(f"[FAIL] {sid} 登记失败：")
        for e in errors:
            print("   -", e)
        return 1

    # 写登记产物
    if ir is not None:
        K.write_json(run_dir / "model_ir.json", ir)
    if vp is not None:
        K.write_json(run_dir / "validation_plan.json", vp)

    det = {"coverage": coverage}
    if ir is not None:
        fam = ir.get("model_family") or {}
        det["model_family_primary"] = (fam.get("primary")
                                       if isinstance(fam, dict) else None)
        det["mechanism_count"] = len(ir.get("mechanisms") or [])
        det["equation_count"] = len(ir.get("equations") or [])
    if vp is not None:
        det["validation_plan"] = {k: (len(v) if isinstance(v, list) else v)
                                  for k, v in vp.items()}
    K.write_json(run_dir / "deterministic.json", det)

    status = "REGISTERED"
    if coverage and not coverage["complete"]:
        status = "COVERAGE_FAIL"
    manifest.update({
        "status": status,
        "updated_at": K.utc_now_iso(),
        "generator": {"agent_identity": args.agent_identity,
                      "model_version": args.model_version,
                      "provider": args.provider},
        "cost": {"prompt_tokens": args.prompt_tokens,
                 "completion_tokens": args.completion_tokens,
                 "latency_seconds": args.latency},
        "coverage": coverage,
    })
    K.write_json(manifest_path, manifest)

    import subprocess
    subprocess.run([sys.executable, str(K.SCRIPTS_DIR / "k002_state.py"),
                    "set-run", sid, status], capture_output=True)

    print(f"[OK] 已登记 {sid}  臂={arm}  状态={status}")
    if coverage:
        print(f"     coverage: {len(coverage['covered'])}/{len(expected_sqs)} 子问题"
              + (f"（缺失 {coverage['missing']}）" if coverage["missing"] else ""))
    if vp:
        print(f"     validation_plan gate: PASS（5 字段非空）")
    for w in warnings:
        print(f"     [WARN] {w}")
    return 0 if status == "REGISTERED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
