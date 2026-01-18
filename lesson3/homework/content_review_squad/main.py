"""Main runner for the Content Review Squad homework.

Usage:
    python main.py                          # Run with sample reviews
    python main.py --interactive             # Enable human-in-the-loop
    python main.py --visualize ascii         # Show graph in ASCII format
    python main.py --visualize mermaid       # Show Mermaid diagram
    python main.py --visualize png           # Generate PNG (requires grandalf)
    python main.py --visualize png --save-graph graph.png  # Save PNG to file
"""

import asyncio
import argparse
import os
import uuid

from dotenv import load_dotenv
from langgraph.types import Command

# Load environment variables
load_dotenv()

# LangSmith configuration
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "content-review-squad")

from .graph import create_content_review_squad
from .state import ReviewState, Review


# Sample reviews for testing
SAMPLE_REVIEWS: list[Review] = [
    {
        "id": 1,
        "text": "App crashes every time I try to export to PDF. This is really frustrating!",
        "rating": 1,
    },
    {
        "id": 2,
        "text": "Would love to see a dark mode option. My eyes hurt using the app at night.",
        "rating": 4,
    },
    {
        "id": 3,
        "text": "Absolutely love this app! It's changed how I manage my projects. Best purchase ever!",
        "rating": 5,
    },
    {
        "id": 4,
        "text": "The login button doesn't work on Safari browser. Please fix ASAP.",
        "rating": 2,
    },
    {
        "id": 5,
        "text": "Can you add integration with Notion? That would be amazing for my workflow.",
        "rating": 4,
    },
]


async def process_reviews(reviews: list[Review], interactive: bool = False) -> ReviewState:
    """Process a batch of reviews through the Content Review Squad.

    TODO: Implement the review processing loop.

    For this homework, you might want to:
    1. Process reviews one at a time (simpler)
    2. Or process all at once and handle routing (more complex)

    Args:
        reviews: List of reviews to process
        interactive: If True, pause for human review on feature requests

    Returns:
        Final state with all results
    """
    print("\n" + "=" * 60)
    print("CONTENT REVIEW SQUAD")
    print("=" * 60)
    print(f"\nProcessing {len(reviews)} reviews...")

    graph = create_content_review_squad()

    config = {
        "configurable": {
            "thread_id": f"hw3-{uuid.uuid4()}",
            "max_concurrency": 10,
        }
    }

    # Important: initialize aggregates if using reducers
    state: ReviewState = {
        "reviews": reviews,
        "categories": {},
        "bug_results": [],
        "feature_results": [],
        "praise_results": [],
        "pending_feature_specs": {},
        "feature_decisions": {},  # Can be kept even if approval_node writes decisions itself
    }

    # Step 1: Initial run until first pause (or completion)
    result = await graph.ainvoke(state, config=config)

    # Step 2: Human-in-the-loop cycle (process all interrupts simultaneously)
    # When multiple feature requests are processed in parallel, each calls interrupt()
    # Need to handle all interrupts simultaneously via interrupt ID
    while "__interrupt__" in result and result["__interrupt__"]:
        interrupts = result["__interrupt__"]
        
        print(f"\nFound {len(interrupts)} feature request(s) pending approval...")
        
        # Collect decisions for all interrupts
        resume_values = {}
        
        for idx, intr in enumerate(interrupts, 1):
            # Get payload from interrupt
            # interrupt can be an object with .value or a dict
            payload = getattr(intr, "value", None) or (intr if isinstance(intr, dict) else {})
            
            review_id = payload.get("review_id")
            feature_name = payload.get("feature_name", "(unknown)")
            complexity = payload.get("complexity", "(unknown)")
            priority = payload.get("priority", "(unknown)")
            markdown = payload.get("markdown", "")
            
            print("\n" + "-" * 60)
            print(f"HUMAN REVIEW #{idx}/{len(interrupts)} (review #{review_id})")
            print(f"Feature: {feature_name}")
            print(f"Complexity: {complexity} | Priority: {priority}")
            print("-" * 60)
            print(markdown)
            print("-" * 60)
            
            if interactive:
                ans = input("Approve? (y/n): ").strip().lower()
                approved = ans in {"y", "yes"}
                notes = input("Notes (optional): ").strip()
            else:
                approved = True
                notes = "Auto-approved (interactive=False)."
            
            # Save decision with interrupt ID as key
            # interrupt.id is the unique identifier for the interrupt
            # If id is unavailable, use review_id as fallback
            interrupt_id = getattr(intr, "id", None) or review_id
            resume_values[interrupt_id] = {"approved": approved, "notes": notes}
        
        # Resume all interrupts at once via Command(resume={interrupt_id: decision})
        # Format: {interrupt_id: {"approved": bool, "notes": str}}
        result = await graph.ainvoke(Command(resume=resume_values), config=config)

    # Step 3: Done - result already contains final state
    return result


def visualize_graph(output_format: str = "ascii", output_file: str | None = None):
    """Visualize the Content Review Squad graph.
    
    Args:
        output_format: Output format - "ascii", "mermaid", or "png"
        output_file: Optional file path to save output (for PNG or Mermaid)
    """
    graph = create_content_review_squad()
    graph_obj = graph.get_graph()
    
    if output_format == "ascii":
        print("\n" + "=" * 60)
        print("GRAPH VISUALIZATION (ASCII)")
        print("=" * 60)
        print(graph_obj.draw_ascii())
    elif output_format == "mermaid":
        mermaid_text = graph_obj.draw_mermaid()
        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(mermaid_text)
            print(f"\nMermaid diagram saved to {output_file}")
        else:
            print("\n" + "=" * 60)
            print("GRAPH VISUALIZATION (Mermaid)")
            print("=" * 60)
            print(mermaid_text)
    elif output_format == "png":
        try:
            png_data = graph_obj.draw_mermaid_png()
            output_path = output_file or "content_review_squad_graph.png"
            with open(output_path, "wb") as f:
                f.write(png_data)
            print(f"\nGraph PNG saved to {output_path}")
        except Exception as e:
            print(f"\nERROR: Failed to generate PNG: {e}")
            print("Install dependencies: pip install grandalf")
            print("Or use ASCII format: python main.py --visualize ascii")


def print_results(state: ReviewState):
    """Pretty print the processing results."""
    print("\n" + "=" * 60)
    print("PROCESSING RESULTS")
    print("=" * 60)

    # Print results from state
    # - Bug reports created
    # - Feature specs (approved/pending)
    # - Testimonials logged
    # - Summary statistics

    summary = state.get("summary_report", "No summary available")
    print(summary)


def main():
    parser = argparse.ArgumentParser(description="Content Review Squad")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable human-in-the-loop for feature requests"
    )
    parser.add_argument(
        "--visualize",
        type=str,
        choices=["ascii", "mermaid", "png"],
        help="Visualize the graph (ascii, mermaid, or png)"
    )
    parser.add_argument(
        "--save-graph",
        type=str,
        help="Save graph visualization to file (for PNG or Mermaid format)"
    )
    args = parser.parse_args()

    # If visualize flag is set, show graph and exit
    if args.visualize:
        visualize_graph(args.visualize, args.save_graph)
        return

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set. Add it to your .env file.")
        return

    # Process reviews
    result = asyncio.run(process_reviews(SAMPLE_REVIEWS, args.interactive))
    print_results(result)

    # LangSmith trace info
    if os.getenv("LANGCHAIN_API_KEY"):
        print("\nView trace: https://smith.langchain.com")
        print(f"Project: {os.getenv('LANGCHAIN_PROJECT', 'content-review-squad')}")


if __name__ == "__main__":
    main()
