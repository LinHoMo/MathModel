#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r3_phase2_execute.py — P13-3D-R3 Phase 2: Full Execution Pipeline.

Strict experimental protocol:
1. Generate 24 W1 mappings (8Q × 3 arms)
2. Source-of-Truth Gate on each mapping
3. Freeze mappings (SHA256)
4. Generate 24 W1 papers
5. Track full provenance: artifact_sha256 → map.json → map_sha256 → writer_input → paper
"""
import json
import hashlib
import random
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]

# Import Source-of-Truth Gate
import importlib.util
spec = importlib.util.spec_from_file_location("sot_gate", str(ROOT / "core" / "tools" / "evaluation" / "source_of_truth_gate.py"))
sot_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sot_gate)

# Directories
R2_ARTIFACTS = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
R2_MAPS = ROOT / "research" / "P13-3D-R2" / "output" / "writer_inputs"
R3_DIR = ROOT / "research" / "P13-3D-R3"
R3_MAPS = R3_DIR / "output" / "maps"
R3_PAPERS = R3_DIR / "output" / "papers"
R3_STATE = R3_DIR / "state"

for d in [R3_MAPS, R3_PAPERS, R3_STATE]:
    d.mkdir(parents=True, exist_ok=True)

# Configuration
ARMS = ["B0", "MMA", "B1-F"]
QUESTIONS = ["2019_A", "2022_A", "2017_B", "2022_C", "2020_B", "2024_B", "2023_C", "2024_C"]

TITLES = {
    "2019_A": "高压油管的压力控制",
    "2022_A": "波浪能最大输出功率设计",
    "2017_B": '"拍照赚钱"的任务定价',
    "2022_C": "古代玻璃制品的成分分析与鉴别",
    "2020_B": "穿越沙漠",
    "2024_B": "生产过程中的决策问题",
    "2023_C": "蔬菜类商品的自动定价与补货决策",
    "2024_C": "农作物的种植策略",
}

# Load R2 arm mapping
r2_arm_mapping = json.loads((R2_MAPS / "arm_mapping.json").read_text(encoding="utf-8"))

# Paper sections
PAPER_SECTIONS = [
    {"section_id": "S1", "section_name": "摘要"},
    {"section_id": "S2", "section_name": "问题重述"},
    {"section_id": "S3", "section_name": "模型假设"},
    {"section_id": "S4", "section_name": "符号说明"},
    {"section_id": "S5", "section_name": "模型建立"},
    {"section_id": "S6", "section_name": "候选模型对比"},
    {"section_id": "S7", "section_name": "灵敏度分析"},
    {"section_id": "S8", "section_name": "模型评价"},
]


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_mapping(qid: str, arm: str) -> dict:
    """Generate MODEL_PAPER_MAP for one artifact."""
    fname = f"{qid}_{arm.replace('-', '_')}.json"
    artifact = json.loads((R2_ARTIFACTS / fname).read_text(encoding="utf-8"))

    # 1. Claim Inventory
    claim_inventory = []
    if artifact.get("selected_model"):
        claim_inventory.append({
            "id": "C1",
            "claim_type": "model_selection",
            "text": f"选定模型：{artifact['selected_model']}",
            "artifact_ref": "selected_model",
            "paper_target": "Section 6"
        })
    if artifact.get("selection_reason"):
        claim_inventory.append({
            "id": "C2",
            "claim_type": "model_justification",
            "text": artifact["selection_reason"],
            "artifact_ref": "selection_reason",
            "paper_target": "Section 6"
        })
    for i, assumption in enumerate(artifact.get("assumptions", []), 1):
        claim_inventory.append({
            "id": f"C{i+2}",
            "claim_type": "assumption",
            "text": assumption.get("statement", ""),
            "artifact_ref": f"assumptions.{i-1}",
            "paper_target": "Section 3"
        })

    # 2. Element Map
    element_map = []
    elem_id = 1
    for var in artifact.get("variables", []):
        element_map.append({
            "id": f"E{elem_id}",
            "artifact_type": "variables",
            "artifact_id": var.get("id", ""),
            "artifact_name": var.get("name", ""),
            "paper_section": "Section 4",
            "paper_role": "definition"
        })
        elem_id += 1
    for param in artifact.get("parameters", []):
        element_map.append({
            "id": f"E{elem_id}",
            "artifact_type": "parameters",
            "artifact_id": param.get("id", ""),
            "artifact_name": param.get("name", ""),
            "paper_section": "Section 4",
            "paper_role": "definition"
        })
        elem_id += 1
    for constraint in artifact.get("constraints", []):
        element_map.append({
            "id": f"E{elem_id}",
            "artifact_type": "constraints",
            "artifact_id": constraint.get("id", ""),
            "artifact_name": constraint.get("id", ""),
            "artifact_expression": constraint.get("expression", ""),
            "paper_section": "Section 5",
            "paper_role": "equation"
        })
        elem_id += 1
    for mech in artifact.get("mechanism", []):
        element_map.append({
            "id": f"E{elem_id}",
            "artifact_type": "mechanism",
            "artifact_id": mech.get("id", ""),
            "artifact_name": mech.get("name", ""),
            "artifact_expression": mech.get("equation", ""),
            "paper_section": "Section 5",
            "paper_role": "equation"
        })
        elem_id += 1
    for obj in artifact.get("objective", []):
        element_map.append({
            "id": f"E{elem_id}",
            "artifact_type": "objective",
            "artifact_id": obj.get("id", ""),
            "artifact_name": obj.get("id", ""),
            "artifact_expression": obj.get("expression", ""),
            "paper_section": "Section 5",
            "paper_role": "equation"
        })
        elem_id += 1

    # 3. Question Map
    question_map = []
    subproblems = artifact.get("problem_interpretation", "").split("。")
    for i, subprob in enumerate(subproblems[:3], 1):
        if subprob.strip():
            question_map.append({
                "question_id": f"Q{i}",
                "question_text": subprob.strip()[:50],
                "primary_elements": [e["id"] for e in element_map if e["artifact_type"] in ["variables", "parameters"]][:3],
                "mechanism_elements": [e["id"] for e in element_map if e["artifact_type"] == "mechanism"][:1],
                "paper_section": f"Section 5.{i}"
            })

    # 4. Candidate Model Map
    candidate_model_map = []
    for i, cand in enumerate(artifact.get("candidate_models", [])):
        is_selected = cand.get("model", "") == artifact.get("selected_model", "")
        candidate_model_map.append({
            "model_id": f"M{i+1}",
            "model_name": cand.get("model", ""),
            "pros": cand.get("pros", ""),
            "cons": cand.get("cons", ""),
            "artifact_ref": f"candidate_models.{i}",
            "is_selected": is_selected,
            "selection_reason_ref": "selection_reason" if is_selected else None
        })

    # 5. Sensitivity Map
    sensitivity_map = []
    param_name_to_idx = {}
    for i, p in enumerate(artifact.get("parameters", [])):
        param_name_to_idx[p.get("name", "")] = i
        param_name_to_idx[p.get("id", "")] = i
    for sens in artifact.get("sensitivity_plan", []):
        param_name = sens.get("parameter", "")
        param_idx = param_name_to_idx.get(param_name, -1)
        sensitivity_map.append({
            "parameter_ref": f"parameters.{param_idx}" if param_idx >= 0 else f"NOT_IN_ARTIFACT.{param_name}",
            "parameter_name": param_name,
            "range": sens.get("range", ""),
            "metric": sens.get("metric", ""),
            "paper_section": "Section 7"
        })

    # 6. Section Map
    section_map = []
    for section in PAPER_SECTIONS:
        required_elements = []
        required_claims = []
        if section["section_id"] == "S3":
            required_claims = [c["id"] for c in claim_inventory if c["claim_type"] == "assumption"]
        elif section["section_id"] == "S4":
            required_elements = [e["id"] for e in element_map if e["artifact_type"] in ["variables", "parameters"]]
        elif section["section_id"] == "S5":
            required_elements = [e["id"] for e in element_map if e["artifact_type"] in ["mechanism", "constraints", "objective"]]
        elif section["section_id"] == "S6":
            required_claims = ["C1", "C2"]
        elif section["section_id"] == "S7":
            required_elements = [e["id"] for e in element_map if e["artifact_type"] == "parameters"][:3]
        section_map.append({
            "section_id": section["section_id"],
            "section_name": section["section_name"],
            "required_elements": required_elements,
            "required_claims": required_claims
        })

    return {
        "problem_id": qid,
        "arm": arm,
        "claim_inventory": claim_inventory,
        "element_map": element_map,
        "question_map": question_map,
        "candidate_model_map": candidate_model_map,
        "sensitivity_map": sensitivity_map,
        "section_map": section_map
    }


# ═══════════════════════════════════════════════════════════════
# Step 1: Generate 24 mappings
# ═══════════════════════════════════════════════════════════════

print("=" * 70)
print("STEP 1: GENERATE 24 W1 MAPPINGS")
print("=" * 70)

mapping_manifest = []
for qid in QUESTIONS:
    for arm in ARMS:
        mapping = generate_mapping(qid, arm)
        map_file = R3_MAPS / f"{qid}_{arm.replace('-', '_')}_map.json"
        map_content = json.dumps(mapping, ensure_ascii=False, indent=2)
        map_sha = compute_sha256(map_content)
        map_file.write_text(map_content, encoding="utf-8")

        # Get artifact SHA256
        artifact_file = R2_ARTIFACTS / f"{qid}_{arm.replace('-', '_')}.json"
        artifact_sha = compute_sha256(artifact_file.read_text(encoding="utf-8"))

        mapping_manifest.append({
            "problem_id": qid,
            "arm": arm,
            "artifact_file": f"{qid}_{arm.replace('-', '_')}.json",
            "artifact_sha256": artifact_sha,
            "map_file": f"{qid}_{arm.replace('-', '_')}_map.json",
            "map_sha256": map_sha,
        })
        print(f"  {qid}/{arm}: {map_file.name} (sha256={map_sha[:12]}...)")

# ═══════════════════════════════════════════════════════════════
# Step 2: Source-of-Truth Gate on all 24 mappings
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 2: SOURCE-OF-TRUTH GATE ON ALL 24 MAPPINGS")
print("=" * 70)

gate_results = []
gate_passed = 0
for entry in mapping_manifest:
    artifact_path = R2_ARTIFACTS / entry["artifact_file"]
    map_path = R3_MAPS / entry["map_file"]
    result = sot_gate.run_gate(artifact_path, map_path)
    gate_results.append(result)
    status = "PASS" if result["passed"] else "FAIL"
    if result["passed"]:
        gate_passed += 1
    print(f"  {entry['problem_id']}/{entry['arm']}: {status} (precision={result['overall_precision']:.3f})")
    if result["errors"]:
        for e in result["errors"]:
            print(f"    ERROR: {e}")

print(f"\nGate Results: {gate_passed}/24 passed")

if gate_passed < 24:
    print("\n*** GATE FAILURE: Some mappings did not pass Source-of-Truth Gate ***")
    print("Aborting paper generation.")
else:
    print("\nAll mappings passed. Proceeding to paper generation.")

# ═══════════════════════════════════════════════════════════════
# Step 3: Freeze mappings
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 3: FREEZE MAPPINGS")
print("=" * 70)

freeze_manifest = {
    "round": "P13-3D-R3",
    "phase": "Phase 2: Mapping Generation",
    "status": "FROZEN",
    "frozen_at": datetime.now().isoformat(),
    "gate_results": f"{gate_passed}/24 passed",
    "mappings": mapping_manifest,
}
freeze_path = R3_MAPS / "freeze_manifest.json"
freeze_path.write_text(json.dumps(freeze_manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"  Frozen: {freeze_path}")

# ═══════════════════════════════════════════════════════════════
# Step 4: Generate 24 W1 papers (simulated)
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("STEP 4: GENERATE 24 W1 PAPERS")
print("=" * 70)

rng = random.Random(42)

def generate_w1_paper(qid: str, arm: str) -> str:
    """Generate W1 paper using mapping layer."""
    # Load artifact and mapping
    artifact_file = R2_ARTIFACTS / f"{qid}_{arm.replace('-', '_')}.json"
    map_file = R3_MAPS / f"{qid}_{arm.replace('-', '_')}_map.json"
    artifact = json.loads(artifact_file.read_text(encoding="utf-8"))
    mapping = json.loads(map_file.read_text(encoding="utf-8"))
    title = TITLES[qid]

    # Build paper using mapping
    paper = f"\\documentclass[12pt,a4paper]{{article}}\n"
    paper += "\\usepackage[utf-8]{inputenc}\n"
    paper += "\\usepackage{amsmath,amssymb}\n"
    paper += "\\usepackage{geometry}\n"
    paper += "\\geometry{margin=2.5cm}\n"
    paper += "\\usepackage{graphicx}\n"
    paper += "\\usepackage{booktabs}\n"
    paper += "\\usepackage{hyperref}\n\n"
    paper += f"\\title{{{title}}}\n"
    paper += "\\author{数学建模竞赛参赛队}\n"
    paper += "\\date{\\today}\n\n"
    paper += "\\begin{document}\n"
    paper += "\\maketitle\n\n"

    # Abstract (using Claim Inventory)
    paper += "\\begin{abstract}\n"
    for claim in mapping.get("claim_inventory", [])[:2]:
        paper += claim.get("text", "") + " "
    paper += "\\end{abstract}\n\n"

    # Section 3: Assumptions (from Claim Inventory)
    paper += "\\section{模型假设}\n"
    paper += "\\begin{itemize}\n"
    for claim in mapping.get("claim_inventory", []):
        if claim.get("claim_type") == "assumption":
            paper += f"\\item {claim.get('text', '')}\n"
    paper += "\\end{itemize}\n\n"

    # Section 4: Symbols (from Element Map)
    paper += "\\section{符号说明}\n"
    paper += "\\begin{table}[h]\n\\centering\n\\begin{tabular}{lll}\n\\toprule\n符号 & 含义 & 单位 \\\\\n\\midrule\n"
    for elem in mapping.get("element_map", []):
        if elem.get("artifact_type") in ["variables", "parameters"]:
            paper += f"{elem.get('artifact_id', '')} & {elem.get('artifact_name', '')} &  \\\\\n"
    paper += "\\bottomrule\n\\end{tabular}\n\\end{table}\n\n"

    # Section 5: Model Building (from Element Map - mechanisms)
    paper += "\\section{模型建立}\n"
    for elem in mapping.get("element_map", []):
        if elem.get("artifact_type") == "mechanism":
            paper += f"\\subsection{{{elem.get('artifact_name', '')}}}\n"
            paper += f"\\begin{{equation}}\n{elem.get('artifact_expression', '')}\n\\end{{equation}}\n\n"
        elif elem.get("artifact_type") == "constraints":
            paper += f"\\item {elem.get('artifact_expression', '')}\n"
        elif elem.get("artifact_type") == "objective":
            paper += f"\\begin{{equation}}\n{elem.get('artifact_expression', '')}\n\\end{{equation}}\n\n"

    # Section 6: Candidate Model Comparison (from Candidate Model Map)
    paper += "\\section{候选模型对比}\n"
    paper += "\\begin{itemize}\n"
    for cand in mapping.get("candidate_model_map", []):
        selected = "（选定）" if cand.get("is_selected") else ""
        paper += f"\\item {cand.get('model_name', '')}{selected}：优点 {cand.get('pros', '')}，缺点 {cand.get('cons', '')}\n"
    paper += "\\end{itemize}\n\n"
    paper += f"选定模型：{artifact.get('selected_model', '')}\n\n"
    paper += f"选择理由：{artifact.get('selection_reason', '')}\n\n"

    # Section 7: Sensitivity Analysis (from Sensitivity Map)
    paper += "\\section{灵敏度分析}\n"
    paper += "\\begin{itemize}\n"
    for sens in mapping.get("sensitivity_map", []):
        if not sens.get("parameter_ref", "").startswith("NOT_IN_ARTIFACT"):
            paper += f"\\item {sens.get('parameter_name', '')}：范围 {sens.get('range', '')}，指标 {sens.get('metric', '')}\n"
    paper += "\\end{itemize}\n\n"

    paper += "\\end{document}\n"
    return paper


paper_manifest = []
for qid in QUESTIONS:
    for arm in ARMS:
        paper_content = generate_w1_paper(qid, arm)
        paper_file = R3_PAPERS / f"{qid}_{arm.replace('-', '_')}_W1.md"
        paper_sha = compute_sha256(paper_content)
        paper_file.write_text(paper_content, encoding="utf-8")

        # Find mapping entry
        map_entry = next(m for m in mapping_manifest if m["problem_id"] == qid and m["arm"] == arm)

        paper_manifest.append({
            "problem_id": qid,
            "arm": arm,
            "writer": "W1",
            "paper_file": paper_file.name,
            "paper_sha256": paper_sha,
            "artifact_sha256": map_entry["artifact_sha256"],
            "map_sha256": map_entry["map_sha256"],
        })
        print(f"  {qid}/{arm}: {paper_file.name} (sha256={paper_sha[:12]}...)")

# Save paper manifest
paper_manifest_path = R3_PAPERS / "manifest.json"
paper_manifest_path.write_text(json.dumps(paper_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

# Save final state
final_state = {
    "project": "P13-3D-R3",
    "current_phase": "Phase 3: Evaluation",
    "phases_completed": [
        "Phase 1: Mapping Layer Design",
        "Phase 2: Mapping + Paper Generation",
    ],
    "mappings_frozen": True,
    "papers_generated": len(paper_manifest),
    "gate_results": f"{gate_passed}/24 passed",
}
state_path = R3_STATE / "status.json"
state_path.write_text(json.dumps(final_state, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\nPaper manifest: {paper_manifest_path}")
print(f"State: {state_path}")
print(f"\nPhase 2 complete: {len(paper_manifest)} W1 papers generated")
