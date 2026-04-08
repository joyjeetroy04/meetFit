import json
import os
from typing import List, Dict, Any
from datetime import timedelta
import whisper


class RefinementEngine:
    """
    Post-meeting refinement engine.
    Converts full audio into a clean, academic transcript.
    """

    def __init__(self, meeting_dir: str, model_size: str = "small"):
        self.meeting_dir = meeting_dir
        self.audio_path = os.path.join(meeting_dir, "audio_raw.wav")
        self.output_path = os.path.join(meeting_dir, "transcript_refined.json")

        if not os.path.exists(self.audio_path):
            raise FileNotFoundError(f"Audio file not found: {self.audio_path}")

        print(f"[Refinement] Loading Whisper model ({model_size})...")
        self.model = whisper.load_model(model_size)

    def run(self) -> None:
        print("[Refinement] Refinement started...")

        result = self.model.transcribe(
            self.audio_path,
            fp16=False,
            language="en",
            task="transcribe",
            temperature=0.0,
            initial_prompt="This is a formal academic lecture transcript, transcribe all spoken content clearly.",
            verbose=True
        )

        segments = result.get("segments", [])
        if not isinstance(segments, list):
            segments = []

        refined_entries = self._build_entries(segments)
        self._save(refined_entries)

        print(f"[Refinement] Completed. Saved to {self.output_path}")

    def _build_entries(self, segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []

        for seg in segments:
            text = seg.get("text", "").strip()
            if not text:
                continue

            start_time = self._format_time(seg.get("start", 0.0))

            entries.append({
                "time": start_time,
                "speaker": "Teacher",
                "text": text
            })

        return entries

    @staticmethod
    def _format_time(seconds: float) -> str:
        td = timedelta(seconds=int(seconds))
        total_seconds = int(td.total_seconds())

        hrs = total_seconds // 3600
        mins = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        return f"{hrs:02d}:{mins:02d}:{secs:02d}"

    def _save(self, entries: List[Dict[str, Any]]) -> None:
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
