"""
Sales Voice Data Analyst - Homework Starter Template

Build a voice assistant for AutoReach performance analysis.

Your Tasks:
1. Complete the TODOs marked below
2. Add Task orchestration for multi-step queries
3. Test with the required voice queries
4. Create a demo video

Run:
    python homework/sales_voice_analyst.py

Requirements:
    - OpenAI API key (for Realtime API or STT/TTS)
    - LiveKit credentials (if using Option A)
    - Anthropic API key (if using Option B)
"""

import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# Mock Data - Replace with real AutoReach API calls
# =============================================================================

class MockAutoReachData:
    """Mock AutoReach data for development. Replace with real API calls."""

    @staticmethod
    def get_response_rates(period: str = "last_week") -> dict:
        """Get response rate metrics.

        Args:
            period: One of 'today', 'last_week', 'last_month', 'last_quarter'

        Returns:
            Dictionary with response rate data
        """
        # TODO: Replace with real AutoReach API call
        data = {
            "today": {
                "response_rate": 4.2,
                "sent": 150,
                "responses": 6,
                "open_rate": 42.0,
                "period_label": "today"
            },
            "last_week": {
                "response_rate": 3.8,
                "sent": 1200,
                "responses": 46,
                "open_rate": 38.5,
                "period_label": "last week"
            },
            "last_month": {
                "response_rate": 3.5,
                "sent": 4800,
                "responses": 168,
                "open_rate": 35.2,
                "period_label": "last month"
            },
            "last_quarter": {
                "response_rate": 3.2,
                "sent": 14500,
                "responses": 464,
                "open_rate": 33.8,
                "period_label": "last quarter"
            }
        }
        return data.get(period, data["last_week"])

    @staticmethod
    def get_top_templates(limit: int = 5, industry: str | None = None) -> list[dict]:
        """Get top performing templates.

        Args:
            limit: Number of templates to return
            industry: Optional industry filter

        Returns:
            List of template performance data
        """
        # TODO: Replace with real AutoReach API call
        templates = [
            {
                "name": "Direct Question",
                "response_rate": 5.2,
                "uses": 3200,
                "best_industry": "Technology",
                "avg_response_time_hours": 18
            },
            {
                "name": "Industry Insight",
                "response_rate": 4.8,
                "uses": 2100,
                "best_industry": "Finance",
                "avg_response_time_hours": 24
            },
            {
                "name": "Mutual Connection",
                "response_rate": 4.5,
                "uses": 1800,
                "best_industry": "Healthcare",
                "avg_response_time_hours": 36
            },
            {
                "name": "Recent News Hook",
                "response_rate": 4.1,
                "uses": 950,
                "best_industry": "Technology",
                "avg_response_time_hours": 12
            },
            {
                "name": "Problem Statement",
                "response_rate": 3.9,
                "uses": 1500,
                "best_industry": "Manufacturing",
                "avg_response_time_hours": 48
            }
        ]

        if industry:
            templates = [t for t in templates if t["best_industry"].lower() == industry.lower()]

        return templates[:limit]

    @staticmethod
    def get_positive_responses(limit: int = 10) -> list[dict]:
        """Get recent positive responses.

        Args:
            limit: Number of responses to return

        Returns:
            List of positive response data
        """
        # TODO: Replace with real AutoReach API call
        responses = [
            {
                "name": "Sarah Chen",
                "company": "TechCorp",
                "title": "VP of Sales",
                "snippet": "Yes, I'd be interested in learning more about your solution...",
                "sentiment_score": 0.85,
                "received_at": "2024-01-15T10:30:00Z",
                "template_used": "Direct Question"
            },
            {
                "name": "Mike Rodriguez",
                "company": "DataFlow Inc",
                "title": "Head of Revenue",
                "snippet": "This looks relevant to our needs. Can we schedule a call?",
                "sentiment_score": 0.92,
                "received_at": "2024-01-15T09:15:00Z",
                "template_used": "Industry Insight"
            },
            {
                "name": "Emily Watson",
                "company": "CloudBase",
                "title": "Director of Sales Ops",
                "snippet": "Let's schedule a call next week to discuss further...",
                "sentiment_score": 0.78,
                "received_at": "2024-01-14T16:45:00Z",
                "template_used": "Mutual Connection"
            },
            {
                "name": "James Park",
                "company": "AI Solutions Ltd",
                "title": "CRO",
                "snippet": "Interesting approach. Can you send more details about pricing?",
                "sentiment_score": 0.72,
                "received_at": "2024-01-14T14:20:00Z",
                "template_used": "Recent News Hook"
            },
            {
                "name": "Lisa Thompson",
                "company": "StartupXYZ",
                "title": "Sales Manager",
                "snippet": "Forwarding this to our head of sales. Looks promising!",
                "sentiment_score": 0.80,
                "received_at": "2024-01-14T11:00:00Z",
                "template_used": "Problem Statement"
            }
        ]
        return responses[:limit]

    @staticmethod
    def get_comparison(period1: str, period2: str) -> dict:
        """Compare metrics between two periods.

        Args:
            period1: First period (e.g., 'last_week')
            period2: Second period (e.g., 'last_month')

        Returns:
            Comparison data
        """
        # TODO: Replace with real AutoReach API call
        data1 = MockAutoReachData.get_response_rates(period1)
        data2 = MockAutoReachData.get_response_rates(period2)

        return {
            "period1": data1,
            "period2": data2,
            "response_rate_change": data1["response_rate"] - data2["response_rate"],
            "trend": "up" if data1["response_rate"] > data2["response_rate"] else "down"
        }


