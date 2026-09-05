"""delivery gate 交付契约反例测试。

验证：
- 引用完整性：正文 \\cite key 必须在 references.bib 中定义
- AI 披露：正文含 AI 使用标注、参考文献列出 AI 工具、支撑材料含 AI工具使用详情.pdf
- PDF 编译链：xelatex -> bibtex -> xelatex -> xelatex 完整跑完
- 支撑材料：包含源程序、文件清单、不超过 20MB
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.tools import gate  # noqa: E402


def _run_delivery_gate(project, hand=None):
    """运行 delivery 层级门禁，返回 (exit_code, output)。"""
    cmd = [sys.executable, str(ROOT / "core" / "tools" / "gate.py"), str(project), "--level", "delivery"]
    if hand:
        cmd.append(hand)
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def _make_project(tmp_path, name="test_proj"):
    """创建最小可用项目结构。"""
    proj = tmp_path / name
    (proj / "work").mkdir(parents=True)
    (proj / "paper" / "figures").mkdir(parents=True)
    (proj / "code").mkdir(parents=True)
    (proj / "output").mkdir(parents=True)
    (proj / "figures").mkdir(parents=True)
    return proj


def _write_minimal_tex(proj):
    """写入最小可编译 main.tex。"""
    tex = r"""
\documentclass{cumcmthesis}
\begin{document}
\begin{abstract}
摘要内容。
\keywords{关键词1; 关键词2; 关键词3}
\end{abstract}
\section{问题重述}
问题描述。
\section{模型建立}
\begin{equation}
E = mc^2
\end{equation}
\section{结果分析}
结果见表~\ref{tab:1}。
\begin{table}
\caption{结果表}
\label{tab:1}
\begin{tabular}{cc}
\hline
A & B \\
\hline
\end{tabular}
</table>
\section{结论}
结论内容。
\bibliographystyle{gbt7714-numerical}
\bibliography{references}
\end{document}
"""
    (proj / "paper" / "main.tex").write_text(tex.strip(), encoding="utf-8")
    # 创建 PAPER_SPEC.md（交付门禁要求）
    (proj / "output" / "PAPER_SPEC.md").write_text("# PAPER_SPEC\n\n论文规格说明。", encoding="utf-8")


def _write_minimal_bib(proj):
    """写入最小 references.bib。"""
    bib = """@article{test2024,
  title={Test Paper},
  author={Author, A.},
  journal={Journal},
  year={2024}
}
@misc{chatgpt2024,
  title={ChatGPT},
  author={{OpenAI}},
  year={2024},
  howpublished={\\url{https://chat.openai.com}}
}
"""
    (proj / "paper" / "references.bib").write_text(bib, encoding="utf-8")


def _write_all_results(proj):
    """写入 all_results.json。"""
    (proj / "figures" / "all_results.json").write_text(json.dumps({"test": 1.0}), encoding="utf-8")


class TestDeliveryGateCitations:
    """引用完整性反例测试。"""

    def test_undefined_citation_fails(self, tmp_path):
        """正文含未定义的 \\cite key -> delivery gate 硬失败。"""
        proj = _make_project(tmp_path, "cite_fail")
        _write_minimal_tex(proj)
        # 修改 tex 引用不存在的 key
        tex = (proj / "paper" / "main.tex").read_text(encoding="utf-8")
        tex = tex.replace(r"\bibliography{references}", r"\cite{undefined_key}\n\bibliography{references}")
        (proj / "paper" / "main.tex").write_text(tex, encoding="utf-8")
        _write_minimal_bib(proj)
        _write_all_results(proj)

        rc, out = _run_delivery_gate(proj, "writer")
        assert rc == gate.EXIT_HARD, f"期望 EXIT_HARD，实际 {rc}"
        assert "undefined" in out.lower() or "未定义" in out, f"输出应含 undefined 提示: {out}"

    def test_defined_citation_passes(self, tmp_path):
        """正文引用已定义的 key -> delivery gate 通过。"""
        proj = _make_project(tmp_path, "cite_pass")
        _write_minimal_tex(proj)
        # 修改 tex 引用已定义的 key
        tex = (proj / "paper" / "main.tex").read_text(encoding="utf-8")
        tex = tex.replace(r"\bibliography{references}", r"\cite{test2024}\n\bibliography{references}")
        (proj / "paper" / "main.tex").write_text(tex, encoding="utf-8")
        _write_minimal_bib(proj)
        _write_all_results(proj)

        rc, out = _run_delivery_gate(proj, "writer")
        # 可能因其他缺失文件失败，但不应因引用失败
        assert "undefined" not in out.lower() and "未定义" not in out, f"不应报告 undefined 引用: {out}"


class TestDeliveryGateAIDisclosure:
    """AI 披露合规反例测试。"""

    def test_missing_ai_disclosure_in_body_fails(self, tmp_path):
        """正文缺 AI 使用标注 -> writer delivery gate 硬失败。"""
        proj = _make_project(tmp_path, "ai_body_fail")
        _write_minimal_tex(proj)
        _write_minimal_bib(proj)
        _write_all_results(proj)
        # 不添加 AI 披露标注

        rc, out = _run_delivery_gate(proj, "writer")
        assert rc == gate.EXIT_HARD, f"期望 EXIT_HARD，实际 {rc}"
        assert "ai" in out.lower() or "人工智能" in out, f"输出应含 AI 披露失败提示: {out}"

    def test_ai_disclosure_in_body_passes(self, tmp_path):
        """正文含 AI 使用标注 -> 不因 AI 披露失败。"""
        proj = _make_project(tmp_path, "ai_body_pass")
        _write_minimal_tex(proj)
        tex = (proj / "paper" / "main.tex").read_text(encoding="utf-8")
        # 添加 AI 使用标注（按 CUMCM 要求：正文标注、参考文献列出、支撑材料含PDF）
        tex = tex.replace(r"\section{问题重述}", r"\section{问题重述}\n本文使用了 ChatGPT 协助编写代码（AI 使用声明：生成式人工智能辅助）。")
        (proj / "paper" / "main.tex").write_text(tex, encoding="utf-8")
        _write_minimal_bib(proj)
        _write_all_results(proj)
        # 创建 AI 支撑材料 PDF（模拟）
        (proj / "paper" / "AI工具使用详情.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        rc, out = _run_delivery_gate(proj, "writer")
        # 可能因其他原因失败，但不应因正文 AI 披露失败
        ai_body_fail = any("[fail]" in line.lower() and "ai" in line.lower() and ("disclosure" in line.lower() or "披露" in line or "标注" in line) for line in out.splitlines())
        assert not ai_body_fail, f"不应报告正文 AI 披露失败: {out}"


class TestDeliveryGatePDFCompileChain:
    """PDF 编译链完整性反例测试。"""

    def test_incomplete_compile_chain_fails(self, tmp_path):
        """仅跑一次 xelatex（缺 bibtex/二次跑） -> delivery gate 硬失败。"""
        proj = _make_project(tmp_path, "compile_fail")
        _write_minimal_tex(proj)
        _write_minimal_bib(proj)
        _write_all_results(proj)

        # 模拟仅跑一次 xelatex 的 main.log
        log = r"""
This is xelatex, Version 3.14159265-2.6-0.999994 (TeX Live 2024)
Output written on main.pdf (1 pages).
"""
        (proj / "paper" / "main.log").write_text(log.strip(), encoding="utf-8")
        # 创建空 PDF
        (proj / "paper" / "main.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        rc, out = _run_delivery_gate(proj, "writer")
        assert rc == gate.EXIT_HARD, f"期望 EXIT_HARD，实际 {rc}"
        assert "compile chain" in out.lower() or "编译链" in out, f"输出应含编译链失败提示: {out}"

    def test_complete_compile_chain_passes(self, tmp_path):
        """完整编译链 -> 不因编译链失败。"""
        proj = _make_project(tmp_path, "compile_pass")
        _write_minimal_tex(proj)
        _write_minimal_bib(proj)
        _write_all_results(proj)

        # 模拟完整编译链的 main.log（包含 xelatex 4 次 + bibtex）
        log = r"""
This is xelatex, Version 3.14159265-2.6-0.999994 (TeX Live 2024)
Output written on main.pdf (1 pages).
This is xelatex, Version 3.14159265-2.6-0.999994 (TeX Live 2024)
Output written on main.pdf (1 pages).
This is BibTeX, Version 0.99d (TeX Live 2024)
This is xelatex, Version 3.14159265-2.6-0.999994 (TeX Live 2024)
Output written on main.pdf (1 pages).
This is xelatex, Version 3.14159265-2.6-0.999994 (TeX Live 2024)
Output written on main.pdf (1 pages).
"""
        (proj / "paper" / "main.log").write_text(log.strip(), encoding="utf-8")
        (proj / "paper" / "main.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

        rc, out = _run_delivery_gate(proj, "writer")
        # 可能因其他原因失败，但不应因编译链失败
        compile_fail = any("compile chain" in line.lower() and "fail" in line.lower() for line in out.splitlines())
        assert not compile_fail, f"不应报告编译链失败: {out}"


class TestDeliveryGateSupportMaterials:
    """支撑材料合规反例测试。"""

    def test_missing_source_code_fails(self, tmp_path):
        """支撑材料缺源程序 -> programmer delivery gate 硬失败。"""
        proj = _make_project(tmp_path, "support_fail")
        _write_minimal_tex(proj)
        _write_minimal_bib(proj)
        _write_all_results(proj)
        # 不创建 code/main.py

        rc, out = _run_delivery_gate(proj, "programmer")
        assert rc == gate.EXIT_HARD, f"期望 EXIT_HARD，实际 {rc}"
        assert "source" in out.lower() or "源程序" in out or "main.py" in out, f"输出应含源程序缺失提示: {out}"

    def test_source_code_exists_passes(self, tmp_path):
        """有源程序 -> 不因源程序缺失失败。"""
        proj = _make_project(tmp_path, "support_pass")
        _write_minimal_tex(proj)
        _write_minimal_bib(proj)
        _write_all_results(proj)
        (proj / "code" / "main.py").write_text("# main.py\nimport numpy as np\nnp.random.seed(42)\nprint('ok')", encoding="utf-8")

        rc, out = _run_delivery_gate(proj, "programmer")
        source_fail = any("source" in line.lower() and ("missing" in line.lower() or "缺失" in line or "不存在" in line) for line in out.splitlines())
        assert not source_fail, f"不应报告源程序缺失: {out}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])