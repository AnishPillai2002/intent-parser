from abc import ABC, abstractmethod
from google import genai
from google.genai import types

from app.utils.logging_util import logger
from app.config import settings

# ---------------------------------------------------------
# 1. ABSTRACT STRATEGY INTERFACE
# ---------------------------------------------------------
class LLMGenerationStrategy(ABC):
    """
    Interface for LLM generation strategies.
    Now simplified to just accept pre-built text prompts.
    """
    @abstractmethod
    async def generate_sql(self, system_prompt: str, user_prompt: str) -> str:
        pass


# ---------------------------------------------------------
# 2. GEMINI STRATEGY (Pure Executor)
# ---------------------------------------------------------
class GeminiStrategy(LLMGenerationStrategy):
    def __init__(self):
        # Initialize the new GenAI SDK client
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash" 

    async def generate_sql(self, system_prompt: str, user_prompt: str) -> str:
        """
        Executes the generation using Gemini 2.5 Flash.
        """
        try:
            # Combine the System Context and User Query.
            # We still place the user request at the end to utilize Recency Bias.
            full_prompt = f"""
{system_instruction_text(system_prompt)}

---
USER REQUEST:
"{user_prompt}"

YOUR SQL RESPONSE:
"""
            # Call Gemini using the Async Client (aio)
            #
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=full_prompt
            )

            if response.text:
                # Clean up markdown if present
                return response.text.replace("```sql", "").replace("```", "").strip()
            else:
                raise ValueError("Gemini returned an empty response.")
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            raise

def system_instruction_text(prompt: str) -> str:
    """Helper to ensure prompt is a clean string."""
    return prompt.strip()


# ---------------------------------------------------------
# 3. CUSTOM API STRATEGY (Pure Executor)
# ---------------------------------------------------------
class CustomAPIStrategy(LLMGenerationStrategy):
    def __init__(self):
        self.api_url = settings.CUSTOM_LLM_URL
        self.api_key = settings.CUSTOM_LLM_KEY

    async def generate_sql(self, system_prompt: str, user_prompt: str) -> str:
        """
        Executes the generation using a custom HTTP endpoint.
        """
        try:
            logger.info(f"Calling Custom LLM at {self.api_url}")
            
            # Example: Construct payload for a standard LLM endpoint
            # payload = {
            #     "messages": [
            #         {"role": "system", "content": system_prompt},
            #         {"role": "user", "content": user_prompt}
            #     ]
            # }
            # response = await httpx.post(self.api_url, json=payload, ...)
            
            return "SELECT * FROM placeholder_custom_api"
            
        except Exception as e:
            logger.error(f"Custom API generation failed: {str(e)}")
            raise