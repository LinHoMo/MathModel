#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k002_blind_pack.py — 导出 P15-K002 盲评包（去标识）

三臂差异处理：
  * F 臂：盲评主体 = model_doc.md（自由文本）
  * S / SV 臂：盲评主体 = model_ir.json（+SV 臂附 validation_plan.json）

盲评包只包含：submission_id + 题面 + 模型产物 + 评分表模板。
**不含** condition / arm / batch / seed / rep / precheck 的任何信息。
model_id 强制中性化为 `m-<sha256 前 8 位>`，防止产物自带标识解盲。

导出后脚本自检：包内不得出现 arm 标识、precheck、batch 名等泄漏词。

产物：
    analysis_k002/raw/blind/<sid>.md             盲评输入（给 evaluator）
    analysis_k002/raw/scores/<sid>.template.json 评分骨架（填好后改名 <sid>.json）

用法:
    py -3.12 research/P15/scripts/k002_blind_pack.py [--precheck] [--batch <id>]

退出码：0 = 正常；1 = 发现标识泄漏。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k002_common as K  # noqa: E402

PRE_EXP = K.EXP.parent / "P15-K002-precheck"
BLIND_DIR = K.ANALYSIS / "raw_k002" / "blind"
SCORE_DIR = K.ANALYSIS / "raw_k002" / "scores"

LEAK_WORDS = [
    "precheck", "预检", "区分度", "condition_map", "对照实验", "实验分组",
    "knowledge_trace", "manifest.json", "batch0", "batch1", "batch2", "batch3",
    "batch4", "batch5", "batch6", "rejected", "retrieved",
    "armf", "arms", "armsv", "arm f", "arm s", "arm sv",
    "自由文本组", "结构化组", "验证计划组", "baseline", "treatment",
]

RUBRIC_SHEET = """## 评分表（请逐维填写，分数必须附证据指针）

| 维度 | 满分 | 得分 | 证据（artifact 路径 / 字段 / 摘录） |
|---|---|---|---|
| L1.1 显式条件提取 | 2 | | |
| L1.2 隐式条件识别 | 2 | | |
| L1.3 交付要求识别 | 2 | | |
| L1.4 歧义点标注 | 1 | | |
| L1.5 问题类型判定 | 2 | | |
| L2.1 变量声明完备性 | 2 | | |
| L2.2 参数声明完备性 | 2 | | |
| L2.3 假设合理性 | 2 | | |
| L2.4 目标正确性 | 2 | | |
| L2.5 约束完备性 | 2 | | |
| L2.6 机理正确性 | 3 | | |
| L2.7 方程结构完整性 | 2 | | |
| L3.1 求解策略匹配 | 2 | | |
| L3.2 代码可执行性 | 2 | | |
| L3.3 结果收敛性 | 2 | | |
| L3.4 可复现性 | 2 | | |
| L3.5 结果合理性 | 1 | | |
| L4.1 对照基线 | 2 | | |
| L4.2 灵敏度分析 | 2 | | |
| L4.3 极限/边界检验 | 1 | | |
| L4.4 验证目标正确性 | 2 | | |
| L4.5 证据-主张对应 | 2 | | |

评分标准见 `research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md`。
**不要**在备注中出现任何关于本样本属于哪一组的推测或标记。
"""

DIMS = [
    "L1.1", "L1.2", "L1.3", "L1.4", "L1.5",
    "L2.1", "L2.2", "L2.3", "L2.4", "L2.5", "L2.6", "L2.7",
    "L3.1", "L3.2", "L3.3", "L3.4", "L3.5",
    "L4.1", "L4.2", "L4.3", "L4.4", "L4.5",
]


def exp_root(precheck: bool) -> Path:
    return PRE_EXP if precheck else K.EXP


def runs_root(precheck: bool) -> Path:
    return PRE_EXP / "runs" if precheck else K.RUNS


def condition_map(precheck: bool) -> dict:
    if precheck:
        return K.read_json(PRE_EXP / "key" / "condition_map.json")["map"]
    return K.read_json(K.KEY / "condition_map.json")["map"]


