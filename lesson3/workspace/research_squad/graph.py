"""Graph assembly for the Research Squad.

This module wires together all the nodes into a StateGraph with:
- Fan-out: Orchestrator → [LinkedIn, Company, News] in PARALLEL
- Fan-in: All agents → Synthesis
- Optional human-in-the-loop before final output

Key LangGraph concepts demonstrated:
1. StateGraph with typed state
2. Parallel execution via fan-out edges
3. Synchronization via fan-in
4. Conditional edges for routing
5. Checkpointing for persistence
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import ResearchState
from .nodes import (
    orchestrator_node,
    linkedin_agent_node,
    company_agent_node,
    news_agent_node,
    synthesis_node,
)


def should_continue_to_synthesis(state: ResearchState) -> str:
    """Check if we have enough data to synthesize.

    This is a simple router - in production you might add more logic.
    """
    # Always proceed to synthesis - it handles missing data gracefully
    return "synthesis"


def create_research_squad_graph(checkpointer=None):
    """Create and compile the Research Squad graph.

    Architecture:
    ```
                        ┌─────────────────┐
                        │   Orchestrator  │
                        │   (entry node)  │
                        └────────┬────────┘
                                 │
             ┌───────────────────┼───────────────────┐
             ▼                   ▼                   ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ LinkedIn Agent  │  │  Company Agent  │  │   News Agent    │
    │ (parallel node) │  │ (parallel node) │  │ (parallel node) │
    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
             │                    │                    │
             └───────────────────┬┴───────────────────┘
                                 ▼
                        ┌─────────────────┐
                        │    Synthesis    │
                        │     Agent       │
                        └────────┬────────┘
                                 │
                                 ▼
                               END
    ```

    Args:
        checkpointer: Optional checkpointer for persistence (defaults to MemorySaver)

    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize the graph with our state schema
    graph = StateGraph(ResearchState)

    # === ADD NODES ===
    # Each node is an async function that receives state and returns partial updates
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("linkedin_agent", linkedin_agent_node)
    graph.add_node("company_agent", company_agent_node)
    graph.add_node("news_agent", news_agent_node)
    graph.add_node("synthesis", synthesis_node)

    # === ADD EDGES ===
    # Entry point
    graph.add_edge(START, "orchestrator")

    # Fan-out: Orchestrator sends to all research agents IN PARALLEL
    # This is the key pattern - all three agents run concurrently
    graph.add_edge("orchestrator", "linkedin_agent")
    graph.add_edge("orchestrator", "company_agent")
    graph.add_edge("orchestrator", "news_agent")

    # Fan-in: All research agents converge to synthesis
    # LangGraph automatically waits for all parallel branches to complete
    graph.add_edge("linkedin_agent", "synthesis")
    graph.add_edge("company_agent", "synthesis")
    graph.add_edge("news_agent", "synthesis")

    # Synthesis → END
    graph.add_edge("synthesis", END)

    # === COMPILE ===
    # Use provided checkpointer or default to in-memory
    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


def create_research_squad_graph_with_human_review(checkpointer=None):
    """Create graph with human-in-the-loop before synthesis.

    This variant adds an interrupt_before on the synthesis node,
    allowing humans to review research results before final report.

    Use this for production scenarios where human oversight is required.

    Args:
        checkpointer: Optional checkpointer for persistence

    Returns:
        Compiled StateGraph with human review interrupt
    """
    graph = StateGraph(ResearchState)

    # Add nodes (same as above)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("linkedin_agent", linkedin_agent_node)
    graph.add_node("company_agent", company_agent_node)
    graph.add_node("news_agent", news_agent_node)
    graph.add_node("synthesis", synthesis_node)

    # Add edges (same as above)
    graph.add_edge(START, "orchestrator")
    graph.add_edge("orchestrator", "linkedin_agent")
    graph.add_edge("orchestrator", "company_agent")
    graph.add_edge("orchestrator", "news_agent")
    graph.add_edge("linkedin_agent", "synthesis")
    graph.add_edge("company_agent", "synthesis")
    graph.add_edge("news_agent", "synthesis")
    graph.add_edge("synthesis", END)

    # Use provided checkpointer or default to in-memory
    if checkpointer is None:
        checkpointer = MemorySaver()

    # Compile WITH interrupt_before synthesis
    # This pauses execution before synthesis, allowing human review
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["synthesis"],
    )


# Convenience: Pre-built graph instance for simple use cases
# For production, call create_research_squad_graph() with your own checkpointer
research_squad = create_research_squad_graph()
