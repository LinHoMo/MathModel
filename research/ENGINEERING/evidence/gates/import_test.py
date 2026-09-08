#!/usr/bin/env python3
"""Test imports from core.runtime."""
import sys
from pathlib import Path

mathmodel = Path(r'C:\Users\Lin\Desktop\Programs\MathModel')
sys.path.insert(0, str(mathmodel))

# Try the specific modules
try:
    from core.runtime.roles import load_roles, validate_dag_roles
    print('core.runtime.roles imported OK')
except Exception as e:
    print('core.runtime.roles FAIL:', e)

try:
    from core.runtime.execution.composer import WorkflowComposer
    print('core.runtime.execution.composer imported OK')
except Exception as e:
    print('core.runtime.execution.composer FAIL:', e)