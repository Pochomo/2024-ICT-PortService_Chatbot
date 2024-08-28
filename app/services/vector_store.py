import os
import numpy as np
import faiss  # FAISS 라이브러리 직접 사용
import logging
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS as LangchainFAISS
from langchain_community.docstore.in_memory import InMemoryDocstore

class VectorStore:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-MiniLM-L6-v2")
        self.vector_store = None
        self.documents = []
        self.logger = logging.getLogger(__name__)
        self.dimension = None

    def add_documents(self, documents):
        unique_documents = []
        seen = set()

        for doc in documents:
            content_hash = hash(doc.page_content.strip().lower())
            if content_hash not in seen:
                unique_documents.append(doc)
                seen.add(content_hash)
        
        if unique_documents:
            embeddings = self.embedding_model.embed_documents([doc.page_content for doc in unique_documents])
            embeddings = np.array(embeddings, dtype=np.float32)
            
            if self.dimension is None:
                self.dimension = embeddings.shape[1]
            elif embeddings.shape[1] != self.dimension:
                raise ValueError(f"Dimension mismatch: expected {self.dimension}, but got {embeddings.shape[1]}")
            
            self.documents.extend(unique_documents)
            self.logger.info(f"Added {len(unique_documents)} unique documents to the vector store.")
            self.create_vector_store()

    def create_vector_store(self):
        texts = [doc.page_content for doc in self.documents]
        embeddings = self.embedding_model.embed_documents(texts)
        embeddings = np.array(embeddings, dtype=np.float32)

        if self.dimension is None:
            self.dimension = embeddings.shape[1]
        elif embeddings.shape[1] != self.dimension:
            raise ValueError(f"Dimension mismatch: expected {self.dimension}, but got {embeddings.shape[1]}")
        
        self.vector_store = faiss.IndexFlatL2(self.dimension)
        self.vector_store.add(embeddings)
        
        docstore = InMemoryDocstore({i: doc for i, doc in enumerate(self.documents)})
        index_to_docstore_id = {i: i for i in range(len(self.documents))}

        self.langchain_vector_store = LangchainFAISS(
            index=self.vector_store,
            docstore=docstore,
            index_to_docstore_id=index_to_docstore_id,
            embedding_function=self.embedding_model
        )

        self.logger.info(f"Vector store created with {len(self.documents)} documents and dimension {self.dimension}.")

    def similarity_search(self, query, k=8):
        if self.vector_store is None:
            raise ValueError("Vector store is not initialized")
        
        query_embedding = self.embedding_model.embed_query(query)
        query_embedding = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        
        query_dim = query_embedding.shape[1]
        index_dim = self.vector_store.d
        self.logger.info(f"Query embedding dimension: {query_dim}, Index dimension: {index_dim}")
        
        if query_dim != index_dim:
            raise ValueError(f"Dimension mismatch: Query embedding dimension {query_dim} does not match FAISS index dimension {index_dim}")
        
        distances, indices = self.vector_store.search(query_embedding, k)
        
        results = [self.documents[idx] for idx in indices[0]]
        
        if not results:
            raise ValueError("No results found for the query.")
        
        return results

    def save_local(self, path):
        if self.vector_store is None:
            raise ValueError("Vector store is not initialized")
        
        faiss.write_index(self.vector_store, path)
        self.logger.info(f"Vector store saved to {path}.")

    def load_local(self, path):
        if os.path.exists(path):
            self.vector_store = faiss.read_index(path)
            self.logger.info(f"Vector store loaded from {path}.")
            
            docstore = InMemoryDocstore({i: doc for i, doc in enumerate(self.documents)})
            index_to_docstore_id = {i: i for i in range(len(self.documents))}
            
            self.langchain_vector_store = LangchainFAISS(
                index=self.vector_store,
                docstore=docstore,
                index_to_docstore_id=index_to_docstore_id,
                embedding_function=self.embedding_model
            )
        else:
            self.logger.warning(f"No existing index found at {path}. Starting with an empty index.")
            self.vector_store = faiss.IndexFlatL2(self.dimension) if self.dimension else None
