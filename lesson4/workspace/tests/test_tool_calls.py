"""Tool call tests for Research Agents.

These are Tier 1 (Automated) tests that:
1. Run in CI on every PR
2. Cost $0.00 (no LLM calls)
3. Catch regressions in tool behavior

Test Categories:
- Input validation
- Output schema
- Error handling
- Edge cases

Usage:
    pytest tests/test_tool_calls.py -v
"""

import pytest
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from deep_research_agent import (
    fetch_linkedin,
    web_search,
    analyze_company,
)


class TestFetchLinkedIn:
    """Tests for the LinkedIn profile fetching tool."""

    def test_returns_dict(self):
        """Tool must always return a dict."""
        result = fetch_linkedin.invoke({"url": "https://linkedin.com/in/test"})
        assert isinstance(result, dict)

    def test_has_required_fields_on_success(self):
        """Successful response must have name and title."""
        result = fetch_linkedin.invoke({"url": "https://linkedin.com/in/test"})

        # Either has data or has error
        assert "name" in result or "error" in result

    def test_handles_invalid_url(self):
        """Tool should not crash on invalid URL."""
        result = fetch_linkedin.invoke({"url": "not-a-url"})
        assert isinstance(result, dict)
        # Should either handle gracefully or return error
        assert "error" in result or "name" in result

    def test_handles_empty_url(self):
        """Tool should handle empty URL."""
        result = fetch_linkedin.invoke({"url": ""})
        assert isinstance(result, dict)

    @patch("deep_research_agent.httpx.get")
    def test_handles_api_error(self, mock_get):
        """Tool should handle API errors gracefully."""
        mock_get.side_effect = Exception("API Error")

        # Should not raise, should return error dict
        result = fetch_linkedin.invoke({"url": "https://linkedin.com/in/test"})
        assert isinstance(result, dict)

    @patch("deep_research_agent.os.getenv")
    def test_returns_mock_without_api_key(self, mock_getenv):
        """Tool should return mock data when API key is missing."""
        mock_getenv.return_value = None

        result = fetch_linkedin.invoke({"url": "https://linkedin.com/in/test"})

        assert isinstance(result, dict)
        assert result.get("mock", False) is True or "error" in result


class TestWebSearch:
    """Tests for the web search tool."""

    def test_returns_list(self):
        """Tool must return a list of results."""
        result = web_search.invoke({"query": "test query"})
        assert isinstance(result, list)

    def test_results_have_required_fields(self):
        """Each result should have title and url."""
        result = web_search.invoke({"query": "Microsoft AI news"})

        if result and not result[0].get("error"):
            for item in result:
                assert "title" in item or "error" in item

    def test_respects_max_results(self):
        """Tool should respect max_results parameter."""
        result = web_search.invoke({"query": "test", "max_results": 3})

        if result and not result[0].get("error"):
            assert len(result) <= 3

    def test_handles_empty_query(self):
        """Tool should handle empty query."""
        result = web_search.invoke({"query": ""})
        assert isinstance(result, list)


class TestAnalyzeCompany:
    """Tests for the company analysis tool."""

    def test_returns_dict(self):
        """Tool must return a dict."""
        result = analyze_company.invoke({"company_name": "Microsoft"})
        assert isinstance(result, dict)

    def test_has_company_name(self):
        """Result should include the company name."""
        result = analyze_company.invoke({"company_name": "Microsoft"})
        assert result.get("name") == "Microsoft"

    def test_has_industry_field(self):
        """Result should include industry."""
        result = analyze_company.invoke({"company_name": "Apple"})
        assert "industry" in result

    def test_handles_unknown_company(self):
        """Tool should handle unknown companies gracefully."""
        result = analyze_company.invoke({"company_name": "Unknown Company XYZ"})
        assert isinstance(result, dict)
        # Should still return structured data


class TestToolDocstrings:
    """Tests for tool documentation (critical for LLM understanding)."""

    def test_fetch_linkedin_has_docstring(self):
        """fetch_linkedin must have a docstring for LLM guidance."""
        assert fetch_linkedin.__doc__ is not None
        assert len(fetch_linkedin.__doc__) > 50

    def test_web_search_has_docstring(self):
        """web_search must have a docstring for LLM guidance."""
        assert web_search.__doc__ is not None
        assert len(web_search.__doc__) > 50

    def test_analyze_company_has_docstring(self):
        """analyze_company must have a docstring for LLM guidance."""
        assert analyze_company.__doc__ is not None
        assert len(analyze_company.__doc__) > 50

    def test_docstrings_have_use_when(self):
        """Docstrings should explain WHEN to use the tool."""
        # This is crucial for LLM tool selection
        assert "USE WHEN" in fetch_linkedin.__doc__.upper() or "WHEN" in fetch_linkedin.__doc__.upper()
        assert "USE WHEN" in web_search.__doc__.upper() or "WHEN" in web_search.__doc__.upper()


class TestToolSchemas:
    """Tests for tool input/output schemas."""

    def test_fetch_linkedin_accepts_url_param(self):
        """fetch_linkedin should accept 'url' parameter."""
        # The tool should be callable with url parameter
        try:
            result = fetch_linkedin.invoke({"url": "test"})
            assert True  # Didn't raise
        except TypeError as e:
            pytest.fail(f"Tool doesn't accept 'url' parameter: {e}")

    def test_web_search_accepts_query_param(self):
        """web_search should accept 'query' parameter."""
        try:
            result = web_search.invoke({"query": "test"})
            assert True
        except TypeError as e:
            pytest.fail(f"Tool doesn't accept 'query' parameter: {e}")


# === INTEGRATION TESTS ===

class TestToolIntegration:
    """Integration tests for tool combinations."""

    def test_linkedin_then_company(self):
        """Common pattern: fetch LinkedIn, then analyze company."""
        linkedin_result = fetch_linkedin.invoke({
            "url": "https://linkedin.com/in/test"
        })

        company_name = linkedin_result.get("company", "Default Corp")
        company_result = analyze_company.invoke({
            "company_name": company_name
        })

        assert isinstance(linkedin_result, dict)
        assert isinstance(company_result, dict)

    def test_search_then_analyze(self):
        """Common pattern: search for news, then analyze."""
        search_results = web_search.invoke({
            "query": "Microsoft AI announcements",
            "max_results": 3
        })

        # Should be able to process search results
        assert isinstance(search_results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
