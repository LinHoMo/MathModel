#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一门禁入口 —— 跨 runtime 执行协议的卡点层。

用法
----
    python core/tools/gate.py <project> <hand> <agent>   # 单步门禁
    python core/tools/gate.py <project> <hand>           # 整手门禁
    python core/tools/gate.py <project> all              # 全链路门禁

退出码
------
    0  全部通过（含 SKIP）
    1  仅软失败（WARN），可推进
    2  存在 HARD 失败（阻塞，须按 SKILL.md 的 Iteration 修正后重跑）
    3  参数错误 / 项目不存在 / 脚本异常

设计要点
--------
此前 19 个 agent 的 `## Self-Check` 全是人读的 `[ ]` 复选框——
模型可以勾完所有框然后继续，等于没有门禁。
这里把 Self-Check 转成**可执行断言**，由脚本判定 PASS/FAIL，
与宿主 agent 无关：任何 runtime 都能 `python core/tools/gate.py`。
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gatelib as G
import state as S

# ---------------------------------------------------------------------------
# 每个 agent 的门禁断言
# ---------------------------------------------------------------------------
# 产物路径取自各 SKILL.md 的 Contract 段。
# 断言强度分两级：HARD（阻塞）/ 非阻塞（历史项目可能未产出该文件）。

GATES = {
    # ---------------- Modeler ----------------
    ("modeler", "problem-parser"): [
        lambda p: _check_inputs_readonly(p),
        lambda p: G.check_files_exist(p, ["work/question_spec.json"], "question_spec"),
        lambda p: G.check_json_valid(p, "work/question_spec.json"),
        lambda p: G.check_schema(p, "work/question_spec.json",
                                 "core/schemas/question_spec.schema.json"),
    ],
    ("modeler", "type-classifier"): [
        lambda p: G.check_files_exist(p, ["work/type_classification.json"],
                                      "type_classification"),
        lambda p: G.check_json_valid(p, "work/type_classification.json"),
    ],
    ("modeler", "literature-searcher"): [
        lambda p: G.check_files_exist(p, ["work/literature_evidence.json"],
                                      "literature_evidence"),
        lambda p: G.check_json_valid(p, "work/literature_evidence.json"),
        lambda p: G.check_schema(p, "work/literature_evidence.json",
                                 "core/schemas/literature_evidence.schema.json"),
    ],
    ("modeler", "method-matcher"): [
        lambda p: G.check_files_exist(p, ["work/method_candidates.json"],
                                      "method_candidates"),
        lambda p: G.check_json_valid(p, "work/method_candidates.json"),
        # P2-3：编码前风险探针——在投入实现前暴露方法不可行
        lambda p: G.check_risk_probe(p),
    ],
    ("modeler", "model-builder"): [
        lambda p: G.check_files_exist(p, ["work/model_draft.md"], "model_draft"),
    ],
    ("modeler", "dag-builder"): [
        lambda p: G.check_files_exist(p, ["work/model_dag.json"], "model_dag"),
        lambda p: G.check_json_valid(p, "work/model_dag.json"),
        lambda p: G.check_schema(p, "work/model_dag.json",
                                 "core/schemas/model_dag.schema.json"),
        lambda p: G.check_files_exist(p, ["work/model_dag.svg"], "model_dag.svg"),
    ],
    ("modeler", "assumption-validator"): [
        lambda p: G.check_files_exist(p, ["work/assumption_validation.json"],
                                      "assumption_validation"),
        lambda p: G.check_json_valid(p, "work/assumption_validation.json"),
    ],
    ("modeler", "spec-auditor"): [
        lambda p: G.check_files_exist(p, ["output/MODEL_SPEC.md"], "MODEL_SPEC"),
        # 工程产物允许提及内部路径（all_results.json / work/ 等）。
        # 铁律 W7「禁止内部术语」只约束论文正文，不约束交付给下游的工程文档。
        lambda p: G.check_guardrails(p, ["output/MODEL_SPEC.md"], allow_internal=True),
    ],

    # ---------------- Programmer ----------------
    ("programmer", "template-selector"): [
        lambda p: G.check_files_exist(p, ["work/template_plan.json"], "template_plan"),
        lambda p: G.check_json_valid(p, "work/template_plan.json"),
    ],
    ("programmer", "code-implementer"): [
        lambda p: G.check_risk_probe(p),   # 编码前必须已通过风险探针
        lambda p: G.check_files_exist(p, ["code/main.py"], "main.py"),
    ],
    ("programmer", "test-runner"): [
        lambda p: G.check_files_exist(p, ["work/test_report.json"], "test_report"),
        lambda p: G.check_json_valid(p, "work/test_report.json"),
    ],
    ("programmer", "result-verifier"): [
        lambda p: G.check_files_exist(p, ["work/result_validation.json"],
                                      "result_validation"),
        lambda p: G.check_json_valid(p, "work/result_validation.json"),
        lambda p: G.check_files_exist(p, ["figures/all_results.json"],
                                      "all_results"),
    ],
    ("programmer", "guardrails-checker"): [
        lambda p: G.check_files_exist(p, ["work/guardrails_report_programmer.json"],
                                      "guardrails_report_programmer"),
        lambda p: G.check_json_valid(p, "work/guardrails_report_programmer.json"),
    ],
    ("programmer", "hash-auditor"): [
        lambda p: G.check_files_exist(p, ["output/CODE_DELIVERABLES.md"],
                                      "CODE_DELIVERABLES"),
        lambda p: G.check_guardrails(p, ["output/CODE_DELIVERABLES.md"],
                                     allow_internal=True),
    ],

    # ---------------- Writer ----------------
    ("writer", "structure-planner"): [
        lambda p: G.check_files_exist(p, ["work/paper_structure.json"],
                                      "paper_structure"),
        lambda p: G.check_json_valid(p, "work/paper_structure.json"),
        # P2-7：评委视角——评分点必须映射到论文章节
        lambda p: G.check_rubric_alignment(p),
    ],
    ("writer", "section-writer"): [
        lambda p: G.check_files_exist(p, ["paper/main.tex"], "main.tex"),
        lambda p: G.check_tex_no_lists(p, "paper/main.tex"),
        # P2-9 内容级校验：不只是"文件在不在"，而是"内容对不对"
        lambda p: G.check_symbols_consistency(p),
        lambda p: G.check_assumptions_referenced(p),
        lambda p: G.check_figures_referenced(p),
        lambda p: G.check_min_count(p, "paper/main.tex",
                                    r"\\begin\{(equation|align|gather|multline)\*?\}",
                                    15, "公式数(W-env)"),
    ],
    ("writer", "figure-generator"): [
        lambda p: _check_figures(p),
    ],
    ("writer", "reference-curator"): [
        lambda p: G.check_files_exist(p, ["paper/references.bib"], "references.bib"),
        lambda p: G.check_min_count(p, "paper/references.bib", r"@\w+\{",
                                    10, "参考文献数"),
        lambda p: _check_no_future_refs(p),
    ],
    ("writer", "consistency-checker"): [
        lambda p: G.check_files_exist(p, ["work/consistency_report.json"],
                                      "consistency_report"),
        lambda p: G.check_json_valid(p, "work/consistency_report.json"),
    ],
    ("writer", "guardrails-checker"): [
        lambda p: G.check_guardrails(p, ["paper/main.tex"]),
    ],
    # ---------------- Reviewer（P2 新增评审手）----------------
    ("reviewer", "scorer-academic"): [
        lambda p: G.check_files_exist(p, ["work/score_card_academic.json"],
                                      "score_card_academic"),
        lambda p: G.check_json_valid(p, "work/score_card_academic.json"),
    ],
    ("reviewer", "scorer-engineering"): [
        lambda p: G.check_files_exist(p, ["work/score_card_engineering.json"],
                                      "score_card_engineering"),
        lambda p: G.check_json_valid(p, "work/score_card_engineering.json"),
    ],
    ("reviewer", "scorer-judge"): [
        lambda p: G.check_files_exist(p, ["work/score_card_judge.json"],
                                      "score_card_judge"),
        lambda p: G.check_json_valid(p, "work/score_card_judge.json"),
    ],
    ("reviewer", "scorer-reader"): [
        lambda p: G.check_files_exist(p, ["work/score_card_reader.json"],
                                      "score_card_reader"),
        lambda p: G.check_json_valid(p, "work/score_card_reader.json"),
    ],
    ("reviewer", "scorer-adversarial"): [
        lambda p: G.check_files_exist(p, ["work/score_card_adversarial.json"],
                                      "score_card_adversarial"),
        lambda p: G.check_json_valid(p, "work/score_card_adversarial.json"),
        # 聚合卡的存在性/合法性/generated_by 三件事由一次重算比对覆盖：
        # 文件不存在或 JSON 坏了，--verify 同样报错，而且报得更具体。
        lambda p: _check_score_card_aggregated(p),
    ],
    ("reviewer", "weakness-hunter"): [
        lambda p: G.check_files_exist(p, ["work/weakness_report.json"],
                                      "weakness_report"),
        lambda p: G.check_json_valid(p, "work/weakness_report.json"),
    ],
    ("reviewer", "revision-planner"): [
        lambda p: G.check_files_exist(p, ["work/revision_plan.json"],
                                      "revision_plan"),
        lambda p: G.check_json_valid(p, "work/revision_plan.json"),
    ],
    ("reviewer", "revision-executor"): [
        lambda p: G.check_files_exist(p, ["work/execution_report.json"],
                                      "execution_report"),
        lambda p: G.check_json_valid(p, "work/execution_report.json"),
        lambda p: _check_execution_verdict(p),
    ],

    ("writer", "final-validator"): [
        lambda p: G.check_files_exist(p, ["output/PAPER_SPEC.md"], "PAPER_SPEC"),
        lambda p: G.check_guardrails(p, ["output/PAPER_SPEC.md"], allow_internal=True),
        lambda p: G.check_files_exist(p, ["paper/main.tex"], "main.tex"),
        lambda p: G.check_sensitivity_really_scanned(p),
        # ---- 国赛验收（目标 A）：固化 6verity 硬项为可执行断言 ----
        lambda p: G.check_cumcm_placeholders(p),
        lambda p: G.check_cumcm_internal_leaks(p),
        lambda p: G.check_cumcm_section_structure(p),
        lambda p: _check_latex_compiles(p),
        lambda p: _check_code_runs_lite(p),
        lambda p: _check_pdf(p),
        # ---- 论文版面阈值（env: paper.*）----
        # 必须排在 _check_latex_compiles 之后：check_paper_pages 与
        # check_page_fill_ratio 依赖编译产生的 main.log。
        # 只挂 final-validator，不挂 section-writer——写作中途页数必然不足，
        # 挂硬门禁会卡死增量执行。
        lambda p: _vp_check(p, "check_paper_pages"),
        lambda p: _vp_check(p, "check_page_fill_ratio"),
        lambda p: _vp_check(p, "check_paper_words"),
        lambda p: _vp_check(p, "check_paper_tables"),
        lambda p: _vp_check(p, "check_paper_figures"),
        lambda p: _vp_check(p, "check_paper_equations"),
        lambda p: _vp_check(p, "check_paper_references"),
        lambda p: _vp_check(p, "check_pdf_compile_chain"),
        # ---- 国赛官方披露合规 + 内联引用（CUMCM 2025 硬性要求）----
        lambda p: G.check_cumcm_inline_citation(p),
        lambda p: G.check_cumcm_ai_disclosure_body(p),
        lambda p: G.check_cumcm_ai_support(p),
        lambda p: G.check_cumcm_ai_referenced(p),
    ],
}


