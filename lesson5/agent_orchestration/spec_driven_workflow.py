"""
Spec-Driven Development Workflow

A workflow pattern from the community (Vladimir Kovtunovskiy) that
uses structured interviews to create specifications before coding.

The pattern:
1. User dictates idea (voice or text)
2. Claude interviews with clarifying questions
3. Writes spec to SPEC.md
4. Plan mode executes the spec

"Almost always good result first time"

Run:
    python agent_orchestration/spec_driven_workflow.py
"""

import asyncio
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
# Interview System
# =============================================================================

INTERVIEW_SYSTEM_PROMPT = """You are a requirements analyst conducting a structured interview
to understand a project before any code is written.

Your job is to ask clarifying questions to build a complete specification.

<interview_phases>
1. UNDERSTANDING: What problem are we solving? Who is the user?
2. SCOPE: What's in scope vs out of scope? What's the MVP?
3. TECHNICAL: What constraints exist? What should we use/avoid?
4. SUCCESS: How will we know it's done? What does success look like?
</interview_phases>

<rules>
- Ask ONE question at a time (max 2 related questions)
- Build on previous answers
- If something is ambiguous, probe deeper
- When you have enough info, say "READY_TO_SPEC"
- Keep questions conversational but focused
</rules>

After each user response, either:
1. Ask the next clarifying question, OR
2. Say "READY_TO_SPEC" if you have enough information
"""

SPEC_GENERATION_PROMPT = """Based on the interview below, create a detailed specification document.

<interview>
{interview_transcript}
</interview>

Write a specification in this format:

# Project Specification: [Project Name]

## Overview
[1-2 sentence summary]

## Problem Statement
[What problem this solves]

## User Stories
- As a [user], I want to [action] so that [benefit]
- ...

## Requirements

### Functional Requirements
1. [Requirement]
2. [Requirement]
...

### Non-Functional Requirements
1. [Performance, security, etc.]
...

## Scope

### In Scope
- [Feature/capability]
...

### Out of Scope
- [What we're NOT building]
...

## Technical Decisions
- [Decision and rationale]
...

## Success Criteria
- [Observable outcome that indicates success]
...

## Open Questions
- [Anything still unclear]

---
Generated: {timestamp}
"""


# =============================================================================
# Interview State Machine
# =============================================================================

