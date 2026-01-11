# Lesson 4: Evaluation-Driven Development + Deep Agents

## "From 'It Works' to 'I Can Prove It Works'"

This lesson teaches you how to systematically evaluate AI products and introduces LangChain's Deep Agents SDK as an evolution from W3's LangGraph approach.

## Learning Objectives

By the end of this lesson, you will be able to:

1. **Design evaluation strategies** using the 50-40-10 rule (Automated, LLM-as-Judge, Human)
2. **Create evaluation datasets** with diverse test cases (happy path, edge cases, adversarial)
3. **Implement evaluators** for schema validation, keyword coverage, and semantic quality
4. **Compare approaches** using LangSmith experiments
5. **Understand Deep Agents** for dynamic planning vs static LangGraph graphs

## Prerequisites

- Completed Workshops 1-3
- LangSmith account (free tier is fine)
- API keys for OpenAI and/or Anthropic

## Quick Start

```bash
# Navigate to workspace
cd lesson4/workspace

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run the Deep Research Agent
python deep_research_agent.py --target "satya-nadella" --company "Microsoft"

# Create evaluation dataset
python -m evaluation.dataset

# Run comparison (requires W3 setup)
python -m evaluation.compare
```

## Directory Structure

```
lesson4/
├── workspace/
│   ├── deep_research_agent.py     # Deep Agents implementation
│   ├── evaluation/
│   │   ├── dataset.py             # Dataset creation
│   │   ├── evaluators.py          # All evaluators
│   │   └── compare.py             # Experiment comparison
│   ├── tests/
│   │   └── test_tool_calls.py     # Automated tests
│   ├── requirements.txt
│   └── .env.example
├── skills/
│   └── eval-coach/                # Agent Skill for eval design
│       ├── SKILL.md
│       ├── templates/
│       └── examples/
└── README.md
```

## Key Concepts

### The Evaluation Pyramid (50-40-10 Rule)

```
         /\
        /  \  Human (10%)
       /----\  $5-50/run
      /      \
     /        \  LLM-as-Judge (40%)
    /----------\  $0.01-0.05/run
   /            \
  /              \  Automated (50%)
 /----------------\  $0.00/run
```

### Deep Agents vs LangGraph

| Feature | LangGraph (W3) | Deep Agents (W4) |
|---------|----------------|------------------|
| Graph definition | Compile-time | Runtime (`write_todos`) |
| Subagent spawning | Manual edges | Dynamic `task` tool |
| Context management | State dict | File system tools |
| Best for | Fixed workflows | Dynamic exploration |

## Homework

**Task**: Build an Evaluation Suite for AutoReach

| Requirement | Points |
|-------------|--------|
| Dataset Creation (10+ test cases) | 20 |
| Automated Evaluators (3+) | 25 |
| LLM-as-Judge Evaluators (2+) | 25 |
| Experiment Comparison | 20 |
| Documentation | 10 |

**Bonus (+15)**:
- Human-in-the-loop review flow
- Adversarial test cases
- CI pipeline for regression tests

## Resources

- [LangSmith Evaluation Guide](https://docs.smith.langchain.com/evaluation)
- [Deep Agents Documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [Agent Skills Specification](https://agentskills.io/specification)
- [Eval Coach Skill](skills/eval-coach/SKILL.md)
