"""Unit tests for evaluators.

Tests the evaluation functions in isolation with mock Run/Example objects.
These tests do NOT require API keys and run fast (~1s).

Run with:
    pytest tests/test_evaluators.py -v
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import json

# Import evaluators
from evaluation.evaluators import (
    schema_evaluator,
    keyword_coverage_evaluator,
    report_length_evaluator,
    graceful_error_evaluator,
    latency_evaluator,
    token_efficiency_evaluator,
    needs_human_review,
    AUTOMATED_EVALUATORS,
    LLM_JUDGE_EVALUATORS,
    PERFORMANCE_EVALUATORS,
    ALL_EVALUATORS,
)


# === FIXTURES ===

def create_mock_run(
    outputs: dict = None,
    inputs: dict = None,
    error: str = None,
    start_time: datetime = None,
    end_time: datetime = None,
    extra: dict = None,
) -> MagicMock:
    """Create a mock Run object for testing."""
    run = MagicMock()
    run.outputs = outputs or {}
    run.inputs = inputs or {}
    run.error = error
    run.start_time = start_time
    run.end_time = end_time
    run.extra = extra
    return run


def create_mock_example(outputs: dict = None, inputs: dict = None) -> MagicMock:
    """Create a mock Example object for testing."""
    example = MagicMock()
    example.outputs = outputs or {}
    example.inputs = inputs or {}
    return example


# === TIER 1: SCHEMA EVALUATOR TESTS ===

class TestSchemaEvaluator:
    """Tests for schema_evaluator function."""

    def test_perfect_schema_returns_1(self):
        """All expected fields present → score 1.0"""
        run = create_mock_run(outputs={
            "linkedin_data": {"name": "Test"},
            "company_data": {"name": "TestCo"},
            "final_report": "Test report",
        })
        example = create_mock_example(outputs={
            "expected_fields": ["linkedin_data", "company_data", "final_report"]
        })

        result = schema_evaluator(run, example)

        assert result["key"] == "schema_valid"
        assert result["score"] == 1.0
        assert "All fields present" in result["comment"]

    def test_missing_fields_returns_partial(self):
        """2/4 fields → score 0.5"""
        run = create_mock_run(outputs={
            "linkedin_data": {"name": "Test"},
            "final_report": "Test report",
        })
        example = create_mock_example(outputs={
            "expected_fields": ["linkedin_data", "company_data", "news_data", "final_report"]
        })

        result = schema_evaluator(run, example)

        assert result["score"] == 0.5
        assert "Missing:" in result["comment"]
        assert "company_data" in result["comment"]

    def test_empty_output_returns_0(self):
        """No fields present → score 0.0"""
        run = create_mock_run(outputs={})
        example = create_mock_example(outputs={
            "expected_fields": ["linkedin_data", "company_data"]
        })

        result = schema_evaluator(run, example)

        assert result["score"] == 0.0

    def test_no_expected_fields_returns_1(self):
        """No expected fields defined → default score 1.0"""
        run = create_mock_run(outputs={"some_field": "value"})
        example = create_mock_example(outputs={})

        result = schema_evaluator(run, example)

        assert result["score"] == 1.0
        assert "No expected fields defined" in result["comment"]


# === TIER 1: KEYWORD COVERAGE EVALUATOR TESTS ===

class TestKeywordCoverageEvaluator:
    """Tests for keyword_coverage_evaluator function."""

    def test_all_keywords_found_returns_1(self):
        """All keywords present → score 1.0"""
        run = create_mock_run(outputs={
            "final_report": "The CEO leads Microsoft in the cloud and AI space."
        })
        example = create_mock_example(outputs={
            "should_mention": ["CEO", "Microsoft", "cloud", "AI"]
        })

        result = keyword_coverage_evaluator(run, example)

        assert result["key"] == "keyword_coverage"
        assert result["score"] == 1.0

    def test_partial_keywords_returns_partial(self):
        """2/4 keywords → score 0.5"""
        run = create_mock_run(outputs={
            "final_report": "The CEO leads Microsoft."
        })
        example = create_mock_example(outputs={
            "should_mention": ["CEO", "Microsoft", "cloud", "AI"]
        })

        result = keyword_coverage_evaluator(run, example)

        assert result["score"] == 0.5
        assert "Missing:" in result["comment"]

    def test_case_insensitive_matching(self):
        """'CEO' matches 'ceo' in output"""
        run = create_mock_run(outputs={
            "final_report": "ceo microsoft"
        })
        example = create_mock_example(outputs={
            "should_mention": ["CEO", "Microsoft"]
        })

        result = keyword_coverage_evaluator(run, example)

        assert result["score"] == 1.0

    def test_no_keywords_defined_returns_1(self):
        """No keywords to check → default score 1.0"""
        run = create_mock_run(outputs={"final_report": "Some report"})
        example = create_mock_example(outputs={})

        result = keyword_coverage_evaluator(run, example)

        assert result["score"] == 1.0
        assert "No keywords to check" in result["comment"]


# === TIER 1: REPORT LENGTH EVALUATOR TESTS ===

class TestReportLengthEvaluator:
    """Tests for report_length_evaluator function."""

    def test_within_bounds_returns_1(self):
        """Length >= min → score 1.0"""
        run = create_mock_run(outputs={
            "final_report": "A" * 500  # 500 chars
        })
        example = create_mock_example(outputs={
            "min_report_length": 200
        })

        result = report_length_evaluator(run, example)

        assert result["key"] == "report_length"
        assert result["score"] == 1.0

    def test_too_short_penalized(self):
        """Length < min → score < 1.0"""
        run = create_mock_run(outputs={
            "final_report": "A" * 100  # 100 chars
        })
        example = create_mock_example(outputs={
            "min_report_length": 500
        })

        result = report_length_evaluator(run, example)

        assert result["score"] == 0.2  # 100/500
        assert "100 chars" in result["comment"]

    def test_no_minimum_defined_returns_1(self):
        """No min_report_length → default score 1.0"""
        run = create_mock_run(outputs={"final_report": "Short"})
        example = create_mock_example(outputs={})

        result = report_length_evaluator(run, example)

        assert result["score"] == 1.0

    def test_uses_output_field_fallback(self):
        """Falls back to 'output' field if no 'final_report'"""
        run = create_mock_run(outputs={
            "output": "A" * 300
        })
        example = create_mock_example(outputs={
            "min_report_length": 300
        })

        result = report_length_evaluator(run, example)

        assert result["score"] == 1.0


# === TIER 1: GRACEFUL ERROR EVALUATOR TESTS ===

class TestGracefulErrorEvaluator:
    """Tests for graceful_error_evaluator function."""

    def test_not_error_case_returns_1(self):
        """Non-error case → score 1.0"""
        run = create_mock_run(outputs={"final_report": "Report"})
        example = create_mock_example(outputs={"should_handle_gracefully": False})

        result = graceful_error_evaluator(run, example)

        assert result["key"] == "graceful_error"
        assert result["score"] == 1.0
        assert "Not an error case" in result["comment"]

    def test_crash_returns_0(self):
        """Run with error field → score 0.0"""
        run = create_mock_run(
            outputs={},
            error="Connection timeout"
        )
        example = create_mock_example(outputs={"should_handle_gracefully": True})

        result = graceful_error_evaluator(run, example)

        assert result["score"] == 0.0
        assert "crashed" in result["comment"]

    def test_handled_gracefully_returns_1(self):
        """Error case with output → score 1.0"""
        run = create_mock_run(outputs={
            "error_message": "Could not find profile",
            "final_report": "Unable to find the requested profile."
        })
        example = create_mock_example(outputs={"should_handle_gracefully": True})

        result = graceful_error_evaluator(run, example)

        assert result["score"] == 1.0
        assert "Handled gracefully" in result["comment"]

    def test_no_output_no_crash_returns_half(self):
        """No output but no crash → score 0.5"""
        run = create_mock_run(outputs={})
        example = create_mock_example(outputs={"should_handle_gracefully": True})

        result = graceful_error_evaluator(run, example)

        assert result["score"] == 0.5


# === PERFORMANCE: LATENCY EVALUATOR TESTS ===

class TestLatencyEvaluator:
    """Tests for latency_evaluator function."""

    def test_fast_returns_high_score(self):
        """< 30s → high score"""
        start = datetime.now()
        end = start + timedelta(seconds=10)
        run = create_mock_run(start_time=start, end_time=end)
        example = create_mock_example()

        result = latency_evaluator(run, example)

        assert result["key"] == "latency_seconds"
        assert result["score"] > 0.6  # 1 - (10/30) = 0.67
        assert "10.00s" in result["comment"]

    def test_slow_returns_low_score(self):
        """> 30s → low score (capped at 0)"""
        start = datetime.now()
        end = start + timedelta(seconds=60)
        run = create_mock_run(start_time=start, end_time=end)
        example = create_mock_example()

        result = latency_evaluator(run, example)

        assert result["score"] == 0.0  # max(0, 1 - 60/30) = 0

    def test_no_timestamps_returns_half(self):
        """Missing timestamps → default 0.5"""
        run = create_mock_run(start_time=None, end_time=None)
        example = create_mock_example()

        result = latency_evaluator(run, example)

        assert result["score"] == 0.5


# === PERFORMANCE: TOKEN EFFICIENCY EVALUATOR TESTS ===

class TestTokenEfficiencyEvaluator:
    """Tests for token_efficiency_evaluator function."""

    def test_efficient_returns_high_score(self):
        """< 10k tokens → high score"""
        run = create_mock_run(extra={
            "token_usage": {"total_tokens": 5000}
        })
        example = create_mock_example()

        result = token_efficiency_evaluator(run, example)

        assert result["key"] == "token_efficiency"
        assert result["score"] == 0.5  # 1 - (5000/10000)
        assert "5000 tokens" in result["comment"]

    def test_inefficient_returns_low_score(self):
        """> 10k tokens → low score (capped at 0)"""
        run = create_mock_run(extra={
            "token_usage": {"total_tokens": 20000}
        })
        example = create_mock_example()

        result = token_efficiency_evaluator(run, example)

        assert result["score"] == 0.0

    def test_no_token_info_returns_half(self):
        """Missing token info → default 0.5"""
        run = create_mock_run(extra=None)
        example = create_mock_example()

        result = token_efficiency_evaluator(run, example)

        assert result["score"] == 0.5


# === TIER 3: NEEDS HUMAN REVIEW TESTS ===

class TestNeedsHumanReview:
    """Tests for needs_human_review function."""

    def test_good_report_auto_approved(self):
        """Normal report → score 1.0 (auto-approved)"""
        run = create_mock_run(outputs={
            "final_report": "A" * 500  # Sufficiently long
        })
        example = create_mock_example()

        result = needs_human_review(run, example)

        assert result["key"] == "needs_human_review"
        assert result["score"] == 1.0
        assert "Auto-approved" in result["comment"]

    def test_short_report_flagged(self):
        """Short report (< 200 chars) → flagged for review"""
        run = create_mock_run(outputs={
            "final_report": "Too short"
        })
        example = create_mock_example()

        result = needs_human_review(run, example)

        assert result["score"] == 0.0
        assert "Flagged" in result["comment"]

    def test_error_in_report_flagged(self):
        """Report containing 'error' → flagged"""
        run = create_mock_run(outputs={
            "final_report": "An error occurred while processing" + "A" * 200
        })
        example = create_mock_example()

        result = needs_human_review(run, example)

        assert result["score"] == 0.0

    def test_run_error_flagged(self):
        """Run with error → flagged"""
        run = create_mock_run(
            outputs={"final_report": "A" * 500},
            error="Timeout"
        )
        example = create_mock_example()

        result = needs_human_review(run, example)

        assert result["score"] == 0.0


# === EVALUATOR SETS TESTS ===

class TestEvaluatorSets:
    """Tests for pre-configured evaluator collections."""

    def test_automated_evaluators_count(self):
        """AUTOMATED_EVALUATORS has 4 evaluators"""
        assert len(AUTOMATED_EVALUATORS) == 4

    def test_llm_judge_evaluators_count(self):
        """LLM_JUDGE_EVALUATORS has 3 evaluators (quality, relevance, input_data_consistency)"""
        assert len(LLM_JUDGE_EVALUATORS) == 3

    def test_performance_evaluators_count(self):
        """PERFORMANCE_EVALUATORS has 2 evaluators"""
        assert len(PERFORMANCE_EVALUATORS) == 2

    def test_all_evaluators_count(self):
        """ALL_EVALUATORS has 10 evaluators total"""
        assert len(ALL_EVALUATORS) == 10

    def test_evaluators_are_callable(self):
        """All evaluators are callable functions"""
        for evaluator in ALL_EVALUATORS:
            assert callable(evaluator)

    def test_evaluators_return_dict_with_required_keys(self):
        """All evaluators return dict with key, score, comment"""
        run = create_mock_run(outputs={"final_report": "Test"})
        example = create_mock_example()

        for evaluator in AUTOMATED_EVALUATORS + PERFORMANCE_EVALUATORS + [needs_human_review]:
            result = evaluator(run, example)
            assert "key" in result
            assert "score" in result
            assert "comment" in result
            assert 0.0 <= result["score"] <= 1.0
