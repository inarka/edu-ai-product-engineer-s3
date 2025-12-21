"""Main runner for the Research Squad demo.

This script demonstrates:
1. Setting up LangSmith tracing for multi-agent observability
2. Running the Research Squad graph
3. Inspecting results and graph execution

Usage:
    python main.py --url "https://linkedin.com/in/someone" --company "Acme Corp"

With debug mode (shows graph visualization):
    python main.py --url "..." --company "..." --debug

Environment variables required:
    OPENAI_API_KEY: For LLM calls
    LANGCHAIN_API_KEY: For LangSmith tracing (optional but recommended)
    ENRICHLAYER_API_KEY: For LinkedIn data (optional, uses mock if not set)
"""

import asyncio
import argparse
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# LangSmith configuration
# Set these before importing LangGraph for tracing to work
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "research-squad-demo")

from research_squad.graph import (
    create_research_squad_graph,
    create_research_squad_graph_with_human_review,
)
from research_squad.state import ResearchState


async def run_research(
    linkedin_url: str,
    company_name: str = "",
    with_human_review: bool = False,
) -> ResearchState:
    """Run the Research Squad on a target.

    Args:
        linkedin_url: LinkedIn profile URL to research
        company_name: Company name (optional, can be extracted from LinkedIn)
        with_human_review: If True, pauses before synthesis for human review

    Returns:
        Final ResearchState with all research results
    """
    # Create the appropriate graph
    if with_human_review:
        graph = create_research_squad_graph_with_human_review()
    else:
        graph = create_research_squad_graph()

    # Initial state
    initial_state: ResearchState = {
        "linkedin_url": linkedin_url,
        "company_name": company_name,
    }

    # Configuration for this run
    # thread_id enables checkpointing and resumption
    config = {
        "configurable": {
            "thread_id": f"research-{linkedin_url}",
        }
    }

    print("\n" + "=" * 60)
    print("RESEARCH SQUAD - Multi-Agent Research System")
    print("=" * 60)
    print(f"\nTarget: {linkedin_url}")
    if company_name:
        print(f"Company: {company_name}")
    print("\nStarting parallel research agents...")
    print("-" * 60)

    # Run the graph
    result = await graph.ainvoke(initial_state, config)

    return result


def print_results(result: ResearchState):
    """Pretty print the research results."""
    print("\n" + "=" * 60)
    print("RESEARCH RESULTS")
    print("=" * 60)

    # LinkedIn data
    linkedin = result.get("linkedin_data")
    if linkedin:
        print("\n--- LinkedIn Profile ---")
        print(f"Name: {linkedin.get('name', 'N/A')}")
        print(f"Title: {linkedin.get('title', 'N/A')}")
        print(f"Company: {linkedin.get('company', 'N/A')}")
        print(f"Location: {linkedin.get('location', 'N/A')}")
    else:
        print("\n--- LinkedIn Profile ---")
        print("No LinkedIn data available")

    # Company data
    company = result.get("company_data")
    if company:
        print("\n--- Company Intelligence ---")
        print(f"Company: {company.get('name', 'N/A')}")
        print(f"Industry: {company.get('industry', 'N/A')}")
        print(f"Size: {company.get('size', 'N/A')}")
    else:
        print("\n--- Company Intelligence ---")
        print("No company data available")

    # News data
    news = result.get("news_data")
    if news:
        print(f"\n--- News ({len(news)} items) ---")
        for item in news[:3]:
            print(f"- {item['title']} ({item['source']})")
    else:
        print("\n--- News ---")
        print("No news data available")

    # Conflicts
    conflicts = result.get("conflicts", [])
    if conflicts:
        print("\n--- Detected Conflicts ---")
        for conflict in conflicts:
            print(f"! {conflict}")

    # Insights
    insights = result.get("insights", [])
    if insights:
        print("\n--- Key Insights ---")
        for insight in insights:
            print(f"* {insight}")

    # Final report
    report = result.get("final_report")
    if report:
        print("\n" + "=" * 60)
        print("FINAL REPORT")
        print("=" * 60)
        print(report)

    print("\n" + "=" * 60)
    print("Research complete!")
    print("=" * 60)