# 交付门禁：验证各手的最终交付契约（复用 validate_project 检查）
def _vp_check_delivery(project, fname):
    """跑 validate_project 里的单个检查函数，映射为 gatelib.Check。"""
    import validate_project as VP

    fn = getattr(VP, fname, None)
    if fn is None:
        return G.fail(f"交付检查/{fname}", "validate_project 无此检查函数")
    # 初始化 VP 全局变量（复用 gate.py 中的 _vp_init 逻辑）
    module, _err = VP._load_env_loader(G.ROOT)
    if module is not None:
        VP._ENV_GET = module.get
    VP._STRICT_MODE = bool(VP._ENV_GET("runtime.strict_mode") or True)
    _pt, is_physics = VP._detect_problem_type(G.project_dir(project))
    VP._IS_PHYSICS = is_physics

    mark = len(VP.results)
    try:
        fn(G.project_dir(project))
    except Exception as e:
        del VP.results[mark:]
        return G.fail(f"交付检查/{fname}", f"执行异常: {e}", hard=False)

    new = VP.results[mark:]
    del VP.results[mark:]
    if not new:
        return G.fail(f"交付检查/{fname}", "未产生任何判定", hard=False)

    rank = {VP.HARD: 2, VP.WARN: 1, VP.PASS: 0}
    status, name, detail = max(new, key=lambda t: rank.get(t[0], 0))
    if status == VP.PASS:
        return G.ok(name, detail)
    return G.fail(name, detail, hard=(status == VP.HARD))


