"""Dataset creation for Research Squad evaluation.

This module handles:
1. Creating evaluation datasets in LangSmith
2. Adding diverse test cases (happy path, edge cases, adversarial)
3. Dataset versioning and management

Best Practices (from Anthropic):
- Start with 20 high-quality test cases, not 1000 noisy ones
- Include: 50% happy path, 35% edge cases, 15% adversarial
- Focus on realistic distribution matching production
"""

import os
from typing import TypedDict

from langsmith import Client

# Initialize LangSmith client
client = Client()


class TestCase(TypedDict, total=False):
    """Structure for a single test case."""
    # Inputs
    linkedin_url: str
    company_name: str

    # Expected outputs (for validation)
    expected_fields: list[str]  # Fields that MUST be present
    should_mention: list[str]   # Keywords that SHOULD appear
    min_report_length: int      # Minimum length for quality
    should_handle_gracefully: bool  # For error cases


# === SAMPLE TEST CASES ===
# These are used for the workshop demo

SAMPLE_TEST_CASES = [
    # Happy Path (50%)
    {
        "name": "tech_ceo_microsoft",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/satya-nadella",
            "company_name": "Microsoft",
        },
        "outputs": {
            "expected_fields": ["linkedin_data", "company_data", "final_report"],
            "should_mention": ["CEO", "Microsoft", "AI", "cloud"],
            "min_report_length": 500,
        },
    },
    {
        "name": "tech_ceo_nvidia",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/jensen-huang",
            "company_name": "NVIDIA",
        },
        "outputs": {
            "expected_fields": ["linkedin_data", "company_data", "final_report"],
            "should_mention": ["CEO", "NVIDIA", "GPU", "AI"],
            "min_report_length": 500,
        },
    },
    {
        "name": "startup_founder",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/demo-founder",
            "company_name": "AI Startup",
        },
        "outputs": {
            "expected_fields": ["linkedin_data", "final_report"],
            "should_mention": ["founder", "startup"],
            "min_report_length": 300,
        },
    },
    {
        "name": "sales_leader",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/demo-vp-sales",
            "company_name": "Enterprise Corp",
        },
        "outputs": {
            "expected_fields": ["linkedin_data", "company_data", "final_report"],
            "should_mention": ["sales", "revenue", "enterprise"],
            "min_report_length": 400,
        },
    },
    {
        "name": "engineering_manager",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/demo-eng-manager",
            "company_name": "Tech Company",
        },
        "outputs": {
            "expected_fields": ["linkedin_data", "final_report"],
            "should_mention": ["engineering", "team", "technical"],
            "min_report_length": 350,
        },
    },

    # Edge Cases (35%)
    {
        "name": "no_company_provided",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/solo-consultant",
            "company_name": "",  # Empty company
        },
        "outputs": {
            "expected_fields": ["linkedin_data", "final_report"],
            "should_mention": ["consultant"],
            "min_report_length": 200,
        },
    },
    {
        "name": "very_long_url",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/person-with-very-long-profile-url-name-here",
            "company_name": "Company",
        },
        "outputs": {
            "expected_fields": ["final_report"],
            "min_report_length": 100,
        },
    },
    {
        "name": "non_english_company",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/international-exec",
            "company_name": "Deutsche Telekom",
        },
        "outputs": {
            "expected_fields": ["linkedin_data", "company_data", "final_report"],
            "should_mention": ["Deutsche", "Telekom"],
            "min_report_length": 300,
        },
    },
    {
        "name": "acquired_company",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/former-startup-founder",
            "company_name": "Acquired Startup (now part of BigCorp)",
        },
        "outputs": {
            "expected_fields": ["final_report"],
            "should_mention": ["acquired", "acquisition"],
            "min_report_length": 250,
        },
    },

    # Adversarial Cases (15%)
    {
        "name": "invalid_linkedin_url",
        "inputs": {
            "linkedin_url": "not-a-valid-url",
            "company_name": "Company",
        },
        "outputs": {
            "should_handle_gracefully": True,
        },
    },
    {
        "name": "nonexistent_profile",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/this-profile-does-not-exist-12345",
            "company_name": "Unknown Corp",
        },
        "outputs": {
            "should_handle_gracefully": True,
        },
    },
    {
        "name": "adversarial_company_mismatch",
        "inputs": {
            "linkedin_url": "https://linkedin.com/in/demo-founder",
            "company_name": "Wrong Company Inc",  # Deliberately wrong
        },
        "outputs": {
            "should_flag_mismatch": True,
            "expected_behavior": "Agent should notice LinkedIn shows different company",
            "should_handle_gracefully": True,
        },
    },
]


def create_research_dataset(
    dataset_name: str = "research_squad_eval",
    description: str = "Evaluation dataset for Research Squad comparison",
    test_cases: list[dict] | None = None,
) -> str:
    """Create or update an evaluation dataset in LangSmith.

    Args:
        dataset_name: Name for the dataset
        description: Description for the dataset
        test_cases: List of test cases (uses SAMPLE_TEST_CASES if None)

    Returns:
        Dataset ID
    """
    if test_cases is None:
        test_cases = SAMPLE_TEST_CASES

    # Check if dataset exists
    existing = list(client.list_datasets(dataset_name=dataset_name))

    if existing:
        dataset = existing[0]
        print(f"Using existing dataset: {dataset_name} (ID: {dataset.id})")
    else:
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=description,
        )
        print(f"Created new dataset: {dataset_name} (ID: {dataset.id})")

    # Add test cases
    for case in test_cases:
        client.create_example(
            dataset_id=dataset.id,
            inputs=case["inputs"],
            outputs=case.get("outputs", {}),
            metadata={"name": case.get("name", "unnamed")},
        )
        print(f"  Added: {case.get('name', 'unnamed')}")

    print(f"\nDataset ready with {len(test_cases)} test cases")
    return str(dataset.id)


def add_test_case(
    dataset_name: str,
    inputs: dict,
    outputs: dict,
    name: str = "",
) -> None:
    """Add a single test case to an existing dataset.

    Args:
        dataset_name: Name of the dataset
        inputs: Input dict (linkedin_url, company_name)
        outputs: Expected outputs (expected_fields, should_mention, etc.)
        name: Optional name for the test case
    """
    datasets = list(client.list_datasets(dataset_name=dataset_name))

    if not datasets:
        raise ValueError(f"Dataset '{dataset_name}' not found")

    dataset = datasets[0]

    client.create_example(
        dataset_id=dataset.id,
        inputs=inputs,
        outputs=outputs,
        metadata={"name": name} if name else None,
    )

    print(f"Added test case: {name or 'unnamed'} to {dataset_name}")


def list_datasets() -> list[dict]:
    """List all available evaluation datasets."""
    datasets = list(client.list_datasets())
    return [{"name": d.name, "id": str(d.id)} for d in datasets]


if __name__ == "__main__":
    # Quick test: create the sample dataset
    print("Creating evaluation dataset...")
    dataset_id = create_research_dataset()
    print(f"\nDataset ID: {dataset_id}")
    print("\nAvailable datasets:")
    for ds in list_datasets():
        print(f"  - {ds['name']} ({ds['id']})")
