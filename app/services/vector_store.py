import os
import logging
import re
import hashlib
import chromadb
from collections import Counter
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

class VectorStore:
    def __init__(self):
        # OpenAI 임베딩 사용
        self.embedding_model = OpenAIEmbeddings()
        
        # FAISS 벡터 저장소 (langchain 구현체 사용)
        self.general_faiss = None
        self.law_faiss = None
        
        # ChromaDB 클라이언트 및 컬렉션
        self.chromadb_client = chromadb.Client()
        self.general_collection = None
        self.law_collection = None
        
        # 문서 저장
        self.general_documents = []
        self.law_documents = []
        self.document_hashes = set()
        
        # 키워드 인덱스 (Fusion 검색용)
        self.keyword_index = {}
        
        # 로깅
        self.logger = logging.getLogger(__name__)
        
        # 초기화
        self._initialize_collections()
        
    def _initialize_collections(self):
        """ChromaDB 컬렉션 초기화"""
        try:
            # 컬렉션이 이미 존재하는지 확인하고 존재하면 가져오고, 없으면 생성
            try:
                self.general_collection = self.chromadb_client.get_collection("general_docs")
                self.logger.info("기존 general_docs 컬렉션을 가져왔습니다.")
            except Exception:
                self.general_collection = self.chromadb_client.create_collection("general_docs")
                self.logger.info("새 general_docs 컬렉션을 생성했습니다.")
                
            try:
                self.law_collection = self.chromadb_client.get_collection("law_docs")
                self.logger.info("기존 law_docs 컬렉션을 가져왔습니다.")
            except Exception:
                self.law_collection = self.chromadb_client.create_collection("law_docs")
                self.logger.info("새 law_docs 컬렉션을 생성했습니다.")
                
            self.logger.info("ChromaDB 컬렉션 초기화 완료.")
        except Exception as e:
            self.logger.error(f"ChromaDB 컬렉션 초기화 실패: {str(e)}")

    def clean_text(self, text):
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def hash_document(self, doc):
        cleaned_content = self.clean_text(doc.page_content)
        return hashlib.md5(cleaned_content.encode()).hexdigest()

    def extract_keywords(self, text, min_length=2, max_length=20):
        """텍스트에서 키워드 추출 (간단한 방식)"""
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if min_length <= len(w) <= max_length]

    def build_keyword_index(self, documents, is_law_related=False):
        """키워드 기반 인덱스 구축"""
        prefix = "law" if is_law_related else "general"
        
        for idx, doc in enumerate(documents):
            doc_id = f"{prefix}_{idx}"
            keywords = self.extract_keywords(doc.page_content)
            
            for keyword in keywords:
                if keyword not in self.keyword_index:
                    self.keyword_index[keyword] = []
                if doc_id not in self.keyword_index[keyword]:
                    self.keyword_index[keyword].append(doc_id)
                
        self.logger.info(f"키워드 인덱스 업데이트 완료: {len(self.keyword_index)} 키워드")

    def add_documents(self, documents, is_law_related=False):
        target_documents = self.law_documents if is_law_related else self.general_documents
        collection = self.law_collection if is_law_related else self.general_collection
        unique_documents = []

        for doc in documents:
            doc_hash = self.hash_document(doc)
            if doc_hash not in self.document_hashes:
                doc.page_content = self.clean_text(doc.page_content)
                unique_documents.append(doc)
                self.document_hashes.add(doc_hash)

        if unique_documents:
            # 기존 문서 수 기록
            start_idx = len(target_documents)
            
            # 문서 추가
            target_documents.extend(unique_documents)
            
            # 키워드 인덱스 구축
            self.build_keyword_index(unique_documents, is_law_related)
            
            # ChromaDB에 문서 추가
            try:
                # 문서 추가를 위한 데이터 준비
                chroma_ids = []
                chroma_texts = []
                chroma_metadatas = []
                
                for idx, doc in enumerate(unique_documents):
                    doc_id = f"{start_idx + idx}"
                    chroma_ids.append(doc_id)
                    chroma_texts.append(doc.page_content)
                    meta = getattr(doc, 'metadata', {}) or {}
                    chroma_metadatas.append(meta)
                
                # ChromaDB에 문서 추가
                if collection and chroma_ids:
                    collection.add(
                        ids=chroma_ids,
                        documents=chroma_texts,
                        metadatas=chroma_metadatas
                    )
                    self.logger.info(f"ChromaDB에 {len(chroma_ids)}개 문서 추가 완료")
                
            except Exception as e:
                self.logger.error(f"ChromaDB 문서 추가 실패: {str(e)}")
            
            # FAISS 인덱스 생성 (langchain 구현체 사용)
            self.create_faiss_index(is_law_related)
            
            self.logger.info(f"Added {len(unique_documents)} unique documents to the {'law' if is_law_related else 'general'} vector store.")

    def create_faiss_index(self, is_law_related=False):
        """FAISS 인덱스 생성 - langchain_community.vectorstores의 FAISS 사용"""
        target_documents = self.law_documents if is_law_related else self.general_documents
        
        try:
            # langchain FAISS를 사용하여 인덱스 생성
            faiss_store = FAISS.from_documents(documents=target_documents, embedding=self.embedding_model)
            
            # 인덱스 저장
            if is_law_related:
                self.law_faiss = faiss_store
            else:
                self.general_faiss = faiss_store
                
            self.logger.info(f"{'Law' if is_law_related else 'General'} FAISS index created with {len(target_documents)} documents.")
        except Exception as e:
            self.logger.error(f"FAISS 인덱스 생성 실패: {str(e)}")
            raise

    def faiss_search(self, query, is_law_related=False, k=20):
        """FAISS 검색 수행"""
        faiss_store = self.law_faiss if is_law_related else self.general_faiss
        
        if faiss_store is None:
            store_type = "law" if is_law_related else "general"
            self.logger.error(f"{store_type} FAISS index is not initialized.")
            raise ValueError(f"{store_type.capitalize()} FAISS index is not initialized.")
        
        # langchain FAISS의 similarity_search 메서드 사용
        try:
            results = faiss_store.similarity_search(query, k=k)
            return results
        except Exception as e:
            self.logger.error(f"FAISS 검색 실패: {str(e)}")
            return []

    def chromadb_search(self, query, is_law_related=False, k=8):
        """ChromaDB 검색 수행"""
        collection = self.law_collection if is_law_related else self.general_collection
        
        if collection is None:
            store_type = "law" if is_law_related else "general"
            self.logger.error(f"{store_type} ChromaDB collection is not initialized.")
            return []
        
        
        # 더 올바른 ChromaDB 검색 사용 예시
        try:
            # ChromaDB 기본 검색 수행 - include 매개변수 제거
            results = collection.query(
                query_texts=[query],
                n_results=k
            )
            
            # 결과 변환
            chroma_docs = []
            
            # 결과 구조 확인
            if results and "documents" in results and results["documents"]: #len에는 none이 들어있으면 안됨, documents" 키가 results 딕셔너리에 있는지 확인 
                #results["documents"]가 true인지
                documents = results["documents"][0]
                
                # 메타데이터 처리
                if "metadatas" in results and results["metadatas"]:
                    metadatas = results["metadatas"][0]
                else:
                    metadatas = [{} for _ in range(len(documents))]
                    
                # Document 객체 생성
                for i, doc_text in enumerate(documents):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    chroma_docs.append(Document(page_content=doc_text, metadata=metadata))
            
            return chroma_docs
        
        except Exception as e:
            self.logger.error(f"ChromaDB 검색 실패: {str(e)}")
            return []

    def keyword_search(self, query, is_law_related=False, k=20):
        """키워드 기반 검색"""
        keywords = self.extract_keywords(query)
        if not keywords:
            return []
            
        store_prefix = "law" if is_law_related else "general"
        doc_counts = Counter()
        
        # 각 키워드에 해당하는 문서 집계
        for keyword in keywords:
            if keyword in self.keyword_index:
                for doc_id in self.keyword_index[keyword]:
                    # 도메인에 맞는 문서만 선택
                    if doc_id.startswith(store_prefix):
                        doc_counts[doc_id] += 1
        
        # 관련도 순으로 정렬하여 상위 k개 문서 ID 선택
        top_doc_ids = [doc_id for doc_id, _ in doc_counts.most_common(k)]
        
        # 문서 ID를 실제 문서로 변환
        results = []
        documents = self.law_documents if is_law_related else self.general_documents
        
        for doc_id in top_doc_ids:
            parts = doc_id.split('_')
            if len(parts) == 2 and parts[0] == store_prefix:
                try:
                    idx = int(parts[1])
                    if 0 <= idx < len(documents):
                        results.append(documents[idx])
                except ValueError:
                    continue
        
        return results

    def fusion_search(self, query, is_law_related=False, k=8):
        """
        Fusion 검색 (ChromaDB와 키워드 검색의 결합)
        1. ChromaDB로 검색
        2. FAISS로 거리 기반 검색 (백업)
        3. 키워드 검색 수행
        4. 결과 병합
        """
        try:
            # 1. ChromaDB 검색
            chroma_results = self.chromadb_search(query, is_law_related=is_law_related, k=k*2)
            
            # 2. FAISS 검색 (ChromaDB가 실패하거나 결과가 부족한 경우)
            vector_results = []
            if len(chroma_results) < k:
                vector_results = self.faiss_search(query, is_law_related=is_law_related, k=k*2)
            
            # 3. 키워드 검색 수행
            keyword_results = self.keyword_search(query, is_law_related=is_law_related, k=k)
            
            # 4. 결과 병합 (중복 제거)
            seen_hashes = set()
            merged_results = []
            
            # 먼저 ChromaDB 결과 추가 (가장 관련성 높은 결과)
            for doc in chroma_results:
                doc_hash = self.hash_document(doc)
                if doc_hash not in seen_hashes:
                    merged_results.append(doc)
                    seen_hashes.add(doc_hash)
            
            # FAISS 결과 추가
            for doc in vector_results:
                doc_hash = self.hash_document(doc)
                if doc_hash not in seen_hashes:
                    merged_results.append(doc)
                    seen_hashes.add(doc_hash)
            
            # 키워드 검색 결과 추가
            for doc in keyword_results:
                doc_hash = self.hash_document(doc)
                if doc_hash not in seen_hashes:
                    merged_results.append(doc)
                    seen_hashes.add(doc_hash)
            
            # 최종 결과는 k개로 제한
            return merged_results[:k]
        except Exception as e:
            self.logger.error(f"Fusion 검색 실패: {str(e)}")
            # 에러 발생 시, 간단한 키워드 검색으로 대체
            return self.keyword_search

    # similarity_search 함수 (마지막 부분이 완성되지 않음)
    def similarity_search(self, query, is_law_related=False, k=8, use_fusion=True):
        """통합 검색 인터페이스"""
        if use_fusion:
            # Fusion 검색 사용
            results = self.fusion_search(query, is_law_related=is_law_related, k=k)
        else:
            # 단일 검색 방법 사용
            chroma_results = self.chromadb_search(query, is_law_related=is_law_related, k=k)
            if chroma_results:
                results = chroma_results
            else:
                results = self.faiss_search(query, is_law_related=is_law_related, k=k)

        if not results:
            self.logger.warning("No results found for the query.")
            return []

        return results

    # as_retriever 함수 
    def as_retriever(self, is_law_related=False, k=8):
        """LangChain 호환 Retriever 반환"""
        class CustomRetriever:
            def __init__(self, parent, is_law_related, k):
                self.parent = parent
                self.is_law_related = is_law_related
                self.k = k
                
            def get_relevant_documents(self, query):
                return self.parent.similarity_search(
                    query, 
                    is_law_related=self.is_law_related, 
                    k=self.k
                )
        
        return CustomRetriever(self, is_law_related, k)

    # save_local 함수 (LangChain FAISS 사용)
    def save_local(self, path):
        """FAISS 인덱스 저장"""
        self.logger.warning("Saving FAISS indexes locally.")
        if self.general_faiss:
            self.general_faiss.save_local(f"{path}_general")
        if self.law_faiss:
            self.law_faiss.save_local(f"{path}_law")
        self.logger.warning("Note: Chroma data is not being saved in this operation.")

    # load_local 함수 (LangChain FAISS 사용)
    def load_local(self, path):
        """FAISS 인덱스 로드"""
        self.logger.warning("Loading FAISS indexes from local storage.")
        self.general_faiss = FAISS.load_local(f"{path}_general", self.embedding_model)
        self.law_faiss = FAISS.load_local(f"{path}_law", self.embedding_model)
        self.logger.warning("Note: Chroma data is not being loaded in this operation.")

    # clean_existing_documents 함수 
    def clean_existing_documents(self):
        self.document_hashes.clear()
        self.keyword_index.clear()
        
        # ChromaDB 컬렉션 초기화
        try:
            self.chromadb_client.delete_collection("general_docs")
            self.chromadb_client.delete_collection("law_docs")
            self._initialize_collections()
        except Exception as e:
            self.logger.error(f"ChromaDB 컬렉션 초기화 실패: {str(e)}")
        
        for doc_list, is_law in [(self.general_documents, False), (self.law_documents, True)]:
            unique_docs = []
            for doc in doc_list:
                doc_hash = self.hash_document(doc)
                if doc_hash not in self.document_hashes:
                    doc.page_content = self.clean_text(doc.page_content)
                    unique_docs.append(doc)
                    self.document_hashes.add(doc_hash)
            doc_list[:] = unique_docs
            
            # 키워드 인덱스 재구축
            self.build_keyword_index(unique_docs, is_law_related=is_law)

        # 벡터 저장소 재생성
        self.create_faiss_index(is_law_related=False)
        self.create_faiss_index(is_law_related=True)
        
        self.logger.info("Existing documents cleaned and vector stores recreated.")