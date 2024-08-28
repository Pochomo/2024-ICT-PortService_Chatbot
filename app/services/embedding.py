from sentence_transformers import SentenceTransformer

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # 성능 좋은 모델로 변경

    def get_embedding(self, text):
        return self.model.encode(text, convert_to_tensor=True)
