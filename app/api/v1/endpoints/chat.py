from fastapi import APIRouter, HTTPException, UploadFile, Depends, File
from app.services.document_loader import HWPLoader
from app.services.vector_store import VectorStore
from app.core.config import settings
from app.prompts.port_authority_prompt import PORT_AUTHORITY_PROMPT
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db import models, database
from urllib.parse import unquote
from langdetect import detect
from deep_translator import GoogleTranslator

import logging

router = APIRouter()

hwp_loader = HWPLoader()
vector_store = VectorStore()

logger = logging.getLogger(__name__)

@router.post("/upload-hwp")
async def upload_hwp(file: UploadFile = File(...)):
    logger.info(f"Received file: {file.filename}")
    try:
        content = await file.read()
        logger.info(f"File size: {len(content)} bytes")
        if not file.filename.lower().endswith(('.hwp', '.hwpx')):
            logger.warning(f"Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only .hwp and .hwpx files are allowed")
        documents = await hwp_loader.load_and_split(content)
        logger.info(f"Processed {len(documents)} documents")
        vector_store.add_documents(documents)
        logger.info("Documents added to vector store")
        return {"message": f"{file.filename} uploaded and processed successfully"}
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    message: str

translator_ko = GoogleTranslator(source='auto', target='ko')
translator_en = GoogleTranslator(source='auto', target='en')

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        if vector_store.vector_store is None:
            logger.error("Vector store is empty. Please upload documents first.")
            raise HTTPException(status_code=400, detail="Vector store is empty. Please upload documents first.")

        input_language = detect(request.message)
        logger.info(f"Detected language: {input_language}")

        if input_language == 'ko':
            translated_text = request.message
        else:
            translated_text = translator_ko.translate(request.message)

        llm = ChatOpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)
        memory = ConversationBufferWindowMemory(k=3, memory_key="chat_history", return_messages=True)

        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vector_store.vector_store.as_retriever(search_kwargs={"k": 5}),
            memory=memory,
            combine_docs_chain_kwargs={"prompt": PORT_AUTHORITY_PROMPT}
        )

        logger.info(f"Running conversation chain with question: {translated_text}")
        response = conversation_chain({"question": translated_text})

        if input_language == 'ko':
            translated_response = response['answer']
        else:
            translated_response = translator_en.translate(response['answer'])

        logger.info(f"Response generated: {translated_response}")

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
async def check_vector_store():
    try:
        if vector_store.vector_store is None:
            return {"message": "Vector store is empty"}
        
        # 모든 문서를 출력해봅니다.
        results = vector_store.similarity_search("", k=100)  # 최대 100개의 문서를 가져옵니다.
        
        content = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            } for doc in results
        ]
        
        return {"vector_store_content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.get("/vector-store-content")
# async def get_vector_store_content():
#     try:
#         if vector_store.vector_store is None:
#             return {"message": "Vector store is empty"}
        
#         # FAISS doesn't provide a direct way to access all stored vectors
#         # So we'll perform a similarity search with an empty query to get some results
#         results = vector_store.similarity_search("", k=10)  # Get top 10 results
        
#         content = [
#             {
#                 "content": doc.page_content,
#                 "metadata": doc.metadata
#             } for doc in results
#         ]
        
#         return {"vector_store_content": content}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    
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