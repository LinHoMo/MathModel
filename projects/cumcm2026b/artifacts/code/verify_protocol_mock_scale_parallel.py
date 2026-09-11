#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""协议 Mock 演练强度扩容（并行版，逐局落盘，可断点聚合）。

为什么单列一个并行脚本：协议 Mock 单局端到端（真 HTTP 客户端 ↔ 真 Mock 服务器）
约 2.6 s，100 局 × 2 问串行需 ~9 min，超出单条命令的时限。这些局**完全独立**
（各有 seed 与 port），可并行；且本脚本**逐局把记录追加**到 JSONL——即使中途被
打断，已完成的局也已落盘，可再次运行补齐并聚合，不会丢证据。

约束遵循：只 import 被测实现（MockSimulatorServer / SimulatorHTTP / dog_strategy_http），
不修改任何被测代码；随机种子固定 42，N 局取 seed 42..42+N−1 连续；统计口径与
verify_protocol_mock_scale.py 完全一致（样本标准差 + t 分布 95% CI + 线性分位数）。

运行：py -3.12 -X utf8 -m verify_protocol_mock_scale_parallel --trials 100 --workers 12
输出：projects/cumcm2026b/artifacts/protocol_mock_scale.json（聚合）
      projects/cumcm2026b/artifacts/protocol_mock_scale_records.jsonl（逐局，追加）
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulator_http import MockSimulatorServer, SimulatorHTTP  # noqa: E402
import solve_b_http as H  # noqa: E402
from verify_protocol_mock_scale import _stats  # noqa: E402  复用统计口径

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.abspath(os.path.join(HERE, ".."))
OUT_PATH = os.path.join(ART, "protocol_mock_scale.json")
REC_PATH = os.path.join(ART, "protocol_mock_scale_records.jsonl")
SEED = 42


def _one_trial(args):
    """单局：真 Mock 服务器 + 真 HTTP 客户端 + 策略。返回逐局统计。

    port 传 0 让操作系统分配空闲端口（避开 Windows 保留端口段的 WinError 10013），
    绑定后从 server_address 读回实际端口再交给客户端。
    """
    label, seed, kind_mix, _port = args
    srv = MockSimulatorServer(port=0, seed=seed, kind_mix=kind_mix)
    srv.start()
    actual_port = srv._httpd.server_address[1]
    try:
        sim = SimulatorHTTP(base_url=f"http://127.0.0.1:{actual_port}",
                            robot_id="TESTTEAM", timeout=30.0)
        sim.enter()
        st = H.dog_strategy_http(sim, has_directional=kind_mix)
        sim.exit()
        summ = srv.summary()
    finally:
        srv.stop()
    n_cleared = summ["cleared"]
    total = summ["total_sources"]
    return {
        "label": label,
        "seed": seed,
        "total_sources": total,
        "n_cleared": n_cleared,
        "cleared_fraction": n_cleared / total if total else 1.0,
        "virtual_time_s": st["virtual_time_s"],
        "avg_locate_clear_time_s": (st["virtual_time_s"] / n_cleared
                                    if n_cleared else float("inf")),
        "mean_locate_clear_time_s": st["mean_locate_clear_time_s"],
        "n_measure": st["n_measure"],
        "move_dist_m": st["move_dist_m"],
    }


def _existing():
    """读回已落盘记录，按 (label, seed) 去重，支持中断续跑。"""
    done = {}
    if os.path.exists(REC_PATH):
        with open(REC_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                done[(r["label"], r["seed"])] = r
    return done


def _aggregate(per_trials, label, kind_mix, n_trials):
    def col(key):
        return [r[key] for r in per_trials if math.isfinite(r[key])]

    return {
        "label": label,
        "kind_mix": kind_mix,
        "n_trials": n_trials,
        "seed_start": SEED,
        "seed_end": SEED + n_trials - 1,
        "cleared_fraction": _stats(col("cleared_fraction")),
        "avg_locate_clear_time_s": _stats(col("avg_locate_clear_time_s")),
        "mean_locate_clear_time_s": _stats(col("mean_locate_clear_time_s")),
        "virtual_time_s": _stats(col("virtual_time_s")),
        "n_measure": _stats(col("n_measure")),
        "move_dist_m": _stats(col("move_dist_m")),
        "n_cleared_total": sum(r["n_cleared"] for r in per_trials),
        "n_sources_total": sum(r["total_sources"] for r in per_trials),
    }


def main(trials=100, workers=12):
    jobs = []
    for i in range(trials):
        jobs.append(("q3_omni", SEED + i, False, 4000 + i))
    for i in range(trials):
        jobs.append(("q4_mix", SEED + i, True, 4200 + i))

    done = _existing()
    todo = [j for j in jobs if (j[0], j[1]) not in done]
    print(f"已完成 {len(done)} 局，待跑 {len(todo)} 局，workers={workers}", flush=True)

    with open(REC_PATH, "a", encoding="utf-8") as fh:
        if todo:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                futs = {ex.submit(_one_trial, j): j for j in todo}
                for k, fut in enumerate(as_completed(futs), 1):
                    r = fut.result()
                    done[(r["label"], r["seed"])] = r
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                    fh.flush()
                    os.fsync(fh.fileno())
                    if k % 20 == 0:
                        print(f"  {k}/{len(todo)} done", flush=True)

    out = {
        "script": "verify_protocol_mock_scale_parallel.py",
        "protocol": "CUMCM2026B 附件2 HTTP+JSON（本地 Mock，真 HTTP 客户端 ↔ 真 Mock 服务器）",
        "seed_policy": f"固定 42，{trials} 局取 seed 42..{SEED + trials - 1} 连续",
        "std_convention": "样本标准差（n−1）",
        "ci_convention": "均值 t 分布双侧 95% CI（df=n−1）",
        "n_trials": trials,
        "concurrency": workers,
    }
    for label, kind_mix in (("q3_omni", False), ("q4_mix", True)):
        recs = sorted((r for (lb, _s), r in done.items() if lb == label),
                      key=lambda r: r["seed"])
        out[label] = _aggregate(recs, label, kind_mix, trials)
        out[label]["n_actual"] = len(recs)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    for key in ("q3_omni", "q4_mix"):
        b = out[key]
        cf, ac = b["cleared_fraction"], b["avg_locate_clear_time_s"]
        print(f"[{b['label']}] N={b['n_trials']} 实际={b.get('n_actual')} "
              f"seeds {b['seed_start']}..{b['seed_end']}")
        print(f"  清除比例 mean±sd = {cf['mean']:.6f} ± {cf['std_sample']:.6f}  "
              f"min={cf['min']:.6f}  95%CI=[{cf['ci95_low']:.6f},{cf['ci95_high']:.6f}]")
        print(f"  摊薄 avg_locate_clear mean±sd = {ac['mean']:.3f} ± {ac['std_sample']:.3f} s  "
              f"q2.5={ac['q2_5']:.1f} q50={ac['median']:.1f} q97.5={ac['q97_5']:.1f}")
        print(f"  已清除/total = {b['n_cleared_total']}/{b['n_sources_total']}")
    print(f"[OK] {OUT_PATH}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=100)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    raise SystemExit(main(trials=a.trials, workers=a.workers))
