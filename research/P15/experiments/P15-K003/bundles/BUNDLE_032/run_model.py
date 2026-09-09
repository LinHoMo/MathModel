"""2018_A 高温作业专用服装 — 一维四层瞬态热传导显式有限差分（自包含，纯标准库）。"""
import json
import math

def solve(inputs: dict) -> dict:
    # 四层材料参数 (k W/mK, rho*c J/m3K, thickness m)
    layers = [
        {"name": "I",   "k": 0.045, "rhoc": 1.2e6, "d": 0.006},
        {"name": "II",  "k": 0.055, "rhoc": 1.0e6, "d": 0.006},
        {"name": "III", "k": 0.065, "rhoc": 0.8e6, "d": 0.004},
        {"name": "IV",  "k": 0.028, "rhoc": 1.2e3, "d": 0.005},
    ]
    T_ambient = 75.0   # 环境温度 °C
    T_skin_init = 37.0  # 初始皮肤侧温度
    T_body = 37.0       # 体核温度
    h_conv = 8.0        # 皮肤侧对流系数 W/m2K
    total_time = 5400.0  # 90分钟 = 5400秒
    dx = 0.0005          # 空间步长 0.5mm

    # 构建网格
    xs = []
    layer_idx = []
    x = 0.0
    for li, layer in enumerate(layers):
        n_pts = int(round(layer["d"] / dx))
        for i in range(n_pts):
            xs.append(x)
            layer_idx.append(li)
            x += dx
    N = len(xs)
    L = x

    # 时间步长（稳定性：dt <= dx^2 / (2*alpha_max)）
    alpha_max = max(l["k"] / l["rhoc"] for l in layers)
    dt = 0.25 * dx * dx / alpha_max
    n_steps = int(math.ceil(total_time / dt))

    # 初始化温度场
    T = [T_skin_init] * N
    T[0] = T_ambient  # 左边界Dirichlet

    skin_temps = []  # 记录皮肤侧温度随时间
    sample_interval = max(1, n_steps // 100)

    for step in range(n_steps):
        T_new = T[:]
        T_new[0] = T_ambient  # 左边界固定环境温度
        # 内部节点显式更新（层间界面用调和平均热扩散率）
        for i in range(1, N - 1):
            li = layer_idx[i]
            k = layers[li]["k"]
            rhoc = layers[li]["rhoc"]
            alpha = k / rhoc
            # 层间界面处理：用相邻层k的调和平均
            if layer_idx[i - 1] != li:
                k_left = layers[layer_idx[i - 1]]["k"]
                k_eff = 2 * k * k_left / (k + k_left)
                alpha = k_eff / rhoc
            elif layer_idx[i + 1] != li:
                k_right = layers[layer_idx[i + 1]]["k"]
                k_eff = 2 * k * k_right / (k + k_right)
                alpha = k_eff / rhoc
            T_new[i] = T[i] + alpha * dt / (dx * dx) * (T[i + 1] - 2 * T[i] + T[i - 1])
        # 右边界：对流边界（皮肤侧与体核换热）
        i = N - 1
        li = layer_idx[i]
        k = layers[li]["k"]
        rhoc = layers[li]["rhoc"]
        # Neumann型对流：-k dT/dx = h(T - T_body)
        # 用ghost node方法
        T_ghost = T[i - 1] + 2 * dx * h_conv / k * (T_body - T[i])
        alpha = k / rhoc
        T_new[i] = T[i] + alpha * dt / (dx * dx) * (T_ghost - 2 * T[i] + T[i - 1])
        T = T_new
        if step % sample_interval == 0 or step == n_steps - 1:
            t = (step + 1) * dt
            skin_temps.append({"time_s": round(t, 1), "temp_C": round(T[N - 1], 3)})

    T_skin_final = T[N - 1]
    T_skin_max = max(s["temp_C"] for s in skin_temps)
    # 超过44°C的时间
    time_above_44 = 0.0
    for j in range(1, len(skin_temps)):
        if skin_temps[j]["temp_C"] > 44.0:
            dt_sample = skin_temps[j]["time_s"] - skin_temps[j - 1]["time_s"]
            time_above_44 += dt_sample

    return {
        "skin_temp_final": round(T_skin_final, 3),
        "skin_temp_max": round(T_skin_max, 3),
        "time_above_44C_s": round(time_above_44, 1),
        "time_above_44C_min": round(time_above_44 / 60.0, 2),
        "total_thickness_m": round(L, 5),
        "n_grid_points": N,
        "n_time_steps": n_steps,
        "dt_s": round(dt, 4),
        "temperature_curve": skin_temps[::max(1, len(skin_temps) // 20)],
        "ambient_temp": T_ambient,
        "duration_s": total_time,
    }

if __name__ == "__main__":
    print(json.dumps(solve({}), ensure_ascii=False))
