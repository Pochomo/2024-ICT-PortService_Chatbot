from fastapi import APIRouter, HTTPException, UploadFile, Depends, File
from app.services.document_loader import PDFLoader
from app.services.vector_store import VectorStore
from app.prompts.port_authority_prompt import PORT_AUTHORITY_PROMPT
from app.core.config import settings
from langchain.chains import create_retrieval_chain
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
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

router = APIRouter()

pdf_loader = PDFLoader()
vector_store = VectorStore()

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str

translator_ko = GoogleTranslator(source='auto', target='ko')
translator_en = GoogleTranslator(source='auto', target='en')

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# PDF 업로드 및 벡터 저장소에 저장하는 로직
@router.post("/upload-pdf")
async def upload_pdf(files: List[UploadFile] = File(...)):
    logger.info(f"Received {len(files)} files")
    documents = []

    for file in files:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_path = temp_file.name
                temp_file.write(await file.read())

            if file.filename is None or not file.filename.lower().endswith('.pdf'):
                logger.warning(f"Invalid file type: {file.filename}")
                continue

            # PDF 문서 로드 및 분리
            new_documents = pdf_loader.load_and_split(temp_path)
            
            if not new_documents:
                logger.error(f"No documents were extracted from {file.filename}.")
                continue

            # 법 관련 문서인지 판단하여 벡터 저장소에 추가
            for doc in new_documents:
                is_law = pdf_loader.is_law_related(doc.page_content)
                vector_store.add_documents([doc], is_law_related=is_law)
            
            logger.info(f"Processed {len(new_documents)} documents from {file.filename}")
            documents.extend(new_documents)
        
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
            continue

    if not documents:
        raise HTTPException(status_code=500, detail="No valid documents were extracted from any of the files.")

    return {"message": f"{len(files)} files uploaded and processed successfully"}

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # 메시지 언어 감지 및 한국어 번역
        input_language = detect(request.message)
        translated_text = translator_ko.translate(request.message) if input_language != 'ko' else request.message

        # 질의가 법 관련인지 확인
        is_law = vector_store.is_law_related(translated_text)
        logger.info(f"Query classified as law-related: {is_law}")

        # 벡터 저장소에서 리트리버 생성 (search_type과 k 설정)
        target_vector_store = vector_store.law_vector_store if is_law else vector_store.general_vector_store
        logger.info(f"Using {'law' if is_law else 'general'} vector store")

        # target_vector_store가 None인지 확인
        if target_vector_store is None:
            raise HTTPException(status_code=500, detail="Target vector store is not initialized.")

        # as_retriever 메서드가 존재하는지 확인
        if not hasattr(target_vector_store, 'as_retriever'):
            raise HTTPException(status_code=500, detail="The target vector store does not have 'as_retriever' method.")

        retriever = target_vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 6})

        # OPENAI API 키를 가져옴 (SecretStr 타입에서 실제 값 추출)
        api_key = settings.OPENAI_API_KEY.get_secret_value() if settings.OPENAI_API_KEY else None

        # RAG 체인 설정
        if api_key is None:
            raise HTTPException(status_code=500, detail="OpenAI API key is not set.")

        # ChatOpenAI에 문자열 값 전달
        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | PORT_AUTHORITY_PROMPT
            | ChatOpenAI(model="gpt-4", temperature=0.5, api_key=SecretStr(api_key))
            | StrOutputParser()
        )

        # 실시간으로 체인 실행 (스트리밍)
        response = ""
        for chunk in rag_chain.stream(translated_text):
            response += chunk
            print(chunk, end="", flush=True)

        # 응답을 원래 언어로 번역
        translated_response = translator_en.translate(response) if input_language != 'ko' else response

        return {
            "answer": translated_response,
            "is_law_related": is_law
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

# 벡터 저장소 상태 확인 엔드포인트
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
