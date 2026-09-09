"""Inspect registry + evidence graph for P1-VS-001 acceptance criteria."""
import json
from pathlib import Path

EXP = Path(__file__).parent
state = EXP / "project" / "state"

reg = json.loads((state / "registry.json").read_text("utf-8"))
g = json.loads((state / "evidence_graph.json").read_text("utf-8"))

print("=== Artifacts ===")
for aid, a in sorted(reg["artifacts"].items()):
    print(f"  {aid:10s} type={a['type']:20s} status={a['status']:12s} title={a.get('title','')[:40]}")

print("\n=== Evidence Graph Relations ===")
for r in g["relations"]:
    print(f"  {r['from']:10s} -{r['relation']:16s}-> {r['to']}")
print(f"Total: {len(g['relations'])} relations, graph_version={g['graph_version']}")

# Check key lineages
print("\n=== Key Lineage Checks ===")
rels = [(r["from"], r["relation"], r["to"]) for r in g["relations"]]

# 1. Problem motivates Question
print(f"1. P002 -motivates-> Q002: {('P002','motivates','Q002') in rels}")
# 2. Question solved_by Model
print(f"2. Q002 -solved_by-> M002: {('Q002','solved_by','M002') in rels}")
# 3. Model implemented_by Code
print(f"3. M002 -implemented_by-> CODE002: {('M002','implemented_by','CODE002') in rels}")
# 4. Execution verified_by Validation
print(f"4. EXEC002 -verified_by-> VR002: {('EXEC002','verified_by','VR002') in rels}")
# 5. Revision lineage
print(f"5. MIR003 -revision_of-> MIR002: {('MIR003','revision_of','MIR002') in rels}")
print(f"6. MIR003 -supersedes-> MIR002: {('MIR003','supersedes','MIR002') in rels}")
# 7. M2 code/exec/validation
print(f"7. M003 -implemented_by-> CODE003: {('M003','implemented_by','CODE003') in rels}")
print(f"8. EXEC003 -verified_by-> VR003: {('EXEC003','verified_by','VR003') in rels}")

# Check MIR002 is superseded
mir2 = reg["artifacts"].get("MIR002", {})
print(f"\n9. MIR002 status={mir2.get('status')}, invalidation={mir2.get('invalidation',{})}")
m2 = reg["artifacts"].get("M002", {})
print(f"10. M002 status={m2.get('status')}, invalidation={m2.get('invalidation',{})}")

# Check execution results have real numeric outputs
for eid in ["EXEC002", "EXEC003"]:
    e = reg["artifacts"].get(eid, {})
    data = e.get("data", {})
    print(f"\n11. {eid}: status={data.get('status')}, outputs={data.get('outputs')}")
