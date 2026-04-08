import os
import json
import threading
import re
from datetime import datetime
from rag.llm_provider import UniversalLLMProvider

class RAGEvaluator:
    def __init__(self):
        self.llm = UniversalLLMProvider(fallback_model="phi3:latest")
        self.log_file = "data/rag_metrics.json"
        
        if not os.path.exists("data"):
            os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.log_file):
            with open(self.log_file, "w") as f:
                json.dump([], f)

    def evaluate_async(self, question: str, context: str, answer: str):
        """Spins up a background thread so the user doesn't have to wait for the evaluation."""
        threading.Thread(target=self._run_eval, args=(question, context, answer), daemon=True).start()

    def _run_eval(self, question: str, context: str, answer: str):
        prompt = f"""
        You are an impartial AI auditor. Evaluate the following AI response based on the provided context.
        Score it from 1 to 5 on two metrics:
        1. Faithfulness: Did the AI rely ONLY on the provided context? (5 = Completely faithful, 1 = Hallucinated external facts)
        2. Relevance: Did the AI directly answer the user's question? (5 = Directly answered, 1 = Dodged the question)
        
        Return ONLY a JSON object in this exact format:
        {{"faithfulness": 5, "relevance": 4, "reasoning": "brief explanation"}}
        
        Context: {context[:2000]}
        Question: {question}
        Answer: {answer}
        """
        try:
            response = self.llm.generate_with_limit(prompt, max_tokens=300) or ""
            
            # Extract JSON
            match = re.search(r'\{.*?\}', response, re.DOTALL)
            if match:
                metrics = json.loads(match.group(0))
                metrics["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                metrics["question"] = question
                
                # Append to logs
                with open(self.log_file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
                logs.append(metrics)
                with open(self.log_file, "w", encoding="utf-8") as f:
                    json.dump(logs, f, indent=2)
                    
                print(f"📊 [RAG Eval Logged] Faithfulness: {metrics.get('faithfulness')}/5 | Relevance: {metrics.get('relevance')}/5")
        except Exception as e:
            print(f"⚠️ [RAG Eval Error] Failed to compute metrics: {e}")