"""Deep Research Agent - Dynamic planning alternative to W3's LangGraph.

This module demonstrates the Deep Agents approach:
1. Dynamic planning with write_todos (runtime task planning)
2. File system for context management (avoid context overflow)
3. Subagent spawning for specialization

Key difference from W3 Research Squad:
- W3: Static graph edges defined at compile time
- W4: Agent dynamically plans what research to do based on the task

Example:
    python deep_research_agent.py --target "satya-nadella" --company "Microsoft"
"""

import os
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langchain_core.tools import tool
from langsmith import traceable
import httpx

load_dotenv()

# LangSmith configuration
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "lesson4-deep-research")


# === TOOLS ===
# These are the same tools from W3, but now the agent decides WHEN to use them

@tool
@traceable(name="fetch_linkedin")
def fetch_linkedin(url: str) -> dict:
    """Fetch LinkedIn profile data from EnrichLayer API.

    USE WHEN: You need detailed professional background on a person.
    RETURNS: Dict with name, title, company, experience, skills.

    Args:
        url: LinkedIn profile URL (e.g., "https://linkedin.com/in/satya-nadella")
    """
    api_key = os.getenv("ENRICHLAYER_API_KEY")

    if not api_key:
        # Return mock data for demo purposes
        return {
            "name": "Demo User",
            "title": "CEO",
            "company": "Demo Corp",
            "location": "San Francisco, CA",
            "summary": "Experienced technology leader...",
            "experience": [
                {"title": "CEO", "company": "Demo Corp", "duration": "5 years"},
                {"title": "VP Engineering", "company": "Previous Co", "duration": "3 years"},
            ],
            "skills": ["Leadership", "Strategy", "Technology"],
            "mock": True,
        }

    try:
        response = httpx.get(
            "https://enrichlayer.com/api/v2/linkedin",
            params={"url": url},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


@tool
@traceable(name="web_search")
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web for recent information using Tavily.

    USE WHEN: You need current news, market trends, or recent company updates.
    RETURNS: List of search results with title, url, and snippet.

    Args:
        query: Search query (e.g., "Microsoft AI announcements 2024")
        max_results: Maximum results to return (default 5)
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        # Return mock data for demo
        return [
            {
                "title": f"Latest news about {query}",
                "url": "https://example.com/news",
                "snippet": f"Recent developments regarding {query}...",
                "mock": True,
            }
        ]

    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": True,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except Exception as e:
        return [{"error": str(e)}]


@tool
@traceable(name="analyze_company")
def analyze_company(company_name: str) -> dict:
    """Analyze a company's market position and recent activity.

    USE WHEN: You need company-level intelligence (not person-level).
    RETURNS: Dict with industry, size, competitors, recent news.

    Args:
        company_name: Company name to analyze (e.g., "Microsoft")
    """
    # In production, this would call a company intelligence API
    # For demo, we return structured mock data
    return {
        "name": company_name,
        "industry": "Technology",
        "size": "10,000+ employees",
        "description": f"{company_name} is a leading technology company...",
        "recent_initiatives": [
            "AI product launches",
            "Cloud expansion",
            "Strategic acquisitions",
        ],
        "competitors": ["Competitor A", "Competitor B", "Competitor C"],
        "mock": True,
    }


# === DEEP AGENT CONFIGURATION ===

RESEARCH_SYSTEM_PROMPT = """You are an expert B2B sales researcher with filesystem access.

You have access to the project filesystem. File paths start with "/" (e.g., "/context/notes.md").

## Your Workflow (follow exactly)

### Step 1: Plan with write_todos
Create your research plan using write_todos.

### Step 2: Gather data and SAVE to files
After EACH tool call, immediately save results to a file:

1. Call fetch_linkedin(...)
2. Then call write_file("/context/linkedin_profile.md", "# LinkedIn Profile\\n" + results)

3. Call web_search(...)
4. Then call write_file("/context/news_findings.md", "# Recent News\\n" + results)

5. Call analyze_company(...)
6. Then call write_file("/context/company_analysis.md", "# Company Analysis\\n" + results)

### Step 3: Write final report
After gathering all data, write your synthesis:

write_file("/artifacts/final_report.md", "# Sales Intelligence Report\\n...")

## Output Format

Your final report should include:
- Executive Summary (2-3 sentences)
- Key Insights (bulleted list)
- Recommended Talking Points (for sales call)
- Sources (list of data sources used)

## IMPORTANT
You MUST call write_file after each data gathering step.
"""

# Subagent configurations for specialized research
LINKEDIN_SPECIALIST = {
    "name": "linkedin-analyst",
    "description": "Deep analysis of LinkedIn profiles and career trajectories",
    "model": "anthropic:claude-sonnet-4-5-20250929",  # Cost-optimized
    "tools": [fetch_linkedin],
    "system_prompt": """You are a LinkedIn profile analyst.

Focus on:
- Career trajectory patterns
- Skills and expertise areas
- Company tenure and transitions
- Leadership indicators

Be concise - output structured insights, not raw data.""",
}

NEWS_SPECIALIST = {
    "name": "news-researcher",
    "description": "Research recent news, market trends, and company updates",
    "model": "anthropic:claude-sonnet-4-5-20250929",
    "tools": [web_search],
    "system_prompt": """You are a market intelligence researcher.

Focus on:
- Recent company announcements
- Industry trends
- Competitive moves
- Market opportunities

Prioritize recency and relevance to B2B sales.""",
}


# Workspace directory for file system context
WORKSPACE_DIR = Path(__file__).parent / "research_workspace"


def create_deep_research_agent():
    """Create and configure the Deep Research Agent.

    This agent uses:
    - Dynamic planning (write_todos)
    - File system for context management (writes to ./research_workspace/)
    - Subagents for specialized research

    The FilesystemBackend enables the agent to:
    - Write intermediate findings to files (avoids context overflow)
    - Read back context when needed
    - Persist todos and artifacts locally

    Returns:
        Configured DeepAgent CompiledStateGraph
    """
    # Ensure workspace directory exists
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)

    # Configure filesystem backend for local file storage
    # virtual_mode=True ensures /path resolves to workspace/path (not system root)
    backend = FilesystemBackend(root_dir=str(WORKSPACE_DIR), virtual_mode=True)

    agent = create_deep_agent(
        name="research-orchestrator",
        model="anthropic:claude-sonnet-4-5-20250929",  # Main orchestrator
        system_prompt=RESEARCH_SYSTEM_PROMPT,
        tools=[fetch_linkedin, web_search, analyze_company],
        subagents=[LINKEDIN_SPECIALIST, NEWS_SPECIALIST],
        backend=backend,  # Enable file system context management
    )

    return agent


