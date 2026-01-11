"""Evaluator templates for LangSmith.

This template provides common evaluator patterns you can customize.

Evaluator Types:
- Automated (Tier 1): Free, fast, deterministic
- LLM-as-Judge (Tier 2): Semantic understanding, ~$0.01-0.05/run
- Human-in-Loop (Tier 3): Flag for review, $5-50/run
"""

import json
from langsmith.schemas import Run, Example
from langchain_openai import ChatOpenAI


# === TIER 1: AUTOMATED EVALUATORS ===

def schema_evaluator(run: Run, example: Example) -> dict:
    """Check if output contains expected fields.

    Customize: Update expected_fields in your test cases.
    """
    output = run.outputs or {}
    expected = example.outputs.get("expected_fields", [])

    if not expected:
        return {"key": "schema_valid", "score": 1.0, "comment": "No schema defined"}

    present = [f for f in expected if output.get(f) is not None]
    score = len(present) / len(expected)

    return {
        "key": "schema_valid",
        "score": score,
        "comment": f"Fields present: {len(present)}/{len(expected)}",
    }


def keyword_evaluator(run: Run, example: Example) -> dict:
    """Check if output contains expected keywords.

    Customize: Update should_mention in your test cases.
    """
    output = run.outputs or {}
    should_mention = example.outputs.get("should_mention", [])

    if not should_mention:
        return {"key": "keywords", "score": 1.0, "comment": "No keywords defined"}

    output_text = json.dumps(output).lower()
    found = [kw for kw in should_mention if kw.lower() in output_text]
    score = len(found) / len(should_mention)

    return {
        "key": "keywords",
        "score": score,
        "comment": f"Keywords found: {len(found)}/{len(should_mention)}",
    }


def length_evaluator(run: Run, example: Example) -> dict:
    """Check if output meets length requirements.

    Customize: Update min_length/max_length in your test cases.
    """
    output = run.outputs or {}
    # Adjust this to match your output field name
    response = output.get("response", "") or output.get("output", "")

    min_len = example.outputs.get("min_length", 0)
    max_len = example.outputs.get("max_length", float("inf"))

    actual = len(response)

    if actual < min_len:
        score = actual / min_len
        comment = f"Too short: {actual} < {min_len}"
    elif actual > max_len:
        score = max_len / actual
        comment = f"Too long: {actual} > {max_len}"
    else:
        score = 1.0
        comment = f"Length OK: {actual}"

    return {"key": "length", "score": score, "comment": comment}


# === TIER 2: LLM-AS-JUDGE EVALUATORS ===

def quality_evaluator(run: Run, example: Example) -> dict:
    """Evaluate output quality using LLM-as-Judge.

    Customize: Update the rubric in the prompt below.
    """
    output = run.outputs or {}
    response = output.get("response", "") or output.get("output", "")

    if not response:
        return {"key": "quality", "score": 0.0, "comment": "No output"}

    # Customize this prompt for your use case
    judge_prompt = f"""Evaluate this output on a scale of 1-5.

Output to evaluate:
{response[:2000]}

Rubric:
- 5: Excellent - comprehensive, accurate, well-structured
- 4: Good - mostly complete, minor issues
- 3: Adequate - basic but acceptable
- 2: Poor - significant issues
- 1: Failing - incorrect or unusable

Return JSON: {{"score": 1-5, "reasoning": "brief explanation"}}
"""

    try:
        llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
        result = llm.invoke(judge_prompt)
        parsed = json.loads(result.content)

        return {
            "key": "quality",
            "score": parsed["score"] / 5.0,
            "comment": parsed.get("reasoning", ""),
        }
    except Exception as e:
        return {"key": "quality", "score": 0.5, "comment": f"Error: {e}"}


def relevance_evaluator(run: Run, example: Example) -> dict:
    """Check if output is relevant to input.

    Customize: Update relevance criteria in the prompt.
    """
    inputs = run.inputs or {}
    output = run.outputs or {}

    query = inputs.get("query", "")
    response = output.get("response", "") or output.get("output", "")

    if not response:
        return {"key": "relevance", "score": 0.0, "comment": "No output"}

    judge_prompt = f"""Is this response relevant to the query?

Query: {query}
Response: {response[:1500]}

Score 1-5:
- 5: Directly addresses the query
- 3: Partially relevant
- 1: Off-topic or irrelevant

Return JSON: {{"score": 1-5, "reasoning": "brief explanation"}}
"""

    try:
        llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)
        result = llm.invoke(judge_prompt)
        parsed = json.loads(result.content)

        return {
            "key": "relevance",
            "score": parsed["score"] / 5.0,
            "comment": parsed.get("reasoning", ""),
        }
    except Exception as e:
        return {"key": "relevance", "score": 0.5, "comment": f"Error: {e}"}


# === TIER 3: HUMAN-IN-THE-LOOP ===

def needs_review_evaluator(run: Run, example: Example) -> dict:
    """Flag cases that need human review.

    Customize: Update the flagging heuristics below.
    """
    output = run.outputs or {}
    response = output.get("response", "") or output.get("output", "")

    # Customize these heuristics
    needs_review = (
        len(response) < 50 or              # Too short
        "error" in response.lower() or     # Contains error
        "sorry" in response.lower() or     # Apology (often indicates failure)
        run.error is not None              # Agent crashed
    )

    return {
        "key": "needs_review",
        "score": 0.0 if needs_review else 1.0,
        "comment": "Flagged for human review" if needs_review else "Auto-approved",
    }


# === EVALUATOR COLLECTIONS ===

AUTOMATED = [schema_evaluator, keyword_evaluator, length_evaluator]
LLM_JUDGE = [quality_evaluator, relevance_evaluator]
ALL = AUTOMATED + LLM_JUDGE + [needs_review_evaluator]
