#!/usr/bin/env julia

using Printf

const MATLAB_KEYWORDS = Set([
    "if", "elseif", "else", "end", "for", "while", "switch", "case", "otherwise",
    "break", "continue", "return", "function", "classdef", "properties", "methods",
    "events", "try", "catch", "global", "persistent", "spmd", "parfor", "true",
    "false", "zeros", "ones"
])

function usage(io::IO=stdout)
    println(io, "Usage: julia scripts/scan-matlab-project.jl <matlab-project-root>")
end

is_m_file(path::String) = endswith(lowercase(path), ".m")

normalize_line(line::String) = replace(line, '\ufeff' => "")

function strip_comment(line::String)
    line = normalize_line(line)
    idx = findfirst('%', line)
    idx === nothing && return line
    return line[begin:prevind(line, idx)]
end

function nbnc_count(path::String)
    count = 0
    for raw in eachline(path)
        line = strip(strip_comment(raw))
        isempty(line) && continue
        count += 1
    end
    return count
end

function collect_files(root::String)
    files = String[]
    for (dir, _, names) in walkdir(root)
        for name in names
            full = joinpath(dir, name)
            is_m_file(full) || continue
            push!(files, full)
        end
    end
    sort!(files)
    return files
end

function read_lines(path::String)
    return collect(eachline(path))
end

function extract_defined_functions(lines::Vector{String})
    defs = String[]
    pattern_assign = r"^\s*function\s+.*?=\s*([A-Za-z]\w*)"
    pattern_direct = r"^\s*function\s+([A-Za-z]\w*)"
    for raw in lines
        line = strip(strip_comment(raw))
        isempty(line) && continue
        if (m = match(pattern_assign, line)) !== nothing
            push!(defs, m.captures[1])
        elseif (m = match(pattern_direct, line)) !== nothing
            push!(defs, m.captures[1])
        end
    end
    return unique(defs)
end

function extract_call_tokens(lines::Vector{String})
    calls = String[]
    pattern = r"(?<![\.\w])([A-Za-z]\w*)\s*\("
    for raw in lines
        line = strip_comment(raw)
        occursin(r"^\s*function\b", line) && continue
        for m in eachmatch(pattern, line)
            token = m.captures[1]
            token in MATLAB_KEYWORDS && continue
            push!(calls, token)
        end
    end
    return calls
end

function topological_groups(nodes::Vector{String}, deps::Dict{String, Vector{String}})
    state = Dict(node => 0 for node in nodes)
    order = String[]
    cycles = Vector{Vector{String}}()
    stack = String[]

    function dfs(node::String)
        state[node] = 1
        push!(stack, node)
        for dep in get(deps, node, String[])
            dep in nodes || continue
            if state[dep] == 0
                dfs(dep)
            elseif state[dep] == 1
                start_idx = findfirst(==(dep), stack)
                if start_idx !== nothing
                    push!(cycles, copy(stack[start_idx:end]))
                end
            end
        end
        pop!(stack)
        state[node] = 2
        push!(order, node)
    end

    for node in nodes
        state[node] == 0 || continue
        dfs(node)
    end

    return order, cycles
end

function scan_project(root::String)
    root = abspath(root)
    isdir(root) || error("Not a directory: $root")

    files = collect_files(root)
    total_nbnc = 0
    dir_stats = Dict{String, Tuple{Int, Int}}()
    file_stats = Vector{Tuple{String, Int}}()
    lines_by_file = Dict{String, Vector{String}}()
    base_to_rel = Dict{String, String}()
    defined_functions = Dict{String, Vector{String}}()

    for path in files
        rel = relpath(path, root)
        rel_dir = dirname(rel)
        rel_dir = isempty(rel_dir) || rel_dir == "." ? "." : rel_dir
        nbnc = nbnc_count(path)
        total_nbnc += nbnc
        push!(file_stats, (rel, nbnc))
        count, sum_nbnc = get(dir_stats, rel_dir, (0, 0))
        dir_stats[rel_dir] = (count + 1, sum_nbnc + nbnc)

        lines = read_lines(path)
        lines_by_file[rel] = lines
        base_to_rel[splitext(basename(rel))[1]] = rel
        defined_functions[rel] = extract_defined_functions(lines)
    end

    file_deps = Dict{String, Vector{String}}()
    external_calls = Dict{String, Vector{String}}()

    for (rel, lines) in lines_by_file
        local_deps = String[]
        externals = String[]
        for token in extract_call_tokens(lines)
            if haskey(base_to_rel, token) && base_to_rel[token] != rel
                push!(local_deps, base_to_rel[token])
            elseif !(token in defined_functions[rel])
                push!(externals, token)
            end
        end
        file_deps[rel] = sort!(unique(local_deps))
        external_calls[rel] = sort!(unique(externals))
    end

    ordered_files, cycles = topological_groups(sort!(collect(keys(file_deps))), file_deps)

    return (
        root = root,
        files = files,
        total_nbnc = total_nbnc,
        dir_stats = dir_stats,
        file_stats = file_stats,
        defined_functions = defined_functions,
        file_deps = file_deps,
        external_calls = external_calls,
        conversion_order = ordered_files,
        cycles = cycles,
    )
