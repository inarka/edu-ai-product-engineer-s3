"""LLM-as-Judge evaluator tests.

These tests verify the semantic evaluators work correctly.
They require OPENAI_API_KEY to run and cost ~$0.10 total.

Run with:
    pytest tests/test_llm_judge.py -v -m llm_judge

Skip if no API key:
    pytest tests/test_llm_judge.py -v  # auto-skips without key
"""

import os
import pytest
from unittest.mock import MagicMock, patch

# Mark all tests in this module as llm_judge
pytestmark = pytest.mark.llm_judge

# Skip module if no OpenAI API key
skip_without_api_key = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set - skipping LLM judge tests"
)


def create_mock_run(outputs: dict = None, inputs: dict = None) -> MagicMock:
    """Create a mock Run object for testing."""
    run = MagicMock()
    run.outputs = outputs or {}
    run.inputs = inputs or {}
    run.error = None
    return run


def create_mock_example(outputs: dict = None) -> MagicMock:
    """Create a mock Example object for testing."""
    example = MagicMock()
    example.outputs = outputs or {}
    return example


# === QUALITY EVALUATOR TESTS ===

@skip_without_api_key
class TestQualityEvaluatorLive:
    """Live tests for quality_evaluator (requires API key)."""

    def test_high_quality_report_scores_high(self):
        """Well-structured report → score > 0.6"""
        from evaluation.evaluators import quality_evaluator

        high_quality_report = """
        ## Executive Summary
        John Smith is a seasoned technology executive with 15+ years of experience
        in enterprise software. Currently serving as CTO at TechCorp, he oversees
        a team of 200 engineers and has driven significant cloud transformation.

        ## Key Insights
        - Recently led migration to microservices architecture (completed Q3 2024)
        - Active speaker at AWS re:Invent on cloud-native strategies
        - Board member at two AI startups, suggesting interest in emerging tech
        - LinkedIn shows engagement with content about DevOps and SRE practices

        ## Recommended Talking Points
        1. Reference their recent microservices migration success
        2. Discuss challenges in managing distributed engineering teams
        3. Ask about their AI/ML infrastructure strategy

        ## Sources
        - LinkedIn profile analysis
        - TechCorp company news
        - Conference speaker database
        """

        run = create_mock_run(outputs={"final_report": high_quality_report})
        example = create_mock_example()

        result = quality_evaluator(run, example)

        assert result["key"] == "research_quality"
        assert result["score"] > 0.6, f"Expected high score, got {result['score']}: {result['comment']}"
        assert "reasoning" in result["comment"] or len(result["comment"]) > 10

    def test_low_quality_report_scores_low(self):
        """Generic, short report → score < 0.6"""
        from evaluation.evaluators import quality_evaluator

        low_quality_report = "John works at a company. He seems to be in tech."

        run = create_mock_run(outputs={"final_report": low_quality_report})
        example = create_mock_example()

        result = quality_evaluator(run, example)

        assert result["score"] < 0.6, f"Expected low score, got {result['score']}: {result['comment']}"

    def test_no_report_returns_zero(self):
        """Empty report → score 0"""
        from evaluation.evaluators import quality_evaluator

        run = create_mock_run(outputs={})
        example = create_mock_example()

        result = quality_evaluator(run, example)

        assert result["score"] == 0.0
        assert "No report" in result["comment"]


# === RELEVANCE EVALUATOR TESTS ===

@skip_without_api_key
class TestRelevanceEvaluatorLive:
    """Live tests for relevance_evaluator (requires API key)."""

    def test_relevant_response_scores_high(self):
        """On-topic response for target → score > 0.6"""
        from evaluation.evaluators import relevance_evaluator

        # Report about Satya Nadella at Microsoft
        report = """
        Satya Nadella has been Microsoft's CEO since 2014. Under his leadership,
        Microsoft has pivoted strongly toward cloud computing with Azure, and
        more recently has made significant investments in AI through partnerships
        with OpenAI. He frequently speaks about "growth mindset" and the importance
        of empathy in leadership. For a B2B sales approach, discussing Azure's
        enterprise capabilities or their Copilot AI initiatives would be relevant.
        """

        run = create_mock_run(
            outputs={"final_report": report},
            inputs={
                "linkedin_url": "https://linkedin.com/in/satya-nadella",
                "company_name": "Microsoft"
            }
        )
        example = create_mock_example()

        result = relevance_evaluator(run, example)

        assert result["key"] == "relevance"
        assert result["score"] > 0.6, f"Expected relevant, got {result['score']}: {result['comment']}"

    def test_irrelevant_response_scores_low(self):
        """Off-topic response → score < 0.6"""
        from evaluation.evaluators import relevance_evaluator

        # Report about wrong person/company
        report = """
        Apple is a technology company known for the iPhone and Mac computers.
        Tim Cook is their current CEO. They have a strong focus on privacy
        and consumer hardware. The company was founded by Steve Jobs.
        """

        run = create_mock_run(
            outputs={"final_report": report},
            inputs={
                "linkedin_url": "https://linkedin.com/in/satya-nadella",
                "company_name": "Microsoft"
            }
        )
        example = create_mock_example()

        result = relevance_evaluator(run, example)

        assert result["score"] < 0.6, f"Expected irrelevant, got {result['score']}: {result['comment']}"


# === MOCK TESTS (Always Run) ===

class TestQualityEvaluatorMocked:
    """Mocked tests for quality_evaluator (no API needed)."""

    @patch("evaluation.evaluators.ChatOpenAI")
    def test_returns_reasoning(self, mock_llm_class):
        """Evaluator returns reasoning from LLM"""
        from evaluation.evaluators import quality_evaluator

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"score": 4, "reasoning": "Good structure and specific details"}'
        )
        mock_llm_class.return_value = mock_llm

        run = create_mock_run(outputs={"final_report": "Some report content here"})
        example = create_mock_example()

        result = quality_evaluator(run, example)

        assert result["score"] == 0.8  # 4/5
        assert "Good structure" in result["comment"]

    @patch("evaluation.evaluators.ChatOpenAI")
    def test_handles_llm_error_gracefully(self, mock_llm_class):
        """Evaluator returns 0.5 on LLM error"""
        from evaluation.evaluators import quality_evaluator

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API rate limit")
        mock_llm_class.return_value = mock_llm

        run = create_mock_run(outputs={"final_report": "Some report"})
        example = create_mock_example()

        result = quality_evaluator(run, example)

        assert result["score"] == 0.5
        assert "error" in result["comment"].lower()


class TestRelevanceEvaluatorMocked:
    """Mocked tests for relevance_evaluator (no API needed)."""

    @patch("evaluation.evaluators.ChatOpenAI")
    def test_handles_missing_inputs(self, mock_llm_class):
        """Evaluator handles missing target/company gracefully"""
        from evaluation.evaluators import relevance_evaluator

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(
            content='{"score": 3, "reasoning": "Cannot verify relevance without target"}'
        )
        mock_llm_class.return_value = mock_llm

        run = create_mock_run(
            outputs={"final_report": "Some report"},
            inputs={}  # Missing target and company
        )
        example = create_mock_example()

        result = relevance_evaluator(run, example)

        # Should still return a valid result
        assert "key" in result
        assert "score" in result
        assert 0.0 <= result["score"] <= 1.0
