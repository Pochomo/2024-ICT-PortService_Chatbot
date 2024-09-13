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
        self.general_vector_store = None
        self.law_vector_store = None
        self.general_documents = []
        self.law_documents = []
        self.logger = logging.getLogger(__name__)
        self.dimension = None

    def add_documents(self, documents, is_law_related=False):
        target_documents = self.law_documents if is_law_related else self.general_documents
        target_vector_store = self.law_vector_store if is_law_related else self.general_vector_store

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
            
            target_documents.extend(unique_documents)
            self.logger.info(f"Added {len(unique_documents)} unique documents to the {'law' if is_law_related else 'general'} vector store.")
            self.create_vector_store(is_law_related)

    def create_vector_store(self, is_law_related=False):
        target_documents = self.law_documents if is_law_related else self.general_documents
        target_vector_store = self.law_vector_store if is_law_related else self.general_vector_store

        texts = [doc.page_content for doc in target_documents]
        embeddings = self.embedding_model.embed_documents(texts)
        embeddings = np.array(embeddings, dtype=np.float32)

        if self.dimension is None:
            self.dimension = embeddings.shape[1]
        elif embeddings.shape[1] != self.dimension:
            raise ValueError(f"Dimension mismatch: expected {self.dimension}, but got {embeddings.shape[1]}")
        
        new_vector_store = faiss.IndexFlatL2(self.dimension)
        new_vector_store.add(embeddings)
        
        docstore = InMemoryDocstore({i: doc for i, doc in enumerate(target_documents)})
        index_to_docstore_id = {i: i for i in range(len(target_documents))}

        if is_law_related:
            self.law_vector_store = LangchainFAISS(
                index=new_vector_store,
                docstore=docstore,
                index_to_docstore_id=index_to_docstore_id,
                embedding_function=self.embedding_model
            )
        else:
            self.general_vector_store = LangchainFAISS(
                index=new_vector_store,
                docstore=docstore,
                index_to_docstore_id=index_to_docstore_id,
                embedding_function=self.embedding_model
            )

        self.logger.info(f"{'Law' if is_law_related else 'General'} vector store created with {len(target_documents)} documents and dimension {self.dimension}.")

    def similarity_search(self, query, is_law_related=False, k=8):
        target_vector_store = self.law_vector_store if is_law_related else self.general_vector_store
        
        if target_vector_store is None:
            raise ValueError("Vector store is not initialized")
        
        query_embedding = self.embedding_model.embed_query(query)
        query_embedding = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        
        query_dim = query_embedding.shape[1]
        index_dim = target_vector_store.index.d
        self.logger.info(f"Query embedding dimension: {query_dim}, Index dimension: {index_dim}")
        
        if query_dim != index_dim:
            raise ValueError(f"Dimension mismatch: Query embedding dimension {query_dim} does not match FAISS index dimension {index_dim}")
        
        distances, indices = target_vector_store.index.search(query_embedding, k)
        
        # Use the correct method to retrieve documents from the docstore using the index
        results = [target_vector_store.docstore.search(i) for i in indices[0]]
        
        if not results:
            raise ValueError("No results found for the query.")
        
        return results
    def is_law_related(self, text):
        """
        텍스트가 법과 관련이 있는지 확인하는 메소드.
        법 관련 키워드가 포함되어 있는지 여부를 기준으로 판단합니다.
        """
        law_keywords = ["법", "조항", "규정", "제한", "법률", "조례", "규칙", "정관"]
        return any(keyword in text for keyword in law_keywords)

    def save_local(self, path, is_law_related=False):
        target_vector_store = self.law_vector_store if is_law_related else self.general_vector_store

        if target_vector_store is None:
            raise ValueError(f"{'Law' if is_law_related else 'General'} vector store is not initialized")
        
        faiss.write_index(target_vector_store.index, path)
        self.logger.info(f"{'Law' if is_law_related else 'General'} vector store saved to {path}.")

    def load_local(self, path, is_law_related=False):
        if os.path.exists(path):
            new_vector_store = faiss.read_index(path)
            self.logger.info(f"{'Law' if is_law_related else 'General'} vector store loaded from {path}.")
            
            target_documents = self.law_documents if is_law_related else self.general_documents
            docstore = InMemoryDocstore({i: doc for i, doc in enumerate(target_documents)})
            index_to_docstore_id = {i: i for i in range(len(target_documents))}
            
            if is_law_related:
                self.law_vector_store = LangchainFAISS(
                    index=new_vector_store,
                    docstore=docstore,
                    index_to_docstore_id=index_to_docstore_id,
                    embedding_function=self.embedding_model
                )
            else:
                self.general_vector_store = LangchainFAISS(
                    index=new_vector_store,
                    docstore=docstore,
                    index_to_docstore_id=index_to_docstore_id,
                    embedding_function=self.embedding_model
                )
        else:
            self.logger.warning(f"No existing index found at {path}. Starting with an empty index.")
            new_vector_store = faiss.IndexFlatL2(self.dimension) if self.dimension else None

            if is_law_related:
                self.law_vector_store = new_vector_store
            else:
                self.general_vector_store = new_vector_store