import fitz  # PyMuPDF
from models import Document
from services.parser.dispatcher import BaseParser
import os

class PDFParser(BaseParser):
    async def parse(self, file_path: str, metadata: dict = None) -> Document:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
            
        doc.close()
        
        filename = os.path.basename(file_path)
        return Document(
            id=file_path,
            title=metadata.get("title", filename),
            source_type="pdf",
            text=text.strip(),
            metadata=metadata or {}
        )