def show_graph_visualization():
    """Display ASCII visualization of the graph structure."""
    from research_squad.graph import research_squad

    print("\n" + "=" * 60)
    print("GRAPH STRUCTURE")
    print("=" * 60)

    # Get the graph's nodes and edges
    print("""
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │   (entry node)  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ LinkedIn Agent  │  │  Company Agent  │  │   News Agent    │
│ (parallel node) │  │ (parallel node) │  │ (parallel node) │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └───────────────────┬┴───────────────────┘
                             ▼
                    ┌─────────────────┐
                    │    Synthesis    │
                    │     Agent       │
                    └────────┬────────┘
                             │
                             ▼
                           END
    """)

    # Also print the graph's actual structure
    print("\nGraph nodes:", list(research_squad.nodes.keys()))


async def demo_human_in_the_loop(linkedin_url: str, company_name: str = ""):
    """Demonstrate the human-in-the-loop workflow.

    This shows how to:
    1. Start research with interrupt
    2. Review intermediate results
    3. Resume execution
    """
    print("\n" + "=" * 60)
    print("HUMAN-IN-THE-LOOP DEMO")
    print("=" * 60)

    graph = create_research_squad_graph_with_human_review()

    initial_state: ResearchState = {
        "linkedin_url": linkedin_url,
        "company_name": company_name,
    }

    config = {
        "configurable": {
            "thread_id": f"research-hitl-{linkedin_url}",
        }
    }

    print("\nPhase 1: Running research agents (will pause before synthesis)...")

    # This will pause before synthesis due to interrupt_before
    result = await graph.ainvoke(initial_state, config)

    # Check current state
    state = await graph.aget_state(config)

    if state.next:
        print(f"\n--- Paused before: {state.next} ---")
        print("\nIntermediate results available for review:")

        if result.get("linkedin_data"):
            print(f"  - LinkedIn: {result['linkedin_data'].get('name', 'N/A')}")
        if result.get("company_data"):
            print(f"  - Company: {result['company_data'].get('name', 'N/A')}")
        if result.get("news_data"):
            print(f"  - News: {len(result.get('news_data', []))} items")

        # Simulate human approval
        print("\n[Human reviews and approves...]")
        input("Press Enter to continue to synthesis...")

        # Resume execution
        print("\nPhase 2: Resuming execution...")
        result = await graph.ainvoke(None, config)

    return result


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Research Squad - Multi-Agent Research System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py --url "https://linkedin.com/in/someone"
    python main.py --url "..." --company "Acme Corp" --debug
    python main.py --url "..." --human-review
        """
    )

    parser.add_argument(
        "--url",
        type=str,
        default="https://linkedin.com/in/demo-user",
        help="LinkedIn profile URL to research"
    )

    parser.add_argument(
        "--company",
        type=str,
        default="",
        help="Company name (optional, can be extracted from LinkedIn)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show graph visualization"
    )

    parser.add_argument(
        "--human-review",
        action="store_true",
        help="Enable human-in-the-loop before synthesis"
    )

    args = parser.parse_args()

    # Check for API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY not set. LLM calls will fail.")

    if not os.getenv("LANGCHAIN_API_KEY"):
        print("NOTE: LANGCHAIN_API_KEY not set. LangSmith tracing disabled.")
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

    # Show graph if debug
    if args.debug:
        show_graph_visualization()

    # Run the appropriate mode
    if args.human_review:
        result = asyncio.run(demo_human_in_the_loop(args.url, args.company))
    else:
        result = asyncio.run(run_research(args.url, args.company))

    print_results(result)

    # Print LangSmith link if available
    if os.getenv("LANGCHAIN_API_KEY"):
        print(f"\nView trace in LangSmith: https://smith.langchain.com")
        print(f"Project: {os.getenv('LANGCHAIN_PROJECT', 'research-squad-demo')}")


if __name__ == "__main__":
    main()
