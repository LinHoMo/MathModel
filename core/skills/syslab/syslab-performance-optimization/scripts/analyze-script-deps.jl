#!/usr/bin/env julia

struct Options
    project_root::String
    entry_scripts::Vector{String}
end

mutable struct FileAnalysis
    abs_path::String
    rel_path::String
    includes::Vector{String}
    dynamic_includes::Vector{String}
    import_refs::Vector{String}
    defined_modules::Vector{String}
    top_level_signals::Vector{String}
    data_paths::Vector{String}
    parse_error::Union{Nothing, String}
end

function usage(io::IO=stdout)
    print(io, """
Usage:
julia scripts/analyze-script-deps.jl [--project-root PATH] ENTRY1.jl [ENTRY2.jl ...]

Purpose:
  Recursively analyze local Julia script dependencies starting from one or more entry scripts.
  Print dependency-analysis data in markdown, or return structured dependency data
  through `analyze_deps(...)` when this file is loaded via `include(...)`.

Options:
  --project-root PATH   Project root used to resolve relative entry-script paths.
                        Defaults to the current working directory.
  -h, --help            Show this help message.
""")
end

function parse_args(args::Vector{String})
    project_root = pwd()
    entry_scripts = String[]

    i = 1
    while i <= length(args)
        arg = args[i]
        if arg == "-h" || arg == "--help"
            usage()
            exit(0)
        elseif arg == "--project-root"
            i += 1
            i > length(args) && error("missing value for --project-root")
            project_root = args[i]
        elseif startswith(arg, "--project-root=")
            project_root = split(arg, "=", limit=2)[2]
        elseif startswith(arg, "-")
            error("unsupported option: $arg")
        else
            push!(entry_scripts, arg)
        end
        i += 1
    end

    isempty(entry_scripts) && error("at least one entry script is required")

    root = normpath(abspath(project_root))
    entries = [normalize_input_path(root, path) for path in entry_scripts]
    for path in entries
        isfile(path) || error("entry script does not exist: $path")
    end

    return Options(root, entries)
end

normalize_input_path(root::String, path::String) = normpath(isabspath(path) ? path : joinpath(root, path))

sanitize_display(value) = replace(strip(sprint(show, value)), r"\s+" => " ")

function unique_sorted(values::Vector{String})
    return sort!(collect(Set(filter(!isempty, values))))
end

function is_definition(expr)
    !(expr isa Expr) && return false
    expr.head in (:function, :macro, :module, :baremodule, :struct, :abstract, :primitive, :const) && return true
    if expr.head == :(=)
        lhs = expr.args[1]
        return is_method_lhs(lhs)
    end
    return false
end

function is_method_lhs(lhs)
    lhs isa Expr || return false
    lhs.head in (:call, :where) && return true
    if lhs.head == :(::) && !isempty(lhs.args)
        return is_method_lhs(lhs.args[1])
    end
    return false
end

function call_name(expr)
    if expr isa Symbol
        return String(expr)
    elseif expr isa Expr
        if expr.head == :.
            return sanitize_display(expr)
        elseif expr.head == :curly && !isempty(expr.args)
            return call_name(expr.args[1])
        end
    end
    return sanitize_display(expr)
end

function walk_expr(visitor, expr)
    visitor(expr)
    if expr isa Expr
        for arg in expr.args
            walk_expr(visitor, arg)
        end
    elseif expr isa QuoteNode
        walk_expr(visitor, expr.value)
    end
end

function static_string_value(expr, current_dir::String)
    if expr isa String
        return expr
    elseif expr isa Expr
        if expr.head == :string
            parts = String[]
            for arg in expr.args
                value = static_string_value(arg, current_dir)
                value === nothing && return nothing
                push!(parts, value)
            end
            return join(parts)
        elseif expr.head == :macrocall
            if expr.args[1] == Symbol("@__DIR__")
                return current_dir
            end
        elseif expr.head == :call && !isempty(expr.args)
            fn = expr.args[1]
            values = map(arg -> static_string_value(arg, current_dir), expr.args[2:end])
            any(isnothing, values) && return nothing
            parts = String[something(value) for value in values]
            if fn == :joinpath
                return joinpath(parts...)
            elseif fn == :normpath
                return normpath(parts...)
            elseif fn == :abspath
                return abspath(parts...)
            elseif fn == :realpath
                length(parts) == 1 || return nothing
                return realpath(parts[1])
            end
        end
    end
    return nothing
end

function resolve_include_path(expr, current_dir::String)
    value = static_string_value(expr, current_dir)
    value === nothing && return nothing
    return normpath(isabspath(value) ? value : joinpath(current_dir, value))
