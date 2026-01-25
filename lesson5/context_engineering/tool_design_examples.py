"""
Tool Design: Good vs Bad Examples

From Anthropic's Advanced Tool Use guidelines:
- Minimal: Only tools actually needed
- Focused: Each tool does one thing well
- No overlap: "If humans can't decide which tool, neither can the LLM"
- Self-contained: Return all needed info, don't require follow-ups
- Token-efficient: Don't return 10KB when 500 bytes suffice

Run:
    python context_engineering/tool_design_examples.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any

from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    sys.exit(1)


# =============================================================================
# BAD Tool Design Examples
# =============================================================================

BAD_TOOLS = [
    {
        "name": "search",
        "description": "Search for anything. search_type can be 'web', 'docs', 'code', 'all'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "search_type": {"type": "string", "default": "all"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_data",
        "description": "Get data from the database. Specify table and optional filters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "filters": {"type": "object"},
                "fields": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["table"]
        }
    },
    {
        "name": "send_message",
        "description": "Send a message via email, slack, or SMS.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "enum": ["email", "slack", "sms"]},
                "recipient": {"type": "string"},
                "message": {"type": "string"},
                "subject": {"type": "string"}
            },
            "required": ["channel", "recipient", "message"]
        }
    }
]

# Problems:
# 1. "search" does too many things - when should it use which type?
# 2. "get_data" is too generic - what tables exist? What are valid filters?
# 3. "send_message" combines different channels with different needs


# =============================================================================
# GOOD Tool Design Examples
# =============================================================================

GOOD_TOOLS = [
    {
        "name": "search_product_documentation",
        "description": """Search official product documentation for feature info.

USE WHEN: User asks about product features, configuration, or API usage.
NOT FOR: Code examples, troubleshooting, or support tickets.

RETURNS:
- title: Document title
- section: Relevant section header
- content: Matching content (max 500 chars)
- url: Link to full documentation""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_codebase",
        "description": """Search project source code for implementations.

USE WHEN: User needs code examples or implementation details.
NOT FOR: Configuration questions or API documentation.

RETURNS:
- file_path: Path to matching file
- line_number: Starting line of match
- snippet: Code snippet (10 lines context)
- language: Programming language""",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Code pattern or function name to find"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '*.py')",
                    "default": "*"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_campaign_metrics",
        "description": """Get performance metrics for outreach campaigns.

USE WHEN: User asks about response rates, open rates, or campaign performance.

RETURNS:
- response_rate: Percentage of responses received
- open_rate: Percentage of emails opened
- total_sent: Number of messages sent
- total_responses: Number of responses
- period: Time period for metrics""",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_period": {
                    "type": "string",
                    "enum": ["today", "this_week", "this_month", "last_month"],
                    "description": "Time period to get metrics for"
                },
                "campaign_id": {
                    "type": "string",
                    "description": "Optional: specific campaign ID"
                }
            },
            "required": ["time_period"]
        }
    },
    {
        "name": "get_top_templates",
        "description": """Get top performing email templates by response rate.

USE WHEN: User wants to know which templates work best.

RETURNS:
- templates: List of templates with:
  - name: Template name
  - response_rate: Response percentage
  - uses: Number of times used
  - industry: Best performing industry for this template""",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of templates to return (1-10)",
                    "default": 5
                },
                "industry": {
                    "type": "string",
                    "description": "Optional: filter by industry"
                }
            }
        }
    },
    {
        "name": "send_slack_message",
        "description": """Send a message to a Slack channel.

USE WHEN: User explicitly wants to send a Slack notification.
REQUIRES: Channel must exist and bot must be a member.

RETURNS:
- success: Boolean
- message_ts: Slack message timestamp (for threading)
- channel: Channel where message was sent""",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Slack channel name (without #)"
                },
                "message": {
                    "type": "string",
                    "description": "Message text (supports Slack markdown)"
                }
            },
            "required": ["channel", "message"]
        }
    }
]


# =============================================================================
# Tool Response Examples
# =============================================================================

def bad_tool_response_example():
    """Example of a bad (verbose) tool response."""
    return {
        "status": "success",
        "data": {
            "query": "response rate",
            "timestamp": "2024-01-15T10:30:00Z",
            "execution_time_ms": 45,
            "database": "analytics_prod",
            "table": "campaigns",
            "row_count": 1543,
            "metrics": {
                "response_rate": 3.5,
                "response_rate_previous_period": 3.2,
                "response_rate_change": 0.3,
                "response_rate_change_percentage": 9.375,
                # ... 50 more metrics the user didn't ask for
            },
            "debug_info": {
                "query_plan": "...",
                "cache_hit": False,
            }
        }
    }


