# -*- coding: utf-8 -*-
"""P0-E8 K002 dry-run v2 — 修复后 fidelity 在真实 MODEL_IR（2019_C）上的判定。

对照三段外部 code：
  A  忠实实现 MODEL_IR + output_mapping（全量声明变量输出）→ 预期 aligned
  A' 忠实实现但缺 output_mapping（中文名→英文输出未翻译）→ 预期 misaligned
      （证明 mapping 是必要契约，不是装饰）
  B  跑通但模型不对（静态值/字段全错）→ 预期 misaligned
  C  mapping 撒谎（声明 key 在输出里不存在）→ 预期 misaligned（防谎报）
同时输出执行级终点（K002 G4 预检）：execution_success_rate / model_fidelity /
evidence_completeness。
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "core"))

from runtime.execution.codegen import run_code_pipeline

MODEL_IR = json.load(open(
    REPO / "research/P15/experiments/P15-K001/runs"
    "/02f06b90-f143-462f-9c5c-0eed8da0365b/model_ir.json", encoding="utf-8"))

MAPPING = {
    "时段索引": "i", "时段乘客到达率": "lambda_p", "时段出租车到达率": "lambda_t",
    "时段初排队长度": "n", "期望等待时间": "Wq", "期望排队长度": "Lq",
    "班次总收益": "J", "阈值排队长度": "nstar", "系统空闲概率": "P0",
    "排队等待概率": "Pw", "蓄车净收益": "Rq", "放空净收益": "Rl",
    "值函数": "V", "决策变量": "d", "求和指标": "k",
    "服务台数": "c", "服务率": "mu",
}

CODE_A = """import json
# 外部 Agent 生成：忠实实现 MODEL_IR（2019_C 蓄车池 M/M/c 排队 + 阈值 DP）
c, mu, lam_t, lam_p = 3, 6.0, 4.0, 3.2
rho = lam_t / (c * mu)
# M/M/c 稳态概率（Erlang-C 示意）
s = sum((c*rho)**k / __import__('math').factorial(k) for k in range(c))
P0 = 1.0 / (s + (c*rho)**c / (__import__('math').factorial(c) * (1 - rho)))
Pw = ((c*rho)**c * P0) / (__import__('math').factorial(c) * (1 - rho))
Wq = Pw / (c * mu - lam_t)
Lq = lam_t * Wq
nstar = max(0, int(round(c * mu - lam_t)))
d = 1 if nstar > 0 else 0
Rq, Rl = 2.0, 1.0
J = Rq * min(lam_t, nstar) - Rl * max(0, lam_t - nstar)
V = J
res = {"i": 1, "lambda_p": lam_p, "lambda_t": lam_t, "n": 2, "Wq": round(Wq, 4),
       "Lq": round(Lq, 4), "J": round(J, 3), "nstar": nstar, "P0": round(P0, 4),
       "Pw": round(Pw, 4), "Rq": Rq, "Rl": Rl, "V": round(V, 3), "d": d,
       "k": 0, "c": c, "mu": mu}
print(json.dumps(res))
"""

CODE_X = """import json
# 外部 Agent 生成：忠实实现但输出用**私有命名空间**（wait_time 等）
# ——与 MODEL_IR 的声明名/符号均不同，必须靠 output_mapping 翻译
c, mu, lam_t, lam_p = 3, 6.0, 4.0, 3.2
rho = lam_t / (c * mu)
s = sum((c*rho)**k / __import__('math').factorial(k) for k in range(c))
P0 = 1.0 / (s + (c*rho)**c / (__import__('math').factorial(c) * (1 - rho)))
Pw = ((c*rho)**c * P0) / (__import__('math').factorial(c) * (1 - rho))
Wq = Pw / (c * mu - lam_t)
Lq = lam_t * Wq
nstar = max(0, int(round(c * mu - lam_t)))
d = 1 if nstar > 0 else 0
Rq, Rl = 2.0, 1.0
J = Rq * min(lam_t, nstar) - Rl * max(0, lam_t - nstar)
res = {"period": 1, "arr_p": lam_p, "arr_t": lam_t, "q_len": 2,
       "wait_time": round(Wq, 4), "queue_len": round(Lq, 4),
       "profit_total": round(J, 3), "threshold": nstar, "idle_prob": round(P0, 4),
       "wait_prob": round(Pw, 4), "gain_hold": Rq, "gain_empty": Rl,
       "value_fn": round(J, 3), "dec": d, "idx": 0, "servers": c, "serv_rate": mu}
