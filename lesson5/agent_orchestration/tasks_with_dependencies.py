"""
Tasks with Dependencies: blockedBy Chains

Dependencies are the key feature that makes Tasks powerful.
With blockedBy, you can:
- Enforce execution order
- Create parallel workstreams
- Build complex DAGs of work

This file demonstrates advanced dependency patterns.

Run:
    python agent_orchestration/tasks_with_dependencies.py
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Import from our basic module
try:
    from tasks_basic import Task, TaskList
except ImportError:
    from .tasks_basic import Task, TaskList


# =============================================================================
# Dependency Graph Visualization
# =============================================================================

def visualize_dependencies(tasks: TaskList) -> str:
    """Create ASCII visualization of task dependencies.

    Args:
        tasks: TaskList to visualize

    Returns:
        ASCII art representation of the dependency graph
    """
    lines = []
    lines.append("\nDependency Graph:")
    lines.append("-" * 40)

    # Sort tasks by ID for consistent display
    sorted_tasks = sorted(tasks.tasks.values(), key=lambda t: int(t.id))

    for task in sorted_tasks:
        status_icon = {
            "completed": "[x]",
            "in_progress": "[>]",
            "pending": "[ ]"
        }.get(task.status, "[?]")

        # Show what this task blocks
        if task.blocks:
            arrow = f" → blocks: {', '.join(task.blocks)}"
        else:
            arrow = ""

        # Show what blocks this task
        if task.blocked_by:
            deps = f" (needs: {', '.join(task.blocked_by)})"
        else:
            deps = " (ready)"

        lines.append(f"{status_icon} {task.id}: {task.subject}{deps}{arrow}")

    lines.append("-" * 40)
    return "\n".join(lines)


def find_critical_path(tasks: TaskList) -> list[str]:
    """Find the critical path (longest chain of dependencies).

    Args:
        tasks: TaskList to analyze

    Returns:
        List of task IDs in the critical path
    """
    def path_length(task_id: str, memo: dict | None = None) -> tuple[int, list[str]]:
        if memo is None:
            memo = {}
        if task_id in memo:
            return memo[task_id]

        task = tasks.get(task_id)
        if not task:
            return (0, [])

        if not task.blocks:
            # Leaf node
            result = (1, [task_id])
        else:
            # Find longest path through children
            max_length = 0
            max_path: list[str] = []
            for child_id in task.blocks:
                length, path = path_length(child_id, memo)
                if length > max_length:
                    max_length = length
                    max_path = path
            result = (1 + max_length, [task_id] + max_path)

        memo[task_id] = result
        return result

    # Find root tasks (no dependencies)
    roots = [t.id for t in tasks.tasks.values() if not t.blocked_by]

    # Find longest path from any root
    max_length = 0
    critical_path: list[str] = []
    for root_id in roots:
        length, path = path_length(root_id)
        if length > max_length:
            max_length = length
            critical_path = path

    return critical_path


# =============================================================================
# Common Dependency Patterns
# =============================================================================

def demo_sequential_pattern():
    """Demonstrate sequential (waterfall) task pattern."""
    print("\n" + "=" * 60)
    print(" Pattern 1: Sequential (Waterfall)")
    print("=" * 60)

    tasks = TaskList(list_id="sequential-demo")

    # Clear existing tasks for demo
    tasks.tasks.clear()
    tasks._next_id = 1

    # Create sequential chain: A → B → C → D
    t1 = tasks.create("Define requirements", "Gather and document requirements")
    t2 = tasks.create("Design system", "Create architecture design", blocked_by=[t1.id])
    t3 = tasks.create("Implement code", "Write the implementation", blocked_by=[t2.id])
    t4 = tasks.create("Test and deploy", "Run tests and deploy", blocked_by=[t3.id])

    print(visualize_dependencies(tasks))
    print("\nUse case: Strict phases where each step depends on previous")
    print("Example: Traditional software development waterfall")


def demo_parallel_pattern():
    """Demonstrate parallel task pattern."""
    print("\n" + "=" * 60)
    print(" Pattern 2: Parallel (Fan-out/Fan-in)")
    print("=" * 60)

    tasks = TaskList(list_id="parallel-demo")
    tasks.tasks.clear()
    tasks._next_id = 1

    # Create fan-out/fan-in pattern
    #     ┌─→ B ─→┐
    # A ──┼─→ C ─→┼──→ E
    #     └─→ D ─→┘

    t1 = tasks.create("Initialize project", "Set up project structure")
    t2 = tasks.create("Build frontend", "Develop React frontend", blocked_by=[t1.id])
    t3 = tasks.create("Build backend", "Develop API backend", blocked_by=[t1.id])
    t4 = tasks.create("Write tests", "Create test suite", blocked_by=[t1.id])
    t5 = tasks.create("Integration testing", "Test full system", blocked_by=[t2.id, t3.id, t4.id])

    print(visualize_dependencies(tasks))
    print("\nUse case: Independent workstreams that converge")
    print("Example: Frontend/backend parallel development")


def demo_diamond_pattern():
    """Demonstrate diamond dependency pattern."""
    print("\n" + "=" * 60)
    print(" Pattern 3: Diamond (Shared Dependencies)")
    print("=" * 60)

    tasks = TaskList(list_id="diamond-demo")
    tasks.tasks.clear()
    tasks._next_id = 1

    # Create diamond pattern
    #       ┌─→ B ─→┐
    # A ────┤       ├──→ D
    #       └─→ C ─→┘

    t1 = tasks.create("Setup database", "Create database schema")
    t2 = tasks.create("User service", "Build user management", blocked_by=[t1.id])
    t3 = tasks.create("Auth service", "Build authentication", blocked_by=[t1.id])
    t4 = tasks.create("API gateway", "Build gateway that uses both", blocked_by=[t2.id, t3.id])

    print(visualize_dependencies(tasks))
    print("\nUse case: Multiple features sharing a common prerequisite")
    print("Example: Services that all need the database first")


def demo_staged_rollout():
    """Demonstrate staged rollout pattern."""
    print("\n" + "=" * 60)
    print(" Pattern 4: Staged Rollout")
    print("=" * 60)

    tasks = TaskList(list_id="staged-demo")
    tasks.tasks.clear()
    tasks._next_id = 1

    # Create staged pattern
    # Dev ─→ Staging ─→ Prod
    #   ↓        ↓
    # Tests   Tests

    t1 = tasks.create("Deploy to dev", "Deploy feature to dev environment")
    t2 = tasks.create("Dev smoke tests", "Run smoke tests on dev", blocked_by=[t1.id])
    t3 = tasks.create("Deploy to staging", "Deploy to staging", blocked_by=[t2.id])
    t4 = tasks.create("Staging integration tests", "Run full test suite", blocked_by=[t3.id])
    t5 = tasks.create("Deploy to production", "Deploy to prod", blocked_by=[t4.id])
    t6 = tasks.create("Monitor production", "Watch metrics for 1 hour", blocked_by=[t5.id])

    print(visualize_dependencies(tasks))
    print("\nUse case: Progressive deployment with gates")
    print("Example: CI/CD pipeline stages")


def demo_research_synthesis():
    """Demonstrate research and synthesis pattern."""
    print("\n" + "=" * 60)
    print(" Pattern 5: Research & Synthesis")
    print("=" * 60)

    tasks = TaskList(list_id="research-demo")
    tasks.tasks.clear()
    tasks._next_id = 1

    # Research pattern - common in agent swarms
    # Multiple research tasks → Synthesis → Report

    t1 = tasks.create("Research competitor A", "Analyze CompetitorA pricing")
    t2 = tasks.create("Research competitor B", "Analyze CompetitorB pricing")
    t3 = tasks.create("Research competitor C", "Analyze CompetitorC pricing")
    t4 = tasks.create("Synthesize findings", "Combine all research", blocked_by=[t1.id, t2.id, t3.id])
    t5 = tasks.create("Generate report", "Create final report", blocked_by=[t4.id])

    print(visualize_dependencies(tasks))
    print("\nUse case: Parallel research with synthesis")
    print("Example: Multi-agent research swarm")

    # Find critical path
    critical = find_critical_path(tasks)
    print(f"\nCritical path: {' → '.join(critical)}")
    print("(Any delay in critical path delays the whole project)")


def demo_execution_simulation():
    """Simulate task execution respecting dependencies."""
    print("\n" + "=" * 60)
    print(" Execution Simulation")
    print("=" * 60)

    tasks = TaskList(list_id="execution-demo")
    tasks.tasks.clear()
    tasks._next_id = 1

    # Create a simple dependency graph
    t1 = tasks.create("Task A", "First task")
    t2 = tasks.create("Task B", "Depends on A", blocked_by=[t1.id])
    t3 = tasks.create("Task C", "Depends on A", blocked_by=[t1.id])
    t4 = tasks.create("Task D", "Depends on B and C", blocked_by=[t2.id, t3.id])

    print("Initial state:")
    print(visualize_dependencies(tasks))

    # Execution loop
    step = 1
    while True:
        available = tasks.list_available()
        if not available:
            break

        print(f"\n--- Step {step} ---")
        print(f"Available tasks: {[f'{t.id}:{t.subject}' for t in available]}")

        # "Execute" all available tasks (in parallel)
        for task in available:
            tasks.update(task.id, status="in_progress")
            print(f"  Starting: {task.id} - {task.subject}")

        for task in available:
            tasks.update(task.id, status="completed")
            print(f"  Completed: {task.id} - {task.subject}")

        step += 1

    print("\nFinal state:")
    print(visualize_dependencies(tasks))
    print(f"\nTotal execution steps: {step - 1}")


def main():
    print("\nTask Dependencies Demo")
    print("=" * 60)
    print("Demonstrates common dependency patterns for task orchestration")
    print("=" * 60)

    demo_sequential_pattern()
    demo_parallel_pattern()
    demo_diamond_pattern()
    demo_staged_rollout()
    demo_research_synthesis()
    demo_execution_simulation()

    print("\n" + "=" * 60)
    print(" Key Takeaways")
    print("=" * 60)
    print("""
1. Sequential: Strict ordering (A → B → C)
2. Parallel: Fan-out/fan-in for independent work
3. Diamond: Shared dependencies converging
4. Staged: Progressive gates (dev → staging → prod)
5. Research: Parallel exploration + synthesis

The Tasks system automatically:
- Blocks execution until dependencies complete
- Enables parallel execution of independent tasks
- Provides a clear execution order
""")


if __name__ == "__main__":
    main()
