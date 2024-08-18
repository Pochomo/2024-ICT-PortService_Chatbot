from fastapi import APIRouter, HTTPException, UploadFile, File
from app.services.document_loader import HWPLoaderWrapper
from app.services.vector_store import VectorStore
from app.core.config import settings
from app.prompts.port_authority_prompt import PORT_AUTHORITY_PROMPT
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory

import logging

router = APIRouter()

hwp_loader = HWPLoaderWrapper()
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

@router.post("/chat")
async def chat(message: str):
    try:
        if vector_store.vector_store is None:
            raise HTTPException(status_code=400, detail="Vector store is empty. Please upload documents first.")

        llm = ChatOpenAI(temperature=0, openai_api_key=settings.OPENAI_API_KEY)
        memory = ConversationBufferWindowMemory(k=3, memory_key="chat_history", return_messages=True)
        
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vector_store.vector_store.as_retriever(search_kwargs={"k": 5}),
            memory=memory,
            combine_docs_chain_kwargs={"prompt": PORT_AUTHORITY_PROMPT}
        )
        
        response = conversation_chain({"question": message})
        
        return {
            "answer": response['answer'],
            # 'source_documents'가 없을 경우 빈 리스트 반환
            "source_documents": [doc.page_content for doc in response.get('source_documents', [])]
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing your request.")

@router.on_event("startup")
def startup_event():
    try:
        vector_store.load_local("faiss_index")
    except:
        print("No existing index found. Starting with an empty index.")

@router.on_event("shutdown")
def shutdown_event():
    vector_store.save_local("faiss_index")

@router.get("/vector-store-content")
async def get_vector_store_content():
    try:
        if vector_store.vector_store is None:
            return {"message": "Vector store is empty"}
        
        # FAISS doesn't provide a direct way to access all stored vectors
        # So we'll perform a similarity search with an empty query to get some results
        results = vector_store.similarity_search("", k=10)  # Get top 10 results
        
        content = [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            } for doc in results
        ]
        
        return {"vector_store_content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))