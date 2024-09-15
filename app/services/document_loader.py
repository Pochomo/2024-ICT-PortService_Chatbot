import fitz  # PyMuPDF
import re
import logging
from langchain.schema import Document

class PDFLoader:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def clean_text(self, text):
        # 불필요한 메타데이터를 제거하고 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def split_by_double_newline(self, text):
        # 두 번의 줄바꿈을 기준으로 텍스트를 분리
        paragraphs = text.split('\n\n')
        return paragraphs

    def is_law_related(self, text):
        # 법 관련 키워드가 텍스트에 포함되어 있는지 확인
        law_keywords = ["법", "제조", "조항", "시행령", "규정", "법령", "조치", "관련 법"]
        return any(keyword in text for keyword in law_keywords)

    def load_and_split_by_paragraphs(self, pdf_path):
        documents = []
        try:
            with fitz.open(pdf_path) as doc:
                for page_num, page in enumerate(doc.pages()):
                    # 페이지 텍스트를 가져오기
                    page_text = page.get_text("text")
                    page_text = self.clean_text(page_text)

                    # 두 번의 줄바꿈을 기준으로 텍스트를 청크로 나누기
                    paragraphs = self.split_by_double_newline(page_text)

                    # 각 단락을 문서로 저장
                    for paragraph in paragraphs:
                        if paragraph:  # 빈 단락은 제외
                            documents.append(Document(page_content=paragraph, metadata={"page_number": page_num + 1}))

        except Exception as e:
            self.logger.error(f"Error loading PDF {pdf_path}: {str(e)}")
        
        return documents

    def load_and_split(self, pdf_path):
        # 기본적으로 두 번의 줄바꿈을 기준으로 텍스트를 청크로 분리
        return self.load_and_split_by_paragraphs(pdf_path)
