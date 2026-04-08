import os
import json
import re
from rag.llm_provider import UniversalLLMProvider

class ExamPredictor:
    def __init__(self):
        self.llm = UniversalLLMProvider(model="phi3:latest")

    def predict_exam_topics(self, meeting_dir: str):
        transcript_path = os.path.join(meeting_dir, "transcript_refined.json")
        if not os.path.exists(transcript_path):
            return []

        with open(transcript_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Logic: We grab the full text but focus on "importance" keywords
        full_text = " ".join([d.get('text', '') for d in data])[:9000]

        prompt = f"""
        You are an expert Professor's Assistant. Your goal is to predict potential exam questions.
        
        Analyze the lecture transcript below. Look for:
        - Phrases like "this will be on the test", "important concept", "remember this".
        - Concepts the professor spent the most time explaining.
        - Definitions or formulas highlighted as "fundamental".

        Return ONLY a JSON array of objects. No intro.
        Format: [ 
            {{
                "topic": "Title of concept", 
                "probability": "High/Medium", 
                "reasoning": "Why you think this is on the exam",
                "predicted_question": "A sample question based on this"
            }} 
        ]

        Transcript:
        {full_text}
        """
        
        response = self.llm.generate_with_limit(prompt, max_tokens=2000)
        if not response: return []

        try:
            match = re.search(r'\[\s*{.*?}\s*\]', response, re.DOTALL)
            json_str = match.group(0) if match else response
            return json.loads(json_str)
        except:
            return []