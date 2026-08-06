from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class ProviderHealth(BaseModel):
    successes: int = 0
    failures: int = 0
    total_latency_seconds: float = 0.0

class LLMProvider(ABC):
    def __init__(self):
        self.health = ProviderHealth()
        
    def record_success(self, latency: float):
        self.health.successes += 1
        self.health.total_latency_seconds += latency
        
    def record_failure(self):
        self.health.failures += 1

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt."""
        pass
        
    @abstractmethod
    async def stream(self, prompt: str, **kwargs):
        """Stream text generation."""
        pass
        
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embeddings for text."""
        pass
        
    @abstractmethod
    async def vision(self, image_path: str, prompt: str, **kwargs) -> str:
        """Process an image with a prompt."""
        pass
        
    @abstractmethod
    async def structured(self, prompt: str, schema: Type[T], **kwargs) -> T:
        """Generate a structured response adhering to a Pydantic schema."""
        pass
        
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text for cost estimation."""
        pass
