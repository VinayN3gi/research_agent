from .dispatcher import registry, get_parser
from .pdf import PDFParser
from .docx import DocxParser
from .csv_excel import CsvExcelParser
from .image import ImageParser

registry.register(".pdf", PDFParser())
registry.register(".docx", DocxParser())
registry.register(".csv", CsvExcelParser())
registry.register(".xlsx", CsvExcelParser())
registry.register(".png", ImageParser())
registry.register(".jpg", ImageParser())
registry.register(".jpeg", ImageParser())
