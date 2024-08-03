from langchain_community.embeddings import OpenAIEmbeddings
import faiss
import numpy as np
import os

# 글로벌 변수로 FAISS 인덱스 설정
index = None

def create_vector_store(documents):
    global index
    openai_api_key = os.getenv('OPENAI_API_KEY')
    embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
    embeddings = [embedding_model.embed(doc) for doc in documents]
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))
    return index

def search_vector_store(query, k=5):
    global index
    openai_api_key = os.getenv('OPENAI_API_KEY')
    embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
    query_vector = embedding_model.embed(query)
    distances, indices = index.search(np.array([query_vector], dtype=np.float32), k)
    return indices

def save_vector(data):
    # 벡터를 저장하는 로직
    # 예시로 SQLite를 사용해 봅니다.
    import sqlite3
    conn = sqlite3.connect('vectors.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS vectors
                 (id INTEGER PRIMARY KEY, vector BLOB)''')
    c.execute('INSERT INTO vectors (vector) VALUES (?)', (data,))
    conn.commit()
    conn.close()

def get_all_vectors():
    # 저장된 모든 벡터를 조회하는 로직
    import sqlite3
    conn = sqlite3.connect('vectors.db')
    c = conn.cursor()
    c.execute('SELECT * FROM vectors')
    results = c.fetchall()
    conn.close()
    return results
