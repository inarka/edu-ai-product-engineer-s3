"""Evaluators for Research Squad and Deep Research Agent.

This module provides the three tiers of evaluation:
1. Automated (Tier 1): Schema validation, keyword checks - $0.00/run
2. LLM-as-Judge (Tier 2): Semantic quality, relevance - $0.01-0.05/run
3. Human-in-the-Loop (Tier 3): Subjective quality - $5-50/run

The 50-40-10 Rule:
- 50% Automated evaluators
- 40% LLM-as-Judge evaluators
- 10% Human evaluation

Usage with LangSmith:
    from langsmith.evaluation import evaluate
    from evaluation.evaluators import schema_evaluator, quality_evaluator

    results = evaluate(
        agent.invoke,
        data="research_squad_eval",
        evaluators=[schema_evaluator, quality_evaluator],
    )
"""

import json
import os
from typing import Any

from langsmith.schemas import Run, Example
from langchain_openai import ChatOpenAI

# LLM for judge evaluations (use fast/cheap model)
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-4.1-mini")


# === TIER 1: AUTOMATED EVALUATORS ===
# These are cheap/free and run on every evaluation

def schema_evaluator(run: Run, example: Example) -> dict:
    """Check if output contains expected fields.

    Tier 1 (Automated): Validates structure, not content.
    Cost: $0.00 per run

    Args:
        run: The agent run to evaluate
        example: The test case with expected outputs

    Returns:
        Evaluation result with score and comment
    """
    output = run.outputs or {}
    expected_fields = example.outputs.get("expected_fields", [])

    if not expected_fields:
        return {
            "key": "schema_valid",
            "score": 1.0,
            "comment": "No expected fields defined",
        }

    # Check which fields are present
    present = [f for f in expected_fields if output.get(f) is not None]
    missing = [f for f in expected_fields if f not in present]

    score = len(present) / len(expected_fields) if expected_fields else 1.0

    return {
        "key": "schema_valid",
        "score": score,
        "comment": f"Present: {present}. Missing: {missing}" if missing else "All fields present",
    }


def keyword_coverage_evaluator(run: Run, example: Example) -> dict:
    """Check if output contains expected keywords.

    Tier 1 (Automated): Simple string matching for key terms.
    Cost: $0.00 per run

    Args:
        run: The agent run to evaluate
        example: The test case with expected outputs

    Returns:
        Evaluation result with score and comment
    """
    output = run.outputs or {}
    should_mention = example.outputs.get("should_mention", [])

    if not should_mention:
        return {
            "key": "keyword_coverage",
            "score": 1.0,
            "comment": "No keywords to check",
        }

    # Convert output to searchable string
    output_text = json.dumps(output).lower()

    # Check which keywords are mentioned
    found = [kw for kw in should_mention if kw.lower() in output_text]
    missing = [kw for kw in should_mention if kw.lower() not in output_text]

    score = len(found) / len(should_mention) if should_mention else 1.0

    return {
        "key": "keyword_coverage",
        "score": score,
        "comment": f"Found: {found}. Missing: {missing}" if missing else "All keywords present",
    }


def report_length_evaluator(run: Run, example: Example) -> dict:
    """Check if report meets minimum length requirements.

    Tier 1 (Automated): Ensures sufficient detail in output.
    Cost: $0.00 per run
    """
    output = run.outputs or {}
    min_length = example.outputs.get("min_report_length", 0)

    report = output.get("final_report", "") or output.get("output", "")
    actual_length = len(report)

    if min_length == 0:
        return {
            "key": "report_length",
            "score": 1.0,
            "comment": "No minimum length defined",
        }

    score = min(1.0, actual_length / min_length)

    return {
        "key": "report_length",
        "score": score,
        "comment": f"Length: {actual_length} chars (min: {min_length})",
    }


def graceful_error_evaluator(run: Run, example: Example) -> dict:
    """Check if agent handles errors gracefully.

    Tier 1 (Automated): For adversarial test cases.
    Cost: $0.00 per run
    """
    should_handle = example.outputs.get("should_handle_gracefully", False)

    if not should_handle:
        return {
            "key": "graceful_error",
            "score": 1.0,
            "comment": "Not an error case",
        }

    # Check for graceful handling
    output = run.outputs or {}
    error = run.error

    # Graceful = no crash AND some output
    if error:
        return {
            "key": "graceful_error",
            "score": 0.0,
            "comment": f"Agent crashed: {error}",
        }

    # Check if there's meaningful output (not just empty)
    has_output = bool(output.get("final_report") or output.get("output") or output.get("error_message"))

    return {
        "key": "graceful_error",
        "score": 1.0 if has_output else 0.5,
        "comment": "Handled gracefully" if has_output else "No output but didn't crash",
    }


