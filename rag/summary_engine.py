import os
import json
from typing import Optional
from rag.llm_provider import UniversalLLMProvider

class SummaryEngine:
    def __init__(self, model_name: str = "phi3:latest"):
        self.llm = UniversalLLMProvider()

    def summarize_meeting(self, meeting_dir: str, mode: str = "Executive Summary") -> Optional[str]:
        chunk_path = os.path.join(meeting_dir, "chunks_final.json")

        if not os.path.exists(chunk_path):
            return "No refined transcript found for this meeting."

        try:
            with open(chunk_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
        except Exception:
            return "Failed to load transcript data."

        if not chunks:
            return "No content available for summary."

        # Extract just the text
        all_text = [c.get("text", "") for c in chunks if c.get("text")]
        
        # Step 1: Map (Summarize in batches to fit context window)
        batch_summaries = []
        current_batch = ""
        
        # Roughly 6000 chars per batch is very safe for local LLMs
        for text in all_text:
            if len(current_batch) + len(text) > 6000:
                prompt = f"Summarize the key points of this part of the lecture concisely:\n\n{current_batch}"
                batch_summary = self.llm.generate_with_limit(prompt, max_tokens=500)
                if batch_summary:
                    batch_summaries.append(batch_summary)
                current_batch = text
            else:
                current_batch += "\n" + text
                
        # Catch the last batch
        if current_batch:
            prompt = f"Summarize the key points of this part of the lecture concisely:\n\n{current_batch}"
            batch_summary = self.llm.generate_with_limit(prompt, max_tokens=500)
            if batch_summary:
                batch_summaries.append(batch_summary)

        # Step 2: Reduce (Final Summary of Summaries)
        combined_summaries = "\n\n".join(batch_summaries)
        
        # 🔥 FIX: Dynamically inject the requested 'mode' into the prompt!
        final_prompt = f"""
        You are an academic assistant helping students revise lectures.
        Based on these sequential summaries of the lecture, write a clear, structured {mode}.

        Make sure your output specifically matches the format of a {mode}. 
        Include appropriate headings, bullet points, and clear paragraphs suitable for revision notes.

        Lecture Summaries:
        {combined_summaries}

        Final {mode}:
        """

        return self.llm.generate_with_limit(final_prompt, max_tokens=2500)