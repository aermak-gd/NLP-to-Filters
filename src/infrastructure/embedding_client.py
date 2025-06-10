from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union, Optional
from config.settings import EmbeddingConfig


class EmbeddingService:
    def __init__(self, config = EmbeddingConfig):
        self.model_name = config.embedding_model
        self.config = config
        # self.local_model_path = './models/all-MiniLM-L6-v2'
        self._model: Optional[SentenceTransformer] = None
        self._dimension: Optional[int] = None

    @property
    def model(self) -> SentenceTransformer:
        """Lazy loading of the model"""
        if self._model is None:
            try:
                # Try to load from local path first if uncommented
                # self._model = SentenceTransformer(self.local_model_path)
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                raise RuntimeError(f"Failed to load embedding model '{self.model_name}': {e}")
        return self._model

    @property
    def dimension(self) -> int:
        """Lazy loading of dimension"""
        if self._dimension is None:
            self._dimension = self.model.get_sentence_embedding_dimension()
        return self._dimension

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


# Global instance - model will be loaded on first use
embedding_service = EmbeddingService()