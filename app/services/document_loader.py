from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET

class HWPLoader:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def load_and_split(self, file_content):
        if self.is_hwpx(file_content):
            text = self.extract_text_from_hwpx(file_content)
        else:
            raise ValueError("Only HWPX format is supported for HWP 2022. Please convert your file to HWPX format.")
        
        if not text:
            raise ValueError("Failed to extract text from the provided HWPX file.")
        
        documents = [Document(page_content=text)]
        split_docs = self.text_splitter.split_documents(documents)
        return split_docs

    def is_hwpx(self, file_content):
        # HWPX files are typically ZIP archives, identified by the 'PK' signature
        return file_content.startswith(b'PK')

    def extract_text_from_hwpx(self, file_content):
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
            return ' '.join(content)
