from langchain_community.document_loaders import UnstructuredFileIOLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import tempfile
import os
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
            text = self.extract_text_from_hwp(file_content)
        
        documents = [Document(page_content=text)]
        split_docs = self.text_splitter.split_documents(documents)
        return split_docs

    def is_hwpx(self, file_content):
        return file_content.startswith(b'PK')

    def extract_text_from_hwp(self, file_content):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.hwp') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        try:
            loader = UnstructuredFileIOLoader(temp_file_path)
            documents = loader.load()
            return ' '.join([doc.page_content for doc in documents])
        finally:
            os.unlink(temp_file_path)

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