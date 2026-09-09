# -*- coding: utf-8 -*-
"""K003 功效预计算（无依赖 Monte Carlo）。

用 K002 实测 per-block sd（4.62，K001 同源）估计 rep=3 下配对差检验功效。
设计：主检验 6 题（block=6）× 3 rep；块内均值 sd = per_block_sd / sqrt(rep)。
配对 t（双侧 α=0.05, df=5, t_crit=2.571）。

用法: py -3.12 research/P15/analysis/k003_power.py
"""
import math
import random

SEED = 42
N_BLOCKS = 6
REPS = 3
PER_BLOCK_SD = 4.62          # K002 实测（K001 per-block sd 同源）
T_CRIT = 2.57058             # 双侧 α=0.05, df=5
N_SIM = 200_000


def block_mean_sd(per_block_sd: float, reps: int) -> float:
    """块内均值标准差：per_block_sd / sqrt(reps)。"""
    return per_block_sd / math.sqrt(reps)


def power(delta: float, sd_mean: float, n_blocks: int, t_crit: float,
          n_sim: int, rng: random.Random) -> float:
    """配对差均值 delta、块均值标准差 sd_mean、block=n_blocks 的检验功效。"""
    se = sd_mean / math.sqrt(n_blocks)
    hits = 0
    for _ in range(n_sim):
        t = (rng.gauss(delta, se)) / se  # 等价于 (delta/se) + 标准正态
        if t > t_crit:
            hits += 1
    return hits / n_sim


def main() -> None:
    rng = random.Random(SEED)
    sd_mean = block_mean_sd(PER_BLOCK_SD, REPS)
    print(f"K003 功效预计算（block={N_BLOCKS}, rep={REPS}, per_block_sd={PER_BLOCK_SD}）")
    print(f"块内均值 sd = {sd_mean:.3f}；配对差 SE = {sd_mean / math.sqrt(N_BLOCKS):.3f}")
    print()
    print("效应量 Δ(S−F)   power（配对 t 双侧 α=0.05, df=5）")
    for delta in [1.0, 2.14, 2.5, 3.0, 3.3, 3.5, 3.9, 4.5, 5.0]:
        p = power(delta, sd_mean, N_BLOCKS, T_CRIT, N_SIM, rng)
        print(f"  {delta:>6.2f}      {p:.3f}")
    print()
    print("参考：K002 @rep=5 块内均值 sd=2.07，Δ=2.14→0.54 / Δ=3.0→0.81 / Δ=3.9→0.95")
    print("K003 @rep=3 块内均值 sd=2.67：Δ=2.14→0.273 / Δ=3.0→0.571 / Δ=3.9→0.845")
    print("power≥0.8 需 Δ≥3.7（如实声明：rep=3 为成本—功效权衡，功效边界写入 DRAFT §5）")


if __name__ == "__main__":
    main()
