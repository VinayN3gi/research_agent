from models import EvaluationMetrics, ResearchPlan
from providers.registry import registry
from utils.logger import get_logger

logger = get_logger("evaluator")

async def evaluate_report(report_text: str, plan: ResearchPlan) -> EvaluationMetrics:
    logger.info("Evaluating report quality across 9 metrics")
    
    # We use gemini-pro for high quality evaluation
    try:
        provider = registry.get("gemini-pro")
    except ValueError:
        provider = registry.get("gemini-flash")

    prompt = f"""You are an expert Research Evaluator. Evaluate the following research report against the original goal.
Score each metric from 1-100. Be extremely critical.

Goal: {plan.goal}
Target Sections: {plan.sections}

Report:
{report_text}

Metrics to evaluate:
1. Coverage: Does the report cover all expected sections and sub-topics?
2. Evidence Quality: Are the claims supported by strong, factual evidence?
3. Citation Correctness: Are sources properly cited and inline?
4. Freshness: Is the information reasonably up-to-date (if applicable)?
5. Source Diversity: Were multiple perspectives and different types of sources used?
6. Contradiction Handling: Were conflicting facts addressed or resolved properly?
7. Hallucination Risk: Is the report grounded in fact, or does it seem to invent details? (100 = No risk of hallucination)
8. Completeness: Is the report a complete, self-contained document?
9. Confidence: Overall confidence in the findings.

Also calculate the 'overall_score' (average of the 9) and list any 'missing_topics' that were completely ignored.
Return a JSON object conforming strictly to the requested schema.
"""
    try:
        metrics = await provider.structured(prompt, EvaluationMetrics)
        logger.info(f"Report scored {metrics.overall_score}/100")
        return metrics
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        # Return a fallback metric object if it fails
        return EvaluationMetrics(
            coverage=0, evidence_quality=0, citation_correctness=0,
            freshness=0, source_diversity=0, contradiction_handling=0,
            hallucination_risk=0, completeness=0, confidence=0, overall_score=0
        )
