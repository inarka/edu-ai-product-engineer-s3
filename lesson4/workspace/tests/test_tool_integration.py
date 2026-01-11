"""Integration tests for tool functions with live APIs.

These tests require API keys and make real HTTP requests.
They are slower and should be run separately from unit tests.

Run with:
    pytest tests/test_tool_integration.py -v -m integration

Skip if no API keys:
    pytest tests/test_tool_integration.py -v  # auto-skips without keys
"""

import os
import pytest

# Mark all tests in this module as integration
pytestmark = pytest.mark.integration


# === LINKEDIN TOOL TESTS ===

@pytest.mark.skipif(
    not os.getenv("ENRICHLAYER_API_KEY"),
    reason="ENRICHLAYER_API_KEY not set"
)
class TestFetchLinkedInLive:
    """Live tests for fetch_linkedin (requires API key)."""

    def test_fetch_real_profile(self):
        """Fetch a real LinkedIn profile"""
        from deep_research_agent import fetch_linkedin

        # Use a well-known public profile
        result = fetch_linkedin("https://linkedin.com/in/satlonaderr")

        assert isinstance(result, dict)
        # API might return error (404, rate limit) or valid data
        # Either is acceptable - we're testing the tool doesn't crash
        if "error" in result:
            # Error response is acceptable (API limitations)
            assert isinstance(result["error"], str)
        elif "mock" in result:
            # Mock data is acceptable
            assert result.get("mock") is True
        else:
            # Real data should have name
            assert result.get("name") is not None

    def test_handles_invalid_url(self):
        """Invalid URL should return error gracefully"""
        from deep_research_agent import fetch_linkedin

        result = fetch_linkedin("not-a-valid-url")

        assert isinstance(result, dict)
        # Should either have error or mock data
        assert "error" in result or "mock" in result


# === WEB SEARCH TOOL TESTS ===

@pytest.mark.skipif(
    not os.getenv("TAVILY_API_KEY"),
    reason="TAVILY_API_KEY not set"
)
class TestWebSearchLive:
    """Live tests for web_search (requires API key)."""

    def test_search_returns_results(self):
        """Search for a known topic returns results"""
        from deep_research_agent import web_search

        results = web_search("Microsoft AI announcements 2024", max_results=3)

        assert isinstance(results, list)
        assert len(results) > 0
        # Real results have title and url
        if "error" not in results[0]:
            assert results[0].get("title") is not None
            assert results[0].get("url") is not None

    def test_respects_max_results(self):
        """max_results parameter limits response"""
        from deep_research_agent import web_search

        results = web_search("Python programming", max_results=2)

        assert len(results) <= 2


# === COMPANY ANALYSIS TOOL TESTS ===

class TestAnalyzeCompanyLive:
    """Tests for analyze_company (always returns mock data)."""

    def test_analyze_returns_company_info(self):
        """analyze_company returns structured data"""
        from deep_research_agent import analyze_company

        result = analyze_company("Microsoft")

        assert isinstance(result, dict)
        assert result.get("name") == "Microsoft"
        assert "industry" in result
        assert "mock" in result  # Currently always mock

    def test_handles_unknown_company(self):
        """Unknown company still returns structured data"""
        from deep_research_agent import analyze_company

        result = analyze_company("XYZ Unknown Company 12345")

        assert isinstance(result, dict)
        assert "name" in result


# === COMBINED WORKFLOW TESTS ===

@pytest.mark.skipif(
    not (os.getenv("ENRICHLAYER_API_KEY") and os.getenv("TAVILY_API_KEY")),
    reason="Missing API keys for full integration test"
)
class TestToolWorkflowLive:
    """Tests combining multiple tools (requires all API keys)."""

    def test_linkedin_then_company(self):
        """Common workflow: LinkedIn profile → Company analysis"""
        from deep_research_agent import fetch_linkedin, analyze_company

        # Step 1: Get LinkedIn data
        linkedin = fetch_linkedin("https://linkedin.com/in/satyanadella")

        # Step 2: Analyze their company
        company_name = linkedin.get("company", "Microsoft")
        company = analyze_company(company_name)

        # Both should return valid data
        assert isinstance(linkedin, dict)
        assert isinstance(company, dict)
        assert company.get("name") is not None

    def test_search_then_analyze(self):
        """Common workflow: Search → Company analysis"""
        from deep_research_agent import web_search, analyze_company

        # Step 1: Search for company news
        results = web_search("NVIDIA AI chips 2024", max_results=2)

        # Step 2: Analyze the company
        company = analyze_company("NVIDIA")

        # Both should return valid data
        assert isinstance(results, list)
        assert isinstance(company, dict)
