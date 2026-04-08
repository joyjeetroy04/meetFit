import os
import json
import tiktoken
from typing import List, Dict, Any


class TranscriptChunker:
    """
    Converts merged transcript entries into overlapping semantic chunks.
    """

    def __init__(
        self,
        meeting_dir: str,
        chunk_size: int = 500,
        overlap: int = 100
    ):
        self.meeting_dir = meeting_dir
        self.chunk_size = chunk_size
        self.overlap = overlap

        self.transcript_path = os.path.join(meeting_dir, "transcript.json")
        self.refined_path = os.path.join(meeting_dir, "transcript_refined.json")

    # ==============================
    # PUBLIC API
    # ==============================

    def build_live_chunks(self) -> List[Dict[str, Any]]:
        """
        Uses transcript.json (merged live transcript).
        """
        entries = self._load_json(self.transcript_path)
        chunks = self._build_chunks(entries)
        self._save_chunks(chunks, "chunks_live.json")
        return chunks

    def build_final_chunks(self) -> List[Dict[str, Any]]:
        """
        Uses transcript_refined.json + visual transcript.
        """
        entries = self._load_final_entries()
        chunks = self._build_chunks(entries)
        self._save_chunks(chunks, "chunks_final.json")
        return chunks

    # ==============================
    # INTERNAL
    # ==============================

    def _load_json(self, path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(path):
            return []

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_final_entries(self) -> List[Dict[str, Any]]:
        """
        Combine refined transcript + visual notes
        """
        refined = self._load_json(self.refined_path)
        visual = self._load_json(
            os.path.join(self.meeting_dir, "visual_notes.json")
        )

        combined = []

        for entry in refined:
            combined.append({
                "text": entry.get("text", ""),
                "elapsed": self._time_to_seconds(entry.get("time", "00:00:00"))
            })

        for entry in visual:
            combined.append({
                "text": entry.get("text", ""),
                "elapsed": self._time_to_seconds(entry.get("time", "00:00:00"))
            })

        # Sort chronologically
        combined.sort(key=lambda x: x.get("elapsed", 0))

        return combined

    def _build_chunks(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Core chunking logic using accurate token limits.
        """
        # Use standard cl100k_base (widely standard for accurate approximation)
        enc = tiktoken.get_encoding("cl100k_base")
        
        # We will map tokens back to elapsed time
        full_text = ""
        timeline = []
        
        for entry in entries:
            text = entry.get("text", "").strip()
            elapsed = entry.get("elapsed")
            
            if not text:
                continue
                
            full_text += text + " "
            
            # Approximate mapping of time to text progression
            tokens_in_entry = len(enc.encode(text))
            timeline.extend([elapsed] * tokens_in_entry)

        tokens = enc.encode(full_text)
        
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]

            if not chunk_tokens:
                break

            chunk_text = enc.decode(chunk_tokens)

            start_elapsed = timeline[start] if start < len(timeline) else 0
            end_elapsed = timeline[min(end - 1, len(timeline) - 1)]

            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "start_elapsed": start_elapsed,
                "end_elapsed": end_elapsed
            })

            chunk_id += 1
            start += self.chunk_size - self.overlap

        return chunks

    def _save_chunks(self, chunks: List[Dict[str, Any]], filename: str):
        path = os.path.join(self.meeting_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _time_to_seconds(time_str: str) -> float:
        try:
            parts = list(map(int, time_str.split(":")))
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        except:
            return 0.0