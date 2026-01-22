"""Triage Node - Classifies all reviews before fan-out.

This node classifies all reviews in parallel before dispatch.
Categories are stored in global state, then dispatch uses them for routing.
"""

import asyncio
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


async def triage_all_node(state: ReviewState) -> dict:
    """Classify all reviews in parallel before fan-out.

    Classification happens before dispatch so categories are available
    in global state for proper routing.

    Steps:
    1. Get all reviews from state
    2. Classify each review in parallel using LLM
    3. Return categories in global state

    Args:
        state: Current review state with reviews list

    Returns:
        State update with categories dict: {review_id: category}
    """
    reviews = state.get("reviews", [])
    
    if not reviews:
        return {
            "categories": {},
            "messages": [AIMessage(content="No reviews to classify.")]
        }

    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    structured_llm = llm.with_structured_output(ReviewClassification)
    
    # Parallel classification of all reviews
    async def classify(review: dict) -> tuple[int, ReviewClassification]:
        """Classify a single review."""
        messages = [
            SystemMessage(content=TRIAGE_SYSTEM_PROMPT),
            HumanMessage(content=f"Review text: {review['text']}\nRating: {review['rating']}/5"),
        ]
        classification = await structured_llm.ainvoke(messages)
        return review["id"], classification
    
    # Classify all reviews in parallel
    results = await asyncio.gather(*[classify(r) for r in reviews])
    
    # Collect categories and messages
    categories = {rid: cls.category for rid, cls in results}
    messages = [
        AIMessage(
            content=(
                f"Classified review #{rid} as: {cls.category.upper()} "
                f"(confidence: {cls.confidence:.2f}). "
                f"Reasoning: {cls.reasoning}"
            )
        )
        for rid, cls in results
    ]
    
    return {
        "categories": categories,
        "messages": messages,
    }
