import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
print(f"ROOT = {ROOT}")
PROJECT_ROOT = str(ROOT)
sys.path.insert(0, PROJECT_ROOT)
print(f"sys.path[0] = {sys.path[0]}")
import core.env.loader
print('OK')