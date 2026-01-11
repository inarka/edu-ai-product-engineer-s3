"""Pytest configuration and fixtures for lesson4 tests.

This file configures pytest markers and provides shared fixtures.

Markers:
    @pytest.mark.integration - Tests requiring API keys
    @pytest.mark.llm_judge - Tests using LLM-as-Judge (costs money)
    @pytest.mark.slow - Tests taking > 10 seconds

Usage:
    # Run only unit tests (fast, no API)
    pytest tests/ -v -m "not integration and not llm_judge"

    # Run integration tests
    pytest tests/ -v -m integration

    # Run LLM judge tests
    pytest tests/ -v -m llm_judge

    # Run all tests
    pytest tests/ -v
"""

import sys
import os
import pytest

# Add workspace directory to path for imports
workspace_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_dir not in sys.path:
    sys.path.insert(0, workspace_dir)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring API keys and external services"
    )
    config.addinivalue_line(
        "markers",
        "llm_judge: mark test as using LLM-as-Judge (costs money)"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (>10 seconds)"
    )


@pytest.fixture
def mock_env_no_api_keys(monkeypatch):
    """Fixture to clear all API keys for testing mock behavior."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("ENRICHLAYER_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)


@pytest.fixture
def sample_linkedin_data():
    """Fixture providing sample LinkedIn profile data."""
    return {
        "name": "Test User",
        "title": "Senior Engineer",
        "company": "Test Corp",
        "location": "San Francisco, CA",
        "summary": "Experienced software engineer with 10+ years...",
        "experience": [
            {"title": "Senior Engineer", "company": "Test Corp", "duration": "3 years"},
            {"title": "Engineer", "company": "Previous Co", "duration": "5 years"},
        ],
        "skills": ["Python", "Machine Learning", "Leadership"],
        "mock": True,
    }


@pytest.fixture
def sample_company_data():
    """Fixture providing sample company analysis data."""
    return {
        "name": "Test Corp",
        "industry": "Technology",
        "size": "1,000+ employees",
        "description": "Test Corp is a leading technology company...",
        "recent_initiatives": ["AI adoption", "Cloud migration"],
        "competitors": ["Competitor A", "Competitor B"],
        "mock": True,
    }


@pytest.fixture
def sample_search_results():
    """Fixture providing sample web search results."""
    return [
        {
            "title": "Test Corp Announces AI Product",
            "url": "https://example.com/news/1",
            "snippet": "Test Corp today announced their new AI product...",
        },
        {
            "title": "Test Corp Q4 Results",
            "url": "https://example.com/news/2",
            "snippet": "Test Corp reported strong Q4 results...",
        },
    ]


@pytest.fixture
def sample_test_case():
    """Fixture providing a sample evaluation test case."""
    return {
        "name": "test_case_fixture",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/test-user",
            "company_name": "Test Corp",
        },
        "outputs": {
            "expected_fields": ["linkedin_data", "company_data", "final_report"],
            "should_mention": ["engineer", "Test Corp", "technology"],
            "min_report_length": 300,
        },
    }


@pytest.fixture
def sample_research_report():
    """Fixture providing a sample research report."""
    return """
    ## Executive Summary
    Test User is a Senior Engineer at Test Corp with strong technical background.

    ## Key Insights
    - 10+ years of engineering experience
    - Currently focused on AI/ML initiatives
    - Active in the tech community

    ## Recommended Talking Points
    1. Discuss their recent AI adoption journey
    2. Ask about engineering team growth challenges
    3. Reference their cloud migration project

    ## Sources
    - LinkedIn profile
    - Company website
    - Recent news articles
    """
