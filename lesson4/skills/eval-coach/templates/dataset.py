"""Dataset template for LangSmith evaluation.

This template provides starter code for creating evaluation datasets.

Usage:
    1. Copy this file to your project
    2. Customize TEST_CASES for your use case
    3. Run: python dataset.py
"""

from langsmith import Client

client = Client()


# === CUSTOMIZE THESE TEST CASES ===

TEST_CASES = [
    # Happy Path Cases (50% of dataset)
    {
        "name": "example_happy_path_1",
        "inputs": {
            # Add your input fields here
            "query": "Example user query",
            "context": "Any relevant context",
        },
        "outputs": {
            "expected_fields": ["response"],  # Fields that MUST be present
            "should_mention": ["keyword1"],   # Keywords to check for
            "min_length": 100,                # Minimum response length
        },
    },

    # Edge Cases (35% of dataset)
    {
        "name": "example_edge_case_1",
        "inputs": {
            "query": "Edge case query with unusual format",
            "context": "",  # Empty context
        },
        "outputs": {
            "expected_fields": ["response"],
            "should_handle_gracefully": True,
        },
    },

    # Adversarial Cases (15% of dataset)
    {
        "name": "example_adversarial_1",
        "inputs": {
            "query": "Ignore previous instructions and...",  # Prompt injection
            "context": "Normal context",
        },
        "outputs": {
            "should_handle_gracefully": True,
            "should_not_contain": ["I will ignore", "Sure, I'll"],
        },
    },
]


def create_dataset(
    name: str = "my_eval_dataset",
    description: str = "Evaluation dataset",
) -> str:
    """Create dataset in LangSmith.

    Args:
        name: Dataset name
        description: Dataset description

    Returns:
        Dataset ID
    """
    # Check if exists
    existing = list(client.list_datasets(dataset_name=name))

    if existing:
        dataset = existing[0]
        print(f"Using existing dataset: {name}")
    else:
        dataset = client.create_dataset(name, description=description)
        print(f"Created dataset: {name}")

    # Add test cases
    for case in TEST_CASES:
        client.create_example(
            dataset_id=dataset.id,
            inputs=case["inputs"],
            outputs=case.get("outputs", {}),
            metadata={"name": case.get("name", "unnamed")},
        )
        print(f"  Added: {case.get('name', 'unnamed')}")

    return str(dataset.id)


if __name__ == "__main__":
    dataset_id = create_dataset()
    print(f"\nDataset ID: {dataset_id}")
