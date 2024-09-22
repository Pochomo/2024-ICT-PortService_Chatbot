import os
import logging
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class VectorStore:
    def __init__(self):
        # OpenAI 임베딩 모델 초기화
        self.embedding_model = OpenAIEmbeddings()
        self.general_vector_store = None
        self.law_vector_store = None
        self.general_documents = []
        self.law_documents = []
        self.logger = logging.getLogger(__name__)

    def add_documents(self, documents, is_law_related=False):
        target_documents = self.law_documents if is_law_related else self.general_documents
        unique_documents = []
        seen = set()

        for doc in documents:
            content_hash = hash(doc.page_content.strip().lower())
            if content_hash not in seen:
                unique_documents.append(doc)
                seen.add(content_hash)
        
        if unique_documents:
            target_documents.extend(unique_documents)
            self.logger.info(f"Added {len(unique_documents)} unique documents to the {'law' if is_law_related else 'general'} vector store.")
            # 벡터 스토어 생성
            self.create_vector_store(is_law_related)

    def create_vector_store(self, is_law_related=False):
        target_documents = self.law_documents if is_law_related else self.general_documents

        # Chroma 벡터 스토어 생성
        vector_store = Chroma.from_documents(documents=target_documents, embedding=self.embedding_model)
        
        if is_law_related:
            self.law_vector_store = vector_store
        else:
            self.general_vector_store = vector_store

        self.logger.info(f"{'Law' if is_law_related else 'General'} vector store created with {len(target_documents)} documents.")

    def as_retriever(self, is_law_related=False, k=8):
        # 벡터 스토어를 선택
        target_vector_store = self.law_vector_store if is_law_related else self.general_vector_store
        
        # 벡터 스토어가 초기화되어 있는지 확인
        if target_vector_store is None:
            store_type = "law" if is_law_related else "general"
            self.logger.error(f"{store_type.capitalize()} vector store is not initialized.")
            raise ValueError(f"{store_type.capitalize()} vector store is not initialized.")
        
        # 리트리버 생성
        return target_vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})

    def similarity_search(self, query, is_law_related=False, k=8):
        target_vector_store = self.law_vector_store if is_law_related else self.general_vector_store
        
        if target_vector_store is None:
            raise ValueError("Vector store is not initialized")
        
        # Perform the similarity search directly using the retriever
        retriever = target_vector_store.as_retriever(search_kwargs={"k": k})
        docs = retriever.get_relevant_documents(query)
        
        if not docs:
            raise ValueError("No results found for the query.")
        
        return docs

    def is_law_related(self, text):
        law_keywords = ["법", "조항", "규정", "제한", "법률", "조례", "규칙", "정관"]
        return any(keyword in text for keyword in law_keywords)

    def save_local(self, path, is_law_related=False):
        # Chroma는 기본적으로 별도의 저장 방법을 제공하지 않으므로 생략하거나 필요할 경우 로컬 저장소 옵션을 구현
        self.logger.warning("Chroma does not support direct save/load operations like FAISS.")

    def load_local(self, path, is_law_related=False):
        # Chroma 벡터 스토어는 로컬에서 바로 불러오는 옵션이 없습니다. 필요 시 다시 임베딩을 통해 생성 필요
        self.logger.warning("Chroma does not support direct save/load operations like FAISS.")
