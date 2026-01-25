# Lesson 5: AI Agents — Voice, Context & Orchestration

## "From Single Agents to Multi-Agent Systems"

The final workshop in Cohort 3 covers advanced topics that build on everything you've learned in W1-W4. We start with a demo, then dive into voice agents, context engineering, and multi-agent orchestration.

## Learning Objectives

By the end of this lesson, you will be able to:

1. **Build voice agents** using LiveKit + OpenAI Realtime API
2. **Apply context engineering** principles from Anthropic's research
3. **Use advanced tool patterns** (Tool Search, Programmatic Tool Calling)
4. **Orchestrate multi-agent swarms** using Claude Code's Tasks system
5. **Understand ChatGPT Apps** architecture and submission process

## Prerequisites

- Completed Workshops 1-4
- OpenAI API key (for Realtime API)
- Anthropic API key
- Claude Code installed (for Tasks demo)

## Quick Start

```bash
# Navigate to lesson5
cd lesson5

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Test voice agent setup
python voice_agents/test_setup.py

# Run context engineering examples
python context_engineering/trimming_example.py

# Explore Tasks system
python agent_orchestration/tasks_basic.py
```

## Directory Structure

```
lesson5/
├── voice_agents/
│   ├── livekit_realtime.py         # LiveKit + OpenAI Realtime integration
│   ├── stt_llm_tts.py              # Traditional STT→LLM→TTS pipeline
│   └── test_setup.py               # Verify voice setup
├── context_engineering/
│   ├── trimming_example.py         # Last-N turns trimming
│   ├── summarization_example.py    # Context summarization
│   ├── scratchpad_pattern.py       # External memory (CLAUDE.md pattern)
│   └── tool_design_examples.py     # Good vs bad tool design
├── agent_orchestration/
│   ├── tasks_basic.py              # Tasks system introduction
│   ├── tasks_with_dependencies.py  # blockedBy dependency chains
│   ├── multi_agent_swarm.py        # Spawning parallel sub-agents
│   └── spec_driven_workflow.py     # Spec-driven development pattern
├── chatgpt_apps/
│   └── README.md                   # Links to chatgpt-app-skill
├── homework/
│   ├── sales_voice_analyst.py      # Starter template
│   └── README.md                   # Homework requirements
├── requirements.txt
├── .env.example
└── README.md
```

---

## Part 1: Voice Agents (30 min)

### Why Voice?

Voice is the most natural human interface. B2B use cases from a16z research:

| Use Case | Description | ROI Driver |
|----------|-------------|------------|
| **After-hours/overflow calls** | Handle calls when staff unavailable | Coverage without headcount |
| **Net-new outbound calls** | Automated SDR outreach | Scale without burning reps |
| **Back office calls** | Collections, scheduling, confirmations | High-volume, low-complexity |
| **Low-incentive calls** | Surveys, feedback collection | Tasks humans avoid |

### Two Architectures

**1. STT → LLM → TTS (Traditional)**
```
Audio → Whisper → Claude → ElevenLabs → Audio
          ↓         ↓          ↓
        ~500ms   ~1000ms    ~500ms

Total latency: 2-3 seconds
Cost: ~$0.02-0.05/minute
```

**2. Speech-to-Speech (Realtime API)**
```
Audio → OpenAI Realtime API → Audio
              ↓
        Voice Activity Detection
        Native audio understanding
        Interruption handling

Total latency: 300-500ms
Cost: ~$0.10-0.20/minute
```

**Decision Framework:**
- Use STT→LLM→TTS for: Cost-sensitive, batch processing, non-realtime
- Use Speech-to-Speech for: Real-time conversations, natural UX, interruption handling

### Code Example: LiveKit + Realtime API

See `voice_agents/livekit_realtime.py` for full implementation.

```python
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, llm
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai

async def entrypoint(ctx: JobContext):
    # Connect to LiveKit room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create voice pipeline with OpenAI Realtime
    agent = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=openai.STT(model="whisper-1"),
        llm=openai.realtime.RealtimeModel(
            voice="alloy",
            temperature=0.8,
            instructions="You are a helpful sales assistant..."
        ),
        tts=openai.TTS(voice="alloy"),
    )

    agent.start(ctx.room)
```

### New: ElevenLabs WhatsApp Integration

ElevenLabs now offers WhatsApp Business integration for voice bots:
- Users send voice messages via WhatsApp
- ElevenLabs processes and responds with voice
- No app installation required
- Excellent for international markets

