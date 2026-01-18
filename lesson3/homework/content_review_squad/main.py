"""Main runner for the Content Review Squad homework.

Usage:
    python main.py

With human-in-the-loop demo:
    python main.py --interactive
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

    # Важно инициализировать агрегаты, если у тебя reducers
    state: ReviewState = {
        "reviews": reviews,
        "categories": {},
        "bug_results": [],
        "feature_results": [],
        "praise_results": [],
        "pending_feature_specs": {},
        "feature_decisions": {},  # можно оставить, даже если approval_node сам пишет решения
    }

    # 1) первый прогон до первой паузы (или до конца)
    result = await graph.ainvoke(state, config=config)

    # 2) human-in-the-loop цикл (обрабатываем все interrupts одновременно)
    # Когда несколько feature requests обрабатываются параллельно, каждый вызывает interrupt()
    # Нужно обработать все interrupts одновременно через interrupt ID
    while "__interrupt__" in result and result["__interrupt__"]:
        interrupts = result["__interrupt__"]
        
        print(f"\nFound {len(interrupts)} feature request(s) pending approval...")
        
        # Собираем решения для всех interrupts
        resume_values = {}
        
        for idx, intr in enumerate(interrupts, 1):
            # Получаем payload из interrupt
            # interrupt может быть объектом с .value или dict
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
            
            # Сохраняем решение с interrupt ID как ключом
            # interrupt.id - уникальный идентификатор interrupt'а
            # Если id недоступен, используем review_id как fallback
            interrupt_id = getattr(intr, "id", None) or review_id
            resume_values[interrupt_id] = {"approved": approved, "notes": notes}
        
        # Резюмим все interrupts сразу через Command(resume={interrupt_id: decision})
        # Формат: {interrupt_id: {"approved": bool, "notes": str}}
        result = await graph.ainvoke(Command(resume=resume_values), config=config)

    # 3) готово — result уже содержит финальный state
    return result


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
        print("\nView trace: https://smith.langchain.com")
        print(f"Project: {os.getenv('LANGCHAIN_PROJECT', 'content-review-squad')}")


if __name__ == "__main__":
    main()
