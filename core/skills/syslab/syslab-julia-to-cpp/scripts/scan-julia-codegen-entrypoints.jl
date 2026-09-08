using Printf

function collect_jl_files(root::AbstractString)
    files = String[]
    for (dir, _, names) in walkdir(root)
        for name in names
            endswith(name, ".jl") || continue
            push!(files, normpath(joinpath(dir, name)))
        end
    end
    sort!(files)
    return files
end

function read_text(path::AbstractString)
    open(path, "r") do io
        return read(io, String)
    end
end

function find_exports(text::AbstractString)
    names = String[]
    for m in eachmatch(r"SyslabCC\.static_compile\s*\(\s*\"([^\"]+)\"", text)
        push!(names, m.captures[1])
    end
    return names
end

function find_includes(text::AbstractString)
    names = String[]
    for m in eachmatch(r"include\s*\(\s*\"([^\"]+)\"\s*\)", text)
        push!(names, m.captures[1])
    end
    return names
end

function has_main(text::AbstractString)
    return occursin(r"function\s+main\s*\(", text)
end

function mode_hint(main_flag::Bool, exports::Vector{String})
    if main_flag && !isempty(exports)
        return "app+shared"
    elseif main_flag
        return "app"
    elseif !isempty(exports)
        return "shared"
    else
        return "-"
    end
end

root = isempty(ARGS) ? pwd() : abspath(ARGS[1])
files = collect_jl_files(root)

println("# SyslabCC Entry Inventory")
println()
println("| file | mode hint | main() | exports | includes |")
println("| --- | --- | --- | --- | --- |")

for file in files
    text = read_text(file)
    main_flag = has_main(text)
    exports = find_exports(text)
    includes = find_includes(text)

    rel = relpath(file, root)
    export_text = isempty(exports) ? "-" : join(exports, ", ")
    include_text = isempty(includes) ? "-" : join(includes, ", ")

    @printf("| `%s` | `%s` | `%s` | `%s` | `%s` |\n",
        replace(rel, "\\" => "/"),
        mode_hint(main_flag, exports),
        main_flag ? "yes" : "no",
        export_text,
        include_text)
end
