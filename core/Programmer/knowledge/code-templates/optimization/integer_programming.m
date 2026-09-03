% 整数规划模板（MATLAB / 北太天元交付分支）
% 交付分支：与 integer_programming.py 数值等价，不产出 all_results.json
% 来源: 高教杯优秀论文 (D001, D042)
% 适用问题: 混合整数线性规划、0-1 规划、指派问题
% 输入: 目标系数、约束矩阵、变量类型
% 输出: 最优解、最优值

function [x, fval, exitflag] = integer_programming(f, Aineq, bineq, Aeq, beq, lb, ub, intcon, opts)
% integer_programming - 混合整数线性规划（调用 intlinprog）
%   f:       目标系数向量（最小化 f'*x）
%   Aineq:   不等式约束矩阵 A*x <= b
%   bineq:   不等式右侧
%   Aeq:     等式约束矩阵 Aeq*x = beq
%   beq:     等式右侧
%   lb:      下界
%   ub:      上界
%   intcon:  整数变量索引向量（如 [1 2 3] 表示 x(1),x(2),x(3) 为整数）
%   opts:    参数结构体（可选）
%
%   北太天元兼容: intlinprog 在 BDT 中可用（Optimization Toolbox 等价）

    if nargin < 9, opts = struct(); end

    % 默认值处理
    if isempty(Aineq), Aineq = []; bineq = []; end
    if isempty(Aeq),   Aeq = [];   beq = []; end
    if isempty(lb),    lb = zeros(length(f), 1); end
    if isempty(ub),    ub = []; end
    if isempty(intcon), intcon = 1:length(f); end

    % 设置选项
    options = optimoptions('intlinprog', 'Display', 'off');
    if isfield(opts, 'max_time')
        options = optimoptions(options, 'MaxTime', opts.max_time);
    end

    [x, fval, exitflag] = intlinprog(f, intcon, Aineq, bineq, Aeq, beq, lb, ub, options);

    if exitflag > 0
        fprintf('整数规划求解成功。最优值: %.6f\n', fval);
    else
        fprintf('整数规划求解失败。exitflag = %d\n', exitflag);
    end
end

% ---- 示例：背包问题 ----
function run_example()
    % 0-1 背包：10 件物品，容量 200
    n = 10;
    values  = [92 57 49 68 60 43 67 84 87 72];
    weights = [23 31 29 44 53 38 63 85 89 82];
    capacity = 200;

    % 最大化价值 → 最小化 -价值
    f = -values';

    % 重量约束
    Aineq = weights;
    bineq = capacity;

    % 0-1 变量
    lb = zeros(n, 1);
    ub = ones(n, 1);
    intcon = 1:n;

    [x, fval, ~] = integer_programming(f, Aineq, bineq, [], [], lb, ub, intcon);

    fprintf('\n选择物品: ');
    fprintf('%d ', find(x > 0.5));
    fprintf('\n总价值: %.0f\n', -fval);
    fprintf('总重量: %.0f / %d\n', weights * x, capacity);
end
