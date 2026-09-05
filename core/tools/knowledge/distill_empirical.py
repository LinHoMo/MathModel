#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Empirical Distillation Pipeline
从获奖论文 PDF 蒸馏实测分位统计，生成 empirical.json

用法：
    python core/tools/distill_empirical.py --input-dir /path/to/papers --output core/knowledge/empirical/cumcm-empirical.json
    python core/tools/distill_empirical.py --from-index core/knowledge/paper-cases/INDEX.md --output core/knowledge/empirical/cumcm-empirical.json
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import statistics

# 尝试导入 PDF 解析库
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False


def extract_text_from_pdf(pdf_path: Path) -> str:
    """从 PDF 提取文本"""
    text = ""
    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
            return text
        except Exception as e:
            print(f"[warn] pdfplumber 失败 {pdf_path}: {e}", file=sys.stderr)
    
    if HAS_PYPDF2:
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
            return text
        except Exception as e:
            print(f"[warn] PyPDF2 失败 {pdf_path}: {e}", file=sys.stderr)
    
    return ""


def count_chinese_words(text: str) -> int:
    """统计中文字符数（近似词数）"""
    # 去除 LaTeX 命令、注释、数学环境
    text = re.sub(r'%.*', '', text)  # 注释
    text = re.sub(r'\\[a-zA-Z]+\{.*?\}', '', text)  # \cmd{...}
    text = re.sub(r'\\[a-zA-Z]+', '', text)  # \cmd
    text = re.sub(r'\$.*?\$', '', text)  # 行内数学
    text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', '', text, flags=re.DOTALL)  # 环境
    text = re.sub(r'[{}]', '', text)
    # 统计中文字符
    chinese = re.findall(r'[\u4e00-\u9fff]', text)
    return len(chinese)


def count_english_words(text: str) -> int:
    """统计英文单词数"""
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    return len(words)


def count_figures(text: str) -> int:
    """统计图表数"""
    # 匹配 \includegraphics, \begin{figure}, \begin{table}
    figs = len(re.findall(r'\\includegraphics', text, re.IGNORECASE))
    figs += len(re.findall(r'\\begin\{figure\}', text, re.IGNORECASE))
    figs += len(re.findall(r'\\begin\{table\}', text, re.IGNORECASE))
    return figs


def count_tables(text: str) -> int:
    """统计表格数"""
    return len(re.findall(r'\\begin\{table\}', text, re.IGNORECASE))


def count_equations(text: str) -> int:
    """统计公式数（编号公式）"""
    return len(re.findall(r'\\begin\{(equation|align|gather|multline)\}', text, re.IGNORECASE))


def count_references(text: str) -> int:
    """统计参考文献数"""
    # 统计 bib 条目或 \bibitem
    return len(re.findall(r'\\bibitem|@\w+\{', text))


def estimate_pages(text: str, chars_per_page: int = 800) -> int:
    """估算页数"""
    total_chars = count_chinese_words(text) + count_english_words(text) * 2
    return max(1, total_chars // chars_per_page)


def extract_abstract(text: str) -> str:
    """提取摘要"""
    # 尝试找 \begin{abstract} ... \end{abstract}
    match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # 尝试中文摘要
    match = re.search(r'摘\s*要[:：](.*?)(?:\n\s*\n|关键词|关键字)', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def analyze_paper(text: str, filename: str) -> Dict[str, Any]:
    """分析单篇论文，返回指标"""
    metrics = {
        "filename": filename,
        "body_words": count_chinese_words(text) + count_english_words(text) * 2,
        "body_pages": estimate_pages(text),
        "figure_count": count_figures(text),
        "table_count": count_tables(text),
        "equation_count": count_equations(text),
        "reference_count": count_references(text),
        "abstract_words": count_chinese_words(extract_abstract(text)) + count_english_words(extract_abstract(text)) * 2,
    }
    # 灵敏度深度、创新标签、模型复杂度需要更复杂的 NLP，这里先置 0
    metrics["sensitivity_depth"] = 0
    metrics["innovation_tags"] = 0
    metrics["model_complexity"] = 0
    metrics["code_lines"] = 0
    return metrics


def compute_percentiles(values: List[float]) -> Dict[str, float]:
    """计算 p25, p50, p75"""
    if not values:
        return {"p25": 0, "p50": 0, "p75": 0}
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    return {
        "p25": sorted_vals[int(n * 0.25)] if n > 3 else sorted_vals[0],
        "p50": sorted_vals[int(n * 0.50)] if n > 1 else sorted_vals[0],
        "p75": sorted_vals[int(n * 0.75)] if n > 3 else sorted_vals[-1],
    }


def main():
    ap = argparse.ArgumentParser(description="蒸馏获奖论文实测分位")
    ap.add_argument("--input-dir", help="论文 PDF 目录")
    ap.add_argument("--from-index", help="从 INDEX.md 读取论文列表")
    ap.add_argument("--output", required=True, help="输出 empirical.json 路径")
    ap.add_argument("--competition", default="cumcm", choices=["cumcm", "mcm", "diangong"], help="竞赛类型")
    args = ap.parse_args()

    papers = []

    if args.input_dir:
        pdf_dir = Path(args.input_dir)
        if not pdf_dir.exists():
            print(f"[error] 目录不存在: {pdf_dir}", file=sys.stderr)
            return 1
        for pdf_file in pdf_dir.rglob("*.pdf"):
            print(f"[info] 处理: {pdf_file.name}")
            text = extract_text_from_pdf(pdf_file)
            if text:
                metrics = analyze_paper(text, pdf_file.name)
                papers.append(metrics)
            else:
                print(f"[warn] 无法提取文本: {pdf_file.name}")

    elif args.from_index:
        # 从 INDEX.md 读取论文元数据（不提取全文，仅用于生成模板）
        print(f"[info] 从 INDEX 生成模板: {args.from_index}")
        # 这里仅生成模板结构，实际分位需人工填入或后续跑 PDF 提取
        pass

    if not papers:
        print("[warn] 无有效论文数据，生成空模板", file=sys.stderr)
        papers = []

    # 计算整体分位
    all_metrics = {}
    for key in ["body_words", "body_pages", "figure_count", "table_count", 
                "equation_count", "reference_count", "abstract_words",
                "sensitivity_depth", "innovation_tags", "model_complexity", "code_lines"]:
        vals = [p.get(key, 0) for p in papers]
        all_metrics[key] = compute_percentiles(vals)

    # 构建输出
    output = {
        "schema_version": "1.0",
        "description": f"{args.competition.upper()} 获奖论文实测分位统计",
        "source": {
            "papers_collected": len(papers),
            "years": [2023, 2024, 2025],
            "sources": [],
            "distillation_date": datetime.now().strftime("%Y-%m-%d"),
            "note": "仅统计量，不存储全文内容"
        },
        "metrics": {},
        "by_topic": {},
        "award_level": {}
    }

    # 填充 metrics
    for key, percentiles in all_metrics.items():
        # 确定单位
        unit_map = {
            "body_words": "chars", "body_pages": "pages", "figure_count": "count",
            "table_count": "count", "equation_count": "count", "reference_count": "count",
            "abstract_words": "chars", "sensitivity_depth": "score",
            "innovation_tags": "count", "model_complexity": "score", "code_lines": "lines"
        }
        output["metrics"][key] = {
            "description": key,
            "p25": percentiles["p25"],
            "p50": percentiles["p50"],
            "p75": percentiles["p75"],
            "unit": unit_map.get(key, "")
        }

    # 按题型/奖项分组（需要元数据，这里仅占位）
    output["by_topic"] = {}
    output["award_level"] = {}

    # 写入
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[done] 已生成: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())