import os
import json
import re
from rag.llm_provider import UniversalLLMProvider

class FlashcardEngine:
    def __init__(self):
        self.llm = UniversalLLMProvider(fallback_model="phi3:latest")

    def generate_flashcards(self, meeting_dir: str):
        print(f"[Flashcards] Generating for {meeting_dir}...")
        transcript_path = os.path.join(meeting_dir, "transcript_refined.json")
        
        if not os.path.exists(transcript_path):
            return [{"question": "Error: No transcript found.", "answer": "Please ensure the class was recorded and refined."}]

        response = None 
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Safely limit to 5000 chars so we don't blow up Ollama's memory
            text_block = " ".join([d.get("text", "") for d in data])[:5000]

            prompt = f"""
You are an elite academic tutor. Extract the 5 most important, testable concepts from the transcript below and turn them into flashcards.

You MUST reply ONLY with a valid JSON array of objects. Do not include markdown blocks like ```json. Do not include any introductory text. 

Format strictly like this:
[
  {{"question": "What is the primary function of the mitochondria?", "answer": "It is the powerhouse of the cell, generating most of the cell's supply of ATP."}},
  {{"question": "Define concept X.", "answer": "Concept X means Y."}}
]

Transcript:
{text_block}
"""
            # 🔥 FIX: Pass require_json=True to lock Ollama into formatting rules
            response = self.llm.generate_with_limit(prompt, max_tokens=1000, require_json=True)

            if not response:
                 return [{"question": "LLM Timeout.", "answer": "The local model failed to respond. Check if Ollama is running."}]

            # Robust JSON extraction (in case the LLM adds chatter or markdown)
            match = re.search(r'\[\s*{.*?}\s*\]', response, re.DOTALL)
            json_str = match.group(0) if match else response

            if not json_str:
                 return [{"question": "Formatting Error.", "answer": "The AI did not return parsable text."}]

            raw_cards = json.loads(json_str)
            
            # 🔥 FIX: Bulletproof Parsing Layer (Removed the duplicate code you had below this!)
            cards = []
            for c in raw_cards:
                if isinstance(c, dict):
                    q = c.get("question") or c.get("Question") or c.get("Q") or "⚠️ AI forgot to write the question."
                    a = c.get("answer") or c.get("Answer") or c.get("A") or "⚠️ AI forgot to write the answer."
                    cards.append({"question": str(q), "answer": str(a)})
                    
            if not cards:
                return [{"question": "No cards found.", "answer": "The AI returned JSON, but it was empty."}]

            return cards

        except Exception as e:
            print(f"[Flashcards Error] {e}")
            print(f"Raw LLM Output: {response}")
            return [{"question": "AI Generation Failed.", "answer": "The AI did not return a valid JSON format. Try again."}]