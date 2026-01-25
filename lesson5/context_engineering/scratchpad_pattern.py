"""
External Memory: The Scratchpad Pattern (CLAUDE.md)

Instead of keeping everything in context, persist state to files
that can be read back when needed.

This is the pattern used by Claude Code's CLAUDE.md file.

Pros:
- Unlimited "memory" capacity
- Persists across sessions
- Can be version controlled
- Multiple agents can share state

Cons:
- Must explicitly read/write
- Adds file I/O overhead
- State can become stale

Best for:
- Multi-session workflows
- Team/shared context
- Complex projects with many details
- Agent handoffs

Run:
    python context_engineering/scratchpad_pattern.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


# =============================================================================
# Scratchpad File Management
# =============================================================================

SCRATCHPAD_DIR = Path(__file__).parent / "scratch"
SCRATCHPAD_FILE = SCRATCHPAD_DIR / "session_state.md"


def ensure_scratchpad_dir():
    """Create scratchpad directory if it doesn't exist."""
    SCRATCHPAD_DIR.mkdir(parents=True, exist_ok=True)


def read_scratchpad() -> str:
    """Read current scratchpad contents."""
    if not SCRATCHPAD_FILE.exists():
        return ""
    return SCRATCHPAD_FILE.read_text()


def write_scratchpad(content: str):
    """Write to scratchpad file."""
    ensure_scratchpad_dir()
    SCRATCHPAD_FILE.write_text(content)


def append_to_scratchpad(section: str, content: str):
    """Append content to a section in the scratchpad."""
    ensure_scratchpad_dir()

    current = read_scratchpad()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entry = f"\n## {section}\n*Updated: {timestamp}*\n\n{content}\n"

    write_scratchpad(current + new_entry)


def create_initial_scratchpad(project_info: dict):
    """Create initial scratchpad with project info."""
    content = f"""# Project Scratchpad

## Project Info
- **Name**: {project_info.get('name', 'Unnamed')}
- **Started**: {datetime.now().strftime('%Y-%m-%d')}
- **Goal**: {project_info.get('goal', 'Not specified')}

## Key Facts
{project_info.get('facts', '- (none yet)')}

## Decisions Made
- (none yet)

## Current Status
- Phase: Starting
- Next action: Define requirements

---
*This file persists context across sessions. Update as needed.*
"""
    write_scratchpad(content)
    return content


# =============================================================================
# Agent with Scratchpad Integration
# =============================================================================

SYSTEM_PROMPT = """You are a project assistant with access to a persistent scratchpad.

The scratchpad contains context that persists across sessions:
- Project info and goals
- Key facts and decisions
- Current status

<scratchpad_contents>
{scratchpad}
</scratchpad_contents>

When you learn important new information, suggest updating the scratchpad.
Format scratchpad updates as:

```update_scratchpad
SECTION: [section name]
CONTENT: [content to add]
```

Always check the scratchpad for context before answering questions about the project.
"""


def parse_scratchpad_updates(response: str) -> list[tuple[str, str]]:
    """Parse scratchpad update commands from response.

    Returns list of (section, content) tuples.
    """
    updates = []
    lines = response.split("\n")

    in_update_block = False
    current_section = None
    current_content = []

    for line in lines:
        if line.strip() == "```update_scratchpad":
            in_update_block = True
            current_section = None
            current_content = []
        elif line.strip() == "```" and in_update_block:
            if current_section and current_content:
                updates.append((current_section, "\n".join(current_content)))
            in_update_block = False
        elif in_update_block:
            if line.startswith("SECTION:"):
                current_section = line.replace("SECTION:", "").strip()
            elif line.startswith("CONTENT:"):
                current_content.append(line.replace("CONTENT:", "").strip())
            elif current_section:
                current_content.append(line)

    return updates


