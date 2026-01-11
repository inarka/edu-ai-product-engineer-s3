"""Evaluation framework for Research Squad and Deep Research Agent.

This module provides:
- Dataset creation utilities
- Automated evaluators (schema, keywords)
- LLM-as-Judge evaluators (quality, relevance)
- Experiment comparison tools

Usage:
    from evaluation import create_dataset, evaluate_agent, compare_experiments
"""

from .dataset import create_research_dataset, add_test_case
from .evaluators import (
    schema_evaluator,
    keyword_coverage_evaluator,
    quality_evaluator,
    latency_evaluator,
    token_efficiency_evaluator,
)
from .compare import run_comparison, print_comparison_results

__all__ = [
    "create_research_dataset",
    "add_test_case",
    "schema_evaluator",
    "keyword_coverage_evaluator",
    "quality_evaluator",
    "latency_evaluator",
    "token_efficiency_evaluator",
    "run_comparison",
    "print_comparison_results",
]
