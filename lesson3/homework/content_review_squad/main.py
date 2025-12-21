"""Main runner for the Content Review Squad homework.

Usage:
    python main.py

With human-in-the-loop demo:
    python main.py --interactive
"""

import asyncio
import argparse
import os
from dotenv import load_dotenv

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

    # TODO: Create the graph
    # graph = create_content_review_squad()

    # TODO: Process reviews
    # Option 1: Process one at a time
    # for review in reviews:
    #     state = {"current_review": review, ...}
    #     result = await graph.ainvoke(state, config)
    #
    # Option 2: Process batch (more complex)
    # state = {"reviews": reviews, ...}
    # result = await graph.ainvoke(state, config)

    # TODO: Handle human-in-the-loop for feature requests
    # If using interrupt_before/after, you'll need to:
    # 1. Check if graph is paused (state.next is not empty)
    # 2. Show the pending feature spec
    # 3. Get human approval
    # 4. Resume with await graph.ainvoke(None, config)

    raise NotImplementedError("Implement the review processing!")


def print_results(state: ReviewState):
    """Pretty print the processing results."""
    print("\n" + "=" * 60)
    print("PROCESSING RESULTS")
    print("=" * 60)

    # TODO: Print results from state
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
    args = parser.parse_args()

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set. Add it to your .env file.")
        return

    # Process reviews
    result = asyncio.run(process_reviews(SAMPLE_REVIEWS, args.interactive))
    print_results(result)

    # LangSmith trace info
    if os.getenv("LANGCHAIN_API_KEY"):
        print(f"\nView trace: https://smith.langchain.com")
        print(f"Project: {os.getenv('LANGCHAIN_PROJECT', 'content-review-squad')}")


if __name__ == "__main__":
    main()
