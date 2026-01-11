# Evaluation Plan: Research Squad

Example evaluation plan for a B2B sales research multi-agent system.

## Business Objectives

**Primary Goal**: Provide actionable sales intelligence for B2B outreach

**Success Criteria**:
- Research reports enable personalized outreach
- Reports contain specific, verifiable information
- Latency under 30 seconds for standard requests

**Failure Modes**:
- Generic, non-personalized information
- Incorrect company/person data
- Missing recent news/updates
- Reports that are too long or too short

## Dataset Strategy

**Total Test Cases**: 20

### Happy Path (10 cases - 50%)
| ID | Description | Key Validation |
|----|-------------|----------------|
| HP-1 | Tech CEO (Microsoft) | Should mention AI, cloud |
| HP-2 | Tech CEO (NVIDIA) | Should mention GPU, AI |
| HP-3 | Startup Founder | Should identify startup stage |
| HP-4 | Sales VP at Enterprise | Should identify sales focus |
| HP-5 | Engineering Manager | Should identify technical focus |
| HP-6 | Healthcare Executive | Should identify industry context |
| HP-7 | Finance Director | Should identify finance focus |
| HP-8 | Marketing CMO | Should identify marketing focus |
| HP-9 | Product Manager | Should identify product focus |
| HP-10 | International Executive | Should handle non-US context |

### Edge Cases (7 cases - 35%)
| ID | Description | Key Validation |
|----|-------------|----------------|
| EC-1 | No company provided | Should infer from LinkedIn |
| EC-2 | Very long profile URL | Should handle gracefully |
| EC-3 | Non-English company name | Should handle Unicode |
| EC-4 | Acquired company | Should note acquisition |
| EC-5 | Person with multiple roles | Should identify current role |
| EC-6 | Minimal LinkedIn profile | Should handle limited data |
| EC-7 | Stealth mode startup | Should handle missing data |

### Adversarial Cases (3 cases - 15%)
| ID | Description | Key Validation |
|----|-------------|----------------|
| AD-1 | Invalid LinkedIn URL | Should return error gracefully |
| AD-2 | Non-existent profile | Should indicate not found |
| AD-3 | Malformed company name | Should handle gracefully |

## Evaluation Methods

| Metric | Type | Method | Threshold |
|--------|------|--------|-----------|
| Schema Valid | Automated | Check fields present | 100% |
| Keywords Present | Automated | Check for expected terms | 80% |
| Report Length | Automated | 200-2000 chars | 100% |
| Research Quality | LLM-as-Judge | 5-point rubric | 4.0/5.0 |
| Relevance | LLM-as-Judge | Matches target person | 4.0/5.0 |
| Latency | Performance | Under 30s | 95th %ile |
| Token Efficiency | Performance | Under 10k tokens | 90th %ile |

## Evaluator Implementation

```python
from langsmith.evaluation import evaluate
from evaluation.evaluators import (
    schema_evaluator,
    keyword_coverage_evaluator,
    quality_evaluator,
    latency_evaluator,
)

# Run evaluation
results = evaluate(
    research_agent.invoke,
    data="research_squad_eval",
    evaluators=[
        schema_evaluator,
        keyword_coverage_evaluator,
        quality_evaluator,
        latency_evaluator,
    ],
    experiment_prefix="research_squad_v1",
)
```

## CI/CD Integration

### Tier 1: PR Checks (<5 min)
- schema_evaluator
- keyword_coverage_evaluator
- report_length_evaluator
- **Threshold**: All automated tests pass

### Tier 2: Pre-Deploy (15-30 min)
- All Tier 1 evaluators
- quality_evaluator (LLM-as-Judge)
- relevance_evaluator (LLM-as-Judge)
- **Threshold**: Average quality > 4.0/5.0

### Tier 3: Production Monitoring
- Sample 5% of production traffic
- Weekly evaluation runs
- Alert on quality drop > 10%

## Comparison: LangGraph vs Deep Agents

When comparing implementations, focus on:

| Metric | LangGraph Expected | Deep Agents Expected |
|--------|-------------------|---------------------|
| Latency | Faster (parallel execution) | Slower (dynamic planning) |
| Quality | Consistent | Potentially higher |
| Token Usage | Predictable | Variable |
| Flexibility | Low (static graph) | High (dynamic) |

## Next Steps

1. [ ] Create dataset in LangSmith with 20 test cases
2. [ ] Implement automated evaluators
3. [ ] Run baseline evaluation on current implementation
4. [ ] Add LLM-as-Judge evaluators for quality
5. [ ] Set up CI pipeline for PR checks
6. [ ] Configure production monitoring

## Notes

- Start with happy path cases to establish baseline
- Add edge cases as you discover production issues
- Review flagged cases weekly and add to dataset
- Re-run full evaluation after any major change
