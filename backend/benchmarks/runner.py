import sys
import os
import json
import asyncio

# Ensure backend directory is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import engine, Base
from providers import init_providers
from models import ResearchPlan, PlannerTask
from evaluation.evaluator import evaluate_report

async def run_benchmark(filepath: str):
    print(f"Running Benchmark: {filepath}")
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    print(f"Question: {data['question']}")
    
    # Initialize the provider registry
    init_providers()
    
    # Normally we would run the full research pipeline here,
    # but for this script we will simulate a generated report to evaluate the evaluator.
    mock_report = f"""# {data['topic']}
    This is a mock report covering some elements of the topic.
    We discuss {data['expected_topics'][0]} and {data['expected_topics'][1]}.
    """
    
    mock_plan = ResearchPlan(
        goal=data['question'],
        sections=data['expected_topics'],
        tasks=[],
        success_criteria=["Answer the question thoroughly"]
    )
    
    print("\nEvaluating Report...")
    metrics = await evaluate_report(mock_report, mock_plan)
    
    print("\n--- Evaluation Results ---")
    print(f"Overall Score: {metrics.overall_score}/100")
    print(f"Coverage: {metrics.coverage}")
    print(f"Evidence Quality: {metrics.evidence_quality}")
    print(f"Citation Correctness: {metrics.citation_correctness}")
    print(f"Freshness: {metrics.freshness}")
    print(f"Source Diversity: {metrics.source_diversity}")
    print(f"Contradiction Handling: {metrics.contradiction_handling}")
    print(f"Hallucination Risk: {metrics.hallucination_risk}")
    print(f"Completeness: {metrics.completeness}")
    print(f"Confidence: {metrics.confidence}")
    print(f"Missing Topics: {', '.join(metrics.missing_topics)}")
    print("--------------------------\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(run_benchmark(sys.argv[1]))
    else:
        print("Usage: python runner.py <path_to_benchmark.json>")
