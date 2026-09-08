# 测试设计指南

本文档提供 MATLAB 到 Julia 转换的功能和性能测试策略。

---

## 一、核心原则

**不追求 100% 路径覆盖，聚焦关键路径测试。**

---

## 二、测试策略选择

| 场景 | 测试策略 | 参考章节 |
|------|----------|----------|
| 无测试用例 | 从原代码提取或生成测试数据 | 第三至五节 |
| 已有测试用例 | 复用现有测试，转换后对比 | 第六节 |

---

## 三、测试数据来源

### 3.1 从原代码提取（推荐）

| 来源 | 提取方法 |
|------|----------|
| 硬编码常量 | 搜索赋值语句 `N = 1000;` |
| .mat 文件 | 直接使用 `load` 语句引用的数据文件 |
| 示例数据 | 分析主脚本的数据初始化部分 |
| 函数调用实参 | 追踪调用链，记录传入参数 |
| 注释示例 | 解析 `% 示例:`、`% Example:` 注释 |

### 3.2 生成测试数据

| 类型 | 生成策略 |
|------|----------|
| 典型值 | 根据参数类型生成合理范围值 |
| 边界值 | 0、1、最大值、最小值、空数组 |
| 异常值 | NaN、Inf、空值 |

---

## 四、测试执行方法

### 4.1 分层测试策略

| 层级 | 内容 | 耗时 |
|------|------|------|
| 冒烟测试 | 主入口脚本能否运行 | 5-10 分钟 |
| 关键路径测试 | 核心算法计算结果一致性 | 30 分钟 |
| 回归测试 | 全量函数覆盖（可选） | - |

### 4.2 不同规模项目策略

| 项目规模 | 测试策略 |
|----------|----------|
| 小型（<10 文件） | 主入口 + 关键函数 |
| 中型（10-50 文件） | 关键路径 + 问题模块 |
| 大型（>50 文件） | 仅测试入口 + 核心算法 |

### 4.3 MATLAB 端捕获基准数据

```matlab
% 创建测试脚本保存基准数据
function benchmark_xxx()
    N = 1000;
    SNR_dB = 10;
    [result, key_metrics] = original_function(N, SNR_dB);
    save('benchmark_xxx.mat');
end
```

### 4.4 Julia 端对比测试

```julia
using MAT
benchmark = matread("benchmark_xxx.mat")

result, key_metrics = converted_function(benchmark["N"], benchmark["SNR_dB"])

# 对比关键指标
@show abs(benchmark["BER"] - key_metrics["BER"]) / benchmark["BER"]
```

### 4.5 关键指标测试优先级

| 优先级 | 内容 |
|--------|------|
| 必须测试 | 核心算法输出（BER、SNR）、最终结果 |
| 建议测试 | 中间计算结果、收敛条件 |
| 可选测试 | 调试日志、进度输出 |

---

## 五、容差与判定标准

### 5.1 默认容差

| 指标类型 | 相对误差 | 绝对误差 |
|----------|----------|----------|
| BER/PER/FER | < 1e-6 | < 1e-9 |
| SNR (dB) | < 0.1 | < 0.01 |
| MSE/RMSE | < 1e-8 | < 1e-12 |
| 其他数值 | < 1e-6 | < 1e-9 |

### 5.2 判定标准

| 结果 | 判定条件 | 处理方式 |
|------|----------|----------|
| ✅ 通过 | 相对误差 < 容差 | 标记为已测试 |
| ⚠️ 近似 | 误差略超但结果合理 | 记录偏差，标记可接受 |
| ❌ 失败 | 误差显著超限 | 记录问题，进入问题清单 |

### 5.3 常见陷阱

| 陷阱 | 解决方案 |
|------|----------|
| 随机数不一致 | 固定种子：MATLAB `rng default;rand(2,3)`，Julia `rng = TyRandom.MT19937ar(5489);rand(rng,2,3)` |
| 浮点精度差异 | 使用相对误差而非绝对相等 |
| 默认参数不同 | 显式指定所有参数 |
| 全局变量状态 | 测试前后重置全局变量 |

---

## 六、已有测试用例复用

当 MATLAB 工程已包含测试用例时，直接复用现有测试资源。

### 6.1 测试资源识别

