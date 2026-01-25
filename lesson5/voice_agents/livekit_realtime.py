"""
Voice Agent using LiveKit + OpenAI Realtime API or Gemini Live API

This example demonstrates a voice assistant that:
1. Uses LiveKit for real-time audio streaming
2. Supports BOTH OpenAI Realtime API and Gemini Live API
3. Supports tool calling for sales data queries

Switch providers via VOICE_PROVIDER env var: "openai" (default) or "gemini"

Prerequisites:
- LiveKit Cloud account (or self-hosted server)
- OpenAI API key OR Google API key
- Run test_setup.py first to verify configuration

Run:
    # OpenAI (default)
    python voice_agents/livekit_realtime.py

    # Gemini
    VOICE_PROVIDER=gemini python voice_agents/livekit_realtime.py

Then connect via LiveKit Playground or your own client.
"""

import os
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Provider Selection
# =============================================================================

VOICE_PROVIDER = os.getenv("VOICE_PROVIDER", "openai").lower()

# LiveKit imports
try:
    from livekit import rtc
    from livekit.agents import Agent, AgentSession, AutoSubscribe, JobContext, WorkerOptions, cli, function_tool
    from livekit.plugins import silero

    # Import provider-specific plugins
    if VOICE_PROVIDER == "gemini":
        from livekit.plugins import google
        print("Using Gemini Live API")
    else:
        from livekit.plugins import openai
        print("Using OpenAI Realtime API")

except ImportError as e:
    print(f"Error: LiveKit packages not installed. {e}")
    print("\nFor OpenAI:")
    print("  pip install livekit livekit-agents livekit-plugins-openai livekit-plugins-silero")
    print("\nFor Gemini:")
    print("  pip install livekit livekit-agents livekit-plugins-google livekit-plugins-silero")
    sys.exit(1)


# =============================================================================
# Provider Configuration
# =============================================================================

# Voice mapping between providers
VOICE_MAP = {
    "openai": {
        "default": "alloy",
        "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
    },
    "gemini": {
        "default": "Puck",
        "voices": ["Puck", "Charon", "Kore", "Fenrir", "Aoede"],
    },
}


def get_realtime_model():
    """Get the appropriate realtime model based on VOICE_PROVIDER."""
    voice = os.getenv("VOICE_NAME", VOICE_MAP[VOICE_PROVIDER]["default"])

    if VOICE_PROVIDER == "gemini":
        return google.realtime.RealtimeModel(
            voice=voice,
            temperature=0.8,
        )
    else:
        return openai.realtime.RealtimeModel(
            voice=voice,
            temperature=0.8,
        )


def get_stt():
    """Get the STT model based on provider."""
    if VOICE_PROVIDER == "gemini":
        # Gemini Live API handles STT internally
        return None
    else:
        return openai.STT(model="whisper-1")


def get_tts():
    """Get the TTS model based on provider."""
    if VOICE_PROVIDER == "gemini":
        # Gemini Live API handles TTS internally
        return None
    else:
        voice = os.getenv("VOICE_NAME", VOICE_MAP["openai"]["default"])
        return openai.TTS(voice=voice)


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

    # Create the voice agent with provider-specific config
    agent_config = {
        "instructions": system_prompt,
        "vad": silero.VAD.load(),  # Voice Activity Detection
        "llm": get_realtime_model(),
        "tools": [get_response_rate, get_top_templates, get_positive_responses],
    }

    # Add STT/TTS only for OpenAI (Gemini handles them internally)
    stt = get_stt()
    tts = get_tts()
    if stt:
        agent_config["stt"] = stt
    if tts:
        agent_config["tts"] = tts

    agent = Agent(**agent_config)

    # Create and start the agent session
    session = AgentSession()
    await session.start(agent, room=ctx.room)

    # Initial greeting
    # Note: For Gemini, skip greeting - session.say() requires separate TTS
    # Gemini handles audio natively, user just starts talking
    if VOICE_PROVIDER != "gemini":
        await session.say(
            "Hi! I'm your AutoReach analytics assistant. "
            "Ask me about response rates, top templates, or interested leads.",
            allow_interruptions=True
        )


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    # Verify environment based on provider
    if VOICE_PROVIDER == "gemini":
        if not os.getenv("GOOGLE_API_KEY"):
            print("Error: GOOGLE_API_KEY not set")
            print("Copy .env.example to .env and add your Google API key")
            sys.exit(1)
    else:
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not set")
            print("Copy .env.example to .env and add your API key")
            sys.exit(1)

    if not os.getenv("LIVEKIT_URL"):
        print("Error: LiveKit credentials not set")
        print("Set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET in .env")
        sys.exit(1)

    print(f"\nStarting Voice Agent with {VOICE_PROVIDER.upper()}...")
    print(f"LiveKit URL: {os.getenv('LIVEKIT_URL')}")
    print(f"Voice: {os.getenv('VOICE_NAME', VOICE_MAP[VOICE_PROVIDER]['default'])}")
    print(f"\nAvailable voices for {VOICE_PROVIDER}: {', '.join(VOICE_MAP[VOICE_PROVIDER]['voices'])}")
    print("\nConnect via LiveKit Playground or your client to start talking.")
    print("Ctrl+C to stop.\n")

    # Run the agent
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
