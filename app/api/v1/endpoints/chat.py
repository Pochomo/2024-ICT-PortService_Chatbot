from fastapi import APIRouter, HTTPException, UploadFile, Depends, File
from langchain_community.document_loaders import PyPDFLoader
from app.services.vector_store import VectorStore
from app.prompts.port_authority_prompt import PORT_AUTHORITY_PROMPT
from app.core.config import settings
from langchain.chains.retrieval import create_retrieval_chain
from pydantic import SecretStr
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai import ChatOpenAI
from langchain.prompts import load_prompt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import models, database
from urllib.parse import unquote
from langdetect import detect
from deep_translator import GoogleTranslator
import tempfile
import logging
from typing import List, Dict, Any
import os

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

router = APIRouter()

vector_store = VectorStore()

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str

translator_ko = GoogleTranslator(source='auto', target='ko')
translator_en = GoogleTranslator(source='auto', target='en')

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

@router.post("/upload-pdf")
async def upload_pdf(files: List[UploadFile] = File(...)):
    logger.info(f"Received {len(files)} files")
    documents = []

    for file in files:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_path = temp_file.name
                temp_file.write(await file.read())

            if file.filename is None or not file.filename.lower().endswith('.pdf'):
                logger.warning(f"Invalid file type: {file.filename}")
                continue

            # PDF 문서 로드 및 분리
            pdf_loader = PyPDFLoader(temp_path)
            new_documents = pdf_loader.load_and_split()
            
            if not new_documents:
                logger.error(f"No documents were extracted from {file.filename}.")
                continue

            # 파일 이름에 'law'가 포함되어 있는지 확인
            is_law = 'law' in file.filename.lower()
            
            # 벡터 저장소에 문서 추가
            vector_store.add_documents(new_documents, is_law_related=is_law)
            
            logger.info(f"Processed {len(new_documents)} documents from {file.filename}. Is law related: {is_law}")
            documents.extend(new_documents)
        
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    if not documents:
        raise HTTPException(status_code=500, detail="No valid documents were extracted from any of the files.")

    # 기존 문서 정제 및 중복 제거
    vector_store.clean_existing_documents()

    return {"message": f"{len(files)} files uploaded and processed successfully"}

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # 메시지 언어 감지 및 한국어 번역
        input_language = detect(request.message)
        translated_text = translator_ko.translate(request.message) if input_language != 'ko' else request.message

        # 질문이 법률 관련인지 확인
        law_keywords = ["법", "규율", "조항", "규정", "법적", "항만공사법", "조례"]
        is_law_related = any(keyword in translated_text for keyword in law_keywords)

        # 벡터 저장소 선택 및 검색
        docs = []
        if is_law_related and vector_store.law_vector_store:
            law_retriever = vector_store.law_vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})
            docs = law_retriever.get_relevant_documents(translated_text)

        # 법률 관련 문서가 충분하지 않으면 일반 벡터 저장소에서도 검색
        if len(docs) < 2 and vector_store.general_vector_store:
            general_retriever = vector_store.general_vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})
            general_docs = general_retriever.get_relevant_documents(translated_text)
            docs.extend(general_docs)

        if not docs:
            return {"answer": "죄송합니다. 관련된 정보를 찾을 수 없습니다.", "is_law_related": is_law_related}

        # OPENAI API 키를 가져옴
        api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None
        if api_key is None:
            raise HTTPException(status_code=500, detail="OpenAI API key is not set.")

        # RAG 체인 설정 및 실행
        rag_chain = (
            {"context": RunnablePassthrough() | (lambda x: format_docs(docs)), "question": RunnablePassthrough()}
            | PORT_AUTHORITY_PROMPT
            | ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5, api_key=SecretStr(api_key))
            | StrOutputParser()
        )

        response = rag_chain.invoke(translated_text)

        # 응답 포맷팅
        formatted_response = "\n\n".join(paragraph.strip() for paragraph in response.split('\n') if paragraph.strip())

        # 응답을 원래 언어로 번역
        translated_response = translator_en.translate(formatted_response) if input_language != 'ko' else formatted_response

        return {
            "answer": translated_response,
            "is_law_related": is_law_related
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")
    
@router.get("/check-vector-store")
async def check_vector_store(is_law_related: bool = False):
    try:
        target_vector_store = vector_store.law_vector_store if is_law_related else vector_store.general_vector_store
        target_documents = vector_store.law_documents if is_law_related else vector_store.general_documents

        if target_vector_store is None:
            return {"message": f"{'Law' if is_law_related else 'General'} vector store is empty"}

        seen_contents = set()
        content = []

        for doc in target_documents:
            if doc.page_content not in seen_contents:
                seen_contents.add(doc.page_content)
                content.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })

        if not content:
            return {"message": "No documents found in the vector store"}

        return {
            "message": f"{'Law' if is_law_related else 'General'} vector store contains documents",
            "vector_store_content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.on_event("shutdown")
def shutdown_event():
    vector_store.save_local("faiss_index")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/get-info")
async def get_info(button_name: str, db: Session = Depends(get_db)):
    button_name = unquote(button_name)
    try:
        information = db.query(models.Information).filter(models.Information.button_name == button_name).first()
        
        if not information:
            raise HTTPException(status_code=404, detail="Information not found")
        
        return {
            "message": information.response_text,
            "link": information.link
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/endpoint")
async def get_info_by_title(infoType: str, db: Session = Depends(get_db)):
    try:
        information = db.query(models.Information).filter(models.Information.title == infoType).first()
        
        if not information:
            raise HTTPException(status_code=404, detail="Information not found")
        
        return {
            "message": information.content,
            "options": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")  