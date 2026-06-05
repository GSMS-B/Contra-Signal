import time
import logging
from groq import Groq
from openai import OpenAI
from backend.config import GROQ_API_KEY, OPENROUTER_API_KEY

logger = logging.getLogger(__name__)

# Initialize clients lazily or handle missing keys gracefully
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
or_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
) if OPENROUTER_API_KEY else None

def generate_content_with_fallback(prompt: str) -> str:
    """
    Generates content using a fallback chain:
    1. Groq (llama3-70b-8192)
    2. Groq (llama3-8b-8192)
    3. OpenRouter (openrouter/auto)
    """
    
    # 1. Primary: Groq 70B
    if groq_client:
        try:
            print("[AI Helper] Trying Primary: Groq llama-3.3-70b-versatile")
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq 70B failed: {e}")
            print(f"!!! [AI Helper] Groq 70B failed: {e}. Falling back to 8B...")

        # 2. Secondary: Groq 8B
        try:
            print("[AI Helper] Trying Secondary: Groq llama3-8b-8192")
            completion = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq 8B failed: {e}")
            print(f"!!! [AI Helper] Groq 8B failed: {e}. Falling back to OpenRouter...")

    # 3. Tertiary: OpenRouter Auto
    if or_client:
        try:
            print("[AI Helper] Trying Tertiary: OpenRouter Auto")
            completion = or_client.chat.completions.create(
                model="openrouter/auto",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenRouter Auto failed: {e}")
            print(f"!!! [AI Helper] OpenRouter Auto failed: {e}.")
            raise Exception("All models in the fallback chain failed.")
    
    raise Exception("No valid API clients configured for AI generation.")

# Legacy adapter for agents still using the old method signature
class DummyModel:
    pass

def generate_content_with_retry(model, prompt, max_retries=3, initial_delay=5):
    # Ignore the model parameter and just use the fallback chain
    # The fallback chain has its own retry-like mechanism via fallbacks.
    class DummyResponse:
        def __init__(self, text):
            self.text = text
    
    text = generate_content_with_fallback(prompt)
    return DummyResponse(text)
