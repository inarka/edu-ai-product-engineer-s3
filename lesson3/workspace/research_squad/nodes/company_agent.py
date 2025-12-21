"""Company Agent Node - Specialist for company intelligence research.

This agent:
1. Researches company information via Tavily web search
2. Analyzes market position and competitors
3. Returns structured company insights
"""

import os
from tavily import TavilyClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool

from ..state import ResearchState, CompanyData


COMPANY_SYSTEM_PROMPT = """You are a company intelligence specialist. Your job is to:

1. Research company background and industry
2. Analyze market position and competitive landscape
3. Identify key business priorities
4. Find relevant talking points for B2B outreach

When researching a company, provide:
- Company overview (industry, size, key products)
- Recent news or announcements
- Competitive positioning
- Potential pain points or opportunities

Be concise and focus on actionable insights for sales context.
If you don't have real-time data, provide general industry knowledge.
"""


def get_simulated_company(company_name: str) -> dict:
    """Return simulated company data for fallback."""
    return {
        "name": company_name,
        "industry": "Technology",
        "size": "Unknown",
        "description": f"{company_name} - company information not available.",
        "recent_news": [],
        "competitors": [],
        "key_people": [],
        "note": "Simulated data (Tavily API unavailable)",
    }


@tool
def search_company_info(company_name: str) -> dict:
    """Search for company information using Tavily web search.

    USE WHEN: You need to research a company's background, products, or news.

    RETURNS ON SUCCESS: Dict with company data
    RETURNS ON ERROR: Dict with 'error' key

    Args:
        company_name: Name of the company to research

    Returns:
        Company information dict
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        print("TAVILY_API_KEY not set, using simulated data")
        return get_simulated_company(company_name)

    try:
        client = TavilyClient(api_key=api_key)

        # Search for company info - exclude legal pages
        response = client.search(
            query=f'"{company_name}" what does company do product features',
            search_depth="advanced",
            max_results=8,
        )

        # Extract insights from search results
        results = response.get("results", [])
        if not results:
            return get_simulated_company(company_name)

        # Build company profile from search results
        # Filter out legal/policy pages
        descriptions = []
        news_items = []
        sources = []

        skip_keywords = ["privacy", "terms", "cookie", "legal", "policy"]

        for item in results:
            content = item.get("content", "")
            title = item.get("title", "").lower()
            url = item.get("url", "").lower()

            # Skip legal/policy pages
            if any(kw in title or kw in url for kw in skip_keywords):
                continue

            if content:
                descriptions.append(content[:300])
            if item.get("title"):
                news_items.append(item.get("title"))
            if item.get("url"):
                sources.append(item.get("url"))

        return {
            "name": company_name,
            "industry": "Technology/AI",  # Default, LLM will refine
            "size": "Startup",  # Default for AI companies
            "description": " ".join(descriptions[:2]) if descriptions else f"Information about {company_name}",
            "recent_news": news_items[:3],
            "competitors": [],  # LLM will analyze
            "key_people": [],  # LLM will extract
            "sources": sources[:3],
        }

    except Exception as e:
        print(f"Tavily company search error: {e}, using simulated data")
        return get_simulated_company(company_name)


def extract_company_data(response: dict) -> CompanyData:
    """Extract structured company data from search response."""
    return CompanyData(
        name=response.get("name", "Unknown"),
        industry=response.get("industry", ""),
        size=response.get("size", ""),
        description=response.get("description", ""),
        recent_news=response.get("recent_news", []),
        competitors=response.get("competitors", []),
        key_people=response.get("key_people", []),
    )


async def company_agent_node(state: ResearchState) -> dict:
    """Research company intelligence and extract insights.

    This is a complete agent with:
    - Its own LLM instance
    - Its own tools (company search)
    - Its own system prompt

    Args:
        state: Current research state

    Returns:
        State update with company_data and messages
    """
    company_name = state.get("company_name", "")

    # Try to extract company from LinkedIn data if not provided
    if not company_name and state.get("linkedin_data"):
        company_name = state["linkedin_data"].get("company", "")

    if not company_name:
        return {
            "company_data": None,
            "messages": [AIMessage(content="No company name available for research.")],
        }

    # Create agent with tools
    # Using a smaller, faster model for data extraction tasks
    # Subagents can use cheaper models since they have focused, simpler tasks
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0, stream_usage=True)
    llm_with_tools = llm.bind_tools([search_company_info])

    # Research company
    messages = [
        SystemMessage(content=COMPANY_SYSTEM_PROMPT),
        HumanMessage(content=f"Research this company: {company_name}"),
    ]

    response = await llm_with_tools.ainvoke(messages)

    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_result = search_company_info.invoke(tool_call["args"])

        if "error" in tool_result:
            return {
                "company_data": None,
                "messages": [
                    AIMessage(content=f"Company research failed: {tool_result['error']}")
                ],
            }

        company_data = extract_company_data(tool_result)

        # Analyze with LLM
        analysis_messages = [
            SystemMessage(content=COMPANY_SYSTEM_PROMPT),
            HumanMessage(content=f"Analyze this company data: {tool_result}"),
        ]

        analysis = await llm.ainvoke(analysis_messages)

        return {
            "company_data": company_data,
            "messages": [
                AIMessage(content=f"Company research complete for {company_name}"),
                analysis,
            ],
        }
    else:
        return {
            "company_data": None,
            "messages": [response],
        }
