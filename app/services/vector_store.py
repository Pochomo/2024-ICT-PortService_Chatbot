import os
import logging
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import re
import hashlib

class VectorStore:
    def __init__(self):
        self.embedding_model = OpenAIEmbeddings()
        self.general_vector_store = None
        self.law_vector_store = None
        self.general_documents = []
        self.law_documents = []
        self.document_hashes = set()
        self.logger = logging.getLogger(__name__)

    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def hash_document(self, doc):
        cleaned_content = self.clean_text(doc.page_content)
        return hashlib.md5(cleaned_content.encode()).hexdigest()

    def add_documents(self, documents, is_law_related=False):
        target_documents = self.law_documents if is_law_related else self.general_documents
        unique_documents = []

        for doc in documents:
            doc_hash = self.hash_document(doc)
            if doc_hash not in self.document_hashes:
                doc.page_content = self.clean_text(doc.page_content)
                unique_documents.append(doc)
                self.document_hashes.add(doc_hash)

        if unique_documents:
            target_documents.extend(unique_documents)
            self.logger.info(f"Added {len(unique_documents)} unique documents to the {'law' if is_law_related else 'general'} vector store.")
            self.create_vector_store(is_law_related)

    def create_vector_store(self, is_law_related=False):
        target_documents = self.law_documents if is_law_related else self.general_documents

        vector_store = Chroma.from_documents(documents=target_documents, embedding=self.embedding_model)

        if is_law_related:
            self.law_vector_store = vector_store
        else:
            self.general_vector_store = vector_store

        self.logger.info(f"{'Law' if is_law_related else 'General'} vector store created with {len(target_documents)} documents.")

    def as_retriever(self, is_law_related=False, k=8):
        target_vector_store = self.law_vector_store if is_law_related else self.general_vector_store

        if target_vector_store is None:
            store_type = "law" if is_law_related else "general"
            self.logger.error(f"{store_type.capitalize()} vector store is not initialized.")
            raise ValueError(f"{store_type.capitalize()} vector store is not initialized.")

        return target_vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})

    def similarity_search(self, query, is_law_related=False, k=8):
        target_vector_store = self.law_vector_store if is_law_related else self.general_vector_store

        if target_vector_store is None:
            raise ValueError("Vector store is not initialized")

        retriever = target_vector_store.as_retriever(search_kwargs={"k": k})
        docs = retriever.get_relevant_documents(query)

        if not docs:
            raise ValueError("No results found for the query.")

        return docs

    def save_local(self, path, is_law_related=False):
        self.logger.warning("Chroma does not support direct save/load operations like FAISS.")

    def load_local(self, path, is_law_related=False):
        self.logger.warning("Chroma does not support direct save/load operations like FAISS.")

    def clean_existing_documents(self):
        self.document_hashes.clear()
        for doc_list in [self.general_documents, self.law_documents]:
            unique_docs = []
            for doc in doc_list:
                doc_hash = self.hash_document(doc)
                if doc_hash not in self.document_hashes:
                    doc.page_content = self.clean_text(doc.page_content)
                    unique_docs.append(doc)
                    self.document_hashes.add(doc_hash)
            doc_list[:] = unique_docs

        self.create_vector_store(is_law_related=False)
        self.create_vector_store(is_law_related=True)
        self.logger.info("Existing documents cleaned and vector stores recreated.")