| 资源类型 | 识别模式 | 利用策略 |
|----------|----------|----------|
| 测试脚本 | `test_*.m`、`*_test.m` | 直接转换为 Julia 测试 |
| 测试数据 | `.mat` 文件、`testdata/` 目录 | 直接复用 |
| 单元测试 | MATLAB 单元测试框架 | 转换为 Julia `@test` |
| 示例脚本 | `example_*.m`、`demo_*.m` | 作为集成测试 |

### 6.2 测试转换对照

| MATLAB | Julia |
|--------|-------|
| `verifyEqual(testCase, a, b)` | `@test a == b` |
| `verifyAlmostEqual(testCase, a, b)` | `@test isapprox(a, b, rtol=1e-6)` |
| `assertTrue(testCase, cond)` | `@test cond == true` |
| `verifyError(testCase, ...)` | `@test_throws ErrorType expr` |

### 6.3 测试数据复用

```julia
using MAT
test_data = matread("test_data.mat")

actual = converted_function(test_data["input"])
@test isapprox(actual, test_data["expected"], rtol=1e-6)
```

### 6.4 测试覆盖补充建议

| 情况 | 建议 |
|------|------|
| 测试覆盖不足 | 补充关键路径测试 |
| 无关键指标验证 | 添加核心指标断言 |
| 仅单元测试 | 补充端到端集成测试 |

---

## 七、特殊情况处理

| 情况 | 处理方法 |
|------|----------|
| 无 .mat 文件 | 提取硬编码参数或生成典型值 |
| 随机算法 | 固定种子，测试统计特性 |

---

## 八、性能测试设计

### 8.1 性能测试目标

验证 Julia 代码在**真实数据量**下的执行效率**优于** MATLAB。

### 8.2 测试数据量级设计

**核心原则**：覆盖 4 个以上数量级，消除 JIT 编译影响。

| 量级 | 数据规模 | 用途 | 执行次数 |
|------|----------|------|----------|
| 小量级 | 10³ ~ 10⁴ | 快速验证功能正确性 | 1 次 |
| 中量级 | 10⁴ ~ 10⁵ | 性能对比基准 | 3-5 次 |
| 大量级 | 10⁵ ~ 10⁷ | 真实场景性能验证 | 3-5 次 |
| 超大量级 | 10⁷ ~ 10⁹ | 大规模数据处理测试 | 1-2 次 |
| 极限量级 | 10⁹ ~ 10¹¹ | 压力测试（可选） | 1 次 |

**量级选择依据**：

| 项目类型 | 推荐量级组合 | 说明 |
|----------|--------------|------|
| 信号处理 | 小/中/大/超大 | 采样点数：10000/100000/1000000/10000000 |
| 通信仿真 | 小/中/大/超大 | 比特数：10000/100000/1000000/10000000 |
| 图像处理 | 小/中/大 | 像素：512×512/4096×4096/16384×16384 |
| 控制系统 | 小/中 | 仿真步数：1000/10000 |
| 优化算法 | 小/中/大/超大 | 迭代次数：1000/10000/100000/1000000 |

### 8.3 性能测试前置验证（强制要求）

**核心原则**：先验证功能正确性，再进行性能对比。

每个量级必须执行以下流程：

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: MATLAB 执行 → 保存输出结果                              │
│  Step 2: Julia 执行 → 对比输出结果                               │
│  Step 3: 功能验证通过 → 方可进行性能计时                          │
│  Step 4: 功能验证失败 → 排查问题，禁止继续性能测试                 │
│  Step 5: Julia 性能低于 MATLAB → 记录问题，继续剩余用例测试        │
└─────────────────────────────────────────────────────────────────┘
```

**验证要求**：

| 量级 | 功能验证要求 | 验证通过后操作 |
|------|--------------|----------------|
| 小量级 | **必须**验证核心输出指标 | 可跳过性能计时 |
| 中量级 | **必须**验证核心输出指标 | 开始性能对比 |
| 大量级 | **必须**验证核心输出指标 | 开始性能对比 |
| 超大量级 | **必须**验证核心输出指标 | 开始性能对比 |
| 极限量级 | 建议验证核心输出指标 | 开始性能对比 |

**验证脚本示例**：

```julia
# 每个量级先验证功能，再计时
for N in data_sizes
    # Step 1: 读取 MATLAB 基准数据
    matlab_result = matread("benchmark_N$(N).mat")

    # Step 2: Julia 执行
    julia_result = test_function(N)

    # Step 3: 功能验证
    relative_error = abs(matlab_result["output"] - julia_result) / matlab_result["output"]
    if relative_error > tolerance
        error("功能验证失败: N=$N, 相对误差=$relative_error > $tolerance")
    end

    # Step 4: 功能通过后，进行性能计时
    times = Float64[]
    for run in 1:num_runs
        start_time = time()
        _ = test_function(N)
        push!(times, time() - start_time)
    end
    # ... 记录性能数据
