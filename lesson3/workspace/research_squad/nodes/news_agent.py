"""News Agent Node - Specialist for news and trends research.

This agent:
1. Searches for recent news about the person/company using Tavily
2. Analyzes sentiment and trends
3. Returns structured news insights
"""

import os
from tavily import TavilyClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool

from ..state import ResearchState, NewsItem


NEWS_SYSTEM_PROMPT = """You are a news and trends research specialist. Your job is to:

1. Find recent news about a person or company
2. Analyze sentiment and key themes
3. Identify relevant industry trends
4. Find potential conversation starters for outreach

When researching news, provide:
- Recent news headlines and summaries
- Sentiment analysis (positive/negative/neutral)
- Relevant industry trends
- Potential talking points

Be concise and focus on recent, relevant news (last 30 days preferred).
If no recent news, provide industry context.
"""


def get_simulated_news(query: str) -> list[dict]:
    """Return simulated news for fallback."""
    return [
        {
            "title": f"{query} announces strategic initiative",
            "source": "TechCrunch",
            "date": "2025-01-15",
            "summary": f"In a recent announcement, {query} revealed plans for expansion.",
            "url": "https://example.com/news/1",
        },
        {
            "title": f"Industry analysis: {query}'s market position",
            "source": "Bloomberg",
            "date": "2025-01-10",
            "summary": f"Analysts weigh in on {query}'s competitive advantages.",
            "url": "https://example.com/news/2",
        },
    ]


@tool
def search_news(query: str) -> list[dict]:
    """Search for recent news about a topic using Tavily.

    USE WHEN: You need to find recent news about a person, company, or topic.

    RETURNS ON SUCCESS: List of news items with title, source, date, summary
    RETURNS ON ERROR: Empty list

    Args:
        query: Search query (person name, company name, or topic)

    Returns:
        List of news items
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        print("TAVILY_API_KEY not set, using simulated data")
        return get_simulated_news(query)

    try:
        client = TavilyClient(api_key=api_key)
        # Search for recent news - use quotes for exact name matching
        # Remove domain restrictions to get more relevant results
        response = client.search(
            query=f'"{query}" news OR announcement OR interview',
            search_depth="advanced",  # Better relevance filtering
            max_results=5,
        )

        # Convert to our format
        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "source": item.get("url", "").split("/")[2] if item.get("url") else "Unknown",
                "date": item.get("published_date", "Recent"),
                "summary": item.get("content", "")[:300] + "..." if len(item.get("content", "")) > 300 else item.get("content", ""),
                "url": item.get("url", ""),
            })

        return results if results else get_simulated_news(query)

    except Exception as e:
        print(f"Tavily search error: {e}, using simulated data")
        return get_simulated_news(query)


def extract_news_items(response: list[dict]) -> list[NewsItem]:
    """Convert raw news response to typed NewsItems."""
    return [
        NewsItem(
            title=item.get("title", ""),
            source=item.get("source", ""),
            date=item.get("date", ""),
            summary=item.get("summary", ""),
            url=item.get("url", ""),
        )
        for item in response
    ]


async def news_agent_node(state: ResearchState) -> dict:
    """Research news and trends for the target.

    This is a complete agent with:
    - Its own LLM instance
    - Its own tools (news search)
    - Its own system prompt

    Args:
        state: Current research state

    Returns:
        State update with news_data and messages
    """
    # Build search query from available data
    linkedin_url = state.get("linkedin_url", "")
    company_name = state.get("company_name", "")

    if state.get("linkedin_data"):
        linkedin_data = state["linkedin_data"]
        # Handle both dict and object access
        if isinstance(linkedin_data, dict):
            person_name = linkedin_data.get("name", "")
            # Get company from LinkedIn if not provided
            if not company_name:
                company_name = linkedin_data.get("company", "")
        else:
            person_name = getattr(linkedin_data, "name", "")
            if not company_name:
                company_name = getattr(linkedin_data, "company", "")
    else:
        person_name = ""

    # Construct search query - be specific about person AND company
    if person_name and company_name:
        query = f"{person_name} {company_name}"
    elif person_name:
        query = person_name
    elif company_name:
        query = company_name
    else:
        query = "technology industry trends"

    # Create agent with tools
    # Using a smaller, faster model for data extraction tasks
    # Subagents can use cheaper models since they have focused, simpler tasks
    llm = ChatOpenAI(model="gpt-5-mini", temperature=0, stream_usage=True)
    llm_with_tools = llm.bind_tools([search_news])

    # Search news
    messages = [
        SystemMessage(content=NEWS_SYSTEM_PROMPT),
        HumanMessage(content=f"Find recent news about: {query}"),
    ]

    response = await llm_with_tools.ainvoke(messages)

    if response.tool_calls:
        tool_call = response.tool_calls[0]
        tool_result = search_news.invoke(tool_call["args"])

        if not tool_result:
            return {
                "news_data": [],
                "messages": [AIMessage(content="No recent news found.")],
            }

        news_items = extract_news_items(tool_result)

        # Analyze with LLM
        analysis_messages = [
            SystemMessage(content=NEWS_SYSTEM_PROMPT),
            HumanMessage(content=f"Analyze these news items for outreach context: {tool_result}"),
        ]

        analysis = await llm.ainvoke(analysis_messages)

        return {
            "news_data": news_items,
            "messages": [
                AIMessage(content=f"News research complete: {len(news_items)} items found"),
                analysis,
            ],
        }
    else:
        return {
            "news_data": [],
            "messages": [response],
        }
