"""evaluation — V3 评估层（P4 桥接）。

P4 阶段评分实现仍驻留 core/tools/（零依赖脚本，state/gate/编排器消费）；
本包提供稳定的 V3 import 面 `evaluation.scoring`。P5 目录重构时实现
迁入本包，core/tools/ 侧退化为 CLI 薄转发，本 import 面保持不变。
"""

from . import scoring

__all__ = ["scoring"]
