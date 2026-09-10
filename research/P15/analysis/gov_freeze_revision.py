# -*- coding: utf-8 -*-
"""K002/K003 冻结 new revision：
audit FIX-5.3/5.4（code_mapping + validations.type enum 扩展 + L2 数学校验）
原地修改了冻结项 core/schemas/v3/model/model_ir.schema.json → 双实验冻结漂移。
处理：升 PROTOCOL_VERSION + 重写 hashes.json（new revision，保留 audit 修复）。
"""
import re
import subprocess
from pathlib import Path

REPO = Path(r"C:\Users\Lin\Desktop\Programs\MathModel")
SCRIPTS = REPO / "research" / "P15" / "scripts"


def bump(path: Path, old: str, new: str):
    s = path.read_text(encoding="utf-8")
    assert f'PROTOCOL_VERSION = "{old}"' in s or f"PROTOCOL_VERSION = '{old}'" in s, \
        f"{path.name}: 未找到 PROTOCOL_VERSION = {old}"
    s = s.replace(f'PROTOCOL_VERSION = "{old}"', f'PROTOCOL_VERSION = "{new}"')
    s = s.replace(f"PROTOCOL_VERSION = '{old}'", f'PROTOCOL_VERSION = "{new}"')
    path.write_text(s, encoding="utf-8")
    print(f"{path.name}: PROTOCOL_VERSION {old} -> {new}")


def freeze(script: str, version: str):
    r = subprocess.run(["py", "-3.12", str(SCRIPTS / script), "freeze"],
                       capture_output=True, text=True, cwd=str(REPO))
    print(r.stdout.strip())
    if r.returncode != 0:
        print("STDERR:", r.stderr[-500:])


# K002: 0.8 -> 0.9（audit FIX 后 new revision）
bump(SCRIPTS / "k002_common.py", "0.8", "0.9")
freeze("k002_freeze.py", "0.9")

# K003: 0.1 -> 0.2（audit FIX 后 new revision）
bump(SCRIPTS / "k003_common.py", "0.1", "0.2")
freeze("k003_freeze.py", "0.2")
