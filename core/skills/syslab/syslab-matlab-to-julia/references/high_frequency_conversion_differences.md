# 高频转换差异

本文件整理 MATLAB -> Syslab/Julia 转换中最常重复出现的语言差异和处理规则。

## 使用规则

- 开始任何代码转换前，先阅读本文件，再进入具体编码。
- 命中以下任一差异时，不要按 MATLAB 写法直译，必须按本文件规则改写。
- 无法直接确认的差异，记录到 `docs/issues.md`，并保持问题分类与本文件一致。

## 1. 图形与绘图差异

- 图形属性设置：`set(...)` 不直接照搬，优先检查是否应改为 `plt_set(...)`。
- `TyPlot` 创建图形后默认处于 `hold("off")` 状态；若要在同一图中继续叠加数据点、拟合曲线或多组序列，必须在添加后续内容前显式调用 `hold("on")`。
- `hold` 参数：不要写 `hold(true/false)`，改为 `hold("on"/"off")`。
- `ishold()` 返回值：不要直接用于 `!` 或 `if`，先按 `0/1` 比较或显式转成 `Bool`。
- 图形属性支持范围：`gcf/gca` 的很多 MATLAB 属性在 TyPlot 中可能不支持，先保留核心属性，非关键属性可删减。
- `Location` 参数：MATLAB 的 `"NorthWest"`、`"SouthEast"` 等需改为小写 `"northwest"`、`"southeast"`。
- `plot` 对元组切片的兼容性有限；若上游 API 返回的是元组（例如 `axis(...)` 的返回值），不要直接把 `limits[3:4]` 这类切片传给 `plot`，先显式转成向量，例如 `collect(limits[3:4])`。

## 2. 语法与表达式差异

- 字符串格式化：优先用 Julia 原生字符串插值，其次 `Printf.@sprintf`；避免为 `sprintf` 引入不必要的 `MultiLanguage` 依赖。
- 向量化运算：MATLAB 的逐元素语义在 Julia 中通常要补 `.`，包括函数调用、算术和逻辑非 `.!`。
- 函数定义：不要保留 MATLAB 式 `function y = foo(x)` 写法，改为 Julia 原生函数定义。
- 区间与拼接：`linspace`、`[a, b]` 一类 MATLAB 写法不要直译，优先改为 `LinRange(..., ..., n)`、`vcat/hcat`。
- 交互暂停：MATLAB `pause` / `pause(...)` 暂无等价 Julia 实现，转换时建议注释掉。

## 3. 类型与维度差异

- 整数语义：MATLAB 中常被默认当作整数的量，在 Julia 中经 `/`、推导或中间计算后可能变成 `Float64`；传给长度、索引、维度、离散阶数等位置前必须显式转回 `Int`。
- 维度语义：明确区分一维向量与二维数组；MATLAB 的 `1xN`、`Nx1`、标量扩展行为不能直接假定在 Julia 中等价。
- 空值与形状判断：不要机械套用 MATLAB 的空数组、`reshape`、逻辑索引写法；涉及标量、空向量和重塑时要分别检查。
- 标量与数组兼容：MATLAB 函数常同时接受标量和数组；迁移时要显式处理两类输入，不能只保留数组路径。
- 循环变量初始化：MATLAB 中隐式形成的迭代状态，在 Julia 中必须在循环前显式初始化。

## 4. 模块与命名冲突

- `include(...)` 后优先使用 `ModuleName.func(...)`，避免与 Ty 库函数重名。
- 不要把 MATLAB 兼容层函数误当作 Julia 原生 API；先确认映射结果，再决定 `using` 和调用方式。

## 5. 随机数一致性

目标：尽量生成与 MATLAB 一致的随机数据。

示例 1：

MATLAB 代码：

```matlab
rng default
rand(2,3)
```

Julia 代码：

```julia
using TyRandom
rng = MT19937ar(5489)
rand(rng, 2, 3)
```

示例 2：

MATLAB 代码：

```matlab
rng default
sigin = sqrt(2) * sin(0:pi/8:6*pi);
sigout3 = awgn(sigin, 10.0, 0.0)
```

Julia 代码：

```julia
using TyRandom
using TyCommunication
rng = MT19937ar(5489)
sigin = sqrt(2) .* sin.(0:pi/8:6*pi)
sigout3 = awgn(rng, sigin, 10.0, 0.0)
```

