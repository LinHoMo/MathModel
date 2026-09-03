#!/usr/bin/env bash
# MathModelSkills 全局安装脚本
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
    log "[dry-run] 将创建 $dest 并复制 23 个 agent SKILL.md"
    continue
  fi

  mkdir -p "$dest"

  # 四手编排器
  for hand in Modeler Programmer Writer Reviewer; do
    mkdir -p "$dest/$hand"
    cp "$REPO_ROOT/core/$hand/SKILL.md" "$dest/$hand/SKILL.md"
  done

  # 23 个 agent
  count=0
  for hand in Modeler Programmer Writer Reviewer; do
    for d in "$REPO_ROOT/core/$hand/agents"/*/; do
      agent="$(basename "$d")"
      mkdir -p "$dest/$hand/agents/$agent"
      cp "$d/SKILL.md" "$dest/$hand/agents/$agent/SKILL.md"
      count=$((count + 1))
    done
  done

  # 工具与配置（供门禁脚本使用）
  cp -r "$REPO_ROOT/core/tools" "$dest/tools" 2>/dev/null || true
  cp -r "$REPO_ROOT/core/env" "$dest/env" 2>/dev/null || true
  cp -r "$REPO_ROOT/core/knowledge" "$dest/knowledge" 2>/dev/null || true
  cp -r "$REPO_ROOT/core/schemas" "$dest/schemas" 2>/dev/null || true
  cp "$REPO_ROOT/catalog.yaml" "$dest/" 2>/dev/null || true

  log "已安装: 4 个手编排器 + $count 个 agent + tools/env/knowledge/schemas"
done

log "────────────────────────────────"
log "完成。重启 runtime 后生效。"
log ""
log "提示：全局模式下知识库路径需为绝对路径；"
log "      若只要在当前项目使用，无需安装——"
log "      把仓库放在工作目录，runtime 会自动读取 AGENTS.md。"
