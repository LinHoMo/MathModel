"""
L5: Runtime Guardrails - 运行时护栏
在LLM输出时实时拦截问题，而非事后检查
"""
import re
import json
from pathlib import Path
from typing import Optional


# === 禁用词列表（与 validate.py 同步）===
FORBIDDEN_WORDS = [
    # 现有 19 词
    "赋能", "抓手", "闭环", "颗粒度", "底层逻辑", "打法", "对齐",
    "倒逼", "复盘", "首先", "其次", "最后", "综上所述", "众所周知",
    "显而易见", "PaperCritic", "Prompt", "作为 AI", "token",
    # 中文套话新增
    "具有重要的理论意义和实践价值", "深入探讨", "创新性地", "值得注意的是",
    "总而言之", "具有重要意义", "实现了良好效果", "具有较高价值", "在当今",
    # 元叙述新增
    "参赛者", "参赛队伍", "我们团队",
    # 英文新增
    "delve", "pivotal", "tapestry", "underscore", "noteworthy",
    "It is worth noting that", "Importantly,", "Notably,",
]

# === 占位符模式（与 validate.py 同步）===
PLACEHOLDER_PATTERNS = [
    r"TODO", r"FIXME", r"TBD", r"__XXX__",
    r"\[待补\]", r"\[TBD\]", r"示例数据", r"模板数据",
    r"PLACEHOLDER", r"XXX", r"这里填写",
    r"待补充", r"待续写", r"这里补", r"待完善",
]

# === 内部路径模式（与 validate.py 同步）===
INTERNAL_PATH_PATTERNS = [
    r"\.py\b", r"\.ipynb\b", r"code/\w+\.py",
    r"/tmp/", r"__pycache__", r"\.pytest_cache",
    # 内部术语泄露扩充
    r"MODEL_SPEC\.md", r"CODE_DELIVERABLES\.md", r"PAPER_SPEC\.md",
    r"all_results\.json", r"RESULTS_REPORT", r"ANALYSIS_MODELING_REPORT",
    r"PROBLEM_ANALYSIS", r"CLAUDE\.md", r"AGENTS\.md",
    r"figures/\S+\.json", r"_tmp/", r"work/",
]

# === AI痕迹模式（与 validate.py 同步）===
AI_TRACE_PATTERNS = [
    r"作为\s*AI", r"由\s*AI\s*生成", r"I\s*am\s*an?\s*AI",
    r"language\s*model", r"我是\s*AI", r"作为一个\s*AI"
]


class GuardrailResult:
    """单个护栏检查结果"""
    def __init__(self, name: str, passed: bool, message: str = "", severity: str = "error"):
        self.name = name
        self.passed = passed
        self.message = message
        self.severity = severity  # error, warning

    def to_dict(self):
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "severity": self.severity
        }


