"""State definition for the Content Review Squad.

TODO: Extend this state schema with all the fields you need.

Hints:
- Think about what each agent needs to read and write
- Consider using sub-TypedDicts for structured data
- Remember to use Annotated[list, add_messages] for conversation history
"""

from typing import TypedDict, Literal, Annotated
from langgraph.graph import add_messages


class Review(TypedDict):
    """A single review to process."""
    id: int
    text: str
    rating: int


class ReviewResult(TypedDict, total=False):
    """Result of processing a single review."""
    id: int
    category: Literal["bug", "feature", "praise"]
    action_taken: str
    details: dict


class ReviewState(TypedDict, total=False):
    """The shared state for the Content Review Squad.

    TODO: Add more fields as needed for your implementation.

    Consider organizing into sections:
    - INPUT: Reviews to process
    - TRIAGE: Classification results
    - AGENT RESULTS: What each specialist produces
    - HUMAN REVIEW: Approval status
    - SYNTHESIS: Final summary
    - MESSAGES: Conversation history
    """

    # === INPUT ===
    reviews: list[Review]
    current_review: Review | None  # The review currently being processed

    # === TRIAGE ===
    # TODO: Add fields for classification results
    # Hint: What category is the current review?

    # === AGENT RESULTS ===
    # TODO: Add fields for each agent's output
    # Hint: bug_results, feature_results, praise_results

    # === HUMAN REVIEW ===
    # TODO: Add fields for human-in-the-loop
    # Hint: pending_approval, approved, rejected

    # === SYNTHESIS ===
    # TODO: Add fields for the final summary
    # Hint: summary_report, statistics

    # === MESSAGES ===
    # Use add_messages reducer for conversation history
    messages: Annotated[list, add_messages]
