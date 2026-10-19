import mimetypes
from providers.registry import registry
from utils.logger import get_logger
from tenacity import retry, wait_exponential, stop_after_attempt

logger = get_logger("vision")

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
async def perform_ocr(image_path: str) -> str:
    logger.info(f"Performing OCR on image: {image_path}")
    try:
        provider = registry.get("gemini-flash")
    except ValueError:
        return "[OCR Failed: LLM Provider not registered]"

    prompt = "Transcribe and describe the contents of this image in high detail. If it is a chart, extract the data points. If it is a diagram, describe the flow. If it is text, transcribe it verbatim."
    
    try:
        return await provider.vision(image_path, prompt)
    except Exception as e:
        logger.error(f"Error in OCR: {e}")
        return f"[OCR Failed: {e}]"

