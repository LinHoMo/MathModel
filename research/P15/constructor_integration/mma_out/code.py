# -*- coding: utf-8 -*-
"""2024A 简化校准模型（外部 Constructor 注入；demo 可执行模型）。

约定（LocalPythonAdapter）：stdout 最后一块合法 JSON 作为 outputs。
真实数值：a=2.0, x=3.0, b=1.0 -> y = 7.0。
"""
import json


def solve(inputs):
    a = float(inputs["a"])
    x = float(inputs["x"])
    b = float(inputs["b"])
    return {"y": a * x + b, "ok": True, "a": a, "x": x, "b": b}


if __name__ == "__main__":
    data = json.load(open("input.json", encoding="utf-8"))
    print(json.dumps(solve(data), ensure_ascii=False))
