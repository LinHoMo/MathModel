% 差分进化模板（MATLAB / 北太天元交付分支）
% 交付分支：与 differential_evolution.py 数值等价，不产出 all_results.json
% 来源: 高教杯优秀论文 (C038)
% 适用问题: 连续优化、参数辨识、多峰函数
% 输入: 目标函数、变量边界
% 输出: 最优解、最优值、收敛历史

function [best_x, best_f, history] = differential_evolution(objective, bounds, opts)
% differential_evolution - 差分进化求解器 (DE/rand/1/bin)
%   objective:  目标函数句柄（最小化）
%   bounds:     N×2 矩阵，每行 [lb, ub]
%   opts:       参数结构体（可选）
%
%   opts 字段:
%     pop_size    种群大小 (默认 50)
%     max_gen     最大代数 (默认 300)
%     F           缩放因子 (默认 0.8)
%     CR          交叉概率 (默认 0.9)
%     seed        随机种子 (默认 42)

    if nargin < 3, opts = struct(); end

    pop_size = getfield_or(opts, 'pop_size', 50);
    max_gen  = getfield_or(opts, 'max_gen', 300);
    F        = getfield_or(opts, 'F', 0.8);
    CR       = getfield_or(opts, 'CR', 0.9);
    seed     = getfield_or(opts, 'seed', 42);

    rng(seed);

    nvar = size(bounds, 1);
    lb   = bounds(:, 1)';
    ub   = bounds(:, 2)';

    % 初始化种群
    pop = repmat(lb, pop_size, 1) + ...
          repmat(ub - lb, pop_size, 1) .* rand(pop_size, nvar);
    fitness = arrayfun(@(i) objective(pop(i,:)), 1:pop_size);

    [best_f, best_idx] = min(fitness);
    best_x = pop(best_idx, :);
    history = best_f;

    for gen = 1:max_gen
        for i = 1:pop_size
            % 选 3 个互不相同的个体（不等于 i）
            pool = setdiff(1:pop_size, i);
            idxs = pool(randperm(length(pool), 3));
            a = pop(idxs(1), :);
            b = pop(idxs(2), :);
            c = pop(idxs(3), :);

            % 变异
            mutant = a + F * (b - c);

            % 交叉
            trial = pop(i, :);
            j_rand = randi(nvar);
            for j = 1:nvar
                if rand() < CR || j == j_rand
                    trial(j) = mutant(j);
                end
            end

            % 边界处理
            trial = max(lb, min(ub, trial));

            % 选择
            f_trial = objective(trial);
            if f_trial < fitness(i)
                pop(i, :) = trial;
                fitness(i) = f_trial;
                if f_trial < best_f
                    best_f = f_trial;
                    best_x = trial;
                end
            end
        end
        history(end+1) = best_f;

        if mod(gen, 50) == 0
            fprintf('Generation %d/%d, Best Fitness: %.6f\n', gen, max_gen, best_f);
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
    opts = struct('pop_size', 50, 'max_gen', 300, 'seed', 42);

    [best_x, best_f, ~] = differential_evolution(objective, bounds, opts);

    fprintf('\n最优解: [%.6f, %.6f]\n', best_x(1), best_x(2));
    fprintf('最优值: %.6f\n', best_f);
    fprintf('理论最优: [1, 1], f(x) = 0\n');
end
