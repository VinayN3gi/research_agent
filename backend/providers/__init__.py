from providers.registry import registry
from providers.gemini_provider import GeminiProvider

def init_providers():
    registry.register("gemini-flash", GeminiProvider(model_name="gemini-3.1-flash-lite"))
    registry.register("gemini-pro", GeminiProvider(model_name="gemini-3.1-pro"))
    
    # We can register stub providers for future implementation
    # registry.register("gpt-4o", OpenAIProvider(model_name="gpt-4o"))
