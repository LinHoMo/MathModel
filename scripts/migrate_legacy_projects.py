"""migrate_legacy_projects.py — Modeling-Harness 旧项目一次性迁移脚本。

背景：技术重构后 Artifact ID 统一为 MH-<TYPE>-<NNNN>（schema 命名空间
modeling_harness:*）。旧 V3 项目（Q001 / M001 / CODE001 / EXEC001 系 Stable
ID，及 mathmodel:v3 schema 引用）在**运行时不再兼容**；本脚本把历史
projects/ 数据一次性迁移到新命名空间。

范围（只动数据层，不改 git 历史 / 不改源码）：
  1. projects/*/state/registry.json   — artifact_id + 契约引用字段（question /
     depends_on / parent / relations / execution_ref / invalidated_by 等）
  2. projects/*/state/decisions.json  — decision_id / invalidated_by / evidence_ids
  3. projects/*/state/evidence_graph.json — from / to / exec_ref
  4. projects/*/state/status.json     — 引用 artifact ID 的字段
  5. projects/*/state/runs/*.json     — run record 的 exec_id / code_id 等
  6. .mathmodel/ 配置目录 → .mh/（存在才处理）
  7. 扫描项目内脚本/配置中的 MATHMODEL_* 环境变量引用，输出替换提示

不迁移：
  - MIR 内容里的外部命名（implementation_ref="CODE-<qid>" 等是外部 Model
    Constructor 的命名空间，不是 harness Artifact ID）
  - 退役类型（S005 paper_section 等）：跳过并报告
  - research/ 与 docs/ 历史证据（冻结）

用法（默认 dry-run，只输出迁移计划）：
    py -3.12 scripts/migrate_legacy_projects.py
    py -3.12 scripts/migrate_legacy_projects.py --apply
    py -3.12 scripts/migrate_legacy_projects.py --project projects/comp-2026-a
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from modeling_harness.runtime.artifacts.ids import (  # noqa: E402
    ARTIFACT_TYPES, IDFormatError, parse_id,
)


# 旧 ID 字面量正则（完整 token 匹配，避免误伤 "CODE-Q001" 等外部命名）
_LEGACY_RE = re.compile(
    r"(?<![A-Za-z0-9])(P|Q|MIR|M|A|DATA|CODE|E|R|F|T|C|D|DELIV|EXEC|VR|DIAG)(\d{1,6})(?![A-Za-z0-9])"
)
_RETIRED = {"S"}  # S005 paper_section 等退役类型：跳过


def _to_mh(aid: str) -> str | None:
    """旧 ID → MH- 格式；非法/退役/非旧格式返回 None。"""
    m = _LEGACY_RE.fullmatch(aid)
    if not m:
        return None
    prefix, num = m.group(1), int(m.group(2))
    if prefix in _RETIRED:
        return None
    try:
        atype, _, _ = parse_id(aid)
    except IDFormatError:
        return None
    from modeling_harness.runtime.artifacts.ids import format_id
    return format_id(atype, num)


def _rewrite_str(value: str, mapping: dict[str, str], changed: set) -> str:
    """把字符串中的旧 ID token 替换为 MH-（保持非 ID 文本不变）。"""
    out = _LEGACY_RE.sub(lambda m: mapping.get(m.group(0), m.group(0)), value)
    if out != value:
        changed.add(value)
    return out


def _rewrite(node, mapping: dict[str, str], changed: set, key: str = ""):
    """递归重写 dict/list 中的字符串 ID 引用。"""
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if isinstance(v, str):
                node[k] = _rewrite_str(v, mapping, changed)
            else:
                _rewrite(v, mapping, changed, k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            if isinstance(v, str):
                node[i] = _rewrite_str(v, mapping, changed)
            else:
                _rewrite(v, mapping, changed, "")


def _migrate_file(path: Path, mapping: dict[str, str], report: dict) -> bool:
    """迁移单个 JSON 文件；返回是否发生改动。"""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report["skipped"].append(f"{path}: 读取失败: {exc}")
        return False
    changed: set = set()
    # artifacts dict：key 也要重写（key 是 artifact_id）
    if isinstance(data, dict) and "artifacts" in data and isinstance(
            data["artifacts"], dict):
        new_arts = {}
        for aid, art in data["artifacts"].items():
            naid = mapping.get(aid, aid)
            if naid != aid:
                changed.add(aid)
            _rewrite(art, mapping, changed)
            if art.get("artifact_id") in mapping:
                art["artifact_id"] = mapping[art["artifact_id"]]
                changed.add(art["artifact_id"])
            new_arts[naid] = art
        data["artifacts"] = new_arts
    _rewrite(data, mapping, changed)
    if not changed:
        return False
    if report["dry_run"]:
        report["planned"].append(
            f"{path.relative_to(REPO)}: {len(changed)} 处旧 ID 引用待迁移")
        return False
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)
    report["migrated"].append(str(path.relative_to(REPO)))
    return True


def _collect_mapping(paths: list[Path], report: dict) -> dict[str, str]:
    """从 registry.json / decisions.json 收集 artifact_id → MH- 映射。"""
    mapping: dict[str, str] = {}
    for p in paths:
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        ids = set()
        if isinstance(data, dict) and "artifacts" in data:
            ids |= set(data["artifacts"].keys())
        if isinstance(data, dict) and "decisions" in data:
            ids |= {d.get("decision_id") for d in data["decisions"]
                    if isinstance(d, dict) and d.get("decision_id")}
        for aid in sorted(ids):
            if aid in mapping:
                continue
            new = _to_mh(aid)
            if new and new != aid:
                mapping[aid] = new
            elif _LEGACY_RE.fullmatch(aid or ""):
                report["skipped"].append(f"{p.name}: {aid}（退役/无法迁移）")
    return mapping


def _migrate_config_dir(project: Path, report: dict) -> None:
    """.mathmodel/ → .mh/（存在才迁移；dry-run 只报告）。"""
    old = project / ".mathmodel"
    new = project / ".mh"
    if old.is_dir():
        if report["dry_run"]:
            report["planned"].append(
                f"{project.name}/.mathmodel/ → .mh/（配置目录迁移）")
        else:
            new.mkdir(parents=True, exist_ok=True)
            for item in old.iterdir():
                (new / item.name).write_bytes(item.read_bytes()
                                              if item.is_file() else b"")
            report["migrated"].append(f"{project.name}/.mathmodel/ → .mh/")
    env_hits = []
    for f in project.rglob("*"):
        if f.is_file() and f.suffix in (".py", ".toml", ".yaml", ".yml", ".env",
                                        ".json", ".md"):
            try:
                txt = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for m in re.finditer(r"MATHMODEL_[A-Z0-9_]+", txt):
                env_hits.append(f"{f.relative_to(project)}: {m.group(0)}")
    if env_hits:
        report["env_refs"].extend(env_hits)


def main() -> int:
    ap = argparse.ArgumentParser(description="Modeling-Harness 旧项目一次性迁移")
    ap.add_argument("--project", default=None,
                    help="指定单个项目目录（默认扫描全部 projects/）")
    ap.add_argument("--dry-run", action="store_true",
                    help="只输出迁移计划，不写盘（默认行为，显式声明亦可）")
    ap.add_argument("--apply", action="store_true",
                    help="实际执行迁移（默认 dry-run 只输出计划）")
    args = ap.parse_args()

    if args.project:
        roots = [Path(args.project)]
    else:
        roots = [d for d in (REPO / "projects").iterdir() if d.is_dir()] \
            if (REPO / "projects").is_dir() else []

    report = {"dry_run": not args.apply, "planned": [], "migrated": [],
              "skipped": [], "env_refs": []}
    if not roots:
        print("projects/ 无历史项目，无需迁移。")
        return 0

    for proj in roots:
        state = proj / "state"
        state_files = [
            state / "registry.json", state / "decisions.json",
            state / "evidence_graph.json", state / "status.json",
        ] + sorted((state / "runs").glob("*.json")) \
            if (state / "runs").is_dir() else []
        state_files = [p for p in state_files if p.exists()]
        mapping = _collect_mapping([state / "registry.json",
                                    state / "decisions.json"], report)
        if not mapping:
            report["skipped"].append(f"{proj.name}: 未发现旧 V3 Stable ID")
        for sf in state_files:
            _migrate_file(sf, mapping, report)
        _migrate_config_dir(proj, report)

    mode = "DRY-RUN（未写盘）" if report["dry_run"] else "APPLY"
    print(f"=== 迁移报告（{mode}）===")
    for line in report["planned"]:
        print(f"  [待迁移] {line}")
    for line in report["migrated"]:
        print(f"  [已迁移] {line}")
    for line in report["skipped"]:
        print(f"  [跳过]   {line}")
    for line in report["env_refs"]:
        print(f"  [环境变量引用] {line}")
    if report["dry_run"]:
        print("\n确认无误后运行： py -3.12 scripts/migrate_legacy_projects.py --apply")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
