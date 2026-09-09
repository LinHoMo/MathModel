"""2018_B 智能RGV动态调度 — 离散事件仿真+贪心调度（自包含，纯标准库）。"""
import json
import heapq

def solve(inputs: dict) -> dict:
    # 系统参数（第1组数据）
    move_times = {1: 20, 2: 33, 3: 46}  # RGV移动1/2/3个单位时间（秒）
    process_time = 560  # 一道工序加工时间（秒）
    load_odd = 28   # RGV为1#,3#,5#,7#上下料时间
    load_even = 31  # RGV为2#,4#,6#,8#上下料时间
    clean_time = 25  # 清洗时间
    n_cnc = 8
    shift_time = 8 * 3600  # 8小时 = 28800秒

    def move_time(from_pos, to_pos):
        dist = abs(from_pos - to_pos)
        if dist == 0:
            return 0
        # 线性插值：已知1/2/3单位时间
        if dist <= 3:
            return move_times[dist]
        # 超过3单位：用3单位时间 + 每额外单位约13秒
        return move_times[3] + (dist - 3) * 13

    # 离散事件仿真
    # 事件: (time, type, cnc_id)
    # type: "cnc_done" (CNC加工完成), "rgv_arrive" (RGV到达某CNC)
    events = []
    # CNC状态: "idle" / "processing" / "done_waiting"
    cnc_state = ["idle"] * n_cnc
    cnc_done_time = [0.0] * n_cnc
    cnc_parts = [0] * n_cnc  # 每台CNC完成的物料数

    rgv_pos = 0  # RGV初始位置（在1#CNC旁，位置索引0）
    rgv_busy_until = 0.0
    total_parts = 0
    rgv_move_total = 0.0
    rgv_idle_total = 0.0
    last_event_time = 0.0

    # 初始化：所有CNC idle，RGV依次上料
    # 贪心策略：RGV总是去最近的需要上下料的CNC
    def find_nearest_idle(pos):
        best = None
        best_dist = float("inf")
        for i in range(n_cnc):
            if cnc_state[i] == "idle":
                d = abs(pos - i)
                if d < best_dist:
                    best_dist = d
                    best = i
        return best

    def find_nearest_done(pos):
        best = None
        best_time = float("inf")
        for i in range(n_cnc):
            if cnc_state[i] == "done_waiting":
                if cnc_done_time[i] < best_time:
                    best_time = cnc_done_time[i]
                    best = i
            elif cnc_state[i] == "processing":
                if cnc_done_time[i] < best_time:
                    best_time = cnc_done_time[i]
                    best = i
        return best

    current_time = 0.0
    # 初始：给所有CNC上料（RGV依次移动）
    init_order = list(range(n_cnc))
    for cnc_id in init_order:
        mt = move_time(rgv_pos, cnc_id)
        current_time += mt
        rgv_move_total += mt
        lt = load_odd if cnc_id % 2 == 0 else load_even
        current_time += lt
        cnc_state[cnc_id] = "processing"
        cnc_done_time[cnc_id] = current_time + process_time
        rgv_pos = cnc_id

    # 主仿真循环
    while current_time < shift_time:
        # 找最近的已完成或即将完成的CNC
        target = find_nearest_done(rgv_pos)
        if target is None:
            break

        # 移动到目标
        mt = move_time(rgv_pos, target)
        arrival_time = current_time + mt
        rgv_move_total += mt

        # 等待CNC加工完成（如果还没完成）
        if arrival_time < cnc_done_time[target]:
            wait = cnc_done_time[target] - arrival_time
            rgv_idle_total += wait
            arrival_time = cnc_done_time[target]

        if arrival_time > shift_time:
            break

        # 下料+上料+清洗
        lt = load_odd if target % 2 == 0 else load_even
        service_time = lt * 2 + clean_time  # 下料+上料+清洗
        finish_time = arrival_time + service_time

        if finish_time > shift_time:
            break

        # 完成一个物料
        total_parts += 1
        cnc_parts[target] += 1
        cnc_state[target] = "processing"
        cnc_done_time[target] = finish_time + process_time
        current_time = finish_time
        rgv_pos = target

    # 统计
    utilization = []
    for i in range(n_cnc):
        busy = cnc_parts[i] * process_time
        utilization.append(round(min(1.0, busy / shift_time), 4))

    avg_cycle = shift_time / total_parts if total_parts > 0 else 0
    rgv_util = round(1.0 - rgv_idle_total / shift_time, 4) if shift_time > 0 else 0

    return {
        "total_parts": total_parts,
        "throughput_per_hour": round(total_parts / 8.0, 2),
        "avg_cycle_time_s": round(avg_cycle, 2),
        "rgv_utilization": rgv_util,
        "rgv_move_total_s": round(rgv_move_total, 1),
        "rgv_idle_total_s": round(rgv_idle_total, 1),
        "cnc_utilization": utilization,
        "cnc_parts_per_machine": cnc_parts,
        "shift_duration_s": shift_time,
        "n_cnc": n_cnc,
        "process_time_s": process_time,
        "scheduling_strategy": "greedy_nearest",
    }

if __name__ == "__main__":
    print(json.dumps(solve({}), ensure_ascii=False))
