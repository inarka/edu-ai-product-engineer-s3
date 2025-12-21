"""Praise Logger Node - Records positive feedback as testimonials.

TODO: Implement this node to:
1. Take a positive review from state
2. Extract key quotes and sentiment
3. Format as a testimonial
4. Return the result in state
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from ..state import ReviewState


PRAISE_LOGGER_PROMPT = """You are a testimonial curator. Your job is to:

1. Extract the most impactful quote from the positive review
2. Summarize the key positive sentiment
3. Rate the testimonial value (high/medium/low)
4. Suggest where this testimonial could be used (landing page, social, etc.)

Keep the original voice of the user when extracting quotes.
"""


async def praise_logger_node(state: ReviewState) -> dict:
    """Log positive feedback as a testimonial.

    TODO: Implement this function.

    Steps:
    1. Get the positive review from state
    2. Use LLM to extract and format testimonial (gpt-5-mini is fine)
    3. Return state update with testimonial

    Args:
        state: Current review state

    Returns:
        State update with testimonial result
    """
    # TODO: Get current review
    current_review = state.get("current_review")

    if not current_review:
        return {
            "messages": [AIMessage(content="No praise to log.")]
        }

    # TODO: Create LLM (gpt-5-mini is sufficient for this task)

    # TODO: Extract and format testimonial

    # TODO: Return state update
    # Hint: Add to praise_results list in state

    raise NotImplementedError("Implement this node!")
