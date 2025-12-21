"""Bug Reporter Node - Creates GitHub issues for bug reports.

TODO: Implement this node to:
1. Take a bug report review from state
2. Generate a structured bug report
3. (Optional) Create a GitHub issue via API
4. Return the result in state
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool

from ..state import ReviewState


BUG_REPORTER_PROMPT = """You are a bug report specialist. Your job is to:

1. Analyze the user's bug report
2. Extract key information:
   - Summary (one line)
   - Steps to reproduce (if mentioned)
   - Expected behavior
   - Actual behavior
   - Severity (critical/high/medium/low)
3. Format as a structured bug report

Be concise and technical. Focus on actionable information.
"""


@tool
def create_github_issue(title: str, body: str, labels: list[str]) -> dict:
    """Create a GitHub issue for the bug report.

    USE WHEN: You have a structured bug report ready to submit.

    RETURNS ON SUCCESS: Dict with issue number and URL
    RETURNS ON ERROR: Dict with 'error' key

    Note: This is a simulated tool for the homework.
    In production, you would use the GitHub API.

    Args:
        title: Issue title
        body: Issue body in markdown
        labels: Labels to apply (e.g., ["bug", "high-priority"])

    Returns:
        Issue creation result
    """
    # Simulated response
    import random
    issue_num = random.randint(100, 999)
    return {
        "issue_number": issue_num,
        "url": f"https://github.com/example/repo/issues/{issue_num}",
        "status": "created",
    }


async def bug_reporter_node(state: ReviewState) -> dict:
    """Process a bug report and create a GitHub issue.

    TODO: Implement this function.

    Steps:
    1. Get the bug review from state
    2. Use LLM to generate structured bug report
    3. (Optional) Use the create_github_issue tool
    4. Return state update with the result

    Args:
        state: Current review state

    Returns:
        State update with bug report result
    """
    # TODO: Get current review
    current_review = state.get("current_review")

    if not current_review:
        return {
            "messages": [AIMessage(content="No bug review to process.")]
        }

    # TODO: Create LLM (can use gpt-5-mini for this task)

    # TODO: Generate structured bug report

    # TODO: Optionally create GitHub issue

    # TODO: Return state update with result
    # Hint: Add to bug_results list in state

    raise NotImplementedError("Implement this node!")
