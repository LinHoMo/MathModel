% 粒子群优化模板（MATLAB / 北太天元交付分支）
% 交付分支：与 particle_swarm.py 数值等价，不产出 all_results.json
% 来源: 高教杯优秀论文 (A070, C038)
% 适用问题: 连续优化、参数寻优、多峰函数
% 输入: 目标函数、变量边界
% 输出: 最优解、最优值、收敛历史

function [gbest_x, gbest_f, history] = particle_swarm(objective, bounds, opts)
% particle_swarm - 粒子群优化求解器
%   objective:  目标函数句柄（最小化）
%   bounds:     N×2 矩阵，每行 [lb, ub]
%   opts:       参数结构体（可选）
%
%   opts 字段:
%     n_particles  粒子数 (默认 50)
%     max_iter     最大迭代 (默认 300)
%     w            惯性权重 (默认 0.7)
%     c1           个体学习因子 (默认 1.5)
%     c2           社会学习因子 (默认 1.5)
%     seed         随机种子 (默认 42)

    if nargin < 3, opts = struct(); end

    n_particles = getfield_or(opts, 'n_particles', 50);
    max_iter    = getfield_or(opts, 'max_iter', 300);
    w           = getfield_or(opts, 'w', 0.7);
    c1          = getfield_or(opts, 'c1', 1.5);
    c2          = getfield_or(opts, 'c2', 1.5);
    seed        = getfield_or(opts, 'seed', 42);

    rng(seed);

    nvar = size(bounds, 1);
    lb   = bounds(:, 1)';
    ub   = bounds(:, 2)';

    % 初始化位置与速度
    pos = repmat(lb, n_particles, 1) + ...
          repmat(ub - lb, n_particles, 1) .* rand(n_particles, nvar);
    vel = 0.1 * (ub - lb) .* (2*rand(n_particles, nvar) - 1);

    pbest_pos = pos;
    pbest_val = arrayfun(@(i) objective(pos(i,:)), 1:n_particles);
    [gbest_f, gbest_idx] = min(pbest_val);
    gbest_x = pbest_pos(gbest_idx, :);
    history = gbest_f;

    for iter = 1:max_iter
        r1 = rand(n_particles, nvar);
        r2 = rand(n_particles, nvar);

        vel = w * vel + c1 * r1 .* (pbest_pos - pos) + ...
              c2 * r2 .* (repmat(gbest_x, n_particles, 1) - pos);

        pos = pos + vel;

        % 边界反弹
        for d = 1:nvar
            below = pos(:,d) < lb(d);
            above = pos(:,d) > ub(d);
            pos(below, d) = lb(d);
            pos(above, d) = ub(d);
            vel(below, d) = 0;
            vel(above, d) = 0;
        end

        for i = 1:n_particles
            fval = objective(pos(i, :));
            if fval < pbest_val(i)
                pbest_val(i) = fval;
                pbest_pos(i, :) = pos(i, :);
            end
            if fval < gbest_f
                gbest_f = fval;
                gbest_x = pos(i, :);
            end
        end

        history(end+1) = gbest_f;

        if mod(iter, 50) == 0
            fprintf('Iteration %d/%d, Best Fitness: %.6f\n', iter, max_iter, gbest_f);
        end
    end
end

function v = getfield_or(s, name, default)
    if isfield(s, name), v = s.(name); else, v = default; end
end

% ---- 示例 ----
function run_example()
    objective = @(x) (1 - x(1))^2 + 100*(x(2) - x(1)^2)^2;
    bounds = [-5 5; -5 5];
    opts = struct('n_particles', 50, 'max_iter', 300, 'seed', 42);

    [gbest_x, gbest_f, ~] = particle_swarm(objective, bounds, opts);

    fprintf('\n最优解: [%.6f, %.6f]\n', gbest_x(1), gbest_x(2));
    fprintf('最优值: %.6f\n', gbest_f);
    fprintf('理论最优: [1, 1], f(x) = 0\n');
end