# =============================================================================
# Voice Agent Tools
# =============================================================================

# TODO: Implement these tool functions for your voice agent

def format_response_rate_answer(data: dict) -> str:
    """Format response rate data for voice output.

    Args:
        data: Response rate data from API

    Returns:
        Human-friendly response string
    """
    return (
        f"For {data['period_label']}, your response rate was {data['response_rate']}%. "
        f"You sent {data['sent']} messages and received {data['responses']} responses. "
        f"Your open rate was {data['open_rate']}%."
    )


def format_templates_answer(templates: list[dict]) -> str:
    """Format template data for voice output.

    Args:
        templates: List of template data

    Returns:
        Human-friendly response string
    """
    if not templates:
        return "I couldn't find any template data."

    result = f"Here are your top {len(templates)} performing templates. "
    for i, t in enumerate(templates, 1):
        result += (
            f"Number {i}: {t['name']} with a {t['response_rate']}% response rate, "
            f"used {t['uses']} times. "
        )
    return result


def format_positive_responses_answer(responses: list[dict]) -> str:
    """Format positive responses for voice output.

    Args:
        responses: List of positive response data

    Returns:
        Human-friendly response string
    """
    if not responses:
        return "No positive responses found in the selected period."

    result = f"You have {len(responses)} recent positive responses. "
    for r in responses[:3]:  # Limit to 3 for voice
        result += f"{r['name']} from {r['company']} said: {r['snippet'][:50]}. "
    return result


# =============================================================================
# Voice Agent Implementation
# =============================================================================

# TODO: Choose your implementation approach:

# OPTION A: LiveKit + OpenAI Realtime API
# Uncomment and complete the LiveKit implementation below

"""
from livekit.agents import AutoSubscribe, JobContext, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero

class SalesAnalyticsTools(llm.FunctionContext):
    '''Voice-callable tools for sales analytics.'''

    @llm.ai_callable(
        description="Get response rate metrics for a time period"
    )
    async def get_response_rate(self, time_period: str = "last_week") -> str:
        data = MockAutoReachData.get_response_rates(time_period)
        return format_response_rate_answer(data)

    @llm.ai_callable(
        description="Get top performing email templates"
    )
    async def get_top_templates(self, limit: int = 3) -> str:
        templates = MockAutoReachData.get_top_templates(limit)
        return format_templates_answer(templates)

    @llm.ai_callable(
        description="Get recent positive responses from prospects"
    )
    async def get_positive_responses(self, limit: int = 5) -> str:
        responses = MockAutoReachData.get_positive_responses(limit)
        return format_positive_responses_answer(responses)

# TODO: Add more tools as needed for your implementation
"""


# OPTION B: STT → LLM → TTS
# Use the code below as a starting point

