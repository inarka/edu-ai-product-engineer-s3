"""Comparison framework for LangGraph vs Deep Agents.

This module enables side-by-side evaluation of:
1. W3 Research Squad (LangGraph StateGraph)
2. W4 Deep Research Agent (Deep Agents SDK)

The comparison shows:
- Quality scores across test cases
- Latency differences
- Token efficiency
- Approach differences (static vs dynamic planning)

Usage:
    python -m evaluation.compare
"""

import asyncio
import os
import sys
from pathlib import Path

from langsmith import Client
from langsmith.evaluation import evaluate

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from .evaluators import (
    AUTOMATED_EVALUATORS,
    LLM_JUDGE_EVALUATORS,
    PERFORMANCE_EVALUATORS,
)

client = Client()


async def run_comparison(
    dataset_name: str = "research_squad_eval",
    include_llm_judge: bool = True,
) -> dict:
    """Run comparison between LangGraph and Deep Agents.

    Args:
        dataset_name: Name of the LangSmith dataset to use
        include_llm_judge: Whether to include LLM-as-Judge evaluators

    Returns:
        Comparison results with metrics for both approaches
    """
    print("=" * 60)
    print("RESEARCH AGENT COMPARISON")
    print("LangGraph Research Squad vs Deep Research Agent")
    print("=" * 60)

    # Build evaluator list
    evaluators = AUTOMATED_EVALUATORS + PERFORMANCE_EVALUATORS
    if include_llm_judge:
        evaluators += LLM_JUDGE_EVALUATORS

    print(f"\nDataset: {dataset_name}")
    print(f"Evaluators: {len(evaluators)}")
    print(f"  - Automated: {len(AUTOMATED_EVALUATORS)}")
    print(f"  - Performance: {len(PERFORMANCE_EVALUATORS)}")
    if include_llm_judge:
        print(f"  - LLM-as-Judge: {len(LLM_JUDGE_EVALUATORS)}")

    # Import the agents
    print("\nLoading agents...")

    try:
        # Import W3 Research Squad
        from lesson3.workspace.research_squad.graph import create_research_squad_graph

        langgraph_agent = create_research_squad_graph()
        print("  - LangGraph Research Squad: loaded")
    except ImportError:
        print("  - LangGraph Research Squad: NOT FOUND (skipping)")
        langgraph_agent = None

    try:
        # Import W4 Deep Research Agent
        from deep_research_agent import create_deep_research_agent

        deep_agent = create_deep_research_agent()
        print("  - Deep Research Agent: loaded")
    except ImportError:
        print("  - Deep Research Agent: NOT FOUND (skipping)")
        deep_agent = None

    results = {}

    # Evaluate LangGraph Research Squad
    if langgraph_agent:
        print("\n" + "-" * 60)
        print("Evaluating: LangGraph Research Squad (W3)")
        print("-" * 60)

        async def langgraph_invoke(inputs: dict) -> dict:
            """Wrapper for LangGraph agent."""
            config = {"configurable": {"thread_id": f"eval-{inputs.get('linkedin_url', 'test')}"}}
            return await langgraph_agent.ainvoke(inputs, config)

        langgraph_results = evaluate(
            langgraph_invoke,
            data=dataset_name,
            evaluators=evaluators,
            experiment_prefix="langgraph_research_squad",
        )

        results["langgraph"] = langgraph_results
        print(f"Experiment: langgraph_research_squad")

    # Evaluate Deep Research Agent
    if deep_agent:
        print("\n" + "-" * 60)
        print("Evaluating: Deep Research Agent (W4)")
        print("-" * 60)

        async def deep_agent_invoke(inputs: dict) -> dict:
            """Wrapper for Deep Agent."""
            target = inputs.get("linkedin_url", "")
            company = inputs.get("company_name", "")
            return await deep_agent.run(f"Research {target} at {company}")

        deep_agent_results = evaluate(
            deep_agent_invoke,
            data=dataset_name,
            evaluators=evaluators,
            experiment_prefix="deep_research_agent",
        )

        results["deep_agent"] = deep_agent_results
        print(f"Experiment: deep_research_agent")

    return results


def print_comparison_results(results: dict) -> None:
    """Pretty print comparison results.

    Args:
        results: Dict with 'langgraph' and/or 'deep_agent' experiment results
    """
    print("\n" + "=" * 60)
    print("COMPARISON RESULTS")
    print("=" * 60)

    # Extract summary metrics
    def get_summary(experiment_results) -> dict:
        """Extract summary metrics from experiment."""
        if not experiment_results:
            return {}

        summary = {}
        for result in experiment_results:
            for feedback in result.get("feedback", []):
                key = feedback.get("key", "unknown")
                score = feedback.get("score", 0)
                if key not in summary:
                    summary[key] = []
                summary[key].append(score)

        # Average each metric
        return {k: sum(v) / len(v) for k, v in summary.items() if v}

    langgraph_summary = get_summary(results.get("langgraph"))
    deep_agent_summary = get_summary(results.get("deep_agent"))

    # Print comparison table
    all_keys = set(langgraph_summary.keys()) | set(deep_agent_summary.keys())

    print(f"\n{'Metric':<25} {'LangGraph':<15} {'Deep Agent':<15} {'Winner':<10}")
    print("-" * 65)

    for key in sorted(all_keys):
        lg_score = langgraph_summary.get(key, "N/A")
        da_score = deep_agent_summary.get(key, "N/A")

        if isinstance(lg_score, float) and isinstance(da_score, float):
            winner = "LangGraph" if lg_score > da_score else "Deep Agent" if da_score > lg_score else "Tie"
            lg_str = f"{lg_score:.3f}"
            da_str = f"{da_score:.3f}"
        else:
            winner = "-"
            lg_str = str(lg_score)
            da_str = str(da_score)

        print(f"{key:<25} {lg_str:<15} {da_str:<15} {winner:<10}")

    print("-" * 65)

    # Summary
    print("\nKey Differences:")
    print("  - LangGraph: Static graph, parallel execution, predictable")
    print("  - Deep Agent: Dynamic planning, adaptive, context-aware")

    print("\nView detailed results in LangSmith:")
    print(f"  https://smith.langchain.com")


def compare_experiments_in_langsmith(
    experiment_1: str,
    experiment_2: str,
) -> str:
    """Generate LangSmith comparison URL.

    Args:
        experiment_1: First experiment prefix
        experiment_2: Second experiment prefix

    Returns:
        URL for LangSmith comparison view
    """
    # Note: LangSmith comparison requires looking up experiment IDs
    # This is a simplified version that returns the project URL
    project = os.getenv("LANGCHAIN_PROJECT", "default")
    return f"https://smith.langchain.com/o/default/projects/{project}"


async def main():
    """Run the comparison."""
    results = await run_comparison(
        dataset_name="research_squad_eval",
        include_llm_judge=True,
    )

    print_comparison_results(results)


if __name__ == "__main__":
    asyncio.run(main())