print(json.dumps(res))
"""

# 跨命名空间映射：声明名/符号 → 私有输出 key
MAPPING_X = {
    "时段索引": "period", "i": "period",
    "时段乘客到达率": "arr_p", "lambda_p": "arr_p",
    "时段出租车到达率": "arr_t", "lambda_t": "arr_t",
    "时段初排队长度": "q_len", "n": "q_len",
    "期望等待时间": "wait_time", "Wq": "wait_time",
    "期望排队长度": "queue_len", "Lq": "queue_len",
    "班次总收益": "profit_total", "J": "profit_total",
    "阈值排队长度": "threshold", "nstar": "threshold",
    "系统空闲概率": "idle_prob", "P0": "idle_prob",
    "排队等待概率": "wait_prob", "Pw": "wait_prob",
    "蓄车净收益": "gain_hold", "Rq": "gain_hold",
    "放空净收益": "gain_empty", "Rl": "gain_empty",
    "值函数": "value_fn", "V": "value_fn",
    "决策变量": "dec", "d": "dec",
    "求和指标": "idx", "k": "idx",
    "服务台数": "servers", "c": "servers",
    "服务率": "serv_rate", "mu": "serv_rate",
}

CODE_B = """import json
# 外部 Agent 生成：跑通但没实现声明的模型（静态值 + 无关字段）
print(json.dumps({"answer": 42, "score": 0.8}))
"""

CODE_C = """import json
# 外部 Agent 生成：mapping 撒谎——声明 '期望等待时间' 输出 wait_time，但实际没有
print(json.dumps({"threshold": 14, "profit_total": 12.5}))
"""


def run(label, code, mapping=None):
    proj = REPO / f"research/P15/dryrun/k002-dryrun-2019C/{label}"
    proj.mkdir(parents=True, exist_ok=True)
    out = run_code_pipeline(proj, MODEL_IR, code, model_id=f"M-{label}",
                            solver_id="S-2019C", output_mapping=mapping)
    rep = json.loads(Path(out["fidelity_report"]).read_text(encoding="utf-8"))
    return out, rep


def main():
    results = {}
    cases = (
        ("A", CODE_A, MAPPING, "aligned"),      # 符号命名空间 + mapping
        ("X", CODE_X, None, "misaligned"),      # 私有命名空间、缺 mapping → 不可验证
        ("XM", CODE_X, MAPPING_X, "aligned"),   # 私有命名空间 + mapping → 对齐
        ("B", CODE_B, None, "misaligned"),      # 跑通但模型不对
        ("C", CODE_C, MAPPING_X, "misaligned"),  # mapping 撒谎
    )
    for label, code, mapping, want in cases:
        out, rep = run(label, code, mapping)
        results[label] = {
            "exec_status": out["exec_status"],
            "fidelity_status": out["fidelity_status"],
            "fidelity_score": out["fidelity_score"],
            "checks_total": rep["total"], "checks_passed": rep["passed"],
        }
        print(f"[{label}] exec={out['exec_status']} "
              f"fidelity={out['fidelity_status']} score={out['fidelity_score']} "
              f"({rep['passed']}/{rep['total']}) want={want}")
        if label in ("X",):
            for c in rep["checks"]:
                if not c["passed"] and c["kind"] != "precondition":
                    print("    FAIL:", c["name"], "|", c.get("detail", "")[:90])
    print("\n=== 判定核查 ===")
    ok = True
    for k, want in (("A", "aligned"), ("X", "misaligned"), ("XM", "aligned"),
                    ("B", "misaligned"), ("C", "misaligned")):
        got = results[k]["fidelity_status"]
        mark = "OK" if got == want else "!! WRONG !!"
        ok = ok and got == want
        print(f"  {k}: want={want} got={got} {mark}")
    print("全部符合" if ok else "存在不符合")
    # K002 G4 执行级终点预检（本次 dry-run 样本）
    n = len(results)
    succ = sum(1 for r in results.values() if r["exec_status"] == "success")
    align = sum(1 for r in results.values()
                if r["fidelity_status"] == "aligned")
    print("\n=== K002 G4 预检（n=%d dry-run 样本）===" % n)
    print(f"  execution_success_rate = {succ}/{n} = {succ/n:.2f}")
    print(f"  model_fidelity(aligned rate) = {align}/{n} = {align/n:.2f}")
    out_file = REPO / "research/P15/dryrun/k002-dryrun-2019C/summary.json"
    out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2)
                        + "\n", encoding="utf-8")
    print(f"  summary -> {out_file}")
    return 0 if ok else 1


if __name__ == "__main__":
    main()
