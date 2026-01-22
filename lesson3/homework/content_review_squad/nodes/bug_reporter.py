"""Bug Reporter Node - Creates GitHub issues for bug reports.

TODO: Implement this node to:
1. Take a bug report review from state
2. Generate a structured bug report
3. (Optional) Create a GitHub issue via API
4. Return the result in state
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Literal

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


class BugReport(BaseModel):
    summary: str = Field(description="One-line summary")
    steps_to_reproduce: list[str] = Field(default_factory=list, description="Numbered steps if known")
    expected_behavior: str = Field(description="What the user expected")
    actual_behavior: str = Field(description="What actually happened")
    severity: Literal["critical", "high", "medium", "low"] = Field(description="Severity level")


async def bug_reporter_node(state: ReviewState) -> dict:
    """Process a bug report review and create a GitHub issue."""
    current_review = state.get("current_review")
    if not current_review:
        return {"messages": [AIMessage(content="No bug review to process.")]}

    review_id = current_review.get("id")
    review_text = current_review.get("text", "")
    rating = current_review.get("rating", 0)

    llm = ChatOpenAI(model="gpt-5-mini", temperature=0).bind_tools([create_github_issue])

    messages = [
        SystemMessage(content=BUG_REPORTER_PROMPT),
        HumanMessage(
            content=(
                "Analyze this bug report and create a GitHub issue.\n"
                "You MUST call the create_github_issue tool with:\n"
                "- title: One-line summary (str)\n"
                "- body: Full bug report in markdown (str)\n"
                "- labels: Include 'bug' and one of ['severity:critical','severity:high','severity:medium','severity:low'] (list[str])\n"
                f"Review ID: {review_id}\n"
                f"Rating: {rating}/5\n"
                f"Text: {review_text}\n"
            )
        ),
    ]

    ai_response = await llm.ainvoke(messages)

    tool_calls = getattr(ai_response, "tool_calls", None) or []
    if not tool_calls:
        return {
            "bug_results": [{
                "id": review_id,
                "category": "bug",
                "action_taken": "Failed: LLM did not call tool",
                "details": {"llm_output": ai_response.content},
            }],
            "messages": [ai_response],
        }

    tool_call = tool_calls[0]
    tool_name = tool_call.get("name", "")
    if tool_name != "create_github_issue":
        return {
            "bug_results": [{
                "id": review_id,
                "category": "bug",
                "action_taken": f"Failed: Unexpected tool call: {tool_name}",
                "details": {"tool_call": tool_call},
            }],
            "messages": [ai_response],
        }

    tool_args = tool_call.get("args", {}) or {}
    title = tool_args.get("title") or f"Bug report from review {review_id}"
    body = tool_args.get("body") or f"Review: {review_text}"
    labels = tool_args.get("labels") or ["bug"]
    if isinstance(labels, str):
        labels = [labels]
    issue_result = create_github_issue.invoke({"title": title, "body": body, "labels": labels})

    tool_message = ToolMessage(
        content=str(issue_result),
        tool_call_id=tool_call.get("id", ""),
    )

    # Extract severity from labels
    labels = tool_args.get("labels", [])
    severity = _extract_severity_from_labels(labels)

    return {
        "bug_results": [{
            "id": review_id,
            "category": "bug",
            "action_taken": f"Created GitHub issue #{issue_result.get('issue_number')}",
            "details": {
                "issue": issue_result,
                "severity": severity,
                "labels": labels,
            },
        }],
        "messages": [ai_response, tool_message],
    }


def _extract_severity_from_labels(labels: list[str]) -> str:
    for label in labels:
        lb = label.lower().strip()
        if lb.startswith("severity:"):
            lvl = lb.split("severity:", 1)[1].strip()
            if lvl in {"critical","high","medium","low"}:
                return lvl
    return "medium"
