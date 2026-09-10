"""路径与配置目录解析（MH_* 环境变量、.mh/ 配置目录）。

命名规范（tech-rebuild）：
- 环境变量前缀：MH_（如 MH_CONFIG_DIR）
- 配置目录：.mh/（用户级默认 <home>/.mh/，可用 MH_CONFIG_DIR 覆盖）
"""
from __future__ import annotations

import os
from pathlib import Path

#: 配置目录环境变量（MH_* 前缀命名规范）
MH_CONFIG_DIR_ENV = "MH_CONFIG_DIR"
#: 默认配置目录名（.mh/）
DEFAULT_CONFIG_DIR = ".mh"


def config_dir() -> Path:
    """返回用户级配置目录。

    优先级：MH_CONFIG_DIR 环境变量 > <home>/.mh/。
    """
    env = os.environ.get(MH_CONFIG_DIR_ENV)
    if env:
        return Path(env).expanduser()
    return Path.home() / DEFAULT_CONFIG_DIR


def config_path(*parts: str) -> Path:
    """返回配置目录下某文件的路径（自动建目录）。"""
    p = config_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p.joinpath(*parts)


def project_config_dir(project_root: Path) -> Path:
    """项目级配置目录：<project_root>/.mh/。"""
    p = Path(project_root) / DEFAULT_CONFIG_DIR
    p.mkdir(parents=True, exist_ok=True)
    return p


def env_flag(name: str, default: bool = False) -> bool:
    """MH_* 布尔开关解析（true/1/yes 为真）。"""
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}
