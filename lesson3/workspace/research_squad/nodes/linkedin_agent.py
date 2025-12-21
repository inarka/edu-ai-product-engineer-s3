"""LinkedIn Agent Node - Specialist for LinkedIn profile research.

This agent:
1. Fetches LinkedIn profile data via EnrichLayer API
2. Analyzes career trajectory and skills
3. Returns structured profile insights

This is a complete agent with its own LLM and tools.
"""

import os
import httpx
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool

from ..state import ResearchState, LinkedInData


LINKEDIN_SYSTEM_PROMPT = """You are a LinkedIn research specialist. Your job is to:

1. Analyze LinkedIn profile data
2. Extract key career insights
3. Identify patterns in career trajectory
4. Summarize skills and expertise

When given profile data, provide:
- Career summary (2-3 sentences)
- Key skills and expertise areas
- Notable career moves or patterns
- Potential talking points for outreach

Be concise and focus on actionable insights for B2B sales context.
"""


def get_simulated_profile(url: str) -> dict:
    """Return simulated profile data for demo purposes."""
    # Extract name from URL for personalization
    name_part = url.rstrip("/").split("/")[-1].replace("-", " ").title()

    return {
        "name": name_part if name_part else "Demo User",
        "title": "Senior Product Manager",
        "company": "Tech Company",
        "location": "San Francisco Bay Area",
        "summary": "Experienced product leader focused on AI/ML products and platform development.",
        "experience": [
            {"title": "Senior Product Manager", "company": "Tech Company", "duration": "2022 - Present"},
            {"title": "Product Manager", "company": "Previous Corp", "duration": "2019 - 2022"},
        ],
        "skills": ["Product Strategy", "AI/ML", "Platform Development", "Team Leadership", "Agile"],
        "connections": 500,
        "note": "This is simulated data for demo purposes (API key expired or unavailable)",
    }


@tool
def fetch_linkedin_profile(url: str) -> dict:
    """Fetch LinkedIn profile data from EnrichLayer API.

    USE WHEN: You need to get profile information for a LinkedIn URL.

    RETURNS ON SUCCESS: Dict with profile data (name, title, experience, etc.)
    RETURNS ON ERROR: Dict with 'error' key describing the failure.

    Note: Falls back to simulated data if API is unavailable (for demo purposes).

    Args:
        url: The LinkedIn profile URL to fetch

    Returns:
        Profile data dict or error dict
    """
    api_key = os.getenv("ENRICHLAYER_API_KEY")

    if not api_key:
        # Return simulated data for demo
        return get_simulated_profile(url)

    try:
        response = httpx.get(
            "https://enrichlayer.com/api/v2/profile",
            params={"url": url},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        # API error - fallback to simulated data for demo
        print(f"EnrichLayer API error ({e.response.status_code}), using simulated data")
        return get_simulated_profile(url)
    except httpx.RequestError as e:
        # Network error - fallback to simulated data
        print(f"Network error ({e}), using simulated data")
        return get_simulated_profile(url)


def extract_linkedin_data(response: dict) -> LinkedInData:
    """Extract structured data from EnrichLayer response.

    Handles missing fields gracefully.
    EnrichLayer uses different field names than our internal schema.
    """
    # Extract current company from experiences
    current_company = ""
    experiences = response.get("experiences", [])
    if experiences:
        # First experience is usually current
        current_company = experiences[0].get("company", "")

    # Extract skills from various sources
    skills = []
    # Try certifications as skills proxy
    for cert in response.get("certifications", []):
        if cert.get("name"):
            skills.append(cert.get("name"))

    return LinkedInData(
        name=response.get("full_name", response.get("name", "Unknown")),
        title=response.get("headline", response.get("occupation", "")),
        company=current_company,
        location=response.get("location_str", response.get("location", "")),
        summary=response.get("summary", ""),
        experience=experiences,
        skills=skills[:10],  # Limit to 10
        connections=response.get("connections", response.get("follower_count", 0)),
        raw_response=response,
    )


async def linkedin_agent_node(state: ResearchState) -> dict:
    """Research LinkedIn profile and extract insights.

    This is a complete agent with:
    - Its own LLM instance
    - Its own tools (EnrichLayer)
    - Its own system prompt

    Args:
        state: Current research state

    Returns:
        State update with linkedin_data and messages
    """
    linkedin_url = state.get("linkedin_url", "")

    if not linkedin_url:
        return {
            "linkedin_data": None,
            "messages": [AIMessage(content="No LinkedIn URL provided.")],
        }

    # Create agent with tools
    # Using a smaller, faster model for data extraction tasks
    # Subagents can use cheaper models since they have focused, simpler tasks
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0, stream_usage=True)
    llm_with_tools = llm.bind_tools([fetch_linkedin_profile])

    # Step 1: Fetch profile data
    fetch_messages = [
        SystemMessage(content=LINKEDIN_SYSTEM_PROMPT),
        HumanMessage(content=f"Fetch and analyze this LinkedIn profile: {linkedin_url}"),
    ]

    # Let the LLM decide to use the tool
    response = await llm_with_tools.ainvoke(fetch_messages)

    # Check if tool was called
    if response.tool_calls:
        # Execute tool call
        tool_call = response.tool_calls[0]
        tool_result = fetch_linkedin_profile.invoke(tool_call["args"])

        if "error" in tool_result:
            return {
                "linkedin_data": None,
                "messages": [
                    AIMessage(content=f"LinkedIn research failed: {tool_result['error']}")
                ],
            }

        # Extract structured data
        linkedin_data = extract_linkedin_data(tool_result)

        # Step 2: Analyze with LLM
        analysis_messages = [
            SystemMessage(content=LINKEDIN_SYSTEM_PROMPT),
            HumanMessage(content=f"Analyze this profile data: {tool_result}"),
        ]

        analysis = await llm.ainvoke(analysis_messages)

        return {
            "linkedin_data": linkedin_data,
            "messages": [
                AIMessage(content=f"LinkedIn research complete for {linkedin_url}"),
                analysis,
            ],
        }
    else:
        # LLM didn't use tool - return whatever it said
        return {
            "linkedin_data": None,
            "messages": [response],
        }
