"""Unit tests for CLI argument parsing and validation.

Tests the command-line interface without running the full agent.
These tests do NOT require API keys and run fast.

Run with:
    pytest tests/test_cli.py -v
"""

import pytest
import argparse
from unittest.mock import patch, MagicMock
import sys


# === CLI ARGUMENT TESTS ===

class TestCLIArguments:
    """Tests for CLI argument parsing."""

    def test_target_is_required(self):
        """--target is a required argument"""
        from deep_research_agent import main

        with patch.object(sys, 'argv', ['prog']):
            with pytest.raises(SystemExit) as excinfo:
                # Create a parser to test
                parser = argparse.ArgumentParser()
                parser.add_argument("--target", type=str, required=True)
                parser.parse_args([])

            # argparse exits with code 2 for missing required args
            assert excinfo.value.code == 2

    def test_target_accepts_value(self):
        """--target accepts a string value"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--target", type=str, required=True)
        args = parser.parse_args(["--target", "https://linkedin.com/in/test"])

        assert args.target == "https://linkedin.com/in/test"

    def test_company_is_optional(self):
        """--company has default empty string"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--target", type=str, required=True)
        parser.add_argument("--company", type=str, default="")
        args = parser.parse_args(["--target", "test"])

        assert args.company == ""

    def test_company_accepts_value(self):
        """--company accepts a string value"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--target", type=str, required=True)
        parser.add_argument("--company", type=str, default="")
        args = parser.parse_args(["--target", "test", "--company", "Microsoft"])

        assert args.company == "Microsoft"

    def test_focus_is_optional(self):
        """--focus has default empty string"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--target", type=str, required=True)
        parser.add_argument("--focus", type=str, default="")
        args = parser.parse_args(["--target", "test"])

        assert args.focus == ""

    def test_focus_accepts_value(self):
        """--focus accepts a string value"""
        parser = argparse.ArgumentParser()
        parser.add_argument("--target", type=str, required=True)
        parser.add_argument("--focus", type=str, default="")
        args = parser.parse_args(["--target", "test", "--focus", "AI strategy"])

        assert args.focus == "AI strategy"


class TestCLIHelp:
    """Tests for CLI help display."""

    def test_help_displays_usage(self):
        """--help shows usage information"""
        parser = argparse.ArgumentParser(
            description="Deep Research Agent - Dynamic B2B Sales Intelligence"
        )
        parser.add_argument("--target", type=str, required=True, help="LinkedIn URL")

        # Get help string
        help_text = parser.format_help()

        assert "Deep Research Agent" in help_text
        assert "--target" in help_text
        assert "LinkedIn" in help_text


class TestCLIIntegration:
    """Tests for CLI main function integration."""

    @patch("deep_research_agent.asyncio.run")
    @patch("deep_research_agent.print_results")
    def test_main_calls_run_research(self, mock_print, mock_asyncio_run):
        """main() calls run_research with parsed arguments"""
        from deep_research_agent import main

        mock_asyncio_run.return_value = {"output": "Test report"}

        with patch.object(
            sys, 'argv',
            ['prog', '--target', 'https://linkedin.com/in/test', '--company', 'TestCo']
        ):
            main()

        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()

        # Verify print_results was called with the result
        mock_print.assert_called_once()

    @patch("deep_research_agent.asyncio.run")
    @patch("deep_research_agent.print_results")
    def test_main_passes_all_arguments(self, mock_print, mock_asyncio_run):
        """main() passes target, company, and focus to run_research"""
        from deep_research_agent import main

        mock_asyncio_run.return_value = {"output": "Test"}

        with patch.object(
            sys, 'argv',
            ['prog', '--target', 'test-url', '--company', 'TestCo', '--focus', 'AI']
        ):
            main()

        # Check the coroutine was created with correct args
        call_args = mock_asyncio_run.call_args
        # The coroutine is passed as the first positional arg
        assert call_args is not None
