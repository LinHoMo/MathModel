# MathModelSkills 全局安装脚本（Windows PowerShell）
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
        Write-Host "[dry-run] 将创建 $dest 并复制 23 个 agent SKILL.md"
        continue
    }

    New-Item -ItemType Directory -Force -Path $dest | Out-Null

    foreach ($hand in @('Modeler', 'Programmer', 'Writer', 'Reviewer')) {
        $handDest = Join-Path $dest $hand
        New-Item -ItemType Directory -Force -Path $handDest | Out-Null
        Copy-Item (Join-Path $RepoRoot "core\$hand\SKILL.md") $handDest -Force
    }

    $count = 0
    foreach ($hand in @('Modeler', 'Programmer', 'Writer', 'Reviewer')) {
        $agentsDir = Join-Path $RepoRoot "core\$hand\agents"
        if (-not (Test-Path $agentsDir)) { continue }
        foreach ($d in Get-ChildItem -Path $agentsDir -Directory) {
            $agentDest = Join-Path $dest "$hand\agents\$($d.Name)"
            New-Item -ItemType Directory -Force -Path $agentDest | Out-Null
            Copy-Item (Join-Path $d.FullName 'SKILL.md') $agentDest -Force
            $count++
        }
    }

    foreach ($dir in @('tools', 'env', 'knowledge', 'schemas')) {
        $src = Join-Path $RepoRoot "core\$dir"
        if (Test-Path $src) {
            Copy-Item $src $dest -Recurse -Force
        }
    }
    $catalog = Join-Path $RepoRoot 'catalog.yaml'
    if (Test-Path $catalog) { Copy-Item $catalog $dest -Force }

    Write-Host "已安装: 4 个手编排器 + $count 个 agent + tools/env/knowledge/schemas"
}

Write-Host "────────────────────────────────"
Write-Host "完成。重启 runtime 后生效。"
Write-Host ""
Write-Host "提示：全局模式下知识库路径需为绝对路径；"
Write-Host "      若只要在当前项目使用，无需安装——"
Write-Host "      把仓库放在工作目录，runtime 会自动读取 AGENTS.md。"