end

function format_import_ref(ref)
    if ref isa Symbol
        return String(ref)
    elseif ref isa QuoteNode
        return format_import_ref(ref.value)
    elseif ref isa Expr
        if ref.head == :.
            dot_prefix = 0
            parts = String[]
            for arg in ref.args
                if arg == Symbol(".")
                    dot_prefix += 1
                else
                    push!(parts, format_import_ref(arg))
                end
            end
            prefix = repeat(".", dot_prefix)
            return prefix * join(filter(!isempty, parts), ".")
        elseif ref.head == Symbol(":")
            lhs = isempty(ref.args) ? "" : format_import_ref(ref.args[1])
            rhs = [format_import_ref(arg) for arg in ref.args[2:end]]
            return isempty(rhs) ? lhs : lhs * ": " * join(rhs, ", ")
        end
    end
    return sanitize_display(ref)
end

function extract_import_refs(expr)
    refs = String[]
    expr isa Expr || return refs
    expr.head in (:using, :import) || return refs

    for arg in expr.args
        if arg isa LineNumberNode
            continue
        else
            push!(refs, format_import_ref(arg))
        end
    end
    return refs
end

function root_module_name(ref::String)
    stripped = replace(strip(ref), r"^\.+\s*" => "")
    match_obj = match(r"[A-Za-z_][A-Za-z0-9_]*", stripped)
    return match_obj === nothing ? "" : match_obj.match
end

function looks_like_data_path(value::String)
    stripped = strip(value)
    isempty(stripped) && return false
    (stripped == "\\" || stripped == "/") && return false
    occursin('\n', stripped) && return false
    startswith(lowercase(stripped), "http://") && return false
    startswith(lowercase(stripped), "https://") && return false

    has_data_extension = occursin(r"\.(csv|tsv|txt|json|toml|yaml|yml|mat|h5|hdf5|bin|dat|wav|png|jpg|jpeg|bmp|tif|tiff|jld2?)$"i, stripped)
    has_explicit_path_prefix =
        startswith(stripped, "./") ||
        startswith(stripped, "../") ||
        startswith(stripped, ".\\") ||
        startswith(stripped, "..\\") ||
        (startswith(stripped, "/") && (occursin('/', stripped[2:end]) || has_data_extension)) ||
        (startswith(stripped, "\\") && (occursin('\\', stripped[2:end]) || has_data_extension)) ||
        occursin(r"^[A-Za-z]:[\\/]" , stripped)

    return has_data_extension || has_explicit_path_prefix
end

function normalize_data_path(value::String, current_dir::String)
    if occursin('/', value) || occursin('\\', value)
        return normpath(isabspath(value) ? value : joinpath(current_dir, value))
    end
    return value
end

function top_level_signal(expr)
    expr isa LineNumberNode && return nothing
    is_definition(expr) && return nothing
    !(expr isa Expr) && return nothing

    if expr.head == :call
        name = call_name(expr.args[1])
        return name == "include" ? nothing : "顶层调用: $name"
    elseif expr.head == :macrocall
        return "顶层宏调用: $(call_name(expr.args[1]))"
    elseif expr.head == :for
        return "顶层循环: for"
    elseif expr.head == :while
        return "顶层循环: while"
    elseif expr.head == :(=)
        lhs = expr.args[1]
        is_method_lhs(lhs) && return nothing
        rhs = length(expr.args) >= 2 ? expr.args[2] : nothing
        return contains_runtime_work(rhs) ? "顶层初始化/赋值" : nothing
    elseif expr.head == :if
        return "顶层条件分支"
    elseif expr.head == :let
        return "顶层 let 块"
    elseif expr.head == :try
        return "顶层 try/catch"
    elseif expr.head == :block
        for arg in expr.args
            signal = top_level_signal(arg)
            signal === nothing || return signal
        end
    end

    return nothing
end

function contains_runtime_work(expr)
    expr === nothing && return false
    expr isa LineNumberNode && return false
    if expr isa Expr
        expr.head in (:call, :macrocall, :for, :while, :if, :try, :let, :do) && return true
        for arg in expr.args
            contains_runtime_work(arg) && return true
        end
    elseif expr isa QuoteNode
        return contains_runtime_work(expr.value)
    end
    return false
end

function parse_toplevel_expressions(text::String, filename::String)
    expressions = Any[]
    pos = firstindex(text)
    while pos <= lastindex(text)
        expr, next_pos = Meta.parse(text, pos; greedy=true, raise=false, filename=filename)
        expr === nothing && break
        if expr isa Expr && expr.head in (:error, :incomplete)
            push!(expressions, expr)
            break
        end
        push!(expressions, expr)
        next_pos <= pos && break
        pos = next_pos
    end
    return expressions
