import os
import json
import requests
from typing import Optional

class UniversalLLMProvider:
    """
    Universal LLM provider that reads user settings and seamlessly routes 
    requests to Local Ollama, OpenAI, Anthropic, or OpenRouter.
    Includes Auto-Detection logic for API keys.
    """
    def __init__(self, fallback_model="phi3:latest"):
        self.engine = "Local Ollama"
        self.api_key = ""
        self.ollama_model = fallback_model
        
        # 1. Load the user's choices from the Settings UI
        config_path = "data/config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    saved_engine = config.get("engine", "Local Ollama")
                    self.api_key = config.get("api_key", "").strip()

                    # 2. 🔥 AUTO-DETECT LOGIC
                    if saved_engine == "Auto-Detect (Paste Key)" and self.api_key:
                        self.engine = self._detect_provider(self.api_key)
                        print(f"[LLMProvider] Auto-Detect: Recognized key as {self.engine}")
                    else:
                        self.engine = saved_engine
                        
            except Exception as e:
                print(f"[LLMProvider] Error reading config: {e}")

    def _detect_provider(self, key: str) -> str:
        """Analyzes API key prefix to automatically set the engine."""
        if key.startswith("sk-ant-"):
            return "Anthropic (Claude 3.5)"
        elif key.startswith("sk-or-"):
            return "OpenRouter"
        elif key.startswith("sk-") and len(key) > 40:
            return "OpenAI (GPT-4o)"
        elif key.startswith("xai-"):
            return "OpenRouter" # Defaults to OpenRouter for X.ai
        
        # Fallback if detection fails
        return "OpenAI (GPT-4o)"

    # ==============================
    # PUBLIC API
    # ==============================
    def generate(self, prompt: str, require_json: bool = False) -> Optional[str]:
        return self._generate_internal(prompt, max_tokens=4000, require_json=require_json)

    def generate_with_limit(self, prompt: str, max_tokens: int, require_json: bool = False) -> Optional[str]:
        return self._generate_internal(prompt, max_tokens=max_tokens, require_json=require_json)

    # ==============================
    # TRUE STREAMING GENERATOR
    # ==============================
    def generate_stream(self, prompt: str, max_tokens: int = 4000):
        """Yields tokens in real-time based on the selected engine."""
        
        # --- 1. LOCAL OLLAMA STREAMING ---
        if "Ollama" in self.engine:
            payload = {"model": self.ollama_model, "prompt": prompt, "stream": True}
            try:
                response = requests.post("http://localhost:11434/api/generate", json=payload, stream=True, timeout=180)
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
            except Exception as e:
                yield f"\n[Ollama Error: {e}]"

        # --- 2. OPENAI STREAMING ---
        elif "OpenAI" in self.engine:
            if not self.api_key:
                yield "\n[Error: OpenAI API Key missing.]"
                return
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "stream": True, "max_tokens": max_tokens}
            try:
                response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, stream=True, timeout=180)
                response.raise_for_status()
                for line in response.iter_lines():
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data: ") and "[DONE]" not in decoded:
                        chunk = json.loads(decoded[6:])
                        if "content" in chunk["choices"][0]["delta"]:
                            yield chunk["choices"][0]["delta"]["content"]
            except Exception as e:
                yield f"\n[OpenAI Error: {e}]"

        # --- 3. ANTHROPIC STREAMING ---
        elif "Anthropic" in self.engine:
            if not self.api_key:
                yield "\n[Error: Anthropic API Key missing.]"
                return
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
            payload = {"model": "claude-3-5-sonnet-20240620", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "stream": True}
            try:
                response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, stream=True, timeout=180)
                response.raise_for_status()
                for line in response.iter_lines():
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data: "):
                        chunk = json.loads(decoded[6:])
                        if chunk.get("type") == "content_block_delta":
                            yield chunk["delta"]["text"]
            except Exception as e:
                yield f"\n[Anthropic Error: {e}]"

        # --- 4. OPENROUTER STREAMING ---
        elif "OpenRouter" in self.engine:
            if not self.api_key:
                yield "\n[Error: OpenRouter API Key missing.]"
                return
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "AI Study OS",
                "Content-Type": "application/json"
            }
            # Change model to "deepseek/deepseek-chat" or "openrouter/auto"
            payload = {"model": "openrouter/auto", "messages": [{"role": "user", "content": prompt}], "stream": True}
            try:
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, stream=True, timeout=180)
                response.raise_for_status()
                for line in response.iter_lines():
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data: ") and "[DONE]" not in decoded:
                        chunk = json.loads(decoded[6:])
                        if "choices" in chunk and "content" in chunk["choices"][0]["delta"]:
                            yield chunk["choices"][0]["delta"]["content"]
            except Exception as e:
                yield f"\n[OpenRouter Error: {e}]"

    # ==============================
    # INTERNAL CORE GENERATOR
    # ==============================
    def _generate_internal(self, prompt: str, max_tokens: int, require_json: bool = False) -> Optional[str]:
        print(f"🚀 Routing request to: {self.engine}")
        
        if "Ollama" in self.engine:
            payload = {"model": self.ollama_model, "prompt": prompt, "stream": False, "options": {"num_predict": max_tokens}}
            if require_json: payload["format"] = "json"
            try:
                response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=180)
                return response.json().get("response", "").strip()
            except Exception as e:
                print(f"❌ [Ollama Error] {e}")
                return None

        elif "OpenAI" in self.engine:
            if not self.api_key: return None
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
            if require_json: payload["response_format"] = {"type": "json_object"}
            try:
                response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=180)
                return response.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"❌ [OpenAI Error] {e}")
                return None

        elif "Anthropic" in self.engine:
            if not self.api_key: return None
            headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
            messages = [{"role": "user", "content": prompt}]
            if require_json: messages.append({"role": "assistant", "content": "{"})
            payload = {"model": "claude-3-5-sonnet-20240620", "messages": messages, "max_tokens": max_tokens}
            try:
                response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=180)
                result = response.json()["content"][0]["text"].strip()
                return "{" + result if require_json and not result.startswith("{") else result
            except Exception as e:
                print(f"❌ [Anthropic Error] {e}")
                return None

        elif "OpenRouter" in self.engine:
            if not self.api_key: return None
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": "openrouter/auto", "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
            try:
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=180)
                return response.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"❌ [OpenRouter Error] {e}")
                return None