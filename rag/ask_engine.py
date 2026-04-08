import os
import tiktoken
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder

from rag.eval_engine import RAGEvaluator
from rag.retriever import MeetingRetriever
from rag.llm_provider import UniversalLLMProvider 
from rag.memory_manager import MemoryManager

_index_cache = {}

class AskEngine:
    """
    Orchestrates retrieval across meetings + LLM generation.
    """

    def __init__(self, base_data_dir: str = "data"):
        self.base_data_dir = base_data_dir
        self.llm = UniversalLLMProvider(fallback_model="phi3:latest")
        self.memory = MemoryManager(storage_dir=self.base_data_dir)
        self.last_results = []
        self.evaluator = RAGEvaluator()
        
        # 🔥 Upgraded to a true Cross-Encoder for highly accurate RAG reranking
        self.rerank_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

        # warm up model once
        try:
            self.llm.generate("Hello")
        except:
            pass

    # ==============================
    # PUBLIC API
    # ==============================

    def ask(
        self,
        question: str,
        selected_meetings: Optional[List[str]] = None,
        top_k_per_meeting: int = 1
    ) -> str:
        print("DEBUG → Question received:", question)
        print("DEBUG → Selected meetings:", selected_meetings)

        # Determine search scope
        if selected_meetings:
            meetings = []
            for m in selected_meetings:
                meeting_dir = os.path.join(self.base_data_dir, m)
                if os.path.exists(meeting_dir):
                    meetings.append(meeting_dir)
                else:
                    print("[AskEngine] Meeting not found:", m)
        else:
            meetings = self._discover_meetings()

        # DEBUG: show search scope
        print("\n🔎 SEARCH SCOPE:")
        for m in meetings:
            print("   ", m)
        print()

        all_results = []

        # Retrieval loop
        for meeting_dir in meetings:
            version = self._select_best_version(meeting_dir)
            if not version:
                continue

            if meeting_dir not in _index_cache:
                _index_cache[meeting_dir] = MeetingRetriever(meeting_dir, version=version)

            retriever = _index_cache[meeting_dir]
            results = retriever.retrieve(question, top_k=5)

            print("Results from", meeting_dir, "=", len(results))

            for r in results:
                r["meeting"] = os.path.basename(meeting_dir)

                # preserve slide metadata
                if "image" in r:
                    r["image"] = r["image"]

                if "timestamp" in r:
                    r["timestamp"] = r["timestamp"]

                all_results.append(r)

        if not all_results:
            return "I couldn't find relevant content in your meetings."

        # Rerank results using the Cross-Encoder
        all_results = self._rerank_results(question, all_results)[:5]
        
        chat_context = self.memory.get_formatted_history()
        prompt = self._build_prompt(question, all_results, chat_context)

        print("PROMPT LENGTH:", len(prompt))

        answer = self.llm.generate(prompt)

        return answer or "LLM failed to generate a response."

    def ask_stream(self, question: str, selected_meetings: Optional[List[str]] = None):
        """Identical to ask(), but yields tokens for real-time UI streaming."""
        
        if selected_meetings:
            meetings = [os.path.join(self.base_data_dir, m) for m in selected_meetings if os.path.exists(os.path.join(self.base_data_dir, m))]
        else:
            meetings = self._discover_meetings()

        all_results = []
        for meeting_dir in meetings:
            version = self._select_best_version(meeting_dir)
            if not version: continue

            if meeting_dir not in _index_cache:
                _index_cache[meeting_dir] = MeetingRetriever(meeting_dir, version=version)
            
            results = _index_cache[meeting_dir].retrieve(question, top_k=10)
            
            for r in results:
                r["meeting"] = os.path.basename(meeting_dir)
                all_results.append(r)

        if not all_results:
            yield "I couldn't find relevant content in your meetings."
            return

        all_results = self._rerank_results(question, all_results)[:10]
        self.last_results = all_results
        
        # 1. Fetch chat memory from disk
        chat_context = self.memory.get_formatted_history()
        
        # 2. Pass history into the prompt builder
        prompt = self._build_prompt(question, all_results, chat_context)

        full_answer = "" # 3. Create a buffer to capture the full response
        
        if hasattr(self.llm, "generate_stream"):
            for token in self.llm.generate_stream(prompt):
                full_answer += token # 4. Collect tokens
                yield token
        else:
            full_answer = self.llm.generate(prompt)
            yield full_answer

        # 5. Save this turn to disk and evaluate
        if full_answer and full_answer.strip():
            self.memory.add_turn("user", question)
            self.memory.add_turn("assistant", full_answer.strip())
            eval_context = "\n".join([c["text"] for c in all_results])
            self.evaluator.evaluate_async(question, eval_context, full_answer.strip())

    # ==============================
    # INTERNAL
    # ==============================
    def clear_cache(self, meeting_dir: str):
        """Forces the engine to drop the cached FAISS index so it reads the fresh live one."""
        if meeting_dir in _index_cache:
            del _index_cache[meeting_dir]
            print(f"[AskEngine] Cleared live cache for {os.path.basename(meeting_dir)}")

    def _discover_meetings(self) -> List[str]:
        if not os.path.exists(self.base_data_dir):
            return []

        return [
            os.path.join(self.base_data_dir, name)
            for name in os.listdir(self.base_data_dir)
            if os.path.isdir(os.path.join(self.base_data_dir, name))
        ]

    def _select_best_version(self, meeting_dir: str) -> str:
        final_index = os.path.join(meeting_dir, "vector_final.index")
        live_index = os.path.join(meeting_dir, "vector_live.index")

        if os.path.exists(final_index):
            return "final"
        elif os.path.exists(live_index):
            return "live"

        return ""

    def _rerank_results(self, question: str, results: list):
        if not results:
            return results

        # Format inputs as a list of [query, document] pairs
        pairs = [[question, r["text"]] for r in results]
        
        # CrossEncoder outputs raw logits/scores directly
        scores = self.rerank_model.predict(pairs)

        # Sort based on the CrossEncoder scores
        ranked = sorted(
            zip(results, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [r[0] for r in ranked]

    def _build_prompt(self, question: str, contexts: List[Dict[str, Any]], chat_context: str = "") -> str:
        enc = tiktoken.get_encoding("cl100k_base")
        MAX_CONTEXT_TOKENS = 2500

        context_text = "=== RETRIEVED KNOWLEDGE BASE ===\n"
        current_tokens = len(enc.encode(context_text))

        for i, c in enumerate(contexts):
            snippet = c["text"]
            meeting = c["meeting"]
            source = c.get("source", "transcript")

            if source == "slide":
                image_name = c.get("image", "unknown_slide.jpg")
                addition = (
                    f"SOURCE {i+1} [SLIDE]: File {image_name} from class @{meeting}\n"
                    f"Content: {snippet}\n\n"
                )
            else:
                start_sec = c.get("start_elapsed", 0)
                mins = int(start_sec // 60)
                secs = int(start_sec % 60)
                time_tag = f"[{mins:02d}:{secs:02d}]"

                addition = (
                    f"SOURCE {i+1} [AUDIO]: {time_tag} from class @{meeting}\n"
                    f"Content: {snippet}\n\n"
                )

            addition_tokens = len(enc.encode(addition))

            if current_tokens + addition_tokens > MAX_CONTEXT_TOKENS:
                print(f"[Context Manager] Token limit reached ({current_tokens}/{MAX_CONTEXT_TOKENS}).")
                break

            context_text += addition
            current_tokens += addition_tokens

        prompt = f"""You are an elite AI Study Operating System.
Your job is to answer the user's question using ONLY the provided knowledge base.

CRITICAL INSTRUCTIONS FOR CITATIONS (DO NOT IGNORE):
1. You MUST cite your sources inline.
2. Audio: @ClassName [MM:SS]
3. Slides: exact filename
4. NEVER hallucinate timestamps
5. Use **bold** for key terms

{chat_context}

Context:
{context_text}

Question:
{question}

Answer concisely with proper citations:
"""
        return prompt.strip()