## 6. TyControlSystems 高频差异

### 6.1 ZPK 对象属性访问

**⚠️ 强制要求**: Syslab 的 ZPK 对象**不支持直接属性访问**，必须使用 `zpkdata()` 函数。

| MATLAB 写法 | ❌ 错误的 Julia 写法 | ✅ 正确的 Julia 写法 |
|-------------|---------------------|---------------------|
| `H.z` | `H.z` 或 `H.z[1]` | `z_data, _, _ = zpkdata(H); z_data[1]` |
| `H.p` | `H.p` 或 `H.p[1]` | `_, p_data, _ = zpkdata(H); p_data[1]` |
| `H.k` | `H.k` 或 `H.k[1]` | `_, _, k_data = zpkdata(H); k_data[1]` |

**错误示例**：
```julia
H = zpk([0.5], [0.3], 1.0, 1)
z = H.z[1]  # ❌ 报错: ZPK 没有名为 z 的属性
```

**正确示例**：
```julia
H = zpk([0.5], [0.3], 1.0, 1)
z_data, p_data, k_data = zpkdata(H)
z = z_data[1]  # ✅ 正确
p = p_data[1]  # ✅ 正确
k = k_data[1]  # ✅ 正确
```

### 6.2 zpkdata 返回值类型

`zpkdata()` 返回的是 `Matrix{Vector}` 而非 MATLAB 的 cell array：

| MATLAB | Julia |
|--------|-------|
| `z{1}` (cell 索引) | `z_data[1]` (矩阵索引，返回 Vector) |
| `z{i,j}` (多输入多输出) | `z_data[i,j]` |

**SISO 系统**：对于单输入单输出系统，直接用 `z_data[1]` 获取零点向量。

### 6.3 修改 ZPK 对象属性

Syslab ZPK 对象的属性**不可直接修改**，必须重新构造：

```julia
# ❌ 错误：直接修改属性
# H.z = new_zeros  # 不支持

# ✅ 正确：重新构造
z_data, p_data, k_data = zpkdata(H)
H_new = zpk(new_zeros, p_data[1], k_data[1], H.Ts)
```

### 6.4 `zpk` 参数类型必须收紧

`zpk` 的增益参数应是标量 `Number`，不能是数组（尤其误写成 3 维数组）。

MATLAB：

```matlab
z = [0.5, 0.5];
p = [0.1, 0.2];
G = zpk(z, p, 1.0, 1);
```

Julia：

```julia
using TyControlSystems

z = ComplexF64[0.5 + 0im, 0.5 + 0im]
p = ComplexF64[0.1 + 0im, 0.2 + 0im]

G = zpk(z, p, 1.0, -1)
```

错误写法：

```julia
G = zpk(z, p, [1.0 ;;;], -1)
```

## 7. 常见函数映射

### 7.1 FFT 相关函数映射

**⚠️ 强制要求**: 迁移产物中，MATLAB 的 `fft/ifft/fft2/ifft2/fftn/ifftn` 默认必须映射为 `ty_fft/ty_ifft/ty_fft2/ty_ifft2/ty_fftn/ty_ifftn`。不要把 Julia / FFTW 风格的 `fft/ifft` 直接当作这些 MATLAB 调用的落地结果。

- 优先采用 TyMath 的 `ty_*` 系列函数，接口更接近 MATLAB，迁移成本更低
- 如果项目没有采用 TyMath，再考虑使用 FFTW 作为备选；但 FFTW 只能覆盖一部分 MATLAB 写法，不能机械直译

#### 7.1.1 首选：TyMath 映射

