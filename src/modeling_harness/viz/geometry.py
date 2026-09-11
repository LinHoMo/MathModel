#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""viz.geometry — GeometryIR：二维几何图示的类型化中间表示 + 确定性渲染。

为什么需要：``DiagramIR`` 表达的是「节点-边」关系图，画不出数学模型的**平面几何**
（角域楔形、凸多边形定位区域、外接圆、测向射线、覆盖环、归航轨迹）。本题（2026 B）
的模型主体恰恰是二维几何，需要一种能把坐标、形状与标注确定性地渲染成图的能力。

范式与 ``viz.ir`` 一致：类型化 IR + 确定性渲染 + fail-closed 契约校验，纯标准库
（零第三方依赖，ADR-0004），输出 byte-stable（无时间戳、无集合迭代序），可直接 git diff。

契约（schema_version 1.0）::

    {
      "schema_version": "1.0",
      "kind": "geometry",
      "title": "...",
      "viewport": {"xlim": [x0, x1], "ylim": [y0, y1], "equal_aspect": true},   # 可选
      "items": [
        {"kind": "point",    "points": [[x, y]],          "label": "...", "variant": "..."},
        {"kind": "segment",  "points": [[x1,y1],[x2,y2]], "label": "...", "variant": "..."},
        {"kind": "ray",      "at": [x, y], "bearing_deg": 30.0, "length": 1200.0},
        {"kind": "polygon",  "points": [[..],[..],[..]],  "label": "...", "variant": "..."},
        {"kind": "polyline", "points": [[..],[..], ...],  "arrow": true},
        {"kind": "circle",   "center": [x, y], "radius": 50.0, "label": "...", "variant": "..."},
        {"kind": "label",    "at": [x, y], "text": "...", "variant": "..."}
      ],
      "legend": ["..."]
    }

契约破损（未知 kind / 点数不足 / 非有限坐标 / 半径非正 / label 无文本 / 空图）一律抛
:class:`GeometryIRError` —— fail-closed，绝不放行半成品。
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = "1.0"

FIGURE_KINDS = ("geometry",)
ITEM_KINDS = ("point", "segment", "ray", "polygon", "polyline", "circle", "label")
#: 视觉变体（对齐 viz.ir 的 Node.variant 思路）：默认 / 强调 / 弱化 / 虚线 / 危险
ITEM_VARIANTS = ("default", "emphasis", "muted", "dashed", "danger", "accent")

_MIN_POINTS = {"point": 1, "segment": 2, "polygon": 3, "polyline": 2}


class GeometryIRError(ValueError):
    """GeometryIR 契约破损 —— fail-closed。"""


