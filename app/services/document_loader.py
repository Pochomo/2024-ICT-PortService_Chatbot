import fitz  # PyMuPDF
import re
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

class PDFLoader:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # 문서를 더 작은 크기로 분할
            chunk_overlap=200,
            length_function=len,
        )
        self.logger = logging.getLogger(__name__)

    def clean_text(self, text):
        # 불필요한 메타데이터를 제거하는 정규 표현식
        text = re.sub(r'\s+', ' ', text).strip()  # 여러 공백을 하나로
        return text

    def load_and_split(self, pdf_path):
        documents = []
        try:
            with fitz.open(pdf_path) as doc:
                for i, page in enumerate(doc):
                    text = page.get_text()
                    clean_text = self.clean_text(text)
                    if clean_text:
                        # 페이지 내용을 분할하여 Document로 변환
                        chunks = self.text_splitter.split_text(clean_text)
                        for chunk in chunks:
                            documents.append(Document(page_content=chunk, metadata={"page_number": i + 1}))
            self.logger.info(f"Loaded and split {len(documents)} documents from {pdf_path}")
        except Exception as e:
            self.logger.error(f"Error loading PDF {pdf_path}: {str(e)}")
        return documents

    def load_and_split_by_keyword(self, pdf_path, keywords):
        documents = self.load_and_split(pdf_path)  # 기존 로드 및 분할된 문서들
        keyword_documents = {keyword: [] for keyword in keywords}

        # 키워드별로 문서 분류 및 주변 청크 포함
        for idx, doc in enumerate(documents):
            for keyword in keywords:
                if keyword in doc.page_content:
                    keyword_documents[keyword].append(doc)
                    # 키워드 주변의 청크도 함께 묶어줍니다.
                    if idx > 0:
                        keyword_documents[keyword].append(documents[idx - 1])  # 이전 청크 추가
                    if idx < len(documents) - 1:
                        keyword_documents[keyword].append(documents[idx + 1])  # 다음 청크 추가
                    break  # 한 문서가 여러 키워드에 중복되지 않도록 하기 위함

        # 분류된 문서를 합쳐서 리턴
        split_documents = []
        for keyword, docs in keyword_documents.items():
            split_documents.extend(docs)

        return split_documents
    
    def get_related_content(query_result, all_documents, max_length=2000):
        """
        검색 결과에 연관된 추가 콘텐츠를 가져옴.
        """
        related_content = query_result.page_content
        current_length = len(related_content)
        page_number = query_result.metadata["page_number"]

        # 이후 페이지에서 추가 콘텐츠를 가져옴
        for doc in all_documents:
            if doc.metadata["page_number"] > page_number:
                if current_length + len(doc.page_content) > max_length:
                    break
                related_content += " " + doc.page_content
                current_length += len(doc.page_content)
        
        return related_content