end
```

**禁止行为**：

| 禁止项 | 原因 |
|--------|------|
| 跳过功能验证直接计时 | 性能数据无意义，可能掩盖功能错误 |
| 仅验证小量级就测全部性能 | 大数据量可能暴露新问题 |
| 功能失败后继续性能测试 | 违背测试目的，浪费资源 |

### 8.4 JIT 预热处理

**问题**：Julia 首次执行包含 JIT 编译开销，不能用于性能对比。

**解决方案**：

```julia
# 预热执行（不计入性能数据）
warmup_result = test_function(small_data)

# 正式计时
times = Float64[]
for i in 1:5
    start_time = time()
    result = test_function(test_data)
    push!(times, time() - start_time)
end

# 取中位数或平均值
avg_time = sum(times) / length(times)
median_time = sort(times)[length(times) ÷ 2 + 1]
```

**预热规则**：
- 预热数据量：小量级即可
- 预热次数：至少 1 次
- 正式测量：取 3-5 次的平均值或中位数

### 8.5 基准测试脚本模板

**MATLAB 端**：
```matlab
% benchmark_xxx.m
function results = benchmark_xxx()
    % 测试参数
    data_sizes = [10000, 100000, 1000000, 10000000];
    num_runs = 5;

    results = struct();

    for N = data_sizes
        times = zeros(num_runs, 1);

        % 生成测试数据
        test_data = generate_test_data(N);

        for run = 1:num_runs
            tic;
            output = core_function(test_data);
            times(run) = toc;
        end

        results.(['N_' num2str(N)]) = struct(...
            'mean_time', mean(times), ...
            'median_time', median(times), ...
            'std_time', std(times), ...
            'all_times', times);
    end

    save('benchmark_xxx.mat', 'results');
end
```

**Julia 端**：
```julia
# benchmark_xxx.jl
using Random
using Statistics

function benchmark_xxx()
    # 测试参数
    data_sizes = [10000, 100000, 1000000, 10000000]
    num_runs = 5

    results = Dict{String, Dict{String, Float64}}()

    for N in data_sizes
        test_data = generate_test_data(N)

        # 预热
        _ = core_function(test_data)

        # 正式计时
        times = Float64[]
        for run in 1:num_runs
            start_time = time()
            output = core_function(test_data)
            push!(times, time() - start_time)
        end

        results["N_$N"] = Dict{String, Float64}(
            "mean_time" => mean(times),
            "median_time" => median(times),
            "std_time" => std(times)
        )
    end

    return results
end
```

### 8.6 性能验收标准

| 判定 | 条件 | 说明 |
|------|------|------|
| ✅ 通过 | Julia 时间 < MATLAB 时间 | 性能优于 MATLAB |
| ❌ 失败 | Julia 时间 ≥ MATLAB 时间 | 性能未达标，需优化 |

**性能失败排查清单**：

| 可能原因 | 排查方法 |
|----------|----------|
| 类型不稳定 | 使用 `@code_warntype` 检查 |
| 内存分配过多 | 使用 `@time` 查看分配次数 |
| 算法未优化 | 对比 MATLAB 与 Julia 实现差异 |
| 工具箱函数差异 | 检查是否使用了兼容层函数 |
| JIT 未充分预热 | 增加预热次数或数据量 |

### 8.7 性能对比报告格式

| 数据量级 | MATLAB 时间(s) | Julia 时间(s) | 加速比(MATLAB/Julia) | 判定 |
|----------|----------------|---------------|--------|------|
| N=10,000 | 0.05 ± 0.01 | 0.03 ± 0.00 | 1.67x | ✅ |
| N=100,000 | 0.52 ± 0.03 | 0.28 ± 0.02 | 1.86x | ✅ |
| N=1,000,000 | 5.21 ± 0.15 | 2.89 ± 0.12 | 1.80x | ✅ |
| N=10,000,000 | 52.3 ± 1.2 | 28.5 ± 0.8 | 1.83x | ✅ |

**加速比计算**：
```
加速比 = MATLAB 时间 / Julia 时间
> 1.0 表示 Julia 更快（通过）
≤ 1.0 表示 MATLAB 更快或持平（失败）
```