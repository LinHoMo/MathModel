"""Knowledge 层运行时（V3 P2）。

- cards.py: Method Card / Failure / Pattern 加载 + 契约校验（零依赖，yamlio 解析）
- retriever.py: KnowledgeRetriever 检索 API（输入问题特征，输出排序决策建议包）

内容源: core/knowledge/methods/cards/*.yaml + failures/*.yaml + patterns/*.yaml
契约: core/schemas/v3/knowledge/{method_card,failure,pattern}.schema.json
（loader 按契约必填字段做 fail-closed 校验；JSON Schema 供外部工具消费）
"""

from .cards import CardError, FailureMemory, MethodCard, Pattern, load_knowledge
from .retriever import KnowledgeRetriever, Recommendation

__all__ = [
    "CardError", "FailureMemory", "MethodCard", "Pattern",
    "load_knowledge", "KnowledgeRetriever", "Recommendation",
]
