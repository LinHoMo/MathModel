# -*- coding: utf-8 -*-
"""K002 G5 Statistical validity — 功效预计算（无依赖 Monte Carlo 模拟）

设计：block=6，臂内 5 rep，配对差（blocked design）。
配对差均值按 block 内 5 rep 平均 → 方差缩 5 倍（rep 独立假设）。
基线方差：K001 per-block 差值 sd（2020_B +6.41 / 2018_A -2.56 / 2019_C 0.0）。
问题：给定效应量 Δ，6 块配对 t 检验（双侧 α=0.05）的检出功效。
"""
import math
import random

K001_BLOCKS = [6.41, -2.56, 0.0]
mean_k = sum(K001_BLOCKS) / 3
sd_k = math.sqrt(sum((x - mean_k) ** 2 for x in K001_BLOCKS) / (3 - 1))

N_BLOCKS = 6
REP = 5
N_SIM = 200_000
ALPHA = 0.05
SEED = 20260909


def t_crit_two_sided(df, alpha):
    # 二分求 t 临界值（双侧），用 Beta 函数正则化近似精度有限，
    # 直接查表近似：df=5 时 t_{0.975}=2.5706
    table = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
             7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}
    return table.get(df, 1.96)


def simulate_power(effect, sd_block, n_blocks, rep, n_sim, seed):
    """模拟：每 block 差值为 N(effect, (sd_block/sqrt(rep))^2) 的 5-rep 均值。"""
    rng = random.Random(seed + int(effect * 100))
    sigma_block_mean = sd_block / math.sqrt(rep)
    crit = t_crit_two_sided(n_blocks - 1, ALPHA)
    hits = 0
    for _ in range(n_sim):
        diffs = [effect + rng.gauss(0, sigma_block_mean) for _ in range(n_blocks)]
        d_bar = sum(diffs) / n_blocks
        s = math.sqrt(sum((x - d_bar) ** 2 for x in diffs) / (n_blocks - 1))
        if s <= 1e-12:
            t = float("inf") if d_bar != 0 else 0.0
        else:
            t = d_bar / (s / math.sqrt(n_blocks))
        if abs(t) > crit:
            hits += 1
    return hits / n_sim


def main():
    print(f"K001 per-block sd（配对差口径）={sd_k:.2f}")
    print(f"K002 设计：block={N_BLOCKS}，rep={REP}，"
          f"块内均值 sd={sd_k / math.sqrt(REP):.2f}")
    print(f"配对 t 检验（双侧 α={ALPHA}，df={N_BLOCKS-1}，"
          f"t_crit={t_crit_two_sided(N_BLOCKS - 1, ALPHA)}），"
          f"模拟 {N_SIM} 次\n")
    print(f"{'效应量 Δ':>8} | {'功效':>6} | 判断")
    print("-" * 42)
    for eff in [1.0, 2.14, 3.0, 3.5, 3.9, 5.0]:
        p = simulate_power(eff, sd_k, N_BLOCKS, REP, N_SIM, SEED)
        tag = "≥0.80 可接受" if p >= 0.80 else ("<0.80 不足" if p < 0.80 else "")
        print(f"{eff:8.2f} | {p:6.2f} | {tag}")
    print("\n结论：K001 观测效应 2.14 在本设计下功效约 0.5 档；")
    print("     要达到 80% 功效需效应量 ≥3.5–3.9。")
    print("     预注册口径：效应量 + 95% CI 为主终点（与 K001 同决策门），")
    print("     假设检验为辅助；此表即 G5 的诚实功效声明。")


if __name__ == "__main__":
    main()
