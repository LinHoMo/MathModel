#!/usr/bin/env python3
"""Check runtime package structure."""
import sys
from pathlib import Path

# Use absolute path
mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')
sys.path.insert(0, str(mathmodel))

# Check core/runtime
core_runtime = mathmodel / "core" / "runtime"
print("core/runtime exists:", core_runtime.exists())
print("core/runtime/__init__.py:", core_runtime.joinpath("__init__.py").exists())

# List runtime contents
if core_runtime.exists():
    print("\nRuntime files:")
    for f in sorted(core_runtime.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
        print(f"  {f.name} -> {'dir' if f.is_dir() else 'file'} ({f.stat().st_size} bytes)")

# Check if runtime is a proper package
init_file = core_runtime / "__init__.py"
print("\nRuntime __init__.py size:", init_file.stat().st_size if init_file.exists() else "N/A", "bytes")