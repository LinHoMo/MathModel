# -*- coding: utf-8 -*-
"""U10 二次修复：坏测试代码（语法错误）→ 合法执行代码。"""
from pathlib import Path

p = Path(r"C:\Users\Lin\Desktop\Programs\MathModel\tests\unit\test_execution_adapter.py")
s = p.read_text(encoding="utf-8")

old = '''    def test_status_never_defaulted(self):
        # 执行必须产生真实状态；plan 不执行时不能凭空 success
        r = self._run("raise SystemExit(0) if False else print('ok')")
        # audit Batch8：原断言 status in 全枚举恒真（重言式）——强化为
        # 验证真实执行内容：success 且 stdout 含输出
        assert r.status == "success", f"真实执行应 success，实际 {r.status}"
        assert "ok" in (r.stdout or ""), f"stdout 应含真实输出，实际 {r.stdout!r}"'''

new = '''    def test_status_never_defaulted(self):
        # 执行必须产生真实状态；plan 不执行时不能凭空 success
        # audit Batch8：原代码 `raise SystemExit(0) if False else print('ok')`
        # 是语法错误（raise 不能用于条件表达式）→ 恒 failed → 原断言恒真掩盖坏测试；
        # 现改为合法代码，验证真实执行内容（success + stdout 输出）
        r = self._run("print('ok')")
        assert r.status == "success", f"真实执行应 success，实际 {r.status}"
        assert "ok" in (r.stdout or ""), f"stdout 应含真实输出，实际 {r.stdout!r}"'''

assert old in s, "pattern not found"
p.write_text(s.replace(old, new, 1), encoding="utf-8")
print("U10 fixed (round 2)")
