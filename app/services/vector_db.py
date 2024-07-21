from langchain_community.embeddings import OpenAIEmbeddings
import faiss
import numpy as np
import os

def create_vector_store(documents):
    openai_api_key = os.getenv('OPENAI_API_KEY')
    embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
    embeddings = [embedding_model.embed(doc) for doc in documents]
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))
    return index

def search_vector_store(query, index, k=5):
    openai_api_key = os.getenv('OPENAI_API_KEY')
    embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
    query_vector = embedding_model.embed(query)
    distances, indices = index.search(np.array([query_vector], dtype=np.float32), k)
    return indices
