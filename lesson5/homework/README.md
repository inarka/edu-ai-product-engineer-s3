# Homework: Sales Voice Data Analyst

Build a voice assistant for AutoReach performance analysis.

## Overview

Create a voice-enabled assistant that allows sales teams to query their AutoReach performance data using natural language voice commands.

## Requirements

| Component | Description | Points |
|-----------|-------------|--------|
| **Voice Interface** | LiveKit + Realtime API or STT→LLM→TTS | 25 |
| **Data Connection** | Connect to AutoReach (real or mock data) | 20 |
| **Task Orchestration** | Use Tasks system for multi-step analysis | 25 |
| **Example Queries** | Handle the queries listed below | 20 |
| **Documentation** | README with setup and demo instructions | 10 |

**Total: 100 points**

## Required Voice Queries

Your assistant must be able to handle these queries:

1. **"What was our response rate last week?"**
   - Return response rate percentage
   - Include total sent and total responses

2. **"Which templates performed best?"**
   - Return top 3 templates by response rate
   - Include usage counts

3. **"Show me positive responses"**
   - Return recent positive replies
   - Include prospect name, company, and snippet

## Bonus Points (+20)

| Bonus | Points |
|-------|--------|
| Multi-agent orchestration for parallel analysis | +5 |
| Persistent task list across sessions | +5 |
| Export analysis to files (CSV, PDF) | +5 |
| Voice activity visualization | +5 |

## Architecture Options

### Option A: LiveKit + Realtime API (Recommended)
```
User Voice → LiveKit → OpenAI Realtime → Tools → Response → User
```

Pros:
- Lowest latency (~300ms)
- Natural interruption handling
- Built-in voice activity detection

Setup:
1. Create LiveKit Cloud account
2. Get OpenAI API key with Realtime access
3. Use `livekit_realtime.py` as starting point

### Option B: STT → LLM → TTS
```
User Voice → Whisper → Claude → ElevenLabs → User
```

Pros:
- More control over each stage
- Can use Claude for reasoning
- Lower cost per minute

Setup:
1. Get OpenAI API key (for Whisper)
2. Get Anthropic API key (for Claude)
3. Get ElevenLabs API key (optional, or use OpenAI TTS)
4. Use `stt_llm_tts.py` as starting point

## Task Orchestration

For multi-step analysis queries, use the Tasks system:

**Example: "Give me a full performance review"**

```
Task 1: Get response rate metrics          [parallel]
Task 2: Get top templates                   [parallel]
Task 3: Get positive responses              [parallel]
Task 4: Synthesize and present findings     [blocked by 1,2,3]
```

See `agent_orchestration/tasks_with_dependencies.py` for implementation patterns.

## Getting Started

### 1. Environment Setup

```bash
cd lesson5
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### 2. Verify Setup

```bash
python voice_agents/test_setup.py
```

### 3. Start with the Starter Template

```bash
# Edit the starter template
python homework/sales_voice_analyst.py
```

### 4. Test Your Implementation

Create test scenarios:
1. Basic query: "What's our response rate?"
2. Comparison: "Compare this week to last week"
3. Deep dive: "Why are tech companies responding better?"

## Data Source Options

### Option 1: Mock Data (Easiest)
Use the mock data functions in the starter template. Good for development and demo.

### Option 2: Real AutoReach API
If you have access to AutoReach, integrate with their API:
- See AutoReach API documentation
- Implement API client in `tools/autoreach.py`
- Handle authentication and rate limiting

### Option 3: CSV/Database
Create a local data source:
- Generate sample data in CSV format
- Use pandas for analysis
- Store in SQLite for persistence

## Deliverables

1. **Code Repository**
   - All source code
   - `requirements.txt`
   - `.env.example`
   - `README.md` with setup instructions

2. **Demo**
   - Video recording of voice interaction (2-3 minutes), OR
   - Live demo during review session

3. **Brief Writeup** (~1 page)
   - Architecture choices and rationale
   - Challenges encountered
   - What you'd do differently next time

## Evaluation Criteria

| Criterion | Weight |
|-----------|--------|
| Functionality (all queries work) | 40% |
| Code quality (clean, documented) | 25% |
| Voice UX (natural, responsive) | 20% |
| Documentation (clear setup, demo) | 15% |

## Tips for Success

1. **Start Simple**: Get basic voice I/O working first, then add tools
2. **Use Mock Data**: Don't get stuck on API integration
3. **Test Incrementally**: Test each query type before combining
4. **Record Demo Early**: Don't wait until the last minute
5. **Document As You Go**: Write README while building

## Resources

- `voice_agents/livekit_realtime.py` - LiveKit + Realtime example
- `voice_agents/stt_llm_tts.py` - Traditional pipeline example
- `agent_orchestration/tasks_with_dependencies.py` - Task patterns
- `context_engineering/` - Long-horizon techniques

## Questions?

Post in the course Telegram channel or reach out to the instructor.

Good luck! This is the capstone homework - show us what you've learned across all 5 workshops.