class Guardrails:
    """L5: 运行时护栏引擎"""
    
    def __init__(self):
        self.results = []
    
    def check_forbidden_words(self, text: str) -> GuardrailResult:
        """检查禁用词"""
        found = []
        for word in FORBIDDEN_WORDS:
            if word in text:
                found.append(word)
        
        if found:
            return GuardrailResult(
                "forbidden_words", False,
                f"发现禁用词: {', '.join(found)}",
                "error"
            )
        return GuardrailResult("forbidden_words", True)
    
    def check_placeholders(self, text: str) -> GuardrailResult:
        """检查占位符"""
        found = []
        for pattern in PLACEHOLDER_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found.extend(matches)
        
        if found:
            return GuardrailResult(
                "placeholders", False,
                f"发现占位符: {', '.join(set(found))}",
                "error"
            )
        return GuardrailResult("placeholders", True)
    
    def check_internal_paths(self, text: str) -> GuardrailResult:
        """检查内部文件路径"""
        found = []
        for pattern in INTERNAL_PATH_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                found.extend(matches)
        
        if found:
            return GuardrailResult(
                "internal_paths", False,
                f"发现内部路径: {', '.join(list(set(found))[:3])}",
                "warning"
            )
        return GuardrailResult("internal_paths", True)
    
    def check_ai_traces(self, text: str) -> GuardrailResult:
        """检查AI痕迹"""
        found = []
        for pattern in AI_TRACE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found.extend(matches)
        
        if found:
            return GuardrailResult(
                "ai_traces", False,
                f"发现AI痕迹: {', '.join(set(found)[:3])}",
                "error"
            )
        return GuardrailResult("ai_traces", True)
    
    def check_numeric_reasonableness(self, data: dict, expected_ranges: dict) -> GuardrailResult:
        """检查数值合理性"""
        issues = []
        for key, (lo, hi) in expected_ranges.items():
            if key in data:
                val = data[key]
                if isinstance(val, (int, float)):
                    if val < lo or val > hi:
                        issues.append(f"{key}={val} 不在范围[{lo},{hi}]")
        
        if issues:
            return GuardrailResult(
                "numeric_reasonableness", False,
                "; ".join(issues),
                "warning"
            )
        return GuardrailResult("numeric_reasonableness", True)
    
    def check_citation_integrity(self, text: str, bib_keys: list) -> GuardrailResult:
        """检查引用完整性"""
        cite_pattern = r"\\cite[tp]?\{([^}]+)\}"
        cites = re.findall(cite_pattern, text)
        
        all_keys = []
        for c in cites:
            all_keys.extend([k.strip() for k in c.split(",")])
        
        missing = [k for k in all_keys if k not in bib_keys]
        if missing:
            return GuardrailResult(
                "citation_integrity", False,
                f"引用不存在的key: {', '.join(missing)}",
                "error"
            )
        return GuardrailResult("citation_integrity", True)
    
    def check_figure_refs(self, text: str, figure_files: list) -> GuardrailResult:
        """检查图表引用"""
        include_pattern = r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}"
        refs = re.findall(include_pattern, text)
        
        missing = [r for r in refs if r not in figure_files]
        if missing:
            return GuardrailResult(
                "figure_refs", False,
                f"引用不存在的图片: {', '.join(missing)}",
                "error"
            )
        return GuardrailResult("figure_refs", True)
    
    def check_itemize_in_body(self, text: str) -> GuardrailResult:
        """检查正文是否包含 \begin{itemize} 或 \begin{enumerate}"""
        found_itemize = []
        if re.search(r'\\begin\{itemize\}', text):
            found_itemize.append("itemize")
        if re.search(r'\\begin\{enumerate\}', text):
            found_itemize.append("enumerate")
        
        if found_itemize:
            return GuardrailResult(
                "itemize_in_body", False,
                f"正文发现列表环境: {', '.join(found_itemize)}（学术论文不应使用列表环境）",
                "error"
            )
        return GuardrailResult("itemize_in_body", True)
    
    def check_chinese_numbered_list(self, text: str) -> GuardrailResult:
        """检查正文是否出现全角中文分点式（（1）（2）/（一）（二）/①②③）。

        LaTeX 列表环境由 check_itemize_in_body 拦截，本方法拦截「手写全角编号」这条
        更容易漏掉的 AI 痕迹（套列点模板）。半角 (1) 是公式编号，不拦截；记 WARN。
        """
        found = re.findall(r"（\s*[0-9一二三四五六七八九十]+\s*）|[①②③④⑤⑥⑦⑧⑨⑩]", text)
        uniq = sorted(set(found))
        if uniq:
            return GuardrailResult(
                "chinese_numbered_list", False,
                f"正文出现全角分点式 {len(uniq)} 类（{', '.join(uniq[:6])}）→ 建议改为段落式",
                "warning"
            )
        return GuardrailResult("chinese_numbered_list", True)
    
    def check_figure_as_subject(self, text: str) -> GuardrailResult:
        """检查图表主语句式（≥3次返回 FAIL）"""
        patterns = [
            r"图\d+展示了", r"如图\d+所示", r"由图\d+可知",
            r"从图\d+可以看出", r"图\d+给出了", r"图\d+表明",
            r"表\d+展示了", r"如表\d+所示", r"由表\d+可知",
            r"从表\d+可以看出", r"表\d+给出了", r"表\d+表明",
        ]
        count = 0
        for pat in patterns:
            matches = re.findall(pat, text)
            count += len(matches)
        
        if count >= 3:
            return GuardrailResult(
                "figure_as_subject", False,
                f"图表主语句式出现{count}次（≥3），应改为非主语形式",
                "error"
            )
        return GuardrailResult("figure_as_subject", True)
    
    def check_consecutive_same_openings(self, text: str) -> GuardrailResult:
        """检查连续段落相同句式开头"""
        lines = [l.strip() for l in text.split('\n') if l.strip() and not l.strip().startswith('%')]
        openings = []
        for line in lines:
            # 提取前4个中文字符或前2个英文单词作为开头
            chinese_match = re.match(r'([\u4e00-\u9fff]{4})', line)
            if chinese_match:
                openings.append(chinese_match.group(1))
            else:
                eng_match = re.match(r'([A-Za-z]+(?:\s+[A-Za-z]+)?)', line)
                if eng_match:
                    openings.append(eng_match.group(1))
        
        consecutive_count = 0
        for i in range(1, len(openings)):
            if openings[i] == openings[i-1]:
                consecutive_count += 1
        
        if consecutive_count >= 2:
            return GuardrailResult(
                "consecutive_same_openings", False,
                f"发现{consecutive_count}处连续相同句式开头",
                "warning"
            )
        return GuardrailResult("consecutive_same_openings", True)
    
    def validate_output(self, text: str, context: dict = None) -> list:
        """运行所有护栏检查"""
        self.results = []
        
        # 基础检查
        self.results.append(self.check_forbidden_words(text))
        self.results.append(self.check_placeholders(text))
        self.results.append(self.check_internal_paths(text))
        self.results.append(self.check_ai_traces(text))
        
        # 结构化 AI 痕迹检测
        self.results.append(self.check_itemize_in_body(text))
        self.results.append(self.check_chinese_numbered_list(text))
        self.results.append(self.check_figure_as_subject(text))
        self.results.append(self.check_consecutive_same_openings(text))
        
        # 上下文检查
        if context:
            if "bib_keys" in context:
                self.results.append(self.check_citation_integrity(text, context["bib_keys"]))
            if "figure_files" in context:
                self.results.append(self.check_figure_refs(text, context["figure_files"]))
            if "expected_ranges" in context:
                self.results.append(self.check_numeric_reasonableness(
                    context.get("numeric_data", {}), context["expected_ranges"]
                ))
        
        return self.results
    
    def has_errors(self) -> bool:
        return any(not r.passed and r.severity == "error" for r in self.results)
    
    def summary(self) -> dict:
        return {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "failed": sum(1 for r in self.results if not r.passed),
            "errors": [r.to_dict() for r in self.results if not r.passed and r.severity == "error"],
            "warnings": [r.to_dict() for r in self.results if not r.passed and r.severity == "warning"]
        }


def guardrail_check(text: str, context: dict = None) -> dict:
    """便捷函数：运行护栏检查"""
    g = Guardrails()
    g.validate_output(text, context)
    return g.summary()
