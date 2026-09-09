# MathModel 全局安装脚本（V3 认知工作流运行时）（Windows PowerShell）
#
# 用法:
#   .\install.ps1 -Target claude
#   .\install.ps1 -Target codex
#   .\install.ps1 -Target workbuddy
#   .\install.ps1 -Target trae
#   .\install.ps1 -All
#   .\install.ps1 -Target claude -DryRun
#   .\install.ps1 -Target claude -Force
#
# 说明: 本项目默认以「项目内模式」使用——把仓库放到工作目录，
# runtime 会自动读取根目录 AGENTS.md 及各 runtime 入口文件，无需安装。
# 本脚本用于需要「任意目录都能调用」的场景。

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('claude', 'codex', 'workbuddy', 'trae')]
    [string]$Target,

    [switch]$All,
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$DestMap = @{
    claude    = Join-Path $HOME '.claude\skills\mathmodel'
    codex     = Join-Path $HOME '.codex\skills\mathmodel'
    workbuddy = Join-Path $HOME '.workbuddy\skills\mathmodel'
    trae      = Join-Path $HOME '.trae\skills\mathmodel'
}

# V3 引擎可复用资产（与 core/ 顶层目录一一对应）
$InstallDirs = @(
    'core\skills',      # 建模 / 验证 / 论文映射技能
    'core\roles',       # 5 角色 YAML
    'core\workflows',   # Workflow DAG 定义
    'core\runtime',     # V3 认知运行时（artifacts/state/graph/execution/modeling/knowledge）
    'core\validators',  # L1–L6 门禁
    'core\schemas',     # v3/ 六域 canonical schema
    'core\tools',       # 运行时工具（orchestrator / validate / state / new_project …）
    'core\env',         # 阈值配置
    'core\knowledge',   # 建模知识方法卡
    'core\templates',   # 论文 / 代码模板
    'catalog'           # v3 目录索引
)

if ($All) {
    $targets = @('claude', 'codex', 'workbuddy', 'trae')
}
elseif ($Target) {
    $targets = @($Target)
}
else {
    Write-Host "可用目标: claude / codex / workbuddy / trae / -All"
    $t = Read-Host "选择目标"
    $targets = @($t)
}

foreach ($t in $targets) {
    $dest = $DestMap[$t]
    if (-not $dest) {
        Write-Host "跳过未知目标: $t"
        continue
    }

    Write-Host "────────────────────────────────"
    Write-Host "目标: $t"
    Write-Host "位置: $dest"

    if (Test-Path $dest) {
        if ($Force) {
            $stamp = Get-Date -Format 'yyyyMMddHHmmss'
            $backup = "$dest.bak.$stamp"
            Write-Host "已存在 -> 备份到 $backup"
            if (-not $DryRun) { Move-Item $dest $backup }
        }
        else {
            Write-Host "已存在，跳过（用 -Force 覆盖，会先备份）"
            continue
        }
    }

    if ($DryRun) {
        Write-Host "[dry-run] 将创建 $dest 并安装 V3 运行时（skills/roles/workflows/runtime/validators/schemas/tools/env/knowledge/templates/catalog）"
        continue
    }

    New-Item -ItemType Directory -Force -Path $dest | Out-Null

    # V3 运行时 + 技能 + 角色 + 工具
    foreach ($dir in $InstallDirs) {
        $src = Join-Path $RepoRoot $dir
        if (Test-Path $src) {
            Copy-Item $src $dest -Recurse -Force
        }
    }

    # 双视图元数据单一真源 + agent 协议入口
    $catalog = Join-Path $RepoRoot 'catalog.yaml'
    if (Test-Path $catalog) { Copy-Item $catalog $dest -Force }
    $agents = Join-Path $RepoRoot 'AGENTS.md'
    if (Test-Path $agents) { Copy-Item $agents $dest -Force }

    Write-Host "已安装: V3 运行时 + 技能 + 角色 + 工具（skills/roles/workflows/runtime/validators/schemas/tools/env/knowledge/templates/catalog）"
}

Write-Host "────────────────────────────────"
Write-Host "完成。重启 runtime 后生效。"
Write-Host ""
Write-Host "提示：全局模式下知识库路径需为绝对路径；"
Write-Host "      若只要在当前项目使用，无需安装——"
Write-Host "      把仓库放在工作目录，runtime 会自动读取 AGENTS.md。"