end

function analyze_file(path::String, project_root::String)
    text = read(path, String)
    current_dir = dirname(path)
    includes = String[]
    dynamic_includes = String[]
    import_refs = String[]
    defined_modules = String[]
    top_level_signals = String[]
    data_paths = String[]
    parse_error = nothing

    expressions = parse_toplevel_expressions(text, path)
    for expr in expressions
        if expr isa Expr && expr.head in (:error, :incomplete)
            parse_error = "解析失败，存在无法静态分析的语法片段"
            continue
        end

        signal = top_level_signal(expr)
        signal === nothing || push!(top_level_signals, signal)

        walk_expr(expr) do node
            if !(node isa Expr)
                if node isa String && looks_like_data_path(node)
                    push!(data_paths, normalize_data_path(node, current_dir))
                end
                return
            end

            if node.head == :call && !isempty(node.args) && node.args[1] == :include
                if length(node.args) >= 2
                    include_path = resolve_include_path(node.args[2], current_dir)
                    if include_path === nothing
                        push!(dynamic_includes, sanitize_display(node))
                    elseif isfile(include_path)
                        push!(includes, include_path)
                    else
                        push!(dynamic_includes, sanitize_display(node) * "  # unresolved -> " * include_path)
                    end
                end
            elseif node.head in (:using, :import)
                append!(import_refs, extract_import_refs(node))
            elseif node.head in (:module, :baremodule)
                for arg in node.args
                    if arg isa Symbol
                        push!(defined_modules, String(arg))
                        break
                    end
                end
            elseif node.head == :string
                value = static_string_value(node, current_dir)
                if value !== nothing && looks_like_data_path(value)
                    push!(data_paths, normalize_data_path(value, current_dir))
                end
            end
        end
    end

    return FileAnalysis(
        path,
        relpath(path, project_root),
        unique_sorted(includes),
        unique_sorted(dynamic_includes),
        unique_sorted(import_refs),
        unique_sorted(defined_modules),
        unique_sorted(top_level_signals),
        unique_sorted(data_paths),
        parse_error,
    )
end

function ensure_analysis!(analyses::Dict{String, FileAnalysis}, path::String, project_root::String)
    if !haskey(analyses, path)
        analyses[path] = analyze_file(path, project_root)
    end
    return analyses[path]
end

function trace_entry!(
    analyses::Dict{String, FileAnalysis},
    parents::Dict{String, Set{String}},
    reached_by_entries::Dict{String, Set{String}},
    project_root::String,
    entry::String,
    current::String,
    parent::Union{Nothing, String},
)
    ensure_analysis!(analyses, current, project_root)
    parent === nothing || push!(get!(parents, current, Set{String}()), parent)

    entry_set = get!(reached_by_entries, current, Set{String}())
    entry in entry_set && return
    push!(entry_set, entry)

    for child in analyses[current].includes
        trace_entry!(analyses, parents, reached_by_entries, project_root, entry, child, current)
    end
end

function collect_dependency_graph(options::Options)
    analyses = Dict{String, FileAnalysis}()
    parents = Dict{String, Set{String}}()
    reached_by_entries = Dict{String, Set{String}}()

    for entry in options.entry_scripts
        trace_entry!(analyses, parents, reached_by_entries, options.project_root, entry, entry, nothing)
    end

    return analyses, parents, reached_by_entries
end

function classify_file_role(path::String, entry_scripts::Set{String}, parent_count::Int, entry_count::Int)
    if path in entry_scripts
        return "入口脚本"
    elseif entry_count > 1
        return "共享脚本/模块"
    elseif parent_count > 1
        return "被多个上游复用"
    else
        return "include 调用链节点"
    end
end

function helper_requirement(analysis::FileAnalysis, parent_count::Int, entry_count::Int)
    reasons = String[]
    if entry_count > 1 || parent_count > 1
        push!(reasons, "命中共享热路径/多入口复用候选")
    end
    if !isempty(analysis.top_level_signals)
        push!(reasons, "存在顶层执行体，需检查是否应移入稳定函数边界")
    end
    if entry_count > 1 && !isempty(analysis.top_level_signals)
        push!(reasons, "多入口重复触达且含顶层执行，需检查重复初始化入口")
    end

    return isempty(reasons) ? "N/A 或待人工确认" : join(reasons, "；")
end