class SpecInterviewer:
    """Conducts structured interview and generates spec."""

    def __init__(self, output_dir: Path | None = None):
        """Initialize interviewer.

        Args:
            output_dir: Directory to write SPEC.md
        """
        self.client = anthropic.AsyncAnthropic()
        self.conversation: list[dict] = []
        self.output_dir = output_dir or Path(".")
        self.project_name = "unnamed"

    async def ask(self, user_input: str) -> str:
        """Process user input and get next question or spec.

        Args:
            user_input: User's response

        Returns:
            Next question or "READY" if interview is complete
        """
        self.conversation.append({"role": "user", "content": user_input})

        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            system=INTERVIEW_SYSTEM_PROMPT,
            messages=self.conversation
        )

        assistant_response = response.content[0].text
        self.conversation.append({"role": "assistant", "content": assistant_response})

        return assistant_response

    def _build_transcript(self) -> str:
        """Build interview transcript from conversation."""
        lines = []
        for msg in self.conversation:
            role = "Interviewer" if msg["role"] == "assistant" else "User"
            lines.append(f"{role}: {msg['content']}")
        return "\n\n".join(lines)

    async def generate_spec(self) -> str:
        """Generate specification from interview.

        Returns:
            Specification document text
        """
        transcript = self._build_transcript()

        prompt = SPEC_GENERATION_PROMPT.format(
            interview_transcript=transcript,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        response = await self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        spec = response.content[0].text

        # Extract project name from spec
        if "# Project Specification:" in spec:
            title_line = spec.split("\n")[0]
            self.project_name = title_line.replace("# Project Specification:", "").strip()

        return spec

    def save_spec(self, spec: str, filename: str = "SPEC.md"):
        """Save specification to file.

        Args:
            spec: Specification content
            filename: Output filename
        """
        output_path = self.output_dir / filename
        output_path.write_text(spec)
        print(f"\nSpecification saved to: {output_path}")


# =============================================================================
# Interactive Interview Session
# =============================================================================

async def run_interactive_interview():
    """Run an interactive interview session."""
    print("\n" + "=" * 60)
    print(" Spec-Driven Development: Interview Mode")
    print("=" * 60)

    print("""
This is a structured interview to create a project specification.

I'll ask you questions about your project to understand:
- What problem you're solving
- Who the users are
- What success looks like
- Technical constraints

Type your responses naturally. When I have enough information,
I'll generate a SPEC.md file.

Type 'quit' to exit, 'skip' to end interview early.
""")

    interviewer = SpecInterviewer()

    # Start with initial prompt
    initial = "I'd like to build something. Let me tell you about it..."
    print(f"\nYou: {initial}")

    response = await interviewer.ask(initial)
    print(f"\nInterviewer: {response}")

    # Interview loop
    while "READY_TO_SPEC" not in response:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == "quit":
            print("\nInterview cancelled.")
            return

        if user_input.lower() == "skip":
            print("\nEnding interview early...")
            break

        if not user_input:
            continue

        response = await interviewer.ask(user_input)
        print(f"\nInterviewer: {response}")

    # Generate spec
    print("\n" + "=" * 60)
    print(" Generating Specification...")
    print("=" * 60)

    spec = await interviewer.generate_spec()

    print("\n" + spec)

    # Offer to save
    save = input("\n\nSave specification to SPEC.md? [y/n]: ").strip().lower()
    if save == "y":
        interviewer.save_spec(spec)


# =============================================================================
# Demo: Pre-scripted Interview
# =============================================================================

async def demo_scripted_interview():
    """Demonstrate the interview flow with pre-scripted responses."""
    print("\n" + "=" * 60)
    print(" Spec-Driven Demo (Pre-scripted)")
    print("=" * 60)

    # Simulated interview responses
    script = [
        "I want to build a voice assistant that helps sales teams analyze their AutoReach performance.",
        "The main users are sales managers who want quick insights without logging into dashboards.",
        "They need to ask questions like 'what was our response rate last week?' and get voice answers.",
        "MVP should handle basic metrics queries. Advanced analytics and recommendations are out of scope.",
        "We're using OpenAI's Realtime API for voice and already have AutoReach data via API.",
        "Success is when a manager can get their daily briefing in under 2 minutes via voice.",
        "Budget is flexible. Main constraint is the voice assistant needs to respond in under 2 seconds."
    ]

    interviewer = SpecInterviewer()

    print("\nSimulating interview...\n")

    # Initial question
    response = await interviewer.ask("I want to build something for my team.")
    print(f"Interviewer: {response}\n")

    # Run through script
    for user_response in script:
        print(f"User: {user_response}")

        response = await interviewer.ask(user_response)
        print(f"\nInterviewer: {response}\n")

        if "READY_TO_SPEC" in response:
            break

    # Generate spec
    print("\n" + "=" * 60)
    print(" Generated Specification")
    print("=" * 60)

    spec = await interviewer.generate_spec()
    print(spec)

    return spec


def show_workflow_concept():
    """Explain the spec-driven workflow concept."""
    print("\n" + "=" * 60)
    print(" Spec-Driven Development Workflow")
    print("=" * 60)

    print("""
The Spec-Driven workflow is a pattern from the community that
dramatically improves first-time success rates for AI-assisted development.

┌─────────────────────────────────────────────────────────────┐
│  1. CAPTURE: User describes idea (voice or text)            │
│                                                              │
│     "I want to build a voice assistant for sales analytics" │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  2. INTERVIEW: Claude asks clarifying questions             │
│                                                              │
│     "Who are the primary users?"                            │
│     "What's the MVP scope?"                                 │
│     "What are the technical constraints?"                   │
│     "How will you measure success?"                         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  3. SPEC: Claude writes specification to SPEC.md            │
│                                                              │
│     - User stories                                          │
│     - Requirements (functional & non-functional)            │
│     - Scope (in/out)                                        │
│     - Success criteria                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  4. PLAN: Claude Code enters plan mode                      │
│                                                              │
│     Reads SPEC.md and creates implementation plan           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  5. EXECUTE: Claude Code implements per plan                │
│                                                              │
│     "Almost always good result first time"                  │
└─────────────────────────────────────────────────────────────┘

Why This Works:
---------------
1. REDUCES AMBIGUITY: Interview catches unstated assumptions
2. CREATES ALIGNMENT: Both human and AI agree on what "done" means
3. ENABLES AUTONOMY: Spec is a self-contained instruction set
4. PREVENTS SCOPE CREEP: Clear in/out of scope boundaries
5. SUPPORTS ITERATION: Spec can be revised before coding

Tools That Help:
----------------
- WisprFlow: Voice transcription for initial idea capture
- Claude Code AskUserQuestion tool: Structured interview flow
- SPEC.md: Standardized specification format
- OpenSpec (github.com/Fission-AI/OpenSpec): Spec templates

Community Quote:
----------------
"Since adopting spec-driven development, I get good results on
the first try almost every time. The interview step catches all
the edge cases and unstated requirements that used to cause
rework." - Vladimir Kovtunovskiy
""")


async def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY not set")
        show_workflow_concept()
        return

    print("\nSpec-Driven Development Demo")
    print("=" * 60)
    print("1. Workflow concept (no API)")
    print("2. Pre-scripted demo (uses API)")
    print("3. Interactive interview (uses API)")

    choice = input("\nChoice [1/2/3]: ").strip()

    if choice == "3":
        await run_interactive_interview()
    elif choice == "2":
        await demo_scripted_interview()
    else:
        show_workflow_concept()


if __name__ == "__main__":
    asyncio.run(main())