end

function print_dependency_graph(result; io::IO=stdout)
    println(io, "## Candidate File Dependency Graph")
    if isempty(result.file_deps)
        println(io, "(no .m files found)")
        return
    end
    for rel in sort!(collect(keys(result.file_deps)))
        deps = result.file_deps[rel]
        if isempty(deps)
            println(io, "- $rel -> (none)")
        else
            println(io, "- $rel -> ", join(deps, ", "))
        end
    end
    if !isempty(result.cycles)
        println(io)
        println(io, "## Cycles")
        for cycle in result.cycles
            println(io, "- ", join(cycle, " -> "))
        end
    end
end

function print_mapping_candidates(result; io::IO=stdout)
    println(io)
    println(io, "## Candidate MATLAB Functions To Map")
    empty = true
    for rel in sort!(collect(keys(result.external_calls)))
        tokens = result.external_calls[rel]
        isempty(tokens) && continue
        empty = false
        println(io, "- $rel")
        for token in tokens
            println(io, "  - $token")
        end
    end
    empty && println(io, "(no external function calls detected)")
end

function print_defined_functions(result; io::IO=stdout)
    println(io)
    println(io, "## Defined Functions")
    if isempty(result.defined_functions)
        println(io, "(no .m files found)")
        return
    end
    for rel in sort!(collect(keys(result.defined_functions)))
        defs = result.defined_functions[rel]
        if isempty(defs)
            println(io, "- $rel | functions=(script/no local function definition)")
        else
            println(io, "- $rel | functions=", join(defs, ", "))
        end
    end
end

function print_task_seed(result; io::IO=stdout)
    println(io)
    println(io, "## Suggested Task Seed")
    if isempty(result.conversion_order)
        println(io, "(no .m files found)")
        return
    end
    println(io, "### Conversion Order")
    for rel in result.conversion_order
        println(io, "- convert:$rel")
    end
    println(io)
    println(io, "### Script Test Tasks")
    for rel in result.conversion_order
        println(io, "- test-script:$rel")
    end
end

function print_report(result; io::IO=stdout)
    println(io, "# MATLAB Project Scan")
    println(io)
    println(io, "Root: $(result.root)")
    println(io, "MATLAB files: $(length(result.files))")
    println(io, "Total NBNC: $(result.total_nbnc)")
    println(io)
    println(io, "## Per-file NBNC")
    if isempty(result.file_stats)
        println(io, "(no .m files found)")
    else
        for (rel, nbnc) in result.file_stats
            @printf(io, "- %s | NBNC=%d\n", rel, nbnc)
        end
    end
    println(io)
    println(io, "## Per-directory Summary")
    if isempty(result.dir_stats)
        println(io, "(no .m files found)")
    else
        for dir in sort!(collect(keys(result.dir_stats)))
            count, sum_nbnc = result.dir_stats[dir]
            @printf(io, "- %s | files=%d | NBNC=%d\n", dir, count, sum_nbnc)
        end
    end
    println(io)
    print_defined_functions(result; io=io)
    print_dependency_graph(result; io=io)
    print_mapping_candidates(result; io=io)
    print_task_seed(result; io=io)
end

function main(args=ARGS; io::IO=stdout)
    length(args) == 1 || return (usage(io); 1)
    result = scan_project(args[1])
    print_report(result; io=io)
    return 0
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
