"""
Test script to verify voice agent setup.

Run: python voice_agents/test_setup.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


def check_api_keys():
    """Check that required API keys are set."""
    checks = []

    # OpenAI
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key and openai_key.startswith("sk-"):
        checks.append(("OpenAI API Key", True, "Found"))
    else:
        checks.append(("OpenAI API Key", False, "Missing or invalid"))

    # LiveKit
    livekit_url = os.getenv("LIVEKIT_URL", "")
    livekit_api = os.getenv("LIVEKIT_API_KEY", "")
    livekit_secret = os.getenv("LIVEKIT_API_SECRET", "")

    if livekit_url and livekit_api and livekit_secret:
        checks.append(("LiveKit Credentials", True, "All three found"))
    else:
        missing = []
        if not livekit_url:
            missing.append("URL")
        if not livekit_api:
            missing.append("API_KEY")
        if not livekit_secret:
            missing.append("API_SECRET")
        checks.append(("LiveKit Credentials", False, f"Missing: {', '.join(missing)}"))

    # Optional: ElevenLabs
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
    if elevenlabs_key:
        checks.append(("ElevenLabs (optional)", True, "Found"))
    else:
        checks.append(("ElevenLabs (optional)", None, "Not set (optional)"))

    return checks


def check_packages():
    """Check that required packages are installed."""
    packages = [
        ("openai", "openai"),
        ("livekit", "livekit"),
        ("livekit.agents", "livekit-agents"),
        ("dotenv", "python-dotenv"),
    ]

    checks = []
    for import_name, package_name in packages:
        try:
            __import__(import_name)
            checks.append((package_name, True, "Installed"))
        except ImportError:
            checks.append((package_name, False, "Not installed"))

    return checks


def print_results(title: str, checks: list):
    """Print check results in a formatted table."""
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print('=' * 50)

    for name, status, message in checks:
        if status is True:
            symbol = "[OK]"
        elif status is False:
            symbol = "[X]"
        else:
            symbol = "[~]"

        print(f"  {symbol} {name}: {message}")


def main():
    print("\nVoice Agent Setup Verification")
    print("=" * 50)

    # Check packages
    package_checks = check_packages()
    print_results("Package Dependencies", package_checks)

    # Check API keys
    api_checks = check_api_keys()
    print_results("API Keys", api_checks)

    # Summary
    print("\n" + "=" * 50)
    print(" Summary")
    print("=" * 50)

    all_required_ok = all(
        status is True
        for name, status, _ in package_checks + api_checks
        if "optional" not in name.lower()
    )

    if all_required_ok:
        print("  All required dependencies and keys are configured.")
        print("  You're ready to run the voice agent examples!")
        print("\n  Try: python voice_agents/livekit_realtime.py")
    else:
        print("  Some required items are missing.")
        print("  Please review the checklist above and fix any [X] items.")
        print("\n  Quick fixes:")
        print("  1. Copy .env.example to .env and fill in your keys")
        print("  2. Run: pip install -r requirements.txt")

    print()


if __name__ == "__main__":
    main()
