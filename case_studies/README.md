# Case Studies

Real-world examples of AI agent patterns in production systems. Each case study connects course concepts to cutting-edge implementations.

## Available Case Studies

| Case Study | Key Patterns | Related Lessons |
|------------|--------------|-----------------|
| [Poetiq ARC-AGI-2 SOTA](./poetiq-arc-agi-2/) | Reflection Pattern, Multi-Model Ensemble | Lesson 2, Lesson 3 |
| [Anthropic Multi-Agent Research](./anthropic-multi-agent-research/) | Orchestrator-Worker, Model Optimization | Lesson 3, Lesson 4 |

---

## Poetiq ARC-AGI-2: Breaking the 50% Barrier

**What**: Poetiq achieved 54% accuracy on ARC-AGI-2, becoming the first to break the 50% barrier while spending half the cost of previous SOTA.

**Why it matters**: Demonstrates that intelligent orchestration of existing models beats scaling a single model — validating core course concepts.

### Course Connections

| Course Concept | Poetiq Implementation |
|----------------|----------------------|
| **Reflection Pattern** (L2) | Iterative code generation with execution-based feedback |
| **External Feedback** (L2) | Ground-truth from actual code execution, not LLM self-critique |
| **Multi-Agent Systems** (L3) | 8 parallel experts with voting-based consensus |
| **Tool Use** (L1-L2) | Code as tool output, sandbox as execution environment |

### Key Insight

> "The future of AI capability may be less about training larger models and more about intelligent orchestration of diverse reasoning processes."

[Read the full analysis →](./poetiq-arc-agi-2/)

---

## Anthropic Multi-Agent Research: 90% Improvement Through Orchestration

**What**: Anthropic built a production multi-agent system powering Claude's Research feature, using an orchestrator-worker pattern with model optimization per role.

**Why it matters**: Demonstrates that a multi-agent architecture with tiered models (Opus lead + Sonnet workers) outperforms a single powerful model by 90% — validating L3's core teaching on model optimization per node.

### Course Connections

| Course Concept | Anthropic Implementation |
|----------------|-------------------------|
| **Orchestrator Pattern** (L3) | Lead agent creates strategy, delegates to subagents |
| **Fan-out/Fan-in** (L3) | Parallel subagent exploration with synthesis |
| **Model per Node** (L3) | Opus lead + Sonnet subagents = 90% improvement |
| **Production Tracing** (L3) | Essential for debugging non-deterministic behavior |
| **Rainbow Deployments** (L4 preview) | Don't kill running agents during updates |

### Key Insight

> "A multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2%"

[Read the full analysis →](./anthropic-multi-agent-research/)

---

## Contributing Case Studies

Have a production AI system that demonstrates course patterns? Case studies should include:

1. **Technical Architecture** — How the system works
2. **Course Connections** — Which patterns from lessons apply
3. **Results & Evidence** — Quantitative outcomes
4. **Key Takeaways** — Lessons for practitioners

Open a PR or discuss in class!
