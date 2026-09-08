#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""p14_integrity_gate.py — P14 integrity gate (G0–G7).

实现 RUNBOOK_P14_1.md §4/§5/§6 的冻结语义（本脚本只实现语义，不定义语义）：
  G0_SCHEMA            结构与 envelope / id / 枚举 / content_sha256 重算一致
  G1_PROVENANCE        spec.model_artifact_hash == 冻结表 && artifact 文件实测一致
  G2_DETERMINISM       每个 completed Execution 有 ≥1 条 replay match=true
  G3_RESULT_BINDING    Result→Execution 1:1 且引用 hash 一致；Execution→Spec 链一致
  G4_EVIDENCE_BINDING  Evidence→Result 引用一致；Claim 的 evidence id 可解析
  G5_INVALIDATION      失效传播规则（RUNBOOK §5，1–4 条全部强制）
  G6_C1_CONTAINMENT    C1 checklist：禁增词表 + 每条锚定 artifact 元素
  G7_CLAIM_ORIGIN      Claim.model_origin.anchor 必须出现在冻结 artifact 文本中

用法:
  python p14_integrity_gate.py <run_dir>    # 校验正式运行（跳过 _ 前缀目录）
  python p14_integrity_gate.py --selftest   # 合成图自检：合法图 PASS + 注入缺陷逐一 FAIL
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # research/P14/scripts/ → repo 根

# ---------------------------------------------------------------- 冻结表（RUNBOOK §1）
FROZEN_ARTIFACTS = {
    ("2020_B", "MMA"): {
        "path": "research/P13-3D-R2/output/artifacts/2020_B_MMA.json",
        "sha256": "3da8d82ee6708d4339becefa3790f93c5f5cff0e168e88eb298a84f2a25571fa",
    },
    ("2024_B", "B1_F"): {
        "path": "research/P13-3D-R2/output/artifacts/2024_B_B1_F.json",
        "sha256": "a808a0f7edece952e69205c06c7647e40ba29fbe92e078a5e13234419c388e6d",
    },
    ("2022_C", "B1_F"): {
        "path": "research/P13-3D-R2/output/artifacts/2022_C_B1_F.json",
        "sha256": "c15924bee329867701c502d768b338b6c8782f22cbc1bb5ce37b66ccf5468012",
    },
}

ENTITY_TYPES = ("experiment_spec", "execution", "result", "evidence", "claim")
SPEC_DIR, EXE_DIR, RES_DIR, EVI_DIR, CLM_DIR = (
    "specs", "executions", "results", "evidences", "claims")
TYPE_DIRS = {"experiment_spec": SPEC_DIR, "execution": EXE_DIR, "result": RES_DIR,
             "evidence": EVI_DIR, "claim": CLM_DIR}
ID_PREFIX = {"experiment_spec": "P14-SPEC", "execution": "P14-EXE", "result": "P14-RES",
             "evidence": "P14-EVI", "claim": "P14-CLM"}
EXEC_STATUSES = ("completed", "failed", "timeout", "diverged")
RESULT_STATUSES = ("valid", "stale", "invalid")
EVIDENCE_STATUSES = ("valid", "stale", "invalid")
CLAIM_STATUSES = ("supported", "refuted", "untested", "unresolved", "stale", "invalid")
EXP_TYPES = ("sensitivity", "robustness", "ablation", "extreme_value", "fit", "simulation")
ORIGIN_TYPES = ("objective", "constraint", "mechanism", "assumption", "parameter", "variable")
POSITIONS = ("supports", "refutes", "characterizes")

# G6 禁增词表（RUNBOOK §2，FROZEN）
FORBIDDEN_RE = [
    r"(新增|添加|增加|引入)(变量|参数|约束|机制|结论|假设)",
    r"修改假设", r"替换假设", r"重新设定参数", r"额外假设",
]

RUN_ID_RE = re.compile(r"^P14-[0-9]{8}-[0-9]{2}$")
ENTITY_ID_RE = re.compile(r"^P14-(SPEC|EXE|RES|EVI|CLM)[0-9]{3}$")


