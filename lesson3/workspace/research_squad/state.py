"""State definition for the Research Squad.

This is the shared contract between all agents in the squad.
Each agent receives the full state and returns partial updates.
"""

from typing import TypedDict, Annotated
from langgraph.graph import add_messages


class LinkedInData(TypedDict, total=False):
    """Structured LinkedIn profile data."""
    name: str
    title: str
    company: str
    location: str
    summary: str
    experience: list[dict]
    skills: list[str]
    connections: int
    raw_response: dict


class CompanyData(TypedDict, total=False):
    """Structured company intelligence."""
    name: str
    industry: str
    size: str
    description: str
    recent_news: list[str]
    competitors: list[str]
    key_people: list[str]


class NewsItem(TypedDict):
    """A single news item."""
    title: str
    source: str
    date: str
    summary: str
    url: str


class ResearchState(TypedDict, total=False):
    """The shared state for the Research Squad.

    Organized into sections:
    - INPUT: What the user provides
    - AGENT RESULTS: What each specialist produces
    - SYNTHESIS: Combined analysis
    - MESSAGES: Conversation history with reducers
    - CONTROL: Flow control flags
    """

    # === INPUT ===
    linkedin_url: str
    company_name: str

    # === AGENT RESULTS ===
    linkedin_data: LinkedInData | None
    company_data: CompanyData | None
    news_data: list[NewsItem] | None

    # === SYNTHESIS ===
    conflicts: list[str]  # Conflicting information between sources
    insights: list[str]   # Key insights discovered
    final_report: str

    # === MESSAGES ===
    # Using add_messages reducer: new messages append, don't replace
    messages: Annotated[list, add_messages]

    # === CONTROL ===
    human_approved: bool
    validation_result: dict | None
