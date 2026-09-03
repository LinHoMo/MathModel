"""碰撞检测模块。

相邻板凳夹角判据 + 非相邻板凳中心线段距离判据 + 矩形板凳重叠判据(SAGITTA)。
圈层剪枝：仅扫圈层差 <= 1 的板凳对，大幅降低计算量。

模板来源: code-templates/optimization/differential_evolution.py（无梯度骨架）
"""

import numpy as np
from spiral import spiral_point


def _segment_distance(p1, p2, p3, p4):
    """两线段 [p1,p2] 与 [p3,p4] 的最短距离。"""
    def dot(a, b):
        return a[0] * b[0] + a[1] * b[1]

    d = (p2[0] - p1[0], p2[1] - p1[1])
    e = (p4[0] - p3[0], p4[1] - p3[1])

    denom = dot(d, d) * dot(e, e) - dot(d, e) * dot(d, e)
    if abs(denom) < 1e-18:
        candidates = [
            np.hypot(p1[0] - p3[0], p1[1] - p3[1]),
            np.hypot(p1[0] - p4[0], p1[1] - p4[1]),
            np.hypot(p2[0] - p3[0], p2[1] - p3[1]),
            np.hypot(p2[0] - p4[0], p2[1] - p4[1]),
        ]
        return min(candidates)

    t = (dot(d, e) * dot((p3[0] - p1[0], p3[1] - p1[1]), e)
         - dot(e, e) * dot((p3[0] - p1[0], p3[1] - p1[1]), d)) / denom
    s = (dot(d, d) * dot((p3[0] - p1[0], p3[1] - p1[1]), e)
         - dot(d, e) * dot((p3[0] - p1[0], p3[1] - p1[1]), d)) / denom

    t = max(0.0, min(1.0, t))
    s = max(0.0, min(1.0, s))

    cx = p1[0] + t * d[0]
    cy = p1[1] + t * d[1]
    dx = p3[0] + s * e[0]
    dy = p3[1] + s * e[1]

    return np.hypot(cx - dx, cy - dy)


def _bench_sagitta(theta_a, theta_b, b):
    """板凳弦线偏离螺线弧的最大垂度。"""
    r_a = b * theta_a / (2.0 * np.pi)
    r_b = b * theta_b / (2.0 * np.pi)
    r_mid = (r_a + r_b) / 2.0
    dtheta = abs(theta_b - theta_a)
    return r_mid * (1.0 - np.cos(dtheta / 2.0))


def _rect_collision_sat(p1, p2, p3, p4, w):
    """SAT 矩形碰撞检测：两线段为中心线、宽度 w 的矩形是否重叠。"""
    d1 = np.array(p2) - np.array(p1)
    d2 = np.array(p4) - np.array(p3)
    l1 = np.linalg.norm(d1)
    l2 = np.linalg.norm(d2)
    if l1 < 1e-15 or l2 < 1e-15:
        return False

    dir1 = d1 / l1
    dir2 = d2 / l2
    axes = [dir1, dir2, np.array([-dir1[1], dir1[0]]), np.array([-dir2[1], dir2[0]])]

    n1 = np.array([-dir1[1], dir1[0]]) * w / 2.0
    n2 = np.array([-dir2[1], dir2[0]]) * w / 2.0

    rect1 = [np.array(p1) + n1, np.array(p2) + n1, np.array(p2) - n1, np.array(p1) - n1]
    rect2 = [np.array(p3) + n2, np.array(p4) + n2, np.array(p4) - n2, np.array(p3) - n2]

    for axis in axes:
        proj1 = [np.dot(v, axis) for v in rect1]
        proj2 = [np.dot(v, axis) for v in rect2]
        if max(proj1) < min(proj2) or max(proj2) < min(proj1):
            return False
    return True


def _sagitta_collision(theta_array, L_list, b, w):
    """垂度判据：板凳内侧边缘超越相邻内圈螺线弧。
    
    物理模型：板凳为宽度 w 的矩形，中心线为螺线弦。
    弦偏离弧的最大垂度 sagitta = r_mid * (1 - cos(dtheta/2))
    板凳内侧边缘距离弧线 = sagitta + w/2
    相邻内圈螺线弧距离当前弧径向距离 = b
    碰撞条件：sagitta + w/2 >= b
    
    Args:
        theta_array: 全部把手极角数组。
        L_list: 板凳长度列表。
        b: 螺距系数。
        w: 板凳宽度。
    
    Returns:
        (is_collision, collision_info) 或 (False, {})
    """
    n = len(L_list)
    threshold = b - w / 2.0
    for i in range(n):
        theta_a = theta_array[i]
        theta_b = theta_array[i + 1]
        r_a = b * theta_a / (2.0 * np.pi)
        r_b = b * theta_b / (2.0 * np.pi)
        r_mid = (r_a + r_b) / 2.0
        dtheta = abs(theta_b - theta_a)
        sagitta = r_mid * (1.0 - np.cos(dtheta / 2.0))
        if sagitta >= threshold:
            return (True, {
                "type": "sagitta_overlap",
                "pair": (i, i + 1),
                "gap": threshold - sagitta,
                "threshold": threshold,
                "sagitta": sagitta,
                "r_mid": r_mid,
            })
    return (False, {})


