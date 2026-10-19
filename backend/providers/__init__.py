import os
from providers.registry import registry
from providers.gemini_provider import GeminiProvider

def init_providers():
    flash_model = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.1-flash-lite")
    pro_model = os.getenv("GEMINI_PRO_MODEL", "gemini-3.1-flash-lite")
    fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-flash-lite-latest")
    
    registry.register("gemini-flash", GeminiProvider(model_name=flash_model, fallback_model=fallback_model))
    registry.register("gemini-pro", GeminiProvider(model_name=pro_model, fallback_model=fallback_model))



