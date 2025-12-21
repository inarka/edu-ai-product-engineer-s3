"""Summary Node - Aggregates all processed reviews into a report.

TODO: Implement this node to:
1. Collect results from all branches (bugs, features, praise)
2. Generate statistics
3. Create a summary report
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from ..state import ReviewState


SUMMARY_PROMPT = """You are a review processing summary writer. Your job is to:

1. Summarize the results from processing multiple reviews
2. Provide counts by category (bugs, features, praise)
3. Highlight key actions taken
4. Note any items pending human review

Format the summary in a clear, executive-friendly way.
"""


async def summary_node(state: ReviewState) -> dict:
    """Generate a summary of all processed reviews.

    TODO: Implement this function.

    This node is the fan-in point where all branches converge.
    It should aggregate results from:
    - bug_results
    - feature_results (both approved and pending)
    - praise_results

    Steps:
    1. Collect all results from state
    2. Calculate statistics
    3. Use LLM to generate readable summary
    4. Return final state with summary

    Args:
        state: Current review state with all results

    Returns:
        State update with summary report
    """
    # TODO: Collect results from all branches
    bug_results = state.get("bug_results", [])
    feature_results = state.get("feature_results", [])
    praise_results = state.get("praise_results", [])

    # TODO: Calculate statistics
    # total_reviews, bugs_count, features_count, praise_count

    # TODO: Use LLM to generate summary (gpt-5-mini is fine)

    # TODO: Return state update with summary_report

    raise NotImplementedError("Implement this node!")
