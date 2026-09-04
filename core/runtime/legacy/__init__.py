"""Legacy Compatibility Layer（V2 ⇄ V3 桥接）。"""

from .convert import LegacyError, convert_project, export_results, import_results, import_state

__all__ = [
    "LegacyError", "convert_project", "export_results",
    "import_results", "import_state",
]
