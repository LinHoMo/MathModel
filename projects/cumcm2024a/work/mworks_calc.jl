# MWORKS/Syslab 板凳龙图片生成 —— 计算与验证部分
# 等距螺线 r = b*theta/(2pi)，链式约束递推，与 code/solve.py 同公式
using Printf

# ---- 参数（与 all_results.json / solve.py 一致）----
const B = 0.55          # 螺距 (m)
const V1 = 1.0          # 龙头速度 (m/s)
const R0 = 8.8          # 初始极径 (m)
const THETA_0 = 32 * pi # 初始极角 (rad)
const N_BENCH = 222     # 板凳总数
const L_HEAD = 3.41     # 龙头板凳长 (m)
const L_BODY = 2.20     # 龙身板凳长 (m)
const W = 0.30          # 板凳宽 (m)

a_coef(b) = b / (2 * pi)

spiral_r(theta, b) = a_coef(b) * theta
spiral_point(theta, b) = begin
    r = spiral_r(theta, b)
    (r * cos(theta), r * sin(theta))
end
spiral_tangent(theta, b) = begin
    a = a_coef(b)
    (a * (cos(theta) - theta * sin(theta)),
     a * (sin(theta) + theta * cos(theta)))
end
spiral_tangent_norm(theta, b) = a_coef(b) * sqrt(1 + theta^2)

function spiral_arc_length(theta, b)
    a = a_coef(b)
    a / 2 * (theta * sqrt(1 + theta^2) + log(theta + sqrt(1 + theta^2)))
end

function inverse_arc_length(s_target, b; tol=1e-10)
    lo, hi = 0.0, 200.0
    while spiral_arc_length(hi, b) < s_target
        hi *= 2.0
    end
    for _ in 1:200
        mid = (lo + hi) / 2.0
        sm = spiral_arc_length(mid, b)
        if abs(sm - s_target) < tol
            return mid
        elseif sm < s_target
            lo = mid
        else
            hi = mid
        end
    end
    (lo + hi) / 2.0
end

function solve_chain_thetas(theta_head, L_list, b; delta=0.5, tol=1e-10)
    n = length(L_list)
    theta = zeros(n + 1)
    theta[1] = theta_head
    for i in 2:(n + 1)
        theta_prev = theta[i - 1]
        L_i = L_list[i - 1]
        lo = theta_prev + 1e-12
        hi = theta_prev + delta
        for _ in 1:50
            (xh, yh) = spiral_point(hi, b)
            (xl, yl) = spiral_point(lo, b)
            dist_hi = hypot(xh - xl, yh - yl)
            if dist_hi >= L_i
                break
            end
            hi += delta
        end
        for _ in 1:200
            mid = (lo + hi) / 2.0
            (xm, ym) = spiral_point(mid, b)
            (xp, yp) = spiral_point(theta_prev, b)
            dist = hypot(xm - xp, ym - yp)
            if abs(dist - L_i) < tol
                break
            elseif dist < L_i
                lo = mid
            else
                hi = mid
            end
        end
        theta[i] = (lo + hi) / 2.0
    end
    theta
end

function chain_velocities(theta_array, dtheta_head, b)
    n = length(theta_array) - 1
    dtheta = zeros(n + 1)
    dtheta[1] = dtheta_head
    for i in 2:(n + 1)
        (xi, yi) = spiral_point(theta_array[i], b)
        (xp, yp) = spiral_point(theta_array[i - 1], b)
        ux = xi - xp
        uy = yi - yp
        (txp, typ) = spiral_tangent(theta_array[i - 1], b)
        (txi, tyi) = spiral_tangent(theta_array[i], b)
        numerator = ux * txp + uy * typ
        denominator = ux * txi + uy * tyi
        if abs(denominator) < 1e-12
            denominator = denominator >= 0 ? 1e-12 : -1e-12
        end
        dtheta[i] = (numerator / denominator) * dtheta[i - 1]
    end
    speed = zeros(n + 1)
    for i in 1:(n + 1)
        speed[i] = abs(dtheta[i]) * spiral_tangent_norm(theta_array[i], b)
    end
    speed
end

