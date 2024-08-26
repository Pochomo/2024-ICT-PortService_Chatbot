import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

class HWPLoader:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
        )
        self.logger = logging.getLogger(__name__)

    def is_hwpx(self, file_content):
        # HWPX 파일은 일반적으로 'PK' 서명을 가진 ZIP 압축 파일입니다.
        return file_content.startswith(b'PK')

    async def load_and_split(self, file_content):
        if self.is_hwpx(file_content):
            text = self.extract_text_from_hwpx(file_content)
        else:
            raise ValueError("Only HWPX format is supported for HWP 2022. Please convert your file to HWPX format.")
        
        if not text:
            raise ValueError("Failed to extract text from the provided HWPX file.")
        
        self.logger.info(f"Extracted text length: {len(text)} characters")

        documents = [Document(page_content=text)]
        split_docs = self.text_splitter.split_documents(documents)
        self.logger.info(f"Split into {len(split_docs)} documents")

        return split_docs

    def extract_text_from_hwpx(self, file_content):
        try:
            with zipfile.ZipFile(BytesIO(file_content), 'r') as zip_ref:
                content = []
                for file in zip_ref.namelist():
                    if file.startswith('Contents/') and file.endswith('.xml'):
                        with zip_ref.open(file) as xml_file:
                            tree = ET.parse(xml_file)
                            root = tree.getroot()
                            for elem in root.iter():
                                if elem.text:
                                    content.append(elem.text.strip())
            extracted_text = ' '.join(content)
            self.logger.info(f"Extracted {len(extracted_text)} characters from HWPX file")
            return extracted_text
        except Exception as e:
            self.logger.error(f"Error extracting text: {str(e)}")
            return ""
