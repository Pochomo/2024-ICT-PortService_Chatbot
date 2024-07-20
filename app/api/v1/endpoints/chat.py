from fastapi import APIRouter, HTTPException
from app.services.vector_db import create_vector_store, search_vector_store
import os

router = APIRouter()

# Load documents (you can load documents from a database or other source)
documents = [
    "This is the first document.",
    "This is the second document.",
    "And here is the third document."
]

# Create the vector store
index = create_vector_store(documents)

@router.post("/chat")
async def chat(query: str):
    try:
        indices = search_vector_store(query, index)
        results = [documents[i] for i in indices[0]]
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
