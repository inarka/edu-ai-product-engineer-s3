"""
Prompts for Evening Agent V2.

These prompts implement the Reflection Pattern:
V1 (initial) -> External Feedback -> V2 (improved)

The key insight: External feedback breaks the prompt engineering plateau
by providing signals the LLM couldn't generate through reasoning alone.
"""

from prompts.evening_reflection import (
    SYSTEM_PROMPT,
    NEWSLETTER_CRITERIA,
    V1_REPORT_PROMPT,
    VALIDATION_PROMPT,
    REFLECTION_PROMPT,
)

__all__ = [
    "SYSTEM_PROMPT",
    "NEWSLETTER_CRITERIA",
    "V1_REPORT_PROMPT",
    "VALIDATION_PROMPT",
    "REFLECTION_PROMPT",
]

