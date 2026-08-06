import json
from models import ResearchPlan, KnowledgeBase
from providers.registry import registry
from utils.logger import get_logger

logger = get_logger("writer")

async def generate_report(plan: ResearchPlan, kb: KnowledgeBase, template_type: str = "General Report", feedback: str = None) -> str:
    logger.info("Generating final report from Knowledge Base")
    # Use pro model for high-quality writing
    try:
        provider = registry.get("gemini-pro")
    except ValueError:
        provider = registry.get("gemini-flash")

    source_map = {url: i+1 for i, url in enumerate(kb.sources)}

    formatted_claims = "\n".join([f"- {f.statement} (Source ID: [{source_map.get(f.url, 0)}])" for f in kb.claims])
    formatted_stats = "\n".join([f"- {s}" for s in kb.statistics])
    formatted_quotes = "\n".join([f"- {q}" for q in kb.quotes])

    prompt = f"""You are a deep research expert. Write a detailed, comprehensive report.
Template Style: {template_type}

Goal: {plan.goal}
Target Sections: {plan.sections}

Use ONLY the following structured evidence to write the report. NEVER invent information.
Mention conflicting evidence if any exists. Mention missing information if relevant.
Cite your sources clearly using the provided Source IDs like this: [1] or [2, 3].

=== FACTS & CLAIMS ===
{formatted_claims}

=== STATISTICS ===
{formatted_stats}

=== QUOTES ===
{formatted_quotes}

Return ONLY Markdown text. Do NOT add a References or Bibliography section yourself, it will be generated automatically.

If you are presenting comparisons, trends, or structured numeric data, you MUST include a JSON chart representation wrapped in triple backticks with the language "chart".
Format exactly like this:
```chart
{{
  "chart": {{
    "type": "bar",
    "title": "Chart Title",
    "labels": ["Item A", "Item B"],
    "values": [10, 20]
  }}
}}
```
Supported types are: "bar", "line", "pie".
"""
    if feedback:
        prompt += f"\n\nPREVIOUS REVIEW FEEDBACK TO FIX IN THIS REWRITE:\n{feedback}\n"

    return await provider.generate(prompt)
