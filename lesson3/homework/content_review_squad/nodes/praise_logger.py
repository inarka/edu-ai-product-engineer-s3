"""Praise Logger Node - Records positive feedback as testimonials.

TODO: Implement this node to:
1. Take a positive review from state
2. Extract key quotes and sentiment
3. Format as a testimonial
4. Return the result in state
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import Literal

from ..state import ReviewState

class Testimonial(BaseModel):
    quote: str = Field(description="Most impactful direct quote from the review (verbatim style)")
    sentiment_summary: str = Field(description="1–2 sentence summary of positive sentiment")
    value: Literal["high", "medium", "low"] = Field(description="Testimonial value")
    suggested_uses: list[str] = Field(description="Where to use it (e.g., landing page, social, app store)")


PRAISE_LOGGER_PROMPT = """You are a testimonial curator. Your job is to:

1. Extract the most impactful quote from the positive review
2. Summarize the key positive sentiment
3. Rate the testimonial value (high/medium/low)
4. Suggest where this testimonial could be used (landing page, social, etc.)

Keep the original voice of the user when extracting quotes.
"""


async def praise_logger_node(state: ReviewState) -> dict:
    """Log positive feedback as a testimonial.

    Steps:
    1. Get the positive review from state
    2. Use LLM to extract and format testimonial (gpt-5-mini is fine)
    3. Return state update with testimonial

    Args:
        state: Current review state

    Returns:
        State update with testimonial result
    """
    current_review = state.get("current_review")
    if not current_review:
        return {"messages": [AIMessage(content="No praise to log.")]}

    review_id = current_review.get("id")
    review_text = current_review.get("text", "")
    rating = int(current_review.get("rating", 0))

    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    structured_llm = llm.with_structured_output(Testimonial)

    messages = [
        SystemMessage(content=PRAISE_LOGGER_PROMPT),
        HumanMessage(
            content=(
                "Extract a testimonial from the review.\n"
                "- Quote should preserve the user's voice.\n"
                "- If the review is short, the quote can be the full text.\n\n"
                f"Review ID: {review_id}\n"
                f"Rating: {rating}/5\n"
                f"Text: {review_text}\n"
            )
        ),
    ]

    t: Testimonial = await structured_llm.ainvoke(messages)

    action = f"Logged testimonial (value: {t.value.upper()})"

    return {
        "praise_results": [
            {
                "id": review_id,
                "category": "praise",
                "action_taken": action,
                "details": {
                    "quote": t.quote,
                    "sentiment_summary": t.sentiment_summary,
                    "value": t.value,
                    "suggested_uses": t.suggested_uses,
                    "rating": rating,
                },
            }
        ],
        "messages": [
            AIMessage(
                content=(
                    f"Extracted testimonial for review #{review_id}. "
                    f"Value={t.value.upper()}. Quote: “{t.quote}”"
                )
            )
        ],
    }
