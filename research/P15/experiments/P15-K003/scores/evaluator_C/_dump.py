# -*- coding: utf-8 -*-
"""Dump bundle contents for blind evaluation (evaluator C, P15-K003)."""
import json, sys, os

BASE = r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\experiments\P15-K003\bundles"

def dump(bundle_id):
    d = os.path.join(BASE, bundle_id)
    sep = "=" * 70
    print(sep)
    print("### %s ###" % bundle_id)
    print(sep)
    # problem_statement.txt
    ps = os.path.join(d, "problem_statement.txt")
    if os.path.exists(ps):
        print("----- problem_statement.txt -----")
        with open(ps, "r", encoding="utf-8") as f:
            print(f.read())
    # model_ir.json or model_doc.md
    ir = os.path.join(d, "model_ir.json")
    if os.path.exists(ir):
        print("----- model_ir.json -----")
        with open(ir, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                print(json.dumps(data, ensure_ascii=False, indent=1))
            except Exception as e:
                print("JSON parse error:", e)
                f.seek(0)
                print(f.read())
    md = os.path.join(d, "model_doc.md")
    if os.path.exists(md):
        print("----- model_doc.md -----")
        with open(md, "r", encoding="utf-8") as f:
            print(f.read())
    # run_model.py
    rp = os.path.join(d, "run_model.py")
    if os.path.exists(rp):
        print("----- run_model.py -----")
        with open(rp, "r", encoding="utf-8") as f:
            print(f.read())
    # execution_result.json
    er = os.path.join(d, "execution_result.json")
    if os.path.exists(er):
        print("----- execution_result.json -----")
        with open(er, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                print(json.dumps(data, ensure_ascii=False, indent=1))
            except Exception as e:
                print("JSON parse error:", e)
                f.seek(0)
                print(f.read())
    # fidelity_report.json
    fr = os.path.join(d, "fidelity_report.json")
    if os.path.exists(fr):
        print("----- fidelity_report.json -----")
        with open(fr, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                print(json.dumps(data, ensure_ascii=False, indent=1))
            except Exception as e:
                print("JSON parse error:", e)
                f.seek(0)
                print(f.read())
    # validation_plan.json if exists (SV arm)
    vp = os.path.join(d, "validation_plan.json")
    if os.path.exists(vp):
        print("----- validation_plan.json -----")
        with open(vp, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                print(json.dumps(data, ensure_ascii=False, indent=1))
            except Exception as e:
                print("JSON parse error:", e)
                f.seek(0)
                print(f.read())
    print()

if __name__ == "__main__":
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    for i in range(start, end + 1):
        dump("BUNDLE_%03d" % i)
