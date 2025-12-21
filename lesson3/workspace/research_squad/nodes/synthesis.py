"""Synthesis Node - Combines results from all specialist agents.

This node:
1. Receives results from LinkedIn, Company, and News agents
2. Identifies conflicts or inconsistencies
3. Generates a comprehensive research report
4. Optionally requests human approval before finalizing
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from ..state import ResearchState


SYNTHESIS_SYSTEM_PROMPT = """You are a research synthesis specialist. Your job is to:

1. Combine insights from multiple research sources
2. Identify any conflicts or inconsistencies
3. Generate a comprehensive, actionable research report
4. Highlight key talking points for B2B outreach

The report should include:
- Executive Summary (2-3 sentences)
- Profile Overview (from LinkedIn data)
- Company Context (from company research)
- Recent News & Trends (from news research)
- Recommended Talking Points (3-5 bullets)
- Potential Concerns or Gaps

Be concise but comprehensive. Focus on actionable insights.
"""


async def synthesis_node(state: ResearchState) -> dict:
    """Synthesize all research into a comprehensive report.

    This node:
    1. Collects results from all parallel agents
    2. Uses LLM to synthesize into coherent report
    3. Identifies any conflicts between sources

    Args:
        state: Current research state with all agent results

    Returns:
        State update with final_report and insights
    """
    linkedin_data = state.get("linkedin_data")
    company_data = state.get("company_data")
    news_data = state.get("news_data")

    # Prepare context for synthesis
    context_parts = []

    if linkedin_data:
        context_parts.append(f"""
LINKEDIN DATA:
- Name: {linkedin_data.get('name', 'Unknown')}
- Title: {linkedin_data.get('title', 'Unknown')}
- Company: {linkedin_data.get('company', 'Unknown')}
- Location: {linkedin_data.get('location', 'Unknown')}
- Summary: {linkedin_data.get('summary', 'Not available')}
- Skills: {', '.join(linkedin_data.get('skills', [])[:10])}
""")
    else:
        context_parts.append("LINKEDIN DATA: Not available")

    if company_data:
        context_parts.append(f"""
COMPANY DATA:
- Name: {company_data.get('name', 'Unknown')}
- Industry: {company_data.get('industry', 'Unknown')}
- Size: {company_data.get('size', 'Unknown')}
- Description: {company_data.get('description', 'Not available')}
- Recent News: {'; '.join(company_data.get('recent_news', [])[:3])}
- Competitors: {', '.join(company_data.get('competitors', [])[:5])}
""")
    else:
        context_parts.append("COMPANY DATA: Not available")

    if news_data:
        news_summary = "\n".join([
            f"- {item['title']} ({item['source']}, {item['date']})"
            for item in news_data[:5]
        ])
        context_parts.append(f"""
NEWS DATA:
{news_summary}
""")
    else:
        context_parts.append("NEWS DATA: Not available")

    context = "\n".join(context_parts)

    # Identify conflicts
    conflicts = []
    if linkedin_data and company_data:
        li_company = linkedin_data.get("company", "").lower()
        co_name = company_data.get("name", "").lower()
        if li_company and co_name and li_company != co_name:
            conflicts.append(
                f"Company mismatch: LinkedIn shows '{linkedin_data.get('company')}' "
                f"but researched '{company_data.get('name')}'"
            )

    # Synthesis requires complex reasoning - use the most capable model
    # This is where we need the full power of gpt-5.2
    llm = ChatOpenAI(model="gpt-5.2", temperature=0, stream_usage=True)

    messages = [
        SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
        HumanMessage(content=f"""
Please synthesize the following research data into a comprehensive report:

{context}

{"NOTED CONFLICTS: " + "; ".join(conflicts) if conflicts else "No conflicts detected."}

Generate a structured research report suitable for B2B sales outreach preparation.
"""),
    ]

    response = await llm.ainvoke(messages)

    # Extract insights
    insights = []
    if linkedin_data:
        insights.append(f"Target: {linkedin_data.get('name', 'Unknown')} at {linkedin_data.get('company', 'Unknown')}")
    if company_data and company_data.get("industry"):
        insights.append(f"Industry: {company_data.get('industry')}")
    if news_data:
        insights.append(f"Recent activity: {len(news_data)} news items found")

    return {
        "final_report": response.content,
        "conflicts": conflicts,
        "insights": insights,
        "messages": [
            AIMessage(content="Research synthesis complete."),
            response,
        ],
    }
