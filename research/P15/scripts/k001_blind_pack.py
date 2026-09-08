#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""k001_blind_pack.py — 导出盲评包（去标识）

盲评包只包含：submission_id + 题面 + MODEL_IR + 评分表模板。
**不含** condition / arm / batch / knowledge / seed / rep 的任何信息。

导出后脚本会自检：包内不得出现 arm 标识、sham、批次名等泄漏词。

产物：
    analysis/raw/blind/<sid>.md            盲评输入（给 evaluator）
    analysis/raw/scores/<sid>.template.json 评分骨架（填好后改名为 <sid>.json）

用法:
    py -3.12 research/P15/scripts/k001_blind_pack.py
    py -3.12 research/P15/scripts/k001_blind_pack.py --batch batch0

退出码：0 = 正常；1 = 发现标识泄漏。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import k001_common as K  # noqa: E402

BLIND_DIR = K.ANALYSIS / "raw" / "blind"
SCORE_DIR = K.ANALYSIS / "raw" / "scores"

LEAK_WORDS = [
    "sham", "负控制", "对照实验", "实验分组", "knowledge_trace", "manifest.json",
    "batch0", "batch1", "batch2", "batch3", "batch4",
    "rejected", "retrieved",
    # 臂标识：model_id / 描述里出现 armX、baseline、case 等都会直接解盲
    "arm a", "arm b", "arm c", "arm d", "arm e", "arma", "armb", "armc", "armd",
    "arme", "-baseline", "structural case", "knowledge card", "方法卡", "结构案例",
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


def registered_runs(batch: str | None = None) -> list:
    cmap = K.read_json(K.KEY / "condition_map.json")["map"]
    out = []
    for sid in sorted(cmap):
        mpath = K.RUNS / sid / "manifest.json"
        if not mpath.exists():
            continue
        m = K.read_json(mpath)
        if m.get("status") != "REGISTERED":
            continue
        if batch and m.get("batch") != batch:
            continue
        out.append(sid)
    return out


def build_pack(sid: str) -> tuple:
    m = K.read_json(K.RUNS / sid / "manifest.json")
    problem = K.problem_index()[m["problem_id"]]
    statement = (K.ROOT / problem["statement_path"]).read_text(encoding="utf-8").strip()
    ir = (K.RUNS / sid / "model_ir.json").read_text(encoding="utf-8")

    md = f"""# 盲评样本 {sid}

> 评估者须知：请只依据下面「题面」与「模型产物」评分。
> 本样本不含任何分组信息，也**不要**推测其分组。
> 评分标准：`research/P15/capability/MODEL_CONSTRUCTION_RUBRIC.md`（v1.0）

## 题面

{statement}

## 模型产物（MODEL IR）

```json
{ir}
```

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


def check_leak(sid: str, text: str) -> list:
    low = text.lower()
    hits = [w for w in LEAK_WORDS if w.lower() in low]
    return hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", default=None)
    args = ap.parse_args(argv)

    sids = registered_runs(args.batch)
    if not sids:
        print("[FAIL] 没有 status=REGISTERED 的 run，请先执行 k001_register.py")
        return 1

    BLIND_DIR.mkdir(parents=True, exist_ok=True)
    SCORE_DIR.mkdir(parents=True, exist_ok=True)

    leaked = []
    for sid in sids:
        md, m = build_pack(sid)
        hits = check_leak(sid, md)
        if hits:
            leaked.append((sid, hits))
        (BLIND_DIR / f"{sid}.md").write_text(md, encoding="utf-8")

        det_path = K.RUNS / sid / "deterministic.json"
        det = K.read_json(det_path) if det_path.exists() else {}
        template = {
            "submission_id": sid,
            "evaluator": {"model": "", "type": "independent_llm", "version": "", "timestamp": ""},
            "rubric_version": "MODEL_CONSTRUCTION_RUBRIC-v1.0",
            "dimensions": {d: {"score": None, "evidence": ""} for d in [
                "L1.1", "L1.2", "L1.3", "L1.4", "L1.5",
                "L2.1", "L2.2", "L2.3", "L2.4", "L2.5", "L2.6", "L2.7",
                "L3.1", "L3.2", "L3.3", "L3.4", "L3.5",
                "L4.1", "L4.2", "L4.3", "L4.4", "L4.5"]},
            "vector": {},
            "deterministic": det,
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
