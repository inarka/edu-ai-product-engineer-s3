"""Unit tests for dataset creation.

Tests the dataset module structure and validation WITHOUT hitting LangSmith API.
These tests do NOT require API keys and run fast.

Run with:
    pytest tests/test_dataset.py -v
"""

import pytest
from unittest.mock import MagicMock, patch

# Import dataset module
from evaluation.dataset import (
    SAMPLE_TEST_CASES,
    TestCase,
)


# === TEST CASE STRUCTURE TESTS ===

class TestSampleTestCasesStructure:
    """Tests for SAMPLE_TEST_CASES structure."""

    def test_sample_test_cases_is_list(self):
        """SAMPLE_TEST_CASES is a non-empty list"""
        assert isinstance(SAMPLE_TEST_CASES, list)
        assert len(SAMPLE_TEST_CASES) > 0

    def test_all_cases_have_name(self):
        """Each test case has a 'name' field"""
        for case in SAMPLE_TEST_CASES:
            assert "name" in case, f"Missing name in case: {case}"
            assert isinstance(case["name"], str)

    def test_all_cases_have_inputs(self):
        """Each test case has 'inputs' dict"""
        for case in SAMPLE_TEST_CASES:
            assert "inputs" in case, f"Missing inputs in case: {case['name']}"
            assert isinstance(case["inputs"], dict)

    def test_all_cases_have_outputs(self):
        """Each test case has 'outputs' dict"""
        for case in SAMPLE_TEST_CASES:
            assert "outputs" in case, f"Missing outputs in case: {case['name']}"
            assert isinstance(case["outputs"], dict)


class TestTestCaseDistribution:
    """Tests for test case distribution (50-35-15 rule)."""

    def test_happy_path_cases_count(self):
        """At least 5 happy path cases (50% of ~11)"""
        happy_path = [
            c for c in SAMPLE_TEST_CASES
            if not c["outputs"].get("should_handle_gracefully")
            and "expected_fields" in c["outputs"]
            and len(c["outputs"].get("expected_fields", [])) >= 2
        ]
        assert len(happy_path) >= 5

    def test_edge_cases_exist(self):
        """Edge cases exist (empty company, long URL, non-English, acquired)"""
        edge_case_names = [
            "no_company_provided",
            "very_long_url",
            "non_english_company",
            "acquired_company",
        ]
        actual_names = [c["name"] for c in SAMPLE_TEST_CASES]

        found = [name for name in edge_case_names if name in actual_names]
        assert len(found) >= 3, f"Expected edge cases, found: {found}"

    def test_adversarial_cases_exist(self):
        """At least 2 adversarial cases (should_handle_gracefully=True)"""
        adversarial = [
            c for c in SAMPLE_TEST_CASES
            if c["outputs"].get("should_handle_gracefully", False)
        ]
        assert len(adversarial) >= 2


class TestTestCaseInputs:
    """Tests for test case input fields."""

    def test_inputs_have_linkedin_url_or_company(self):
        """Each case has at least linkedin_url or company_name"""
        for case in SAMPLE_TEST_CASES:
            inputs = case["inputs"]
            has_url = "linkedin_url" in inputs and inputs["linkedin_url"]
            has_company = "company_name" in inputs
            assert has_url or has_company, f"Missing input in: {case['name']}"

    def test_linkedin_urls_are_valid_format(self):
        """LinkedIn URLs start with https://linkedin.com or are invalid test cases"""
        for case in SAMPLE_TEST_CASES:
            url = case["inputs"].get("linkedin_url", "")
            # Either valid LinkedIn URL or intentionally invalid (adversarial)
            is_valid = url.startswith("https://linkedin.com")
            is_adversarial = case["outputs"].get("should_handle_gracefully", False)

            assert is_valid or is_adversarial, f"Invalid URL in non-adversarial case: {case['name']}"


class TestTestCaseOutputs:
    """Tests for test case output/validation fields."""

    def test_happy_path_has_expected_fields(self):
        """Happy path cases define expected_fields"""
        happy_path_names = [
            "tech_ceo_microsoft",
            "tech_ceo_nvidia",
            "startup_founder",
            "sales_leader",
            "engineering_manager",
        ]

        for case in SAMPLE_TEST_CASES:
            if case["name"] in happy_path_names:
                assert "expected_fields" in case["outputs"], f"Missing expected_fields in: {case['name']}"

    def test_adversarial_has_graceful_handling_flag(self):
        """Adversarial cases have should_handle_gracefully=True"""
        adversarial_names = [
            "invalid_linkedin_url",
            "nonexistent_profile",
        ]

        for case in SAMPLE_TEST_CASES:
            if case["name"] in adversarial_names:
                assert case["outputs"].get("should_handle_gracefully") is True, \
                    f"Missing should_handle_gracefully in: {case['name']}"

    def test_min_report_length_is_positive(self):
        """min_report_length values are positive integers"""
        for case in SAMPLE_TEST_CASES:
            min_len = case["outputs"].get("min_report_length")
            if min_len is not None:
                assert isinstance(min_len, int), f"min_report_length not int in: {case['name']}"
                assert min_len > 0, f"min_report_length not positive in: {case['name']}"


class TestTestCaseNames:
    """Tests for test case naming conventions."""

    def test_names_are_unique(self):
        """All test case names are unique"""
        names = [c["name"] for c in SAMPLE_TEST_CASES]
        assert len(names) == len(set(names)), "Duplicate test case names found"

    def test_names_use_snake_case(self):
        """Names follow snake_case convention"""
        for case in SAMPLE_TEST_CASES:
            name = case["name"]
            # Snake case: lowercase letters, numbers, underscores
            assert name == name.lower(), f"Name not lowercase: {name}"
            assert " " not in name, f"Name has spaces: {name}"


# === MOCK TESTS FOR LANGSMITH FUNCTIONS ===

class TestDatasetCreation:
    """Tests for dataset creation functions (mocked LangSmith)."""

    @patch("evaluation.dataset.client")
    def test_create_dataset_uses_sample_cases_by_default(self, mock_client):
        """create_research_dataset uses SAMPLE_TEST_CASES when no cases provided"""
        from evaluation.dataset import create_research_dataset

        mock_dataset = MagicMock()
        mock_dataset.id = "test-id"
        mock_client.list_datasets.return_value = []
        mock_client.create_dataset.return_value = mock_dataset

        create_research_dataset()

        # Should create examples for all sample cases
        assert mock_client.create_example.call_count == len(SAMPLE_TEST_CASES)

    @patch("evaluation.dataset.client")
    def test_create_dataset_uses_existing_if_found(self, mock_client):
        """create_research_dataset reuses existing dataset"""
        from evaluation.dataset import create_research_dataset

        mock_dataset = MagicMock()
        mock_dataset.id = "existing-id"
        mock_client.list_datasets.return_value = [mock_dataset]

        result = create_research_dataset()

        # Should NOT create a new dataset
        mock_client.create_dataset.assert_not_called()

    @patch("evaluation.dataset.client")
    def test_add_test_case_raises_if_dataset_not_found(self, mock_client):
        """add_test_case raises ValueError if dataset doesn't exist"""
        from evaluation.dataset import add_test_case

        mock_client.list_datasets.return_value = []

        with pytest.raises(ValueError, match="not found"):
            add_test_case(
                dataset_name="nonexistent",
                inputs={"linkedin_url": "test"},
                outputs={},
            )