| MATLAB 写法 | Julia / Syslab 写法 | 说明 |
|------|------|------|
| `Y = fft(X)` | `ty_fft(X)` | 一维 FFT |
| `Y = fft(X,n)` | `ty_fft(X,n)` | 指定长度 |
| `Y = fft(X,n,dim)` | `ty_fft(X,n,dim)` | 指定长度和维度 |
| `Y = fft2(X)` | `ty_fft2(X)` | 二维 FFT |
| `Y = fft2(X,m,n)` | `ty_fft2(X,m,n)` | 指定二维尺寸 |
| `Y = fftn(X)` | `ty_fftn(X)` | N 维 FFT |
| `Y = fftn(X,sz)` | `ty_fftn(X,sz)` | 指定 N 维尺寸 |
| `X = ifft(Y)` | `ty_ifft(Y)` | 一维逆 FFT |
| `X = ifft(Y,n)` | `ty_ifft(Y,n)` | 指定长度 |
| `X = ifft(Y,n,dim)` | `ty_ifft(Y,n,dim)` | 指定长度和维度 |
| `X = ifft(___,symflag)` | `ty_ifft(___,symflag)` | 支持 `symflag` |
| `X = ifft2(Y)` | `ty_ifft2(Y)` | 二维逆 FFT |
| `X = ifft2(Y,m,n)` | `ty_ifft2(Y,m,n)` | 指定二维尺寸 |
| `X = ifft2(___,symflag)` | 无 | 暂无直接对应 |
| `X = ifftn(Y)` | `ty_ifftn(Y)` | N 维逆 FFT |
| `X = ifftn(Y,sz)` | `ty_ifftn(Y,sz)` | 指定 N 维尺寸 |
| `X = ifftn(___,symflag)` | 无 | 暂无直接对应 |

#### 7.1.2 备选：FFTW 映射

| MATLAB 写法 | Julia / FFTW 写法 | 说明 |
|------|------|------|
| `Y = fft(X)` | `fft(X, @something findfirst(>1, size(X)) 1)` | 沿第一个非单例维做 FFT |
| `Y = fft(X,n)` | 无 | 需手动补齐 / 截断后改写 |
| `Y = fft(X,n,dim)` | 无 | 需手动处理长度和维度 |
| `Y = fft(X,[],dim)` | `fft(X, dim)` | `[]` 在迁移时不能直译 |
| `Y = fft2(X)` | `fft(X, 1:2)` | 沿前两维做 FFT |
| `Y = fft2(X,m,n)` | 无 | 需手动 padding / reshape |
| `Y = fftn(X)` | `fft(X)` | 默认对全部维度 |
| `Y = fftn(X,sz)` | 无 | 需手动处理目标尺寸 |
| `X = ifft(Y)` | `ifft(Y, @something findfirst(>1, size(Y)) 1)` | 沿第一个非单例维做逆 FFT |
| `X = ifft(Y,n)` | 无 | 需手动补齐 / 截断后改写 |
| `X = ifft(Y,n,dim)` | 无 | 需手动处理长度和维度 |
| `X = ifft(Y,[],dim)` | `ifft(Y, dim)` | `[]` 在迁移时不能直译 |
| `X = ifft(___,symflag)` | 无 | 无直接对应 |
| `X = ifft2(Y)` | `ifft(Y, 1:2)` | 沿前两维做逆 FFT |
| `X = ifft2(Y,m,n)` | 无 | 需手动 padding / reshape |
| `X = ifft2(___,symflag)` | 无 | 无直接对应 |
| `X = ifftn(Y)` | `ifft(Y)` | 默认对全部维度 |
| `X = ifftn(Y,sz)` | 无 | 需手动处理目标尺寸 |
| `X = ifftn(___,symflag)` | 无 | 无直接对应 |

### 7.2 interp1 函数映射

| MATLAB 写法 | Ty 推荐写法 |
|---|---|
| `interp1(x, v, xq)` | `interp1(x, v, xq)` |
| `interp1(x, v, xq, "linear")` | `interp1(x, v, xq, "linear")` |
| `interp1(x, v, xq, "linear", "extrap")` | `interp1(x, v, xq, "linear", "linear")` |
| `interp1(x, v, xq, "spline", "extrap")` | `interp1(x, v, xq, "spline", "spline")` |
| `interp1(x, v, xq, "pchip", "extrap")` | `interp1(x, v, xq, "pchip", "pchip")` |
| `interp1(x, v, xq, "makima", "extrap")` | `interp1(x, v, xq, "makima", "makima")` |
| `interp1(x, v, xq, method, scalar)` | `interp1(x, v, xq, method, scalar)` |

**注意**： Ty 使用 Julia 数组语义，行向量/列向量和长度为 1 的维度可能与 MATLAB 输出形状不同。

### 7.3 优化库相关函数

fmincon/optimset：在Matlab中，fmincon/optimset可以组合使用；但是在Julia中不行，需要使用fmincon/optimoptions 组合。

MATLAB 代码：

