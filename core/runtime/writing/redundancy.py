#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Redundancy / AI-pattern Detection（P11-17）—— 确定性结构检测，非"AI 概率"。

检测项（全部可解释）:
    repeated claim / repeated transition template / repeated sentence template /
    excessive 首先-其次-最后 / empty academic phrases / repeated section summary /
    model boilerplate / unsupported superlative
"""

from __future__ import annotations

from dataclasses import dataclass, field

EMPTY_PHRASES = ("具有重要意义", "效果良好", "模型优秀", "息息相关",
                 "综上所述，本文方法具有很大的优势", "众所周知")
TRANSITION_TEMPLATES = ("下面研究问题", "接下来研究问题")
SUPERLATIVES = ("最优", "best", "显著优于", "完胜", "证明")


@dataclass
class RedundancyFinding:
    code: str             # RED-1..RED-6
    severity: str          # fail / weak
    subject: str
    reason: str

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in ("code", "severity", "subject",
                                              "reason")}


def detect(text: str, paragraphs: list[str] | None = None) -> list[RedundancyFinding]:
    out: list[RedundancyFinding] = []
    paras = paragraphs or [p for p in (text or "").split("\n") if p.strip()]

    # RED-1 重复句子模板（≥3 次相同开头 8 字）
    heads: dict[str, int] = {}
    for p in paras:
        head = p.strip()[:8]
        if len(head) == 8:
            heads[head] = heads.get(head, 0) + 1
    for head, n in heads.items():
        if n >= 3:
            out.append(RedundancyFinding(
                "RED-1", "weak", head, f"相同句式开头重复 {n} 次"))

    # RED-2 空 academic 短语
    for ph in EMPTY_PHRASES:
        if ph in text:
            out.append(RedundancyFinding(
                "RED-2", "weak", ph, "空学术短语（无信息量）"))

    # RED-3 过度 首先/其次/最后
    n_seq = sum(text.count(w) for w in ("首先", "其次", "最后"))
    if n_seq >= 3:
        out.append(RedundancyFinding(
            "RED-3", "weak", "首先/其次/最后", f"出现 {n_seq} 次"))

    # RED-4 转场模板
    for t in TRANSITION_TEMPLATES:
        n = text.count(t)
        if n >= 2:
            out.append(RedundancyFinding(
                "RED-4", "weak", t, f"无信息转场模板出现 {n} 次"))

    # RED-5 unsupported superlative（与 P11-10 措辞校准联动的文本级检查）
    for w in SUPERLATIVES:
        if w in text:
            out.append(RedundancyFinding(
                "RED-5", "fail", w, "强断言词出现（须有对应证据级别）"))

    # RED-6 重复 claim（同一 claim 文本 ≥2 次）
    seen: dict[str, int] = {}
    for p in paras:
        seen[p] = seen.get(p, 0) + 1
    for p, n in seen.items():
        if n >= 2 and len(p) >= 5:
            out.append(RedundancyFinding(
                "RED-6", "weak", p[:20], f"同一段落文本重复 {n} 次"))
    return out
