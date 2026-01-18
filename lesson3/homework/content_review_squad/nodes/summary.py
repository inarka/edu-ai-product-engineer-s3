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
    # Collect results from all branches
    bug_results = state.get("bug_results", [])
    feature_results = state.get("feature_results", [])
    praise_results = state.get("praise_results", [])

    # Calculate statistics
    total_reviews = len(state.get("reviews", []))
    bugs_count = len(bug_results)
    features_count = len(feature_results)
    feature_approved_count = len([
        r for r in feature_results 
        if r.get("details", {}).get("approved", False)
    ])
    feature_rejected_count = features_count - feature_approved_count
    praise_count = len(praise_results)

    # Build detailed content for LLM
    content_parts = [
        f"Total reviews processed: {total_reviews}",
        f"\nBugs: {bugs_count}",
        f"\nFeatures: {features_count} (Approved: {feature_approved_count}, Rejected: {feature_rejected_count})",
        f"\nPraise: {praise_count}",
    ]

    # Add details for each category
    if bug_results:
        content_parts.append("\n\nBug Reports:")
        for result in bug_results:
            action = result.get("action_taken", "Unknown")
            details = result.get("details", {})
            content_parts.append(f"- Review #{result.get('id')}: {action}")
            if details:
                content_parts.append(f"  Details: {details}")

    if feature_results:
        content_parts.append("\n\nFeature Requests:")
        for result in feature_results:
            action = result.get("action_taken", "Unknown")
            details = result.get("details", {})
            feature_name = details.get("feature_name", "Unknown")
            approved = details.get("approved", False)
            status = "APPROVED" if approved else "REJECTED"
            content_parts.append(f"- Review #{result.get('id')}: {feature_name} - {status}")
            content_parts.append(f"  Action: {action}")
            if details.get("notes"):
                content_parts.append(f"  Notes: {details['notes']}")
            if details.get("spec_path"):
                content_parts.append(f"  Spec written to: {details['spec_path']}")

    if praise_results:
        content_parts.append("\n\nPraise:")
        for result in praise_results:
            action = result.get("action_taken", "Unknown")
            content_parts.append(f"- Review #{result.get('id')}: {action}")

    # Use LLM to generate summary (gpt-5-mini is fine)
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0)
    summary_response = await llm.ainvoke([
        SystemMessage(content=SUMMARY_PROMPT),
        HumanMessage(content="\n".join(content_parts))
    ])

    summary_text = summary_response.content if hasattr(summary_response, 'content') else str(summary_response)

    return {
        "summary_report": summary_text,
        "messages": [AIMessage(content=f"Summary generated: {summary_text[:100]}...")],
    }