```matlab
options = optimset('TolX',0.001, 'TolFun',0.01, 'MaxIter',100 );
options = optimset(options,'LargeScale','off');
options = optimset(options,'Algorithm','active-set');
options = optimset(options,'Display','off');
x = fmincon( @(x) ds_synNTFobj1(x,p,osr,f0), x0,[],[],[],[], lb,ub,[],options);
```

等价的 Julia 代码：

```julia
options = optimoptions(:fmincon,
                StepTolerance=0.001,
                FunctionTolerance=0.01,
                MaxIterations=100,
                # ScaleProblem=false,
                Algorithm="active-set",
                Display="off")
fun = x -> ds_synNTFobj1(x, p, osr, f0)
x, = fmincon(fun, x0, [], [], [], [], lb, ub, nothing, options)
```

### 7.4 类型判断与空值处理

MATLAB 的 `isnan()` 在 Julia 中**不支持 Vector/Array**。

**推荐的参数默认值处理模式**：

```julia
function foo(x, y, z)
    # 处理可能为 nothing、空数组、或 NaN 的参数
    if x === nothing || isempty(x) || (isa(x, Number) && isnan(x))
        x = default_x
    end
    # ...
end
```

### 7.5 标量 size() 行为差异

标量的 `size()` 返回值不同：

```julia
# MATLAB
size(5)    % 返回 [1, 1]

# Julia
size(5)    # 返回 ()，即 0 维 Tuple
```

## 8. 常见错误模式与教训

### 8.1 不完整阅读源代码

**错误模式**：只读取函数开头或部分代码，根据变量名推测逻辑，遗漏关键的变量修改语句。

**正确做法**：
1. **完整阅读**：从第一行读到最后一行，不要跳过
2. **跟踪变量**：对关键变量，记录其从定义到使用的完整路径
3. **特别关注**：
   - 循环中的累积修改
   - 条件分支中的不同处理

### 8.2 语义对齐案例清单

以下问题通常不会表现为语法错误，而是表现为结果数值或图形与 MATLAB 不一致。遇到这类差异时，先确认语义是否一致，再检查具体 API。

#### A. `[]` 不是普通空数组

MATLAB 的 `[]` 经常用于占住可选参数位置，表示“使用该参数的默认值，但继续传入后续参数”。迁移到 Julia 时不要直接删除这个位置，否则后续实参会整体前移。

MATLAB：

```matlab
H = synthesizeNTF(order, OSR, opt, [], f0);
```

Julia 中应显式补上对应默认值：

```julia
H = synthesizeNTF(order, OSR, opt, 1.5, f0)
```

不要写成：

```julia
H = synthesizeNTF(order, OSR, opt, f0)  # f0 会被误当成 H_inf
```

### 8.3 数字信号处理领域常见错误

#### A. 角度域和 z 平面值不能混用

MATLAB 代码中常见“先计算角度，再映射到单位圆”的写法。迁移时要保留这个语义，不要把角度值直接当作零点或极点。

```julia
z_ang = dw * ds_optzeros(n, opt)
z = exp.(im .* z_ang)
```

#### B. 建议排查顺序

优先按以下顺序排查：参数传递与默认值语义 -> 角度或频率到 z 平面的映射 -> 维度与阶数变量 -> Ty API 类型约束 -> 关键中间数值 -> 最终图形。

## 9. 结果不一致时的调试策略

当 Julia 代码可以运行但输出与 MATLAB 不一致时，不要先调图形或改参数。应先把差异定位到最早发生变化的中间变量。

### 9.1 有 MATLAB 环境时

| 步骤 | 动作 | 目的 |
| ---- | ---- | ---- |
| 1 | 在 MATLAB 中运行原代码，并打印关键中间变量 | 建立基准结果 |
| 2 | 在 Julia 中打印对应中间变量 | 找到首次偏离的位置 |
| 3 | 对偏离位置附近的 MATLAB 和 Julia 代码逐行比对 | 判断是参数、维度、类型还是算法语义问题 |
| 4 | 修复后重新运行同一组输入 | 验证修复是否真正消除差异 |

### 9.2 没有 MATLAB 环境时

无法运行 MATLAB 时，仍然要按 MATLAB 源码逐行追踪变量来源。重点检查默认参数、`[]` 占位、向量形状、复数类型、随机数种子和单位转换；必要时在 Julia 代码中打印每一步中间变量，避免只根据最终图形猜测问题。
