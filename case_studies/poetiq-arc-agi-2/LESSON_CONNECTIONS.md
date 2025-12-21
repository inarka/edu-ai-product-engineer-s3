# Lesson Connections: Poetiq ARC-AGI-2

How Poetiq's SOTA approach maps to course concepts.

---

## Lesson 2: Building Reliable Agents

### The Reflection Pattern

**Course Version (L2)**:
```
Turn 1: Generate V1 Research (initial)
         ↓
Turn 2: Collect External Feedback (human review)
         ↓
Turn 3: Reflect and Generate V2 (improved)
```

**Poetiq's Version**:
```
Iteration 1: Generate Python transform() function
         ↓
Iteration 2: Execute code, collect errors + soft scores
         ↓
Iteration 3-10: Feed errors back, generate improved code
```

**Key Difference**: Poetiq's reflection is **grounded in execution**. Instead of human feedback or LLM self-critique, they get ground-truth from running actual code. This eliminates hallucinated quality assessments.

### External Feedback Sources

| L2 Feedback Source | Poetiq Equivalent |
|--------------------|-------------------|
| Human-in-the-loop (CLI) | Code execution results |
| Data quality signals (EnrichLayer) | Soft scoring (pixel accuracy) |
| Quality assessment in tool response | Pass/fail on training examples |

**Lesson**: External feedback breaks the "prompt engineering plateau" — Poetiq proves this works at SOTA scale.

### Improved Tool Design

L2 teaches structured tool docstrings with:
- `USE WHEN` clauses
- `RETURNS ON SUCCESS/ERROR` sections

Poetiq's prompts use similar patterns:
- Explicit transformation taxonomies (Color, Spatial, Pattern)
- Clear output format requirements (`def transform(grid)`)
- Constraint specification (numpy only, no main blocks)

---

## Lesson 3: Multi-Agent Systems with LangGraph

### The Research Squad Pattern = Poetiq's Multi-Expert Architecture

| L3 Research Squad | Poetiq ARC-AGI-2 |
|-------------------|------------------|
| Orchestrator node | Main solver entry |
| 3 parallel agents (LinkedIn, Company, News) | 8 parallel experts (different seeds/models) |
| Fan-out from orchestrator | `asyncio.gather(*tasks)` |
| Synthesis node combines results | Voting-based consensus |
| StateGraph for explicit state | `solutions`, `scores`, `votes` tracking |

### LangGraph Concept Mapping

**Fan-Out/Fan-In (L3 Parallel Execution):**
```python
# L3 Research Squad
graph.add_edge("orchestrator", "linkedin_agent")
graph.add_edge("orchestrator", "company_agent")
graph.add_edge("orchestrator", "news_agent")

# Poetiq equivalent
tasks = [asyncio.create_task(solve_coding(cfg)) for cfg in expert_configs]
results = await asyncio.gather(*tasks)
```

**Model Optimization per Node (L3 Architecture):**
```python
# L3 pattern - different models per agent
linkedin_agent: gpt-4.1-mini  # Cheaper, focused
synthesis:      gpt-4.1       # More capable

# Poetiq pattern - different models per expert
expert_1: Gemini 2.5 Pro
expert_2: GPT-5.1
expert_3: Claude
```

### The Subagents Pattern at Scale

L3 teaches the **Subagents pattern** (Multi-Agent Patterns): Central agent invokes specialists as tools.

Poetiq implements this at scale:
- **Central orchestrator**: `solve_parallel_coding.py`
- **8 specialist subagents**: Each with different seeds/models
- **Context isolation**: Agents don't communicate during solving
- **Parallel execution**: All experts run concurrently

### Diversity-First = Many-Model Thinking

L3's **Pattern Selection Matrix** emphasizes choosing patterns for distributed development and parallelization. Poetiq proves this works:

```
L3 Teaching: "Use different models per agent for cost optimization"
Poetiq Result: 8 diverse experts → 54% accuracy vs 45% single model
               $30/problem vs $77/problem (60% cost reduction)
```

**Scott Page's Diversity Prediction Theorem** (mentioned in Poetiq README):
> Collective Error = Average Individual Error - Diversity

This is exactly why L3's multi-agent patterns work — diversity of processing beats a single powerful processor.

### Human-in-the-Loop vs Execution-Based Feedback

| L3 Pattern | Poetiq Pattern |
|------------|----------------|
| `interrupt_before=["synthesis"]` | Pause before voting |
| Human reviews intermediate results | Code execution provides feedback |
| Resume with `graph.ainvoke(None, config)` | Feed errors back to LLM |

**Key Insight**: Poetiq's "human" is the Python interpreter — ground-truth feedback that can't hallucinate.

---

## Cross-Cutting Concepts

### Intelligence as Process, Not Just Model

| Course Teaching | Poetiq Evidence |
|-----------------|-----------------|
| Agentic > Chained (L1) | Iterative refinement beats single-pass |
| Reflection improves output (L2) | 10 iterations find solutions 1 pass misses |
| Multi-agent + Fan-out (L3) | 8 parallel experts with voting outperform monolithic approach |
| Model optimization per node (L3) | Different models for different tasks = cost efficiency |

### Cost Efficiency Through Orchestration

**Course Principle (L3 When to Decompose)**: Only decompose when you meet 3+ criteria. Poetiq meets multiple of the 7 criteria:

| L3 Criterion | Poetiq Implementation |
|--------------|----------------------|
| 1. Parallelization benefit | 8 experts run concurrently |
| 2. Context window efficiency | Each expert has focused context |
| 3. Different domain experts | Different LLMs (Gemini, GPT, Claude) |
| 4. Time/cost optimization | Mix of models for cost/capability |
| 5. Failure isolation | Isolated execution sandboxes |
| 6. Reusability | Expert pattern reused across problems |

**Result**:
- Previous SOTA: $77.16/problem
- Poetiq: $30.57/problem
- **60% cost reduction** through intelligent orchestration

---

## Discussion Questions

1. **L2 Connection**: How does Poetiq's execution-based feedback compare to human-in-the-loop? What are the tradeoffs?

2. **L3 Connection**: Why might 8 diverse experts with voting beat a single more powerful model? Connect to Scott Page's Diversity Prediction Theorem and L3's 7 decomposition criteria.

3. **Architecture Choice**: Poetiq chose code generation over direct answer prediction. How does this enable better reflection? What other domains could use "executable intermediate representations"?

4. **L3 Application**: Could you apply the Research Squad pattern to Poetiq? Design a LangGraph StateGraph with parallel coding experts and a voting synthesis node.

5. **Model Selection**: L3 teaches using gpt-4.1-mini for subagents and gpt-4.1 for synthesis. How does this map to Poetiq's multi-model approach? What would you choose for a production system?
