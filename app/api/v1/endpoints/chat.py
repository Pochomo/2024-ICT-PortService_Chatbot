from fastapi import APIRouter, HTTPException, UploadFile, Depends, File
from app.services.document_loader import PDFLoader
from app.services.vector_store import VectorStore
from app.core.config import settings
from app.prompts.port_authority_prompt import PORT_AUTHORITY_PROMPT
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import models, database
from urllib.parse import unquote
from langdetect import detect
from deep_translator import GoogleTranslator
import tempfile
import logging
from typing import List
import numpy as np

router = APIRouter()

pdf_loader = PDFLoader()
vector_store = VectorStore()

logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str

translator_ko = GoogleTranslator(source='auto', target='ko')
translator_en = GoogleTranslator(source='auto', target='en')

@router.post("/upload-pdf")
async def upload_pdf(files: List[UploadFile] = File(...)):
    logger.info(f"Received {len(files)} files")
    documents = []

    for file in files:
        try:
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_path = temp_file.name
                temp_file.write(await file.read())
            
            if not file.filename.lower().endswith('.pdf'):
                logger.warning(f"Invalid file type: {file.filename}")
                continue  # 유효하지 않은 파일은 건너뜁니다.

            new_documents = pdf_loader.load_and_split(temp_path)
            
            if not new_documents:
                logger.error(f"No documents were extracted from {file.filename}.")
                continue  # 문서를 추출하지 못한 경우 건너뜁니다.

            for doc in new_documents:
                is_law = pdf_loader.is_law_related(doc.page_content)
                vector_store.add_documents([doc], is_law_related=is_law)
            
            logger.info(f"Processed {len(new_documents)} documents from {file.filename}")
            documents.extend(new_documents)
        
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}", exc_info=True)
            continue  # 에러가 발생한 파일은 건너뜁니다.

    if not documents:
        raise HTTPException(status_code=500, detail="No valid documents were extracted from any of the files.")

    return {"message": f"{len(files)} files uploaded and processed successfully"}


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Load vector stores if not already loaded
        if vector_store.general_vector_store is None and vector_store.documents:
            vector_store.create_vector_store()

        input_language = detect(request.message)
        translated_text = translator_ko.translate(request.message) if input_language != 'ko' else request.message

        # Check if the query is law-related
        is_law = vector_store.is_law_related(translated_text)

        # Perform the similarity search on the appropriate vector store
        results = vector_store.similarity_search(translated_text, is_law_related=is_law, k=10)
        
        # Use the appropriate vector store (general or law) to create the retriever
        target_vector_store = vector_store.law_vector_store if is_law else vector_store.general_vector_store
        retriever = target_vector_store.as_retriever()

        # Use the ConversationalRetrievalChain to generate a response
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(temperature=0.5, openai_api_key=settings.OPENAI_API_KEY),
            retriever=retriever,    
            memory=ConversationBufferWindowMemory(k=3, memory_key="chat_history", return_messages=True),
            combine_docs_chain_kwargs={"prompt": PORT_AUTHORITY_PROMPT}
        )

        response = conversation_chain.invoke({"question": translated_text})

        translated_response = translator_en.translate(response['answer']) if input_language != 'ko' else response['answer']

        return {
            "answer": translated_response,
            "source_documents": [doc.page_content for doc in response.get('source_documents', [])]
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")


@router.on_event("shutdown")
def shutdown_event():
    vector_store.save_local("faiss_index")

@router.get("/check-vector-store")
async def check_vector_store(is_law_related: bool = False):
    try:
        # 선택된 벡터 스토어를 확인
        if is_law_related:
            target_vector_store = vector_store.law_vector_store
            target_documents = vector_store.law_documents
        else:
            target_vector_store = vector_store.general_vector_store
            target_documents = vector_store.general_documents

        if target_vector_store is None:
            return {"message": f"{'Law' if is_law_related else 'General'} vector store is empty"}

        # 중복 제거를 위해 집합을 사용
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




def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/get-info")
async def get_info(button_name: str, db: Session = Depends(get_db)):
    button_name = unquote(button_name)  # URL 인코딩된 문자열을 디코딩
    try:
        # MySQL에서 button_name과 일치하는 정보를 검색
        information = db.query(models.Information).filter(models.Information.button_name == button_name).first()
        
        if not information:
            raise HTTPException(status_code=404, detail="Information not found")
        
        return {
            "message": information.response_text,
            "link": information.link  # 필요시 링크도 반환 가능
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/endpoint")
async def get_info_by_title(infoType: str, db: Session = Depends(get_db)):
    try:
        # MySQL에서 infoType과 일치하는 정보를 검색
        information = db.query(models.Information).filter(models.Information.title == infoType).first()
        
        if not information:
            raise HTTPException(status_code=404, detail="Information not found")
        
        return {
            "message": information.content,
            "options": []  # 추가적인 옵션이 있다면 여기에 추가 가능
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")