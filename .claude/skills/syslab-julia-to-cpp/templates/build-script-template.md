# `build.jl` 模板

适用于动态库导出场景。将复杂 Julia 逻辑保留在普通函数中，仅把导出约束放在最外层包装函数。
模板中的函数名、导出名和签名仅为占位示例。实际使用时，必须替换为用户明确指定的导出函数、导出符号名以及参数类型和返回类型。
若包装函数不是直接沿用原始 Julia 入参，必须按 `../references/wrapper-arg-conversion.md` 推导包装函数签名与 `static_compile(...)` 参数元组。
若用户源码已有合法的直接导出签名，可以沿用 `SyslabCC.static_compile("symbol", user_function, (...))`；本模板主要用于需要新增 ABI 包装层的情况。

### 标量返回值通过出参带出

```julia
function kernel(x::Float64, y::Float64)
    return x + y
end

function cwrap_kernel(x::Float64, y::Float64, outpara_1::Ptr{Float64})::Int32
    ret_1 = kernel(x, y)
    unsafe_store!(outpara_1, ret_1)
    return Int32(0)
end

@static if @isdefined(SyslabCC)
    SyslabCC.static_compile("kernel_add_f64", cwrap_kernel, (Float64, Float64, Ptr{Float64}))
end
```

### 向量返回值通过出参带出

```julia
function kernel(x::Vector{Float64})
    return x .* 2
end

function cwrap_kernel(x::Ptr{Float64}, x_dims::Ptr{Int64}, outpara_1::Ptr{Float64})::Int32
    arr_x_dims = unsafe_wrap(Array, x_dims, (1,); own=false)
    arr_x = unsafe_wrap(Array, x, (arr_x_dims[1],); own=false)
    ret_1 = kernel(arr_x)
    for i in 1:length(ret_1)
        unsafe_store!(outpara_1, ret_1[i], i)
    end
    return Int32(0)
end

@static if @isdefined(SyslabCC)
    SyslabCC.static_compile("kernel_vec_f64", cwrap_kernel, (Ptr{Float64}, Ptr{Int64}, Ptr{Float64}))
end
```

使用提醒：

- 导出函数优先使用稳定、窄签名。
- 如需导出多个符号，每个符号单独写一条 `static_compile(...)`。
- 若原始函数使用复杂类型，优先增加一层导出包装函数。
- 若原始参数是数组，包装函数通常要拆成 `Ptr{T}` 与 `Ptr{Int64}` 维度参数，并在函数体中用 `unsafe_wrap(...; own=false)` 还原。
- 若原始函数有返回值，优先把返回值改成包装函数的额外出参；包装函数自身统一返回 `Int32(0)`。
- 标量返回值通常对应 `Ptr{T}` 出参；数组返回值通常对应 `Ptr{element_type}` 出参，并在函数体内用 `unsafe_store!` 写回。
- `static_compile(...)` 的参数类型元组必须与包装函数签名一致，而不是与原始 Julia 函数签名一致。
- 不要直接照抄模板中的 `kernel`、`kernel_export` 或 `kernel_export_f64`。
