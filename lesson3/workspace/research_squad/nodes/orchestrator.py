"""Orchestrator Node - The entry point for the Research Squad.

This node:
1. Receives the initial request
2. Creates a research plan
3. Delegates to specialist agents (via graph edges)

Note: The orchestrator doesn't call agents directly - that's handled
by the graph's fan-out edges. This keeps orchestration logic separate
from execution logic.
"""

from langchain_core.messages import AIMessage, HumanMessage

from ..state import ResearchState


async def orchestrator_node(state: ResearchState) -> dict:
    """Plan the research and prepare for delegation.

    In a more sophisticated system, this could use an LLM to create
    a dynamic research plan. For this demo, we use a simple template.

    Args:
        state: Current research state with input fields

    Returns:
        State update with plan messages
    """
    linkedin_url = state.get("linkedin_url", "")
    company_name = state.get("company_name", "Unknown Company")

    # Create research plan (deterministic for demo)
    plan = f"""Research Plan
================

Target: {linkedin_url}
Company: {company_name}

Execution Steps:
1. LinkedIn Agent → Profile analysis and career trajectory
2. Company Agent → Company intelligence and market position
3. News Agent → Recent news, trends, and sentiment
4. Synthesis Agent → Combined insights and recommendations

All research agents will execute in PARALLEL for efficiency.
Results will be synthesized into a comprehensive report.
"""

    return {
        "messages": [
            HumanMessage(content=f"Research request: {linkedin_url}"),
            AIMessage(content=plan),
        ]
    }
