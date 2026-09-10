"""Quick debug: run ref +RT on 2024_A and inspect results."""
import sys, json, time
from pathlib import Path

REPO = Path("C:/Users/Lin/Desktop/Programs/MathModel")
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "research/P15/vs001_run"))
sys.path.insert(0, str(REPO / "research/P15/k004"))

from reference_constructor import ReferenceConstructor
from runtime.execution.session import RuntimeSession
from runtime.execution.adapters import LocalPythonAdapter
from runtime.constructors.registry import apply_bundle
import yaml

qid = "2024_A"
card_path = REPO / "research/P15/benchmark/problem_cards" / qid / "card.yaml"
with open(card_path, encoding="utf-8") as f:
    card = yaml.safe_load(f)
stmt_path = REPO / "research/P15/benchmark/problem_cards" / qid / "problem_statement.txt"
statement = stmt_path.read_text(encoding="utf-8")[:2000] if stmt_path.exists() else ""

problem = {
    "question": qid,
    "statement": statement or card.get("title", ""),
    "features": {
        "problem_types": card.get("family", []),
        "sub_questions": card.get("sub_questions", []),
        "allowed_structures": card.get("allowed_modeling_structures", []),
        "key_variables": card.get("key_variables", []),
        "key_constraints": card.get("key_constraints", []),
    },
}

constructor = ReferenceConstructor()
bundle = constructor.construct(problem)
proj = REPO / "research/P15/k004/results/_debug2"
proj.mkdir(parents=True, exist_ok=True)

adapter = LocalPythonAdapter()
session = RuntimeSession(project_dir=proj, questions=[qid], execution_adapter=adapter)
apply_bundle(session, bundle, workdir=str(proj))

report = session.run(save=True)
session.checkpoint()

prog = report.get("progress", {})
completed = prog.get("completed", [])
print("completed nodes:", completed)

execs = session.registry.list_by_type("execution_result")
print(f"exec results: {len(execs)}")
for ex in execs:
    d = ex.data or {}
    print(f"  {ex.artifact_id}: status={d.get('status')}")

vrs = session.registry.list_by_type("verification_result")
print(f"verification results: {len(vrs)}")
for vr in vrs:
    d = vr.data or {}
    print(f"  {vr.artifact_id}: status={d.get('status')}")

fids = [a for a in session.registry.list_by_type("fidelity_report")]
print(f"fidelity reports: {len(fids)}")
for fid in fids:
    d = fid.data or {}
    print(f"  {fid.artifact_id}: score={d.get('fidelity_score')} status={d.get('fidelity_status')}")

edges = list(session.graph.all_edges())
print(f"evidence edges: {len(edges)}")
for src, rel, tgt in edges[:10]:
    print(f"  {src} --{rel}--> {tgt}")
