import os
import json

class MemoryManager:
    """
    Manages persistent chat history with a sliding window compression.
    """
    def __init__(self, storage_dir="data", max_pairs=4):
        # max_pairs = 4 means it remembers the last 4 Questions AND 4 Answers
        self.filepath = os.path.join(storage_dir, "global_chat_history.json")
        self.max_pairs = max_pairs 
        self.history = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Memory] Failed to load history: {e}")
        return []

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"[Memory] Failed to save history: {e}")

    def add_turn(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        
        # Compression: Keep only the most recent (max_pairs * 2) messages
        max_messages = self.max_pairs * 2
        if len(self.history) > max_messages:
            self.history = self.history[-max_messages:]
            
        self._save()

    def get_formatted_history(self) -> str:
        if not self.history:
            return ""
            
        formatted = "=== RECENT CONVERSATION HISTORY ===\n"
        for msg in self.history:
            role_name = "User" if msg["role"] == "user" else "AI Assistant"
            formatted += f"{role_name}: {msg['content']}\n\n"
            
        return formatted.strip() + "\n\n"
    
    def clear_memory(self):
        self.history = []
        self._save()