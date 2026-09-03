# `build.jl` 包装函数 ABI 转换规则

当 `shared` 模式需要在 `build.jl` 中新建包装函数，再由 `SyslabCC.static_compile(...)` 导出包装函数时，包装函数的入参、返回值出参和 `static_compile(...)` 完整类型元组都不要凭经验手写，必须对齐当前文件实现的 ABI 规则。

## 使用时机

- 用户原始 Julia 函数签名不适合直接导出。
- 需要把 Julia 函数入参转换成包装函数的 ABI 友好入参。
- 需要把 Julia 函数业务返回值转换成包装函数的额外出参。
- 需要判断 `static_compile(...)` 里应填写什么完整类型元组。

## 转换流程

1. 先按精确类型表匹配 Julia 入参类型。
2. 若精确类型表未命中，再按泛型类型表顺序匹配。
3. 若泛型映射结果不是 `Ptr{Nothing}`，直接采用该结果。
4. 若泛型映射结果是 `Ptr{Nothing}`，则回退为“指向底层元素类型的指针”：
   - 数组或元组：递归取最里层元素类型，生成 `Ptr{element_type}`。
   - 其他值：退化为 `Ptr{typeof(x)}`。
5. 若 Julia 入参是数组，包装函数除了数据指针外，还要额外追加一个维度参数：`<arg>_dims::Ptr{Int64}`。
6. 包装函数内部按两步还原数组：
   - 先把维度指针还原为 `arr_<arg>_dims = unsafe_wrap(Array, <arg>_dims, (ndims,); own=false)`
   - 再把数据指针还原为 `arr_<arg> = unsafe_wrap(Array, <arg>, (arr_<arg>_dims[1], ...); own=false)`

## 精确类型映射

这些类型优先级最高，命中后不再继续泛型匹配。

### 标量

- `Float64 -> Float64`
- `Float32 -> Float32`
- `Float16 -> Float32`
- `Int64 -> Int64`
- `Int32 -> Int32`
- `Int16 -> Int16`
- `Int8 -> Int8`
- `UInt64 -> UInt64`
- `UInt32 -> UInt32`
- `UInt16 -> UInt16`
- `UInt8 -> UInt8`
- `Char -> UInt32`
- `Bool -> UInt8`
- `Complex{Float64} -> Complex{Float64}`
- `Complex{Float32} -> Complex{Float32}`
- `Complex{Float16} -> Complex{Float32}`
- `Complex{Int64} -> Complex{Int64}`
- `Complex{Int32} -> Complex{Int32}`
- `Complex{Int16} -> Complex{Int16}`
- `Complex{Int8} -> Complex{Int8}`
- `Complex{UInt64} -> Complex{UInt64}`
- `Complex{UInt32} -> Complex{UInt32}`
- `Complex{UInt16} -> Complex{UInt16}`
- `Complex{UInt8} -> Complex{UInt8}`
- `Nothing -> Nothing`

### 一维数组

- `Vector{Float64} -> Ptr{Float64}`
- `Vector{Float32} -> Ptr{Float32}`
- `Vector{Float16} -> Ptr{Float16}`
- `Vector{Int64} -> Ptr{Int64}`
- `Vector{Int32} -> Ptr{Int32}`
- `Vector{Int16} -> Ptr{Int16}`
- `Vector{Int8} -> Ptr{Int8}`
- `Vector{UInt64} -> Ptr{UInt64}`
- `Vector{UInt32} -> Ptr{UInt32}`
- `Vector{UInt16} -> Ptr{UInt16}`
- `Vector{UInt8} -> Ptr{UInt8}`
- `Vector{Char} -> Ptr{UInt32}`
- `Vector{Bool} -> Ptr{UInt8}`
- `Vector{Complex{Float64}} -> Ptr{Complex{Float64}}`
- `Vector{Complex{Float32}} -> Ptr{Complex{Float32}}`
- `Vector{Complex{Int64}} -> Ptr{Complex{Int64}}`
- `Vector{Complex{Int32}} -> Ptr{Complex{Int32}}`
- `Vector{Complex{Int16}} -> Ptr{Complex{Int16}}`
- `Vector{Complex{Int8}} -> Ptr{Complex{Int8}}`
- `Vector{Complex{UInt64}} -> Ptr{Complex{UInt64}}`
- `Vector{Complex{UInt32}} -> Ptr{Complex{UInt32}}`
- `Vector{Complex{UInt16}} -> Ptr{Complex{UInt16}}`
- `Vector{Complex{UInt8}} -> Ptr{Complex{UInt8}}`

限制：

- `Vector{Complex{Float16}}` 不要擅自提升成 `Ptr{Complex{Float32}}`，否则会破坏原始内存布局。

## 泛型映射

