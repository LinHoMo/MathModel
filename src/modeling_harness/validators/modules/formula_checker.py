"""
L2: Formula Checker - 公式语法检查
检查数学公式的语法正确性
"""
import re
from typing import Optional


class FormulaChecker:
    """L2: 公式语法检查器"""
    
    # 括号匹配
    BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
    OPEN_BRACKETS = set(BRACKET_PAIRS.keys())
    CLOSE_BRACKETS = set(BRACKET_PAIRS.values())
    
    # 允许的数学运算符
    VALID_OPERATORS = {"+", "-", "*", "/", "^", "=", "<", ">", "<=", ">=", "!=", "\\frac", "\\sqrt", "\\sum", "\\int", "\\prod", "\\lim", "\\log", "\\ln", "\\sin", "\\cos", "\\tan", "\\exp"}
    
    # 允许的LaTeX命令
    VALID_LATEX = {"\\frac", "\\sqrt", "\\sum", "\\int", "\\prod", "\\lim", "\\log", "\\ln", "\\sin", "\\cos", "\\tan", "\\exp", "\\alpha", "\\beta", "\\gamma", "\\delta", "\\theta", "\\pi", "\\sigma", "\\mu", "\\lambda", "\\omega", "\\Omega", "\\Sigma", "\\Pi", "\\Delta", "\\nabla", "\\partial", "\\infty", "\\rightarrow", "\\leftarrow", "\\Rightarrow", "\\Leftarrow", "\\leftrightarrow", "\\times", "\\cdot", "\\div", "\\pm", "\\mp", "\\leq", "\\geq", "\\neq", "\\approx", "\\sim", "\\equiv", "\\propto", "\\subset", "\\supset", "\\in", "\\notin", "\\cup", "\\cap", "\\emptyset", "\\mathbb", "\\text", "\\mathrm", "\\mathbf", "\\mathit", "\\begin", "\\end", "\\left", "\\right", "\\Big", "\\bigg", "\\displaystyle", "\\quad", "\\qquad", "\\,\\,", "\\;", "\\!", "\\tag", "\\label", "\\ref", "\\cite"}
    
    def __init__(self):
        self.errors = []
    
    def check(self, formula: str) -> dict:
        """检查公式语法"""
        self.errors = []
        
        # 基本检查
        if not formula or len(formula.strip()) == 0:
            return {"valid": False, "issues": ["公式为空"]}
        
        # 检查括号匹配
        bracket_result = self._check_brackets(formula)
        if not bracket_result["valid"]:
            self.errors.extend(bracket_result["issues"])
        
        # 检查LaTeX语法
        latex_result = self._check_latex(formula)
        if not latex_result["valid"]:
            self.errors.extend(latex_result["issues"])
        
        # 检查常见错误
        common_result = self._check_common_errors(formula)
        if not common_result["valid"]:
            self.errors.extend(common_result["issues"])
        
        return {"valid": len(self.errors) == 0, "issues": self.errors}
    
    def _check_brackets(self, formula: str) -> dict:
        """检查括号匹配"""
        stack = []
        issues = []
        
        for i, char in enumerate(formula):
            if char in self.OPEN_BRACKETS:
                stack.append((char, i))
            elif char in self.CLOSE_BRACKETS:
                if not stack:
                    issues.append(f"位置{i}: 多余的闭括号 '{char}'")
                else:
                    open_char, pos = stack.pop()
                    expected_close = self.BRACKET_PAIRS[open_char]
                    if char != expected_close:
                        issues.append(f"位置{i}: 括号不匹配, 期望 '{expected_close}' 得到 '{char}'")
        
        for char, pos in stack:
            issues.append(f"位置{pos}: 未闭合的开括号 '{char}'")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def _check_latex(self, formula: str) -> dict:
        """检查LaTeX语法"""
        issues = []
        
        # 检查 \\frac 需要两个参数
        frac_pattern = r"\\frac\s*\{[^}]*\}\s*\{[^}]*\}"
        frac_count = len(re.findall(r"\\frac", formula))
        frac_matched = len(re.findall(frac_pattern, formula))
        if frac_count > frac_matched:
            issues.append(f"\\frac 命令参数不完整 (期望2个花括号参数)")
        
        # 检查 \\sqrt 需要参数
        sqrt_count = len(re.findall(r"\\sqrt", formula))
        sqrt_matched = len(re.findall(r"\\sqrt\s*\{[^}]*\}", formula))
        if sqrt_count > sqrt_matched:
            issues.append(f"\\sqrt 命令参数不完整")
        
        # 检查未闭合的花括号
        brace_count = formula.count("{") - formula.count("}")
        if brace_count != 0:
            issues.append(f"花括号不平衡: 多余 {'{' if brace_count > 0 else '}'} {abs(brace_count)} 个")
        
        # 检查 \\begin 和 \\end 配对
        begin_count = len(re.findall(r"\\begin\s*\{[^}]*\}", formula))
        end_count = len(re.findall(r"\\end\s*\{[^}]*\}", formula))
        if begin_count != end_count:
            issues.append(f"\\begin 和 \\end 不配对: {begin_count} vs {end_count}")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def _check_common_errors(self, formula: str) -> dict:
        """检查常见错误"""
        issues = []
        
        # 检查连续运算符
        if re.search(r"[+\-*/^=<>]{2,}", formula):
            # 排除合法的组合如 <=, >=, !=
            if re.search(r"[+\-*/^](?!=)", formula) and not re.search(r"[<>!=]=[<>!=]", formula):
                issues.append("检测到连续运算符，可能缺少操作数")
        
        # 检查空分母
        if "\\frac{}" in formula or "\\frac { }" in formula:
            issues.append("检测到空分母")
        
        # 检查空参数
        if "\\sqrt{}" in formula:
            issues.append("检测到空的平方根参数")
        
        return {"valid": len(issues) == 0, "issues": issues}
    
    def check_formula_list(self, formulas: list) -> dict:
        """检查公式列表"""
        all_issues = []
        for i, formula in enumerate(formulas):
            result = self.check(formula)
            if not result["valid"]:
                all_issues.extend([f"公式{i+1}: {issue}" for issue in result["issues"]])
        
        return {"valid": len(all_issues) == 0, "issues": all_issues}
    
    def extract_formulas(self, text: str) -> list:
        """从文本中提取公式"""
        formulas = []
        
        # 提取 $$...$$ 中的公式
        display_patterns = re.findall(r"\$\$(.*?)\$\$", text, re.DOTALL)
        formulas.extend(display_patterns)
        
        # 提取 $...$ 中的公式
        inline_patterns = re.findall(r"\$(.*?)\$", text)
        formulas.extend(inline_patterns)
        
        # 提取 \begin{equation}...\end{equation} 中的公式
        eq_patterns = re.findall(r"\\begin\{equation\}(.*?)\\end\{equation\}", text, re.DOTALL)
        formulas.extend(eq_patterns)
        
        return formulas


def check_formulas(text: str) -> dict:
    """便捷函数：检查文本中的公式"""
    checker = FormulaChecker()
    formulas = checker.extract_formulas(text)
    return checker.check_formula_list(formulas)
