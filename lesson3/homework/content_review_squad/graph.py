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
    triage_all_node,
    bug_reporter_node,
    feature_analyst_node,
    feature_approval_node,
    feature_finalize_node,
    feature_reject_node,
    praise_logger_node,
    summary_node,
)

def dispatch_reviews(state: ReviewState):
    """Dispatch reviews to appropriate handlers based on categories.

    Reads categories from global state (set by triage_all_node) and creates
    Send for each review to route it to the correct handler.

    Args:
        state: Current review state with categories and reviews

    Returns:
        List of Send objects routing each review to appropriate handler
    """
    categories = state.get("categories", {})
    reviews = state.get("reviews", [])
    
    sends = []
    for r in reviews:
        review_id = r.get("id")
        category = categories.get(review_id, "bug")  # default to bug if not classified
        
        # Map category to target node
        node = {
            "bug": "bug_reporter",
            "feature": "feature_analyst",
            "praise": "praise_logger",
        }.get(category, "bug_reporter")
        
        # Send передаёт изолированное состояние следующему узлу
        sends.append(Send(node, {
            "current_review": r,
            "category": category,
        }))
    
    return sends

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

    # === NODES ===
    graph.add_node("triage_all", triage_all_node)
    graph.add_node("bug_reporter", bug_reporter_node)
    graph.add_node("feature_analyst", feature_analyst_node)
    graph.add_node("feature_approval", feature_approval_node)
    graph.add_node("feature_finalize", feature_finalize_node)
    graph.add_node("feature_reject", feature_reject_node)
    graph.add_node("praise_logger", praise_logger_node)

    # summary once at the end
    graph.add_node("summary", summary_node, defer=True)

    # === EDGES ===
    # Классификация до fan-out: START -> triage_all -> dispatch -> Send(...)
    graph.add_edge(START, "triage_all")
    
    # FAN-OUT: dispatch читает categories из глобального state и создаёт Send для каждого ревью
    graph.add_conditional_edges(
        "triage_all",
        dispatch_reviews,
        ["bug_reporter", "feature_analyst", "praise_logger"]
    )
    
    # FEATURE FLOW: analyst -> approval (HIL) -> finalize/reject
    graph.add_edge("feature_analyst", "feature_approval")
    # feature_approval uses Command(goto=...) to route to finalize or reject

    # FAN-IN: all branches converge in summary
    graph.add_edge("bug_reporter", "summary")
    graph.add_edge("feature_finalize", "summary")
    graph.add_edge("feature_reject", "summary")
    graph.add_edge("praise_logger", "summary")
    graph.add_edge("summary", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(
        checkpointer=checkpointer,
    )


# Convenience instance (students should implement create_content_review_squad first)
# content_review_squad = create_content_review_squad()
