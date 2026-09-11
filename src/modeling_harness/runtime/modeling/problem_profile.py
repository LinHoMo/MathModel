# -*- coding: utf-8 -*-
"""问题理解层（ADR-0008）——题面文本 → 子问题分解 + 问题类型 + 检索特征。

定位：Runtime **前置确定性层**，LLM-free、零第三方依赖、可重放。
它回答的问题只有一个：**在没有外部 Constructor 注入的情况下，生产路径如何
自己得到 features**。此前该环节缺失，`DefaultNodeExecutor` 回退把任何题硬编码为
`problem_types=["evaluation"]`，导致分解只出 1 问、选型家族全错（见 ADR-0008 证据）。

边界：
    * 本模块**不**做数学建模、不生成 MODEL_IR、不写 Artifact/Evidence。
    * 输出是**检索输入 DTO**，不是对问题本体的断言；类型标签是启发式映射，
      须随知识库扩充而维护（新增标签同时登记方法卡 problem_types 与
      `catalog/model_families.yaml`）。
    * 与 `runtime/knowledge/intelligence.py` 的 `ProblemProfile` 不是同一物：
      后者是竞赛智能包（P8）的画像 DTO；本模块的 `ProblemUnderstanding` 是
      从**原始题面文本**确定性派生出来的、可重放的理解结果。

来源单一真源：`inputs/question_spec.json`（结构化）优先，否则 `inputs/problem.txt`
（纯文本）。两者皆缺 → 返回 None（调用方如实处理，禁止回退掩盖）。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROFILER_VERSION = "profiler-v1"

# --------------------------------------------------------------- 子问题切分
#
# 真实 CUMCM 题面形态实测（2026-09-10）：
#   「问题 1 舞龙队沿螺距为 55 cm 的等距螺线……」   ← 数字前有空格、无冒号（2024A）
#   「问题1　某中药材形状大致呈圆柱形……」          ← 全角空格分隔（2026A/2026B）
# 旧实现的 `问题[一二三…\d]+[：:]` 要求冒号，对上述两种形态全部失配（产出 0 问）。
# 因此这里锚定**行首**，并要求数字后接分隔符（空白/全角空格/标点）或行尾——
# 后者可自动排除「附录2　问题1相关参数」这类行内引用（「问题1相」数字后无分隔符）。

_CN_DIGITS = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

_NUM = r"[0-9０-９一二三四五六七八九十]+"
_SEP = r"[\s\u3000：:、.．)）]"
_HEAD_RE = re.compile(
    rf"(?m)^[ \t\u3000]*(?:问题|Question)\s*({_NUM})\s*(?={_SEP}|$)",
    re.IGNORECASE,
)
# 段尾截断：附录/附件 标题行起（避免把附录内容算进最后一个子问题）
_TAIL_CUT_RE = re.compile(
    rf"(?m)^[ \t\u3000]*(?:附录|附件)\s*{_NUM}")


def _to_int(token: str) -> int:
    """「一」/「3」/「３」→ int；无可解析值返回 0。"""
    token = token.strip()
    if token.isdigit():
        return int(token)
    full = str.maketrans("０１２３４５６７８９", "0123456789")
    if token.translate(full).isdigit():
        return int(token.translate(full))
    if token in _CN_DIGITS:
        return _CN_DIGITS[token]
    if token == "十":
        return 10
    # 十一 … 十九
    if token.startswith("十") and token[1:] in _CN_DIGITS:
        return 10 + _CN_DIGITS[token[1:]]
    if token.endswith("十") and token[:-1] in _CN_DIGITS:
        return _CN_DIGITS[token[:-1]] * 10
    if len(token) == 3 and token[1] == "十":
        return _CN_DIGITS.get(token[0], 0) * 10 + _CN_DIGITS.get(token[2], 0)
    return 0


def split_sub_questions(text: str) -> list[dict[str, Any]]:
    """把题面文本切成子问题段。返回 [{index, label, heading, text}]。

    无任何标题命中时返回空列表（调用方如实处理，不编造子问题）。
    """
    marks = list(_HEAD_RE.finditer(text))
    if not marks:
        return []
    out: list[dict[str, Any]] = []
    for i, m in enumerate(marks):
        start = m.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[start:end]
        cut = _TAIL_CUT_RE.search(body)
        if cut:
            body = body[:cut.start()]
        body = body.strip()
        n = _to_int(m.group(1))
        label = f"Q{n}" if n else f"Q{i + 1}"
        first_line = body.splitlines()[0].strip() if body else ""
        out.append({
            "index": n or (i + 1),
            "label": label,
            "heading": m.group(0).strip(),
            "text": body,
            "title": first_line[:80],
        })
    return out


# --------------------------------------------------------------- 类型映射
#
# 标签取值**必须**来自方法卡 problem_types 词汇表（否则检索不可能命中）：
#   场/PDE: heat_transfer diffusion wave fluid_flow pollution_spread
#   移动边界: moving_boundary drying_shrinkage free_boundary
#   定位/几何: bearing_localization wedge_intersection geometric_inference
#   覆盖/搜索: coverage_path_planning search_and_clear discrete_event_simulation
#   评价/决策: evaluation ranking weighting decision
#   优化: optimization multi-objective
#   序贯/资源: sequential_decision resource_allocation shortest_path inventory_control
#   统计/学习: prediction timeseries classification clustering regression fitting
#              dimensionality-reduction
#   随机/模拟: uncertainty simulation random_service_system
#
# 顺序即输出顺序：先物理场，后几何/优化，最后通用手段——便于人工审阅。
_TYPE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("heat_transfer", ("热传导", "导热", "换热", "对流换热", "温度场",
                       "比热", "热风", "预热", "恒温干燥", "热扩散")),
    ("diffusion", ("扩散", "传质", "质量传递", "含水率", "水分浓度",
                   "渗透", "烘干", "干燥")),
    ("moving_boundary", ("移动边界", "自由边界", "尺寸变化", "收缩",
                         "半径变化", "形变", "干壳")),
    ("drying_shrinkage", ("失水收缩", "干缩", "收缩域")),
    ("fluid_flow", ("流体", "流动", "湍流", "水动力", "流场", "管道")),
    ("wave", ("波动", "振动", "波传播", "频率响应", "声波")),
    ("pollution_spread", ("污染物", "浓度分布", "扩散范围")),
    ("bearing_localization", ("示向度", "测向", "交会定位", "定位区域",
                              "干扰源", "测向机", "信号源")),
    ("wedge_intersection", ("交会", "方向线", "楔形", "夹角", "凸多边形")),
    ("coverage_path_planning", ("覆盖", "路径规划", "搜索路径", "巡逻", "遍历区域")),
    ("search_and_clear", ("清除", "搜索并", "归航", "逐个", "自动定位")),
    ("discrete_event_simulation", ("离散事件", "逐事件", "流程仿真")),
    ("geometric_inference", ("几何", "螺线", "位置", "速度", "轨迹", "曲线",
                             "坐标", "形状", "把手", "弦长", "半径")),
    ("evaluation", ("评价", "评估", "评分", "综合排序", "考核", "等级")),
    ("ranking", ("排名", "排序", "优劣")),
    ("weighting", ("权重", "赋权", "指标权重")),
    ("decision", ("决策", "方案选择", "取舍")),
    ("multi-objective", ("多目标", "多个目标", "均衡")),
    ("optimization", ("优化", "最优", "最小", "最大", "最短", "最长", "最快",
                      "目标函数", "策略设计", "求解")),
    ("sequential_decision", ("序贯", "分阶段决策", "动态规划", "逐步决策")),
    ("resource_allocation", ("资源分配", "调度", "分配方案")),
    ("shortest_path", ("最短路径", "最优路径")),
    ("prediction", ("预测", "预报", "估计未来")),
    ("timeseries", ("时间序列", "随时间变化", "逐时", "时序")),
    ("classification", ("分类", "判别", "识别", "诊断")),
    ("clustering", ("聚类", "分组", "分群")),
    ("regression", ("回归", "拟合关系")),
    ("fitting", ("拟合", "参数识别", "标定", "反演")),
    ("dimensionality-reduction", ("降维", "主成分", "因子分析")),
    ("uncertainty", ("误差", "不确定", "随机", "敏感性", "鲁棒")),
    ("simulation", ("模拟", "仿真", "演练", "蒙特卡洛")),
    ("random_service_system", ("排队", "服务系统", "到达率", "服务台")),
)

_DATA_HINTS = ("附件", "附表", "给定的", "给出", "已知", "测得", "实测", "数据")
_TIME_HINTS = ("随时间", "随时间变化", "每秒", "每隔", "时长", "时间演化",
               "时刻", "小时", "分钟", "秒")
_UNCERTAINTY_HINTS = ("误差", "不确定", "随机", "敏感性", "波动范围", "鲁棒")


@dataclass
class SubProblem:
    """一个子问题及其检索特征。"""
    label: str
    index: int
    title: str = ""
    text: str = ""
    problem_types: list[str] = field(default_factory=list)

    @property
    def features(self) -> dict[str, Any]:
        return {"problem_types": list(self.problem_types)}

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label, "index": self.index, "title": self.title,
            "problem_types": list(self.problem_types),
            "text_chars": len(self.text),
        }


@dataclass
class ProblemUnderstanding:
    """问题理解结果（确定性派生，可重放）。"""
    sub_questions: list[SubProblem]
    problem_types: list[str]
    features: dict[str, Any]
    per_question: dict[str, dict[str, Any]]
    source: str = "problem_txt"
    profiler_version: str = PROFILER_VERSION

    def as_dict(self) -> dict[str, Any]:
        return {
            "profiler_version": self.profiler_version,
            "source": self.source,
            "problem_types": list(self.problem_types),
            "sub_questions": [s.as_dict() for s in self.sub_questions],
            "features": dict(self.features),
            "per_question": {k: dict(v) for k, v in self.per_question.items()},
        }


def classify_types(text: str) -> list[str]:
    """文本 → 问题类型标签（按 _TYPE_RULES 顺序去重）。"""
    if not text:
        return []
    hits: list[str] = []
    for tag, keywords in _TYPE_RULES:
        if any(kw in text for kw in keywords):
            if tag not in hits:
                hits.append(tag)
    return hits


def _derive_global_features(text: str, sub_types: list[str]) -> dict[str, Any]:
    """全局特征（retriever.recommend 消费的六键 + 可观测来源标记）。

    objectives：题面显式多目标或子问题类型含 multi-objective → 2，否则 1。
    """
    multi = ("multi-objective" in sub_types)
    return {
        "problem_types": list(sub_types),
        "has_data": any(h in text for h in _DATA_HINTS),
        "sample_size": "medium",
        "time_series": any(h in text for h in _TIME_HINTS),
        "objectives": 2 if multi else 1,
        "uncertainty": any(h in text for h in _UNCERTAINTY_HINTS),
        "_features_source": PROFILER_VERSION,
    }


def understand_problem(text: str, source: str = "problem_txt") -> ProblemUnderstanding:
    """题面文本 → ProblemUnderstanding（确定性）。"""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("题面文本为空：无法派生问题理解（禁止编造特征）")
    raw = split_sub_questions(text)
    subs: list[SubProblem] = []
    per_question: dict[str, dict[str, Any]] = {}
    for item in raw:
        tags = classify_types(item["text"])
        sp = SubProblem(label=item["label"], index=item["index"],
                        title=item["title"], text=item["text"],
                        problem_types=tags)
        subs.append(sp)
        per_question[sp.label] = {
            "problem_types": list(tags),
            "problem_title": sp.title,
            "text_chars": len(sp.text),
            "_features_source": PROFILER_VERSION,
        }
    # 全局类型 = 各子问题类型并集（保持出现顺序）；无子问题时退回全文分类
    global_types: list[str] = []
    for s in subs:
        for t in s.problem_types:
            if t not in global_types:
                global_types.append(t)
    if not global_types:
        global_types = classify_types(text)
    features = _derive_global_features(text, global_types)
    features["problem_title"] = _problem_title(text)
    if subs:
        features["per_question"] = {k: dict(v) for k, v in per_question.items()}
    return ProblemUnderstanding(
        sub_questions=subs, problem_types=global_types, features=features,
        per_question=per_question, source=source)


def _problem_title(text: str) -> str:
    """取首个非空行的实质标题（去竞赛抬头）。失败时返回空串。"""
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if "数学建模竞赛题目" in s or "请先阅读" in s:
            continue
        return s[:120]
    return ""


# --------------------------------------------------------------- 项目加载

def load_problem_understanding(project_dir: str | Path) -> "ProblemUnderstanding | None":
    """从项目 inputs 派生问题理解；两处来源皆缺 → None。"""
    base = Path(project_dir) / "inputs"
    spec = base / "question_spec.json"
    text = base / "problem.txt"
    if spec.exists():
        try:
            raw = json.loads(spec.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(raw, dict):
            return None
        subs_raw = raw.get("problems") or raw.get("sub_questions") or []
        subs: list[SubProblem] = []
        per_question: dict[str, dict[str, Any]] = {}
        for i, q in enumerate(subs_raw):
            if isinstance(q, dict):
                label = str(q.get("id") or f"Q{i + 1}")
                desc = str(q.get("description") or q.get("content") or "")
                title = str(q.get("title") or "")
            else:
                label, desc, title = f"Q{i + 1}", str(q), ""
            tags = classify_types(desc) or classify_types(
                str(raw.get("background") or ""))
            subs.append(SubProblem(label=label, index=i + 1, title=title,
                                   text=desc, problem_types=tags))
            per_question[label] = {"problem_types": list(tags),
                                   "problem_title": title,
                                   "_features_source": PROFILER_VERSION}
        body = str(raw.get("background") or "") + " " + " ".join(s.text for s in subs)
        gtypes: list[str] = []
        for s in subs:
            for t in s.problem_types:
                if t not in gtypes:
                    gtypes.append(t)
        if not gtypes:
            gtypes = classify_types(body)
        features = _derive_global_features(body, gtypes)
        features["problem_title"] = str(raw.get("title") or _problem_title(body))
        if per_question:
            features["per_question"] = {k: dict(v) for k, v in per_question.items()}
        return ProblemUnderstanding(
            sub_questions=subs, problem_types=gtypes, features=features,
            per_question=per_question, source="question_spec")
    if text.exists():
        return understand_problem(text.read_text(encoding="utf-8"),
                                  source="problem_txt")
    return None
