#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k001_register.py — 登记一次模型构造运行的产物

外部 Agent 产出 `runs/<sid>/model_ir.json` 后调用本脚本登记：
  1. 校验 MODEL_IR 必需顶层字段与 problem_sha256 绑定
  2. 校验 latency > 0、payload 非空
  3. 计算确定性机器指标（符号自洽率、claim 支撑率、方法族识别）
  4. 校验/更新 manifest，并推进状态机

用法:
    py -3.12 research/P15/scripts/k001_register.py \
        --submission-id <sid> --latency 134 --agent-identity claude \
        --model-version "claude-x" --provider "console" \
        [--prompt-tokens 3200] [--completion-tokens 4100] \
        [--knowledge-trace path/to/trace.json]

退出码：0 = 登记成功；1 = 校验失败（产物作废，不得进入盲评）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k001_common as K  # noqa: E402

REQUIRED_TOP = [
    "ir_version", "model_id", "model_family", "problem_binding", "assumptions",
    "variables", "parameters", "objectives", "constraints", "mechanisms",
    "equations", "dependencies", "solvers", "experiments", "validations",
    "claims", "model_graph", "modeling_trace",
]

LATEX_COMMANDS = {
    "frac", "partial", "sum", "int", "cdot", "times", "left", "right", "max", "min",
    "alpha", "beta", "gamma", "delta", "theta", "lambda", "mu", "sigma", "rho", "pi",
    "log", "ln", "exp", "sin", "cos", "tan", "sqrt", "lim", "infty", "forall", "in",
    "ldots", "quad", "text", "mathrm", "mathbf", "operatorname", "hat", "bar",
    "tilde", "vec", "dot", "nabla", "epsilon", "varphi", "tau", "Omega", "Delta",
}

# \text{...} / \mathrm{...} 等块内是说明文字，不是符号，先整体剔除
TEXT_BLOCK = re.compile(r"\\[A-Za-z]+\s*\{[^{}]*\}")

# 英文停用词：latex 里夹带的自然语言词汇，不参与符号自洽判定
STOPWORDS = {
    "if", "otherwise", "for", "all", "and", "or", "the", "where", "when", "then",
    "else", "with", "at", "by", "in", "of", "to", "is", "be", "not", "no", "day",
    "per", "end", "start", "multi", "mine", "stay", "levels", "pending",
}


def extract_symbols(latex: str) -> set:
    """从 latex 串中粗提标识符（启发式，用于符号自洽率）。

    处理顺序：去说明文字块 → 去 latex 命令 → 去花括号与上标符号 → 提普通标识符。
    """
    cleaned = TEXT_BLOCK.sub(" ", latex)
    cleaned = re.sub(r"\\[A-Za-z]+", " ", cleaned)      # 去掉全部 latex 命令
    cleaned = re.sub(r"[{}\\\^\$#&]", " ", cleaned)      # 去掉花括号与上标等
    out = set()
    for tok in re.findall(r"[A-Za-z][A-Za-z0-9_]*", cleaned):
        tok = tok.strip("_")
        if not tok or tok in STOPWORDS or len(tok) > 12:
            continue
        out.add(tok)
    return out


def is_declared(tok: str, declared: set) -> bool:
    """完整记号命中，或其下标前的主干命中（如 w_t → w，b_w 保持完整）。"""
    if tok in declared:
        return True
    if "_" in tok:
        base = tok.split("_")[0]
        if base and base in declared:
            return True
    return False


