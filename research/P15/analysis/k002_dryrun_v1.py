# -*- coding: utf-8 -*-
"""P0-E8 K002 dry-run v1 — 实证 fidelity 在真实 MODEL_IR（2019_C）上的表现。

对照两段外部 code：
  A 忠实实现 MODEL_IR 声明（M/M/c 排队 + DP 阈值策略）
  B 跑通但模型不对（静态值、漏输出）
并记录 fidelity 判定；重点观察中文声明名 vs 英文输出 key 的映射表现。
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

CODE_A = """import json

# 外部 Agent 生成：忠实实现 MODEL_IR（2019_C 蓄车池 M/M/c 排队 + 阈值 DP）
c = 3          # 服务台数
mu = 6.0       # 每台服务率（辆/10min）
lam_t = 4.0    # 出租车到达率
nstar = max(0, int(round(c * mu - lam_t)))   # 阈值排队长度（简化闭环）
J = lam_t * nstar                            # 班次总收益（示意量纲）
Wq = 1.0 / (c * mu - lam_t)                  # 期望等待时间
n = 2                                         # 时段初排队长度
res = {
    "nstar": nstar,
    "J": round(J, 3),
    "Wq": round(Wq, 3),
    "n": n,
    "lambda_t": lam_t,
    "lambda_p": 3.2,
    "Lq": round(lam_t * Wq, 3),
    "i": 1,
}
print(json.dumps(res))
"""

CODE_B = """import json

# 外部 Agent 生成：跑通但没实现声明的模型（静态值 + 换字段名）
print(json.dumps({"answer": 42, "score": 0.8}))
"""


def main():
    proj = REPO / "research/P15/dryrun/k002-dryrun-2019C"
    proj.mkdir(parents=True, exist_ok=True)
    print("=== RUN A（忠实实现，无 mapping）===")
    out_a = run_code_pipeline(proj, MODEL_IR, CODE_A,
                              model_id="M-DRY-A", solver_id="S-DRY-A")
    print(json.dumps({k: v for k, v in out_a.items()
                      if k != "fidelity_report"}, ensure_ascii=False))
    print("\n=== RUN B（跑通但模型不对）===")
    out_b = run_code_pipeline(proj, MODEL_IR, CODE_B,
                              model_id="M-DRY-B", solver_id="S-DRY-B")
    print(json.dumps({k: v for k, v in out_b.items()
                      if k != "fidelity_report"}, ensure_ascii=False))
    print("\n=== fidelity 明细（A）===")
    rep = json.loads(Path(out_a["fidelity_report"]).read_text(encoding="utf-8"))
    fails = [c for c in rep["checks"] if not c["passed"]]
    print(f"checks={rep['total']} passed={rep['passed']} "
          f"score={rep['fidelity_score']} status={rep['fidelity_status']}")
    for c in fails:
        print("  FAIL:", c["name"])
        print("        ", c.get("detail", "")[:120])
    print("\n=== 判定 ===")
    print("A 应为 aligned（忠实实现）；B 应为 misaligned（漏声明模型）")
    print(f"实际: A={out_a['fidelity_status']} B={out_b['fidelity_status']}")


if __name__ == "__main__":
    main()
