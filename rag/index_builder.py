import os
import json
from typing import List, Dict, Any

from rag.embedding_provider import LocalEmbeddingProvider
from rag.vector_store import FaissVectorStore


class MeetingIndexBuilder:
    """
    Builds FAISS index from chunk files.
    """

    def __init__(self, meeting_dir: str):
        self.meeting_dir = meeting_dir
        self.embedder = LocalEmbeddingProvider()

    # ==========================
    # LIVE INDEX
    # ==========================

    def build_live_index(self):
        chunk_path = os.path.join(self.meeting_dir, "chunks_live.json")
        index_path = os.path.join(self.meeting_dir, "vector_live.index")

        chunks = self._load_chunks(chunk_path)
        if not chunks:
            return False

        texts = [c["text"] for c in chunks]

        embeddings = self.embedder.embed_texts(texts)
        dimension = embeddings.shape[1]

        store = FaissVectorStore(dimension, index_path)
        store.build(embeddings)

        return True

    # ==========================
    # FINAL INDEX
    # ==========================

    def build_final_index(self):
        chunk_path = os.path.join(self.meeting_dir, "chunks_final.json")
        index_path = os.path.join(self.meeting_dir, "vector_final.index")

        chunks = self._load_chunks(chunk_path)
        if not chunks:
            return False

        texts = [c["text"] for c in chunks]

        embeddings = self.embedder.embed_texts(texts)
        dimension = embeddings.shape[1]

        store = FaissVectorStore(dimension, index_path)
        store.build(embeddings)

        return True

    # ==========================

    def _load_chunks(self, path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)