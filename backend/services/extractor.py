from models import Source, ExtractionResult
from services import gemini
from utils.logger import get_logger

logger = get_logger("extractor")

def extract(source: Source) -> ExtractionResult:
    logger.info(f"Extracting facts from: {source.url}")
    result = gemini.extract_evidence(source)
    logger.info(f"Extracted {len(result.facts)} facts, {len(result.statistics)} stats, {len(result.quotes)} quotes.")
    return result