async def run_research(
    target: str,
    company: str = "",
    focus: str = "",
) -> dict[str, Any]:
    """Run deep research on a target.

    Unlike W3's static graph, this agent:
    1. Dynamically plans research steps
    2. Adjusts based on findings
    3. Manages context via file system

    Args:
        target: LinkedIn URL or person identifier
        company: Company name (optional)
        focus: Specific research focus (optional)

    Returns:
        Research results with final report
    """
    agent = create_deep_research_agent()

    # Build the research request
    task = f"Research {target}"
    if company:
        task += f" at {company}"
    if focus:
        task += f". Focus on: {focus}"
    task += ". Produce a comprehensive B2B sales intelligence report."

    print("\n" + "=" * 60)
    print("DEEP RESEARCH AGENT")
    print("=" * 60)
    print(f"\nTask: {task}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)

    # Run the agent using invoke with messages format
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": task}]
    })

    return result


def print_workspace_files() -> None:
    """Show files created in the workspace directory."""
    print("\n" + "=" * 60)
    print("WORKSPACE FILES (File System Context)")
    print("=" * 60)
    print(f"Location: {WORKSPACE_DIR}")
    print("-" * 60)

    if not WORKSPACE_DIR.exists():
        print("  (workspace not created yet)")
        return

    files_found = False
    for path in sorted(WORKSPACE_DIR.rglob("*")):
        if path.is_file():
            files_found = True
            rel_path = path.relative_to(WORKSPACE_DIR)
            size = path.stat().st_size
            print(f"  {rel_path} ({size} bytes)")

    if not files_found:
        print("  (no files created yet)")


def print_results(result: dict[str, Any]) -> None:
    """Pretty print research results."""
    print("\n" + "=" * 60)
    print("RESEARCH RESULTS")
    print("=" * 60)

    # Check for files in agent state (StateBackend stores files here)
    files_in_state = result.get("files", {})
    if files_in_state:
        print("\n--- Files in Agent State ---")
        for path, content in files_in_state.items():
            preview = content[:100] + "..." if len(content) > 100 else content
            print(f"  {path}: {preview}")

    # The real SDK returns messages in a specific format
    messages = result.get("messages", [])

    # Print message count
    print(f"\nTotal messages in conversation: {len(messages)}")

    # Print tool calls (if visible in messages)
    tool_calls = []
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_calls.extend(msg.tool_calls)
        elif isinstance(msg, dict) and msg.get("tool_calls"):
            tool_calls.extend(msg["tool_calls"])

    if tool_calls:
        print("\n--- Tool Calls ---")
        for tc in tool_calls:
            name = tc.get("name", tc.get("function", {}).get("name", "unknown"))
            print(f"  - {name}")

    # Print final response (last AI message)
    if messages:
        final_msg = messages[-1]
        content = getattr(final_msg, "content", None) or (final_msg.get("content") if isinstance(final_msg, dict) else str(final_msg))

        print("\n" + "=" * 60)
        print("FINAL REPORT")
        print("=" * 60)
        print(content if content else "No content in final message")

    print("\n" + "=" * 60)
    print("Research complete!")
    print("=" * 60)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Deep Research Agent - Dynamic B2B Sales Intelligence"
    )
    parser.add_argument(
        "--target",
        type=str,
        required=True,
        help="LinkedIn URL or person identifier to research"
    )
    parser.add_argument(
        "--company",
        type=str,
        default="",
        help="Company name (optional)"
    )
    parser.add_argument(
        "--focus",
        type=str,
        default="",
        help="Specific research focus (optional)"
    )

    args = parser.parse_args()

    result = asyncio.run(run_research(
        target=args.target,
        company=args.company,
        focus=args.focus,
    ))

    print_results(result)

    # Show what files the agent created in the workspace
    print_workspace_files()

    # Print LangSmith link
    print(f"\nView trace in LangSmith: https://smith.langchain.com")
    print(f"Project: {os.getenv('LANGCHAIN_PROJECT', 'lesson4-deep-research')}")


if __name__ == "__main__":
    main()
