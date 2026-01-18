"""State definition for the Content Review Squad.

TODO: Extend this state schema with all the fields you need.

Hints:
- Think about what each agent needs to read and write
- Consider using sub-TypedDicts for structured data
- Remember to use Annotated[list, add_messages] for conversation history
"""

from typing import TypedDict, Literal, Annotated
from langgraph.graph import add_messages
import operator
Category = Literal["bug", "feature", "praise"]


class Review(TypedDict):
    """A single review to process."""
    id: int
    text: str
    rating: int


class ReviewResult(TypedDict, total=False):
    """Result of processing a single review."""
    id: int
    category: Category
    action_taken: str
    details: dict

class FeatureDraft(TypedDict, total=False):
    feature_name: str
    complexity: Literal["low", "medium", "high"]
    priority: Literal["low", "medium", "high"]
    markdown: str

class FeatureDecision(TypedDict, total=False):
    approved: bool
    notes: str


class ReviewState(TypedDict, total=False):
    # === INPUT ===
    reviews: list[Review]
    current_review: Review | None

    # === TRIAGE ===
    categories: Annotated[dict[int, Category], operator.or_]

    # === AGENT RESULTS ===
    bug_results: Annotated[list[ReviewResult], operator.add]
    praise_results: Annotated[list[ReviewResult], operator.add]
    pending_feature_specs: Annotated[dict[int, FeatureDraft], operator.or_]
    feature_decisions: dict[int, FeatureDecision]

    # === SYNTHESIS ===
    summary_report: str

    # === MESSAGES ===
    messages: Annotated[list, add_messages]
