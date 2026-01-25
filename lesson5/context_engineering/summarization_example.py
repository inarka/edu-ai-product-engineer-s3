"""
Context Summarization: Compress Older Messages

A more sophisticated technique that summarizes older parts of the
conversation instead of discarding them entirely.

Pros:
- Preserves key information from early context
- Maintains continuity over long conversations
- More informative than pure trimming

Cons:
- Adds latency (LLM call for summarization)
- Risk of distortion if summarization is poor
- Errors can propagate and compound

Best for:
- Long analysis sessions
- Coaching/mentoring conversations
- Planning and strategy discussions

Run:
    python context_engineering/summarization_example.py
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


SUMMARIZATION_PROMPT = """Summarize the following conversation, preserving:
1. Key facts mentioned (names, numbers, dates, decisions)
2. User's goals and constraints
3. Important context for continuing the conversation

Be concise but don't lose critical information.

<conversation>
{conversation}
</conversation>

<summary>
"""


async def summarize_messages(
    client: anthropic.AsyncAnthropic,
    messages: list[Message]
) -> str:
    """Summarize a list of messages into a concise summary.

    Args:
        client: Anthropic client
        messages: Messages to summarize

    Returns:
        Summary text
    """
    # Format conversation for summarization
    conversation_text = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in messages
    )

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": SUMMARIZATION_PROMPT.format(conversation=conversation_text)
        }]
    )

    return response.content[0].text


def manage_context_with_summarization(
    messages: list[Message],
    summary: str | None,
    keep_recent: int = 4,
    summarize_threshold: int = 8
) -> tuple[list[Message], bool]:
    """Manage context by summarizing older messages.

    Args:
        messages: Full conversation history
        summary: Current running summary (if any)
        keep_recent: Number of recent messages to keep verbatim
        summarize_threshold: When to trigger summarization

    Returns:
        Tuple of (messages_for_context, needs_new_summary)
    """
    if len(messages) < summarize_threshold:
        # No summarization needed yet
        return messages, False

    # Need to summarize - keep recent messages, rest becomes summary
    needs_summary = len(messages) >= summarize_threshold
    return messages[-keep_recent:], needs_summary


def create_context_with_summary(
    summary: str | None,
    recent_messages: list[Message]
) -> list[dict]:
    """Create API messages with summary as system context.

    Args:
        summary: Summary of older conversation
        recent_messages: Recent messages to include verbatim

    Returns:
        List of messages for API call
    """
    context = []

    if summary:
        # Include summary as first message
        context.append({
            "role": "user",
            "content": f"[Previous conversation summary: {summary}]"
        })
        context.append({
            "role": "assistant",
            "content": "I understand. Let's continue from where we left off."
        })

    # Add recent messages
    for m in recent_messages:
        context.append({"role": m.role, "content": m.content})

    return context


async def chat_with_summarization(
    client: anthropic.AsyncAnthropic,
    messages: list[Message],
    summary: str | None,
    user_input: str,
    keep_recent: int = 4,
    summarize_threshold: int = 8
) -> tuple[str, list[Message], str | None]:
    """Chat with automatic context summarization.

    Args:
        client: Anthropic client
        messages: Full conversation history
        summary: Current running summary
        user_input: New user message
        keep_recent: Recent messages to keep verbatim
        summarize_threshold: When to trigger summarization

    Returns:
        Tuple of (response, updated_messages, updated_summary)
    """
    # Add new user message to full history
    messages.append(Message(role="user", content=user_input))

    # Check if we need to summarize
    context_messages, needs_summary = manage_context_with_summarization(
        messages, summary, keep_recent, summarize_threshold
    )

    # Summarize if needed
    if needs_summary and summary is None:
        # Summarize everything except recent messages
        to_summarize = messages[:-keep_recent]
        print("  [Summarizing older context...]")
        summary = await summarize_messages(client, to_summarize)
        print(f"  [Summary: {summary[:100]}...]")

    # Create context for API call
    api_messages = create_context_with_summary(summary, context_messages)

    # Make API call
    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        system="You are a helpful assistant. Continue the conversation naturally.",
        messages=api_messages
    )

    assistant_content = response.content[0].text

    # Add to full history
    messages.append(Message(role="assistant", content=assistant_content))

    return assistant_content, messages, summary


async def demo_summarization():
    """Demonstrate context summarization."""
    print("\n" + "=" * 60)
    print(" Context Summarization Demo")
    print("=" * 60)

    client = anthropic.AsyncAnthropic()

    messages: list[Message] = []
    summary: str | None = None

    # Longer conversation that will trigger summarization
    conversation = [
        "I'm Sarah, VP of Sales at DataTech Inc.",
        "We have 200 sales reps and 50,000 accounts.",
        "Our average deal size is $25,000.",
        "Current close rate is 18% but we want 25%.",
        "We think the problem is lead qualification.",
        "Reps are wasting time on unqualified leads.",
        "We've tried BANT but it's not working well.",
        "What would you recommend for better qualification?",  # Turn 8 - triggers summary
        "By the way, what was my name again?",  # Tests if summary preserved it
    ]

    print("\nConversation with summarization (threshold=8, keep_recent=4)...")
    print("-" * 60)

    for i, user_input in enumerate(conversation, 1):
        print(f"\n[Turn {i}] User: {user_input}")

        response, messages, summary = await chat_with_summarization(
            client,
            messages,
            summary,
            user_input,
            keep_recent=4,
            summarize_threshold=8
        )

        print(f"[Turn {i}] Assistant: {response}")

    print("\n" + "-" * 60)
    print("Final Summary:")
    print("-" * 60)
    if summary:
        print(summary)
    else:
        print("(No summarization was triggered)")


async def demo_summary_structure():
    """Show what a good summary structure looks like."""
    print("\n" + "=" * 60)
    print(" Summary Structure Example")
    print("=" * 60)

    client = anthropic.AsyncAnthropic()

    # Example conversation to summarize
    messages = [
        Message("user", "I'm working on optimizing our sales pipeline."),
        Message("assistant", "Great! What's your current pipeline structure?"),
        Message("user", "We have 5 stages: Lead, Qualified, Demo, Proposal, Closed."),
        Message("assistant", "That's a solid structure. What metrics are you tracking?"),
        Message("user", "Conversion rates between stages. Lead to Qualified is only 15%."),
        Message("assistant", "That's quite low. What's your qualification criteria?"),
        Message("user", "Just basic info - company size and industry."),
        Message("assistant", "You might benefit from more detailed qualification criteria."),
    ]

    print("\nOriginal conversation (8 messages):")
    print("-" * 60)
    for m in messages:
        print(f"{m.role.upper()}: {m.content}")

    print("\nGenerating summary...")
    summary = await summarize_messages(client, messages)

    print("-" * 60)
    print("Summary:")
    print("-" * 60)
    print(summary)


async def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    await demo_summary_structure()
    await demo_summarization()


if __name__ == "__main__":
    asyncio.run(main())
