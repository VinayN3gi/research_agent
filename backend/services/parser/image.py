from models import Document
from services.parser.dispatcher import BaseParser
from services.vision import perform_ocr
import os

class ImageParser(BaseParser):
    async def parse(self, file_path: str, metadata: dict = None) -> Document:
        text = await perform_ocr(file_path)
        
        filename = os.path.basename(file_path)
        return Document(
            id=file_path,
            title=metadata.get("title", filename),
            source_type="image",
            text=text.strip(),
            metadata=metadata or {}
        )