function solve_chain_out_robust(phi_head, L_list, b; tol=1e-10)
    n = length(L_list)
    phi = zeros(n + 1)
    phi[1] = phi_head
    for i in 2:(n + 1)
        phi_prev = phi[i - 1]
        L_i = L_list[i - 1]
        norm_prev = spiral_tangent_norm(abs(phi_prev), b)
        dphi_est = L_i / norm_prev
        if i >= 3
            dphi_prev = abs(phi[i - 1] - phi[i - 2])
            dphi_est = 0.5 * dphi_est + 0.5 * dphi_prev
        end
        phi_est = phi_prev - dphi_est
        lo = phi_est - 1.0
        hi = min(phi_est + 0.5, phi_prev - 1e-12)
        dist(pa, pb) = begin
            (xa, ya) = spiral_point(abs(pa), b)
            (xb, yb) = spiral_point(abs(pb), b)
            hypot(xa - xb, ya - yb)
        end
        d_lo = dist(lo, phi_prev)
        d_hi = dist(hi, phi_prev)
        expand = 0
        while d_lo < L_i && d_hi < L_i && expand < 100
            lo -= 1.0
            d_lo = dist(lo, phi_prev)
            expand += 1
        end
        for _ in 1:200
            mid = (lo + hi) / 2.0
            d_mid = dist(mid, phi_prev)
            if abs(d_mid - L_i) < tol
                break
            elseif d_mid < L_i
                hi = mid
            else
                lo = mid
            end
        end
        phi[i] = (lo + hi) / 2.0
    end
    phi
end

# ---- 计算各图数据 ----
L_list = vcat(L_HEAD, [L_BODY for _ in 1:(N_BENCH - 1)])
s0 = spiral_arc_length(THETA_0, B)

# Fig1: t=0,100,200,300 盘入构型
times1 = [0, 100, 200, 300]
fig1_data = []
for t in times1
    s_target = s0 - V1 * t
    theta_head = inverse_arc_length(s_target, B)
    theta_arr = solve_chain_thetas(theta_head, L_list, B)
    pts = [spiral_point(th, B) for th in theta_arr]
    push!(fig1_data, (t, pts))
end

# Fig2: 碰撞时刻 t*=412.83
t_star = 412.83
s_target2 = s0 - V1 * t_star
theta_head2 = inverse_arc_length(s_target2, B)
theta_arr2 = solve_chain_thetas(theta_head2, L_list, B)
pts2 = [spiral_point(th, B) for th in theta_arr2]

# 验证: 龙头位置应接近 all_results.json problem_2.head_pos_at_t_star=[1.488096, 1.720932]
println("Fig2 head pos at t*: ", round.(pts2[1], digits=6))
println("Fig2 head r at t*:   ", round(spiral_r(theta_arr2[1], B), digits=6))
println("Fig2 tail pos at t*: ", round.(pts2[end], digits=6))

# Fig1 验证: t=300 龙头位置应接近 [4.420274, 2.320429]
println("Fig1 t=300 head pos: ", round.(fig1_data[4][2][1], digits=6))
println("Fig1 t=0   head pos: ", round.(fig1_data[1][2][1], digits=6))
println("Fig1 t=0   tail pos: ", round.(fig1_data[1][2][end], digits=6))

# Fig4: 盘出速度分布 t=407
r_start = 2.27509  # all_results problem_3.r_collision
phi_head407 = inverse_arc_length(spiral_arc_length(r_start / a_coef(B), B) + V1 * 407.0, B)
phi_arr407 = solve_chain_out_robust(phi_head407, L_list, B)
dphi_head407 = V1 / spiral_tangent_norm(phi_head407, B)
speeds407 = chain_velocities(phi_arr407, dphi_head407, B)
vmax, idxmax = findmax(speeds407)
println("Fig4 v_max: ", round(vmax, digits=6), " at handle ", idxmax - 1)
println("Fig4 pos at vmax: ", round.((-spiral_point(abs(phi_arr407[idxmax]), B)[1], -spiral_point(abs(phi_arr407[idxmax]), B)[2]), digits=6))

# 保存数据供绘图脚本使用
using JSON
dat = Dict(
    "fig1" => [[t, [collect(p) for p in pts]] for (t, pts) in fig1_data],
    "fig2" => [collect(p) for p in pts2],
    "fig4_phi" => collect(phi_arr407),
    "fig4_speed" => collect(speeds407),
    "t_star" => t_star,
)
open("C:/Users/Lin/Desktop/Programs/MathModel/projects/cumcm2024a/work/figdata.json", "w") do f
    JSON.print(f, dat)
end
println("figdata.json saved")
