import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

DEEPSEEK_API_BASE = "https://api.deepseek.com"

CRITIC_SYSTEM_PROMPT = """You are an expert content critic and editor. Your role is to:

1. Evaluate content for quality, clarity, accuracy, and effectiveness
2. Identify strengths and areas for improvement
3. Provide specific, actionable feedback
4. Suggest refined versions when appropriate

When critiquing content, consider:
- Clarity: Is the message clear and easy to understand?
- Structure: Is the content well-organized?
- Accuracy: Are facts and claims accurate?
- Tone: Is the tone appropriate for the intended audience?
- Completeness: Does it address all relevant points?
- Engagement: Is it compelling and interesting?

Provide your critique in a structured format with:
1. Overall Assessment (brief summary)
2. Strengths (what works well)
3. Areas for Improvement (specific issues)
4. Suggestions (actionable recommendations)
5. Refined Version (if applicable)"""


class ContentCritic:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=DEEPSEEK_API_BASE
        )
        self.model = "deepseek-chat"

    def _extract_usage(self, response) -> dict:
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
        
        return usage_data

    def critique(self, content: str, context: str = None,
                 focus_areas: list = None, max_tokens: int = 2000) -> dict:
        user_message = f"Please critique the following content:\n\n---\n{content}\n---"
        
        if context:
            user_message += f"\n\nOriginal request/context:\n{context}"
        
        if focus_areas:
            areas = ", ".join(focus_areas)
            user_message += f"\n\nPlease focus particularly on: {areas}"
        
        messages = [
            {"role": "system", "content": CRITIC_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.5
            )
            
            if not response.choices or len(response.choices) == 0:
                return {
                    "success": False,
                    "error": "No critique generated",
                    "critique": None
                }
            
            critique_content = response.choices[0].message.content
            
            return {
                "success": True,
                "critique": critique_content,
                "usage": self._extract_usage(response)
            }
        except Exception as e:
            logger.error(f"Critic API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "critique": None
            }

    def refine(self, original_content: str, critique: str, 
               instructions: str = None, max_tokens: int = 2000) -> dict:
        user_message = f"""Based on the following critique, please provide an improved version of the content.

Original Content:
---
{original_content}
---

Critique:
---
{critique}
---"""
        
        if instructions:
            user_message += f"\n\nAdditional instructions: {instructions}"
        
        user_message += "\n\nPlease provide the refined version:"
        
        messages = [
            {
                "role": "system", 
                "content": "You are an expert editor. Your task is to refine content based on critique feedback while maintaining the original intent and voice."
            },
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.6
            )
            
            if not response.choices or len(response.choices) == 0:
                return {
                    "success": False,
                    "error": "No refined content generated",
                    "refined_content": None
                }
            
            refined_content = response.choices[0].message.content
            
            return {
                "success": True,
                "refined_content": refined_content,
                "usage": self._extract_usage(response)
            }
        except Exception as e:
            logger.error(f"Refine API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "refined_content": None
            }


def get_critic() -> ContentCritic:
    return ContentCritic()
