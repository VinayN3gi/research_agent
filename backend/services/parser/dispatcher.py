from models import Document
from typing import Dict
import os

class BaseParser:
    async def parse(self, file_path: str, metadata: dict = None) -> Document:
        raise NotImplementedError()

class ParserRegistry:
    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}
        
    def register(self, extension: str, parser: BaseParser):
        self._parsers[extension.lower()] = parser
        
    async def parse(self, file_path: str, metadata: dict = None) -> Document:
        ext = os.path.splitext(file_path)[1].lower()
        parser = self._parsers.get(ext)
        if not parser:
            raise ValueError(f"No parser registered for extension: {ext}")
        return await parser.parse(file_path, metadata or {})

registry = ParserRegistry()

def get_parser() -> ParserRegistry:
    return registry