DELIVERY_GATES = {
    "modeler": [
        lambda p: G.check_files_exist(p, ["output/MODEL_SPEC.md"], "MODEL_SPEC"),
        lambda p: G.check_guardrails(p, ["output/MODEL_SPEC.md"], allow_internal=True),
        lambda p: G.check_schema(p, "output/MODEL_SPEC.md", "core/schemas/model_spec.schema.json"),
    ],
    "programmer": [
        lambda p: G.check_files_exist(p, ["output/CODE_DELIVERABLES.md"], "CODE_DELIVERABLES"),
        lambda p: G.check_guardrails(p, ["output/CODE_DELIVERABLES.md"], allow_internal=True),
        lambda p: G.check_files_exist(p, ["figures/all_results.json"], "all_results"),
        lambda p: G.check_files_exist(p, ["code/main.py"], "main.py"),
    ],
    "writer": [
        lambda p: G.check_files_exist(p, ["output/PAPER_SPEC.md"], "PAPER_SPEC"),
        lambda p: G.check_guardrails(p, ["output/PAPER_SPEC.md"], allow_internal=True),
        lambda p: G.check_files_exist(p, ["paper/main.tex"], "main.tex"),
        lambda p: G.check_files_exist(p, ["paper/references.bib"], "references.bib"),
        # 复用 validate_project 的深度检查
        lambda p: _vp_check_delivery(p, "check_citation_integrity"),
        lambda p: _vp_check_delivery(p, "check_figure_refs"),
        lambda p: _vp_check_delivery(p, "check_pdf_compile_chain"),
        lambda p: _vp_check_delivery(p, "check_placeholders"),
        lambda p: _vp_check_delivery(p, "check_forbidden_words"),
        # CUMCM 合规检查（通过 gatelib 直接调用）
        lambda p: G.check_cumcm_inline_citation(p),
        lambda p: G.check_cumcm_ai_disclosure_body(p),
        lambda p: G.check_cumcm_ai_support(p),
        lambda p: G.check_cumcm_ai_referenced(p),
    ],
    "reviewer": [
        lambda p: G.check_files_exist(p, ["work/revision_plan.json"], "revision_plan"),
        lambda p: G.check_json_valid(p, "work/revision_plan.json"),
        lambda p: G.check_files_exist(p, ["work/execution_report.json"], "execution_report"),
        lambda p: G.check_json_valid(p, "work/execution_report.json"),
        lambda p: _check_execution_verdict(p),
    ],
}


