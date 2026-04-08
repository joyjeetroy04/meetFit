import json
import os
from datetime import datetime
from typing import Literal, List, Dict, Any

class MergeEngine:
    def __init__(self, meeting_dir: str):
        self.meeting_dir: str = meeting_dir
        self.transcript_path: str = os.path.join(meeting_dir, "transcript.json")
        self.live_path = os.path.join(self.meeting_dir, "live_transcript.json")
        
        if not os.path.exists(self.live_path):
             with open(self.live_path, "w", encoding="utf-8") as f:
                 json.dump([], f)

        if not os.path.exists(self.transcript_path):
            with open(self.transcript_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

    # --- NEW METHOD: This fixes the Pylance Error ---
    def merge(self, transcript_chunks: List[Dict], slide_chunks: List[Dict]) -> List[Dict]:
        """
        Combines transcripts and slide OCR data into a single list.
        Each chunk is marked with a 'source' so the RAG knows where it came from.
        """
        final_list = []

        # Add transcript chunks
        for chunk in transcript_chunks:
            chunk["source"] = "transcript"
            final_list.append(chunk)

        # Add slide chunks
        for chunk in slide_chunks:
            chunk["source"] = "slides"
            # Ensure slides have a 'text' field so the embedder can read them
            if "text" not in chunk and "content" in chunk:
                chunk["text"] = chunk["content"]
            final_list.append(chunk)

        # Sort by timestamp (elapsed seconds) so the context remains chronological
        final_list.sort(key=lambda x: x.get("elapsed", 0))

        return final_list

    def _load(self) -> List[Dict[str, Any]]:
        with open(self.transcript_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: List[Dict[str, Any]]) -> None:
        with open(self.transcript_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _append_live(self, entry):
       try:
            with open(self.live_path, "r", encoding="utf-8") as f:
                live = json.load(f)
            live.append(entry)
            with open(self.live_path, "w", encoding="utf-8") as f:
                json.dump(live, f, indent=2)
       except Exception as e:
            print("[Live Transcript Error]", e)

    def add_entry(self, text: str, entry_type: Literal["audio", "visual"], elapsed_seconds: float) -> None:
        cleaned_text = text.strip()
        if not cleaned_text:
            return
    
        entry: Dict[str, Any] = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "elapsed": round(elapsed_seconds, 2),
            "type": entry_type,
            "text": cleaned_text
        }

        data = self._load()
        data.append(entry)
        self._save(data)
        self._append_live(entry)

    def get_session_stats(self):
        data = self._load()
        stats = {
            "total": len(data),
            "audio": 0,
            "visual": 0
        }
        for entry in data:
            if entry["type"] == "audio":
                stats["audio"] += 1
            elif entry["type"] == "visual":
                stats["visual"] += 1
        return stats