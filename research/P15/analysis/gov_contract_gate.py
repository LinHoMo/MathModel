# -*- coding: utf-8 -*-
"""契约 gate 注入：k003_formal_runner.py 加 runtime schema jsonschema 校验。"""
import re
from pathlib import Path

p = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\research\P15\experiments\P15-K003\k003_formal_runner.py")
s = p.read_text(encoding="utf-8")

# 1) 找 write_json(model_ir) 出现次数与上下文
hits = [m.start() for m in re.finditer(r'write_json\(run_dir / "model_ir\.json", model_ir\)', s)]
print("write_json(model_ir) hits:", len(hits))
assert len(hits) >= 1

# 2) 在函数顶部 import 之后注入 gate helper（找第一个 def 前的位置）
anchor = None
m = re.search(r"^def ", s, re.M)
assert m, "no def found"
anchor = m.start()

gate_helper = '''def _assert_mir_schema(model_ir: dict, *, run_id: str = "") -> None:
    """CONTRACT DRIFT 治理（2026-09-10）：register schema gate。

    实验 run 的 MODEL_IR 必须通过 runtime MODEL_IR schema（Draft 202012）。
    历史 36/44 不合规事实见 research/P15/analysis/CONTRACT_DRIFT_K003.md；
    本 gate 只拦未来生成，不回溯修改已生成 run。
    """
    import jsonschema as _js
    schema = json.loads(
        (Path(__file__).resolve().parents[3]
         / "research" / "P15" / "model_representation"
         / "model_ir.schema.json").read_text(encoding="utf-8"))
    validator = _js.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(model_ir), key=lambda e: list(e.path))
    if errors:
        head = "; ".join(f"{'/'.join(map(str, e.path))}: {e.message}"
                         for e in errors[:3])
        raise ValueError(f"run {run_id} MODEL_IR 不合 runtime schema: {head}"
                         f"（共 {len(errors)} 错误；契约见 CONTRACT_DRIFT_K003.md）")


'''

s = s[:anchor] + gate_helper + s[anchor:]

# 3) 在每个 write_json(model_ir) 前注入 gate 调用（用独立函数包装更稳：直接在调用点前插）
#    简单方案：把 write_json 行替换为 gate + write
s = s.replace(
    'write_json(run_dir / "model_ir.json", model_ir)',
    '_assert_mir_schema(model_ir, run_id=run_dir.name)\n'
    '        write_json(run_dir / "model_ir.json", model_ir)',
)
p.write_text(s, encoding="utf-8")
print("schema gate injected")

# 4) 语法检查
import subprocess
r = subprocess.run(["py", "-3.12", "-m", "py_compile", str(p)],
                   capture_output=True, text=True)
print("compile:", "OK" if r.returncode == 0 else r.stderr[:400])
