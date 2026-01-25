"""
Traditional Voice Pipeline: STT → LLM → TTS

This example shows the traditional approach to voice agents:
1. Speech-to-Text (Whisper)
2. LLM Processing (Claude or GPT)
3. Text-to-Speech (ElevenLabs or OpenAI)

Use this approach when:
- You need more control over each stage
- Cost is a primary concern
- Latency of 2-3 seconds is acceptable
- You want to use Claude instead of GPT for reasoning

Run:
    python voice_agents/stt_llm_tts.py --audio input.wav

Or for continuous mode:
    python voice_agents/stt_llm_tts.py --continuous
"""

import argparse
import asyncio
import io
import os
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

import httpx

# Check for required packages
try:
    import openai
except ImportError:
    print("Error: openai package not installed. Run: pip install openai")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


# =============================================================================
# Speech-to-Text (Whisper)
# =============================================================================

async def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file to text using Whisper.

    Args:
        audio_path: Path to audio file (wav, mp3, etc.)

    Returns:
        Transcribed text
    """
    client = openai.AsyncOpenAI()

    with open(audio_path, "rb") as audio_file:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )

    return response


async def transcribe_bytes(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """Transcribe audio bytes to text using Whisper.

    Args:
        audio_bytes: Raw audio data
        filename: Filename to use for the upload

    Returns:
        Transcribed text
    """
    client = openai.AsyncOpenAI()

    # Create file-like object from bytes
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = filename

    response = await client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text"
    )

    return response


# =============================================================================
# LLM Processing (Claude)
# =============================================================================

async def process_with_claude(
    user_text: str,
    conversation_history: list[dict] | None = None,
    system_prompt: str | None = None
) -> str:
    """Process user input with Claude and return response.

    Args:
        user_text: Transcribed user speech
        conversation_history: Previous messages for context
        system_prompt: System instructions

    Returns:
        Claude's response text
    """
    client = anthropic.AsyncAnthropic()

    if system_prompt is None:
        system_prompt = """You are a helpful voice assistant for sales analytics.
Keep responses concise (2-3 sentences max) since they will be spoken aloud.
Be conversational and natural."""

    messages = conversation_history or []
    messages.append({"role": "user", "content": user_text})

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=300,  # Keep responses short for voice
        system=system_prompt,
        messages=messages
    )

    assistant_message = response.content[0].text

    # Update conversation history
    messages.append({"role": "assistant", "content": assistant_message})

    return assistant_message


# =============================================================================
# Text-to-Speech (OpenAI TTS)
# =============================================================================

async def synthesize_speech_openai(
    text: str,
    voice: str = "alloy",
    output_path: str | None = None
) -> bytes:
    """Synthesize speech using OpenAI TTS.

    Args:
        text: Text to speak
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
        output_path: Optional path to save audio file

    Returns:
        Audio bytes (mp3 format)
    """
    client = openai.AsyncOpenAI()

    response = await client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )

    audio_bytes = response.content

    if output_path:
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        print(f"Audio saved to: {output_path}")

    return audio_bytes


async def synthesize_speech_elevenlabs(
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel voice
    output_path: str | None = None
) -> bytes:
    """Synthesize speech using ElevenLabs.

    Args:
        text: Text to speak
        voice_id: ElevenLabs voice ID
        output_path: Optional path to save audio file

    Returns:
        Audio bytes (mp3 format)
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not set")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            },
            timeout=30.0
        )
        response.raise_for_status()
        audio_bytes = response.content

    if output_path:
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        print(f"Audio saved to: {output_path}")

    return audio_bytes


# =============================================================================
# Complete Pipeline
# =============================================================================

async def voice_pipeline(
    audio_input: str | bytes,
    conversation_history: list[dict] | None = None,
    tts_provider: str = "openai",
    output_audio_path: str | None = None
) -> tuple[str, str, bytes]:
    """Run complete voice pipeline: STT → LLM → TTS.

    Args:
        audio_input: Path to audio file or raw audio bytes
        conversation_history: Previous messages for context
        tts_provider: "openai" or "elevenlabs"
        output_audio_path: Optional path to save response audio

    Returns:
        Tuple of (transcribed_text, response_text, response_audio_bytes)
    """
    print("Step 1: Transcribing audio...")
    if isinstance(audio_input, str):
        user_text = await transcribe_audio(audio_input)
    else:
        user_text = await transcribe_bytes(audio_input)
    print(f"  User said: {user_text}")

    print("Step 2: Processing with LLM...")
    response_text = await process_with_claude(
        user_text,
        conversation_history=conversation_history
    )
    print(f"  Response: {response_text}")

    print("Step 3: Synthesizing speech...")
    if tts_provider == "elevenlabs":
        audio_bytes = await synthesize_speech_elevenlabs(
            response_text,
            output_path=output_audio_path
        )
    else:
        audio_bytes = await synthesize_speech_openai(
            response_text,
            output_path=output_audio_path
        )
    print(f"  Audio: {len(audio_bytes)} bytes")

    return user_text, response_text, audio_bytes


# =============================================================================
# Demo Mode
# =============================================================================

async def run_demo():
    """Run a demo of the pipeline with sample text."""
    print("\n" + "=" * 60)
    print(" STT → LLM → TTS Pipeline Demo")
    print("=" * 60)

    # Since we don't have audio input, we'll skip STT and demo LLM → TTS
    print("\nDemo: LLM → TTS (skipping STT since no audio file)")

    user_text = "How did our campaigns perform last week?"
    print(f"\nSimulated user input: {user_text}")

    print("\nStep 1: Processing with Claude...")
    response = await process_with_claude(user_text)
    print(f"Response: {response}")

    print("\nStep 2: Synthesizing speech with OpenAI TTS...")
    audio = await synthesize_speech_openai(response, output_path="response.mp3")
    print(f"Audio generated: {len(audio)} bytes saved to response.mp3")

    print("\n" + "=" * 60)
    print(" Demo Complete!")
    print("=" * 60)
    print("\nTo run with your own audio:")
    print("  python stt_llm_tts.py --audio your_audio.wav")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="STT → LLM → TTS Voice Pipeline"
    )
    parser.add_argument(
        "--audio",
        help="Path to audio file to transcribe"
    )
    parser.add_argument(
        "--tts",
        choices=["openai", "elevenlabs"],
        default="openai",
        help="TTS provider to use"
    )
    parser.add_argument(
        "--output",
        help="Path to save output audio"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo mode"
    )

    args = parser.parse_args()

    # Check API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        sys.exit(1)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    if args.tts == "elevenlabs" and not os.getenv("ELEVENLABS_API_KEY"):
        print("Error: ELEVENLABS_API_KEY not set (required for ElevenLabs TTS)")
        sys.exit(1)

    if args.demo or not args.audio:
        asyncio.run(run_demo())
    else:
        # Run full pipeline with provided audio
        asyncio.run(voice_pipeline(
            args.audio,
            tts_provider=args.tts,
            output_audio_path=args.output or "response.mp3"
        ))


if __name__ == "__main__":
    main()
