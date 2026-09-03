% 遗传算法模板（MATLAB / 北太天元交付分支）
% 交付分支：与 genetic_algorithm.py 数值等价，不产出 all_results.json
% 来源: 高教杯优秀论文 (A001, A028, A070)
% 适用问题: 连续优化、离散优化、多峰函数、整数规划
% 输入: 目标函数、约束、变量边界
% 输出: 最优解、最优值、收敛历史

function [best_x, best_f, history] = genetic_algorithm(objective, bounds, opts)
% genetic_algorithm - 遗传算法求解器
%   objective:  目标函数句柄（最小化）
%   bounds:     N×2 矩阵，每行 [lb, ub]
%   opts:       参数结构体（可选）
%
%   opts 字段:
%     pop_size       种群大小 (默认 100)
%     max_gen        最大代数 (默认 200)
%     crossover_rate 交叉概率 (默认 0.8)
%     mutation_rate  变异概率 (默认 0.1)
%     tournament_k   锦标赛选择大小 (默认 3)
%     constraints    约束函数 cell array，每个返回 >=0 表示可行
%     seed           随机种子 (默认 42)

    if nargin < 3, opts = struct(); end

    pop_size       = getfield_or(opts, 'pop_size', 100);
    max_gen        = getfield_or(opts, 'max_gen', 200);
    cr             = getfield_or(opts, 'crossover_rate', 0.8);
    mr             = getfield_or(opts, 'mutation_rate', 0.1);
    tsize          = getfield_or(opts, 'tournament_k', 3);
    constraints    = getfield_or(opts, 'constraints', {});
    seed           = getfield_or(opts, 'seed', 42);

    rng(seed);

    nvar = size(bounds, 1);
    lb   = bounds(:, 1)';
    ub   = bounds(:, 2)';

    % --- 初始化种群 ---
    pop = repmat(lb, pop_size, 1) + ...
          repmat(ub - lb, pop_size, 1) .* rand(pop_size, nvar);

    fitness = eval_fitness(pop, objective, constraints);
    [best_f, best_idx] = min(fitness);
    best_x = pop(best_idx, :);
    history = best_f;

    for gen = 1:max_gen
        % 锦标赛选择
        selected = zeros(pop_size, nvar);
        for i = 1:pop_size
            cands = randperm(pop_size, tsize);
            [~, w] = min(fitness(cands));
            selected(i, :) = pop(cands(w), :);
        end

        % 交叉 + 变异
        new_pop = zeros(pop_size, nvar);
        for i = 1:2:pop_size
            p1 = selected(i, :);
            p2 = selected(min(i+1, pop_size), :);
            [c1, c2] = sbx_crossover(p1, p2, lb, ub, cr);
            c1 = gauss_mutate(c1, lb, ub, mr);
            c2 = gauss_mutate(c2, lb, ub, mr);
            new_pop(i, :) = c1;
            if i + 1 <= pop_size
                new_pop(i+1, :) = c2;
            end
        end

        % 精英保留
        [~, worst_idx] = max(fitness);
        new_pop(worst_idx, :) = best_x;

        pop = new_pop;
        fitness = eval_fitness(pop, objective, constraints);

        [gen_best, gen_idx] = min(fitness);
        if gen_best < best_f
            best_f = gen_best;
            best_x = pop(gen_idx, :);
        end
        history(end+1) = best_f;

        if mod(gen, 50) == 0
            fprintf('Generation %d/%d, Best Fitness: %.6f\n', gen, max_gen, best_f);
        end
    end
end

% ---- 内部函数 ----

function f = eval_fitness(pop, objective, constraints)
    n = size(pop, 1);
    f = zeros(n, 1);
    for i = 1:n
        x = pop(i, :);
        f(i) = objective(x);
        pen = 0;
        for j = 1:length(constraints)
            v = max(0, -constraints{j}(x));
            pen = pen + v^2;
        end
        f(i) = f(i) + 1000 * pen;
    end
end

function [c1, c2] = sbx_crossover(p1, p2, lb, ub, cr)
    c1 = p1; c2 = p2;
    if rand() > cr, return; end
    eta = 20;
    for i = 1:length(p1)
        if rand() < 0.5, continue; end
        u = rand();
        if u <= 0.5
            beta = (2*u)^(1/(eta+1));
        else
            beta = (1/(2*(1-u)))^(1/(eta+1));
        end
        c1(i) = 0.5 * ((1+beta)*p1(i) + (1-beta)*p2(i));
        c2(i) = 0.5 * ((1-beta)*p1(i) + (1+beta)*p2(i));
    end
    for i = 1:length(lb)
        c1(i) = max(lb(i), min(ub(i), c1(i)));
        c2(i) = max(lb(i), min(ub(i), c2(i)));
    end
end

function m = gauss_mutate(x, lb, ub, mr)
    m = x;
    for i = 1:length(x)
        if rand() < mr
            sigma = (ub(i) - lb(i)) * 0.1;
            m(i) = m(i) + sigma * randn();
            m(i) = max(lb(i), min(ub(i), m(i)));
        end
    end
end

function v = getfield_or(s, name, default)
    if isfield(s, name)
        v = s.(name);
    else
        v = default;
    end
end

% ---- 示例 ----
function run_example()
    objective = @(x) (1 - x(1))^2 + 100*(x(2) - x(1)^2)^2;
    bounds = [-5 5; -5 5];
    opts = struct('pop_size', 100, 'max_gen', 200, 'seed', 42);

    [best_x, best_f, history] = genetic_algorithm(objective, bounds, opts);

    fprintf('\n最优解: [%.6f, %.6f]\n', best_x(1), best_x(2));
    fprintf('最优值: %.6f\n', best_f);
    fprintf('理论最优: [1, 1], f(x) = 0\n');

    figure('Name', 'GA Convergence');
    plot(0:length(history)-1, history, 'b-', 'LineWidth', 2);
    xlabel('Generation'); ylabel('Best Fitness');
    title('Genetic Algorithm Convergence');
    grid on;
end
