"""Graph assembly for the Content Review Squad.

TODO: Implement the graph wiring.

Key patterns to implement:
1. Triage node at entry
2. Conditional edges based on classification
3. Fan-in to summary node
4. Human-in-the-loop for feature approval
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send

from .state import ReviewState
from .nodes import (
    triage_node,
    bug_reporter_node,
    feature_analyst_node,
    praise_logger_node,
    summary_node,
)
from .nodes.triage import route_review

def dispatch_reviews(state: ReviewState):
    # fan-out: create a triage branch for each review
    return [Send("triage", {"current_review": r}) for r in state["reviews"]]

def create_content_review_squad(checkpointer=None):
    """Create and compile the Content Review Squad graph.

    Architecture:
    ```
                        ┌─────────────────┐
                        │  Triage Agent   │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌───────────┐ ┌───────────┐ ┌───────────┐
             │    Bug    │ │  Feature  │ │   Praise  │
             │  Reporter │ │  Analyst  │ │   Logger  │
             └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
                   │             │             │
                   │      [HUMAN REVIEW]       │
                   │             │             │
                   └─────────────┼─────────────┘
                                 ▼
                        ┌─────────────────┐
                        │     Summary     │
                        └─────────────────┘
    ```

    Steps:
    1. Create StateGraph with ReviewState
    2. Add all nodes
    3. Add edges from START to triage
    4. Add conditional edges from triage to handlers
    5. Add edges from handlers to summary
    6. Add edge from summary to END
    7. Compile with checkpointer
    8. For human-in-the-loop: use interrupt_before or interrupt_after

    Args:
        checkpointer: Optional checkpointer for persistence

    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(ReviewState)

    graph.add_node("dispatch", lambda s: {})
    graph.add_node("triage", triage_node)
    graph.add_node("bug_reporter", bug_reporter_node)
    graph.add_node("feature_analyst", feature_analyst_node)
    graph.add_node("praise_logger", praise_logger_node)

    # summary once at the end
    graph.add_node("summary", summary_node, defer=True)

    graph.add_edge(START, "dispatch")

    # FAN-OUT: dispatch -> many triage
    graph.add_conditional_edges("dispatch", dispatch_reviews, ["triage"])

    # ROUTING: triage -> appropriate agent
    graph.add_conditional_edges(
        "triage",
        route_review,
        {
            "bug_reporter": "bug_reporter",
            "feature_analyst": "feature_analyst",
            "praise_logger": "praise_logger",
        },
    )

    # FAN-IN: all branches converge in summary
    graph.add_edge("bug_reporter", "summary")
    graph.add_edge("feature_analyst", "summary")
    graph.add_edge("praise_logger", "summary")
    graph.add_edge("summary", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["feature_finalize"],
    )


# Convenience instance (students should implement create_content_review_squad first)
# content_review_squad = create_content_review_squad()
