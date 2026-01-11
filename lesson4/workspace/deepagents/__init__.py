"""Mock deepagents module for testing.

This mock allows tests to run without the actual deepagents package installed.
The real deepagents package requires Python 3.11+.

Note: This is only for testing purposes. For actual use, install:
    pip install deepagents>=0.3.2  (requires Python 3.11+)
"""

from unittest.mock import MagicMock
from .tools import tool, ToolWrapper


class MockDeepAgent:
    """Mock DeepAgent for testing."""

    def __init__(
        self,
        name: str = "mock-agent",
        model: str = "mock-model",
        system_prompt: str = "",
        tools: list = None,
        subagents: list = None,
        enable_filesystem: bool = False,
        workspace_dir: str = "/tmp",
        **kwargs
    ):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.subagents = subagents or []
        self.enable_filesystem = enable_filesystem
        self.workspace_dir = workspace_dir

    async def run(self, task: str) -> dict:
        """Mock run method that returns test data."""
        return {
            "output": f"Mock research report for: {task}",
            "todos": [{"task": "Research", "completed": True}],
            "files_written": [],
            "subagent_calls": [],
        }


# Export the mock class
DeepAgent = MockDeepAgent


class tools:
    """Mock tools namespace (for deepagents.tools.tool import pattern)."""

    # Reference the real tool decorator from tools module
    tool = staticmethod(tool)