def _finite(value: Any, what: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise GeometryIRError(f"{what} 必须为数值，得到 {value!r}")
    out = float(value)
    if not math.isfinite(out):
        raise GeometryIRError(f"{what} 必须为有限数，得到 {value!r}")
    return out


def _point(value: Any, what: str) -> Tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise GeometryIRError(f"{what} 必须为 [x, y]，得到 {value!r}")
    return (_finite(value[0], f"{what}[0]"), _finite(value[1], f"{what}[1]"))


@dataclass
class Item:
    """几何图元。``kind`` 决定哪些字段必填；其余留空。"""

    kind: str
    points: List[Tuple[float, float]] = field(default_factory=list)
    center: Optional[Tuple[float, float]] = None
    radius: Optional[float] = None
    at: Optional[Tuple[float, float]] = None
    bearing_deg: Optional[float] = None
    length: Optional[float] = None
    text: str = ""
    label: str = ""
    variant: str = "default"
    arrow: bool = False

    def validate(self) -> None:
        if self.kind not in ITEM_KINDS:
            raise GeometryIRError(f"非法 item.kind={self.kind!r}；允许 {ITEM_KINDS}")
        if self.variant not in ITEM_VARIANTS:
            raise GeometryIRError(
                f"{self.kind} 非法 variant={self.variant!r}；允许 {ITEM_VARIANTS}"
            )
        for i, p in enumerate(self.points):
            _point(list(p), f"{self.kind}.points[{i}]")

        if self.kind in _MIN_POINTS:
            need = _MIN_POINTS[self.kind]
            if len(self.points) < need:
                raise GeometryIRError(
                    f"{self.kind} 至少需要 {need} 个点，得到 {len(self.points)}"
                )
            if self.kind in ("point", "segment") and len(self.points) != need:
                raise GeometryIRError(
                    f"{self.kind} 恰好需要 {need} 个点，得到 {len(self.points)}"
                )
        elif self.kind == "circle":
            if self.center is None:
                raise GeometryIRError("circle 缺少 center")
            _point(list(self.center), "circle.center")
            if self.radius is None:
                raise GeometryIRError("circle 缺少 radius")
            if _finite(self.radius, "circle.radius") <= 0:
                raise GeometryIRError(f"circle.radius 必须为正，得到 {self.radius!r}")
        elif self.kind == "ray":
            if self.at is None:
                raise GeometryIRError("ray 缺少 at")
            _point(list(self.at), "ray.at")
            if self.bearing_deg is None:
                raise GeometryIRError("ray 缺少 bearing_deg")
            _finite(self.bearing_deg, "ray.bearing_deg")
            if self.length is None or _finite(self.length, "ray.length") <= 0:
                raise GeometryIRError(f"ray.length 必须为正，得到 {self.length!r}")
        elif self.kind == "label":
            if self.at is None:
                raise GeometryIRError("label 缺少 at")
            _point(list(self.at), "label.at")
            if not self.text.strip():
                raise GeometryIRError("label 的 text 不可为空")

    # ---- 序列化 ----------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"kind": self.kind}
        if self.kind in _MIN_POINTS:
            out["points"] = [[p[0], p[1]] for p in self.points]
        if self.kind == "circle" and self.center is not None:
            out["center"] = [self.center[0], self.center[1]]
            out["radius"] = self.radius
        if self.kind == "ray" and self.at is not None:
            out["at"] = [self.at[0], self.at[1]]
            out["bearing_deg"] = self.bearing_deg
            out["length"] = self.length
        if self.kind == "label" and self.at is not None:
            out["at"] = [self.at[0], self.at[1]]
            out["text"] = self.text
        if self.kind == "polyline" and self.arrow:
            out["arrow"] = True
        if self.label:
            out["label"] = self.label
        if self.variant and self.variant != "default":
            out["variant"] = self.variant
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Item":
        if not isinstance(data, dict):
            raise GeometryIRError(f"item 必须为对象，得到 {type(data).__name__}")
        pts: List[Tuple[float, float]] = [
            _point(p, f"points[{i}]") for i, p in enumerate(data.get("points", []) or [])
        ]
        item = cls(
            kind=str(data.get("kind") or ""),
            points=pts,
            center=_point(data["center"], "center") if data.get("center") else None,
            radius=data.get("radius"),
            at=_point(data["at"], "at") if data.get("at") else None,
            bearing_deg=data.get("bearing_deg"),
            length=data.get("length"),
            text=str(data.get("text") or ""),
            label=str(data.get("label") or ""),
            variant=str(data.get("variant") or "default"),
            arrow=bool(data.get("arrow") or False),
        )
        item.validate()
        return item

    # ---- 几何辅助 --------------------------------------------------------

    def bounds(self) -> Optional[Tuple[float, float, float, float]]:
        """返回 (minx, miny, maxx, maxy)；无法给出有限界时返回 None。"""
        xs: List[float] = []
        ys: List[float] = []
        if self.kind in _MIN_POINTS:
            xs += [p[0] for p in self.points]
            ys += [p[1] for p in self.points]
        elif self.kind == "circle":
            if self.center is None or self.radius is None:  # validate() 已保证
                return None
            cx, cy = self.center
            r = float(self.radius)
            xs += [cx - r, cx + r]
            ys += [cy - r, cy + r]
        elif self.kind == "ray":
            if self.at is None or self.bearing_deg is None or self.length is None:
                return None
            ax, ay = self.at
            ln = float(self.length)
            ex = ax + ln * math.cos(math.radians(float(self.bearing_deg)))
            ey = ay + ln * math.sin(math.radians(float(self.bearing_deg)))
            xs += [ax, ex]
            ys += [ay, ey]
        elif self.kind == "label":
            if self.at is None:
                return None
            xs += [self.at[0]]
            ys += [self.at[1]]
        if not xs or not ys:
            return None
        return (min(xs), min(ys), max(xs), max(ys))


@dataclass
class Viewport:
    """视口。给定时按给定范围，否则由内容自动取界。``equal_aspect`` 保持等比。"""

    xlim: Optional[Tuple[float, float]] = None
    ylim: Optional[Tuple[float, float]] = None
    equal_aspect: bool = True

    def validate(self) -> None:
        for name, lim in (("xlim", self.xlim), ("ylim", self.ylim)):
            if lim is None:
                continue
            lo = _finite(lim[0], f"viewport.{name}[0]")
            hi = _finite(lim[1], f"viewport.{name}[1]")
            if hi <= lo:
                raise GeometryIRError(f"viewport.{name} 必须递增，得到 {lim!r}")

    def to_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        if self.xlim is not None:
            out["xlim"] = [self.xlim[0], self.xlim[1]]
        if self.ylim is not None:
            out["ylim"] = [self.ylim[0], self.ylim[1]]
        out["equal_aspect"] = bool(self.equal_aspect)
        return out


@dataclass
class GeometryIR:
    """二维几何图示的中间表示。构建后须 :meth:`validate` 通过方可渲染。"""

    title: str = ""
    items: List[Item] = field(default_factory=list)
    viewport: Viewport = field(default_factory=Viewport)
    legend: List[str] = field(default_factory=list)
    kind: str = "geometry"
    schema_version: str = SCHEMA_VERSION

    # ---- 契约校验 --------------------------------------------------------

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise GeometryIRError(
                f"schema_version 必须为 {SCHEMA_VERSION!r}，得到 {self.schema_version!r}"
            )
        if self.kind not in FIGURE_KINDS:
            raise GeometryIRError(f"非法 kind={self.kind!r}；允许 {FIGURE_KINDS}")
        if not self.items:
            raise GeometryIRError("GeometryIR 至少需要一个 item（空图无意义）")
        for i, item in enumerate(self.items):
            try:
                item.validate()
            except GeometryIRError as exc:
                raise GeometryIRError(f"items[{i}]（{item.kind}）：{exc}") from exc
        self.viewport.validate()

    # ---- 确定性序列化 ----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "title": self.title,
            "viewport": self.viewport.to_dict(),
            "items": [i.to_dict() for i in self.items],
            "legend": list(self.legend),
        }

    def to_json(self) -> str:
        # sort_keys + 固定缩进 + 末尾换行 → byte-stable，可 git diff
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GeometryIR":
        if not isinstance(data, dict):
            raise GeometryIRError("IR 顶层必须为对象")
        items = [Item.from_dict(x) for x in data.get("items", []) or []]
        vp_raw = data.get("viewport") or {}
        if not isinstance(vp_raw, dict):
            raise GeometryIRError("viewport 必须为对象")
        vp = Viewport(
            xlim=_point(vp_raw["xlim"], "viewport.xlim") if vp_raw.get("xlim") else None,
            ylim=_point(vp_raw["ylim"], "viewport.ylim") if vp_raw.get("ylim") else None,
            equal_aspect=bool(vp_raw.get("equal_aspect", True)),
        )
        ir = cls(
            title=str(data.get("title") or ""),
            items=items,
            viewport=vp,
            legend=[str(x) for x in data.get("legend", []) or []],
            kind=str(data.get("kind") or "geometry"),
            schema_version=str(data.get("schema_version") or SCHEMA_VERSION),
        )
        ir.validate()
        return ir

    @classmethod
    def from_json(cls, text: str) -> "GeometryIR":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeometryIRError(f"IR 非合法 JSON：{exc}") from exc
        return cls.from_dict(data)

    @classmethod
    def load(cls, path: "str | Path") -> "GeometryIR":
        return cls.from_json(Path(path).read_text(encoding="utf-8"))


__all__ = [
    "SCHEMA_VERSION",
    "FIGURE_KINDS",
    "ITEM_KINDS",
    "ITEM_VARIANTS",
    "GeometryIRError",
    "Item",
    "Viewport",
    "GeometryIR",
]
