# Research Squad - Multi-Agent System Demo

A LangGraph-based multi-agent system for B2B prospect research. This demo accompanies **Workshop 3: Multi-Agent Systems**.

## Architecture

```
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │   (entry node)  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ LinkedIn Agent  │  │  Company Agent  │  │   News Agent    │
│  (gpt-5-mini)   │  │  (gpt-5-mini)   │  │  (gpt-5-mini)   │
│   [extraction]  │  │   [extraction]  │  │   [extraction]  │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └───────────────────┬┴───────────────────┘
                             ▼
                    ┌─────────────────┐
                    │    Synthesis    │
                    │     (gpt-5.2)   │
                    │    [reasoning]  │
                    └────────┬────────┘
                             │
                             ▼
                           END
```

**Key Insight: Model Optimization**

Subagents use cheaper/faster models (`gpt-5-mini`) for focused extraction tasks,
while the synthesis agent uses the most capable model (`gpt-5.2`) for complex reasoning.
This is one of the 5 decomposition criteria from the course - using appropriate models for different tasks.

### Key Patterns Demonstrated

1. **Fan-out/Fan-in**: Parallel execution of research agents
2. **Typed State**: `ResearchState` with structured data models
3. **Agent as Node**: Each agent has its own LLM, tools, and prompts
4. **Model Optimization**: Different models for different task complexity
5. **Human-in-the-Loop**: Optional interrupt before synthesis
6. **LangSmith Tracing**: Full observability of multi-agent execution

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Required keys:
- `OPENAI_API_KEY`: For LLM calls (required)
- `TAVILY_API_KEY`: For news and company web search (required)
- `LANGCHAIN_API_KEY`: For LangSmith tracing (recommended)
- `ENRICHLAYER_API_KEY`: For LinkedIn data (optional, uses simulated data if not set)

## Usage

### Basic Run

```bash
python main.py --url "https://linkedin.com/in/someone" --company "Acme Corp"
```

### With Debug (Show Graph Structure)

```bash
python main.py --url "..." --company "..." --debug
```

### Human-in-the-Loop Mode

```bash
python main.py --url "..." --human-review
```

This pauses execution before the synthesis agent, allowing you to review intermediate results.

## Project Structure

```
workspace/
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
├── main.py                   # CLI runner with LangSmith tracing
├── README.md                 # This file
└── research_squad/
    ├── __init__.py
    ├── state.py              # ResearchState TypedDict
    ├── graph.py              # StateGraph assembly
    └── nodes/
        ├── __init__.py
        ├── orchestrator.py   # Entry node, creates plan
        ├── linkedin_agent.py # LinkedIn research specialist
        ├── company_agent.py  # Company intelligence specialist
        ├── news_agent.py     # News & trends specialist
        └── synthesis.py      # Combines all results
```

## Key Concepts

### 1. StateGraph with Typed State

```python
class ResearchState(TypedDict, total=False):
    # INPUT
    linkedin_url: str
    company_name: str

    # AGENT RESULTS
    linkedin_data: LinkedInData | None
    company_data: CompanyData | None
    news_data: list[NewsItem] | None

    # SYNTHESIS
    final_report: str
    conflicts: list[str]

    # MESSAGES (with reducer)
    messages: Annotated[list, add_messages]
```

### 2. Parallel Execution

```python
# Fan-out: All three agents run concurrently
graph.add_edge("orchestrator", "linkedin_agent")
graph.add_edge("orchestrator", "company_agent")
graph.add_edge("orchestrator", "news_agent")

# Fan-in: LangGraph waits for all branches
graph.add_edge("linkedin_agent", "synthesis")
graph.add_edge("company_agent", "synthesis")
graph.add_edge("news_agent", "synthesis")
```

### 3. Agent as Node

Each agent is a complete unit with:
- Its own LLM instance (can use different models)
- Its own tools (isolated tool sets)
- Its own system prompt (specialized context)

### 4. Human-in-the-Loop

```python
# Compile with interrupt_before
graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["synthesis"],
)

# Resume after human approval
result = await graph.ainvoke(None, config)
```

## LangSmith Tracing

LangSmith provides full observability into multi-agent execution - crucial for debugging and optimization.

### Setup Steps

1. **Create a LangSmith account**: https://smith.langchain.com
2. **Create an API key**: Settings → API Keys → Create Key
3. **Add to your .env**:
   ```bash
   LANGCHAIN_API_KEY=lsv2_pt_xxxxx
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=research-squad
   ```

### What You'll See in LangSmith

When `LANGCHAIN_API_KEY` is set, all agent executions are traced:

1. **Multi-agent execution graph**: See how agents fan-out and fan-in
2. **Per-agent token usage**: Track costs for each subagent
3. **Latency breakdown**: Identify bottlenecks in parallel execution
4. **Message history**: Debug agent conversations and tool calls

### Accessing Your Traces

1. Go to: https://smith.langchain.com
2. Navigate to your project: `research-squad`
3. Click on any run to see the full execution tree

### Verify Setup

Run the setup checker:
```bash
python check_setup.py
```

## Extending the Demo

### Adding a New Agent

1. Create `research_squad/nodes/new_agent.py`:
   ```python
   async def new_agent_node(state: ResearchState) -> dict:
       # Your agent logic
       return {"new_data": result}
   ```

2. Add to `research_squad/nodes/__init__.py`

3. Wire into graph in `research_squad/graph.py`:
   ```python
   graph.add_node("new_agent", new_agent_node)
   graph.add_edge("orchestrator", "new_agent")
   graph.add_edge("new_agent", "synthesis")
   ```

4. Update `ResearchState` in `state.py` if needed

### Using Different Models per Agent

```python
# In linkedin_agent.py - use cheaper model for simple tasks
llm = ChatOpenAI(model="gpt-5-mini", temperature=0)

# In synthesis.py - use powerful model for complex reasoning
llm = ChatOpenAI(model="gpt-5.2", temperature=0)
```

## Related Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [Multi-Agent Patterns](https://docs.langchain.com/oss/python/langchain/multi-agent)
- [Survey: Measuring Agents in Production](https://arxiv.org/abs/2512.04123)