def _check_execution_verdict(project):
    """revision-executor：execution_report.json 的 verdict 必须为 pass。"""
    import json
    path = G.project_dir(project) / "work" / "execution_report.json"
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return G.fail("execution_report", f"读取失败: {e}")
    verdict = report.get("verdict", "")
    if verdict != "pass":
        unresolved = report.get("blocking_unresolved", [])
        detail = f"blocking_unresolved={unresolved}" if unresolved else "见 execution_report.json"
        return G.fail("execution_verdict", f"verdict={verdict!r}，{detail}")
    failed_tasks = [t for t in report.get("tasks", []) if t.get("acceptance_check") != "pass"]
    if failed_tasks:
        ids = [t.get("id") for t in failed_tasks]
        return G.fail("execution_tasks", f"以下任务未通过验收: {ids}")
    if report.get("consistency_gate") != "pass":
        return G.fail("consistency_gate", "consistency-checker 门禁未通过")
    return G.ok("execution_verdict", "所有修改任务验收通过，consistency-checker 门禁放行")


def _check_figures(project):
    """论文插图：figures/ 下至少 6 张 png/pdf。"""
    d = G.project_dir(project) / "paper" / "figures"
    if not d.exists():
        return G.fail("插图数", "paper/figures 目录不存在")
    imgs = [f for f in d.iterdir()
            if f.suffix.lower() in (".png", ".pdf", ".jpg", ".eps")]
    if len(imgs) < 6:
        return G.fail("插图数", f"{len(imgs)} < 6（env: paper.min_figures）")
    return G.ok("插图数", f"{len(imgs)} >= 6")


def _check_pdf(project):
    """最终 PDF：存在且不小于 100KB（env: paper.pdf_min_bytes）。"""
    pdf = G.project_dir(project) / "paper" / "main.pdf"
    if not pdf.exists():
        return G.fail("PDF 产物", "无 paper/main.pdf", hard=False)
    size = pdf.stat().st_size
    if size < 102400:
        return G.fail("PDF 大小", f"{size} 字节 < 100KB", hard=False)
    return G.ok("PDF 产物", f"{size // 1024} KB")


