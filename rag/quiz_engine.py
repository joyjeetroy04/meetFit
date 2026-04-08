import os
import json
from rag.llm_provider import UniversalLLMProvider 

class QuizEngine:
    def __init__(self):
        self.llm = UniversalLLMProvider(fallback_model="phi3:latest")

    def generate_quiz(self, meeting_dir: str):
        print(f"[Quiz] Generating for {meeting_dir}...")
        transcript_path = os.path.join(meeting_dir, "transcript_refined.json")
        
        if not os.path.exists(transcript_path):
            return [{"question": "Error: No transcript found.", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "Please ensure the class was recorded and refined."}]

        response = None
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Limit transcript size to avoid overwhelming local LLM memory
            text_block = " ".join([d.get("text", "") for d in data])[:5000]

            prompt = f"""
You are an expert professor. Generate a 5-question multiple-choice quiz based on the core concepts in the transcript below. 
The questions should test comprehension, not just rote memorization.

You MUST reply ONLY with a valid JSON array of objects. Do not include markdown blocks like ```json. Do not include any introductory text. 

Format strictly like this:
[
  {{
    "question": "What is the primary function of the mitochondria?", 
    "options": ["To synthesize proteins", "To generate ATP", "To store DNA", "To breakdown waste"],
    "answer": "To generate ATP",
    "explanation": "Mitochondria are known as the powerhouses of the cell because they generate most of the cell's supply of adenosine triphosphate (ATP)."
  }}
]

Transcript:
{text_block}
"""
            # 🔥 FIX: Pass require_json=True to lock Ollama into strict formatting
            response = self.llm.generate_with_limit(prompt, max_tokens=1500, require_json=True)

            if not response:
                 return [{"question": "LLM Timeout.", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "The local model failed to respond. Check if Ollama is running."}]

            # 🔥 FIX: Skip the Regex! Just load the JSON directly.
            raw_quiz = json.loads(response)
            
            # Bulletproof Parsing Layer (Catch LLM capitalization typos)
            quiz_data = []
            for q in raw_quiz:
                if isinstance(q, dict):
                    question_text = q.get("question") or q.get("Question") or "⚠️ AI forgot the question."
                    options = q.get("options") or q.get("Options") or ["Option 1", "Option 2", "Option 3", "Option 4"]
                    
                    # Ensure options is actually a list
                    if not isinstance(options, list):
                        options = [str(options), "B", "C", "D"]
                        
                    answer = q.get("answer") or q.get("Answer") or options[0] if options else "Unknown"
                    explanation = q.get("explanation") or q.get("Explanation") or "No explanation provided by AI."
                    
                    quiz_data.append({
                        "question": str(question_text), 
                        "options": [str(opt) for opt in options], 
                        "answer": str(answer),
                        "explanation": str(explanation)
                    })

            if not quiz_data:
                return [{"question": "No quiz data found.", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "The AI returned JSON, but it was empty."}]

            return quiz_data

        except Exception as e:
            print(f"[Quiz Error] {e}")
            print(f"Raw LLM Output: {response}")
            return [{"question": "AI Generation Failed.", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "The AI did not return a valid JSON format. Try again."}]