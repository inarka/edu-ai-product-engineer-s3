"""Unit tests for Deep Research Agent factory and configuration.

Tests agent creation and tool configuration WITHOUT running full workflows.
These tests do NOT require API keys for most scenarios.

Run with:
    pytest tests/test_agent_factory.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
import os


# === SYSTEM PROMPT TESTS ===

class TestSystemPrompt:
    """Tests for the research system prompt."""

    def test_prompt_exists(self):
        """RESEARCH_SYSTEM_PROMPT is defined"""
        from deep_research_agent import RESEARCH_SYSTEM_PROMPT
        assert RESEARCH_SYSTEM_PROMPT is not None
        assert len(RESEARCH_SYSTEM_PROMPT) > 100

    def test_prompt_mentions_todos(self):
        """Prompt instructs write_todos usage for planning"""
        from deep_research_agent import RESEARCH_SYSTEM_PROMPT
        assert "write_todos" in RESEARCH_SYSTEM_PROMPT.lower() or "todos" in RESEARCH_SYSTEM_PROMPT.lower()

    def test_prompt_mentions_subagents(self):
        """Prompt describes subagent delegation"""
        from deep_research_agent import RESEARCH_SYSTEM_PROMPT
        prompt_lower = RESEARCH_SYSTEM_PROMPT.lower()
        assert "subagent" in prompt_lower or "delegate" in prompt_lower

    def test_prompt_mentions_file_system(self):
        """Prompt describes file system for context management"""
        from deep_research_agent import RESEARCH_SYSTEM_PROMPT
        prompt_lower = RESEARCH_SYSTEM_PROMPT.lower()
        assert "file" in prompt_lower or "context" in prompt_lower

    def test_prompt_has_output_format(self):
        """Prompt defines expected output format"""
        from deep_research_agent import RESEARCH_SYSTEM_PROMPT
        # Should mention summary, insights, or talking points
        prompt_lower = RESEARCH_SYSTEM_PROMPT.lower()
        has_format = any([
            "summary" in prompt_lower,
            "insights" in prompt_lower,
            "talking points" in prompt_lower,
            "output format" in prompt_lower,
        ])
        assert has_format


# === SUBAGENT CONFIGURATION TESTS ===

class TestSubagentConfig:
    """Tests for subagent configurations."""

    def test_linkedin_specialist_exists(self):
        """LINKEDIN_SPECIALIST config is defined"""
        from deep_research_agent import LINKEDIN_SPECIALIST
        assert LINKEDIN_SPECIALIST is not None
        assert isinstance(LINKEDIN_SPECIALIST, dict)

    def test_linkedin_specialist_has_required_fields(self):
        """LINKEDIN_SPECIALIST has name, model, tools, system_prompt"""
        from deep_research_agent import LINKEDIN_SPECIALIST
        assert "name" in LINKEDIN_SPECIALIST
        assert "model" in LINKEDIN_SPECIALIST
        assert "tools" in LINKEDIN_SPECIALIST
        assert "system_prompt" in LINKEDIN_SPECIALIST

    def test_news_specialist_exists(self):
        """NEWS_SPECIALIST config is defined"""
        from deep_research_agent import NEWS_SPECIALIST
        assert NEWS_SPECIALIST is not None
        assert isinstance(NEWS_SPECIALIST, dict)

    def test_news_specialist_has_required_fields(self):
        """NEWS_SPECIALIST has name, model, tools, system_prompt"""
        from deep_research_agent import NEWS_SPECIALIST
        assert "name" in NEWS_SPECIALIST
        assert "model" in NEWS_SPECIALIST
        assert "tools" in NEWS_SPECIALIST
        assert "system_prompt" in NEWS_SPECIALIST

    def test_subagents_have_different_names(self):
        """Subagents have unique names"""
        from deep_research_agent import LINKEDIN_SPECIALIST, NEWS_SPECIALIST
        assert LINKEDIN_SPECIALIST["name"] != NEWS_SPECIALIST["name"]


# === TOOL CONFIGURATION TESTS ===

class TestToolConfiguration:
    """Tests for tool functions (not the actual execution)."""

    def test_fetch_linkedin_is_callable(self):
        """fetch_linkedin is a callable function"""
        from deep_research_agent import fetch_linkedin
        assert callable(fetch_linkedin)

    def test_web_search_is_callable(self):
        """web_search is a callable function"""
        from deep_research_agent import web_search
        assert callable(web_search)

    def test_analyze_company_is_callable(self):
        """analyze_company is a callable function"""
        from deep_research_agent import analyze_company
        assert callable(analyze_company)

    def test_fetch_linkedin_has_docstring(self):
        """fetch_linkedin has a descriptive docstring"""
        from deep_research_agent import fetch_linkedin
        # Access underlying function if decorated
        func = getattr(fetch_linkedin, "__wrapped__", fetch_linkedin)
        assert func.__doc__ is not None
        assert len(func.__doc__) > 20

    def test_web_search_has_docstring(self):
        """web_search has a descriptive docstring"""
        from deep_research_agent import web_search
        func = getattr(web_search, "__wrapped__", web_search)
        assert func.__doc__ is not None
        assert len(func.__doc__) > 20

    def test_analyze_company_has_docstring(self):
        """analyze_company has a descriptive docstring"""
        from deep_research_agent import analyze_company
        func = getattr(analyze_company, "__wrapped__", analyze_company)
        assert func.__doc__ is not None
        assert len(func.__doc__) > 20


# === AGENT FACTORY TESTS ===

class TestAgentFactory:
    """Tests for create_deep_research_agent factory function."""

    @patch("deep_research_agent.DeepAgent")
    def test_create_agent_returns_deep_agent(self, mock_deep_agent_class):
        """Factory returns a DeepAgent instance"""
        from deep_research_agent import create_deep_research_agent

        mock_agent = MagicMock()
        mock_deep_agent_class.return_value = mock_agent

        result = create_deep_research_agent()

        assert result == mock_agent
        mock_deep_agent_class.assert_called_once()

    @patch("deep_research_agent.DeepAgent")
    def test_agent_has_name(self, mock_deep_agent_class):
        """Agent is created with a name"""
        from deep_research_agent import create_deep_research_agent

        create_deep_research_agent()

        call_kwargs = mock_deep_agent_class.call_args[1]
        assert "name" in call_kwargs
        assert call_kwargs["name"] == "research-orchestrator"

    @patch("deep_research_agent.DeepAgent")
    def test_agent_has_model(self, mock_deep_agent_class):
        """Agent is created with a model"""
        from deep_research_agent import create_deep_research_agent

        create_deep_research_agent()

        call_kwargs = mock_deep_agent_class.call_args[1]
        assert "model" in call_kwargs
        assert "anthropic" in call_kwargs["model"] or "openai" in call_kwargs["model"]

    @patch("deep_research_agent.DeepAgent")
    def test_agent_has_three_tools(self, mock_deep_agent_class):
        """Agent is created with 3 tools"""
        from deep_research_agent import create_deep_research_agent

        create_deep_research_agent()

        call_kwargs = mock_deep_agent_class.call_args[1]
        assert "tools" in call_kwargs
        assert len(call_kwargs["tools"]) == 3

    @patch("deep_research_agent.DeepAgent")
    def test_agent_has_subagents(self, mock_deep_agent_class):
        """Agent is created with subagents"""
        from deep_research_agent import create_deep_research_agent

        create_deep_research_agent()

        call_kwargs = mock_deep_agent_class.call_args[1]
        assert "subagents" in call_kwargs
        assert len(call_kwargs["subagents"]) == 2

    @patch("deep_research_agent.DeepAgent")
    def test_filesystem_enabled(self, mock_deep_agent_class):
        """Agent has enable_filesystem=True"""
        from deep_research_agent import create_deep_research_agent

        create_deep_research_agent()

        call_kwargs = mock_deep_agent_class.call_args[1]
        assert call_kwargs.get("enable_filesystem") is True

    @patch("deep_research_agent.DeepAgent")
    def test_workspace_dir_set(self, mock_deep_agent_class):
        """Agent workspace directory is configured"""
        from deep_research_agent import create_deep_research_agent

        create_deep_research_agent()

        call_kwargs = mock_deep_agent_class.call_args[1]
        assert "workspace_dir" in call_kwargs
        assert call_kwargs["workspace_dir"] is not None


# === TOOL MOCK DATA TESTS ===

class TestToolMockData:
    """Tests for tool behavior when API keys are missing.

    Note: These tests verify mock fallback behavior for CI environments
    without API keys. When API keys are present, the live integration
    tests in test_tool_integration.py cover the tools instead.
    """

    @pytest.mark.skipif(
        bool(os.getenv("ENRICHLAYER_API_KEY")),
        reason="Mock test skipped when ENRICHLAYER_API_KEY is set"
    )
    def test_fetch_linkedin_returns_mock_without_api_key(self):
        """fetch_linkedin returns mock data when API key missing"""
        from deep_research_agent import fetch_linkedin
        result = fetch_linkedin("https://linkedin.com/in/test")
        assert result.get("mock") is True

    @pytest.mark.skipif(
        bool(os.getenv("TAVILY_API_KEY")),
        reason="Mock test skipped when TAVILY_API_KEY is set"
    )
    def test_web_search_returns_mock_without_api_key(self):
        """web_search returns mock data when API key missing"""
        from deep_research_agent import web_search
        result = web_search("test query")
        assert isinstance(result, list)
        assert result[0].get("mock") is True

    def test_analyze_company_returns_mock_data(self):
        """analyze_company returns mock data (always mock in demo)"""
        from deep_research_agent import analyze_company
        result = analyze_company("Test Company")
        assert result.get("mock") is True
        assert result.get("name") == "Test Company"
