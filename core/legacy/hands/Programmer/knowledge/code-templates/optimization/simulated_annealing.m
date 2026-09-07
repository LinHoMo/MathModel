% 模拟退火模板（MATLAB / 北太天元交付分支）
% 交付分支：与 simulated_annealing.py 数值等价，不产出 all_results.json
% 来源: 高教杯优秀论文 (A092)
% 适用问题: 组合优化、TSP、连续优化
% 输入: 目标函数、变量边界
% 输出: 最优解、最优值、温度历史

function [best_x, best_f, history] = simulated_annealing(objective, bounds, opts)
% simulated_annealing - 模拟退火求解器
%   objective:  目标函数句柄（最小化）
%   bounds:     N×2 矩阵，每行 [lb, ub]
%   opts:       参数结构体（可选）
%
%   opts 字段:
%     T0          初始温度 (默认 1000)
%     T_min       终止温度 (默认 1e-6)
%     cooling     降温系数 (默认 0.995)
%     n_steps     每温度步数 (默认 100)
%     step_scale  扰动步长占范围比 (默认 0.1)
%     seed        随机种子 (默认 42)

    if nargin < 3, opts = struct(); end

    T0         = getfield_or(opts, 'T0', 1000);
    T_min      = getfield_or(opts, 'T_min', 1e-6);
    cooling    = getfield_or(opts, 'cooling', 0.995);
    n_steps    = getfield_or(opts, 'n_steps', 100);
    step_scale = getfield_or(opts, 'step_scale', 0.1);
    seed       = getfield_or(opts, 'seed', 42);

    rng(seed);

    nvar = size(bounds, 1);
    lb   = bounds(:, 1)';
    ub   = bounds(:, 2)';

    % 初始解
    x = lb + (ub - lb) .* rand(1, nvar);
    f = objective(x);
    best_x = x;
    best_f = f;
    history = best_f;

    T = T0;
    while T > T_min
        for ~ = 1:n_steps
            % 高斯扰动
            dx = step_scale * (ub - lb) .* randn(1, nvar);
            x_new = x + dx;
            % 边界截断
            x_new = max(lb, min(ub, x_new));

            f_new = objective(x_new);
            delta = f_new - f;

            if delta < 0 || rand() < exp(-delta / T)
                x = x_new;
                f = f_new;
            end

            if f < best_f
                best_f = f;
                best_x = x;
            end
        end
        T = T * cooling;
        history(end+1) = best_f;
    end

    fprintf('SA finished. Best Fitness: %.6f\n', best_f);
end

function v = getfield_or(s, name, default)
    if isfield(s, name), v = s.(name); else, v = default; end
end

% ---- 示例 ----
function run_example()
    objective = @(x) (1 - x(1))^2 + 100*(x(2) - x(1)^2)^2;
    bounds = [-5 5; -5 5];
    opts = struct('T0', 1000, 'T_min', 1e-6, 'cooling', 0.995, 'seed', 42);

    [best_x, best_f, ~] = simulated_annealing(objective, bounds, opts);

    fprintf('\n最优解: [%.6f, %.6f]\n', best_x(1), best_x(2));
    fprintf('最优值: %.6f\n', best_f);
    fprintf('理论最优: [1, 1], f(x) = 0\n');
end
