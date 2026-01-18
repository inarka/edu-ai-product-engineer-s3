"""Feature Processor Node - Analyzes feature requests with human-in-the-loop approval.

This is a single-node implementation (like bug_reporter and praise_logger) that:
1. Analyzes the feature request and generates a spec
2. Interrupts for human approval
3. Finalizes (writes file) or rejects based on decision

Single-node design is required because Command(goto=...) inside Send branches
applies updates to global state, losing the isolated current_review.
"""

import re
from typing import Literal
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langgraph.types import interrupt
from pydantic import BaseModel, Field

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


def _slugify(text: str) -> str:
    """Slugify text for filename."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "feature"


async def feature_processor_node(state: ReviewState) -> dict:
    """Process feature request: analyze, get human approval, finalize/reject.

    This is a single-node implementation that handles the entire feature flow:
    1. Analyze review and generate feature spec
    2. Interrupt for human approval
    3. Write spec file if approved, or mark as rejected

    Args:
        state: Current review state (isolated from Send branch with current_review)

    Returns:
        State update with feature_results, pending_feature_specs, feature_decisions
    """
    current_review = state.get("current_review")
    if not current_review:
        return {"messages": [AIMessage(content="No feature request to process.")]}

    review_id = int(current_review.get("id"))
    review_text = current_review.get("text", "")
    rating = int(current_review.get("rating", 0))

    # === 1. ANALYZE: Generate feature spec ===
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

    draft = {
        "feature_name": spec.feature_name,
        "complexity": spec.complexity,
        "priority": spec.priority,
        "markdown": markdown,
    }

    # === 2. INTERRUPT: Wait for human approval ===
    decision = interrupt({
        "type": "feature_approval",
        "question": "Approve this feature?",
        "review_id": review_id,
        "feature_name": spec.feature_name,
        "complexity": spec.complexity,
        "priority": spec.priority,
        "markdown": markdown,
    })

    # Parse decision (support both bool and dict formats)
    if isinstance(decision, bool):
        approved = decision
        notes = ""
    elif isinstance(decision, dict):
        approved = bool(decision.get("approved", False))
        notes = str(decision.get("notes", "")).strip()
    else:
        approved = False
        notes = ""

    # === 3. FINALIZE or REJECT ===
    if approved:
        # Write spec to file
        out_dir = Path("features")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{_slugify(spec.feature_name)}.md"
        out_path.write_text(markdown, encoding="utf-8")

        action = f"APPROVED → spec written to {out_path.as_posix()}"
        result_details = {
            "approved": True,
            "feature_name": spec.feature_name,
            "complexity": spec.complexity,
            "priority": spec.priority,
            "spec_path": out_path.as_posix(),
            "notes": notes,
        }
        msg_content = f"Feature for review #{review_id} approved. Wrote {out_path.as_posix()}."
    else:
        action = "REJECTED by human reviewer"
        result_details = {
            "approved": False,
            "feature_name": spec.feature_name,
            "complexity": spec.complexity,
            "priority": spec.priority,
            "draft_markdown": markdown,
            "notes": notes,
        }
        msg_content = f"Feature for review #{review_id} rejected."

    return {
        # For statistics
        "pending_feature_specs": {review_id: draft},
        "feature_decisions": {review_id: {"approved": approved, "notes": notes}},
        # Final result
        "feature_results": [{
            "id": review_id,
            "category": "feature",
            "action_taken": action,
            "details": result_details,
        }],
        "messages": [
            AIMessage(content=f"Drafted feature spec for review #{review_id}: {spec.feature_name}"),
            AIMessage(content=msg_content),
        ],
    }