# ---------------------------------------------------------------- 基础
def canonical_hash(entity: dict) -> str:
    e = dict(entity)
    e.pop("content_sha256", None)
    blob = json.dumps(e, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_entities(run: Path):
    out = {}
    for t, sub in TYPE_DIRS.items():
        out[t] = {}
        d = run / sub
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                out[t][f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                out[t][f.stem] = {"__parse_error__": str(e)}
    return out


def cjk_fourgrams(text: str) -> set:
    s = re.sub(r"\s+", "", text)
    return {s[i:i + 4] for i in range(len(s) - 3)}


def anchor_vocabulary(artifact_text: str) -> set:
    """锚定词表：latin 符号 token（≥2 位）+ 全文 CJK 4-gram。"""
    vocab = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{1,}", artifact_text))
    vocab |= cjk_fourgrams(artifact_text)
    return vocab


# ---------------------------------------------------------------- 门禁
def check_run(run: Path, frozen: dict) -> list:
    """返回 [(code, message)]；空列表 = 全绿。"""
    errors = []

    def err(code, msg):
        errors.append((code, msg))

    man_p = run / "manifest.json"
    if not man_p.exists():
        err("G0_SCHEMA", "manifest.json 缺失")
        return errors
    try:
        man = json.loads(man_p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        err("G0_SCHEMA", f"manifest.json 解析失败: {e}")
        return errors
    ent = load_entities(run)

    # ---------- G0 结构 ----------
    if man.get("prereg_version") != "p14.v1":
        err("G0_SCHEMA", "manifest.prereg_version != p14.v1")
    if not RUN_ID_RE.match(str(man.get("run_id", ""))):
        err("G0_SCHEMA", f"manifest.run_id 非法: {man.get('run_id')!r}")
    for t in ENTITY_TYPES:
        for eid, e in ent[t].items():
            if "__parse_error__" in e:
                err("G0_SCHEMA", f"{eid}: JSON 解析失败")
                continue
            if e.get("entity_type") != t:
                err("G0_SCHEMA", f"{eid}: entity_type={e.get('entity_type')!r} 与目录不符")
            if not ENTITY_ID_RE.match(str(e.get("entity_id", ""))) or e.get("entity_id") != eid:
                err("G0_SCHEMA", f"{eid}: entity_id 与文件名不一致或格式非法")
            if e.get("schema_version") != "p14.v1":
                err("G0_SCHEMA", f"{eid}: schema_version != p14.v1")
            if e.get("run_id") != man.get("run_id"):
                err("G0_SCHEMA", f"{eid}: run_id 与 manifest 不一致")
            for k in ("created_at", "content_sha256", "parent_ref"):
                if k not in e:
                    err("G0_SCHEMA", f"{eid}: 缺字段 {k}")
            pref = e.get("parent_ref") or {}
            if set(pref) != {"entity_type", "entity_id", "content_sha256"}:
                err("G0_SCHEMA", f"{eid}: parent_ref 字段不完整")
            if e.get("content_sha256") != canonical_hash(e):
                err("G0_SCHEMA", f"{eid}: content_sha256 重算不一致")
    # 逐类型必填与枚举
    for eid, s in ent["experiment_spec"].items():
        for k in ("question_id", "condition", "model_artifact_ref", "verification_questions", "experiments", "generator"):
            if k not in s:
                err("G0_SCHEMA", f"{eid}: 缺字段 {k}")
        if s.get("condition") not in ("C0", "C1"):
            err("G0_SCHEMA", f"{eid}: condition 非法")
        if s.get("condition") == "C0" and s.get("verification_questions"):
            err("G0_SCHEMA", f"{eid}: C0 的 verification_questions 必须为空")
        mar = s.get("model_artifact_ref") or {}
        if (mar.get("question_id"), mar.get("arm")) not in frozen:
            err("G1_PROVENANCE", f"{eid}: (question, arm) 不在冻结表: "
                                 f"{mar.get('question_id')}/{mar.get('arm')}")
        for x in s.get("experiments", []) or []:
            for k in ("experiment_id", "title", "purpose", "type", "procedure", "metrics", "seed", "runs"):
                if k not in x:
                    err("G0_SCHEMA", f"{eid}/{x.get('experiment_id')}: 缺字段 {k}")
            if x.get("type") not in EXP_TYPES:
                err("G0_SCHEMA", f"{eid}/{x.get('experiment_id')}: type 非法")
            if x.get("seed") != 42:
                err("G0_SCHEMA", f"{eid}/{x.get('experiment_id')}: seed != 42")
            if not isinstance(x.get("runs"), int) or x.get("runs", 0) < 1:
                err("G0_SCHEMA", f"{eid}/{x.get('experiment_id')}: runs < 1")
    for eid, x in ent["execution"].items():
        for k in ("spec_ref", "experiment_id", "runner", "seed", "runs", "status", "log_path", "env_fingerprint"):
            if k not in x:
                err("G0_SCHEMA", f"{eid}: 缺字段 {k}")
        if x.get("status") not in EXEC_STATUSES:
            err("G0_SCHEMA", f"{eid}: status 非法")
        if x.get("seed") != 42:
            err("G0_SCHEMA", f"{eid}: seed != 42")
        r = x.get("runner") or {}
        if r.get("backend") != "python-sandbox" or "code_sha256" not in r:
            err("G0_SCHEMA", f"{eid}: runner 契约不符")
    for eid, r in ent["result"].items():
        for k in ("execution_ref", "data", "status"):
            if k not in r:
                err("G0_SCHEMA", f"{eid}: 缺字段 {k}")
        if r.get("status") not in RESULT_STATUSES:
            err("G0_SCHEMA", f"{eid}: status 非法")
    for eid, v in ent["evidence"].items():
        for k in ("result_ref", "interpretation", "position", "target_claim_desc", "status"):
            if k not in v:
                err("G0_SCHEMA", f"{eid}: 缺字段 {k}")
        if v.get("position") not in POSITIONS:
            err("G0_SCHEMA", f"{eid}: position 非法")
        if v.get("status") not in EVIDENCE_STATUSES:
            err("G0_SCHEMA", f"{eid}: status 非法")
    for eid, c in ent["claim"].items():
        for k in ("text", "model_origin", "supported_by", "refuted_by", "status"):
            if k not in c:
                err("G0_SCHEMA", f"{eid}: 缺字段 {k}")
        if c.get("status") not in CLAIM_STATUSES:
            err("G0_SCHEMA", f"{eid}: status 非法")
        mo = c.get("model_origin") or {}
        if mo.get("element_type") not in ORIGIN_TYPES or not mo.get("anchor"):
            err("G0_SCHEMA", f"{eid}: model_origin 契约不符")

    # ---------- G1 provenance ----------
    man_fa = man.get("frozen_artifacts") or {}
    norm = {k: (v or {}).get("sha256") for k, v in man_fa.items()} if man_fa else {}
    want = {f"{q}/{a}": v["sha256"] for (q, a), v in frozen.items()}
    if man_fa and norm != want:
        err("G1_PROVENANCE", f"manifest.frozen_artifacts 与冻结表不一致: {norm}")
    for eid, s in ent["experiment_spec"].items():
        mar = s.get("model_artifact_ref") or {}
        key = (mar.get("question_id"), mar.get("arm"))
        if key in frozen:
            if mar.get("model_artifact_hash") != frozen[key]["sha256"]:
                err("G1_PROVENANCE", f"{eid}: model_artifact_hash != 冻结表")
            ap = ROOT / mar.get("path", "")
            if not ap.exists() or sha256_file(ap) != frozen[key]["sha256"]:
                err("G1_PROVENANCE", f"{eid}: artifact 文件缺失或实测 hash 不符: {mar.get('path')}")

    # ---------- G3 result binding（先于 G2/G4，构建索引） ----------
    exe_by_id = ent["execution"]
    spec_by_id = ent["experiment_spec"]
    res_by_exe = {}
    for rid, r in ent["result"].items():
        ref = r.get("execution_ref") or {}
        xid = ref.get("entity_id")
        if xid not in exe_by_id:
            err("G3_RESULT_BINDING", f"{rid}: execution_ref 指向不存在的 {xid!r}")
            continue
        if ref.get("content_sha256") != canonical_hash(exe_by_id[xid]):
            err("G3_RESULT_BINDING", f"{rid}: execution_ref.hash 与 {xid} 实测不一致")
        res_by_exe.setdefault(xid, []).append(rid)
    for xid, rids in res_by_exe.items():
        if len(rids) > 1:
            err("G3_RESULT_BINDING", f"Execution {xid} 被多个 Result 绑定: {rids}")
    for xid, x in exe_by_id.items():
        sref = x.get("spec_ref") or {}
        sid = sref.get("entity_id")
        if sid not in spec_by_id:
            err("G3_RESULT_BINDING", f"{xid}: spec_ref 指向不存在的 {sid!r}")
            continue
        if sref.get("content_sha256") != canonical_hash(spec_by_id[sid]):
            err("G3_RESULT_BINDING", f"{xid}: spec_ref.hash 与 {sid} 实测不一致")
        exp_ids = {e.get("experiment_id") for e in spec_by_id[sid].get("experiments", [])}
        if x.get("experiment_id") not in exp_ids:
            err("G3_RESULT_BINDING", f"{xid}: experiment_id {x.get('experiment_id')!r} 不在 {sid} 中")

    # ---------- G2 determinism ----------
    replays = man.get("replays") or []
    completed = {xid for xid, x in exe_by_id.items() if x.get("status") == "completed"}
    ok_replayed = set()
    for rp in replays:
        xid = rp.get("execution_id")
        if xid not in exe_by_id:
            err("G2_DETERMINISM", f"replay 指向不存在的 Execution {xid!r}")
            continue
        if rp.get("match") is True:
            ok_replayed.add(xid)
        if rp.get("result_sha256_original") != rp.get("result_sha256_replay") and rp.get("match") is True:
            err("G2_DETERMINISM", f"{xid}: replay match=true 但两个 result hash 不同")
    for xid in sorted(completed - ok_replayed):
        err("G2_DETERMINISM", f"completed Execution {xid} 缺少 match=true 的 replay 记录")

    # ---------- G4 evidence binding ----------
    evi_by_id = ent["evidence"]
    for vid, v in ent["evidence"].items():
        ref = v.get("result_ref") or {}
        rid = ref.get("entity_id")
        if rid not in ent["result"]:
            err("G4_EVIDENCE_BINDING", f"{vid}: result_ref 指向不存在的 {rid!r}")
            continue
        if ref.get("content_sha256") != canonical_hash(ent["result"][rid]):
            err("G4_EVIDENCE_BINDING", f"{vid}: result_ref.hash 与 {rid} 实测不一致")
    for cid, c in ent["claim"].items():
        for l in ("supported_by", "refuted_by"):
            for vid in c.get(l, []) or []:
                if vid not in evi_by_id:
                    err("G4_EVIDENCE_BINDING", f"{cid}: {l} 引用不存在的 Evidence {vid!r}")

    # ---------- G5 invalidation ----------
    def result_status_of(xid):
        rids = res_by_exe.get(xid, [])
        return ent["result"][rids[0]].get("status") if len(rids) == 1 else None

    bad_exec = {xid for xid, x in exe_by_id.items()
                if x.get("status") in ("failed", "timeout", "diverged")}
    stale_exec = {rp.get("execution_id") for rp in replays if rp.get("match") is False}
    for xid in sorted(bad_exec):
        st = result_status_of(xid)
        if st is not None and st != "invalid":
            err("G5_INVALIDATION", f"Execution {xid} 失败，但其 Result.status={st!r}（应为 invalid）")
    for xid in sorted(stale_exec - bad_exec):
        st = result_status_of(xid)
        if st is not None and st not in ("stale", "invalid"):
            err("G5_INVALIDATION", f"Execution {xid} replay 不一致，但其 Result.status={st!r}")
    for vid, v in ent["evidence"].items():
        rid = (v.get("result_ref") or {}).get("entity_id")
        rst = ent["result"].get(rid, {}).get("status") if rid in ent["result"] else None
        if rst == "invalid" and v.get("status") != "invalid":
            err("G5_INVALIDATION", f"Evidence {vid} 绑定 invalid Result，但 status={v.get('status')!r}")
        if rst == "stale" and v.get("status") == "valid":
            err("G5_INVALIDATION", f"Evidence {vid} 绑定 stale Result，但 status=valid")
    for cid, c in ent["claim"].items():
        sup = [evi_by_id[i] for i in (c.get("supported_by") or []) if i in evi_by_id]
        ref = [evi_by_id[i] for i in (c.get("refuted_by") or []) if i in evi_by_id]
        valid_sup = [e for e in sup if e.get("status") == "valid"]
        valid_ref = [e for e in ref if e.get("status") == "valid"]
        any_inv_sup = any(e.get("status") == "invalid" for e in sup)
        st = c.get("status")
        if valid_ref and st != "refuted":
            err("G5_INVALIDATION", f"Claim {cid} 存在有效反驳证据，但 status={st!r}")
        if any_inv_sup and st == "supported":
            err("G5_INVALIDATION", f"Claim {cid} 的支持证据含 invalid，但 status=supported")
        if sup and not valid_sup and st not in ("stale", "invalid"):
            err("G5_INVALIDATION", f"Claim {cid} 全部支持证据 stale/invalid，但 status={st!r}")
        if not sup and not ref and st not in ("untested", "unresolved"):
            err("G5_INVALIDATION", f"Claim {cid} 无任何证据，status 必须为 untested/unresolved（现 {st!r}）")
        if st == "unresolved" and not (c.get("supported_by") or []):
            err("G5_INVALIDATION", f"Claim {cid} status=unresolved 但未绑定任何 Evidence")

    # ---------- G6 C1 containment + G7 claim origin ----------
    art_text_cache = {}
    for eid, s in ent["experiment_spec"].items():
        mar = s.get("model_artifact_ref") or {}
        key = (mar.get("question_id"), mar.get("arm"))
        if key not in frozen:
            continue
        ap = ROOT / mar.get("path", "")
        if not ap.exists():
            continue
        art_text_cache[key] = ap.read_text(encoding="utf-8")
    for eid, s in ent["experiment_spec"].items():
        if s.get("condition") != "C1":
            continue
        key = ((s.get("model_artifact_ref") or {}).get("question_id"),
               (s.get("model_artifact_ref") or {}).get("arm"))
        text = art_text_cache.get(key, "")
        vocab = anchor_vocabulary(text)
        for i, item in enumerate(s.get("verification_questions") or [], 1):
            for pat in FORBIDDEN_RE:
                if re.search(pat, item):
                    err("G6_C1_CONTAINMENT", f"{eid}: checklist[{i}] 触碰禁增词表（{pat!r}）: {item[:40]}…")
            if not (set(re.findall(r"[A-Za-z_][A-Za-z0-9_]{1,}", item)) & vocab
                    or (cjk_fourgrams(item) & vocab)):
                err("G6_C1_CONTAINMENT", f"{eid}: checklist[{i}] 无法锚定到 artifact 元素: {item[:40]}…")
    all_art_text = "\n".join(art_text_cache.values())
    for cid, c in ent["claim"].items():
        anchor = (c.get("model_origin") or {}).get("anchor", "")
        if anchor and anchor not in all_art_text:
            err("G7_CLAIM_ORIGIN", f"{cid}: anchor 在冻结 artifact 中找不到: {anchor[:40]}…")
    return errors


# ---------------------------------------------------------------- selftest
def _fixture(tmp: Path, frozen: dict):
    """合成一个合法 run；返回 (run_dir, artifact_path)。"""
    art = {
        "question_id": "T0_X",
        "variables": [{"name": "状态", "symbol": "s_t"}],
        "parameters": [{"name": "消耗", "symbol": "c_w"}],
        "assumptions": ["资源消耗随速度单调递增"],
        "mechanisms": [{"id": "M1", "text": "消耗量等于速度乘以时间"}],
        "objective": ["最小化总消耗"],
        "constraints": ["0 <= s_t <= 1"],
    }
    art_path = tmp / "artifact_T0_X.json"
    art_path.write_text(json.dumps(art, ensure_ascii=False), encoding="utf-8")
    art_hash = sha256_file(art_path)

    run = tmp / "P14-20260907-99"
    for sub in TYPE_DIRS.values():
        (run / sub).mkdir(parents=True)

    spec = {
        "entity_type": "experiment_spec", "entity_id": "P14-SPEC001",
        "schema_version": "p14.v1", "run_id": "P14-20260907-99",
        "created_at": "2026-09-07T00:00:00",
        "question_id": "T0_X", "condition": "C1",
        "model_artifact_ref": {"question_id": "T0_X", "arm": "MMA",
                               "path": str(art_path), "model_artifact_hash": art_hash},
        "verification_questions": ["灵敏度分析：消耗系数 c_w 扰动时，最小化总消耗 的最优解如何变化？"],
        "experiments": [{"experiment_id": "EXP-1", "title": "灵敏度", "purpose": "检验 M1",
                         "type": "sensitivity", "procedure": "扰动 c_w 重跑",
                         "metrics": ["total_cost"], "seed": 42, "runs": 2}],
        "generator": "selftest",
        "parent_ref": {"entity_type": "model_artifact", "entity_id": "artifact_T0_X.json",
                       "content_sha256": art_hash},
    }
    spec["content_sha256"] = canonical_hash(spec)
    (run / SPEC_DIR / "P14-SPEC001.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")

    code_hash = hashlib.sha256(b"code").hexdigest()
    exes = {}
    for eid, status in (("P14-EXE001", "completed"), ("P14-EXE002", "failed")):
        e = {"entity_type": "execution", "entity_id": eid, "schema_version": "p14.v1",
             "run_id": "P14-20260907-99", "created_at": "2026-09-07T00:01:00",
             "spec_ref": {"entity_type": "experiment_spec", "entity_id": "P14-SPEC001",
                          "content_sha256": spec["content_sha256"]},
             "experiment_id": "EXP-1",
             "runner": {"backend": "python-sandbox", "python_version": "3.12",
                        "entrypoint": "exp1.py", "code_sha256": code_hash},
             "seed": 42, "runs": 2, "status": status,
             "log_path": f"logs/{eid}.log", "env_fingerprint": "py3.12-win64",
             "parent_ref": {"entity_type": "experiment_spec", "entity_id": "P14-SPEC001",
                            "content_sha256": spec["content_sha256"]}}
        e["content_sha256"] = canonical_hash(e)
        exes[eid] = e
        (run / EXE_DIR / f"{eid}.json").write_text(
            json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")

    results = {}
    for rid, xid, status in (("P14-RES001", "P14-EXE001", "valid"),
                             ("P14-RES002", "P14-EXE002", "invalid")):
        r = {"entity_type": "result", "entity_id": rid, "schema_version": "p14.v1",
             "run_id": "P14-20260907-99", "created_at": "2026-09-07T00:02:00",
             "execution_ref": {"entity_type": "execution", "entity_id": xid,
                               "content_sha256": exes[xid]["content_sha256"]},
             "data": {"total_cost": [1.0, 2.0]}, "status": status,
             "parent_ref": {"entity_type": "execution", "entity_id": xid,
                            "content_sha256": exes[xid]["content_sha256"]}}
        r["content_sha256"] = canonical_hash(r)
        results[rid] = r
        (run / RES_DIR / f"{rid}.json").write_text(
            json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")

    evids = {}
    for vid, rid, status, pos in (("P14-EVI001", "P14-RES001", "valid", "supports"),
                                  ("P14-EVI002", "P14-RES002", "invalid", "supports")):
        v = {"entity_type": "evidence", "entity_id": vid, "schema_version": "p14.v1",
             "run_id": "P14-20260907-99", "created_at": "2026-09-07T00:03:00",
             "result_ref": {"entity_type": "result", "entity_id": rid,
                            "content_sha256": results[rid]["content_sha256"]},
             "interpretation": "消耗随 c_w 单调", "position": pos,
             "target_claim_desc": "最优消耗单调性", "status": status,
             "parent_ref": {"entity_type": "result", "entity_id": rid,
                            "content_sha256": results[rid]["content_sha256"]}}
        v["content_sha256"] = canonical_hash(v)
        evids[vid] = v
        (run / EVI_DIR / f"{vid}.json").write_text(
            json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")

    claims = [
        ("P14-CLM001", "最优总消耗随 c_w 单调递增", "mechanism", "消耗量等于速度乘以时间",
         ["P14-EVI001"], [], "supported"),
        ("P14-CLM002", "约束 0 <= s_t <= 1 下可行", "constraint", "0 <= s_t <= 1",
         ["P14-EVI002"], [], "stale"),
        ("P14-CLM003", "未检验的极端情形", "objective", "最小化总消耗", [], [], "untested"),
    ]
    for cid, text, etype, anchor, sup, ref, status in claims:
        c = {"entity_type": "claim", "entity_id": cid, "schema_version": "p14.v1",
             "run_id": "P14-20260907-99", "created_at": "2026-09-07T00:04:00",
             "text": text,
             "model_origin": {"element_type": etype, "anchor": anchor},
             "supported_by": sup, "refuted_by": ref, "status": status,
             "parent_ref": {"entity_type": "model_artifact", "entity_id": "artifact_T0_X.json",
                            "content_sha256": art_hash}}
        c["content_sha256"] = canonical_hash(c)
        (run / CLM_DIR / f"{cid}.json").write_text(
            json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")

    r1 = hashlib.sha256(json.dumps(results["P14-RES001"], sort_keys=True).encode()).hexdigest()
    man = {"run_id": "P14-20260907-99", "prereg_version": "p14.v1",
           "frozen_artifacts": {"T0_X/MMA": {"path": str(art_path), "sha256": art_hash}},
           "replays": [{"execution_id": "P14-EXE001", "replayed_at": "2026-09-07T01:00:00",
                        "result_sha256_original": r1, "result_sha256_replay": r1,
                        "match": True}],
           "created_at": "2026-09-07T00:00:00"}
    (run / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return run, {("T0_X", "MMA"): {"path": str(art_path), "sha256": art_hash}}


def selftest() -> bool:
    tmproot = Path(tempfile.mkdtemp(prefix="p14_gate_selftest_"))
    try:
        run, table = _fixture(tmproot, None)
        base = check_run(run, table)
        results = [("VALID GRAPH (baseline)", "PASS" if not base else "FAIL", not base, base)]

        def mutate(fn):
            d = shutil.copytree(run, Path(tempfile.mkdtemp(dir=tmproot)) / "mut")
            fn(d, table)
            return check_run(d, table)

        def m_g1(d, t):
            p = d / SPEC_DIR / "P14-SPEC001.json"
            e = json.loads(p.read_text(encoding="utf-8"))
            e["model_artifact_ref"]["model_artifact_hash"] = "0" * 64
            p.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")

        def m_g2(d, t):
            p = d / "manifest.json"
            m = json.loads(p.read_text(encoding="utf-8"))
            m["replays"] = []
            p.write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")

        def m_g3(d, t):
            p = d / RES_DIR / "P14-RES001.json"
            e = json.loads(p.read_text(encoding="utf-8"))
            e["execution_ref"]["content_sha256"] = "1" * 64
            p.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")

        def m_g4(d, t):
            p = d / CLM_DIR / "P14-CLM001.json"
            e = json.loads(p.read_text(encoding="utf-8"))
            e["supported_by"] = ["P14-EVI999"]
            p.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")

        def m_g5(d, t):
            p = d / RES_DIR / "P14-RES002.json"
            e = json.loads(p.read_text(encoding="utf-8"))
            e["status"] = "valid"
            p.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")

        def m_g6(d, t):
            p = d / SPEC_DIR / "P14-SPEC001.json"
            e = json.loads(p.read_text(encoding="utf-8"))
            e["verification_questions"] = ["新增参数：引入与模型无关的量子波动参数"]
            p.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")

        def m_g7(d, t):
            p = d / CLM_DIR / "P14-CLM003.json"
            e = json.loads(p.read_text(encoding="utf-8"))
            e["model_origin"]["anchor"] = "量子纠缠隧穿系数完全决定收盘价"
            p.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")

        def m_g8(d, t):
            p = d / CLM_DIR / "P14-CLM003.json"
            e = json.loads(p.read_text(encoding="utf-8"))
            e["status"] = "unresolved"
            e["supported_by"] = []
            p.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")

        for name, fn, code in (
                ("G1_PROVENANCE tamper", m_g1, "G1_PROVENANCE"),
                ("G2_DETERMINISM missing replay", m_g2, "G2_DETERMINISM"),
                ("G3_RESULT_BINDING broken ref", m_g3, "G3_RESULT_BINDING"),
                ("G4_EVIDENCE_BINDING dangling", m_g4, "G4_EVIDENCE_BINDING"),
                ("G5_INVALIDATION not propagated", m_g5, "G5_INVALIDATION"),
                ("G6_C1_CONTAINMENT 禁增/无锚定", m_g6, "G6_C1_CONTAINMENT"),
                ("G7_CLAIM_ORIGIN 无源 claim", m_g7, "G7_CLAIM_ORIGIN"),
                ("G5_INVALIDATION unresolved 无证据", m_g8, "G5_INVALIDATION")):
            errs = mutate(fn)
            fired = any(c == code for c, _ in errs)
            results.append((name, "PASS" if fired else "FAIL", fired, errs))

        print("=" * 72)
        print("P14 INTEGRITY GATE — SELFTEST")
        print("=" * 72)
        all_ok = True
        for name, verdict, ok, errs in results:
            all_ok &= ok
            print(f"  [{verdict}] {name}")
            if not ok:
                for c, m in errs:
                    print(f"        {c}: {m}")
        print("-" * 72)
        print(f"  SELFTEST: {'PASS' if all_ok else 'FAIL'}")
        return all_ok
    finally:
        shutil.rmtree(tmproot, ignore_errors=True)


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    run_dirs = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not run_dirs:
        print("usage: p14_integrity_gate.py <run_dir> | --selftest")
        sys.exit(2)
    rc = 0
    for rd in run_dirs:
        run = Path(rd)
        if run.name.startswith("_"):
            print(f"skip scratch dir: {run}")
            continue
        errs = check_run(run, FROZEN_ARTIFACTS)
        print("=" * 72)
        print(f"P14 INTEGRITY GATE — {run.name}")
        print("=" * 72)
        if errs:
            rc = 1
            from collections import Counter
            cnt = Counter(c for c, _ in errs)
            for c, m in errs:
                print(f"  [{c}] {m}")
            print("-" * 72)
            print("  GATE: FAIL  (" + ", ".join(f"{k}×{v}" for k, v in sorted(cnt.items())) + ")")
        else:
            print("  G0–G7: ALL PASS")
            print("  GATE: PASS")
    sys.exit(rc)


if __name__ == "__main__":
    main()
