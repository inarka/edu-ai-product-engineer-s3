# Case Study: Anthropic's Multi-Agent Research System

How Anthropic built a production multi-agent system that powers Claude's Research feature, achieving 90% improvement over single-agent approaches.

**Source**: [Building effective agents: Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)

---

## Overview

Anthropic's Research feature enables Claude to conduct comprehensive web searches and synthesize information from multiple sources to answer complex questions. Under the hood, it's powered by a **multi-agent orchestrator-worker architecture** that demonstrates production-grade patterns for coordinating specialized agents.

### The Challenge

Complex research queries require:
- Exploring multiple information sources in parallel
- Synthesizing diverse findings into coherent answers
- Ensuring proper citation and attribution
- Scaling effort based on query complexity

A single agent with all tools becomes overwhelmed. The solution: **orchestrated multi-agent collaboration**.

---

## Architecture

```
                    ┌─────────────────┐
                    │   Lead Agent    │
                    │  (Claude Opus)  │
                    │ Creates strategy│
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Subagent 1    │  │   Subagent 2    │  │   Subagent N    │
│ (Claude Sonnet) │  │ (Claude Sonnet) │  │ (Claude Sonnet) │
│  Aspect A       │  │  Aspect B       │  │  Aspect N       │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └───────────────────┬┴───────────────────┘
                             ▼
                    ┌─────────────────┐
                    │  Lead Agent     │
                    │  (Synthesis)    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Citation Agent  │
                    │ (Attribution)   │
                    └─────────────────┘
```

### Key Components

| Component | Model | Role |
|-----------|-------|------|
| **Lead Agent** | Claude Opus 4 | Analyzes query, creates strategy, synthesizes results |
| **Subagents** | Claude Sonnet 4 | Parallel exploration of specific aspects |
| **Citation Agent** | Claude Sonnet 4 | Ensures proper source attribution |

### The 90% Improvement

> "A multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2%"

This validates a core course principle: **intelligent orchestration of diverse agents beats scaling a single model**.

---

## Production Lessons Learned

### 1. Prompt Engineering for Orchestrators

**Teach explicit delegation strategies:**
- "Break this into 3-5 sub-questions"
- "Assign each sub-question to a subagent"
- "Provide detailed context for each delegation"

**Scale effort based on complexity:**
- Simple queries → fewer subagents, less depth
- Complex queries → more subagents, deeper exploration

### 2. Parallel Execution Matters

Implementing parallel tool calling reduced research time by **up to 90%**. Sequential execution is too slow for production research.

```python
# Pattern: Fan-out to parallel subagents
tasks = [subagent.explore(aspect) for aspect in aspects]
results = await asyncio.gather(*tasks)  # Parallel execution
```

### 3. Extended Thinking for Planning

Using extended thinking (chain-of-thought) for the lead agent's planning phase improves:
- Strategy quality
- Task decomposition
- Result synthesis

### 4. Evaluation Strategies

**Start small**: Begin with 20 test cases, not 1000. Iterate quickly.

**LLM-as-judge**: For free-form research outputs, use an LLM to evaluate quality against criteria:
- Accuracy
- Completeness
- Citation quality
- Coherence

**Human testing catches edge cases** that automated evals miss. Always include human review.

### 5. Production Operations

**Agents are stateful - errors compound:**
- One bad tool call can derail an entire research flow
- Implement resumable execution
- Add graceful error handling with fallbacks

**Rainbow deployments:**
- Don't kill running agents when deploying updates
- Route new requests to new version
- Let existing agents complete naturally

**Production tracing is essential:**
- Non-deterministic behavior requires detailed logs
- Trace every tool call, decision, and state transition
- Enables debugging of "why did the agent do X?"

---

## Key Patterns

### Pattern 1: Model Optimization per Role

| Role | Model | Why |
|------|-------|-----|
| Lead Agent | Opus 4 (most capable) | Complex reasoning, synthesis |
| Subagents | Sonnet 4 (balanced) | Focused tasks, cost efficiency |
| Citation | Sonnet 4 | Structured extraction |

**Result**: Better performance at lower cost than using Opus everywhere.

### Pattern 2: Parallel Fan-Out with Synthesis

```
Lead Agent (strategy)
    ↓
[Subagent 1] [Subagent 2] [Subagent 3]  ← Parallel
    ↓
Lead Agent (synthesis)
```

This is exactly the **Subagents pattern** from LangChain's multi-agent framework.

### Pattern 3: Specialized Citation Agent

Rather than asking research agents to also handle citations, a dedicated **Citation Agent** ensures:
- Consistent attribution format
- No missed sources
- Clean separation of concerns

---

## Results

| Metric | Single Agent (Opus) | Multi-Agent System |
|--------|--------------------|--------------------|
| Quality Score | Baseline | **+90.2%** |
| Research Time | Baseline | **-90%** (with parallel) |
| Cost per Query | High (all Opus) | Lower (Opus + Sonnet mix) |

---

## Key Takeaways

1. **Orchestration beats scaling**: Multi-agent with model mix outperforms single powerful model
2. **Parallel execution is essential**: Sequential is too slow for production
3. **Specialized agents > generalist agents**: Citation agent, research agents, lead agent each do one thing well
4. **Production != prototypes**: Rainbow deployments, tracing, error handling are critical
5. **Start eval small**: 20 test cases → iterate → expand

---

## Course Connections

This case study directly validates W3 concepts:

| Course Concept | Anthropic Implementation |
|----------------|-------------------------|
| Orchestrator pattern | Lead agent creates strategy |
| Fan-out/Fan-in | Subagents explore in parallel |
| Model per node | Opus lead + Sonnet subagents |
| Synthesis node | Lead agent combines findings |
| Human-in-the-loop | Human testing catches edge cases |

See [LESSON_CONNECTIONS.md](./LESSON_CONNECTIONS.md) for detailed mapping.

---

## Further Reading

- [Original Blog Post](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Building effective agents (Anthropic)](https://www.anthropic.com/research/building-effective-agents)
- [Multi-agent patterns (LangChain)](https://docs.langchain.com/oss/python/langchain/multi-agent)
