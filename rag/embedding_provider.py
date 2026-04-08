import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List

_model_instance = None

class LocalEmbeddingProvider:
    def __init__(self):
        global _model_instance
        if _model_instance is None:
            from sentence_transformers import SentenceTransformer
            _model_instance = SentenceTransformer("all-MiniLM-L6-v2")
        self.model = _model_instance

    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Returns normalized embeddings for cosine similarity search.
        """
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / (norms + 1e-10)

        return embeddings