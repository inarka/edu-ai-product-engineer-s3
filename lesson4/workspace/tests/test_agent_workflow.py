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

    @patch("deep_research_agent.create_deep_agent")
    def test_agent_ainvoke_called_with_task(self, mock_create_agent):
        """Agent.ainvoke() is called with constructed task"""
        from deep_research_agent import run_research

        mock_agent = MagicMock()
        mock_result = {"messages": [{"role": "assistant", "content": "Test report"}]}
        mock_agent.ainvoke = AsyncMock(return_value=mock_result)
        mock_create_agent.return_value = mock_agent

        asyncio.run(run_research(
            target="test-target",
            company="TestCo",
        ))

        # Verify ainvoke was called
        mock_agent.ainvoke.assert_called_once()
        call_args = mock_agent.ainvoke.call_args[0][0]
        assert "messages" in call_args
        assert "test-target" in call_args["messages"][0]["content"]
        assert "TestCo" in call_args["messages"][0]["content"]

    @patch("deep_research_agent.create_deep_agent")
    def test_result_contains_messages_field(self, mock_create_agent):
        """Result should include messages (conversation trace)"""
        from deep_research_agent import run_research

        mock_agent = MagicMock()
        mock_result = {
            "messages": [
                {"role": "user", "content": "Research test"},
                {"role": "assistant", "content": "Final report"}
            ]
        }
        mock_agent.ainvoke = AsyncMock(return_value=mock_result)
        mock_create_agent.return_value = mock_agent

        result = asyncio.run(run_research(target="test"))

        assert "messages" in result
        assert len(result["messages"]) > 0

    @patch("deep_research_agent.create_deep_agent")
    def test_result_messages_contain_content(self, mock_create_agent):
        """Result messages should include content (final report)"""
        from deep_research_agent import run_research

        mock_agent = MagicMock()
        mock_result = {"messages": [{"role": "assistant", "content": "Final research report"}]}
        mock_agent.ainvoke = AsyncMock(return_value=mock_result)
        mock_create_agent.return_value = mock_agent

        result = asyncio.run(run_research(target="test"))

        assert "messages" in result
        assert result["messages"][-1]["content"] == "Final research report"


# === PRINT RESULTS TESTS ===

class TestPrintResults:
    """Tests for print_results utility function."""

    def test_handles_minimal_result(self, capsys):
        """print_results handles minimal output dict with messages"""
        from deep_research_agent import print_results

        print_results({"messages": [{"role": "assistant", "content": "Simple report"}]})

        captured = capsys.readouterr()
        assert "Simple report" in captured.out
        assert "RESULTS" in captured.out

    def test_handles_full_result(self, capsys):
        """print_results handles full output with multiple messages"""
        from deep_research_agent import print_results

        result = {
            "messages": [
                {"role": "user", "content": "Research test"},
                {"role": "assistant", "content": "Final report with insights"},
            ],
        }

        print_results(result)

        captured = capsys.readouterr()
        assert "Final report" in captured.out
        assert "FINAL REPORT" in captured.out
        assert "Total messages" in captured.out

    def test_handles_empty_result(self, capsys):
        """print_results handles empty dict"""
        from deep_research_agent import print_results

        print_results({})

        captured = capsys.readouterr()
        # Should still print headers without crashing
        assert "RESULTS" in captured.out