async def process_voice_query_stt_llm_tts(audio_file: str) -> str:
    """Process a voice query using STT → LLM → TTS pipeline.

    Args:
        audio_file: Path to audio file with user's query

    Returns:
        Path to audio response file
    """
    # TODO: Implement this function
    # 1. Transcribe audio using Whisper
    # 2. Process query with Claude
    # 3. Synthesize response with TTS
    # 4. Return path to response audio

    # Example implementation (pseudo-code):
    # transcript = await transcribe(audio_file)
    # response = await process_with_claude(transcript)
    # audio_response = await synthesize_speech(response)
    # return audio_response

    pass


# =============================================================================
# Task Orchestration for Complex Queries
# =============================================================================

# TODO: Add task orchestration for multi-step queries

"""
Example: "Give me a full performance review"

This should create a task list like:
1. Task 1: Get response rate metrics (parallel)
2. Task 2: Get top templates (parallel)
3. Task 3: Get positive responses (parallel)
4. Task 4: Synthesize findings (blocked by 1,2,3)

See agent_orchestration/tasks_with_dependencies.py for examples.
"""

from agent_orchestration.tasks_basic import TaskList


async def run_performance_review() -> str:
    """Run a full performance review using task orchestration.

    Returns:
        Synthesized performance review response
    """
    # TODO: Implement task orchestration

    # 1. Create task list
    tasks = TaskList(list_id="voice-review")

    # 2. Create parallel research tasks
    # t1 = tasks.create(...)
    # t2 = tasks.create(...)
    # t3 = tasks.create(...)

    # 3. Create synthesis task with dependencies
    # t4 = tasks.create(..., blocked_by=[t1.id, t2.id, t3.id])

    # 4. Execute tasks in order
    # ...

    # 5. Return synthesized response
    return "Performance review: ..."  # Replace with actual implementation


# =============================================================================
# Main Entry Point
# =============================================================================

async def demo_mode():
    """Run in demo mode to test without voice setup."""
    print("\n" + "=" * 60)
    print(" Sales Voice Analyst - Demo Mode")
    print("=" * 60)
    print("\nThis mode tests the data functions without voice.")
    print("For full voice functionality, complete the TODOs above.\n")

    # Test response rate
    print("Query: 'What was our response rate last week?'")
    data = MockAutoReachData.get_response_rates("last_week")
    print(f"Response: {format_response_rate_answer(data)}\n")

    # Test templates
    print("Query: 'Which templates performed best?'")
    templates = MockAutoReachData.get_top_templates(3)
    print(f"Response: {format_templates_answer(templates)}\n")

    # Test positive responses
    print("Query: 'Show me positive responses'")
    responses = MockAutoReachData.get_positive_responses(5)
    print(f"Response: {format_positive_responses_answer(responses)}\n")

    # Test comparison
    print("Query: 'Compare this week to last month'")
    comparison = MockAutoReachData.get_comparison("last_week", "last_month")
    trend = "improved" if comparison["trend"] == "up" else "declined"
    change = abs(comparison["response_rate_change"])
    print(f"Response: Your response rate has {trend} by {change:.1f} percentage points "
          f"compared to last month.\n")

    print("=" * 60)
    print("Demo complete! Now implement the full voice pipeline.")
    print("=" * 60)


def main():
    """Main entry point."""
    print("\nSales Voice Data Analyst")
    print("=" * 60)

    # Check environment
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_livekit = bool(os.getenv("LIVEKIT_URL"))

    print("\nEnvironment Check:")
    print(f"  OpenAI API Key: {'Found' if has_openai else 'Missing'}")
    print(f"  Anthropic API Key: {'Found' if has_anthropic else 'Missing'}")
    print(f"  LiveKit Credentials: {'Found' if has_livekit else 'Missing'}")

    if not has_openai and not has_anthropic:
        print("\nWarning: No API keys found. Running in demo mode.")
        asyncio.run(demo_mode())
        return

    print("\nModes:")
    print("1. Demo mode (test data functions)")
    print("2. Voice mode (requires completed implementation)")

    choice = input("\nChoice [1/2]: ").strip()

    if choice == "2":
        print("\nVoice mode not yet implemented.")
        print("Complete the TODOs in this file to enable voice mode.")
        print("Falling back to demo mode...\n")

    asyncio.run(demo_mode())


if __name__ == "__main__":
    main()