def check_collision(theta_array, L_list, b=0.55, w=0.30):
    """碰撞判据检测。

    四重判据：
    1. 相邻板凳夹角判据：min(L_i, L_{i+1}) * sin(alpha_i) < w
    2. 非相邻板凳中心线距离判据：线段最短距离 < w（圈层剪枝：仅扫圈层差 <= 1）
    3. 矩形板凳重叠判据：相邻圈板凳矩形几何重叠（SAT）
    4. 垂度判据：板凳内侧边缘超越相邻内圈螺线弧（sagitta + w/2 >= b）

    Args:
        theta_array: 全部把手极角数组。
        L_list: 板凳长度列表。
        b: 螺距系数。
        w: 板凳宽度。

    Returns:
        (is_collision, collision_info): 是否碰撞 + 碰撞信息字典。
    """
    n = len(L_list)
    positions = [spiral_point(t, b) for t in theta_array]

    # 预计算每个把手的圈层编号
    turns = [t / (2.0 * np.pi) for t in theta_array]

    # 1. 相邻板凳夹角判据
    for i in range(n - 1):
        u_i = (positions[i][0] - positions[i + 1][0],
               positions[i][1] - positions[i + 1][1])
        u_next = (positions[i + 2][0] - positions[i + 1][0],
                  positions[i + 2][1] - positions[i + 1][1])

        norm_i = np.hypot(u_i[0], u_i[1])
        norm_next = np.hypot(u_next[0], u_next[1])
        if norm_i < 1e-15 or norm_next < 1e-15:
            continue

        cos_alpha = -(u_i[0] * u_next[0] + u_i[1] * u_next[1]) / (norm_i * norm_next)
        cos_alpha = max(-1.0, min(1.0, cos_alpha))
        sin_alpha = np.sqrt(max(0.0, 1.0 - cos_alpha * cos_alpha))

        L_min = min(L_list[i], L_list[i + 1])
        gap = L_min * sin_alpha
        if gap < w:
            return (True, {
                "type": "adjacent_angle",
                "pair": (i, i + 1),
                "gap": gap,
                "threshold": w,
            })

    # 2. 非相邻板凳中心线距离判据 + 3. 矩形重叠判据
    # 仅检查圈层差 <= 1 的板凳对（相邻圈）
    for i in range(n):
        turn_i = turns[i]
        for j in range(i + 2, n):
            turn_j = turns[j]
            turn_diff = abs(turn_j - turn_i)
            if turn_diff > 1.2:  # 超过相邻圈，剪枝
                break
            if turn_diff < 0.8:  # 同一圈或太近，非相邻圈
                continue

            p1 = positions[i]
            p2 = positions[i + 1]
            p3 = positions[j]
            p4 = positions[min(j + 1, n)]

            # 2. 中心线段距离
            dist = _segment_distance(p1, p2, p3, p4)
            if dist < w:
                return (True, {
                    "type": "non_adjacent_centerline",
                    "pair": (i, j),
                    "gap": dist,
                    "threshold": w,
                })

            # 3. 矩形重叠判据 (SAT)
            if _rect_collision_sat(p1, p2, p3, p4, w):
                # 计算净空用于报告
                d = np.array(p2) - np.array(p1)
                e = np.array(p4) - np.array(p3)
                denom = np.dot(d, d) * np.dot(e, e) - np.dot(d, e) ** 2
                clearance = 0.0
                if abs(denom) > 1e-18:
                    diff = np.array(p3) - np.array(p1)
                    t_param = (np.dot(d, e) * np.dot(diff, e) - np.dot(e, e) * np.dot(diff, d)) / denom
                    s = (np.dot(d, d) * np.dot(diff, e) - np.dot(d, e) * np.dot(diff, d)) / denom
                    t_param = max(0.0, min(1.0, t_param))
                    s = max(0.0, min(1.0, s))
                    cx = np.array(p1) + t_param * d
                    dx = np.array(p3) + s * e
                    clearance = np.linalg.norm(cx - dx) - w
                return (True, {
                    "type": "rectangular_overlap",
                    "pair": (i, j),
                    "gap": clearance,
                    "threshold": 0.0,
                })

    # 4. 垂度判据：板凳内侧边缘超越相邻内圈螺线弧
    # 物理含义：当龙头深入内圈，板凳弦线偏离螺线弧的垂度 + 半宽超过螺距时碰撞
    sag_coll, sag_info = _sagitta_collision(theta_array, L_list, b, w)
    if sag_coll:
        return (True, sag_info)

    return (False, {})


def point_to_segment_distance(px, py, x1, y1, x2, y2):
    """点 (px,py) 到线段 [(x1,y1),(x2,y2)] 的最短距离。"""
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) < 1e-15 and abs(dy) < 1e-15:
        return np.hypot(px - x1, py - y1)

    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx = x1 + t * dx
    cy = y1 + t * dy
    return np.hypot(px - cx, py - cy)