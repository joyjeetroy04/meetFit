import os
import faiss
import numpy as np
from typing import Tuple


class FaissVectorStore:
    """
    Simple FAISS wrapper for cosine similarity search.
    Uses IndexFlatIP (inner product) with L2-normalized vectors.
    """

    def __init__(self, dimension: int, index_path: str):
        self.dimension = dimension
        self.index_path = index_path
        self.index: faiss.Index | None = None

    # ==============================
    # BUILD
    # ==============================

    def build(self, embeddings: np.ndarray):
        """
        Build a new FAISS index from embeddings.
        """

        if embeddings is None or len(embeddings) == 0:
            raise ValueError("Embeddings array is empty")

        # Ensure correct dtype and memory layout
        embeddings = np.asarray(embeddings, dtype="float32")
        embeddings = np.ascontiguousarray(embeddings)

        # Ensure 2D
        if embeddings.ndim != 2:
            raise ValueError("Embeddings must be 2D array")

        self.dimension = embeddings.shape[1]

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)

        index = faiss.IndexFlatIP(self.dimension)

        # 🔧 Pylance-safe call
        index.add(embeddings) # type: ignore[arg-type]

        self.index = index
        self.save()

    # ==============================
    # SAVE / LOAD
    # ==============================

    def save(self):
        if self.index is None:
            return
        faiss.write_index(self.index, self.index_path)

    def load(self):
        if not os.path.exists(self.index_path):
            return False
        self.index = faiss.read_index(self.index_path)
        return True

    # ==============================
    # SEARCH
    # ==============================

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (scores, indices)
        """

        if self.index is None:
            raise RuntimeError("FAISS index not loaded")

        if query_vector is None:
            raise ValueError("Query vector is None")

        # Ensure correct dtype and shape
        query_vector = np.asarray(query_vector, dtype="float32")
        query_vector = np.ascontiguousarray(query_vector)

        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        # Normalize for cosine similarity
        faiss.normalize_L2(query_vector)

        # 🔧 Pylance-safe search
        scores, indices = self.index.search(query_vector, top_k) # type: ignore[call-arg]

        return scores, indices