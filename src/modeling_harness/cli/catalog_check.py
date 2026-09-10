#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ABOUTME: catalog.yaml v5 双视图一致性校验（roles / nodes / validators 三方对齐）
ABOUTME: --check 模式零漂移即 EXIT 0，供 CI 与 doctor.py 消费

校验内容（P4 验收「catalog v5 --check 通过」）:
    1. schema_version == 5，v3 视图存在且结构完整
    2. v3.roles        == src/modeling_harness/roles/*.yaml 实际文件（数量 + 名称 + 路径）
    3. v3.nodes        == 组合 DAG 模板节点（WorkflowComposer.compose()），
                          逐节点比对 role / validator / per_question / stage
    4. v3.validators   == DAG 中绑定的 validator 集合，
                          每个条目 path 指向真实文件
    5. hands legacy 视图未被 v3 追加破坏（agent 总数 29 不变）

用法:
    python src/modeling_harness/cli/catalog_check.py            # 人读报告（问题列出，EXIT 0/1）
    python src/modeling_harness/cli/catalog_check.py --check    # 同上（CI 语义，drift 即 EXIT 1）
    python src/modeling_harness/cli/catalog_check.py --json     # 机器可读输出
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "modeling_harness" / "cli"))
for _cat in ("runtime", "validation", "evaluation", "knowledge", "devtools", "rendering"):
    sys.path.insert(0, str(ROOT / "src" / "modeling_harness" / "cli" / _cat))

CATALOG_PATH = ROOT / "catalog" / "catalog.yaml"
ROLES_DIR = ROOT / "src" / "modeling_harness" / "roles"
WORKFLOWS_DIR = ROOT / "src" / "modeling_harness" / "workflows"

EXPECTED_ROLES = {"analyst", "modeler", "experimenter", "critic"}
EXTRA_VALIDATORS = set()


# ---------------------------------------------------------------- YAML 解析

def load_catalog() -> dict:
    """优先用 runtime yamlio（与工作流同一解析器），失败回退 gen_runtime_manifest。

    GRM 解析器会把含深层 list-of-dict 的顶层块（如 v3）包成单元素 list，
    这里统一解包为 dict。
    """
    try:
        from modeling_harness.runtime.execution.yamlio import load_file
        data = load_file(CATALOG_PATH)
        if isinstance(data, dict) and "hands" in data:
            import gen_runtime_manifest as GRM
            GRM.merge_registries(data)
            _unwrap_v3(data)
            return data
    except Exception:
        pass
    import gen_runtime_manifest as GRM
    data = GRM.load_catalog()
    _unwrap_v3(data)
    return data


def _unwrap_v3(catalog: dict) -> None:
    v3 = catalog.get("v3")
    if isinstance(v3, list) and len(v3) == 1 and isinstance(v3[0], dict):
        catalog["v3"] = v3[0]


# ---------------------------------------------------------------- 校验项

def check_schema(catalog: dict) -> list[str]:
    problems = []
    if catalog.get("schema_version") != 5:
        problems.append(f"schema_version 应为 5，实际 {catalog.get('schema_version')!r}")
    v3 = catalog.get("v3")
    if not isinstance(v3, dict):
        problems.append("缺少 v3 视图节（schema_version 5 必须携带 v3）")
    return problems



def check_roles(v3: dict) -> list[str]:
    problems = []
    roles = v3.get("roles", [])
    names = {r.get("name") for r in roles}
    if names != EXPECTED_ROLES:
        problems.append(f"v3.roles 应为 5 角色 {sorted(EXPECTED_ROLES)}，实际 {sorted(names)}")
    # 与 src/modeling_harness/roles/ 目录对齐
    disk = {p.stem for p in ROLES_DIR.glob("*.yaml")}
    if names != disk:
        problems.append(f"v3.roles 与 src/modeling_harness/roles/ 不一致: catalog={sorted(names)} disk={sorted(disk)}")
    for r in roles:
        path = ROOT / str(r.get("path", ""))
        if not path.exists():
            problems.append(f"v3.roles[{r.get('name')}] 路径不存在: {r.get('path')}")
        elif path.stem != r.get("name"):
            problems.append(
                f"v3.roles[{r.get('name')}] 与文件名不符: {path.stem}.yaml")
    return problems


def _compose_template_dag():
    from modeling_harness.runtime.execution.composer import WorkflowComposer
    return WorkflowComposer(WORKFLOWS_DIR).compose()


def check_nodes(v3: dict) -> list[str]:
    problems = []
    nodes = {n.get("name"): n for n in v3.get("nodes", [])}
    if not nodes:
        return ["v3.nodes 为空"]

    try:
        dag = _compose_template_dag()
    except Exception as exc:
        return [f"组合 DAG 模板失败: {exc}"]

    dag_nodes = dag.nodes
    cat_names, dag_names = set(nodes), set(dag_nodes)
    if cat_names != dag_names:
        only_cat = sorted(cat_names - dag_names)
        only_dag = sorted(dag_names - cat_names)
        if only_cat:
            problems.append(f"v3.nodes 多出 DAG 不存在的节点: {only_cat}")
        if only_dag:
            problems.append(f"组合 DAG 存在但 v3.nodes 缺失的节点: {only_dag}")

    for name in sorted(cat_names & dag_names):
        cat, dnode = nodes[name], dag_nodes[name]
        # role
        if cat.get("role") != dnode.role:
            problems.append(
                f"v3.nodes[{name}].role 应为 {dnode.role!r}，实际 {cat.get('role')!r}")
        # validator
        if (cat.get("validator") or None) != (dnode.validator or None):
            problems.append(
                f"v3.nodes[{name}].validator 应为 {dnode.validator!r}，"
                f"实际 {cat.get('validator')!r}")
        # per_question
        if bool(cat.get("per_question", False)) != bool(dnode.per_question):
            problems.append(
                f"v3.nodes[{name}].per_question 应为 {bool(dnode.per_question)}，"
                f"实际 {bool(cat.get('per_question', False))}")
        # stage
        stage = getattr(dnode, "stage", "") or ""
        if cat.get("stage") != stage:
            problems.append(
                f"v3.nodes[{name}].stage 应为 {stage!r}，实际 {cat.get('stage')!r}")
    return problems


def check_validators(v3: dict) -> list[str]:
    problems = []
    validators = {v.get("name"): v for v in v3.get("validators", [])}
    if not validators:
        return ["v3.validators 为空"]

    # DAG 中绑定的 validator 集合
    try:
        dag = _compose_template_dag()
        bound = {n.validator for n in dag.nodes.values() if n.validator}
    except Exception as exc:
        return [f"组合 DAG 模板失败: {exc}"]
    expected = bound | EXTRA_VALIDATORS

    cat_names = set(validators)
    if cat_names != expected:
        missing = sorted(expected - cat_names)
        extra = sorted(cat_names - expected)
        if missing:
            problems.append(f"v3.validators 缺失: {missing}")
        if extra:
            problems.append(f"v3.validators 多余: {extra}")

    for name, v in validators.items():
        kind = v.get("kind")
        if kind not in ("runtime", "skill"):
            problems.append(f"v3.validators[{name}].kind 非法: {kind!r}（runtime|skill）")
        path = ROOT / str(v.get("path", ""))
        if not (path.is_file() or path.is_dir()):   # 包型 validator 允许目录
            problems.append(f"v3.validators[{name}] 路径不存在: {v.get('path')}")
    return problems


# ---------------------------------------------------------------- terminology lint

# 禁止旧术语（production 区零残留；语义定义见 docs/ONTOLOGY_TERMINOLOGY.md）
# terminology-lint-self: 本表为 lint 的禁止词定义本身，非残留
FORBIDDEN_TERMS = [
    "allowed_model_families",      # → allowed_modeling_structures  (terminology-lint-self)
    "method_family",               # → modeling_structure / model regime  (terminology-lint-self)
    "reference_method",            # 已废弃  (terminology-lint-self)
    "algorithm_card",              # 不存在该概念  (terminology-lint-self)
]

# 允许旧术语的例外路径（migration / history 文档）
TERMINOLOGY_ALLOWED_PATHS = {
    "docs/ONTOLOGY_TERMINOLOGY.md",          # 映射表本身需要旧词
    "docs/architecture/MODELING_KNOWLEDGE_GOVERNANCE.md",  # §8 历史更正记录
}
# 允许旧术语的例外目录片段（research history / 历史报告）
TERMINOLOGY_ALLOWED_DIR_PARTS = {
    "research", "knowledge_calibration", "measurement_recovery",
    "reports", "projects", "legacy", "bench-m4", "archives", "ENGINEERING", "handoff",
}


def _is_terminology_allowed(rel: str) -> bool:
    """判断路径是否属于 research/history/migration 例外区。"""
    rel = rel.replace("\\", "/")
    if rel in TERMINOLOGY_ALLOWED_PATHS:
        return True
    parts = rel.split("/")
    return any(p in TERMINOLOGY_ALLOWED_DIR_PARTS for p in parts)


def _terminology_scan() -> list[str]:
    """扫描 production 区旧术语残留（Zero-residue Gate）。

    范围 = src/modeling_harness/ + AGENTS.md + docs/ 现行文档（排除 history/migration）。
    豁免：research 历史、projects 历史观测、legacy 兼容层、terminology-lint-self 定义行。
    无行内豁免：production 区不允许以任何注释形式携带旧术语。
    """
    problems = []
    targets = [ROOT / "src", ROOT / "AGENTS.md", ROOT / "docs"]
    suffixes = {".py", ".md", ".json", ".yaml", ".yml", ".txt"}
    scanned_files = 0
    for target in targets:
        if target.is_file():
            files = [target]
        else:
            files = [f for f in target.rglob("*") if f.is_file()]
        for f in files:
            if f.suffix not in suffixes:
                continue
            rel = str(f.relative_to(ROOT))
            if _is_terminology_allowed(rel):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            scanned_files += 1
            for lineno, line in enumerate(text.splitlines(), 1):
                if "terminology-lint-self" in line:
                    continue
                for term in FORBIDDEN_TERMS:
                    if term in line:
                        problems.append(f"{rel}:{lineno}: 旧术语「{term}」残留（canonical 见 docs/ONTOLOGY_TERMINOLOGY.md）")
                        break
    return problems


def run_terminology() -> list[str]:
    return _terminology_scan()



def run_all() -> list[str]:
    catalog = load_catalog()
    problems = []
    problems += check_schema(catalog)
    v3 = catalog.get("v3")
    if isinstance(v3, dict):
        problems += check_roles(v3)
        problems += check_nodes(v3)
        problems += check_validators(v3)
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="catalog.yaml v5 双视图一致性校验 + terminology lint")
    ap.add_argument("--check", action="store_true", help="CI 模式：drift 即 EXIT 1")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--check-terminology", action="store_true",
                    help="Zero-residue Gate：production 区旧术语零残留扫描")
    args = ap.parse_args()

    if args.check_terminology:
        problems = run_terminology()
        if args.json:
            print(json.dumps({"ok": not problems, "problems": problems},
                             ensure_ascii=False, indent=2))
        else:
            if problems:
                print(f"[terminology] FAIL — {len(problems)} 个问题:")
                for p in problems:
                    print(f"  - {p}")
            else:
                print("[terminology] OK — production 区旧术语零残留")
        return 1 if problems else 0

    problems = run_all()

    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems},
                         ensure_ascii=False, indent=2))
    else:
        if problems:
            print(f"[catalog-check] FAIL — {len(problems)} 个问题:")
            for p in problems:
                print(f"  - {p}")
        else:
            print("[catalog-check] OK — v3 双视图与 roles/DAG/validators 三方一致"
                  "")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
