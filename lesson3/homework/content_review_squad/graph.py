"""Graph assembly for the Content Review Squad.

Architecture:
- triage_all classifies all reviews before fan-out
- dispatch_reviews creates Send for each review to appropriate handler
- Each handler (bug_reporter, feature_processor, praise_logger) is a single node
- feature_processor includes interrupt() for human-in-the-loop approval
- All handlers fan-in to deferred summary node

Key insight: Single-node handlers are required because Command(goto=...) inside
Send branches applies updates to global state, losing isolated current_review.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send

from .state import ReviewState
from .nodes import (
    triage_all_node,
    bug_reporter_node,
    feature_processor_node,
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
            "feature": "feature_processor",
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
                        │   Triage All    │
                        │  (classifier)   │
                        └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌───────────┐ ┌───────────┐ ┌───────────┐
             │    Bug    │ │  Feature  │ │   Praise  │
             │  Reporter │ │ Processor │ │   Logger  │
             └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
                   │             │             │
                   │      [interrupt()]        │
                   │             │             │
                   └─────────────┼─────────────┘
                                 ▼
                        ┌─────────────────┐
                        │     Summary     │
                        │    (deferred)   │
                        └─────────────────┘
    ```

    Args:
        checkpointer: Optional checkpointer for persistence

    Returns:
        Compiled StateGraph
    """
    graph = StateGraph(ReviewState)

    # === NODES ===
    graph.add_node("triage_all", triage_all_node)
    graph.add_node("bug_reporter", bug_reporter_node)
    graph.add_node("feature_processor", feature_processor_node)
    graph.add_node("praise_logger", praise_logger_node)

    # Summary runs once after all branches complete (deferred)
    graph.add_node("summary", summary_node, defer=True)

    # === EDGES ===
    # START -> triage_all (classifies all reviews)
    graph.add_edge(START, "triage_all")

    # FAN-OUT: triage_all -> dispatch -> Send to handlers
    # dispatch_reviews reads categories and creates Send for each review
    graph.add_conditional_edges(
        "triage_all",
        dispatch_reviews,
        ["bug_reporter", "feature_processor", "praise_logger"]
    )

    # FAN-IN: all handlers converge to summary
    graph.add_edge("bug_reporter", "summary")
    graph.add_edge("feature_processor", "summary")
    graph.add_edge("praise_logger", "summary")

    # summary -> END
    graph.add_edge("summary", END)

    if checkpointer is None:
        checkpointer = MemorySaver()

    return graph.compile(
        checkpointer=checkpointer,
    )
