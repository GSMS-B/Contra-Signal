import pdfplumber
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

    def extract_text(self) -> str:
        """Extracts full text from PDF."""
        full_text = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        full_text.append(f"--- Page {i+1} ---\n{text}")
            return "\n\n".join(full_text)
        except Exception as e:
            logger.error(f"Error extracting text from {self.pdf_path}: {e}")
            return ""

    def extract_tables(self) -> List[Dict[str, Any]]:
        """Extracts all tables with metadata."""
        tables = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for t_idx, table_data in enumerate(page_tables):
                        # Filter out empty or tiny tables (likely noise)
                        if not table_data or len(table_data) < 2:
                            continue
                        
                        # basic cleanup
                        cleaned_table = []
                        for row in table_data:
                            cleaned_row = [cell.strip().replace('\n', ' ') if cell else '' for cell in row]
                            cleaned_table.append(cleaned_row)

                        tables.append({
                            'page': i + 1,
                            'table_index': t_idx,
                            'data': cleaned_table
                        })
            return tables
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []
