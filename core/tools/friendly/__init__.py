#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Friendly Mode 交互包装器

为所有 agent 提供统一的问答式交互界面：
- 关键决策点以编号选项呈现
- 每个问题提供 "让我决定 (推荐 X)" 兜底选项
- 自动记录决策到 decision_log.json
- 支持专家模式跳过交互

用法：
    from core.tools.friendly import FriendlyInteraction
    
    fi = FriendlyInteraction(project="cumcm2024a", stage="modeler/type-classifier", agent="type-classifier")
    choice = fi.ask("赛题属于哪种题型？", 
                    ["A: 物理机理", "B: 实验数据", "C: 数据驱动", "D: 运筹优化", "E: 跨学科综合"],
                    recommended=1,
                    decision_type="model_selection")
"""

import sys
import json
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Any

# 添加项目根目录到路径
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from core.env.loader import get
from core.tools.state import _now, decision_log_path, load_decision_log, save_decision_log


class FriendlyInteraction:
    """友好模式交互器"""
    
    def __init__(self, project: str, stage: str, agent: str, expert_mode: bool = False):
        self.project = project
        self.stage = stage
        self.agent = agent
        self.expert_mode = expert_mode or not get("runtime.friendly_mode", default=True)
    
    def ask(self, 
            question: str, 
            options: List[str], 
            recommended: int = 1,
            decision_type: str = "other",
            allow_free_text: bool = False) -> str:
        """
        发起一个友好模式提问
        
        Args:
            question: 问题文本
            options: 选项列表（不含兜底选项，会自动添加）
            recommended: 推荐选项编号（1-based）
            decision_type: 决策类型
            allow_free_text: 是否允许自由文本输入
            
        Returns:
            用户选择的选项文本
        """
        if self.expert_mode:
            # 专家模式：直接返回推荐选项
            choice = options[recommended - 1] if 1 <= recommended <= len(options) else options[0]
            self._record_decision(question, options, choice, f"专家模式自动选择 (推荐 {recommended})", 1.0, [])
            return choice
        
        # 构建显示选项（添加兜底选项）
        display_options = options.copy()
        fallback_label = f"让我决定 (推荐 {recommended})"
        display_options.append(fallback_label)
        
        # 显示问题
        print(f"\n{'='*60}")
        print(f"🤔 {question}")
        print(f"{'='*60}")
        for i, opt in enumerate(display_options, 1):
            prefix = "▶" if i == recommended else " "
            print(f"  {prefix} {i}. {opt}")
        print(f"{'='*60}")
        
        # 获取用户输入
        while True:
            try:
                if allow_free_text:
                    prompt = f"请输入数字 (1-{len(display_options)}) 或直接输入文本: "
                else:
                    prompt = f"请输入数字 (1-{len(display_options)}): "
                
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                # 尝试解析为数字
                try:
                    choice_idx = int(user_input) - 1
                    if 0 <= choice_idx < len(display_options):
                        choice = display_options[choice_idx]
                        confidence = 1.0 if choice_idx == recommended - 1 else 0.8
                        break
                    else:
                        print(f"❌ 请输入 1-{len(display_options)} 之间的数字")
                        continue
                except ValueError:
                    # 非数字输入
                    if allow_free_text:
                        choice = user_input
                        confidence = 0.7
                        break
                    else:
                        print("❌ 请输入数字选项")
                        continue
                        
            except (EOFError, KeyboardInterrupt):
                print("\n⚠️  用户中断，使用推荐选项")
                choice = display_options[recommended - 1]
                confidence = 0.6
                break
        
        # 记录决策
        rationale = "用户选择" if not self.expert_mode else "专家模式自动选择"
        if choice == fallback_label:
            rationale += f" (采纳推荐 {recommended})"
        
        alternatives = [opt for i, opt in enumerate(options, 1) if i != recommended]
        self._record_decision(question, options, choice, rationale, confidence, alternatives)
        
        print(f"✅ 已选择: {choice}")
        return choice
    
    def ask_yes_no(self, question: str, recommended_yes: bool = True, decision_type: str = "other") -> bool:
        """是/否 确认对话框"""
        options = ["是", "否"]
        recommended = 1 if recommended_yes else 2
        choice = self.ask(question, options, recommended, decision_type)
        return choice == "是"
    
    def ask_multiple(self, question: str, options: List[str], max_choices: int = 3, 
                     recommended: List[int] = None, decision_type: str = "other") -> List[str]:
        """多选对话框"""
        if self.expert_mode:
            rec = recommended or [1]
            choices = [options[i-1] for i in rec if 1 <= i <= len(options)]
            self._record_decision(question, options, ", ".join(choices), "专家模式自动选择", 1.0, [])
            return choices
        
        print(f"\n{'='*60}")
        print(f"🤔 {question} (可多选，最多 {max_choices} 项)")
        print(f"{'='*60}")
        for i, opt in enumerate(options, 1):
            rec_mark = " ★" if recommended and i in recommended else ""
            print(f"  {i}. {opt}{rec_mark}")
        print(f"{'='*60}")
        
        while True:
            try:
                user_input = input(f"请输入数字，用空格分隔 (如: 1 3), 最多 {max_choices} 项: ").strip()
                if not user_input:
                    continue
                
                try:
                    indices = [int(x) - 1 for x in user_input.split()]
                    if all(0 <= i < len(options) for i in indices) and 1 <= len(indices) <= max_choices:
                        choices = [options[i] for i in indices]
                        confidence = 1.0 if recommended and set(indices) == set([r-1 for r in recommended]) else 0.8
                        break
                    else:
                        print(f"❌ 请输入 1-{len(options)} 之间的数字，共 {len(indices)} 项 (限制 1-{max_choices})")
                        continue
                except ValueError:
                    print("❌ 请输入数字，用空格分隔")
                    continue
            except (EOFError, KeyboardInterrupt):
                rec = recommended or [1]
                choices = [options[i-1] for i in rec if 1 <= i <= len(options)]
                confidence = 0.6
                break
        
        rationale = f"用户多选: {', '.join(choices)}"
        all_opts = [opt for i, opt in enumerate(options, 1) if i not in [idx+1 for idx in indices]]
        self._record_decision(question, options, ", ".join(choices), rationale, confidence, all_opts)
        
        print(f"✅ 已选择: {', '.join(choices)}")
        return choices
    
    def _record_decision(self, question: str, options: List[str], choice: str, 
                         rationale: str, confidence: float, alternatives: List[str]):
        """记录决策到 decision_log.json"""
        log = load_decision_log(self.project)
        
        entry = {
            "timestamp": _now(),
            "stage": self.stage,
            "agent": self.agent,
            "decision_type": decision_type,
            "question": question,
            "options": [{"label": opt, "description": ""} for opt in options],
            "choice": choice,
            "rationale": rationale,
            "confidence": confidence,
            "alternatives_considered": alternatives,
            "time_spent_seconds": 0,  # 可扩展为实际计时
        }
        
        log["entries"].append(entry)
        save_decision_log(self.project, log)


def friendly_ask(project: str, stage: str, agent: str, question: str, 
                 options: List[str], recommended: int = 1, 
                 decision_type: str = "other", expert_mode: bool = False) -> str:
    """便捷函数：单次友好提问"""
    fi = FriendlyInteraction(project, stage, agent, expert_mode)
    return fi.ask(question, options, recommended, decision_type)


def friendly_yes_no(project: str, stage: str, agent: str, question: str, 
                    recommended_yes: bool = True, decision_type: str = "other",
                    expert_mode: bool = False) -> bool:
    """便捷函数：是/否 确认"""
    fi = FriendlyInteraction(project, stage, agent, expert_mode)
    return fi.ask_yes_no(question, recommended_yes, decision_type)


def friendly_multiple(project: str, stage: str, agent: str, question: str,
                      options: List[str], max_choices: int = 3,
                      recommended: List[int] = None, decision_type: str = "other",
                      expert_mode: bool = False) -> List[str]:
    """便捷函数：多选"""
    fi = FriendlyInteraction(project, stage, agent, expert_mode)
    return fi.ask_multiple(question, options, max_choices, recommended, decision_type)


# ==================== Agent 集成示例 ====================

class AgentDecisionMixin:
    """Agent 决策混入类，供各 agent 集成友好模式"""
    
    def __init__(self, project: str, agent_name: str):
        self.project = project
        self.agent_name = agent_name
        self.friendly = FriendlyInteraction(project, f"{self._hand}/{agent_name}", agent_name)
    
    @property
    def _hand(self) -> str:
        """子类重写"""
        return "modeler"
    
    def decide_model_selection(self, question: str, candidates: List[dict], recommended: int = 1) -> dict:
        """模型选择决策"""
        options = [f"{c['name']}: {c['desc']}" for c in candidates]
        choice_text = self.friendly.ask(question, options, recommended, "model_selection")
        # 解析选择对应的候选
        idx = options.index(choice_text) if choice_text in options else recommended - 1
        return candidates[idx]
    
    def decide_verdict(self, score_card: dict, weaknesses: List[dict]) -> str:
        """评审裁决决策"""
        options = ["pass: 全部达标", "pass_with_review: 达标但有建议", 
                   "refine_partial: 仅个别子问不达标", "refine: 整体需修改", "block: 存在阻塞级缺陷"]
        # 根据分数推荐
        avg_score = score_card.get("weighted_avg", 0)
        min_score = score_card.get("min_dimension_score", 0)
        
        if avg_score >= 8 and min_score >= 6:
            recommended = 1
        elif avg_score >= 6 and min_score >= 5:
            recommended = 2
        elif min_score < 5:
            recommended = 4
        else:
            recommended = 3
        
        choice_text = self.friendly.ask("根据评分卡与缺陷报告，选择裁决：", options, recommended, "verdict")
        return choice_text.split(":")[0].strip()
    
    def decide_refine_scope(self, weak_questions: List[str]) -> List[str]:
        """决定修改范围（Per-Qi 差异化降级）"""
        if not weak_questions:
            return []
        
        options = [f"仅修改 {q}" for q in weak_questions] + [f"修改全部 ({', '.join(weak_questions)})"]
        recommended = len(weak_questions) + 1  # 默认推荐全部修改
        
        choice_text = self.friendly.ask("选择修改范围（Per-Qi 差异化）：", options, recommended, "refine")
        
        if "全部" in choice_text:
            return weak_questions
        else:
            # 解析单个子问
            for q in weak_questions:
                if q in choice_text:
                    return [q]
            return weak_questions[:1]


if __name__ == "__main__":
    # 测试
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_project = Path(tmpdir) / "test_proj"
        test_project.mkdir()
        (test_project / "work").mkdir()
        
        # 模拟 state.py 的 decision_log 功能
        sys.path.insert(0, str(ROOT))
        from core.tools.state import _now
        
        # 这里仅演示接口，不实际运行交互
        print("FriendlyInteraction 类已就绪")
        print("集成方式：")
        print("  from core.tools.friendly import FriendlyInteraction")
        print("  fi = FriendlyInteraction(project, stage, agent)")
        print("  choice = fi.ask(question, options, recommended=1)")