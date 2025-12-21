"""Research Squad - Multi-Agent System with LangGraph

A demonstration of multi-agent orchestration for B2B research.
"""

from .graph import (
    research_squad,
    create_research_squad_graph,
    create_research_squad_graph_with_human_review,
)
from .state import ResearchState

__all__ = [
    "research_squad",
    "create_research_squad_graph",
    "create_research_squad_graph_with_human_review",
    "ResearchState",
]
