"""Setup verification script for Workshop 3.

Run this script to verify your environment is correctly configured
before running the Research Squad demo.

Usage:
    python check_setup.py
"""

import os
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def check_env_var(name: str, required: bool = True, secret: bool = True) -> bool:
    """Check if an environment variable is set."""
    value = os.getenv(name)

    if value:
        if secret:
            display = value[:8] + "..." if len(value) > 8 else "***"
        else:
            display = value
        print(f"  [OK] {name} = {display}")
        return True
    else:
        status = "[MISSING]" if required else "[OPTIONAL]"
        print(f"  {status} {name}")
        return not required


def check_langsmith_connection() -> bool:
    """Try to connect to LangSmith."""
    try:
        from langsmith import Client

        api_key = os.getenv("LANGCHAIN_API_KEY")
        if not api_key:
            return False

        client = Client(api_key=api_key)
        # Try to list projects (lightweight API call)
        list(client.list_projects(limit=1))
        print("  [OK] LangSmith connection successful")
        return True
    except Exception as e:
        print(f"  [ERROR] LangSmith connection failed: {e}")
        return False


def check_openai_connection() -> bool:
    """Try to connect to OpenAI."""
    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False

        client = OpenAI(api_key=api_key)
        # List available models (lightweight API call)
        client.models.list()
        print("  [OK] OpenAI connection successful")
        return True
    except Exception as e:
        print(f"  [ERROR] OpenAI connection failed: {e}")
        return False


def check_langgraph_imports() -> bool:
    """Verify LangGraph imports work."""
    try:
        from langgraph.graph import StateGraph, START, END
        from langgraph.checkpoint.memory import MemorySaver
        print("  [OK] LangGraph imports successful")
        return True
    except ImportError as e:
        print(f"  [ERROR] LangGraph import failed: {e}")
        return False


def check_research_squad_imports() -> bool:
    """Verify Research Squad imports work."""
    try:
        from research_squad.graph import research_squad, create_research_squad_graph
        from research_squad.state import ResearchState
        print("  [OK] Research Squad imports successful")
        print(f"       Graph nodes: {list(research_squad.nodes.keys())}")
        return True
    except ImportError as e:
        print(f"  [ERROR] Research Squad import failed: {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("Workshop 3: Research Squad Setup Verification")
    print("=" * 60)

    all_ok = True

    # Check environment variables
    print("\n1. Environment Variables:")
    all_ok &= check_env_var("OPENAI_API_KEY", required=True)
    all_ok &= check_env_var("TAVILY_API_KEY", required=True)
    all_ok &= check_env_var("LANGCHAIN_API_KEY", required=False)
    all_ok &= check_env_var("LANGCHAIN_TRACING_V2", required=False, secret=False)
    all_ok &= check_env_var("LANGCHAIN_PROJECT", required=False, secret=False)
    all_ok &= check_env_var("ENRICHLAYER_API_KEY", required=False)

    # Check imports
    print("\n2. Package Imports:")
    all_ok &= check_langgraph_imports()
    all_ok &= check_research_squad_imports()

    # Check API connections
    print("\n3. API Connections:")
    openai_ok = check_openai_connection()
    all_ok &= openai_ok

    langsmith_ok = check_langsmith_connection()
    if not langsmith_ok:
        print("       (LangSmith is optional but recommended for observability)")

    # Summary
    print("\n" + "=" * 60)
    if all_ok:
        print("STATUS: All checks passed! Ready to run the demo.")
        print("\nRun the demo with:")
        print("  python main.py --url 'https://linkedin.com/in/demo' --company 'Demo Corp'")
    else:
        print("STATUS: Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Copy .env.example to .env and fill in your API keys")
        print("  2. Run: pip install -r requirements.txt")
        print("  3. Ensure you're in the workspace directory")
    print("=" * 60 + "\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