# === TIER 2: LLM-AS-JUDGE EVALUATORS ===
# These use LLM for semantic understanding

def quality_evaluator(run: Run, example: Example) -> dict:
    """Evaluate research quality using LLM-as-Judge.

    Tier 2 (LLM-as-Judge): Semantic quality assessment.
    Cost: ~$0.01-0.05 per run

    Rubric:
    - 5: Excellent - actionable insights, specific details, well-structured
    - 4: Good - useful information, some specific details
    - 3: Adequate - basic information, generic insights
    - 2: Poor - minimal useful content
    - 1: Failing - no useful content or incorrect

    Args:
        run: The agent run to evaluate
        example: The test case with expected outputs

    Returns:
        Evaluation result with normalized score (0-1) and reasoning
    """
    output = run.outputs or {}
    report = output.get("final_report", "") or output.get("output", "")

    if not report:
        return {
            "key": "research_quality",
            "score": 0.0,
            "comment": "No report generated",
        }

    # Build judge prompt
    judge_prompt = f"""Evaluate this B2B sales research report on a scale of 1-5.

Report to evaluate:
{report[:3000]}  # Limit to avoid token overflow

Evaluation Criteria:
1. Actionable Insights: Does it provide specific talking points for sales?
2. Specificity: Are details specific (not generic)?
3. Recency: Does it reference recent events/changes?
4. Structure: Is it well-organized and easy to scan?
5. Relevance: Does it focus on B2B sales context?

Scoring:
- 5: Excellent - all criteria met with high quality
- 4: Good - most criteria met
- 3: Adequate - basic but useful
- 2: Poor - minimal value
- 1: Failing - no value or incorrect

Return JSON: {{"score": 1-5, "reasoning": "brief explanation"}}
"""

    try:
        llm = ChatOpenAI(model=JUDGE_MODEL, temperature=0)
        response = llm.invoke(judge_prompt)

        # Parse response
        result = json.loads(response.content)
        score = result.get("score", 3)
        reasoning = result.get("reasoning", "")

        return {
            "key": "research_quality",
            "score": score / 5.0,  # Normalize to 0-1
            "comment": f"Score {score}/5: {reasoning}",
        }
    except Exception as e:
        return {
            "key": "research_quality",
            "score": 0.5,  # Default middle score on error
            "comment": f"Judge error: {str(e)}",
        }


def relevance_evaluator(run: Run, example: Example) -> dict:
    """Evaluate if research is relevant to the target.

    Tier 2 (LLM-as-Judge): Checks if output matches the input request.
    Cost: ~$0.01-0.05 per run
    """
    inputs = run.inputs or {}
    output = run.outputs or {}

    target = inputs.get("linkedin_url", "") or inputs.get("target", "")
    company = inputs.get("company_name", "") or inputs.get("company", "")
    report = output.get("final_report", "") or output.get("output", "")

    if not report:
        return {
            "key": "relevance",
            "score": 0.0,
            "comment": "No report to evaluate",
        }

    judge_prompt = f"""Evaluate if this research report is relevant to the requested target.

Target: {target}
Company: {company}

Report:
{report[:2000]}

Questions:
1. Does the report discuss the correct person/company?
2. Is the information relevant to B2B sales outreach?
3. Does it avoid off-topic tangents?

Return JSON: {{"score": 1-5, "reasoning": "brief explanation"}}
"""

    try:
        llm = ChatOpenAI(model=JUDGE_MODEL, temperature=0)
        response = llm.invoke(judge_prompt)
        result = json.loads(response.content)

        return {
            "key": "relevance",
            "score": result.get("score", 3) / 5.0,
            "comment": result.get("reasoning", ""),
        }
    except Exception as e:
        return {
            "key": "relevance",
            "score": 0.5,
            "comment": f"Judge error: {str(e)}",
        }


