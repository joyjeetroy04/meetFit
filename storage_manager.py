import os
import json
import time
from datetime import datetime


class StorageManager:
    def __init__(self, base_dir="meetings"):
        self.base_dir = "data"
        os.makedirs(self.base_dir, exist_ok=True)
        self.meeting_dir = None
        self.visual_file_path = None
        self.meta_file_path = None
        self.meeting_title = None
        self.start_time = None


    def start_new_meeting(self, class_title: str):
     print("DEBUG: start_new_meeting called")

     self.meeting_title = class_title
     self.start_time = time.time()

     date_str = datetime.now().strftime("%Y-%m-%d")
     safe_title = class_title.replace(" ", "_")
     folder_name = f"{date_str}_{safe_title}"

     print("DEBUG base_dir:", self.base_dir)

     self.meeting_dir = os.path.join(self.base_dir, folder_name)

     print("DEBUG meeting_dir before makedirs:", self.meeting_dir)

     os.makedirs(self.meeting_dir, exist_ok=True)

     print("DEBUG meeting_dir after makedirs:", self.meeting_dir)

     self.visual_file_path = os.path.join(self.meeting_dir, "visual_notes.json")
     self.meta_file_path = os.path.join(self.meeting_dir, "meta.json")

     meta = {
        "title": class_title,
        "date": date_str,
        "start_time": datetime.now().strftime("%H:%M:%S")
    }

     with open(self.meta_file_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

     print("[Storage] Meeting folder created:", self.meeting_dir)
     print("DEBUG inside storage: meeting_dir =", self.meeting_dir)




    # ================= SAVE METHODS =================

    def append_visual_text(self, text: str):
        if not self.visual_file_path:
            print("[Storage] Warning: Meeting not initialized. Skipping save.")
            return

        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "text": text,
            
            "type": "visual"  # ✅ added
        }

        try:
            with open(self.visual_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            data.append(entry)

            with open(self.visual_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            print(f"[Storage] Saved visual text at {entry['time']}")

        except Exception as e:
            print(f"[Storage] Error saving visual text: {e}")

    def append_audio_text(self, text: str, elapsed_seconds: float):
        if not self.meeting_dir:
            print("[Storage] Warning: Meeting not initialized. Skipping audio save.")
            return

        audio_file_path = os.path.join(self.meeting_dir, "audio_notes.json")

        if not os.path.exists(audio_file_path):
            with open(audio_file_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

        entry = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "elapsed": round(elapsed_seconds, 2),
            "text": text,
            "type": "audio"  # ✅ added
        }

        try:
            with open(audio_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            data.append(entry)

            with open(audio_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            print(f"[Storage] Saved audio text at {entry['time']}")

        except Exception as e:
            print(f"[Storage] Error saving audio text: {e}")
    def get_meeting_dir(self):
     if not self.meeting_dir:
        print("[Storage] WARNING: meeting_dir is None")
     return self.meeting_dir


    # ================= COMBINED LOADER =================

    def _load(self):
        if not self.meeting_dir:
            return []

        combined = []

        audio_file = os.path.join(self.meeting_dir, "audio_notes.json")
        visual_file = os.path.join(self.meeting_dir, "visual_notes.json")

        try:
            if os.path.exists(audio_file):
                with open(audio_file, "r", encoding="utf-8") as f:
                    audio = json.load(f)
                    combined.extend(audio)

            if os.path.exists(visual_file):
                with open(visual_file, "r", encoding="utf-8") as f:
                    visual = json.load(f)
                    combined.extend(visual)

            # Sort by time
            combined.sort(key=lambda x: x["time"])
            return combined

        except Exception as e:
            print(f"[Storage] Error loading transcript: {e}")
            return []

    # ================= SESSION STATS =================

    def get_session_stats(self):
        transcript = self._load()

        duration = "-"
        if transcript:
            start = transcript[0]["time"]
            end = transcript[-1]["time"]
            duration = f"{start} → {end}"

        return {
            "title": self.meeting_title or "Unknown",
            "start_time": transcript[0]["time"] if transcript else "-",
            "duration": duration,
            "entries": len(transcript)
        }
        
        # ================= TIMELINE =================

    def load_best_timeline(self):
     """
    Returns the best available transcript:
    refined > merged > audio_notes
    Safe against partial writes.
    """
     if not self.meeting_dir:
        return []

     refined = os.path.join(self.meeting_dir, "transcript_refined.json")
     merged = os.path.join(self.meeting_dir, "transcript.json")
     audio = os.path.join(self.meeting_dir, "audio_notes.json")

     paths = [refined, merged, audio]
 
     for path in paths:
        if not os.path.exists(path):
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Normalize shape
            cleaned = []
            for x in data:
                cleaned.append({
                    "time": x.get("time", "??:??:??"),
                    "text": x.get("text", "").strip(),
                    "elapsed": x.get("elapsed", None),
                    "type": x.get("type", "audio")
                })

            if cleaned:
                return cleaned

        except Exception as e:
            print(f"[Storage] Timeline read failed for {path}: {e}")
            continue

     return []
    def load_timeline(self):
     return self._load()
