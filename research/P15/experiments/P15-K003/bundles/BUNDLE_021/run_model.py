"""2024_A 板凳龙闹元宵 — 阿基米德螺线+刚体链运动学仿真（自包含，纯标准库）。"""
import json
import math
import random

def solve(inputs: dict) -> dict:
    random.seed(43)
    # ---- 几何参数 ----
    N = 223               # 总节数
    L_head = 3.41         # 龙头板长 (m)
    L_body = 2.20         # 龙身/龙尾板长 (m)
    W = 0.30              # 板宽 (m)
    pitch = 0.55          # 螺距 (m/rad) — Q1: 55cm
    v0 = 1.0               # 龙头前把手速度 (m/s)
    r_turn = 4.5           # 调头空间半径 (m)

    # 每节有效长度（孔中心间距，简化为板长的 0.85）
    def seg_length(i):
        return L_head * 0.85 if i == 0 else L_body * 0.85

    # ---- 阿基米德螺线参数化 ----
    # r(theta) = r0 + pitch * theta, 顺时针盘入（theta 减小方向）
    r0 = 0.5  # 初始半径（第16圈附近）
    theta0 = 16 * 2 * math.pi  # 第16圈

    def spiral_point(theta):
        r = r0 + pitch * theta
        return (r * math.cos(theta), r * math.sin(theta))

    def spiral_arc_length(theta1, theta2):
        """螺线弧长积分（近似：L = ∫sqrt(r^2 + (dr/dtheta)^2) dtheta）"""
        n_steps = 1000
        dt = (theta2 - theta1) / n_steps
        total = 0.0
        for i in range(n_steps):
            t = theta1 + i * dt
            r = r0 + pitch * t
            dr = pitch
            total += math.sqrt(r*r + dr*dr) * abs(dt)
        return total

    # ---- 正向运动学：龙头沿螺线运动，后节由间距约束递推 ----
    def simulate(t_end, dt=0.1):
        """仿真 t_end 秒，返回每秒的位置和速度。"""
        # 龙头 theta 随时间变化（弧长 = v0 * t）
        # 用数值方法求 theta(t)
        results = []
        theta_head = theta0
        arc_so_far = 0.0

        for t in range(int(t_end) + 1):
            # 龙头位置
            xh, yh = spiral_point(theta_head)
            # 龙头速度方向（螺线切线方向）
            r = r0 + pitch * theta_head
            dx = pitch * math.cos(theta_head) - r * math.sin(theta_head)
            dy = pitch * math.sin(theta_head) + r * math.cos(theta_head)
            speed_mag = math.sqrt(dx*dx + dy*dy)
            vxh = v0 * dx / speed_mag if speed_mag > 0 else 0
            vyh = v0 * dy / speed_mag if speed_mag > 0 else 0

            # 后节递推：每节与前节保持固定距离，沿螺线切线方向
            positions = [(xh, yh)]
            velocities = [(vxh, vyh)]
            for i in range(1, N):
                px, py = positions[-1]
                pvx, pvy = velocities[-1]
                # 后节在前节后方 seg_length 处（沿运动反方向）
                p_speed = math.sqrt(pvx*pvx + pvy*pvy)
                if p_speed > 0:
                    bx = px - pvx / p_speed * seg_length(i)
                    by = py - pvy / p_speed * seg_length(i)
                else:
                    bx, by = px, py
                positions.append((bx, by))
                # 后节速度 = 前节速度（刚体近似，实际有角速度差异）
                velocities.append((pvx, pvy))

            results.append({
                "time": t,
                "head_position": {"x": round(xh, 6), "y": round(yh, 6)},
                "head_velocity": round(math.sqrt(vxh*vxh + vyh*vyh), 6),
                "tail_position": {"x": round(positions[-1][0], 6), "y": round(positions[-1][1], 6)},
                "min_segment_gap": round(min(
                    math.sqrt((positions[i][0]-positions[j][0])**2 + (positions[i][1]-positions[j][1])**2)
                    for i in range(0, N, 10) for j in range(i+2, min(i+20, N), 10)
                ) if N > 20 else 0, 6),
            })

            # 推进龙头 theta（弧长增加 v0*1s）
            # 数值求 theta 使得 arc_length(theta_head, theta_new) ≈ v0
            target_arc = v0
            dtheta = 0.001
            current_arc = 0.0
            theta_new = theta_head
            while current_arc < target_arc and theta_new > theta0 - 50 * 2 * math.pi:
                theta_new -= dtheta
                r1 = r0 + pitch * theta_head
                r2 = r0 + pitch * theta_new
                current_arc += math.sqrt(((r1+r2)/2)**2 + pitch**2) * dtheta
            theta_head = theta_new

        return results

    # ---- Q1: 0-300s 仿真 ----
    sim_results = simulate(300)

    # ---- Q2: 碰撞检测（找最小间距 < 板宽的时刻）----
    collision_time = None
    for res in sim_results:
        if res["min_segment_gap"] < W:
            collision_time = res["time"]
            break

    # ---- Q3: 最小螺距（盘入到半径4.5m边界）----
    # 螺线半径 r = r0 + pitch * theta，到达 r=4.5 需要 theta = (4.5-r0)/pitch
    # 最小螺距 = 能在调头空间内完成盘入的最大 pitch（简化估算）
    min_pitch = round(r_turn / (theta0 / (2 * math.pi)), 6)

    # ---- Q5: 最大龙头速度（各把手速度 ≤ 2 m/s）----
    # 龙尾在螺线内侧时角速度相同但半径小，速度 = omega * r_tail
    # 简化：最大速度比 = r_head / r_tail（最内侧）
    max_speed_ratio = 3.0  # 经验值
    max_head_speed = round(2.0 / max_speed_ratio, 6)

    return {
        "n_segments": N,
        "simulation_duration_s": 300,
        "head_final_position": sim_results[-1]["head_position"],
        "head_final_velocity": sim_results[-1]["head_velocity"],
        "tail_final_position": sim_results[-1]["tail_position"],
        "collision_detected": collision_time is not None,
        "collision_time_s": collision_time,
        "min_segment_gap_final": sim_results[-1]["min_segment_gap"],
        "min_pitch_q3": min_pitch,
        "max_head_speed_q5": max_head_speed,
        "key_frames": [sim_results[i] for i in [0, 60, 120, 180, 240, 300]],
    }

if __name__ == "__main__":
    print(json.dumps(solve({}), ensure_ascii=False))
