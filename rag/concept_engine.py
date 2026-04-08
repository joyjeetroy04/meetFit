import os
import json
from rag.llm_provider import UniversalLLMProvider

class ConceptEngine:
    def __init__(self):
        self.llm = UniversalLLMProvider(fallback_model="phi3:latest")

    def extract_syllabus(self, meeting_dir: str):
        transcript_path = os.path.join(meeting_dir, "transcript_refined.json")
        if not os.path.exists(transcript_path):
            return [{"title": "Error", "explanation": "Transcript not found.", "importance": "N/A"}]

        with open(transcript_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        full_text = " ".join([d.get('text', '') for d in data])[:8000]

        prompt = f"""
You are an expert academic coordinator. Analyze this lecture transcript and extract a structured syllabus of core concepts.

For each concept, provide:
1. A clear title.
2. A 2-sentence simple explanation.
3. Importance level (High/Medium/Low).

You MUST reply ONLY with a valid JSON array of objects. Do not include markdown blocks like ```json.
Format strictly like this:
[
  {{"title": "Cellular Respiration", "explanation": "The process by which cells convert nutrients into energy.", "importance": "High"}}
]

Transcript: {full_text}
"""
        # 🔥 FIX: Use require_json=True and ditch the Regex!
        response = self.llm.generate_with_limit(prompt, max_tokens=1500, require_json=True)
        
        if not response:
            return [{"title": "LLM Timeout", "explanation": "The local model failed to respond.", "importance": "High"}]
            
        try:
            raw_concepts = json.loads(response)
            
            # 🔥 FIX: Bulletproof parsing layer (Handles LLM typos)
            concepts = []
            for c in raw_concepts:
                if isinstance(c, dict):
                    title = c.get("title") or c.get("Title") or "Unknown Concept"
                    explanation = c.get("explanation") or c.get("Explanation") or "No explanation provided."
                    importance = c.get("importance") or c.get("Importance") or "Medium"
                    
                    concepts.append({
                        "title": str(title),
                        "explanation": str(explanation),
                        "importance": str(importance)
                    })
                    
            if not concepts:
                 return [{"title": "Extraction Error", "explanation": "The AI returned an empty list.", "importance": "N/A"}]

            return concepts
            
        except Exception as e:
            print(f"[Concept Engine Error] {e}\nRaw Output: {response}")
            return [{"title": "Extraction Error", "explanation": "AI failed to format JSON.", "importance": "N/A"}]