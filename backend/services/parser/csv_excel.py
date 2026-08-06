import pandas as pd
from models import Document
from services.parser.dispatcher import BaseParser
import os

class CsvExcelParser(BaseParser):
    async def parse(self, file_path: str, metadata: dict = None) -> Document:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        text = df.to_markdown(index=False)
        
        filename = os.path.basename(file_path)
        return Document(
            id=file_path,
            title=metadata.get("title", filename),
            source_type=ext.strip("."),
            text=text,
            metadata=metadata or {}
        )
