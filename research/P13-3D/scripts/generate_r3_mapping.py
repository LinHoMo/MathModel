#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_r3_mapping.py — P13-3D-R3 Phase 1: Generate MODEL_PAPER_MAP for pilot.

Generates mapping layer for 1 question × 3 arms (pilot).
Each map must have artifact_ref for every entry.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # P4 migration fix: script now at research/P13-3D/scripts/, repo root = parents[3]
ARTIFACTS_DIR = ROOT / "research" / "P13-3D-R2" / "output" / "artifacts"
MAPS_DIR = ROOT / "research" / "P13-3D-R3" / "output" / "maps"
MAPS_DIR.mkdir(parents=True, exist_ok=True)

# Pilot: 2019_A (Mechanism) × 3 arms
PILOT_QUESTION = "2019_A"
ARMS = ["B0", "MMA", "B1-F"]

TITLES = {
    "2019_A": "高压油管的压力控制",
}

# Paper sections
PAPER_SECTIONS = [
    {"section_id": "S1", "section_name": "摘要", "description": "问题、模型、主要结论"},
    {"section_id": "S2", "section_name": "问题重述", "description": "问题理解和成功标准"},
    {"section_id": "S3", "section_name": "模型假设", "description": "所有假设列表"},
    {"section_id": "S4", "section_name": "符号说明", "description": "所有变量和参数表格"},
    {"section_id": "S5", "section_name": "模型建立", "description": "机制方程、约束、目标函数"},
    {"section_id": "S6", "section_name": "候选模型对比", "description": "模型选择理由"},
    {"section_id": "S7", "section_name": "灵敏度分析", "description": "参数扰动和指标"},
    {"section_id": "S8", "section_name": "模型评价", "description": "局限性和改进方向"},
]


def generate_mapping(qid: str, arm: str) -> dict:
    """Generate MODEL_PAPER_MAP for one artifact."""
    fname = f"{qid}_{arm.replace('-', '_')}.json"
    artifact = json.loads((ARTIFACTS_DIR / fname).read_text(encoding="utf-8"))

    # 1. Claim Inventory
    claim_inventory = []

    # Model selection claim
    if artifact.get("selected_model"):
        claim_inventory.append({
            "id": "C1",
            "claim_type": "model_selection",
            "text": f"选定模型：{artifact['selected_model']}",
            "artifact_ref": "selected_model",
            "paper_target": "Section 6"
        })

    # Model justification claim
    if artifact.get("selection_reason"):
        claim_inventory.append({
            "id": "C2",
            "claim_type": "model_justification",
            "text": artifact["selection_reason"],
            "artifact_ref": "selection_reason",
            "paper_target": "Section 6"
        })

    # Key assumptions
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

    # Variables
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

    # Parameters
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

    # Constraints
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

    # Mechanisms
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

    # Objectives
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

    # 3. Question Map (simplified for 2019_A)
    question_map = [
        {
            "question_id": "Q1",
            "question_text": "确定喷油嘴流量系数",
            "primary_elements": [e["id"] for e in element_map if e["artifact_type"] in ["variables", "parameters"]][:3],
            "mechanism_elements": [e["id"] for e in element_map if e["artifact_type"] == "mechanism"][:1],
            "paper_section": "Section 5.1"
        },
        {
            "question_id": "Q2",
            "question_text": "建立凸轮驱动的进油阀运动模型",
            "primary_elements": [e["id"] for e in element_map if e["artifact_type"] in ["variables", "parameters"]][3:5],
            "mechanism_elements": [e["id"] for e in element_map if e["artifact_type"] == "mechanism"][1:2],
            "paper_section": "Section 5.2"
        },
        {
            "question_id": "Q3",
            "question_text": "确定合理的凸轮运动规律",
            "primary_elements": [e["id"] for e in element_map if e["artifact_type"] == "objective"],
            "mechanism_elements": [e["id"] for e in element_map if e["artifact_type"] == "mechanism"][2:],
            "paper_section": "Section 5.3"
        },
    ]

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
    # Map parameter names to artifact parameter array indices
    param_name_to_idx = {}
    for i, p in enumerate(artifact.get("parameters", [])):
        param_name_to_idx[p.get("name", "")] = i
        param_name_to_idx[p.get("id", "")] = i

    for sens in artifact.get("sensitivity_plan", []):
        param_name = sens.get("parameter", "")
        param_idx = param_name_to_idx.get(param_name, -1)
        if param_idx >= 0:
            sensitivity_map.append({
                "parameter_ref": f"parameters.{param_idx}",
                "parameter_name": param_name,
                "range": sens.get("range", ""),
                "metric": sens.get("metric", ""),
                "paper_section": "Section 7"
            })
        else:
            # Parameter not in artifact - this is a mapping error
            sensitivity_map.append({
                "parameter_ref": f"NOT_IN_ARTIFACT.{param_name}",
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

        if section["section_id"] == "S3":  # 模型假设
            required_claims = [c["id"] for c in claim_inventory if c["claim_type"] == "assumption"]
        elif section["section_id"] == "S4":  # 符号说明
            required_elements = [e["id"] for e in element_map if e["artifact_type"] in ["variables", "parameters"]]
        elif section["section_id"] == "S5":  # 模型建立
            required_elements = [e["id"] for e in element_map if e["artifact_type"] in ["mechanism", "constraints", "objective"]]
        elif section["section_id"] == "S6":  # 候选模型对比
            required_claims = ["C1", "C2"]
        elif section["section_id"] == "S7":  # 灵敏度分析
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


# Generate pilot mappings
for arm in ARMS:
    mapping = generate_mapping(PILOT_QUESTION, arm)
    map_file = MAPS_DIR / f"{PILOT_QUESTION}_{arm.replace('-', '_')}_map.json"
    map_file.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ {PILOT_QUESTION}/{arm}: {map_file.name}")
    print(f"  Claims: {len(mapping['claim_inventory'])}, Elements: {len(mapping['element_map'])}, "
          f"Candidates: {len(mapping['candidate_model_map'])}, Sensitivity: {len(mapping['sensitivity_map'])}")

print(f"\nMappings saved to {MAPS_DIR}")