def input_data_consistency_evaluator(run: Run, example: Example) -> dict:
    """Check if report conclusions match the gathered source data.

    Tier 2 (LLM-as-Judge): Detects when agent silently reconciles
    contradictory information instead of flagging it.
    Cost: ~$0.02-0.05 per run

    Example: User says "research X at Company A" but LinkedIn shows
    X works at Company B. Agent should flag this, not silently reconcile.
    """
    inputs = run.inputs or {}
    output = run.outputs or {}

    target = inputs.get("linkedin_url", "") or inputs.get("target", "")
    company = inputs.get("company_name", "") or inputs.get("company", "")
    report = output.get("final_report", "") or output.get("output", "")

    if not report or not company:
        return {
            "key": "input_data_consistency",
            "score": 1.0,
            "comment": "No company to verify",
        }

    judge_prompt = f"""Analyze this research report for input-data consistency.

USER INPUT:
- Target: {target}
- Company claimed: {company}

REPORT:
{report[:3000]}

QUESTIONS:
1. Does the report confirm the person actually works at "{company}"?
2. If LinkedIn/source data shows a DIFFERENT company, did the agent:
   a) Explicitly flag the mismatch? (GOOD)
   b) Silently reconcile by finding tangential connections? (BAD)
   c) Ignore the mismatch entirely? (BAD)

SCORING:
- 1.0: Data matches OR agent explicitly flagged mismatch
- 0.5: Minor discrepancy, agent partially addressed
- 0.0: Major mismatch silently reconciled (hallucination risk)

Return JSON: {{"score": 0.0, "mismatch_found": true, "reasoning": "explanation"}}
Use 0.0, 0.5, or 1.0 for score. Set mismatch_found to true if there's a discrepancy.
"""

    try:
        llm = ChatOpenAI(model=JUDGE_MODEL, temperature=0)
        response = llm.invoke(judge_prompt)
        result = json.loads(response.content)
        return {
            "key": "input_data_consistency",
            "score": result.get("score", 0.5),
            "comment": f"Mismatch: {result.get('mismatch_found', 'unknown')} - {result.get('reasoning', '')}",
        }
    except Exception as e:
        return {
            "key": "input_data_consistency",
            "score": 0.5,
            "comment": f"Judge error: {str(e)}",
        }


# === PERFORMANCE EVALUATORS ===
# These measure efficiency, not quality

def latency_evaluator(run: Run, example: Example) -> dict:
    """Measure execution time.

    Performance metric: Lower is better.
    Used for comparing LangGraph vs Deep Agents efficiency.
    """
    if run.end_time and run.start_time:
        latency = (run.end_time - run.start_time).total_seconds()
    else:
        latency = 0

    # Score: penalize runs over 30 seconds
    max_acceptable = 30.0
    score = max(0.0, 1.0 - (latency / max_acceptable)) if latency > 0 else 0.5

    return {
        "key": "latency_seconds",
        "score": score,
        "comment": f"{latency:.2f}s",
    }


def token_efficiency_evaluator(run: Run, example: Example) -> dict:
    """Measure token usage efficiency.

    Performance metric: Lower tokens = better efficiency.
    Especially important for comparing multi-agent approaches.
    """
    # Sum tokens from all child runs
    total_tokens = 0

    def count_tokens(r: Run) -> int:
        tokens = 0
        if hasattr(r, "extra") and r.extra:
            usage = r.extra.get("token_usage", {}) or {}
            tokens = usage.get("total_tokens", 0)
        return tokens

    total_tokens = count_tokens(run)

    # Also count child runs (for multi-agent)
    # Note: This requires the full run tree which may not always be available

    # Score: penalize runs over 10k tokens
    max_acceptable = 10000
    score = max(0.0, 1.0 - (total_tokens / max_acceptable)) if total_tokens > 0 else 0.5

    return {
        "key": "token_efficiency",
        "score": score,
        "comment": f"{total_tokens} tokens",
    }


# === TIER 3: HUMAN-IN-THE-LOOP ===
# These flag cases for human review

def needs_human_review(run: Run, example: Example) -> dict:
    """Flag cases that need human review.

    Tier 3 preparation: Identifies edge cases for human evaluation.
    This creates a feedback annotation in LangSmith.
    """
    output = run.outputs or {}
    report = output.get("final_report", "") or output.get("output", "")

    # Heuristics for flagging
    needs_review = (
        len(report) < 200 or                    # Too short
        "error" in report.lower() or            # Contains error
        "could not find" in report.lower() or   # Missing data
        "n/a" in report.lower() or              # Placeholder content
        run.error is not None                   # Agent errored
    )

    return {
        "key": "needs_human_review",
        "score": 0.0 if needs_review else 1.0,
        "comment": "Flagged for human review" if needs_review else "Auto-approved",
    }


# === EVALUATOR SETS ===
# Pre-configured evaluator groups for common use cases

AUTOMATED_EVALUATORS = [
    schema_evaluator,
    keyword_coverage_evaluator,
    report_length_evaluator,
    graceful_error_evaluator,
]

LLM_JUDGE_EVALUATORS = [
    quality_evaluator,
    relevance_evaluator,
    input_data_consistency_evaluator,
]

PERFORMANCE_EVALUATORS = [
    latency_evaluator,
    token_efficiency_evaluator,
]

ALL_EVALUATORS = (
    AUTOMATED_EVALUATORS +
    LLM_JUDGE_EVALUATORS +
    PERFORMANCE_EVALUATORS +
    [needs_human_review]
)