---

## Part 2: Context Engineering + Advanced Tool Use (35 min)

### Why Context Engineering Matters

From Andrej Karpathy: "Context Engineering is the delicate art and science of filling the context window with just the right information for the next step."

From Anthropic: "Find the smallest set of high-signal tokens that maximize the likelihood of your desired outcome."

**Problems with poor context:**
- **Poisoning**: Hallucinations in early turns become referenced facts
- **Distraction**: Model overfocuses on context vs. training knowledge
- **Confusion**: Similar tools cause wrong tool calls
- **Clash**: Conflicting information leads to unpredictable behavior

### System Prompt Design (Anthropic Guidelines)

**"Right altitude"** — Not too prescriptive, not too vague:

```python
# Too prescriptive (bad)
SYSTEM_PROMPT = """
1. First, greet the user with exactly "Hello! How can I help you today?"
2. Then, wait for their response
3. If they mention a product, say "Great choice!"
4. Then ask "Would you like to proceed with purchase?"
...
"""

# Too vague (bad)
SYSTEM_PROMPT = "You are helpful."

# Right altitude (good)
SYSTEM_PROMPT = """
You are a sales assistant helping customers find products.

<guidelines>
- Ask clarifying questions before making recommendations
- Explain trade-offs between options, don't just recommend the expensive one
- If you don't know something, say so rather than guessing
</guidelines>

<examples>
User: "I need a laptop"
Assistant: "I'd be happy to help! A few quick questions:
- What will you primarily use it for (work, gaming, browsing)?
- Do you have a budget range in mind?
- Is portability important to you?"
</examples>
"""
```

### Tool Design Principles (Anthropic)

| Principle | Explanation |
|-----------|-------------|
| **Minimal** | Only tools actually needed for the task |
| **Focused** | Each tool does one thing well |
| **No overlap** | "If humans can't decide which tool, neither can the LLM" |
| **Self-contained** | Return all needed info, don't require follow-up calls |
| **Token-efficient** | Don't return 10KB when 500 bytes suffice |

**Bad tool design:**
```python
@tool
def search(query: str, search_type: str = "all"):
    """Search for anything. search_type can be 'web', 'docs', 'code', 'all'."""
```

**Good tool design:**
```python
@tool
def search_documentation(query: str):
    """Search official product documentation.

    USE WHEN: User asks about product features, API usage, or configuration.
    RETURNS: Relevant documentation sections with source links.
    """

@tool
def search_codebase(query: str, file_pattern: str = "*.py"):
    """Search project source code.

    USE WHEN: User needs to find implementation details or code examples.
    RETURNS: Matching code snippets with file paths and line numbers.
    """
```

### Advanced Tool Use Patterns

#### 1. Tool Search Tool (Deferred Loading)

Load tools dynamically instead of all upfront. Reduces system prompt tokens by ~85%.

```python
# Configure tools with defer_loading
tools_config = {
    "tools": [
        {
            "name": "search_crm",
            "description": "Search CRM for customer data",
            "defer_loading": True  # Only load when needed
        },
        {
            "name": "send_email",
            "description": "Send email to customer",
            "defer_loading": True
        }
    ]
}

# Model first uses tool_search to find relevant tools
# Then those tools are loaded into context
```

**Results:** Opus 4.5 accuracy improved from 79.5% → 88.1%

#### 2. Programmatic Tool Calling

Let Claude write Python to orchestrate multiple tool calls:

```python
# Instead of multiple sequential tool calls...
# Claude writes Python that the system executes:

code = """
# Fetch all data in parallel
crm_data = await tools.search_crm(customer_id)
email_history = await tools.get_email_history(customer_id)
support_tickets = await tools.get_support_tickets(customer_id)

# Process and return summary
return {
    "customer": crm_data,
    "recent_emails": email_history[-5:],
    "open_tickets": [t for t in support_tickets if t.status == "open"]
}
"""
```

**Benefits:** 37% token reduction, parallel execution, no context pollution from intermediate results.

#### 3. Tool Use Examples

JSON schemas define structure, but examples teach usage:

```python
tools = [
    {
        "name": "calendar_create_event",
        "description": "Create a calendar event",
        "input_schema": {...},
        "examples": [
            {
                "description": "Schedule a 1-hour team meeting",
                "input": {
                    "title": "Team Standup",
                    "duration_minutes": 60,
                    "attendees": ["alice@company.com", "bob@company.com"]
                }
            },
            {
                "description": "Block focus time (no attendees)",
                "input": {
                    "title": "Deep Work",
                    "duration_minutes": 120,
                    "attendees": []
                }
            }
        ]
    }
]
```

