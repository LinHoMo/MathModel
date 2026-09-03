#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学术诚信门控

7 类阻断式检查：
1. 文本相似度（Turnitin式 n-gram，阈值 15%）
2. 数据造假特征（Benford/分布异常/过度拟合）
3. 引用闭合性（所有 \citep{} 在 bib 中、年份≤赛题年份、无未来文献）
4. AI 写作比例（检测 8 类痕迹，占比 >30% 阻断）
5. 匿名违规（作者/学校/导师/致谢/文件属性）
6. 数值唯一事实源（所有数字可追溯 all_results.json）
7. 占位符/禁用词/内部路径残留
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from core.env.loader import get


class IntegrityGate:
    """学术诚信门控检查器"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.paper_path = self.project_path / "paper" / "main.tex"
        self.bib_path = self.project_path / "paper" / "references.bib"
        self.results_path = self.project_path / "figures" / "all_results.json"
        self.contest_year = self._infer_contest_year()
        self.issues: List[Dict] = []
    
    def _infer_contest_year(self) -> int:
        """从项目目录名或论文中推断赛题年份"""
        # 尝试从项目目录名推断
        name = self.project_path.name
        match = re.search(r'(20\d{2})', name)
        if match:
            return int(match.group(1))
        # 默认当年
        from datetime import datetime
        return datetime.now().year
    
    def check_all(self) -> Tuple[bool, List[Dict]]:
        """运行所有检查，返回 (是否通过, 问题列表)"""
        self.issues = []
        
        # 1. 文本相似度
        self._check_text_similarity()
        
        # 2. 数据造假特征
        self._check_data_fabrication()
        
        # 3. 引用闭合性
        self._check_citation_integrity()
        
        # 4. AI 写作比例
        self._check_ai_writing_ratio()
        
        # 5. 匿名违规
        self._check_anonymity()
        
        # 6. 数值唯一事实源
        self._check_numeric_traceability()
        
        # 7. 占位符/禁用词/内部路径
        self._check_placeholders_and_forbidden()
        
        # 分类问题
        blocking = [i for i in self.issues if i["severity"] == "block"]
        warnings = [i for i in self.issues if i["severity"] == "warn"]
        
        return len(blocking) == 0, self.issues
    
    def _read_text(self, path: Path) -> str:
        """读取文件文本"""
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""
    
    def _check_text_similarity(self):
        """检查 1: 文本相似度（简化版：检查常见模板句式过度使用）"""
        text = self._read_text(self.paper_path)
        if not text:
            return
        
        # 移除 LaTeX 命令、注释、数学环境
        clean = re.sub(r'%.*', '', text)
        clean = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', clean)
        clean = re.sub(r'\\[a-zA-Z]+', '', clean)
        clean = re.sub(r'\$.*?\$', '', clean)
        clean = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', '', clean, flags=re.DOTALL)
        clean = re.sub(r'[{}]', '', clean)
        
        # 分句
        sentences = [s.strip() for s in re.split(r'[。！？.!?]', clean) if len(s.strip()) > 10]
        
        # 检查重复句子（简单 n-gram 近似）
        seen = set()
        duplicates = 0
        for sent in sentences:
            # 简化：取前 20 字符作为指纹
            fp = sent[:20]
            if fp in seen:
                duplicates += 1
            seen.add(fp)
        
        if duplicates > 0:
            ratio = duplicates / max(len(sentences), 1)
            if ratio > 0.15:  # 15% 阈值
                self.issues.append({
                    "check": "text_similarity",
                    "severity": "block",
                    "message": f"文本重复句子比例 {ratio:.1%} > 15%，疑似抄袭或模板套用",
                    "evidence": f"重复句子数: {duplicates}/{len(sentences)}"
                })
    
    def _check_data_fabrication(self):
        """检查 2: 数据造假特征（Benford 律、分布异常）"""
        if not self.results_path.exists():
            return
        
        try:
            results = json.loads(self.results_path.read_text(encoding="utf-8"))
        except Exception:
            return
        
        # 提取所有数值
        numbers = []
        def extract_numbers(obj):
            if isinstance(obj, (int, float)):
                numbers.append(float(obj))
            elif isinstance(obj, dict):
                for v in obj.values():
                    extract_numbers(v)
            elif isinstance(obj, list):
                for v in obj:
                    extract_numbers(v)
        
        extract_numbers(results)
        
        if len(numbers) < 10:
            return  # 样本太小
        
        # Benford 律检查（首位数字分布）
        first_digits = [int(str(abs(n)).replace('.', '')[0]) for n in numbers if n != 0]
        if first_digits:
            digit_counts = Counter(first_digits)
            total = len(first_digits)
            benford_expected = {d: total * (math.log10(1 + 1/d)) for d in range(1, 10)}
            chi2 = sum((digit_counts.get(d, 0) - benford_expected[d])**2 / benford_expected[d] for d in range(1, 10))
            # 简化阈值：卡方统计量过大提示
            if chi2 > 20:  # 经验阈值
                self.issues.append({
                    "check": "benford_law",
                    "severity": "warn",
                    "message": f"数值首位数字分布偏离 Benford 律 (χ²={chi2:.1f})，疑似数据造假",
                    "evidence": f"数值样本数: {total}"
                })
        
        # 过度拟合检查：结果过于"完美"（如相关系数 > 0.999）
        for key, val in results.items():
            if isinstance(val, dict) and "r2" in val:
                if val["r2"] > 0.999:
                    self.issues.append({
                        "check": "overfitting",
                        "severity": "warn",
                        "message": f"结果 {key} R²={val['r2']:.4f} 过高，疑似过度拟合",
                        "evidence": f"R²={val['r2']}"
                    })
    
    def _check_citation_integrity(self):
        """检查 3: 引用闭合性"""
        text = self._read_text(self.paper_path)
        bib_text = self._read_text(self.bib_path)
        
        if not text:
            return
        
        # 提取所有 \citep{} 引用
        cite_keys = re.findall(r'\\citep\{([^}]+)\}', text)
        # 展开逗号分隔
        all_keys = []
        for k in cite_keys:
            all_keys.extend([x.strip() for k in k.split(',') for x in k.split(',')])
            # 修正：上面有 bug，重写
        all_keys = []
        for k in cite_keys:
            all_keys.extend([x.strip() for x in k.split(',')])
        
        # 检查 bib 中是否存在
        missing_keys = []
        for key in set(all_keys):
            if key and f"@{{{key}," not in bib_text and f"@{key}," not in bib_text:
                missing_keys.append(key)
        
        if missing_keys:
            self.issues.append({
                "check": "citation_missing",
                "severity": "block",
                "message": f"引用键在 references.bib 中不存在: {missing_keys[:10]}",
                "evidence": f"共 {len(missing_keys)} 个缺失 key"
            })
        
        # 检查未来文献（年份 > 赛题年份）
        future_refs = []
        year_pattern = re.compile(r'year\s*=\s*\{?(\d{4})}?')
        for match in year_pattern.finditer(bib_text):
            year = int(match.group(1))
            if year > self.contest_year:
                future_refs.append(year)
        
        if future_refs:
            self.issues.append({
                "check": "future_citation",
                "severity": "block",
                "message": f"存在未来文献 (年份 > {self.contest_year}): {future_refs[:10]}",
                "evidence": f"共 {len(future_refs)} 篇未来文献"
            })
    
    def _check_ai_writing_ratio(self):
        """检查 4: AI 写作比例（8 类痕迹）"""
        text = self._read_text(self.paper_path)
        if not text:
            return
        
        # 8 类 AI 痕迹词汇
        ai_patterns = [
            r'首先[，,].*其次[，,].*最后',  # 机械模板
            r'综上所述',
            r'值得注意的是',
            r'至关重要',
            r'赋能',
            r'抓手',
            r'闭环',
            r'底层逻辑',
            r'颗粒度',
        ]
        
        total_chars = len(text)
        ai_chars = 0
        for pattern in ai_patterns:
            matches = list(re.finditer(pattern, text))
            ai_chars += sum(len(m.group()) for m in matches)
        
        ratio = ai_chars / max(total_chars, 1)
        if ratio > 0.30:  # 30% 阈值
            self.issues.append({
                "check": "ai_writing_ratio",
                "severity": "block",
                "message": f"AI 写作痕迹占比 {ratio:.1%} > 30%，疑似大量 AI 生成",
                "evidence": f"AI 特征字符: {ai_chars}/{total_chars}"
            })
    
    def _check_anonymity(self):
        """检查 5: 匿名违规"""
        text = self._read_text(self.paper_path)
        if not text:
            return
        
        # 常见匿名违规模式
        patterns = [
            (r'作者[:：]\s*\S+', "作者信息"),
            (r'学校[:：]\s*\S+', "学校信息"),
            (r'导师[:：]\s*\S+', "导师信息"),
            (r'致谢.*[导师老师同学]', "致谢泄露身份"),
            (r'[Cc]hina', "可能泄露国家"),
            (r'[Uu]niversity', "可能泄露学校"),
        ]
        
        violations = []
        for pattern, desc in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(desc)
        
        if violations:
            self.issues.append({
                "check": "anonymity",
                "severity": "block",
                "message": f"匿名违规: {', '.join(violations)}",
                "evidence": "正文中检测到身份信息"
            })
    
    def _check_numeric_traceability(self):
        """检查 6: 数值唯一事实源"""
        if not self.results_path.exists():
            self.issues.append({
                "check": "numeric_traceability",
                "severity": "block",
                "message": "figures/all_results.json 不存在，无法追溯数值",
                "evidence": "缺少数值账本"
            })
            return
        
        try:
            results = json.loads(self.results_path.read_text(encoding="utf-8"))
        except Exception:
            self.issues.append({
                "check": "numeric_traceability",
                "severity": "block",
                "message": "all_results.json 格式错误",
                "evidence": "JSON 解析失败"
            })
            return
        
        text = self._read_text(self.paper_path)
        if not text:
            return
        
        # 提取论文中的数值（简单正则）
        paper_numbers = re.findall(r'\b\d+\.?\d*\b', text)
        # 只检查有物理意义的数值（>0.01 且 < 1e6）
        paper_numbers = [float(n) for n in paper_numbers if 0.01 <= float(n) <= 1e6]
        
        # 从 results 中提取所有数值
        result_numbers = []
        def extract(obj):
            if isinstance(obj, (int, float)):
                result_numbers.append(float(obj))
            elif isinstance(obj, dict):
                for v in obj.values():
                    extract(v)
            elif isinstance(obj, list):
                for v in obj:
                    extract(v)
        extract(results)
        
        # 检查每个论文数值在 results 中是否有对应（容差 1%）
        untraceable = 0
        for pn in paper_numbers:
            found = any(abs(pn - rn) / max(abs(rn), 1e-9) < 0.01 for rn in result_numbers)
            if not found:
                untraceable += 1
        
        if paper_numbers:
            ratio = untraceable / len(paper_numbers)
            if ratio > 0.10:  # 10% 不可追溯阈值
                self.issues.append({
                    "check": "numeric_traceability",
                    "severity": "block",
                    "message": f"数值不可追溯比例 {ratio:.1%} > 10%",
                    "evidence": f"不可追溯: {untraceable}/{len(paper_numbers)}"
                })
    
    def _check_placeholders_and_forbidden(self):
        """检查 7: 占位符/禁用词/内部路径"""
        text = self._read_text(self.paper_path)
        if not text:
            return
        
        # 占位符
        placeholders = ['TODO', 'FIXME', 'TBD', '待补充', '此处插入', '示例数值', '张三', '李四']
        found_ph = [ph for ph in placeholders if ph in text]
        
        # 禁用词（从 forbidden-words.md 读取或内置）
        forbidden = ['综上所述', '值得注意的是', '至关重要', '赋能', '抓手', '闭环', '底层逻辑', '颗粒度']
        found_fw = [fw for fw in forbidden if fw in text]
        
        # 内部路径
        internal_paths = re.findall(r'[A-Za-z]:[\\/][^<\s]+\.(py|txt|csv|json|md)', text)
        internal_paths += re.findall(r'/[a-zA-Z0-9_/.-]+\.(py|txt|csv|json|md)', text)
        
        issues = []
        if found_ph:
            issues.append(f"占位符: {found_ph}")
        if found_fw:
            issues.append(f"禁用词: {found_fw}")
        if internal_paths:
            issues.append(f"内部路径: {internal_paths[:5]}")
        
        if issues:
            self.issues.append({
                "check": "placeholders_forbidden",
                "severity": "block",
                "message": "发现占位符/禁用词/内部路径: " + "; ".join(issues),
                "evidence": str(issues)
            })


import math  # 用于 Benford 律

def main():
    if len(sys.argv) < 2:
        print("用法: python integrity_gate.py <项目路径>")
        sys.exit(1)
    
    project_path = Path(sys.argv[1])
    gate = IntegrityGate(project_path)
    passed, issues = gate.check_all()
    
    print(f"\n=== 学术诚信门控检查报告 ===")
    print(f"项目: {project_path.name}")
    print(f"赛题年份: {gate.contest_year}")
    print(f"总检查项: 7")
    print(f"问题总数: {len(issues)}")
    
    for issue in issues:
        sev = "🔴 阻断" if issue["severity"] == "block" else "🟡 警告"
        print(f"\n{sev} [{issue['check']}]")
        print(f"  {issue['message']}")
        print(f"  证据: {issue['evidence']}")
    
    blocking_count = len([i for i in issues if i["severity"] == "block"])
    print(f"\n阻断级问题: {blocking_count}")
    print(f"结果: {'✅ 通过' if passed else '❌ 不通过'}")
    
    # 输出 JSON 供脚本消费
    output = {
        "passed": passed,
        "blocking_count": blocking_count,
        "issues": issues
    }
    print(f"\n---JSON---")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()