"""
Multi-Agent Swarm Orchestration

Demonstrates the "Agent Swarm" pattern:
- Main agent coordinates work
- Sub-agents run in parallel with isolated context windows
- Tasks system manages dependencies
- Results are synthesized back to main agent

Key benefits:
- Each sub-agent gets fresh 200k context window
- No context pollution between tasks
- Parallel execution for speed
- Model selection per task (Haiku for simple, Opus for complex)

Run:
    python agent_orchestration/multi_agent_swarm.py
"""

import asyncio
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)

try:
    from tasks_basic import TaskList
except ImportError:
    from .tasks_basic import TaskList


# =============================================================================
# Sub-Agent Definition
# =============================================================================

@dataclass
class SubAgent:
    """Represents a sub-agent that can execute tasks."""
    id: str
    model: str
    max_tokens: int
    system_prompt: str


# Different agent types for different tasks
AGENTS = {
    "researcher": SubAgent(
        id="researcher",
        model="claude-sonnet-4-5-20250929",  # Good balance for research
        max_tokens=2000,
        system_prompt="""You are a research agent. Your job is to analyze information
and provide clear, factual summaries.

Output your findings in this format:
<findings>
- Key point 1
- Key point 2
- Key point 3
</findings>

<confidence>high/medium/low</confidence>

<sources>
List any sources or assumptions
</sources>
"""
    ),
    "analyst": SubAgent(
        id="analyst",
        model="claude-sonnet-4-5-20250929",
        max_tokens=3000,
        system_prompt="""You are an analysis agent. Your job is to synthesize
multiple research findings into insights and recommendations.

Output your analysis in this format:
<synthesis>
Combined insights from all inputs
</synthesis>

<recommendations>
1. Recommendation 1
2. Recommendation 2
3. Recommendation 3
</recommendations>
"""
    ),
    "writer": SubAgent(
        id="writer",
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        system_prompt="""You are a writing agent. Your job is to transform
analysis into clear, professional documents.

Write in a clear, professional tone suitable for business stakeholders.
"""
    )
}


# =============================================================================
# Swarm Coordinator
# =============================================================================

class SwarmCoordinator:
    """Coordinates multiple sub-agents working on a task list."""

    def __init__(self, list_id: str):
        """Initialize swarm coordinator.

        Args:
            list_id: Task list ID to use for coordination
        """
        self.tasks = TaskList(list_id=list_id)
        self.client = anthropic.AsyncAnthropic()
        self.results: dict[str, str] = {}  # task_id -> result

    async def run_sub_agent(
        self,
        agent: SubAgent,
        task_prompt: str,
        context: str = ""
    ) -> str:
        """Run a sub-agent with isolated context.

        Args:
            agent: SubAgent configuration to use
            task_prompt: Specific task for this agent
            context: Any context from previous tasks

        Returns:
            Agent's response
        """
        messages = []

        if context:
            messages.append({
                "role": "user",
                "content": f"<context>\n{context}\n</context>\n\n{task_prompt}"
            })
        else:
            messages.append({
                "role": "user",
                "content": task_prompt
            })

        response = await self.client.messages.create(
            model=agent.model,
            max_tokens=agent.max_tokens,
            system=agent.system_prompt,
            messages=messages
        )

        return response.content[0].text

    def get_dependency_context(self, task_id: str) -> str:
        """Get results from tasks this task depends on.

        Args:
            task_id: Task to get dependency context for

        Returns:
            Combined results from all dependencies
        """
        task = self.tasks.get(task_id)
        if not task or not task.blocked_by:
            return ""

        context_parts = []
        for dep_id in task.blocked_by:
            if dep_id in self.results:
                dep_task = self.tasks.get(dep_id)
                if dep_task:
                    context_parts.append(
                        f"<result task_id=\"{dep_id}\" task=\"{dep_task.subject}\">\n"
                        f"{self.results[dep_id]}\n"
                        f"</result>"
                    )

        return "\n\n".join(context_parts)

    async def execute_available(self) -> list[str]:
        """Execute all currently available tasks in parallel.

        Returns:
            List of completed task IDs
        """
        available = self.tasks.list_available()

        if not available:
            return []

        print(f"\n  Executing {len(available)} tasks in parallel:")
        for t in available:
            print(f"    - {t.id}: {t.subject}")

        # Create coroutines for parallel execution
        async def execute_task(task):
            # Mark as in progress
            self.tasks.update(task.id, status="in_progress")

            # Get context from dependencies
            context = self.get_dependency_context(task.id)

            # Determine which agent to use based on task metadata or description
            agent_type = task.metadata.get("agent_type", "researcher")
            agent = AGENTS.get(agent_type, AGENTS["researcher"])

            print(f"    [{task.id}] Running with {agent.id} agent...")

            # Run sub-agent
            result = await self.run_sub_agent(
                agent=agent,
                task_prompt=task.description,
                context=context
            )

            # Store result
            self.results[task.id] = result

            # Mark as completed
            self.tasks.update(task.id, status="completed")

            print(f"    [{task.id}] Completed")

            return task.id

        # Execute all available tasks in parallel
        completed = await asyncio.gather(*[
            execute_task(task) for task in available
        ])

        return list(completed)

    async def run_until_complete(self) -> dict[str, str]:
        """Run all tasks until completion.

        Returns:
            Dictionary of task_id -> result for all tasks
        """
        print("\nStarting swarm execution...")

        step = 1
        while True:
            pending = [t for t in self.tasks.list_all() if t.status != "completed"]
            if not pending:
                break

            print(f"\n--- Step {step} ---")
            completed = await self.execute_available()

            if not completed:
                # Check for blocked tasks
                blocked = [t for t in pending if t.status == "pending"]
                if blocked:
                    print("  Warning: Tasks are blocked but no tasks completed")
                    print(f"  Blocked: {[t.subject for t in blocked]}")
                break

            step += 1

        print("\n=== Execution Complete ===")
        return self.results