function summarize_local_imports(analyses::Dict{String, FileAnalysis})
    module_names = Set{String}()
    for analysis in values(analyses)
        union!(module_names, analysis.defined_modules)
    end

    local_relative = Dict{String, Vector{String}}()
    external_imports = Dict{String, Vector{String}}()

    for analysis in values(analyses)
        for ref in analysis.import_refs
            if startswith(strip(ref), ".")
                push!(get!(local_relative, analysis.rel_path, String[]), ref)
                continue
            end

            root = root_module_name(ref)
            if !isempty(root) && root in module_names
                push!(get!(local_relative, analysis.rel_path, String[]), ref)
            else
                push!(get!(external_imports, analysis.rel_path, String[]), ref)
            end
        end
    end

    for (_, refs) in local_relative
        sort!(unique!(refs))
    end
    for (_, refs) in external_imports
        sort!(unique!(refs))
    end

    return local_relative, external_imports
end

function markdown_escape(value::String)
    escaped = replace(value, "\\" => "\\\\")
    escaped = replace(escaped, "|" => "\\|")
    return replace(escaped, "\n" => " ")
end

function emit_dependency_tree(io::IO, entry::String, analyses::Dict{String, FileAnalysis}, root::String)
    println(io, "- `", relpath(entry, root), "`")
    visited = Set{String}()

    function walk(path::String, indent::String)
        path in visited && return
        push!(visited, path)
        for child in analyses[path].includes
            println(io, indent, "- `", relpath(child, root), "`")
            walk(child, indent * "  ")
        end
    end

    walk(entry, "  ")
end

function dependency_tree_lines(entry::String, analyses::Dict{String, FileAnalysis}, root::String)
    lines = String[relpath(entry, root)]
    visited = Set{String}()

    function walk(path::String, indent::String)
        path in visited && return
        push!(visited, path)
        for child in analyses[path].includes
            push!(lines, indent * relpath(child, root))
            walk(child, indent * "  ")
        end
    end

    walk(entry, "  ")
    return lines
end

function build_report_data(options::Options, analyses, parents, reached_by_entries)
    local_relative, external_imports = summarize_local_imports(analyses)
    entry_scripts = Set(options.entry_scripts)
    ordered_paths = sort(collect(keys(analyses)); by=path -> analyses[path].rel_path)

    script_rows = Vector{Dict{String, Any}}()
    dependency_edges = Vector{Dict{String, String}}()
    dynamic_items = Vector{Dict{String, String}}()
    data_items = Vector{Dict{String, String}}()

    for path in ordered_paths
        analysis = analyses[path]
        entry_refs = sort([relpath(entry, options.project_root) for entry in get(reached_by_entries, path, Set{String}())])
        direct_includes = [relpath(child, options.project_root) for child in analysis.includes]
        role = classify_file_role(path, entry_scripts, length(get(parents, path, Set{String}())), length(entry_refs))
        requirement = helper_requirement(analysis, length(get(parents, path, Set{String}())), length(entry_refs))

        row = Dict{String, Any}(
            "path" => analysis.rel_path,
            "role" => role,
            "reached_by_entries" => entry_refs,
            "direct_local_dependencies" => direct_includes,
            "helper_script_functionalization_requirement" => requirement,
            "defined_modules" => analysis.defined_modules,
            "top_level_signals" => analysis.top_level_signals,
            "dynamic_includes" => analysis.dynamic_includes,
            "data_paths" => filter(item -> item != "\\" && item != "/", analysis.data_paths),
            "local_relative_imports" => get(local_relative, analysis.rel_path, String[]),
            "external_imports" => get(external_imports, analysis.rel_path, String[]),
        )
        analysis.parse_error === nothing || (row["parse_error"] = analysis.parse_error)
        push!(script_rows, row)

        for child in direct_includes
            push!(dependency_edges, Dict("from" => analysis.rel_path, "to" => child))
        end
        for item in analysis.dynamic_includes
            push!(dynamic_items, Dict("path" => analysis.rel_path, "expr" => item))
        end
        for item in analysis.data_paths
            (item == "\\" || item == "/") && continue
            push!(data_items, Dict("path" => analysis.rel_path, "value" => item))
        end
    end

    return Dict{String, Any}(
        "project_root" => options.project_root,
        "entry_scripts" => [relpath(entry, options.project_root) for entry in options.entry_scripts],
        "entry_dependency_trees" => [
            Dict(
                "entry_script" => relpath(entry, options.project_root),
                "tree_lines" => dependency_tree_lines(entry, analyses, options.project_root),
            ) for entry in options.entry_scripts
        ],
        "local_script_rows" => script_rows,
        "local_dependency_edges" => dependency_edges,
        "dynamic_include_candidates" => dynamic_items,
        "data_path_candidates" => unique(data_items),
    )
end