def compute_deterministic(ir: dict) -> dict:
    declared = set()
    for v in ir.get("variables", []) or []:
        if isinstance(v, dict) and v.get("symbol"):
            declared.add(str(v["symbol"]).strip())
    for p in ir.get("parameters", []) or []:
        if isinstance(p, dict) and p.get("symbol"):
            declared.add(str(p["symbol"]).strip())

    used = set()
    for eq in ir.get("equations", []) or []:
        if isinstance(eq, dict) and eq.get("latex"):
            used |= extract_symbols(str(eq["latex"]))

    undeclared = sorted(s for s in used if not is_declared(s, declared))
    ratio = (len(undeclared) / len(used)) if used else 0.0

    claims = ir.get("claims", []) or []
    total_claims = len(claims)
    supported = sum(
        1 for c in claims
        if isinstance(c, dict) and (c.get("status") == "supported" or (c.get("evidence_refs") or []))
    )

    sqs = set()
    for c in claims:
        if isinstance(c, dict) and c.get("sub_question_binding"):
            sqs.add(str(c["sub_question_binding"]))
    for o in ir.get("objectives", []) or []:
        if isinstance(o, dict) and o.get("sub_question_binding"):
            sqs.add(str(o["sub_question_binding"]))
    for m in ir.get("mechanisms", []) or []:
        if isinstance(m, dict) and m.get("sub_question_binding"):
            sqs.add(str(m["sub_question_binding"]))

    family = ir.get("model_family") or {}
    fam = family.get("primary") if isinstance(family, dict) else None

    return {
        "declared_symbols": len(declared),
        "used_symbols": len(used),
        "undeclared_symbols": undeclared[:40],
        "undeclared_symbol_ratio": round(ratio, 4),
        "index_inconsistency": None,   # 由盲评人工判定回填
        "total_claims": total_claims,
        "supported_claims": supported,
        "sub_question_binding_count": len(sqs),
        "method_family_identified": fam,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="登记 P15-K001 单次运行产物")
    ap.add_argument("--submission-id", required=True)
    ap.add_argument("--latency", type=float, required=True, help="秒，必须 > 0")
    ap.add_argument("--prompt-tokens", type=int, default=None)
    ap.add_argument("--completion-tokens", type=int, default=None)
    ap.add_argument("--agent-identity", default="claude",
                    choices=["doubao", "gpt", "claude", "human", "other"])
    ap.add_argument("--model-version", default="unknown")
    ap.add_argument("--provider", default="unknown")
    ap.add_argument("--knowledge-trace", default=None, help="JSON 文件路径")
    args = ap.parse_args(argv)

    sid = args.submission_id
    run_dir = K.RUNS / sid
    manifest_path = run_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"[FAIL] 未找到 manifest，submission_id 无效: {sid}")
        return 1
    manifest = K.read_json(manifest_path)

    ir_path = run_dir / "model_ir.json"
    if not ir_path.exists():
        print(f"[FAIL] 未找到产物 model_ir.json: {ir_path}")
        return 1
    try:
        ir = json.loads(ir_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[FAIL] model_ir.json 不是合法 JSON: {e}")
        return 1

    errors, warnings = [], []

    missing = [k for k in REQUIRED_TOP if k not in ir]
    if missing:
        errors.append(f"MODEL_IR 缺顶层字段: {missing}")

    pb = ir.get("problem_binding", {}) or {}
    if pb.get("problem_sha256") != manifest["hashes"]["problem_sha256"]:
        errors.append(
            f"problem_sha256 不匹配（产物绑定 {pb.get('problem_sha256')} ≠ 冻结 {manifest['hashes']['problem_sha256']}）"
        )
    if pb.get("problem_id") not in (None, manifest["problem_id"]):
        errors.append(f"problem_id 不匹配: {pb.get('problem_id')} ≠ {manifest['problem_id']}")

    if args.latency <= 0:
        errors.append("latency 必须 > 0（latency≈0 视为空壳产物）")

    kt = {"retrieved": [], "considered": [], "used": [], "adapted": [], "rejected": []}
    if args.knowledge_trace:
        kt.update(K.read_json(Path(args.knowledge_trace)))
    if manifest["condition"]["knowledge"] != "none" and not kt["retrieved"]:
        warnings.append("该臂注入了参考资料，但 knowledge_trace.retrieved 为空")

    if errors:
        print(f"[FAIL] {sid} 登记失败：")
        for e in errors:
            print("   -", e)
        return 1

    det = compute_deterministic(ir)
    K.write_json(run_dir / "deterministic.json", det)

    manifest["status"] = "REGISTERED"
    manifest["created_at"] = K.utc_now_iso()
    manifest["generator"] = {
        "agent_identity": args.agent_identity,
        "model_version": args.model_version,
        "provider": args.provider,
    }
    manifest["cost"] = {
        "prompt_tokens": args.prompt_tokens,
        "completion_tokens": args.completion_tokens,
        "latency_seconds": args.latency,
    }
    manifest["knowledge_trace"] = kt

    # schema 校验（jsonschema 可用时）
    try:
        import jsonschema
        schema = K.read_json(K.SCHEMAS / "experiment_manifest.schema.json")
        jsonschema.validate(manifest, schema)
        manifest["schema_validated"] = True
    except ImportError:
        manifest["schema_validated"] = None
        warnings.append("jsonschema 不可用，跳过 manifest schema 校验")
    except Exception as e:
        errors.append(f"manifest schema 校验失败: {str(e)[:200]}")
        print(f"[FAIL] {sid}: {errors[-1]}")
        return 1

    K.write_json(manifest_path, manifest)

    import subprocess
    subprocess.run([sys.executable, str(K.SCRIPTS_DIR / "k001_state.py"),
                    "set-run", sid, "REGISTERED"], capture_output=True)

    print(f"[OK] 已登记 {sid}")
    print(f"     problem={manifest['problem_id']}  状态=REGISTERED  latency={args.latency}s")
    print(f"     确定性指标: 符号未声明率={det['undeclared_symbol_ratio']}  "
          f"claims={det['supported_claims']}/{det['total_claims']}  "
          f"method_family={det['method_family_identified']}")
    for w in warnings:
        print(f"     [WARN] {w}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
