import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

DEEPSEEK_API_BASE = "https://api.deepseek.com"


class ContentGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=DEEPSEEK_API_BASE
        )
        self.model = "deepseek-chat"

    def generate(self, prompt: str, system_prompt: str = None, 
                 context: str = None, max_tokens: int = 2000,
                 temperature: float = 0.7) -> dict:
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({
                "role": "system", 
                "content": "You are a helpful AI assistant that generates high-quality content."
            })
        
        user_content = prompt
        if context:
            user_content = f"Context from knowledge base:\n{context}\n\n---\n\nUser request:\n{prompt}"
        
        messages.append({"role": "user", "content": user_content})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if not response.choices or len(response.choices) == 0:
                return {
                    "success": False,
                    "error": "No response generated",
                    "content": None
                }
            
            content = response.choices[0].message.content
            
            usage_data = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
            
            if hasattr(response, 'usage') and response.usage is not None:
                usage_data = {
                    "prompt_tokens": getattr(response.usage, 'prompt_tokens', 0) or 0,
                    "completion_tokens": getattr(response.usage, 'completion_tokens', 0) or 0,
                    "total_tokens": getattr(response.usage, 'total_tokens', 0) or 0
                }
            
            return {
                "success": True,
                "content": content,
                "usage": usage_data
            }
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    def generate_with_persona(self, prompt: str, persona_prompt: str,
                              context: str = None, max_tokens: int = 2000,
                              temperature: float = 0.7) -> dict:
        return self.generate(
            prompt=prompt,
            system_prompt=persona_prompt,
            context=context,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def health_check(self) -> bool:
        try:
            result = self.generate("Say 'OK' if you're working.", max_tokens=10)
            return result.get("success", False)
        except Exception as e:
            logger.error(f"DeepSeek health check failed: {e}")
            return False


def get_generator() -> ContentGenerator:
    return ContentGenerator()
