"""Triage Node - Classifies reviews and routes to appropriate handler.

TODO: Implement this node to:
1. Take a review from state
2. Use an LLM to classify it as: bug, feature, or praise
3. Return the classification in state

This node should use conditional edges to route to different branches.
"""

from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from ..state import ReviewState


TRIAGE_SYSTEM_PROMPT = """You are a review triage specialist. Your job is to classify
product reviews into one of three categories:

1. bug - The review describes a bug, error, crash, or something not working correctly
2. feature - The review requests a new feature or improvement
3. praise - The review is positive feedback, testimonial, or general appreciation

Analyze the review text and rating carefully and classify it into the appropriate category.
"""


class ReviewClassification(BaseModel):
    """Structured output for review classification."""
    
    category: Literal["bug", "feature", "praise"] = Field(
        description="The classification category: 'bug', 'feature', or 'praise'"
    )
    confidence: float = Field(
        description="Confidence score between 0.0 and 1.0",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Brief explanation of why this category was chosen"
    )


async def triage_node(state: ReviewState) -> dict:
    """Classify the current review and prepare for routing.

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
    # Get current review from state
    current_review = state.get("current_review")
    if not current_review:
        return {"messages": [AIMessage(content="No review to classify.")]}

    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    structured_llm = llm.with_structured_output(ReviewClassification)

    review_text = current_review.get("text", "")
    review_rating = current_review.get("rating", 0)

    messages = [
        SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
        HumanMessage(content=f"Review text: {review_text}\nRating: {review_rating}/5"),
    ]

    classification = await structured_llm.ainvoke(messages)
    category = classification.category
    rid = current_review.get("id")

    return {
        # IMPORTANT: list to avoid update conflicts when parallel
        "categories": {rid: category},
        "messages": [
            AIMessage(
                content=(
                    f"Classified review #{current_review.get('id')} as: {category.upper()} "
                    f"(confidence: {classification.confidence:.2f}). "
                    f"Reasoning: {classification.reasoning}"
                )
            )
        ],
    }

def route_review(state: ReviewState) -> str:
    rid = state.get("current_review", {}).get("id")
    category = (state.get("categories") or {}).get(rid, "bug")

    return {
        "bug": "bug_reporter",
        "feature": "feature_analyst",
        "praise": "praise_logger",
    }[category]
