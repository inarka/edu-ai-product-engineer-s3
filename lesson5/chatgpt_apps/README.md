# ChatGPT Apps

This section provides a brief overview of ChatGPT Apps. For comprehensive guidance, use the `chatgpt-app-skill`.

## What Are ChatGPT Apps?

ChatGPT Apps are custom applications that extend ChatGPT's capabilities through:
- **MCP Servers**: Define tools that ChatGPT can call
- **Widgets**: Rich UI components for displaying data
- **Backend Integration**: Connect to your APIs and services

## Know/Do/Show Framework

Use this framework to evaluate if your idea should be a ChatGPT App:

| Question | Good Fit | May Not Need App |
|----------|----------|------------------|
| Does it surface unique information? | Yes - external APIs, databases | No - general knowledge |
| Does it take actions in systems? | Yes - CRM, email, calendar | No - just answering questions |
| Does it need custom UI? | Yes - charts, forms, tables | No - text response is fine |

### When to Use What

| Complexity | Solution |
|------------|----------|
| Simple Q&A | Custom GPT with instructions |
| Data display + actions | ChatGPT App |
| Complex workflows | ChatGPT App with MCP |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   ChatGPT   │────▶│  MCP Server │────▶│  Your APIs  │
│             │◀────│   (Tools)   │◀────│  & Data     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Widgets   │
                    │  (Rich UI)  │
                    └─────────────┘
```

## Getting Started

### 1. Comprehensive Skill (Recommended)

Use the `chatgpt-app-skill` for guided development:

```bash
# In Claude Code
/chatgpt-app-builder
```

Or clone the skill repository:
```bash
git clone https://github.com/BayramAnnakov/chatgpt-app-skill
```

The skill provides:
- 5-phase development workflow
- MCP server templates (Python & TypeScript)
- Widget examples
- Testing procedures
- Submission checklist

### 2. Quick Reference

Key resources:
- **ChatGPT Apps Documentation**: https://platform.openai.com/docs/plugins
- **MCP Specification**: https://modelcontextprotocol.io
- **Widgets Guide**: (in chatgpt-app-skill)

### 3. Example: Meeting Prep App

The demo app for Workshop 5 is a Meeting Prep assistant:

```
/Users/bayramannakov/GH/onsa-various/onsa-chatgpt-app
```

Features:
- LinkedIn profile lookup for meeting attendees
- Company research synthesis
- Meeting brief generation
- Talking points suggestions

## Development Phases

From the chatgpt-app-skill:

1. **Discovery**: Define Know/Do/Show requirements
2. **Architecture**: Design MCP server and tools
3. **Implementation**: Build server and widgets
4. **Testing**: Local testing and validation
5. **Submission**: App Store review process

## Code Structure

Typical ChatGPT App structure:

```
my-chatgpt-app/
├── server/
│   ├── main.py           # MCP server entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   └── my_tools.py   # Tool definitions
│   └── widgets/
│       └── my_widget.py  # Widget components
├── requirements.txt
├── README.md
└── manifest.json         # App manifest for submission
```

## Sample Tool Definition

```python
from mcp import Tool

@Tool(
    name="get_meeting_context",
    description="Get context for an upcoming meeting with a person"
)
async def get_meeting_context(
    person_name: str,
    company: str,
    meeting_topic: str | None = None
) -> dict:
    """Fetch context for meeting preparation.

    Args:
        person_name: Name of the person you're meeting
        company: Their company name
        meeting_topic: Optional topic of the meeting

    Returns:
        Meeting context including background, talking points, and suggestions
    """
    # Fetch LinkedIn data
    profile = await fetch_linkedin_profile(person_name, company)

    # Fetch company info
    company_info = await fetch_company_info(company)

    # Generate talking points
    talking_points = generate_talking_points(profile, company_info, meeting_topic)

    return {
        "person": profile,
        "company": company_info,
        "talking_points": talking_points,
        "suggested_questions": generate_questions(profile, meeting_topic)
    }
```

## Submission Checklist

Before submitting to the ChatGPT App Store:

- [ ] App has clear, unique value proposition
- [ ] All tools have descriptive names and docstrings
- [ ] Error handling is robust
- [ ] Rate limiting is implemented
- [ ] Privacy policy is defined
- [ ] Manifest.json is complete
- [ ] Testing across different scenarios
- [ ] Documentation is complete

## Resources

- **chatgpt-app-skill**: https://github.com/BayramAnnakov/chatgpt-app-skill
- **MCP Documentation**: https://modelcontextprotocol.io/docs
- **OpenAI Platform**: https://platform.openai.com

## Example Apps in the Wild

1. **Zapier**: Workflow automation
2. **Instacart**: Grocery ordering
3. **Kayak**: Travel booking
4. **Wolfram Alpha**: Mathematical computation

Study these for patterns and best practices.
