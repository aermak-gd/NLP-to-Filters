from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
from config.settings import EmbeddingConfig


class EmbeddingService:
    def __init__(self, config = EmbeddingConfig):
        self.model_name = config.embedding_model
        # self.local_model_path = './models/all-MiniLM-L6-v2'
        # self.model = SentenceTransformer(self.local_model_path)
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_documents(self, text: Union[str, List[str]]) -> np.ndarray:
        """Generate embeddings for text or list of texts"""
        if isinstance(text, str):
            text = [text]

        embeddings = self.model.encode(text, convert_to_numpy=True)
        return embeddings if len(embeddings) > 1 else embeddings[0]

    def embed_batch(self, texts: List[str], batch_size: int = 8) -> List[np.ndarray]:
        """Embed multiple texts in batches"""
        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
        )

        return [embedding for embedding in embeddings]


embedding_service = EmbeddingService()