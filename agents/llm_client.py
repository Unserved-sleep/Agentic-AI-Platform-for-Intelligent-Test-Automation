import json
import os
import requests
from configs.config import GROQ_API_KEY, GROQ_MODEL
from shared.logger import get_logger

logger = get_logger("agents.llm_client")

class LLMClient:
    """Unified LLM Client using Groq API with Llama 3.3 70B and smart fallback."""

    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL

    def generate(self, prompt: str, system_prompt: str = "You are a helpful QA AI assistant.") -> str:
        """Call Groq API for completion."""
        if not self.api_key or self.api_key.startswith("your_"):
            logger.warning("No valid Groq API key provided. Using fallback logic.")
            return ""

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 3000
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                logger.info(f"Successfully generated LLM completion via Groq ({len(content)} chars).")
                return content
            else:
                logger.warning(f"Groq API error HTTP {response.status_code}: {response.text}")
                return ""
        except Exception as e:
            logger.error(f"Failed to call Groq API: {e}")
            return ""

llm_client = LLMClient()