def _check_score_card_aggregated(project):
    """P0-2：work/score_card.json 必须由 aggregate_scores.py 生成。

    这个文件同时是三个消费方的输入——本门禁、score_artifact.py 的 verdict 重算、
    revision-planner 的修改清单——但此前没有任何 agent 声明产出它、也没有任何脚本
    生成它，唯一的"生成者"是模型手写的 JSON。手写卡在 cumcm2024a 上的实际后果：
    weighted_score 写 7.07（实算 6.99）、对抗评分员的 fail 判定整段丢失。

    不检查磁盘上的 generated_by 字段——那个字段可以伪造。
    直接让脚本重算并比对，重算结果伪造不了。
    """
    import os
    import subprocess

    script = Path(__file__).resolve().parent / "aggregate_scores.py"
    if not script.exists():
        return G.fail("聚合评分卡", "core/tools/aggregate_scores.py 缺失", hard=False)

    env = dict(os.environ, PYTHONIOENCODING="utf-8")  # 子进程输出中文，避免 cp936 解码炸
    try:
        r = subprocess.run(
            [sys.executable or "python", str(script),
             str(G.project_dir(project)), "--verify"],
            cwd=str(G.ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", env=env, timeout=120)
    except subprocess.TimeoutExpired:
        return G.fail("聚合评分卡", "aggregate_scores.py --verify 超时(120s)")

    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        fails = [ln.strip().removeprefix("[FAIL]").strip()
                 for ln in out.splitlines() if "[FAIL]" in ln]
        if fails:
            detail = f"{len(fails)} 处与重算不一致: {fails[0]}"
        else:
            # 分卡不全走 EXIT 2，原因打在 stderr 的 [aggregate] 行里
            notes = [ln.strip().removeprefix("[aggregate]").strip()
                     for ln in out.splitlines()
                     if ln.strip() and "[注意]" not in ln]
            detail = notes[-1] if notes else f"--verify EXIT {r.returncode}"
        return G.fail("聚合评分卡", detail)

    line = next((ln.strip().removeprefix("[PASS]").strip()
                 for ln in out.splitlines() if "[PASS]" in ln), "")
    return G.ok("聚合评分卡", line or "与重算一致")


# ---------------------------------------------------------------------------
# 论文版面阈值：复用 validate_project.py 的实现
# ---------------------------------------------------------------------------
# 为什么是复用而不是重写：同一套 env 阈值若在两个脚本里各判一次，
# 判据必然随时间漂移（此前 gate.py 压根不读 min_pages/min_words/min_tables/
# page_fill_ratio，于是一篇 9 页 2738 字的论文拿到「全链路 0 硬失败」，
# 而 validate_project.py 对同一产物报 10 个 HARD）。
#
# VP 的 check 函数不返回值，只向模块级 `results` 追加 (status, name, detail)，
# 故适配器每次调用前快照长度、调完取增量并复位。

_VP_PAPER_CHECKS = [
    "check_paper_pages",        # -> "paper pages"       (env: paper.min_pages)
    "check_page_fill_ratio",    # -> "page fill ratio"   (env: paper.page_fill_ratio)
    "check_paper_words",        # -> "paper words"       (env: paper.min_words)
    "check_paper_tables",       # -> "paper tables"      (env: paper.min_tables)
    "check_paper_figures",      # -> "paper figures"     (env: paper.min_figures)
    "check_paper_equations",    # -> "paper equations"   (env: paper.min_equations)
    "check_paper_references",   # -> "paper references"  (env: paper.min_references)
    "check_pdf_compile_chain",  # -> "pdf compile chain"
]

_VP_INIT_DONE: dict[str, bool] = {}


def _vp_init(VP, project):
    """按 validate_project.main() 的顺序初始化 VP 的三个模块级全局。"""
    key = str(G.project_dir(project))
    if _VP_INIT_DONE.get(key):
        return
    module, _err = VP._load_env_loader(G.ROOT)
    if module is not None:
        VP._ENV_GET = module.get
    VP._STRICT_MODE = bool(VP._ENV_GET("runtime.strict_mode") or True)
    _pt, is_physics = VP._detect_problem_type(G.project_dir(project))
    VP._IS_PHYSICS = is_physics
    _VP_INIT_DONE[key] = True


def _vp_check(project, fname):
    """跑 validate_project 里的单个检查函数，映射为 gatelib.Check。"""
    import validate_project as VP

    fn = getattr(VP, fname, None)
    if fn is None:
        return G.fail(f"版面检查/{fname}", "validate_project 无此检查函数")
    _vp_init(VP, project)

    mark = len(VP.results)
    try:
        fn(G.project_dir(project))
    except Exception as e:  # noqa: BLE001 - 单个检查异常不应中断整条门禁
        del VP.results[mark:]
        return G.fail(f"版面检查/{fname}", f"执行异常: {e}", hard=False)

    new = VP.results[mark:]
    del VP.results[mark:]  # 复位，避免污染下一次调用
    if not new:
        return G.fail(f"版面检查/{fname}", "未产生任何判定", hard=False)

    rank = {VP.HARD: 2, VP.WARN: 1, VP.PASS: 0}
    status, name, detail = max(new, key=lambda t: rank.get(t[0], 0))
    if status == VP.PASS:
        return G.ok(name, detail)
    return G.fail(name, detail, hard=(status == VP.HARD))


def _check_latex_compiles(project):
    """国赛验收（6verity Step7）：LaTeX 真实编译。

    只检查 main.pdf 存在是不够的——必须真实跑 xelatex 确认能编译。
    在 paper/ 目录内编译（跑两遍解决交叉引用），随后验证 PDF 非空。
    """
    import shutil
    import subprocess
    paper = G.project_dir(project) / "paper"
    main = paper / "main.tex"
    if not main.exists():
        return G.fail("LaTeX 编译", "无 paper/main.tex", hard=False)
    xelatex = shutil.which("xelatex") or shutil.which("pdflatex")
    if not xelatex:
        return G.fail("LaTeX 编译", "环境无 xelatex/pdflatex，跳过真实编译", hard=False)
    try:
        for _ in range(2):
            r = subprocess.run(
                [xelatex, "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                cwd=str(paper), capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                tail = (r.stdout or "") + "\n" + (r.stderr or "")
                errs = [ln for ln in tail.splitlines() if ln.startswith("!")]
                return G.fail("LaTeX 编译",
                              f"xelatex 失败: {errs[0][:120] if errs else '未知错误'}")
    except subprocess.TimeoutExpired:
        return G.fail("LaTeX 编译", "编译超时(300s)")
    pdf = paper / "main.pdf"
    if not pdf.exists() or pdf.stat().st_size < 1024:
        return G.fail("LaTeX 编译", "编译后 main.pdf 缺失或为空")
    return G.ok("LaTeX 编译", f"{pdf.stat().st_size // 1024} KB")


def _check_code_runs_lite(project):
    """国赛验收（6verity Step 代码复现）：代码可复现性（轻量）。

    轻量验证：语法编译 code/ 下全部 .py，并确认数值真相源
    figures/all_results.json 可解析且非空。完整重跑由 test-runner 阶段负责。
    """
    import json
    import subprocess
    import sys as _sys
    code_dir = G.project_dir(project) / "code"
    if not code_dir.exists():
        return G.fail("代码可复现", "code/ 目录不存在", hard=False)
    py_files = sorted(code_dir.glob("*.py"))
    if not py_files:
        return G.fail("代码可复现", "code/ 下无 .py 文件", hard=False)
    try:
        r = subprocess.run(
            [_sys.executable, "-m", "py_compile"] + [str(f) for f in py_files],
            capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return G.fail("代码可复现", "语法编译超时")
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip()
        return G.fail("代码可复现", f"语法编译失败: {tail[:160]}")

    ar = G.project_dir(project) / "figures" / "all_results.json"
    if not ar.exists():
        return G.fail("代码可复现", "缺 figures/all_results.json", hard=False)
    try:
        json.loads(ar.read_text(encoding="utf-8"))
    except Exception as e:
        return G.fail("代码可复现", f"all_results.json 解析失败: {e}")
    return G.ok("代码可复现", f"{len(py_files)} 个 .py 语法通过，all_results.json 可解析")


def _check_no_future_refs(project):
    """未来文献检测：年份晚于赛题年份即判 HARD（引用造假信号）。"""
    import re
    bib = G.project_dir(project) / "paper" / "references.bib"
    text = G.read(bib)
    if text is None:
        return G.fail("未来文献", "无法读取 references.bib", hard=False)
    base_year = _infer_year(G.project_dir(project))
    years = [int(y) for y in re.findall(r"year\s*=\s*\{?(\d{4})\}?", text)]
    future = [y for y in years if y > base_year]
    if future:
        return G.fail("未来文献",
                      f"存在年份晚于赛题年 {base_year} 的文献: {sorted(set(future))}")
    return G.ok("未来文献", f"无（基准年 {base_year}）")


def _infer_year(project_path):
    import re
    m = re.search(r"((?:19|20)\d{2})", Path(project_path).name)
    return int(m.group(1)) if m else 2026


# lite 模式下放宽的检查：弱模型的产出在这些问题上不阻塞交付，
# 但仍会提示，避免"弱模型跑不完全流程"。
# 版面阈值 8 项与既有的「LaTeX 编译」「PDF 产物」「插图数」「公式数」同类：
# 名字取自 validate_project.py 里 _pas/_warn/_hard 的首参（1:1 映射）。
# 这是刻意取舍——runtime.profile 默认 standard，硬门禁照常生效；
# lite 仅把"写不满 min_pages（国赛软目标 17 页）"从阻塞降为提示，不重开漏洞。
LITE_SOFTEN = {"公式数(W-env)", "插图数", "PDF 产物", "运行时护栏",
                "Schema core/schemas/question_spec.schema.json",
                "LaTeX 编译", "代码可复现",
                "paper pages", "page fill ratio", "paper words",
                "paper tables", "paper figures", "paper equations",
                "paper references", "pdf compile chain"}


def _profile():
    """读取能力分层（standard / lite）。"""
    try:
        import sys as _s
        _s.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from env.loader import get
        return str(get("runtime.profile", default="standard") or "standard").lower()
    except Exception:
        return "standard"


def _check_inputs_readonly(project):
    """P2-12：原始数据只读。

    赛题与原始数据被意外改写后，所有基于它的分析都失去意义，
    而且很难被发现。这里比对 inputs/ 下文件的哈希与基线。
    """
    import json as _json
    d = G.project_dir(project) / "inputs"
    if not d.exists():
        return G.fail("原始数据存在性", "inputs/ 目录不存在", hard=False)
    base_file = G.project_dir(project) / "work" / "inputs_baseline.json"
    current = {f.name: G.sha256(f.read_bytes()) for f in sorted(d.iterdir()) if f.is_file()}
    if not current:
        return G.fail("原始数据", "inputs/ 为空", hard=False)

    if not base_file.exists():
        base_file.parent.mkdir(parents=True, exist_ok=True)
        base_file.write_text(_json.dumps(current, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")
        return G.ok("原始数据基线", f"已建立基线（{len(current)} 个文件），后续将检测篡改")

    try:
        baseline = _json.loads(base_file.read_text(encoding="utf-8"))
    except Exception:
        return G.fail("原始数据基线", "基线文件损坏", hard=False)

    changed = [k for k, v in current.items() if k in baseline and baseline[k] != v]
    added = [k for k in current if k not in baseline]
    if changed:
        return G.fail("原始数据只读", f"文件已被修改: {', '.join(changed[:5])}")
    if added:
        return G.fail("原始数据只读", f"新增文件（需重新建立基线）: {', '.join(added[:5])}",
                      hard=False)
    return G.ok("原始数据只读", f"{len(current)} 个文件与基线一致")



def run_gate(project, hand, agent, state=None, profile=None):
    key = (hand, agent)
    if key not in GATES:
        print(f"  [SKIP] {hand}/{agent} - 未定义门禁")
        return []
    # 未执行到的步骤不判失败
    if state is not None:
        done = {(c.get("hand"), c.get("agent")) for c in state.get("completed", [])}
        if key not in done:
            exists = any(
                G.project_dir(project).exists()
                for _ in [0]
            ) and _likely_done(project, hand, agent)
            if not exists:
                print(f"  [SKIP] {hand}/{agent} - 尚未执行")
                return []
    prof = profile or _profile()
    results = []
    for fn in GATES[key]:
        try:
            r = fn(project)
        except Exception as e:
            r = G.fail(f"{hand}/{agent} 断言异常", str(e))
        # lite 模式：把软性检查从 HARD 降级为不阻塞，避免弱模型卡死
        if prof == "lite" and (not r.ok) and r.hard and r.name in LITE_SOFTEN:
            r = G.fail(r.name, r.detail + "  [lite 模式：不阻塞]", hard=False)
        results.append(r)
    return results


def _likely_done(project, hand, agent):
    """粗略判断该步是否已产出（用于历史项目没有 state.json 的情况）。"""
    base = G.project_dir(project)
    probe = {
        ("modeler", "problem-parser"): "work/question_spec.json",
        ("modeler", "type-classifier"): "work/type_classification.json",
        ("modeler", "literature-searcher"): "work/literature_evidence.json",
        ("modeler", "method-matcher"): "work/method_candidates.json",
        ("modeler", "model-builder"): "work/model_draft.md",
        ("modeler", "dag-builder"): "work/model_dag.json",
        ("modeler", "assumption-validator"): "work/assumption_validation.json",
        ("modeler", "spec-auditor"): "output/MODEL_SPEC.md",
        ("programmer", "template-selector"): "work/template_plan.json",
        ("programmer", "code-implementer"): "code/main.py",
        ("programmer", "test-runner"): "work/test_report.json",
        ("programmer", "result-verifier"): "work/result_validation.json",
        ("programmer", "guardrails-checker"): "work/guardrails_report_programmer.json",
        ("programmer", "hash-auditor"): "output/CODE_DELIVERABLES.md",
        ("writer", "structure-planner"): "work/paper_structure.json",
        ("writer", "section-writer"): "paper/main.tex",
        ("writer", "figure-generator"): "paper/figures",
        ("writer", "reference-curator"): "paper/references.bib",
        ("writer", "consistency-checker"): "work/consistency_report.json",
        ("writer", "guardrails-checker"): "work/guardrails_report_writer.json",
        ("writer", "final-validator"): "output/PAPER_SPEC.md",
        ("reviewer", "scorer-academic"): "work/score_card_academic.json",
        ("reviewer", "scorer-engineering"): "work/score_card_engineering.json",
        ("reviewer", "scorer-judge"): "work/score_card_judge.json",
        ("reviewer", "scorer-reader"): "work/score_card_reader.json",
        ("reviewer", "scorer-adversarial"): "work/score_card_adversarial.json",
        ("reviewer", "weakness-hunter"): "work/weakness_report.json",
        ("reviewer", "revision-planner"): "work/revision_plan.json",
        ("reviewer", "revision-executor"): "work/execution_report.json",
    }.get((hand, agent))
    return bool(probe) and (base / probe).exists()


# 语义化退出码 —— state.py advance 依赖它决定是否放行推进
EXIT_PASS = 0        # 全部通过
EXIT_SOFT = 1        # 仅软失败（WARN），可推进
EXIT_HARD = 2        # 有硬失败，禁止推进
EXIT_ERROR = 3       # 项目不存在 / 参数错误 / 脚本异常


# 门禁层级：artifact / hand / delivery
GATE_LEVELS = ("artifact", "hand", "delivery")


def main():
    ap = argparse.ArgumentParser(description="门禁判定（跨 runtime 执行协议）")
    ap.add_argument("project", help="项目目录名或路径")
    ap.add_argument("hand", nargs="?", help="modeler / programmer / writer / reviewer / all")
    ap.add_argument("agent", nargs="?", help="agent 名；hand=all/delivery 时省略")
    ap.add_argument("--level", default="artifact",
                    choices=["artifact", "hand", "delivery", "all"],
                    help="门禁层级：artifact(单agent)/hand(整手)/delivery(交付契约)/all(全链路)")
    ap.add_argument("--json", action="store_true",
                    help="输出 JSON 供脚本消费（state.py advance 使用）")
    ap.add_argument("--quiet", action="store_true", help="只输出结论行")
    args = ap.parse_args()

    project = args.project
    base = G.project_dir(project)
    if not base.exists():
        print(f"[gate] 项目不存在: {base}", file=sys.stderr)
        return EXIT_ERROR

    state = S.load(project)

    if not args.json and not args.quiet:
        print("=" * 60)
        print(f"门禁判定: {base.name} [层级: {args.level}]")
        print("=" * 60)

    results = []
    if args.level == "all":
        for hand, agent, _ in S.PIPELINE:
            results += run_gate(project, hand, agent, state)
    elif args.level == "delivery":
        target_hands = [args.hand] if args.hand else list(DELIVERY_GATES.keys())
        for hand in target_hands:
            if hand in DELIVERY_GATES:
                for fn in DELIVERY_GATES[hand]:
                    try:
                        r = fn(project)
                    except Exception as e:
                        r = G.fail(f"{hand}/delivery 断言异常", str(e))
                    results.append(r)
            else:
                print(f"  [SKIP] {hand}/delivery - 未定义交付门禁", file=sys.stderr)
    elif args.level == "hand":
        if not args.hand:
            print("[gate] hand 层级需要指定 hand", file=sys.stderr)
            return EXIT_ERROR
        for hand, agent, _ in S.PIPELINE:
            if hand == args.hand:
                results += run_gate(project, hand, agent, state)
    else:  # artifact
        if not args.hand or not args.agent:
            print("[gate] artifact 层级需要指定 hand 和 agent", file=sys.stderr)
            return EXIT_ERROR
        results += run_gate(project, args.hand, args.agent, state)

    passed = sum(1 for r in results if r.ok)
    hard_fail = [r for r in results if not r.ok and r.hard]
    soft_fail = [r for r in results if not r.ok and not r.hard]

    if args.json:
        print(json.dumps({
            "project": base.name,
            "hand": args.hand,
            "agent": args.agent or "",
            "passed": passed,
            "hard_fail_count": len(hard_fail),
            "soft_fail_count": len(soft_fail),
            "ok": len(hard_fail) == 0,
            "hard_fail": [{"name": r.name, "detail": r.detail} for r in hard_fail],
            "soft_fail": [{"name": r.name, "detail": r.detail} for r in soft_fail],
        }, ensure_ascii=False, indent=2))
        return EXIT_PASS if not hard_fail and not soft_fail else (
            EXIT_HARD if hard_fail else EXIT_SOFT
        )

    if not args.quiet:
        print("-" * 60)
        for r in results:
            print("  " + repr(r))

    print("-" * 60)
    print(f"通过 {passed} / 硬失败 {len(hard_fail)} / 软失败 {len(soft_fail)}")

    if hard_fail:
        print("\n阻塞项（须按 SKILL.md 的 ## Iteration 修正后重跑）:")
        for r in hard_fail:
            print(f"  - {r.name}: {r.detail}")
        print("=" * 60)
        return EXIT_HARD

    if soft_fail:
        print("\n软失败（不阻塞，建议改进）:")
        for r in soft_fail:
            print(f"  - {r.name}: {r.detail}")

    print("=" * 60)
    return EXIT_PASS if not soft_fail else EXIT_SOFT


if __name__ == "__main__":
    sys.exit(main())
