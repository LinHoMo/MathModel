% 多元回归模板（MATLAB / 北太天元交付分支）
% 交付分支：与 multiple_regression.py 数值等价，不产出 all_results.json
% 来源: 高教杯优秀论文 (B007, B026)
% 适用问题: 多因素回归分析、响应面建模、预测
% 输入: 特征矩阵 X、目标向量 y
% 输出: 回归系数、R²、预测值、残差

function [beta, stats, y_pred, residuals] = multiple_regression(X, y, opts)
% multiple_regression - 多元线性回归（含多项式特征扩展）
%   X:     n×p 特征矩阵
%   y:     n×1 目标向量
%   opts:  参数结构体（可选）
%
%   opts 字段:
%     degree     多项式阶数 (默认 1，即线性)
%     intercept  是否加截距 (默认 true)
%     cv_folds   交叉验证折数 (默认 0，不交叉验证)
%     seed       随机种子 (默认 42)

    if nargin < 3, opts = struct(); end

    degree    = getfield_or(opts, 'degree', 1);
    intercept = getfield_or(opts, 'intercept', true);
    cv_folds  = getfield_or(opts, 'cv_folds', 0);
    seed      = getfield_or(opts, 'seed', 42);

    rng(seed);

    [n, p] = size(X);

    % 多项式特征扩展
    if degree > 1
        X_exp = expand_polynomial(X, degree);
    else
        X_exp = X;
    end

    % 加截距
    if intercept
        X_exp = [ones(n, 1), X_exp];
    end

    % OLS 求解: beta = (X'X)^{-1} X'y
    beta = (X_exp' * X_exp) \ (X_exp' * y);

    % 拟合
    y_pred = X_exp * beta;
    residuals = y - y_pred;

    % 统计量
    SS_res = sum(residuals.^2);
    SS_tot = sum((y - mean(y)).^2);
    R2 = 1 - SS_res / SS_tot;
    R2_adj = 1 - (1 - R2) * (n - 1) / (n - size(X_exp, 2) - 1);
    RMSE = sqrt(mean(residuals.^2));

    stats = struct('R2', R2, 'R2_adj', R2_adj, 'RMSE', RMSE, ...
                   'SS_res', SS_res, 'SS_tot', SS_tot, ...
                   'n_features', size(X_exp, 2));

    fprintf('回归结果: R² = %.4f, R²_adj = %.4f, RMSE = %.4f\n', R2, R2_adj, RMSE);

    % 交叉验证
    if cv_folds > 1
        cv_rmse = cross_validate(X_exp, y, cv_folds);
        stats.CV_RMSE = cv_rmse;
        fprintf('交叉验证 RMSE (%d-fold): %.4f\n', cv_folds, cv_rmse);
    end
end

function X_exp = expand_polynomial(X, degree)
    [n, p] = size(X);
    cols = {};
    for d = 2:degree
        for j = 1:p
            cols{end+1} = X(:, j).^d;
        end
        if d == 2 && p >= 2
            for j1 = 1:p-1
                for j2 = j1+1:p
                    cols{end+1} = X(:, j1) .* X(:, j2);
                end
            end
        end
    end
    X_exp = [X, cell2mat(cols')];
end

function cv_rmse = cross_validate(X, y, k)
    n = length(y);
    idx = randperm(n);
    fold_size = floor(n / k);
    errors = zeros(k, 1);

    for i = 1:k
        test_idx = idx((i-1)*fold_size + 1 : min(i*fold_size, n));
        train_idx = setdiff(1:n, test_idx);

        X_tr = X(train_idx, :);
        y_tr = y(train_idx);
        X_te = X(test_idx, :);
        y_te = y(test_idx);

        beta = (X_tr' * X_tr) \ (X_tr' * y_tr);
        y_pred = X_te * beta;
        errors(i) = sqrt(mean((y_te - y_pred).^2));
    end
    cv_rmse = mean(errors);
end

function v = getfield_or(s, name, default)
    if isfield(s, name), v = s.(name); else, v = default; end
end

% ---- 示例 ----
function run_example()
    rng(42);
    n = 100;
    X = [randn(n, 1), randn(n, 1)];
    y = 3 + 2*X(:,1) - 1.5*X(:,2) + 0.5*X(:,1).*X(:,2) + 0.3*randn(n, 1);

    opts = struct('degree', 2, 'cv_folds', 5, 'seed', 42);
    [beta, stats, ~, ~] = multiple_regression(X, y, opts);

    fprintf('\n回归系数:\n');
    for i = 1:length(beta)
        fprintf('  beta(%d) = %.4f\n', i, beta(i));
    end
end
