import time
import logging
import google.generativeai as genai
from google.api_core import exceptions

logger = logging.getLogger(__name__)

def generate_content_with_retry(model, prompt, max_retries=3, initial_delay=5):
    """
    Generates content using the Gemini model with retry logic for rate limits.
    """
    retries = 0
    while retries <= max_retries:
        try:
            return model.generate_content(prompt)
        except exceptions.ResourceExhausted as e:
            wait_time = initial_delay * (2 ** retries)
            print(f"!!! [AI Helper] Rate Limit hit. Retrying in {wait_time}s... (Attempt {retries + 1}/{max_retries})")
            logger.warning(f"Rate limit hit. Waiting {wait_time}s. Error: {e}")
            time.sleep(wait_time)
            retries += 1
        except Exception as e:
            # For other errors, just re-raise or logging?
            # If it's a 429 that comes as a general exception (sometimes happens), handle it
            if "429" in str(e):
                wait_time = initial_delay * (2 ** retries)
                print(f"!!! [AI Helper] Rate Limit (Generic) hit. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                retries += 1
            else:
                raise e
    
    raise Exception("Max retries exceeded for AI generation")
