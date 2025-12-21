"""Triage Node - Classifies reviews and routes to appropriate handler.

TODO: Implement this node to:
1. Take a review from state
2. Use an LLM to classify it as: bug, feature, or praise
3. Return the classification in state

This node should use conditional edges to route to different branches.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from ..state import ReviewState


TRIAGE_SYSTEM_PROMPT = """You are a review triage specialist. Your job is to classify
product reviews into one of three categories:

1. BUG - The review describes a bug, error, crash, or something not working correctly
2. FEATURE - The review requests a new feature or improvement
3. PRAISE - The review is positive feedback, testimonial, or general appreciation

Analyze the review text and rating. Return ONLY one word: BUG, FEATURE, or PRAISE.
"""


async def triage_node(state: ReviewState) -> dict:
    """Classify the current review and prepare for routing.

    TODO: Implement this function.

    Steps:
    1. Get the current review from state
    2. Use an LLM to classify it (use gpt-5-mini for cost efficiency)
    3. Parse the classification
    4. Return state update with the classification

    The graph's conditional edges will use this classification to route
    to the appropriate handler (bug_reporter, feature_analyst, or praise_logger).

    Args:
        state: Current review state

    Returns:
        State update with classification result
    """
    # TODO: Get current review from state
    current_review = state.get("current_review")

    if not current_review:
        return {
            "messages": [AIMessage(content="No review to classify.")]
        }

    # TODO: Create LLM and classify
    # Hint: Use ChatOpenAI with gpt-5-mini
    # llm = ChatOpenAI(model="gpt-5-mini", temperature=0)

    # TODO: Call the LLM with the system prompt and review text

    # TODO: Parse the response to get category (bug/feature/praise)

    # TODO: Return state update
    # Hint: Return the category so conditional edges can route properly

    raise NotImplementedError("Implement this node!")


def route_review(state: ReviewState) -> str:
    """Route to the appropriate handler based on classification.

    TODO: Implement this routing function.

    This function is used by conditional_edges to determine
    which node to execute next.

    Args:
        state: Current state with classification

    Returns:
        Name of the next node: "bug_reporter", "feature_analyst", or "praise_logger"
    """
    # TODO: Read the classification from state
    # TODO: Return the appropriate node name

    raise NotImplementedError("Implement routing logic!")
