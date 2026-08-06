import asyncio
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
from google import genai
from google.genai import types

from providers.base import LLMProvider, T
from config import GEMINI_API_KEY
from utils.logger import get_logger
from tenacity import retry, wait_exponential, stop_after_attempt

logger = get_logger("gemini_provider")

gemini_semaphore = asyncio.Semaphore(10)

class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = 'gemini-3.1-flash-lite'):
        super().__init__()
        self.model_name = model_name
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            logger.error("GEMINI_API_KEY is not set or is dummy.")
            self.client = None
        else:
            self.client = genai.Client(api_key=GEMINI_API_KEY)

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
    async def generate(self, prompt: str, **kwargs) -> str:
        if not self.client:
            return f"Mock text from {self.model_name}"
            
        temperature = kwargs.get("temperature", 0.7)
        import time
        start_time = time.time()
        async with gemini_semaphore:
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=temperature)
                )
                self.record_success(time.time() - start_time)
                return response.text
            except Exception as e:
                self.record_failure()
                logger.error(f"Gemini generate error: {e}")
                raise

    async def stream(self, prompt: str, **kwargs):
        raise NotImplementedError("Stream not implemented yet")

    async def embed(self, text: str) -> List[float]:
        raise NotImplementedError("Embed not implemented yet")

    async def vision(self, image_path: str, prompt: str, **kwargs) -> str:
        raise NotImplementedError("Vision not implemented yet")

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=True)
    async def structured(self, prompt: str, schema: Type[T], **kwargs) -> T:
        if not self.client:
            # Return empty mock model
            logger.warning("Returning mock structured data due to missing API key")
            # This works well enough for mock data if the schema supports instantiation without args
            return schema.model_validate({})

        temperature = kwargs.get("temperature", 0.7)
        import time
        start_time = time.time()
        async with gemini_semaphore:
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema,
                        temperature=temperature
                    ),
                )
                self.record_success(time.time() - start_time)
                return schema.model_validate_json(response.text)
            except Exception as e:
                self.record_failure()
                logger.error(f"Gemini structured error: {e}")
                raise

    async def count_tokens(self, text: str) -> int:
        # A rough estimate (4 chars = 1 token) until actual API is used
        return len(text) // 4