def good_tool_response_example():
    """Example of a good (focused) tool response."""
    return {
        "response_rate": 3.5,
        "total_sent": 1200,
        "total_responses": 42,
        "period": "this_week"
    }


# =============================================================================
# Demo: Compare Tool Behavior
# =============================================================================

async def demo_tool_selection():
    """Demonstrate how tool design affects model behavior."""
    print("\n" + "=" * 60)
    print(" Tool Design Comparison")
    print("=" * 60)

    client = anthropic.AsyncAnthropic()

    user_query = "How did our email campaigns perform this week?"

    # Test with bad tools
    print("\n[Test 1: Using poorly designed tools]")
    print("-" * 60)
    response_bad = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        tools=BAD_TOOLS,
        messages=[{"role": "user", "content": user_query}]
    )

    # Find tool use in response
    for block in response_bad.content:
        if block.type == "tool_use":
            print(f"Tool called: {block.name}")
            print(f"Inputs: {json.dumps(block.input, indent=2)}")

    # Test with good tools
    print("\n[Test 2: Using well-designed tools]")
    print("-" * 60)
    response_good = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        tools=GOOD_TOOLS,
        messages=[{"role": "user", "content": user_query}]
    )

    for block in response_good.content:
        if block.type == "tool_use":
            print(f"Tool called: {block.name}")
            print(f"Inputs: {json.dumps(block.input, indent=2)}")


async def demo_ambiguous_query():
    """Demonstrate tool confusion with overlapping tools."""
    print("\n" + "=" * 60)
    print(" Ambiguous Query Test")
    print("=" * 60)

    client = anthropic.AsyncAnthropic()

    # This query could match multiple bad tools
    user_query = "Find information about authentication"

    print(f"\nQuery: '{user_query}'")

    print("\n[With overlapping tools (bad)]")
    print("-" * 60)

    overlapping_tools = [
        {
            "name": "search_docs",
            "description": "Search documentation",
            "input_schema": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}
        },
        {
            "name": "find_docs",
            "description": "Find in documentation",
            "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        },
        {
            "name": "query_knowledge_base",
            "description": "Query the knowledge base for information",
            "input_schema": {"type": "object", "properties": {"search_term": {"type": "string"}}, "required": ["search_term"]}
        }
    ]

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        tools=overlapping_tools,
        messages=[{"role": "user", "content": user_query}]
    )

    print("Model's choice:")
    for block in response.content:
        if block.type == "tool_use":
            print(f"  {block.name}: {block.input}")
        elif block.type == "text":
            print(f"  Text: {block.text[:100]}...")

    print("\n[With distinct tools (good)]")
    print("-" * 60)

    distinct_tools = [
        {
            "name": "search_product_documentation",
            "description": """Search official product documentation.
            USE WHEN: User asks about product features or configuration.
            NOT FOR: Code examples or API reference.""",
            "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        },
        {
            "name": "search_api_reference",
            "description": """Search API reference documentation.
            USE WHEN: User needs API endpoints, parameters, or response formats.
            NOT FOR: Conceptual explanations or tutorials.""",
            "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        },
    ]

    response = await client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        tools=distinct_tools,
        messages=[{"role": "user", "content": user_query}]
    )

    print("Model's choice:")
    for block in response.content:
        if block.type == "tool_use":
            print(f"  {block.name}: {block.input}")
        elif block.type == "text":
            print(f"  Text: {block.text[:100]}...")


def print_tool_comparison():
    """Print side-by-side comparison of bad vs good tools."""
    print("\n" + "=" * 60)
    print(" Tool Design Guidelines")
    print("=" * 60)

    comparisons = [
        {
            "principle": "Minimal",
            "bad": "One tool that does everything",
            "good": "Separate tools for distinct operations"
        },
        {
            "principle": "Focused",
            "bad": "search(query, type, filters, options...)",
            "good": "search_docs(query), search_code(query)"
        },
        {
            "principle": "No Overlap",
            "bad": "search_docs, find_docs, query_docs",
            "good": "search_product_docs vs search_api_reference"
        },
        {
            "principle": "Self-contained",
            "bad": "get_user_id() then get_user_details(id)",
            "good": "get_user_by_email(email) returns all details"
        },
        {
            "principle": "Token-efficient",
            "bad": "Return 50 fields, debug info, metadata",
            "good": "Return only requested fields"
        }
    ]

    for c in comparisons:
        print(f"\n{c['principle'].upper()}")
        print(f"  [Bad]:  {c['bad']}")
        print(f"  [Good]: {c['good']}")


async def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    print_tool_comparison()
    await demo_tool_selection()
    await demo_ambiguous_query()


if __name__ == "__main__":
    asyncio.run(main())
