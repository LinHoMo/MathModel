#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Research Quality（P9）—— 统一出口。

    from validators.quality import ResearchQuality
    rq = ResearchQuality(knowledge=retriever, decisions=dlog, pack=pack)
    report = rq.evaluate(registry, graph)
    report.overall_status   # PASS / WEAK / FAIL / UNKNOWN（无黑箱总分）
"""

from .aggregator import ResearchQuality
from .contract import (ACTIONS, DIMENSIONS, FAIL, PASS, QUALITY_STATUSES,
                       UNKNOWN, WEAK, QualityDimensionReport, QualityFinding,
                       QualityReport)

__all__ = ["ResearchQuality", "QualityFinding", "QualityReport",
           "QualityDimensionReport", "QUALITY_STATUSES", "DIMENSIONS",
           "ACTIONS", "PASS", "WEAK", "FAIL", "UNKNOWN"]