# =============================================================================
# Demo: Competitor Research Swarm
# =============================================================================

async def demo_research_swarm():
    """Demonstrate a multi-agent research swarm."""
    print("\n" + "=" * 60)
    print(" Multi-Agent Research Swarm Demo")
    print("=" * 60)

    # Create task list
    coordinator = SwarmCoordinator(list_id="research-swarm")

    # Clear existing tasks
    coordinator.tasks.tasks.clear()
    coordinator.tasks._next_id = 1

    # Create research tasks (parallel)
    t1 = coordinator.tasks.create(
        subject="Research Competitor A",
        description="""Research Acme Corp's pricing strategy:
- What pricing tiers do they offer?
- What features are in each tier?
- What's their pricing model (per user, per feature, flat)?

Focus on their enterprise offering.""",
    )
    coordinator.tasks.update(t1.id, metadata={"agent_type": "researcher"})

    t2 = coordinator.tasks.create(
        subject="Research Competitor B",
        description="""Research TechGiant's pricing strategy:
- What pricing tiers do they offer?
- What features are in each tier?
- What's their pricing model?

Focus on their startup/SMB offering.""",
    )
    coordinator.tasks.update(t2.id, metadata={"agent_type": "researcher"})

    t3 = coordinator.tasks.create(
        subject="Research Competitor C",
        description="""Research StartupX's pricing strategy:
- What pricing tiers do they offer?
- What features are in each tier?
- What differentiates them?

Focus on their unique value proposition.""",
    )
    coordinator.tasks.update(t3.id, metadata={"agent_type": "researcher"})

    # Create synthesis task (depends on all research)
    t4 = coordinator.tasks.create(
        subject="Synthesize competitive analysis",
        description="""Based on the research on Acme Corp, TechGiant, and StartupX:

1. Compare their pricing models
2. Identify gaps in the market
3. Recommend a pricing strategy that differentiates us

Provide actionable recommendations.""",
        blocked_by=[t1.id, t2.id, t3.id]
    )
    coordinator.tasks.update(t4.id, metadata={"agent_type": "analyst"})

    # Create report task (depends on synthesis)
    t5 = coordinator.tasks.create(
        subject="Write pricing strategy report",
        description="""Create a executive summary report on recommended pricing strategy.

Include:
- Market overview
- Key findings from competitor analysis
- Recommended pricing tiers
- Next steps

Keep it concise (1 page maximum).""",
        blocked_by=[t4.id]
    )
    coordinator.tasks.update(t5.id, metadata={"agent_type": "writer"})

    # Show task structure
    print("\nTask structure:")
    coordinator.tasks.print_status()

    # Run the swarm
    results = await coordinator.run_until_complete()

    # Show results
    print("\n" + "=" * 60)
    print(" Results")
    print("=" * 60)

    for task_id, result in results.items():
        task = coordinator.tasks.get(task_id)
        print(f"\n--- Task {task_id}: {task.subject} ---")
        print(result[:500] + "..." if len(result) > 500 else result)


async def demo_agent_swarm_concept():
    """Explain the agent swarm concept without API calls."""
    print("\n" + "=" * 60)
    print(" Agent Swarm Concept")
    print("=" * 60)

    print("""
The Agent Swarm pattern enables complex multi-agent workflows:

┌─────────────────────────────────────────────────────────────┐
│                    MAIN AGENT                                │
│  (Coordinator - manages tasks, context is minimal)          │
└─────────────────────┬───────────────────────────────────────┘
                      │ Creates task list
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   TASK LIST                                  │
│  Task 1: Research A    [pending]                            │
│  Task 2: Research B    [pending]                            │
│  Task 3: Research C    [pending]                            │
│  Task 4: Synthesize    [blocked by 1,2,3]                   │
│  Task 5: Report        [blocked by 4]                       │
└─────────────────────┬───────────────────────────────────────┘
                      │ Spawns sub-agents
                      ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  SUB-AGENT  │ │  SUB-AGENT  │ │  SUB-AGENT  │
│   (Task 1)  │ │   (Task 2)  │ │   (Task 3)  │
│ Fresh 200k  │ │ Fresh 200k  │ │ Fresh 200k  │
│  context    │ │  context    │ │  context    │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │ Run in parallel
       └───────────────┼───────────────┘
                       ▼
              Results stored in files
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  SUB-AGENT (Task 4) - Gets context from Task 1,2,3 results  │
│  Fresh 200k context window                                   │
└─────────────────────────────────────────────────────────────┘

Key Benefits:
1. Fresh Context: Each sub-agent starts with clean 200k window
2. No Pollution: Task 1's exploration doesn't affect Task 2
3. Parallel Speed: Independent tasks run simultaneously
4. Model Selection: Use Haiku for simple, Opus for complex
5. Persistence: Task list survives across sessions
""")


async def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY not set")
        print("Running concept demo only (no API calls)")
        await demo_agent_swarm_concept()
        return

    print("\nMulti-Agent Swarm Demo")
    print("=" * 60)
    print("1. Concept explanation (no API)")
    print("2. Live research swarm demo (uses API)")

    choice = input("\nChoice [1/2]: ").strip()

    if choice == "2":
        await demo_research_swarm()
    else:
        await demo_agent_swarm_concept()


if __name__ == "__main__":
    asyncio.run(main())
