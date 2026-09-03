#!/usr/bin/env python3
"""text_cleanup.py — 10 步确定性 AI 文本净化流水线（移植自 opendraft-master）。

MathModelSkills 项目工具，供 writer/guardrails-checker 在论文生成后自动净化 AI 痕迹。
与 writing_check.py 互补：writing_check.py 只"检"（不 green 则 BLOCK）；
本工具负责"修"——对检出的问题做确定性自动修正。

设计原则：
- 纯函数 `apply_full_cleanup(text) -> {"text": str, "stats": dict}`
- 零外部依赖（仅 re / typing）
- 支持英文过渡词冗余、同义堆叠、元评论、声称校准、词汇多样性等 10 类净化
- 中文论文场景下，英文过渡词冗余项大多不生效，但"同义堆叠裁剪"、"声称校准"、
  "元评论删除"、"冗余短语压缩"仍有效

用法：
    python core/tools/text_cleanup.py <file.tex> [--output <out.tex>] [--stats] [--dry-run]
    python core/tools/text_cleanup.py --text "待清理文本" [--stats]

    # Python API
    from core.tools.text_cleanup import apply_full_cleanup, detect_repetition, detect_advocacy_language
    result = apply_full_cleanup(tex_text)
    cleaned = result["text"]
    stats  = result["stats"]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

# =============================================================================
# 清理模式（纯数据，无依赖）
# =============================================================================

# 句首填充过渡词（英文，中文论文命中有限但仍有"此外/另外"等场景以中文模式补充）
FILLER_STARTS = [
    r"Furthermore,\s*",
    r"Moreover,\s*",
    r"Additionally,\s*",
    r"It is worth noting that\s*",
    r"It should be noted that\s*",
    r"Importantly,\s*",
    r"It is important to note that\s*",
    r"In addition,\s*",
    r"Notably,\s*",
]

# 中文冗余过渡词
ZH_FILLER_STARTS = [
    r"此外，?\s*",
    r"另外，?\s*",
    r"值得注意的是，?\s*",
    r"需要指出的是，?\s*",
    r"重要的是，?\s*",
    r"特别地，?\s*",
]

# 空泛强化词
INTENSIFIERS = re.compile(
    r"\b(very|extremely|highly)\s+(?=[a-z])",
    re.IGNORECASE,
)

# 元评论模式（以"本节讨论..."开头的自指句）
META_PATTERNS = [
    r"This section discusses\s+[^.]+\.\s*",
    r"This subsection examines\s+[^.]+\.\s*",
    r"This section explores\s+[^.]+\.\s*",
    r"This section provides\s+[^.]+\.\s*",
    r"This subsection provides\s+[^.]+\.\s*",
    r"This section reviews\s+[^.]+\.\s*",
    r"In this section,\s+we\s+[^.]+\.\s*",
    r"The following section\s+[^.]+\.\s*",
    r"The following subsection\s+[^.]+\.\s*",
    # 中文元评论
    r"本节讨论了[^。]+\。\s*",
    r"本节探讨了[^。]+\。\s*",
    r"本节提供了[^。]+\。\s*",
    r"本小节讨论了[^。]+\。\s*",
    r"本小节分析了[^。]+\。\s*",
]

# 冗余短语 → 简洁替换
VERBOSE_PHRASES = [
    (r"\bin order to\b", "to"),
    (r"\bdue to the fact that\b", "because"),
    (r"\ba large number of\b", "many"),
    (r"\bthe vast majority of\b", "most"),
    (r"\bat the present time\b", "now"),
    (r"\bin the event that\b", "if"),
    (r"\bhas the ability to\b", "can"),
    (r"\bprior to\b", "before"),
    (r"\bsubsequent to\b", "after"),
    (r"\bwith regard to\b", "regarding"),
    (r"\bwith respect to\b", "regarding"),
    (r"\bin spite of the fact that\b", "although"),
    (r"\bfor the purpose of\b", "to"),
    (r"\bis able to\b", "can"),
    (r"\ba significant number of\b", "many"),
    (r"\bin light of\b", "given"),
    (r"\bon the basis of\b", "based on"),
    (r"\bas a consequence of\b", "because of"),
]

# 同义堆叠链压缩（"important, essential, and paramount" → "essential"）
SYNONYM_CHAINS = [
    (r"\bimportant,\s*essential,\s*and\s*paramount\b", "essential"),
    (r"\bcomprehensive,\s*thorough,\s*and\s*exhaustive\b", "thorough"),
    (r"\bcrucial,\s*vital,\s*and\s*critical\b", "critical"),
    (r"\bsignificant,\s*substantial,\s*and\s*considerable\b", "substantial"),
    (r"\brapid,\s*swift,\s*and\s*fast\b", "rapid"),
    (r"\bvast,\s*extensive,\s*and\s*far-reaching\b", "extensive"),
    (r"\brobust,\s*resilient,\s*and\s*durable\b", "robust"),
    # 中文同义堆叠
    (r"重要[、,]\s*必要[、,]\s*且?关键", "关键"),
    (r"全面[、,]\s*深入[、,]\s*且?系统", "系统"),
    (r"准确[、,]\s*精确[、,]\s*且?可靠", "准确"),
]

# 文中论点重述中和
THESIS_RESTATEMENTS = [
    (r"(?<=\.\s)As\s+this\s+(?:paper|study)\s+argues?,?\s*", "As discussed, "),
    (r"(?<=\.\s)This\s+(?:paper|study)\s+has\s+argued\s+that\b", "The analysis shows that"),
    (r"(?<=\.\s)We\s+argue\s+that\b", "The evidence suggests that"),
    (r"(?<=\.\s)The\s+central\s+argument\s+of\s+this\s+(?:paper|study)\b", "A key finding"),
    (r"(?<=\.\s)This\s+study\s+demonstrates\s+that\b", "The analysis reveals that"),
    # 中文论点重述
    (r"(?<=\。)\s*本文认为，?", ""),
    (r"(?<=\。)\s*综上所述[^，]*，?", "基于以上分析，"),
]

# 词汇多样性轮换（仅在出现 >3 次时生效）
VOCAB_DIVERSITY = [
    (r"\bmechanism\b", ["process", "pathway", "driver", "dynamic", "factor"]),
    (r"\bvulnerability\b", ["susceptibility", "risk factor", "exposure", "sensitivity"]),
    (r"\bsignificant\b(?!\s+(?:at|p\s*[<>=]|difference|effect))",
     ["substantial", "considerable", "notable", "marked", "meaningful"]),
    (r"\bdemonstrates?\b", ["shows", "reveals", "indicates", "illustrates", "establishes"]),
    (r"\butilize[sd]?\b", ["use", "uses", "used"]),
    (r"\bfacilitate[sd]?\b", ["enables", "supports", "helps", "allows"]),
    (r"\bcomprehensive\b", ["thorough", "extensive", "detailed", "wide-ranging"]),
    (r"\brobust\b", ["strong", "reliable", "solid", "stable"]),
    (r"\bparadigm\b(?!\s+shift)", ["framework", "model", "approach", "perspective"]),
]

# 声称校准（overconfident → academic hedging）
CLAIM_CALIBRATION = [
    (r"\bis\s+indisputable\b", "is strongly supported"),
    (r"\bindisputable\s+evidence\b", "strong evidence"),
    (r"\bundeniable\b", "well-established"),
    (r"\bunquestionable\b", "well-documented"),
    (r"\bproves\s+conclusively\s+that\b", "provides strong support for the conclusion that"),
    (r"\bprove\s+conclusively\s+that\b", "provide strong support for the conclusion that"),
    (r"\bwithout\s+(?:a\s+)?doubt\b", "with high confidence"),
    (r"\bis\s+the\s+only\b", "is a primary"),
    (r"\bthe\s+only\s+solution\b", "a key solution"),
    (r"\bthe\s+only\s+approach\b", "a key approach"),
    (r"\bis\s+the\s+best\b", "is among the most effective"),
    (r"\bis\s+revolutionary\b", "represents a significant advancement"),
    (r"\brevolutionary\s+approach\b", "innovative approach"),
    (r"\bparadigm\s+shift\b", "significant development"),
    (r"\bis\s+always\b(?!\s+(?:been|had|have))", "is consistently"),
    (r"\bis\s+never\b(?!\s+(?:been|had|have))", "is rarely"),
    (r"\bis\s+perfect\b", "is highly accurate"),
    (r"\bsolves\s+the\s+problem\b", "addresses the challenge"),
    (r"\bproves\s+that\b", "supports the finding that"),
    (r"\bprove\s+that\b", "support the finding that"),
    (r"\bobviously\b", "notably"),
    (r"\bclearly\s+shows\b", "indicates"),
    (r"\bclearly\s+show\b", "indicate"),
    # 中文声称校准
    (r"无可争议", "有充分证据支撑"),
    (r"毫无疑问", "具有较高置信度"),
    (r"唯一方案", "关键方案"),
    (r"最好的", "较为有效的"),
    (r"总是", "倾向于"),
    (r"从不", "极少"),
    (r"完美的", "高精度的"),
]


# =============================================================================
# 纯函数
# =============================================================================

def apply_full_cleanup(text: str) -> Dict[str, Any]:
    """对文本应用 10 步确定性 AI 痕迹净化流水线。

    Args:
        text: 待清理的论文草稿

    Returns:
        dict: {"text": 清理后文本, "stats": 各类清理计数}
    """
    stats: Dict[str, int] = {
        "fillers": 0,
        "intensifiers": 0,
        "verbose": 0,
        "meta": 0,
        "synonyms": 0,
        "thesis": 0,
        "vocab_diversified": 0,
        "claims_calibrated": 0,
    }

    # 1. 移除句首填充过渡词（英文）
    for pattern in FILLER_STARTS:
        before = text
        text = re.sub(r"(?m)(^|\.\s+)" + pattern, lambda m: m.group(1), text)
        if text != before:
            stats["fillers"] += 1

    # 2. 移除中文句首过渡词冗余
    for pattern in ZH_FILLER_STARTS:
        before = text
        text = re.sub(r"(?m)(^|[。，]\s*)" + pattern, lambda m: m.group(1), text)
        if text != before:
            stats["fillers"] += 1

    # 3. 移除空泛强化词
    text, n = INTENSIFIERS.subn("", text)
    stats["intensifiers"] = n

    # 4. 同义堆叠压缩
    for pattern, replacement in SYNONYM_CHAINS:
        before = text
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        if text != before:
            stats["synonyms"] += 1

    # 5. 移除元评论
    for pattern in META_PATTERNS:
        before = text
        text = re.sub(pattern, "", text)
        if text != before:
            stats["meta"] += 1

    # 6. 压缩冗余短语
    for pattern, replacement in VERBOSE_PHRASES:
        before = text
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        if text != before:
            stats["verbose"] += 1

    # 7. 中和文中论点重述
    for pattern, replacement in THESIS_RESTATEMENTS:
        before = text
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        if text != before:
            stats["thesis"] += 1

    # 8. 词汇多样性轮换（仅当 >3 次时）
    for pattern, synonyms in VOCAB_DIVERSITY:
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        if len(matches) > 3:
            for i, match in enumerate(reversed(matches[2:])):
                idx = len(matches) - 3 - i
                synonym = synonyms[idx % len(synonyms)]
                if match.group().istitle():
                    synonym = synonym.title()
                elif match.group().isupper():
                    synonym = synonym.upper()
                text = text[:match.start()] + synonym + text[match.end():]
                stats["vocab_diversified"] += 1

    # 9. 声称校准
    for pattern, replacement in CLAIM_CALIBRATION:
        before = text
        count = len(re.findall(pattern, text, flags=re.IGNORECASE))
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        if text != before:
            stats["claims_calibrated"] += count

    # 10. 清理多余空白
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"  +", " ", text)

    return {"text": text, "stats": stats}


def detect_repetition(text: str) -> Dict[str, Any]:
    """检测论文重述和短语重复。

    Returns:
        dict: {"warnings": [...], "status": "pass"|"needs_review"}
    """
    warnings: List[Dict[str, Any]] = []

    # 论点重述计数
    thesis_patterns = [
        r"this\s+paper\s+argues?",
        r"the\s+central\s+argument",
        r"this\s+study\s+demonstrates?",
        r"we\s+argue\s+that",
        r"本文认为",
        r"综上所述",
    ]
    thesis_count = sum(len(re.findall(p, text, re.I)) for p in thesis_patterns)
    if thesis_count > 3:
        warnings.append({
            "type": "thesis_repetition",
            "count": thesis_count,
            "message": f"论点重述 {thesis_count} 次（建议 2-3 次）",
        })

    # 5-gram 短语重复检测
    words = text.lower().split()
    if len(words) > 100:
        phrase_counts: Dict[str, int] = {}
        for i in range(len(words) - 4):
            phrase = " ".join(words[i : i + 5])
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        repeated = [(p, c) for p, c in phrase_counts.items() if c >= 3]
        if repeated:
            warnings.append({
                "type": "repeated_phrases",
                "count": len(repeated),
                "examples": [p for p, c in sorted(repeated, key=lambda x: -x[1])[:5]],
            })

    return {"warnings": warnings, "status": "pass" if not warnings else "needs_review"}


def detect_advocacy_language(text: str) -> Dict[str, Any]:
    """检测不适合学术文风的倡导性语言。

    Returns:
        dict: {"findings": [...], "status": "pass"|"needs_review"}
    """
    patterns = [
        (r"\bmust\s+be\s+adopted\b", "prescriptive", "应被采用"),
        (r"\bwe\s+advocate\b", "advocacy", "我们倡导"),
        (r"\bundeniably\b", "overconfident", "无可否认"),
        (r"\bunquestionably\b", "overconfident", "毫无疑问地"),
        (r"\bobviously\b", "overconfident", "显然"),
        (r"\bdemands\s+that\b", "prescriptive", "要求"),
        (r"必须被采纳", "prescriptive_zh", "必须被采纳"),
        (r"我们呼吁", "advocacy_zh", "我们呼吁"),
    ]

    findings: List[Dict[str, Any]] = []
    for pattern, desc, _ in patterns:
        matches = re.findall(pattern, text, re.I)
        if matches:
            findings.append({"type": desc, "count": len(matches)})

    return {"findings": findings, "status": "pass" if not findings else "needs_review"}


def clean_text(text: str) -> str:
    """便捷包装：仅返回清理后的文本。"""
    return apply_full_cleanup(text)["text"]


# =============================================================================
# CLI 入口
# =============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(
        description="10 步 AI 文本净化流水线（移植自 opendraft-master）"
    )
    ap.add_argument("file", nargs="?", help="待清理的 .tex 文件路径")
    ap.add_argument("--output", "-o", help="输出文件路径（默认覆盖源文件）")
    ap.add_argument("--text", "-t", help="直接传入待清理文本（与 file 二选一）")
    ap.add_argument("--stats", action="store_true", help="输出清理统计到 stderr")
    ap.add_argument("--dry-run", action="store_true", help="只输出统计，不修改文件")
    args = ap.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        text = args.text
    else:
        ap.error("请提供 --file 或 --text 参数")
        return 2

    result = apply_full_cleanup(text)

    if args.stats or args.dry_run:
        print(f"[text_cleanup] stats: {result['stats']}", file=sys.stderr)

    if not args.dry_run:
        out_path = args.output or args.file
        if out_path:
            Path(out_path).write_text(result["text"], encoding="utf-8")
            print(f"[text_cleanup] cleaned -> {out_path}", file=sys.stderr)
        else:
            print(result["text"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
