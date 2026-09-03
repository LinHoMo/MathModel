"""
pytest 公共配置。

背景：本项目的结构测试大量使用相对路径断言（如 os.path.isdir("core/Modeler/laws")），
这些断言只有在 cwd 恰好是仓库根时才成立——换个目录跑就全挂。

这里在收集阶段统一把 cwd 切到仓库根，使结构断言的语义明确为
「相对于仓库根」，与 pytest 的调用位置解耦。

同时导出 ROOT 常量，供需要绝对路径的测试使用。
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

os.chdir(ROOT)


def repo_path(*parts):
    """返回相对于仓库根的绝对路径字符串。"""
    return str(ROOT.joinpath(*parts))
