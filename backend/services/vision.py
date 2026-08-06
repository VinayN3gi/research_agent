import mimetypes
from models import Document
from services.gemini import get_client, MODEL_NAME, gemini_semaphore
from google.genai import types
from utils.logger import get_logger
from tenacity import retry, wait_exponential, stop_after_attempt

logger = get_logger("vision")

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
async def perform_ocr(image_path: str) -> str:
    logger.info(f"Performing OCR on image: {image_path}")
    client = get_client()
    if not client:
        return "[OCR Failed: API Key missing]"
        
    try:
        with open(image_path, "rb") as f:
            image_data = f.read()
    except Exception as e:
        logger.error(f"Failed to read image {image_path}: {e}")
        return "[OCR Failed: Image not found]"

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"

    prompt = "Transcribe and describe the contents of this image in high detail. If it is a chart, extract the data points. If it is a diagram, describe the flow. If it is text, transcribe it verbatim."
    
    async with gemini_semaphore:
        try:
            response = await client.aio.models.generate_content(
                model=MODEL_NAME, 
                contents=[
                    types.Part.from_bytes(data=image_data, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1
                ),
            )
            return response.text
        except Exception as e:
            logger.error(f"Error in OCR: {e}")
            return f"[OCR Failed: {e}]"
