from langchain_teddynote.document_loaders import HWPLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import os

class HWPLoaderWrapper:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def load_and_split(self, file_content):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.hwp') as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        try:
            loader = HWPLoader(temp_file_path)
            documents = loader.load()
            split_docs = self.text_splitter.split_documents(documents)
            return split_docs
        finally:
            os.unlink(temp_file_path)