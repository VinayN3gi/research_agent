import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
JINA_API_KEY = os.getenv("JINA_API_KEY")

if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print("WARNING: GEMINI_API_KEY is not set.")

if not TAVILY_API_KEY or TAVILY_API_KEY == "your_tavily_api_key_here":
    print("WARNING: TAVILY_API_KEY is not set.")
