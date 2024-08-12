import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

class VectorStore:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = None

    def create_vector_store(self, documents):
        self.vector_store = FAISS.from_documents(documents, self.embedding_model)

    def add_documents(self, documents):
        if self.vector_store is None:
            self.create_vector_store(documents)
        else:
            self.vector_store.add_documents(documents)

    def similarity_search(self, query, k=4):
        if self.vector_store is None:
            raise ValueError("Vector store is not initialized")
        return self.vector_store.similarity_search(query, k=k)

    def save_local(self, path):
        if self.vector_store is None:
            raise ValueError("Vector store is not initialized")
        self.vector_store.save_local(path)

    def load_local(self, path):
        if os.path.exists(path):
            self.vector_store = FAISS.load_local(path, self.embedding_model)
        else:
            print(f"No existing index found at {path}. Starting with an empty index.")
            self.vector_store = None