"""Feature Analyst Node - Analyzes feature requests and writes specs.

TODO: Implement this node to:
1. Take a feature request review from state
2. Analyze the feature request
3. Generate a feature specification
4. This node should have HUMAN-IN-THE-LOOP before finalizing

IMPORTANT: This is where you implement the human-in-the-loop requirement!
"""

import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langgraph.prebuilt import interrupt
from pydantic import BaseModel, Field
from typing import Literal
from pathlib import Path

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

class FeatureSpec(BaseModel):
    feature_name: str = Field(description="Short, user-facing feature name")
    problem: str = Field(description="Problem this feature solves")
    proposed_solution: str = Field(description="What we will build")
    user_benefit: str = Field(description="Why users care / value")
    complexity: Literal["low", "medium", "high"] = Field(description="Implementation complexity")
    priority: Literal["low", "medium", "high"] = Field(description="Priority recommendation")
    acceptance_criteria: list[str] = Field(default_factory=list, description="Concrete acceptance criteria")


def _spec_to_markdown(spec: FeatureSpec, review_id: int, review_text: str, rating: int) -> str:
    ac = spec.acceptance_criteria or []
    ac_md = "\n".join([f"- {x}" for x in ac]) if ac else "- Not provided"
    return (
        f"# {spec.feature_name}\n\n"
        f"## Problem\n{spec.problem}\n\n"
        f"## Proposed solution\n{spec.proposed_solution}\n\n"
        f"## User benefit\n{spec.user_benefit}\n\n"
        f"## Complexity\n- Complexity: {spec.complexity}\n\n"
        f"## Priority recommendation\n- Priority: {spec.priority}\n\n"
        f"## Acceptance criteria\n{ac_md}\n\n"
        f"---\n"
        f"## Original review\n"
        f"- Review ID: {review_id}\n"
        f"- Rating: {rating}/5\n"
        f"- Text: {review_text}\n"
    )


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
    # Get current review
    current_review = state.get("current_review")
    if not current_review:
        return {"messages": [AIMessage(content="No feature request to analyze.")]}

    review_id = int(current_review.get("id"))
    review_text = current_review.get("text", "")
    rating = int(current_review.get("rating", 0))

    llm = ChatOpenAI(model="gpt-5.2", temperature=0)
    structured_llm = llm.with_structured_output(FeatureSpec)

    msgs = [
        SystemMessage(content=FEATURE_ANALYST_PROMPT),
        HumanMessage(
            content=(
                "Generate a concise feature specification.\n"
                f"Review ID: {review_id}\n"
                f"Rating: {rating}/5\n"
                f"Text: {review_text}\n"
            )
        ),
    ]

    spec: FeatureSpec = await structured_llm.ainvoke(msgs)
    markdown = _spec_to_markdown(spec, review_id=review_id, review_text=review_text, rating=rating)

    # draft кладём в pending_feature_specs[review_id]
    draft = {
        "feature_name": spec.feature_name,
        "complexity": spec.complexity,
        "priority": spec.priority,
        "markdown": markdown,
    }

    return {
        "pending_feature_specs": {review_id: draft},
        "messages": [
            AIMessage(content=f"Drafted feature spec for review #{review_id}: {spec.feature_name} (PENDING HUMAN REVIEW)")
        ],
    }
    
def _slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "feature"


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
    current_review = state.get("current_review")
    if not current_review:
        return {"messages": [AIMessage(content="No feature request to finalize.")]}

    review_id = int(current_review.get("id"))

    drafts = state.get("pending_feature_specs") or {}
    draft = drafts.get(review_id)
    if not draft:
        return {
            "feature_results": [{
                "id": review_id,
                "category": "feature",
                "action_taken": "FAILED: no draft spec found",
                "details": {},
            }],
            "messages": [AIMessage(content=f"No draft spec found for review #{review_id}.")],
        }

    decisions = state.get("feature_decisions") or {}
    decision = decisions.get(review_id) or {}
    approved = bool(decision.get("approved", False))
    notes = (decision.get("notes") or "").strip()

    feature_name = draft.get("feature_name", f"Feature from review {review_id}")
    complexity = draft.get("complexity", "medium")
    priority = draft.get("priority", "medium")
    markdown = draft.get("markdown", "")

    if not approved:
        return {
            "feature_results": [{
                "id": review_id,
                "category": "feature",
                "action_taken": "REJECTED by human reviewer",
                "details": {
                    "feature_name": feature_name,
                    "complexity": complexity,
                    "priority": priority,
                    "draft_markdown": markdown,
                    "notes": notes,
                    "approved": False,
                },
            }],
            "messages": [AIMessage(content=f"Feature spec for review #{review_id} REJECTED. {notes}".strip())],
        }

    # (опционально) запись файла — это как раз “finalize”
    out_dir = Path("features")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{_slugify(feature_name)}.md"
    out_path.write_text(markdown, encoding="utf-8")

    return {
        "feature_results": [{
            "id": review_id,
            "category": "feature",
            "action_taken": f"APPROVED → spec written to {out_path.as_posix()}",
            "details": {
                "feature_name": feature_name,
                "complexity": complexity,
                "priority": priority,
                "spec_path": out_path.as_posix(),
                "notes": notes,
                "approved": True,
            },
        }],
        "messages": [AIMessage(content=f"Feature spec for review #{review_id} APPROVED. Wrote {out_path.as_posix()}.")],
    }
