import json, re, importlib.util, pathlib

# load env loader
repo = pathlib.Path("C:/Users/Lin/Desktop/MathModelSkills")
spec = importlib.util.spec_from_file_location("loader", str(repo/"env/loader.py"))
loader = importlib.util.module_from_spec(spec); spec.loader.exec_module(loader)
get = loader.get

p = pathlib.Path("C:/Users/Lin/Desktop/MathModelSkills/projects/cumcm2024a")

# replicate check_numeric_traceability
data = json.loads((p/"figures/all_results.json").read_text(encoding="utf-8"))
lv = set()
def walk(o):
    if isinstance(o, dict):
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for i in o: walk(i)
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        lv.add(round(float(o), 4))
walk(data)
print("ledger size", len(lv))
t = (p/"paper/main.tex").read_text(encoding="utf-8")
nums = [float(x) for x in re.findall(r"\b\d+\.?\d+\b", t)]
rn = [n for n in nums if n <= 10000]
tolb = float(get("runtime.numeric_tolerance_abs", 0.01))
tolr = float(get("runtime.numeric_tolerance_rel", 0.005))
print("tolb", tolb, "tolr", tolr, "paper nums", len(rn))
nt = []
for pn in rn:
    ok = False
    for v in lv:
        d = max(abs(pn), 1e-9)
        if abs(pn - v) <= tolb or abs(pn - v)/d <= tolr:
            ok = True; break
    if not ok: nt.append(pn)
print("nontrace", len(nt), "ratio", (len(rn)-len(nt))/len(rn))
print("nontrace values:", sorted(set(nt))[:60])
