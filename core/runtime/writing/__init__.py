"""Writing 层运行时（V3 P4）。

- director.py: ResearchDirector — 从 Registry + Evidence Graph 提炼研究叙事
- projection.py: PaperProjection — 叙事 + 证据图 → 论文大纲投影
- narrative_critic.py: 叙事一致性批判（PASS/FAIL + findings）
- judge_critic.py: 评委视角终审（PASS/WEAK/FAIL/UNKNOWN + 风险清单）
"""

from .director import Narrative, ResearchDirector, StoryArc
from .judge_critic import JudgeReport, JudgeCritic
from .narrative_critic import NarrativeCritic, NarrativeReport
from .projection import PaperProjection

__all__ = [
    "Narrative", "ResearchDirector", "StoryArc",
    "PaperProjection",
    "NarrativeCritic", "NarrativeReport",
    "JudgeCritic", "JudgeReport",
]
