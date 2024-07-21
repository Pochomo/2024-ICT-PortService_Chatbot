import openai
from app.core.config import settings

openai.api_key = settings.OPENAI_API_KEY

def get_embedding(text: str):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response['data'][0]['embedding']
