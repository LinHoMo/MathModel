# -*- coding: utf-8 -*-
p = "tests/integration/test_e2e_metrics.py"
for enc in ("utf-8", "gbk", "utf-8-sig"):
    try:
        t = open(p, encoding=enc).read()
        if "_method_hit" in t:
            print("encoding:", enc)
            break
    except Exception as e:
        print(enc, "fail", e)
else:
    raise SystemExit("no encoding")

old = (
    'def test_method_hit_compact_canonicalization():\n'
    '    """P13-2：GT 串与卡族连写 token 的归一化伪影修复（统一规则，非单题特判）。"""\n'
    '    em = importlib.import_module("e2e_metrics")\n'
    '    names = {"mc-arima": "ARIMA 差分整合移动平均自回归 classical_timeseries"}\n'
    '    assert em._method_hit(["mc-arima"], names, ["time series"]) is True\n'
    '    assert em._method_hit(["mc-topsis"], {"mc-topsis": "TOPSIS evaluation"},\n'
    '                          ["time series"]) is False'
)
new = (
    'def test_structure_hit_compact_canonicalization():\n'
    '    """P13-2 统一规则（非单题特判）：allowed_modeling_structures 与卡族名的\n'
    '    紧凑匹配归一化（v1.2 起结构为唯一评分依据，字符串方法匹配已移除）。"""\n'
    '    em = importlib.import_module("e2e_metrics")\n'
    '    fam = {"mc-arima": "classical_timeseries"}\n'
    '    assert em._structure_hit("mc-arima", fam, ["time series"])[0] is True\n'
    '    assert em._structure_hit("mc-topsis", {"mc-topsis": "decision_analysis"},\n'
    '                             ["time series"])[0] is False\n'
    '    assert em._structure_hit("mc-arima", fam,\n'
    '                             ["classical_timeseries"])[0] is True'
)
assert old in t, "old pattern not found"
open(p, "w", encoding=enc).write(t.replace(old, new))
print("[OK] test updated")
