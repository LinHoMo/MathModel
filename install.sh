#!/usr/bin/env bash
# MathModel 全局安装脚本（V3 认知工作流运行时）
#
# 用法:
#   ./install.sh                      # 交互选择目标
#   ./install.sh --target claude      # 装到 ~/.claude/skills/
#   ./install.sh --target codex       # 装到 ~/.codex/skills/
#   ./install.sh --target workbuddy   # 装到 ~/.workbuddy/skills/
#   ./install.sh --target trae        # 装到 ~/.trae/skills/
#   ./install.sh --all                # 装到全部已识别的目标
#   ./install.sh --target claude --dry-run   # 只预览，不实际写入
#   ./install.sh --target claude --force     # 冲突时先备份再覆盖
#
# 说明: 本项目默认以「项目内模式」使用——把仓库 clone 到工作目录，
# runtime 会自动读取根目录 AGENTS.md 及各 runtime 入口文件，无需安装。
# 本脚本用于需要「任意目录都能调用」的场景。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=0
FORCE=0
TARGETS=()

# ---------------- 参数解析 ----------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGETS+=("$2"); shift 2 ;;
    --all) TARGETS=(claude codex workbuddy trae); shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --force) FORCE=1; shift ;;
    -h|--help) sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "未知参数: $1（用 --help 查看用法）" >&2; exit 2 ;;
  esac
done

declare -A DEST=(
  [claude]="$HOME/.claude/skills/mathmodel"
  [codex]="$HOME/.codex/skills/mathmodel"
  [workbuddy]="$HOME/.workbuddy/skills/mathmodel"
  [trae]="$HOME/.trae/skills/mathmodel"
)

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  echo "可用目标: claude / codex / workbuddy / trae / --all"
  read -r -p "选择目标: " t
  TARGETS=("$t")
fi

log() { echo "$@"; }

# V3 引擎可复用资产（与 core/ 顶层目录一一对应）
INSTALL_DIRS=(
  "core/skills"      # 建模 / 验证 / 论文映射技能
  "core/roles"       # 5 角色 YAML
  "core/workflows"   # Workflow DAG 定义
  "core/runtime"     # V3 认知运行时（artifacts/state/graph/execution/modeling/knowledge）
  "core/validators"  # L1–L6 门禁
  "core/schemas"     # v3/ 六域 canonical schema
  "core/tools"       # 运行时工具（orchestrator / validate / state / new_project …）
  "core/env"         # 阈值配置
  "core/knowledge"   # 建模知识方法卡
  "core/templates"   # 论文 / 代码模板
  "catalog"          # v3 目录索引
)

# ---------------- 安装 ----------------
for t in "${TARGETS[@]}"; do
  dest="${DEST[$t]:-}"
  if [[ -z "$dest" ]]; then
    log "跳过未知目标: $t"
    continue
  fi

  log "────────────────────────────────"
  log "目标: $t"
  log "位置: $dest"

  if [[ -e "$dest" ]]; then
    if [[ $FORCE -eq 1 ]]; then
      backup="${dest}.bak.$(date +%Y%m%d%H%M%S)"
      log "已存在 → 备份到 $backup"
      [[ $DRY_RUN -eq 0 ]] && mv "$dest" "$backup"
    else
      log "已存在，跳过（用 --force 覆盖，会先备份）"
      continue
    fi
  fi

  if [[ $DRY_RUN -eq 1 ]]; then
    log "[dry-run] 将创建 $dest 并安装 V3 运行时（skills/roles/workflows/runtime/validators/schemas/tools/env/knowledge/templates/catalog）"
    continue
  fi

  mkdir -p "$dest"

  # V3 运行时 + 技能 + 角色 + 工具
  for dir in "${INSTALL_DIRS[@]}"; do
    cp -r "$REPO_ROOT/$dir" "$dest/" 2>/dev/null || true
  done

  # 双视图元数据单一真源 + agent 协议入口
  cp "$REPO_ROOT/catalog.yaml" "$dest/" 2>/dev/null || true
  cp "$REPO_ROOT/AGENTS.md" "$dest/" 2>/dev/null || true

  log "已安装: V3 运行时 + 技能 + 角色 + 工具（skills/roles/workflows/runtime/validators/schemas/tools/env/knowledge/templates/catalog）"
done

log "────────────────────────────────"
log "完成。重启 runtime 后生效。"
log ""
log "提示：全局模式下知识库路径需为绝对路径；"
log "      若只要在当前项目使用，无需安装——"
log "      把仓库放在工作目录，runtime 会自动读取 AGENTS.md。"
