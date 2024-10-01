import fitz  # PyMuPDF
import re
import logging
import os
from langchain.schema import Document

class PDFLoader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def clean_text(self, text):
        text = text.replace('\n', ' ')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def split_into_sections(self, text):
        sections = re.split(r'(?=\d+\.)', text)
        return [section.strip() for section in sections if section.strip()]

    def is_law_related_file(self, file_path):
        file_name = os.path.basename(file_path).lower()
        return 'law' in file_name

    def load_and_split(self, pdf_path):
        documents = []
        is_law_related = self.is_law_related_file(pdf_path)
        
        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc.pages()):
                    page_text = self.clean_text(page.get_text("text"))
                    sections = self.split_into_sections(page_text)

                    for section in sections:
                        if section:
                            documents.append(Document(
                                page_content=section,
                                metadata={
                                    "page_number": page_num + 1,
                                    "source": pdf_path,
                                    "is_law_related": is_law_related
                                }
                            ))

        except Exception as e:
            self.logger.error(f"Error loading PDF {pdf_path}: {str(e)}")
        
        return documents