**Results:** Accuracy improved from 72% → 90% with examples.

### Long-Horizon Techniques

See `context_engineering/` for implementations of each pattern.

#### 1. Context Trimming
Keep last N turns, discard older ones.
- **Pros:** Zero latency, simple
- **Cons:** Loses early context
- **Best for:** Tool-heavy operations, short workflows

#### 2. Context Summarization
Compress older messages into structured summary.
- **Pros:** Preserves key information
- **Cons:** Risk of distortion, adds latency
- **Best for:** Long analysis, coaching, planning sessions

#### 3. Sub-agent Architectures
Specialized agents with isolated context windows.
- **Pros:** Clean context, no pollution between tasks
- **Cons:** Coordination overhead
- **Best for:** Complex multi-domain tasks

#### 4. External Memory (CLAUDE.md Pattern)
Persist state to files, read back when needed.
- **Pros:** Unlimited "memory", persists across sessions
- **Cons:** Must explicitly read/write
- **Best for:** Multi-session workflows, team context

---

## Part 3: Agent Orchestration — Tasks & Swarms (30 min)

### The Problem with Long Projects

Single-agent limitations:
- Context windows fill up
- State gets lost on `/clear`
- Re-explaining work across sessions
- One agent trying to hold everything

### The Tasks System (Claude Code, Jan 2026)

Tasks replace Todos with key improvements:

| Feature | Todos (Old) | Tasks (New) |
|---------|-------------|-------------|
| Persistence | Session only | `~/.claude/tasks/` |
| Dependencies | None | `blockedBy` field |
| Multi-session | No | `CLAUDE_CODE_TASK_LIST_ID` |
| Sub-agents | Manual | Automatic coordination |

### Basic Tasks Example

```python
# tasks_basic.py
from claude_code import TaskCreate, TaskUpdate, TaskList

# Create tasks
task1 = TaskCreate(
    subject="Research competitor pricing",
    description="Analyze top 5 competitors' pricing pages",
    activeForm="Researching competitor pricing"
)

task2 = TaskCreate(
    subject="Draft pricing recommendations",
    description="Based on competitor research, recommend our pricing tiers",
    activeForm="Drafting pricing recommendations"
)

# Set dependency: task2 blocked by task1
TaskUpdate(taskId=task2.id, addBlockedBy=[task1.id])
```

### Dependencies: The Real Feature

```json
{
  "id": "3",
  "subject": "Implement JWT auth",
  "status": "pending",
  "blockedBy": ["1", "2"]
}
```

Task #3 **literally cannot start** until #1 and #2 complete. This structure:
- Enforces execution order
- Plan exists outside Claude's context
- Enables parallel work on independent tasks

### Agent Swarms Concept

Multiple sub-agents coordinating on complex tasks:

```
Main Agent (Coordinator)
    ├── Task 1 (Agent A) ──┐
    ├── Task 2 (Agent B) ──┼── All parallel (fresh 200k contexts)
    ├── Task 3 (Agent C) ──┘
    └── Task 4 (blocked by 1,2,3) → Agent D
```

**Benefits:**
- Each sub-agent gets fresh 200k context window
- Isolated contexts = no pollution
- 7-10 sub-agents can run in parallel
- Model selection per task (Haiku for simple, Opus for complex)

### ExecPlans Pattern (OpenAI Cookbook)

A living document that enables autonomous work:

```markdown
# EXEC_PLAN.md

## Project: User Authentication System

## Progress
- [x] Design database schema
- [x] Implement User model
- [ ] Add JWT token generation
- [ ] Create login endpoint
- [ ] Create registration endpoint
- [ ] Add password reset flow

## Decision Log
| Date | Decision | Rationale |
|------|----------|-----------|
| Jan 15 | Use bcrypt for passwords | Industry standard, CPU-cost tuneable |
| Jan 15 | JWT over sessions | Stateless, scales better |

## Surprises
- SQLite has no native UUID type, using TEXT instead

## Current Focus
Adding JWT token generation. Need to decide on token expiry time.
```

### Spec-Driven Development Workflow

From the community (Vladimir Kovtunovskiy):

1. **Dictate idea** (using WisprFlow or voice)
2. **Claude interviews you** (AskUserQuestion tool)
3. **Writes spec to SPEC.md**
4. **Plan mode executes the spec**

Result: "Almost always good result first time"

```python
# spec_driven_workflow.py

SPEC_INTERVIEW_PROMPT = """
Before we start building, I need to understand your requirements.

I'll ask you a series of questions to create a clear specification.
Please answer as thoroughly as you can.

1. What problem are you trying to solve?
2. Who will use this solution?
3. What does success look like?
4. What constraints should I know about?
5. Are there any existing systems this needs to integrate with?
"""

# After interview, write to SPEC.md
# Then use plan mode to execute
```

---

## Part 4: ChatGPT Apps (10 min)

### Your Agents as Products

The App Store for AI agents is here:
- Distribution to 300M+ ChatGPT users
- Revenue share model emerging
- Real apps in production today

### Know/Do/Show Framework

When evaluating if something should be a ChatGPT App:

| Question | If Yes | If No |
|----------|--------|-------|
| Does it surface unique information? | ✅ Good fit | Consider other platforms |
| Does it take actions in external systems? | ✅ Good fit | May be too simple |
| Does it need custom UI/visualization? | ✅ Good fit | Text response may suffice |

Not everything should be a ChatGPT App. Simple Q&A → Custom GPT. Complex workflows → ChatGPT App.

### Architecture Overview

```
ChatGPT ←→ MCP Server ←→ Your Backend
              ↓
         Widgets (UI)
```

- **MCP Server**: Defines tools ChatGPT can call
- **Widgets**: Rich UI components (charts, forms, lists)
- **Backend**: Your APIs, databases, services

### Deep Dive Resource

See **chatgpt-app-skill**: https://github.com/BayramAnnakov/chatgpt-app-skill

Covers:
- 5-phase workflow for building apps
- MCP server templates (Python & Node)
- Widget development patterns
- Submission checklist
- Review process guidance

---

## Part 5: Course Journey Recap

| Workshop | Topic | Key Pattern |
|----------|-------|-------------|
| **W1** | Chained vs Agentic | When to use agents (150 → 250 lines) |
| **W2** | Reflection Pattern | V1 → Feedback → V2 structured improvement |
| **W3** | Multi-agent Systems | LangGraph for coordinated workflows |
| **W4** | Evaluation-Driven | "From 'it works' to 'I can prove it works'" |
| **W5** | Voice, Context, Orchestration | Production multi-agent systems |

**From 150 lines to production:** You now have the patterns to build:
- Voice interfaces for your agents
- Proper context management for long sessions
- Multi-agent orchestration for complex tasks
- Apps distributed to 300M users

---

## Homework: Sales Voice Data Analyst

Build a voice assistant for AutoReach performance analysis.

### Requirements

| Component | Description | Points |
|-----------|-------------|--------|
| **Voice Interface** | LiveKit + Realtime API or STT→LLM→TTS | 25 |
| **Data Connection** | Connect to AutoReach (real or mock data) | 20 |
| **Task Orchestration** | Use Tasks system for multi-step analysis | 25 |
| **Example Queries** | Handle: "Response rate last week?", "Best templates?", "Positive responses?" | 20 |
| **Documentation** | README with setup and demo instructions | 10 |

### Bonus Points (+20)

- Multi-agent orchestration for parallel analysis
- Persistent task list across sessions
- Export analysis to files (CSV, PDF)
- Voice activity visualization

### Deliverables

1. Working voice agent demo (video or live)
2. Code repository
3. Brief writeup (~1 page)

### Getting Started

```bash
cd lesson5/homework
python sales_voice_analyst.py
```

See `homework/README.md` for detailed requirements.

---

## Resources

### Anthropic
- [Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)

### OpenAI
- [Session Memory](https://cookbook.openai.com/examples/agents_sdk/session_memory)
- [Codex ExecPlans](https://cookbook.openai.com/articles/codex_exec_plans)
- [Realtime API](https://platform.openai.com/docs/guides/realtime)

### Community
- [ChatGPT App Skill](https://github.com/BayramAnnakov/chatgpt-app-skill)
- [OpenSpec](https://github.com/Fission-AI/OpenSpec)
- [Agent Swarms Article](https://x.com/seejayhess) (CJ Hess)
- [vibekanban.com](https://vibekanban.com) - Managing agent work

### Voice
- [LiveKit Agents](https://docs.livekit.io/agents/)
- [ElevenLabs](https://elevenlabs.io)
- [Voice AI Comparison](https://artificialanalysis.ai/text-to-speech)
