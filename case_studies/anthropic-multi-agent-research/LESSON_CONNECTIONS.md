# Lesson Connections: Anthropic Multi-Agent Research System

How Anthropic's production multi-agent system maps to course concepts.

---

## Lesson 3: Multi-Agent Systems with LangGraph

### The Research Squad Pattern = Anthropic's Architecture

| L3 Research Squad | Anthropic Research System |
|-------------------|---------------------------|
| Orchestrator node | Lead agent (Opus 4) creates strategy |
| 3 parallel agents (LinkedIn, Company, News) | N parallel subagents (Sonnet 4) explore aspects |
| Fan-out from orchestrator | Subagents operate in parallel |
| Synthesis node combines results | Lead agent synthesizes findings |
| StateGraph for explicit state | Internal state tracking |

### LangGraph Concept Mapping

**Fan-Out/Fan-In (L3 Parallel Execution):**
```python
# L3 Research Squad
graph.add_edge("orchestrator", "linkedin_agent")
graph.add_edge("orchestrator", "company_agent")
graph.add_edge("orchestrator", "news_agent")

# Anthropic equivalent
aspects = lead_agent.decompose(query)
tasks = [subagent.explore(aspect) for aspect in aspects]
results = await asyncio.gather(*tasks)  # Parallel execution
```

**Model Optimization per Node (L3 Architecture):**
```python
# L3 pattern - different models per agent
linkedin_agent: gpt-4.1-mini  # Cheaper, focused
synthesis:      gpt-4.1       # More capable

# Anthropic pattern - same principle, different models
lead_agent:     Claude Opus 4    # Most capable for strategy/synthesis
subagents:      Claude Sonnet 4  # Balanced for focused exploration
citation_agent: Claude Sonnet 4  # Structured extraction
```

**Result**: 90% improvement over single Opus agent.

### The Subagents Pattern (L3 Multi-Agent Patterns)

L3 teaches: "Central agent invokes specialists as tools"

Anthropic implements exactly this:
- **Lead agent** = Central orchestrator
- **Subagents** = Specialists invoked for specific aspects
- **Context isolation** = Each subagent gets focused prompt
- **Parallel execution** = All subagents run concurrently

### Decomposition Criteria Validation (L3 When to Decompose)

Anthropic's system meets multiple criteria for decomposition (L3 teaches 7 criteria):

| L3 Criterion | Anthropic Implementation |
|--------------|-------------------------|
| 1. Parallelization benefit | Subagents run concurrently |
| 2. Context window efficiency | Each subagent gets focused prompt |
| 3. Different domain experts | Lead (strategy), Research (exploration), Citation (attribution) |
| 4. Time/cost optimization | Opus lead + Sonnet subagents = 90% improvement |
| 5. Failure isolation | One subagent failing doesn't kill entire research |
| 6. Reusability | Subagent pattern reused across queries |

**Rule validation**: 6/7 criteria met → strong signal to decompose.

---

## Lesson 3 → Lesson 4 Bridge: Production Concerns

Anthropic's case study previews L4 topics:

### Rainbow Deployments
```
Problem: Deploying updates kills running agents mid-research
Solution: Route NEW requests to new version, let existing agents complete
```

This is critical for long-running agent processes.

### Stateful Error Handling
```
Problem: Agents are stateful - one bad tool call compounds errors
Solution:
  - Resumable execution
  - Graceful error handling
  - Fallback strategies
```

### Production Tracing
```
Problem: Non-deterministic behavior is hard to debug
Solution: Trace every:
  - Tool call
  - Decision point
  - State transition
  - Model response
```

Maps directly to LangSmith tracing (L3 Observability).

### LLM-as-Judge Evaluation
```python
# For free-form research outputs
evaluator = LLM("gpt-4")
score = evaluator.evaluate(
    output=research_result,
    criteria=["accuracy", "completeness", "citation_quality"]
)
```

This extends L2's quality assessment patterns.

---

## Cross-Cutting Concepts

### Intelligence as Orchestration

| Course Teaching | Anthropic Evidence |
|-----------------|-------------------|
| Multi-agent > Single agent (L3) | 90% improvement with orchestration |
| Model per node (L3) | Opus lead + Sonnet workers = better + cheaper |
| Fan-out for parallelization (L3) | Parallel subagents enable concurrent exploration |
| Synthesis combines diverse results (L3) | Lead agent synthesizes subagent findings |

### Cost Efficiency Through Architecture

**Single Agent Approach:**
- Use Opus for everything
- High cost per query
- No parallelization

**Multi-Agent Approach:**
- Opus for strategy/synthesis (high-value tasks)
- Sonnet for exploration (high-volume tasks)
- Result: Better quality at lower cost

---

## Discussion Questions

1. **L3 Connection**: How does Anthropic's lead/subagent model map to the Subagents pattern? What are the tradeoffs of using different model tiers?

2. **Model Selection**: Anthropic uses Opus for lead + Sonnet for subagents. How would you apply this to your homework? Which tasks warrant the most capable model?

3. **Parallelization**: Anthropic achieved significant speedup through parallel execution. What are the risks of parallel fan-out? When might sequential be better?

4. **Production Readiness**: Rainbow deployments and error handling aren't in the LangGraph tutorial. Why are they critical for production? How would you implement them?

5. **Evaluation**: Anthropic uses LLM-as-judge for research quality. How does this compare to L2's reflection pattern? What are the pros/cons?

---

## Key Insight

> "A multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2%"

This validates the core L3 teaching: **intelligent orchestration of specialized agents beats a single powerful model** — and does so at lower cost.
