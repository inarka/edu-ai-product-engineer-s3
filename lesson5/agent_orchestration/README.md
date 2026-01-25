# Agent Orchestration Examples

This directory contains Python examples that explain the concepts behind multi-agent orchestration.

## Files

- **`tasks_basic.py`** - Introduction to the Claude Code Tasks system
- **`tasks_with_dependencies.py`** - How `blockedBy` enforces execution order
- **`multi_agent_swarm.py`** - Conceptual multi-agent swarm implementation
- **`spec_driven_workflow.py`** - Spec-driven development pattern

---

## Try It Yourself: claudesp Swarm Mode

The Python examples above explain the concepts. **For the real experience**, install `claudesp` (claude-sneakpeek):

### Installation

```bash
npx @realmikekelly/claude-sneakpeek quick --name claudesp
```

### Basic Usage

```bash
claudesp
```

Then try:

```
> propose a plan to implement [your project idea]
> use swarm mode to implement this
```

### What claudesp Does

| Feature | Description |
|---------|-------------|
| **Teammate()** | Spawns parallel sub-agents |
| **Team creation** | `Teammate(create team: "project-name")` |
| **Dependencies** | `blockedBy` enforces execution order |
| **Message passing** | `Teammate(send message to: "agent-name")` |
| **Parallel execution** | 10+ agents working simultaneously |

### Why claudesp Over Python Examples

| Aspect | Python Examples | claudesp |
|--------|-----------------|----------|
| Reality | Conceptual code | Working tool |
| Agents | Simulated | Real Claude instances |
| Parallel | `asyncio.gather` mockup | 10 agents simultaneously |
| Persistence | JSON files | `~/.claude/tasks/` |
| Visual | Terminal output | Live progress in TUI |

### Example Session

```bash
# Start claudesp
claudesp

# Inside claudesp, propose a project
> propose a plan to implement a CLI tool that tracks daily habits

# Watch it create tasks, then trigger swarm mode
> use swarm mode to implement this

# Observe:
# - Multiple agents spawn in parallel
# - Tasks with dependencies wait automatically
# - Each agent gets fresh 200k context window
# - Results written to files, not held in memory
```

### Resources

- **Repository**: https://github.com/mikekelly/claude-sneakpeek
- **Demo project**: See AgentControlTower - a complete macOS Swift app built by claudesp
- **Workshop slides**: Section 3 covers the theory behind this

---

## Running the Python Examples

If you want to explore the conceptual code:

```bash
# Activate the lesson5 virtual environment
cd /path/to/edu-ai-product-engineer-s3/lesson5
source venv/bin/activate

# Run individual examples
python agent_orchestration/tasks_basic.py
python agent_orchestration/tasks_with_dependencies.py
python agent_orchestration/multi_agent_swarm.py
```

These examples demonstrate the patterns but don't execute real agent swarms. For that, use claudesp.
