"""Feature Analyst Node - Analyzes feature requests and writes specs.

TODO: Implement this node to:
1. Take a feature request review from state
2. Analyze the feature request
3. Generate a feature specification
4. This node should have HUMAN-IN-THE-LOOP before finalizing

IMPORTANT: This is where you implement the human-in-the-loop requirement!
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from ..state import ReviewState


FEATURE_ANALYST_PROMPT = """You are a feature specification writer. Your job is to:

1. Analyze the feature request from a user review
2. Determine feasibility and value
3. Write a brief feature specification including:
   - Feature name
   - Problem it solves
   - Proposed solution
   - User benefit
   - Implementation complexity (low/medium/high)
   - Priority recommendation

Be concise and focus on business value and user impact.
"""


async def feature_analyst_node(state: ReviewState) -> dict:
    """Analyze a feature request and prepare a specification.

    TODO: Implement this function.

    IMPORTANT: This node should prepare the feature spec but NOT finalize it.
    The human-in-the-loop should happen BEFORE this node or AFTER to review
    the spec before it's added to the final results.

    Options for human-in-the-loop:
    1. Use interrupt_before in graph.compile() on this node
    2. Use interrupt_after on this node
    3. Add a separate "review" node after this one

    Steps:
    1. Get the feature request from state
    2. Use LLM to analyze and generate spec (use gpt-5.2 for quality)
    3. Return state update with the spec (marked as pending approval)

    Args:
        state: Current review state

    Returns:
        State update with feature spec (pending human approval)
    """
    # TODO: Get current review
    current_review = state.get("current_review")

    if not current_review:
        return {
            "messages": [AIMessage(content="No feature request to analyze.")]
        }

    # TODO: Use gpt-5.2 for complex feature analysis
    # llm = ChatOpenAI(model="gpt-5.2", temperature=0)

    # TODO: Generate feature specification

    # TODO: Return state update
    # Mark as pending_approval=True so human can review

    raise NotImplementedError("Implement this node!")


async def feature_approval_node(state: ReviewState) -> dict:
    """Handle human approval/rejection of feature specs.

    TODO (OPTIONAL): Implement a separate approval node.

    This is an alternative approach to using interrupt_before/after.
    You can have a dedicated node that checks approval status.

    Args:
        state: Current review state with pending feature spec

    Returns:
        State update with approved/rejected status
    """
    # This is optional - you can use interrupt_before/after instead
    raise NotImplementedError("Optional: Implement if using separate approval node")
