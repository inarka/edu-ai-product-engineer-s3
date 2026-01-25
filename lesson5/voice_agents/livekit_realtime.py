"""
Voice Agent using LiveKit + OpenAI Realtime API

This example demonstrates a voice assistant that:
1. Uses LiveKit for real-time audio streaming
2. Uses OpenAI's Realtime API for speech-to-speech
3. Supports tool calling for sales data queries

Prerequisites:
- LiveKit Cloud account (or self-hosted server)
- OpenAI API key with Realtime API access
- Run test_setup.py first to verify configuration

Run:
    python voice_agents/livekit_realtime.py

Then connect via LiveKit Playground or your own client.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

# LiveKit imports
try:
    from livekit import rtc
    from livekit.agents import Agent, AgentSession, AutoSubscribe, JobContext, WorkerOptions, cli, function_tool
    from livekit.plugins import openai, silero
except ImportError:
    print("Error: LiveKit packages not installed.")
    print("Run: pip install livekit livekit-agents livekit-plugins-openai livekit-plugins-silero")
    sys.exit(1)


# =============================================================================
# Tools for the Voice Agent
# =============================================================================

@function_tool(
    description="""Get the response rate for outreach campaigns.
    Call this when the user asks about response rates, reply rates,
    or how campaigns are performing."""
)
async def get_response_rate(time_period: str = "last_week") -> str:
    """Get response rate for a time period.

    Args:
        time_period: One of 'today', 'last_week', 'last_month', 'all_time'
    """
    # Mock data - replace with real AutoReach API call
    rates = {
        "today": {"rate": 4.2, "sent": 150, "responses": 6},
        "last_week": {"rate": 3.8, "sent": 1200, "responses": 46},
        "last_month": {"rate": 3.5, "sent": 4800, "responses": 168},
        "all_time": {"rate": 3.2, "sent": 25000, "responses": 800},
    }

    data = rates.get(time_period, rates["last_week"])
    return (
        f"For {time_period.replace('_', ' ')}: "
        f"Response rate is {data['rate']}%. "
        f"We sent {data['sent']} messages and received {data['responses']} responses."
    )


@function_tool(
    description="""Get the top performing email templates.
    Call this when the user asks about best templates,
    which messages work best, or template performance."""
)
async def get_top_templates(limit: int = 3) -> str:
    """Get top performing templates by response rate.

    Args:
        limit: Number of templates to return (1-10)
    """
    # Mock data - replace with real AutoReach API call
    templates = [
        {"name": "Direct Question", "rate": 5.2, "uses": 3200},
        {"name": "Industry Insight", "rate": 4.8, "uses": 2100},
        {"name": "Mutual Connection", "rate": 4.5, "uses": 1800},
        {"name": "Recent News Hook", "rate": 4.1, "uses": 950},
        {"name": "Problem Statement", "rate": 3.9, "uses": 1500},
    ]

    top = templates[:min(limit, len(templates))]
    result = "Top performing templates:\n"
    for i, t in enumerate(top, 1):
        result += f"{i}. {t['name']}: {t['rate']}% response rate ({t['uses']} uses)\n"

    return result


@function_tool(
    description="""Get recent positive responses from prospects.
    Call this when the user asks about interested leads,
    positive replies, or who's engaging."""
)
async def get_positive_responses(limit: int = 5) -> str:
    """Get recent positive responses.

    Args:
        limit: Number of responses to return (1-20)
    """
    # Mock data - replace with real AutoReach API call
    responses = [
        {"name": "Sarah Chen", "company": "TechCorp", "snippet": "Yes, I'd be interested in learning more..."},
        {"name": "Mike Rodriguez", "company": "DataFlow", "snippet": "This looks relevant to our needs..."},
        {"name": "Emily Watson", "company": "CloudBase", "snippet": "Let's schedule a call next week..."},
        {"name": "James Park", "company": "AI Solutions", "snippet": "Can you send more details?"},
        {"name": "Lisa Thompson", "company": "StartupXYZ", "snippet": "Forwarding to our head of sales..."},
    ]

    top = responses[:min(limit, len(responses))]
    result = f"Recent positive responses ({len(top)} shown):\n\n"
    for r in top:
        result += f"- {r['name']} ({r['company']}): \"{r['snippet']}\"\n"

    return result


# =============================================================================
# Voice Agent Entry Point
# =============================================================================

async def entrypoint(ctx: JobContext):
    """Main entry point for the voice agent.

    This function is called by LiveKit when a participant joins the room.
    """
    # Wait for connection
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    print(f"Connected to room: {ctx.room.name}")
    print("Waiting for participant...")

    # Wait for a participant to join
    participant = await ctx.wait_for_participant()
    print(f"Participant joined: {participant.identity}")

    # System prompt for the voice assistant
    system_prompt = """You are a helpful sales analytics assistant for AutoReach.

Your role is to help sales teams understand their outreach performance.

<guidelines>
- Be conversational and natural - you're a voice assistant
- Keep responses concise (2-3 sentences max for voice)
- When giving numbers, round appropriately for voice
- If asked about something outside your tools, politely redirect
- Proactively offer to dig deeper or compare time periods
</guidelines>

<available_data>
You can access:
- Response rates for different time periods
- Top performing email templates
- Recent positive responses from prospects
</available_data>

<examples>
User: "How did we do last week?"
You: "Last week you had a 3.8% response rate - that's 46 responses from 1,200 messages sent. Would you like to see which templates performed best?"

User: "Show me the interested leads"
You: "Here are your recent positive responses. Sarah Chen from TechCorp said she's interested in learning more. Mike Rodriguez at DataFlow mentioned this looks relevant. And Emily Watson wants to schedule a call next week. Want me to focus on any of these?"
</examples>
"""

    # Create the voice agent
    # Using OpenAI Realtime API for lowest latency
    agent = Agent(
        instructions=system_prompt,
        vad=silero.VAD.load(),  # Voice Activity Detection
        stt=openai.STT(model="whisper-1"),
        llm=openai.realtime.RealtimeModel(
            voice="alloy",
            temperature=0.8,
        ),
        tts=openai.TTS(voice="alloy"),
        tools=[get_response_rate, get_top_templates, get_positive_responses],
    )

    # Create and start the agent session
    session = AgentSession()
    await session.start(agent, room=ctx.room)

    # Initial greeting
    await session.say(
        "Hi! I'm your AutoReach analytics assistant. "
        "Ask me about response rates, top templates, or interested leads.",
        allow_interruptions=True
    )


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    # Verify environment
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        print("Copy .env.example to .env and add your API key")
        sys.exit(1)

    if not os.getenv("LIVEKIT_URL"):
        print("Error: LiveKit credentials not set")
        print("Set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET in .env")
        sys.exit(1)

    print("Starting Voice Agent...")
    print(f"LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    print("\nConnect via LiveKit Playground or your client to start talking.")
    print("Ctrl+C to stop.\n")

    # Run the agent
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
