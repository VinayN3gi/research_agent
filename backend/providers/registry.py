from typing import Dict
from providers.base import LLMProvider
from utils.logger import get_logger

logger = get_logger("provider_registry")

class ProviderRegistry:
    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        
    def register(self, name: str, provider: LLMProvider):
        logger.info(f"Registering LLM provider: {name}")
        self._providers[name] = provider
        
    def get(self, name: str) -> LLMProvider:
        if name not in self._providers:
            raise ValueError(f"Provider {name} not found in registry.")
        return self._providers[name]

registry = ProviderRegistry()
