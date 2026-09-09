# -*- coding: utf-8 -*-
"""K002 Input Authenticity — 新增 3 题 SHA256 冻结 + manifest 登记 + card.yaml 回填。

流程（沿用 Input Authenticity Recovery 标准）：
1. 题面双源交叉验证（已完成的 web 取证，见各 card.yaml verification notes）
2. 计算 problem_statement.txt sha256
3. 回填 card.yaml 的 text_sha256
4. 更新 input_manifest.json（追加 3 条，保留既有 5 条）
"""
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CARDS = REPO / "research/P15/benchmark/problem_cards"
MANIFEST = REPO / "research/P15/benchmark/manifests/input_manifest.json"

NEW = [
    {
        "problem_id": "2018_B",
        "title": "智能RGV的动态调度策略",
        "year": 2018,
        "letter": "B",
        "source_url": "https://blog.csdn.net/qq_40307529/article/details/82745055",
        "secondary_source_url": "https://www.mcm.edu.cn/html_cn/node/4ecb988d2402ddf884e3b5ea04f0ae14.html",
        "source_type": "mature_resource",
        "source_level": 3,
        "retrieval_date": "2026-09-09",
        "local_path": "research/P15/benchmark/problem_cards/2018_B/problem_statement.txt",
        "text_sha256": None,
        "attachment_sha256": None,
        "authenticity_status": "verified",
        "verification_notes": ("Cross-verified against 2 independent sources: "
            "(1) CSDN blog by qq_40307529 with full problem text incl. 3 scenarios "
            "(single/two-process, 1% fault), task 1+2, Table 1 (3 data groups), 8-hour shift; "
            "(2) mcm.edu.cn official review page confirms title and scope "
            "(2018 undergraduate group B '智能RGV的动态调度策略')."),
        "sub_question_count": 4,
        "has_attachments": True,
        "attachment_note": ("附件1 智能加工系统示意图（图1）；附件2 EXCEL结果表（3个工作表，"
            "对应3组系统作业参数数据，需填写调度策略与作业效率）"),
    },
    {
        "problem_id": "2017_B",
        "title": "“拍照赚钱”的任务定价",
        "year": 2017,
        "letter": "B",
        "source_url": "https://sxx.czc.edu.cn/info/1039/2577.htm",
        "secondary_source_url": "https://dxs.moe.gov.cn/zx/a/hd_sxjm_sthb/231127/1867377.shtml",
        "source_type": "university_repost",
        "source_level": 2,
        "retrieval_date": "2026-09-09",
        "local_path": "research/P15/benchmark/problem_cards/2017_B/problem_statement.txt",
        "text_sha256": None,
        "attachment_sha256": None,
        "authenticity_status": "verified",
        "verification_notes": ("Cross-verified against 2 independent sources: "
            "(1) 长治学院数学系存档 (sxx.czc.edu.cn) with full 4 sub-questions and "
            "3 attachments; (2) 中国大学生在线 official problem download page "
            "(dxs.moe.gov.cn CUMCM2017Problems.rar). Both match: pricing rules, "
            "completion (1/0), member credit/booking limit, pack publishing."),
        "sub_question_count": 4,
        "has_attachments": True,
        "attachment_note": ("附件一 已结束项目任务数据（位置/定价/完成情况）；附件二 会员信息数据"
            "（位置/信誉值/开始预订时间/预订限额）；附件三 新项目任务数据（仅位置信息）"),
    },
    {
        "problem_id": "2011_B",
        "title": "交巡警服务平台的设置与调度",
        "year": 2011,
        "letter": "B",
        "source_url": "https://dxs.moe.gov.cn/zx/a/qkt_sxjm/120829/1185246.shtml",
        "secondary_source_url": "https://sx.xxu.edu.cn/info/1050/1390.htm",
        "source_type": "official_platform",
        "source_level": 1,
        "retrieval_date": "2026-09-09",
        "local_path": "research/P15/benchmark/problem_cards/2011_B/problem_statement.txt",
        "text_sha256": None,
        "attachment_sha256": None,
        "authenticity_status": "verified",
        "verification_notes": ("Cross-verified against 2 independent sources, text "
            "word-for-word identical: (1) 中国大学生在线 official problem page "
            "(dxs.moe.gov.cn); (2) 新乡学院数学与统计学院存档 (sx.xxu.edu.cn). "
            "Both contain Q1(管辖分配/13要道封锁/新增2-5平台), Q2(全市合理性/P32围堵), "
            "attachments 1-2, figure legend notes."),
        "sub_question_count": 5,
        "has_attachments": True,
        "attachment_note": ("附件1 A区与全市六区交通网络与平台设置示意图（附图1 A区、附图2 全市）；"
            "附件2 全市六区交通网络与平台设置相关数据表（5个工作表）"),
    },
]


def sha256_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    # 1) 计算 sha256 + 回填 card.yaml
    for entry in NEW:
        pid = entry["problem_id"]
        txt = CARDS / pid / "problem_statement.txt"
        assert txt.exists(), f"missing: {txt}"
        h = sha256_text(txt)
        entry["text_sha256"] = h
        card = CARDS / pid / "card.yaml"
        content = card.read_text(encoding="utf-8")
        content = re.sub(r"text_sha256: PENDING", f"text_sha256: {h}", content)
        card.write_text(content, encoding="utf-8")
        print(f"[{pid}] sha256={h[:16]}… card.yaml backfilled")

    # 2) 更新 manifest（保留既有，追加新增）
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    existing = {p["problem_id"] for p in manifest["problems"]}
    added = 0
    for entry in NEW:
        if entry["problem_id"] not in existing:
            manifest["problems"].append(entry)
            added += 1
    assert added == 3, f"expected 3 new, got {added}"
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"manifest updated: {len(manifest['problems'])} problems "
          f"({len(existing)} existing + {added} new)")


if __name__ == "__main__":
    main()
