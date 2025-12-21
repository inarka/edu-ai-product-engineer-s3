"""Node functions for the Research Squad.

Each node is a specialist agent with its own prompt and tools.
"""

from .orchestrator import orchestrator_node
from .linkedin_agent import linkedin_agent_node
from .company_agent import company_agent_node
from .news_agent import news_agent_node
from .synthesis import synthesis_node

__all__ = [
    "orchestrator_node",
    "linkedin_agent_node",
    "company_agent_node",
    "news_agent_node",
    "synthesis_node",
]