def build_pack(sid: str, precheck: bool) -> tuple:
    rr = runs_root(precheck)
    m = K.read_json(rr / sid / "manifest.json")
    pid = m["problem_id"]
    statement = (K.PROBLEM_CARDS / pid / "problem_statement.txt").read_text(
        encoding="utf-8").strip()

    arm = m["arm"]
    parts = []
    if arm in ("S", "SV"):
        ir_path = rr / sid / "model_ir.json"
        ir_txt = ir_path.read_text(encoding="utf-8") if ir_path.exists() else "{}"
        # model_id 中性化：防止产物自带标识解盲
        ir_txt = neutralized_json(ir_txt)
        parts.append("## 模型产物（MODEL IR）\n\n```json\n" + ir_txt + "\n```")
        if arm == "SV":
            vp_path = rr / sid / "validation_plan.json"
            vp_txt = vp_path.read_text(encoding="utf-8") if vp_path.exists() else "{}"
            vp_txt = neutralized_json(vp_txt)
            parts.append("## 验证计划（Validation Plan）\n\n```json\n" + vp_txt + "\n```")
    else:  # F
        doc_path = rr / sid / "model_doc.md"
        doc_txt = doc_path.read_text(encoding="utf-8") if doc_path.exists() \
            else "(F 臂产物缺失)"
        doc_txt = re.sub(r"\bM-[0-9a-f]{6,}", "m-xxxx", doc_txt)
        parts.append("## 模型产物（模型文档）\n\n" + doc_txt)

    md = f"""# 盲评样本 {sid}

> 评估者须知：请只依据下面「题面」与「模型产物」评分。
> 本样本不含任何分组信息，也**不要**推测其分组。
> 评分标准：`research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md`（v1.1）

## 题面

{statement}

{chr(10).join(parts)}

{RUBRIC_SHEET}

## 失败模式标注

请从 `research/P15/capability/FAILURE_TAXONOMY.md` 中选择命中的 FM 代号（`FM-XX-NNN`），
可多选，也可为空：

```
failure_modes: []
```

## 备注

```
notes:
```
"""
    return md, m


def neutralized_json(text: str) -> str:
    """把 model_id / submission_id 等身份字段中性化（保 JSON 合法）。"""
    try:
        obj = json.loads(text)
    except Exception:
        # 非合法 JSON（生成者格式问题），退化为正则替换
        text = re.sub(r'"model_id"\s*:\s*"[^"]*"',
                      '"model_id": "m-xxxx"', text)
        return text
    if isinstance(obj, dict):
        if obj.get("model_id"):
            h = hashlib.sha256(str(obj["model_id"]).encode("utf-8")).hexdigest()[:8]
            obj["model_id"] = f"m-{h}"
        if obj.get("submission_id"):
            obj["submission_id"] = sid_placeholder(obj["submission_id"])
        if "validation_plan" in obj and isinstance(obj["validation_plan"], dict):
            if obj["validation_plan"].get("model_id"):
                obj["validation_plan"]["model_id"] = obj.get("model_id", "m-xxxx")
    return json.dumps(obj, ensure_ascii=False, indent=2)


def sid_placeholder(s: str) -> str:
    return "s-xxxx" if isinstance(s, str) and len(s) >= 8 else s


def check_leak(text: str) -> list:
    low = text.lower()
    return [w for w in LEAK_WORDS if w.lower() in low]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--precheck", action="store_true",
                    help="对 P15-K002-precheck 目录出包（区分度预检）")
    ap.add_argument("--batch", default=None)
    args = ap.parse_args(argv)

    cmap = condition_map(args.precheck)
    sids = []
    for sid in sorted(cmap):
        rr = runs_root(args.precheck)
        mpath = rr / sid / "manifest.json"
        if not mpath.exists():
            continue
        m = K.read_json(mpath)
        if m.get("status") not in ("REGISTERED", "GENERATED", "COVERAGE_FAIL"):
            continue
        if args.batch and m.get("batch") != args.batch:
            continue
        sids.append(sid)
    if not sids:
        print("[FAIL] 没有可用 run，请先执行生成与登记")
        return 1

    BLIND_DIR.mkdir(parents=True, exist_ok=True)
    SCORE_DIR.mkdir(parents=True, exist_ok=True)

    leaked = []
    for sid in sids:
        md, m = build_pack(sid, args.precheck)
        hits = check_leak(md)
        if hits:
            leaked.append((sid, hits))
        (BLIND_DIR / f"{sid}.md").write_text(md, encoding="utf-8")

        template = {
            "submission_id": sid,
            "evaluator": {"model": "", "type": "independent_llm",
                          "version": "", "timestamp": ""},
            "rubric_version": "MODEL_CONSTRUCTION_RUBRIC-v1.1",
            "dimensions": {d: {"score": None, "evidence": ""} for d in DIMS},
            "vector": {},
            "failure_modes": [],
            "notes": "",
        }
        (SCORE_DIR / f"{sid}.template.json").write_text(
            json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] 盲评包 {len(sids)} 份 → {K.rel(BLIND_DIR)}")
    print(f"[OK] 评分支架 {len(sids)} 份 → {K.rel(SCORE_DIR)}（填好后去掉 .template 后缀）")
    if leaked:
        print("[FAIL] 盲评包存在标识泄漏：")
        for sid, hits in leaked:
            print(f"   {sid}: {hits}")
        return 1
    print("[PASS] 盲评包无标识泄漏。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