function emit_markdown(io::IO, options::Options, analyses, parents, reached_by_entries)
    report = build_report_data(options, analyses, parents, reached_by_entries)
    local_relative, external_imports = summarize_local_imports(analyses)
    ordered_paths = sort(collect(keys(analyses)); by=path -> analyses[path].rel_path)

    println(io, "# 依赖分析数据")
    println(io)
    println(io, "## 用户直接执行脚本清单")
    for entry in report["entry_scripts"]
        println(io, "- `", entry, "`")
    end

    println(io)
    println(io, "## 入口脚本本地依赖树")
    for item in report["entry_dependency_trees"]
        println(io, "- `", item["entry_script"], "`")
        for line in item["tree_lines"][2:end]
            println(io, "  - `", line, "`")
        end
    end

    println(io)
    println(io, "## 本地脚本依赖概览数据")
    println(io, "| 脚本 | 角色 | 被哪些入口触达 | 直接本地依赖 | 辅助脚本函数化要求 | 备注 |")
    println(io, "| --- | --- | --- | --- | --- | --- |")
    for path in ordered_paths
        analysis = analyses[path]
        row = only(filter(item -> item["path"] == analysis.rel_path, report["local_script_rows"]))
        notes = String[]
        isempty(analysis.top_level_signals) || push!(notes, "顶层信号: " * join(analysis.top_level_signals, "；"))
        isempty(analysis.dynamic_includes) || push!(notes, "动态 include 待人工确认")
        analysis.parse_error === nothing || push!(notes, analysis.parse_error)

        println(
            io,
            "| `", markdown_escape(analysis.rel_path), "` | ",
            markdown_escape(row["role"]), " | ",
            markdown_escape(isempty(row["reached_by_entries"]) ? "-" : join(row["reached_by_entries"], "<br>")), " | ",
            markdown_escape(isempty(row["direct_local_dependencies"]) ? "-" : join(row["direct_local_dependencies"], "<br>")), " | ",
            markdown_escape(row["helper_script_functionalization_requirement"]), " | ",
            markdown_escape(isempty(notes) ? "-" : join(notes, "；")), " |",
        )
    end

    println(io)
    println(io, "## 本地相对导入 / 本地模块导入")
    if isempty(local_relative)
        println(io, "- 未检测到本地相对导入。")
    else
        for path in sort(collect(keys(local_relative)))
            println(io, "- `", path, "`: ", join(local_relative[path], "；"))
        end
    end

    println(io)
    println(io, "## 外部 using/import 依赖")
    if isempty(external_imports)
        println(io, "- 未检测到外部 `using` / `import` 依赖。")
    else
        for path in sort(collect(keys(external_imports)))
            println(io, "- `", path, "`: ", join(external_imports[path], "；"))
        end
    end

    println(io)
    println(io, "## 动态 include 待人工确认")
    dynamic_items = [(analysis.rel_path, item) for analysis in values(analyses) for item in analysis.dynamic_includes]
    if isempty(dynamic_items)
        println(io, "- 未检测到动态 include。")
    else
        for (path, item) in sort(dynamic_items; by=first)
            println(io, "- `", path, "`: ", item)
        end
    end

    println(io)
    println(io, "## 公共数据路径候选")
    if isempty(report["data_path_candidates"])
        println(io, "- 未检测到明显的数据路径字面量。")
    else
        for item in sort(report["data_path_candidates"]; by=item -> item["path"])
            println(io, "- `", item["path"], "`: `", item["value"], "`")
        end
    end
end

function analyze_deps(entry_scripts::Vector{String}; project_root::AbstractString=pwd())
    root = normpath(abspath(String(project_root)))
    entries = [normalize_input_path(root, path) for path in entry_scripts]
    isempty(entries) && error("at least one entry script is required")
    for path in entries
        isfile(path) || error("entry script does not exist: $path")
    end

    options = Options(root, entries)
    analyses, parents, reached_by_entries = collect_dependency_graph(options)
    return build_report_data(options, analyses, parents, reached_by_entries)
end

analyze_deps(entry_script::AbstractString; kwargs...) = analyze_deps(String[entry_script]; kwargs...)

function main(args::Vector{String})
    options = parse_args(args)
    analyses, parents, reached_by_entries = collect_dependency_graph(options)
    emit_markdown(stdout, options, analyses, parents, reached_by_entries)
end

if abspath(PROGRAM_FILE) == @__FILE__
    try
        main(ARGS)
    catch err
        if err isa InterruptException
            rethrow()
        end
        println(stderr, "error: ", sprint(showerror, err))
        println(stderr)
        usage(stderr)
        exit(1)
    end
end