async def chat_with_scratchpad(
    client: anthropic.AsyncAnthropic,
    user_input: str,
    conversation_history: list[dict]
) -> tuple[str, list[dict]]:
    """Chat with scratchpad integration.

    Args:
        client: Anthropic client
        user_input: User's message
        conversation_history: Recent conversation (kept short since scratchpad has state)

    Returns:
        Tuple of (response, updated_history)
    """
    # Read current scratchpad
    scratchpad = read_scratchpad()

    # Build system prompt with scratchpad
    system = SYSTEM_PROMPT.format(scratchpad=scratchpad or "(empty)")

    # Add new user message
    conversation_history.append({"role": "user", "content": user_input})

    # Keep conversation history short - scratchpad has the state
    recent_history = conversation_history[-6:]  # Last 3 exchanges

    # Make API call
    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        system=system,
        messages=recent_history
    )

    assistant_content = response.content[0].text

    # Check for scratchpad updates
    updates = parse_scratchpad_updates(assistant_content)
    for section, content in updates:
        print(f"  [Updating scratchpad: {section}]")
        append_to_scratchpad(section, content)

    # Add to history
    conversation_history.append({"role": "assistant", "content": assistant_content})

    return assistant_content, conversation_history


# =============================================================================
# Demo
# =============================================================================

async def demo_scratchpad():
    """Demonstrate the scratchpad pattern."""
    print("\n" + "=" * 60)
    print(" Scratchpad Pattern Demo")
    print("=" * 60)

    client = anthropic.AsyncAnthropic()

    # Initialize scratchpad with project info
    print("\nInitializing scratchpad...")
    create_initial_scratchpad({
        "name": "AutoReach Optimization",
        "goal": "Improve response rate from 3.5% to 5%",
        "facts": "- Current response rate: 3.5%\n- 50,000 prospects\n- Using 5 email templates"
    })

    print("\nInitial scratchpad contents:")
    print("-" * 60)
    print(read_scratchpad())

    # Simulate a conversation that spans context
    conversation = [
        "Let's brainstorm ways to improve our response rate.",
        "The industry insight template had 4.8% response rate last quarter. Let's use that as a baseline.",
        "We decided to focus on tech companies first since they have the highest conversion.",
        "Let's pause here. I'll continue this tomorrow. Please save the key decisions.",
    ]

    history: list[dict] = []

    print("\n" + "=" * 60)
    print(" Conversation with Scratchpad Updates")
    print("=" * 60)

    for i, user_input in enumerate(conversation, 1):
        print(f"\n[Turn {i}] User: {user_input}")

        response, history = await chat_with_scratchpad(
            client,
            user_input,
            history
        )

        # Remove scratchpad update blocks from displayed response
        display_response = response.split("```update_scratchpad")[0].strip()
        print(f"[Turn {i}] Assistant: {display_response}")

    print("\n" + "=" * 60)
    print(" Final Scratchpad Contents")
    print("=" * 60)
    print(read_scratchpad())

    print("\n" + "-" * 60)
    print("Key Insight: The scratchpad file persists across sessions.")
    print("Next time you run this script, the context will still be there.")
    print(f"File location: {SCRATCHPAD_FILE}")


async def demo_session_resume():
    """Demonstrate resuming a session with existing scratchpad."""
    print("\n" + "=" * 60)
    print(" Session Resume Demo")
    print("=" * 60)

    # Check if scratchpad exists
    if not SCRATCHPAD_FILE.exists():
        print("No existing scratchpad found. Running initial demo first...")
        await demo_scratchpad()
        return

    print("\nExisting scratchpad found!")
    print("-" * 60)
    print(read_scratchpad())

    client = anthropic.AsyncAnthropic()
    history: list[dict] = []

    # Start a "new session" that references previous context
    user_input = "I'm back. What were we working on and what did we decide?"

    print(f"\n[New Session] User: {user_input}")

    response, history = await chat_with_scratchpad(client, user_input, history)
    display_response = response.split("```update_scratchpad")[0].strip()
    print(f"[New Session] Assistant: {display_response}")

    print("\n" + "-" * 60)
    print("Notice: The assistant remembers everything from the scratchpad,")
    print("even though this is a 'new' session with no conversation history!")


async def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Ask which demo to run
    print("Scratchpad Pattern Demos")
    print("1. Initial demo (creates scratchpad)")
    print("2. Resume demo (uses existing scratchpad)")
    print("3. Both")

    choice = input("\nChoice [1/2/3]: ").strip()

    if choice == "1":
        await demo_scratchpad()
    elif choice == "2":
        await demo_session_resume()
    else:
        await demo_scratchpad()
        await demo_session_resume()


if __name__ == "__main__":
    asyncio.run(main())
