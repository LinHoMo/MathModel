"""轻量结构化日志（零第三方依赖，符合 core 定位红利）。

用法：
    from modeling_harness.utils.logging import get_logger
    log = get_logger(__name__)
    log.info("...")
"""
from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def configure(level: int = logging.INFO) -> None:
    """配置根 logger（进程级单次）。"""
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s",
                          datefmt="%H:%M:%S"))
    root = logging.getLogger("modeling_harness")
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """返回 modeling_harness.* 命名空间下的 logger。"""
    configure()
    return logging.getLogger(f"modeling_harness.{name}")