- `AbstractString -> String`
- `Complex -> Complex{Float64}`
- `AbstractArray -> Ptr{Nothing}`，然后按底层元素类型回退为 `Ptr{element_type}`，并额外追加 `Ptr{Int64}` 维度参数。
- `AbstractDict -> Ptr{Nothing}`
- `AbstractSet -> Ptr{Nothing}`
- `Tuple -> Ptr{Nothing}`
- `NamedTuple -> Ptr{Nothing}`
- `AbstractPattern -> Ptr{Nothing}`
- `AbstractMatch -> Ptr{Nothing}`
- `BigFloat -> Ptr{Nothing}`
- `Rational -> Ptr{Nothing}`
- `BigInt -> Ptr{Nothing}`
- `Int128 -> Ptr{Nothing}`
- `UInt128 -> Ptr{Nothing}`
- `Symbol -> Ptr{Nothing}`
- `Module -> Ptr{Nothing}`
- `Any -> Ptr{Nothing}`

对所有映射为 `Ptr{Nothing}` 的类型，都要继续根据真实入参值推导实际指针类型，而不是把 `Ptr{Nothing}` 原样写进包装函数签名。

## 写 `build.jl` 时的落地规则

- `SyslabCC.static_compile("symbol", wrapper, (...))` 的完整类型元组，必须填写包装函数签名中的全部类型，不是原始 Julia 函数签名。
- 若原始参数是数组，`static_compile(...)` 中也要把额外的维度参数一起写进去。
- 若用户函数有返回值，优先把业务返回值改成包装函数的额外出参，不要直接依赖包装函数返回值承载业务数据。
- 包装层只做 ABI 协议转换；核心算法仍留在原始 Julia 函数里。
- 如果某个复杂类型虽然能机械地退化成 `Ptr{T}`，但 ABI 含义不清、外部调用方也无法正确构造，就不要直接导出；应继续收敛成标量、字符串或“数据指针 + 维度”协议。

## 返回值转换规则

导出约定是：包装函数本身返回 `Int32` 状态码，用户函数的业务返回值通过额外出参带出。这里的 `Int32` 是包装函数自己的 ABI 返回值，不是用户函数的业务返回值。

### 总规则

1. 先推断用户函数的返回类型。
2. 仅支持以下返回形式：
   - 基本标量
   - 多维数组
   - `Tuple(...)` 形式的多个返回值
   - `Nothing`
3. 若返回值是 `Nothing`，不生成对应出参。
4. 若返回值是标量，包装函数新增一个 `Ptr{T}` 出参。
5. 若返回值是数组，包装函数新增一个 `Ptr{element_type}` 出参。
6. 若返回值是 `Tuple(...)`，把每个返回项平铺成一个独立出参；`Nothing` 项跳过。
7. 包装函数内部调用原始 Julia 函数后：
   - 标量返回值用 `unsafe_store!(outptr, value)` 写回
   - 数组返回值逐元素循环 `unsafe_store!(outptr, value[i], i)` 写回
8. 包装函数最后统一 `return Int32(0)`；非零返回码只留给错误协议，不承载业务返回值。

### 支持与限制

- 单返回值标量：
  - 若 `get_exact_ctype(T)` 命中标量映射，则对应出参类型为 `Ptr{mapped_ctype}`。
  - 例如：`Float64 -> Ptr{Float64}`，`Bool -> Ptr{UInt8}`，`Char -> Ptr{UInt32}`。
- 单返回值数组：
  - `Array{T,N} -> Ptr{T}` 作为出参
- 多返回值元组：
  - `Tuple{A, B, ...}` 逐项平铺
- `Nothing`：
  - 不生成出参
- 不支持：
  - 除数组外的复杂容器返回值
  - 未经收敛的自定义结构体返回值
  - 依赖包装函数直接返回业务对象

说明：

- 返回数组时，包装函数只负责把结果写入调用方预分配的内存，不负责返回长度或分配内存。
- 数组返回值的维度、长度和内存容量必须由调用方预先按约定准备好；否则即使签名匹配，也可能发生写越界或结果不完整。
- 这套规则和入参规则不同：入参数组需要“数据指针 + 维度指针”，返回数组目前只额外传“结果数据指针”，不附带返回维度指针。

### 包装函数形态

```julia
function cwrap_xxx(in1::..., in2::..., out1::Ptr{T1}, out2::Ptr{T2})::Int32
    ret_1, ret_2 = user_function(...)
    unsafe_store!(out1, ret_1)
    for i in 1:length(ret_2)
        unsafe_store!(out2, ret_2[i], i)
    end
    return Int32(0)
end
```

上面的 `out1`、`out2` 都属于包装函数的额外出参，因此也必须写进 `SyslabCC.static_compile(...)` 的完整类型元组。

## 示例

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
