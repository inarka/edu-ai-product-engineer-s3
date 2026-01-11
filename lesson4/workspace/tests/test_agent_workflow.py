"""Integration tests for agent workflow execution.

These tests run the full Deep Research Agent and verify its behavior.
They require ANTHROPIC_API_KEY and are slow (~30-60s each).

Run with:
    pytest tests/test_agent_workflow.py -v -m integration --timeout=120

Skip if no API key:
    pytest tests/test_agent_workflow.py -v  # auto-skips without key
"""

import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Mark all tests in this module as integration and slow
pytestmark = [pytest.mark.integration, pytest.mark.slow]


# === FULL WORKFLOW TESTS ===

@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)
class TestAgentWorkflowLive:
    """Live tests for run_research workflow."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_simple_research_completes(self):
        """run_research() returns valid output dict"""
        from deep_research_agent import run_research

        result = await run_research(
            target="https://linkedin.com/in/demo-test",
            company="Test Company",
        )

        assert isinstance(result, dict)
        # Should have output field
        assert "output" in result or "final_report" in result or "error" in result

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)
    async def test_research_with_focus(self):
        """run_research() accepts focus parameter"""
        from deep_research_agent import run_research

        result = await run_research(
            target="https://linkedin.com/in/demo-test",
            company="Test Company",
            focus="AI strategy",
        )

        assert isinstance(result, dict)


# === MOCKED WORKFLOW TESTS ===

class TestAgentWorkflowMocked:
    """Mocked tests for agent workflow (no API needed)."""

    @patch("deep_research_agent.DeepAgent")
    def test_agent_run_called_with_task(self, mock_agent_class):
        """Agent.run() is called with constructed task"""
        from deep_research_agent import run_research

        mock_agent = MagicMock()
        mock_result = {"output": "Test report", "todos": []}
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_agent_class.return_value = mock_agent

        asyncio.run(run_research(
            target="test-target",
            company="TestCo",
        ))

        # Verify run was called
        mock_agent.run.assert_called_once()
        call_args = mock_agent.run.call_args[0][0]
        assert "test-target" in call_args
        assert "TestCo" in call_args

    @patch("deep_research_agent.DeepAgent")
    def test_result_contains_todos_field(self, mock_agent_class):
        """Result should include todos (planning trace)"""
        from deep_research_agent import run_research

        mock_agent = MagicMock()
        mock_result = {
            "output": "Test report",
            "todos": [{"task": "Research LinkedIn", "completed": True}]
        }
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_agent_class.return_value = mock_agent

        result = asyncio.run(run_research(target="test"))

        assert "todos" in result
        assert len(result["todos"]) > 0

    @patch("deep_research_agent.DeepAgent")
    def test_result_contains_output_field(self, mock_agent_class):
        """Result should include output (final report)"""
        from deep_research_agent import run_research

        mock_agent = MagicMock()
        mock_result = {"output": "Final research report"}
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_agent_class.return_value = mock_agent

        result = asyncio.run(run_research(target="test"))

        assert "output" in result
        assert len(result["output"]) > 0


# === PRINT RESULTS TESTS ===

class TestPrintResults:
    """Tests for print_results utility function."""

    def test_handles_minimal_result(self, capsys):
        """print_results handles minimal output dict"""
        from deep_research_agent import print_results

        print_results({"output": "Simple report"})

        captured = capsys.readouterr()
        assert "Simple report" in captured.out
        assert "RESULTS" in captured.out

    def test_handles_full_result(self, capsys):
        """print_results handles full output with todos and files"""
        from deep_research_agent import print_results

        result = {
            "output": "Final report",
            "todos": [
                {"task": "Research LinkedIn", "completed": True},
                {"task": "Analyze company", "completed": True},
            ],
            "files_written": ["research_notes.md"],
            "subagent_calls": [
                {"agent": "linkedin-analyst", "task": "Deep dive on profile"}
            ],
        }

        print_results(result)

        captured = capsys.readouterr()
        assert "Final report" in captured.out
        assert "Execution Plan" in captured.out
        assert "Research LinkedIn" in captured.out
        assert "research_notes.md" in captured.out
        assert "linkedin-analyst" in captured.out

    def test_handles_empty_result(self, capsys):
        """print_results handles empty dict"""
        from deep_research_agent import print_results

        print_results({})

        captured = capsys.readouterr()
        # Should still print headers without crashing
        assert "RESULTS" in captured.out
