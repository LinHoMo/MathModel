"""2020_B 穿越沙漠 — 确定性天气下的资源约束动态规划（自包含，纯标准库）。"""
import json
import random

def solve(inputs: dict) -> dict:
    random.seed(44)
    # ---- 简化地图：5节点线性图 Start-Village-Mine-Waypoint-End ----
    nodes = ["Start", "Village", "Mine", "Waypoint", "End"]
    adj = {0: [1], 1: [0, 2], 2: [1, 3], 3: [2, 4], 4: [3]}
    n_days = 10
    # 天气：0=晴朗, 1=高温, 2=沙暴（沙暴日必须停留）
    weather = [0, 0, 1, 0, 2, 0, 1, 0, 0, 0]
    # 资源参数
    base_water, base_food = 1, 1
    price_water, price_food = 5, 10
    capacity = 20
    start_money = 10000
    mine_income = 1000
    village_mult = 2
    refund_mult = 0.5

    # DP: state=(day, pos, water, food) -> max money; -inf = unreachable
    NEG = float("-inf")
    # water, food discretized 0..capacity
    dp = {}
    parent = {}
    # day 0: at Start, buy initial resources
    for w in range(capacity + 1):
        for f in range(capacity + 1 - w):
            cost = w * price_water + f * price_food
            if cost <= start_money:
                dp[(0, 0, w, f)] = start_money - cost

    def consume(day, action, w, f):
        """返回 (water_after, food_after) 或 None if 耗尽."""
        mult = {"stay": 1, "move": 2, "mine": 3}[action]
        w2 = w - base_water * mult
        f2 = f - base_food * mult
        if w2 < 0 or f2 < 0:
            return None
        return w2, f2

    for day in range(n_days):
        next_dp = {}
        for (d, pos, w, f), money in dp.items():
            if d != day:
                continue
            wstate = weather[day]
            # 沙暴日只能停留
            if wstate == 2:
                actions = [("stay", pos)]
            else:
                actions = [("stay", pos)]
                for nb in adj[pos]:
                    actions.append(("move", nb))
                if pos == 2:  # Mine
                    actions.append(("mine", pos))
            for act, new_pos in actions:
                c = consume(day, act, w, f)
                if c is None:
                    continue
                nw, nf = c
                nmoney = money
                if act == "mine":
                    nmoney += mine_income
                # 村庄购买（随时可买，价格2倍）
                if new_pos == 1:
                    # 简化：不主动购买（初始购买已够）
                    pass
                key = (day + 1, new_pos, nw, nf)
                if nmoney > next_dp.get(key, NEG):
                    next_dp[key] = nmoney
                    parent[key] = (day, pos, w, f, act)
        dp = next_dp

    # 终点：到达 End(pos=4) 的最优
    best = None
    best_key = None
    for (d, pos, w, f), money in dp.items():
        if pos == 4:
            # 退回剩余资源
            refund = (w * price_water + f * price_food) * refund_mult
            total = money + refund
            if best is None or total > best:
                best = total
                best_key = (d, pos, w, f)

    # 回溯路径
    path = []
    if best_key:
        cur = best_key
        while cur in parent:
            p = parent[cur]
            path.append({"day": p[0], "from": nodes[p[1]], "action": p[4], "to": nodes[cur[1]]})
            cur = (p[0], p[1], p[2], p[3])
        path.reverse()

    return {
        "optimal_profit": round(best, 2) if best is not None else 0.0,
        "remaining_water": best_key[2] if best_key else 0,
        "remaining_food": best_key[3] if best_key else 0,
        "arrival_day": best_key[0] if best_key else -1,
        "path_length": len(path),
        "optimal_path": path[:5],
        "n_states_explored": len(dp),
        "weather_known": True,
    }

if __name__ == "__main__":
    print(json.dumps(solve({}), ensure_ascii=False))
