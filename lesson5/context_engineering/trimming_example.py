"""
Context Trimming: Keep Last-N Turns

The simplest long-horizon technique. Keep the most recent N turns
and discard older ones.

Pros:
- Zero latency overhead
- Simple to implement
- Predictable context size

Cons:
- Loses early context entirely
- User may need to re-explain things

Best for:
- Tool-heavy operations
- Short workflows
- Stateless Q&A

Run:
    python context_engineering/trimming_example.py
"""

import asyncio
import os
import sys
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


@dataclass
class Message:
    role: str
    content: str


def trim_conversation(
    messages: list[Message],
    keep_last_n: int = 5,
    always_keep_first: bool = True
) -> list[Message]:
    """Trim conversation to last N turns.

    Args:
        messages: Full conversation history
        keep_last_n: Number of recent turns to keep (user + assistant = 2 turns)
        always_keep_first: Whether to always keep the first user message

    Returns:
        Trimmed message list
    """
    if len(messages) <= keep_last_n:
        return messages

    if always_keep_first:
        # Keep first message + last N-1 messages
        return [messages[0]] + messages[-(keep_last_n - 1):]
    else:
        return messages[-keep_last_n:]


def count_tokens(messages: list[Message]) -> int:
    """Rough token count estimation (4 chars ≈ 1 token)."""
    total_chars = sum(len(m.content) for m in messages)
    return total_chars // 4


async def chat_with_trimming(
    client: anthropic.AsyncAnthropic,
    messages: list[Message],
    user_input: str,
    keep_last_n: int = 6
) -> tuple[str, list[Message]]:
    """Send a message with trimmed context.

    Args:
        client: Anthropic client
        messages: Full conversation history
        user_input: New user message
        keep_last_n: Turns to keep

    Returns:
        Tuple of (assistant response, updated messages)
    """
    # Add new user message
    messages.append(Message(role="user", content=user_input))

    # Trim for API call
    trimmed = trim_conversation(messages, keep_last_n=keep_last_n)

    # Convert to API format
    api_messages = [{"role": m.role, "content": m.content} for m in trimmed]

    # Make API call
    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        system="You are a helpful assistant. Keep responses concise.",
        messages=api_messages
    )

    assistant_content = response.content[0].text

    # Add to full history
    messages.append(Message(role="assistant", content=assistant_content))

    return assistant_content, messages


async def demo_trimming():
    """Demonstrate context trimming."""
    print("\n" + "=" * 60)
    print(" Context Trimming Demo")
    print("=" * 60)

    client = anthropic.AsyncAnthropic()

    # Simulate a long conversation
    messages: list[Message] = []

    conversation = [
        "Hi, I'm working on a sales analytics project.",
        "We have about 50,000 prospects in our database.",
        "The main KPI we track is response rate.",
        "Currently it's around 3.5% on average.",
        "We use different templates for different industries.",
        "Tech companies get our 'innovation' template.",
        "Finance gets our 'compliance' template.",
        "What was our response rate again?",  # Tests if model remembers
    ]

    print("\nSimulating conversation with context trimming (keep_last_n=6)...")
    print("-" * 60)

    for i, user_input in enumerate(conversation, 1):
        print(f"\n[Turn {i}] User: {user_input}")

        response, messages = await chat_with_trimming(
            client,
            messages,
            user_input,
            keep_last_n=6  # Keep ~3 exchanges
        )

        tokens_full = count_tokens(messages)
        tokens_trimmed = count_tokens(trim_conversation(messages, keep_last_n=6))

        print(f"[Turn {i}] Assistant: {response}")
        print(f"         [Full history: ~{tokens_full} tokens, Sent: ~{tokens_trimmed} tokens]")

    print("\n" + "-" * 60)
    print("Analysis:")
    print("-" * 60)
    print(f"Total turns: {len(messages)}")
    print(f"Full history tokens: ~{count_tokens(messages)}")
    print(f"Trimmed tokens sent on last turn: ~{count_tokens(trim_conversation(messages, keep_last_n=6))}")
    print("\nNote: On turn 8, the model may not remember the response rate")
    print("from turn 4 because it was trimmed from context.")


async def compare_with_without_trimming():
    """Compare behavior with and without trimming."""
    print("\n" + "=" * 60)
    print(" Comparison: With vs Without Trimming")
    print("=" * 60)

    client = anthropic.AsyncAnthropic()

    # Build up history that exceeds our trim limit
    history = [
        {"role": "user", "content": "My name is Alex and I work at TechCorp."},
        {"role": "assistant", "content": "Nice to meet you, Alex! How can I help you today?"},
        {"role": "user", "content": "We're analyzing our sales data for Q4."},
        {"role": "assistant", "content": "I can help with that. What metrics are you looking at?"},
        {"role": "user", "content": "Response rate is our main KPI. It was 3.5% last quarter."},
        {"role": "assistant", "content": "3.5% is a solid response rate for B2B outreach."},
        {"role": "user", "content": "We want to improve it to 5% by end of year."},
        {"role": "assistant", "content": "That's an ambitious but achievable goal. Let's work on it."},
    ]

    question = "What's my name and what response rate did I mention?"

    # With full history
    print("\n[Full History - 8 messages + question]")
    full_messages = history + [{"role": "user", "content": question}]
    response_full = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=200,
        messages=full_messages
    )
    print(f"Response: {response_full.content[0].text}")

    # With trimmed history (keep last 4 messages)
    print("\n[Trimmed History - last 4 messages + question]")
    trimmed_messages = history[-4:] + [{"role": "user", "content": question}]
    response_trimmed = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=200,
        messages=trimmed_messages
    )
    print(f"Response: {response_trimmed.content[0].text}")

    print("\n" + "-" * 60)
    print("Notice: With trimming, the model may not know your name")
    print("(mentioned in turn 1) but still knows recent context.")


async def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    await demo_trimming()
    await compare_with_without_trimming()


if __name__ == "__main__":
    asyncio.run(main())
