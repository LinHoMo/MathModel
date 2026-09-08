# 导出包装函数模板

当原始 Julia 函数签名不适合直接导出时，优先增加一层稳定包装函数。
模板中的 `internal_kernel`、`exported_kernel` 和导出符号名仅为占位示例。实际使用时，必须替换为用户明确指定的导出函数。
包装函数入参的推导规则必须对齐 `../references/wrapper-arg-conversion.md`。
如果原始函数已经能用官方支持的参数和返回值类型直接 `static_compile(...)`，不要为了使用本模板而强行新增包装层。

```julia
function internal_kernel(data)
    return sum(data)
end

function exported_kernel(ptr::Ptr{Float64}, data_dims::Ptr{Int64}, outpara_1::Ptr{Float64})::Int32
    # 这里根据约定把外部输入转换为内部表示
    arr_data_dims = unsafe_wrap(Array, data_dims, (1,); own=false)
    arr_data = unsafe_wrap(Array, ptr, (arr_data_dims[1],); own=false)
    ret_1 = internal_kernel(arr_data)
    unsafe_store!(outpara_1, ret_1)
    return Int32(0)
end

@static if @isdefined(SyslabCC)
    SyslabCC.static_compile("exported_kernel", exported_kernel, (Ptr{Float64}, Ptr{Int64}, Ptr{Float64}))
end
```

使用规则：

- 包装函数签名尽量只暴露受支持的标量与指针类型。
- 包装层负责协议转换，核心算法层负责计算。
- 若原始 Julia 入参是数组，包装层要显式接收数据指针和维度指针，再用 `unsafe_wrap(...; own=false)` 还原数组。
- 若原始 Julia 函数有返回值，包装层要把返回值改写为额外出参；包装函数自身统一返回 `Int32(0)`。
- 标量返回值用 `unsafe_store!(outptr, value)` 写回；数组返回值逐元素 `unsafe_store!(outptr, value[i], i)` 写回。
- `SyslabCC.static_compile(...)` 填的是包装函数的完整 ABI 签名，不是原始 Julia 函数签名。
- 不要把复杂协议散落到多个导出函数中。
- 不要直接照抄模板中的包装函数名或导出符号名。
