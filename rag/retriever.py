import os
import json
from typing import List, Dict, Any, Optional

from rag.embedding_provider import LocalEmbeddingProvider
from rag.vector_store import FaissVectorStore
from rank_bm25 import BM25Okapi # 🔥 NEW: Keyword Search Engine

_embedder_singleton = None
 
class MeetingRetriever:
    """
    Handles Hybrid Retrieval (FAISS + BM25) from a single meeting.
    """

    def __init__(self, meeting_dir: str, version: str = "live"):
        self.meeting_dir = meeting_dir
        self.version = version
        self._store: Optional[FaissVectorStore] = None
        self._bm25: Optional[BM25Okapi] = None
        self._chunks = []
        
        global _embedder_singleton
        if _embedder_singleton is None:
           _embedder_singleton = LocalEmbeddingProvider()
        self.embedder = _embedder_singleton

        self.chunk_path = os.path.join(meeting_dir, f"chunks_{version}.json")
        self.index_path = os.path.join(meeting_dir, f"vector_{version}.index")

    def _lazy_load(self) -> bool:
        """Loads chunks, FAISS, and builds BM25 only when first queried to save RAM."""
        if self._chunks and self._store and self._bm25:
            return True

        if not os.path.exists(self.chunk_path) or not os.path.exists(self.index_path):
            print(f"⚠️ [Retriever] Missing index/chunks for {os.path.basename(self.meeting_dir)}")
            return False

        with open(self.chunk_path, "r", encoding="utf-8") as f:
            self._chunks = json.load(f)

        if not self._chunks:
            return False

        # 1. Init FAISS (Dense)
        dimension = 384  # MiniLM-L6-v2 dimension
        if self._store is None:
            store = FaissVectorStore(dimension, self.index_path)
            if not store.load(): 
                return False
            self._store = store

        # 2. Init BM25 (Sparse)
        # We tokenize the chunks by lowercasing and splitting by space
        if self._bm25 is None:
            tokenized_corpus = [chunk.get("text", "").lower().split(" ") for chunk in self._chunks]
            self._bm25 = BM25Okapi(tokenized_corpus)

        return True

    def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Executes a Hybrid Search and returns a deduplicated pool of best chunks."""
        if not self._lazy_load() or self._bm25 is None or self._store is None:
            return []

        bm25 = self._bm25

        # ==========================================
        # 1. FAISS DENSE SEARCH (Semantic Meaning)
        # ==========================================
        query_vec = self.embedder.embed_texts([query])
        faiss_scores, faiss_indices = self._store.search(query_vec, top_k)
        
        dense_results = []
        for idx in faiss_indices[0]:
            if 0 <= idx < len(self._chunks):
                dense_results.append(self._chunks[idx])

        # ==========================================
        # 2. BM25 SPARSE SEARCH (Exact Keywords)
        # ==========================================
        tokenized_query = query.lower().split(" ")
        bm25_scores = bm25.get_scores(tokenized_query)
        
        # Sort indices by BM25 score descending
        bm25_top_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
        
        sparse_results = []
        for idx in bm25_top_indices:
            if bm25_scores[idx] > 0: # Only grab it if there is at least one keyword match
                sparse_results.append(self._chunks[idx])

        # ==========================================
        # 3. HYBRID MERGE & DEDUPLICATE
        # ==========================================
        combined_pool = {}
        for chunk in dense_results + sparse_results:
            # Create a unique key for the chunk (using elapsed time and first 20 chars)
            chunk_key = f"{chunk.get('start_elapsed', 0)}_{chunk.get('text', '')[:20]}"
            if chunk_key not in combined_pool:
                combined_pool[chunk_key] = chunk

        # Return the broad combined pool. 
        # The AskEngine's Cross-Encoder will now perfectly rerank this elite dataset!
        return list(combined_pool.values())