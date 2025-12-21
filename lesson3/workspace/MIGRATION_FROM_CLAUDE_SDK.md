# Migration Guide: Claude Agent SDK to LangGraph

This guide helps students transition from **Claude Agent SDK** (Workshops 1-2) to **LangGraph** (Workshop 3+).

## Why Are We Switching?

| Consideration | Claude Agent SDK | LangGraph |
|--------------|------------------|-----------|
| **LLM Provider** | Anthropic only | Any (OpenAI, Anthropic, Gemini, etc.) |
| **Multi-Agent** | Manual orchestration | First-class support with StateGraph |
| **Industry Adoption** | Growing | 25% of production teams (per survey) |
| **Observability** | Custom (Laminar) | Built-in LangSmith |
| **State Management** | Implicit (conversation) | Explicit (TypedDict) |

**Key insight:** We're not abandoning Claude SDK - we're adding another tool to your belt. In production, you'll likely use both depending on the use case.

---

## Concept Mapping

### 1. Agent Definition

**Claude Agent SDK (W1-W2):**
```python
from claude_code_sdk import Agent

agent = Agent(
    model="claude-sonnet-4-20250514",
    system_prompt="You are a research assistant...",
    tools=[linkedin_tool, company_tool],
)

result = agent.run("Research this person...")
```

**LangGraph (W3+):**
```python
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

async def research_node(state: ResearchState) -> dict:
    llm = ChatOpenAI(model="gpt-4.1", temperature=0)
    result = await llm.ainvoke([
        SystemMessage(content="You are a research assistant..."),
        HumanMessage(content=f"Research: {state['linkedin_url']}")
    ])
    return {"research_result": result.content}

graph = StateGraph(ResearchState)
graph.add_node("research", research_node)
```

### 2. Tool Definition

**Claude Agent SDK:**
```python
from claude_code_sdk import tool

@tool
def fetch_linkedin(url: str) -> dict:
    """Fetch LinkedIn profile data."""
    return httpx.get(API_URL, params={"url": url}).json()
```

**LangGraph (LangChain):**
```python
from langchain_core.tools import tool

@tool
def fetch_linkedin(url: str) -> dict:
    """Fetch LinkedIn profile data."""
    return httpx.get(API_URL, params={"url": url}).json()
```

**Note:** Same decorator name, different import!

### 3. State Management

**Claude Agent SDK:**
```python
# State is implicit - stored in conversation history
result = agent.run("Continue from where we left off...")
# Agent remembers previous context automatically
```

**LangGraph:**
```python
# State is explicit - defined as TypedDict
class ResearchState(TypedDict):
    linkedin_url: str           # Input
    linkedin_data: dict | None  # Intermediate
    final_report: str           # Output
    messages: Annotated[list, add_messages]  # History

# You control exactly what flows between nodes
```

### 4. Multi-Agent Orchestration

**Claude Agent SDK (manual):**
```python
# You write the orchestration loop
linkedin_result = linkedin_agent.run(query)
company_result = company_agent.run(query)
news_result = news_agent.run(query)

# Manual synthesis
synthesis_agent.run(f"""
Combine these results:
LinkedIn: {linkedin_result}
Company: {company_result}
News: {news_result}
""")
```

**LangGraph (built-in):**
```python
# Graph handles orchestration
graph.add_edge("orchestrator", "linkedin_agent")  # Parallel
graph.add_edge("orchestrator", "company_agent")   # Parallel
graph.add_edge("orchestrator", "news_agent")      # Parallel

# All three run concurrently, then fan-in to synthesis
graph.add_edge("linkedin_agent", "synthesis")
graph.add_edge("company_agent", "synthesis")
graph.add_edge("news_agent", "synthesis")
```

### 5. Control Flow

**Claude Agent SDK:**
```python
# Agent decides what to do next (tool calls)
# You influence via system prompt
```

**LangGraph:**
```python
# Explicit edges (unconditional)
graph.add_edge("step_a", "step_b")

# Conditional routing
def should_continue(state) -> str:
    if state["needs_review"]:
        return "human_review"
    return "finalize"

graph.add_conditional_edges("check", should_continue, {...})
```

### 6. Observability

**Claude Agent SDK + Laminar (W2):**
```python
from laminar import Laminar
Laminar.initialize(project_api_key="...")

@observe(name="research_agent")
def research(query):
    ...
```

**LangGraph + LangSmith (W3):**
```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "..."
os.environ["LANGCHAIN_PROJECT"] = "research-squad"

# That's it - all graph executions are automatically traced
```

---

## When to Use Which?

| Use Case | Recommended |
|----------|-------------|
| Single-agent with Claude models | Claude Agent SDK |
| Multi-agent orchestration | LangGraph |
| Need vendor flexibility | LangGraph |
| Simple tool-calling agent | Claude Agent SDK |
| Complex workflows with routing | LangGraph |
| Human-in-the-loop patterns | LangGraph |
| Production multi-model optimization | LangGraph |

---

## API Key Migration

**W1-W2 (.env):**
```
ANTHROPIC_API_KEY=sk-ant-xxx
LAMINAR_API_KEY=xxx
```

**W3+ (.env):**
```
OPENAI_API_KEY=sk-xxx
LANGCHAIN_API_KEY=lsv2_xxx
TAVILY_API_KEY=tvly-xxx
```

---

## Common Migration Patterns

### Pattern 1: Single Agent to Node

```python
# Before (Claude SDK)
agent = Agent(model="claude-sonnet-4", tools=[tool1, tool2])
result = agent.run(query)

# After (LangGraph)
async def agent_node(state: MyState) -> dict:
    llm = ChatOpenAI(model="gpt-4.1")
    llm_with_tools = llm.bind_tools([tool1, tool2])
    result = await llm_with_tools.ainvoke([...])
    return {"result": result.content}
```

### Pattern 2: Reflection Loop to Conditional Edge

```python
# Before (W2 - manual loop)
for attempt in range(max_attempts):
    result = agent.run(query)
    critique = critic.run(result)
    if critique.passed:
        break
    query = f"Improve based on: {critique}"

# After (LangGraph)
def should_continue(state) -> str:
    if state["critique_passed"]:
        return END
    return "improve_agent"

graph.add_conditional_edges("critic", should_continue, {...})
```

---

## Key Mindset Shifts

1. **Implicit → Explicit State**: You define exactly what data flows
2. **Agent Decides → Graph Decides**: Control flow is in the graph structure
3. **Single Model → Model per Node**: Optimize cost/capability per task
4. **Conversation → TypedDict**: Structured data instead of message history
5. **Manual Tracing → Automatic**: LangSmith traces everything by default

---

## Resources

- [LangGraph Quickstart](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
- [Claude Agent SDK Docs](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code)
- [LangSmith Setup](https://docs.smith.langchain.com/setup)
