"""
Tasks System Introduction

The Tasks system in Claude Code (Jan 2026) replaces Todos with
persistent, dependency-aware task tracking.

Key features:
- Persistent: stored in ~/.claude/tasks/
- Dependencies: blockedBy enforces execution order
- Multi-session: CLAUDE_CODE_TASK_LIST_ID enables sharing
- Sub-agents: Tasks can spawn sub-agents automatically

This file demonstrates the Tasks API concepts.
For full implementation, use Claude Code directly.

Run:
    python agent_orchestration/tasks_basic.py
"""

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


# =============================================================================
# Task Data Model
# =============================================================================

@dataclass
class Task:
    """Represents a task in the Tasks system."""
    id: str
    subject: str
    description: str
    status: str = "pending"  # pending, in_progress, completed
    active_form: str = ""  # Present continuous form for spinner
    owner: str | None = None
    blocked_by: list[str] = field(default_factory=list)
    blocks: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
    metadata: dict = field(default_factory=dict)


# =============================================================================
# Task List Management
# =============================================================================

class TaskList:
    """Manages a list of tasks with persistence."""

    def __init__(self, list_id: str | None = None):
        """Initialize task list.

        Args:
            list_id: Unique identifier for this task list.
                    If None, generates a new ID.
        """
        self.list_id = list_id or str(uuid.uuid4())[:8]
        self.tasks: dict[str, Task] = {}
        self._next_id = 1

        # Storage directory
        self.storage_dir = Path.home() / ".claude" / "tasks"
        self.storage_file = self.storage_dir / f"{self.list_id}.json"

        # Load existing tasks if file exists
        self._load()

    def _load(self):
        """Load tasks from storage."""
        if self.storage_file.exists():
            data = json.loads(self.storage_file.read_text())
            for task_data in data.get("tasks", []):
                task = Task(**task_data)
                self.tasks[task.id] = task
                # Track highest ID for next assignment
                try:
                    num_id = int(task.id)
                    self._next_id = max(self._next_id, num_id + 1)
                except ValueError:
                    pass

    def _save(self):
        """Save tasks to storage."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "list_id": self.list_id,
            "updated_at": datetime.now().isoformat(),
            "tasks": [asdict(t) for t in self.tasks.values()]
        }
        self.storage_file.write_text(json.dumps(data, indent=2))

    def create(
        self,
        subject: str,
        description: str,
        active_form: str = "",
        blocked_by: list[str] | None = None
    ) -> Task:
        """Create a new task.

        Args:
            subject: Brief title (imperative form, e.g., "Run tests")
            description: Detailed description of what needs to be done
            active_form: Present continuous form for spinner (e.g., "Running tests")
            blocked_by: List of task IDs this task depends on

        Returns:
            Created Task object
        """
        task_id = str(self._next_id)
        self._next_id += 1

        task = Task(
            id=task_id,
            subject=subject,
            description=description,
            active_form=active_form or f"Working on: {subject}",
            blocked_by=blocked_by or []
        )

        self.tasks[task_id] = task

        # Update blocks for dependency tasks
        for dep_id in task.blocked_by:
            if dep_id in self.tasks:
                self.tasks[dep_id].blocks.append(task_id)

        self._save()
        return task

    def update(
        self,
        task_id: str,
        status: str | None = None,
        subject: str | None = None,
        description: str | None = None,
        owner: str | None = None,
        add_blocked_by: list[str] | None = None,
        add_blocks: list[str] | None = None
    ) -> Task:
        """Update an existing task.

        Args:
            task_id: ID of task to update
            status: New status (pending, in_progress, completed)
            subject: New subject
            description: New description
            owner: New owner
            add_blocked_by: Task IDs to add as dependencies
            add_blocks: Task IDs this task should block

        Returns:
            Updated Task object
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        task = self.tasks[task_id]

        if status:
            task.status = status
            if status == "completed":
                task.completed_at = datetime.now().isoformat()

        if subject:
            task.subject = subject
        if description:
            task.description = description
        if owner:
            task.owner = owner

        if add_blocked_by:
            for dep_id in add_blocked_by:
                if dep_id not in task.blocked_by:
                    task.blocked_by.append(dep_id)
                if dep_id in self.tasks:
                    self.tasks[dep_id].blocks.append(task_id)

        if add_blocks:
            for block_id in add_blocks:
                if block_id not in task.blocks:
                    task.blocks.append(block_id)
                if block_id in self.tasks:
                    self.tasks[block_id].blocked_by.append(task_id)

        self._save()
        return task

    def get(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def list_all(self) -> list[Task]:
        """List all tasks."""
        return list(self.tasks.values())

    def list_available(self) -> list[Task]:
        """List tasks that can be started (not blocked, not completed)."""
        available = []
        for task in self.tasks.values():
            if task.status == "completed":
                continue

            # Check if all dependencies are completed
            all_deps_done = all(
                self.tasks.get(dep_id, Task(id="", subject="", description="")).status == "completed"
                for dep_id in task.blocked_by
            )

            if all_deps_done:
                available.append(task)

        return available

    def print_status(self):
        """Print current task list status."""
        print(f"\nTask List: {self.list_id}")
        print("=" * 60)

        for task in self.tasks.values():
            # Status icon
            if task.status == "completed":
                icon = "[x]"
            elif task.status == "in_progress":
                icon = "[>]"
            else:
                # Check if blocked
                blocked = any(
                    self.tasks.get(dep_id, Task(id="", subject="", description="")).status != "completed"
                    for dep_id in task.blocked_by
                )
                icon = "[B]" if blocked else "[ ]"

            # Dependencies info
            deps = ""
            if task.blocked_by:
                deps = f" (blocked by: {', '.join(task.blocked_by)})"

            print(f"{icon} {task.id}: {task.subject}{deps}")

        print("=" * 60)


# =============================================================================
# Demo
# =============================================================================

def demo_basic_tasks():
    """Demonstrate basic task creation and management."""
    print("\n" + "=" * 60)
    print(" Tasks System Basic Demo")
    print("=" * 60)

    # Create a new task list
    tasks = TaskList(list_id="demo-basic")

    # Create some tasks
    print("\nCreating tasks...")

    task1 = tasks.create(
        subject="Research competitor pricing",
        description="Analyze top 5 competitors' pricing pages and document their pricing tiers",
        active_form="Researching competitor pricing"
    )
    print(f"Created: Task {task1.id} - {task1.subject}")

    task2 = tasks.create(
        subject="Draft pricing recommendations",
        description="Based on competitor research, recommend our pricing tiers",
        active_form="Drafting pricing recommendations",
        blocked_by=[task1.id]  # Depends on task 1
    )
    print(f"Created: Task {task2.id} - {task2.subject} (blocked by {task1.id})")

    task3 = tasks.create(
        subject="Design pricing page mockup",
        description="Create Figma mockup of new pricing page",
        active_form="Designing pricing page"
    )
    print(f"Created: Task {task3.id} - {task3.subject}")

    task4 = tasks.create(
        subject="Implement pricing page",
        description="Build the pricing page based on mockup and recommendations",
        active_form="Implementing pricing page",
        blocked_by=[task2.id, task3.id]  # Depends on both
    )
    print(f"Created: Task {task4.id} - {task4.subject} (blocked by {task2.id}, {task3.id})")

    # Show initial status
    print("\nInitial Status:")
    tasks.print_status()

    # Show available tasks
    available = tasks.list_available()
    print(f"\nAvailable to start: {[t.subject for t in available]}")

    # Simulate work
    print("\n--- Simulating work ---")

    # Start task 1
    tasks.update(task1.id, status="in_progress", owner="agent-1")
    print(f"\nStarted: {task1.subject}")
    tasks.print_status()

    # Complete task 1
    tasks.update(task1.id, status="completed")
    print(f"\nCompleted: {task1.subject}")

    # Now task 2 should be available
    available = tasks.list_available()
    print(f"Now available: {[t.subject for t in available]}")

    tasks.print_status()

    print("\nTask file location:", tasks.storage_file)


def demo_persistence():
    """Demonstrate task persistence across sessions."""
    print("\n" + "=" * 60)
    print(" Tasks Persistence Demo")
    print("=" * 60)

    # Set a specific list ID (simulating CLAUDE_CODE_TASK_LIST_ID)
    list_id = "persistent-demo"

    print(f"\nUsing task list ID: {list_id}")

    # First "session"
    print("\n--- Session 1: Create tasks ---")
    tasks1 = TaskList(list_id=list_id)

    # Only create tasks if list is empty
    if not tasks1.tasks:
        tasks1.create(
            subject="Set up database",
            description="Create PostgreSQL database and tables"
        )
        tasks1.create(
            subject="Implement API",
            description="Build REST API endpoints",
            blocked_by=["1"]
        )
        print("Created new tasks")
    else:
        print("Found existing tasks")

    tasks1.print_status()

    # Second "session"
    print("\n--- Session 2: Load and continue ---")
    tasks2 = TaskList(list_id=list_id)  # Same list ID loads existing tasks

    print("Loaded task list from disk")
    tasks2.print_status()

    print(f"\nPersistence verified! File: {tasks2.storage_file}")


def main():
    print("\nTasks System Demo")
    print("=" * 60)
    print("This demonstrates the Tasks system concepts.")
    print("For full integration, use Claude Code directly.")
    print("=" * 60)

    demo_basic_tasks()
    demo_persistence()

    print("\n" + "=" * 60)
    print(" Key Takeaways")
    print("=" * 60)
    print("""
1. Tasks are persistent (stored in ~/.claude/tasks/)
2. Dependencies with blockedBy enforce execution order
3. Use CLAUDE_CODE_TASK_LIST_ID to share task lists
4. list_available() returns only unblocked tasks
5. Status: pending → in_progress → completed
""")


if __name__ == "__main__":
    main()
