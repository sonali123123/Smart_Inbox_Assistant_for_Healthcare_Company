import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current folder or parent project root
env_paths = [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
]
for p in env_paths:
    if p.exists():
        load_dotenv(p)
        break

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Default model name: Gemini 3.5 Flash-Lite (per TRD & user specification)
MODEL_NAME = os.getenv("AI_MODEL_NAME", "gemini-3.5-flash-lite")
TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.1"))
MAX_REQUEST_SIZE = 25 * 1024 * 1024  # 25 MB

import time
import re
import logging

def get_genai_client():
    from google import genai
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please provide it in .env file.")
    return genai.Client(api_key=GEMINI_API_KEY)

def call_gemini_with_retry(client, model, contents, config, max_retries=4):
    """Call Gemini API with automatic exponential backoff on 429 RESOURCE_EXHAUSTED."""
    logger = logging.getLogger("ai-service")
    for attempt in range(1, max_retries + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < max_retries:
                delay = 10.0 * attempt
                delay_match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str, re.IGNORECASE)
                if not delay_match:
                    delay_match = re.search(r"retryDelay['\":\s]+(\d+)s?", err_str)
                if delay_match:
                    delay = max(float(delay_match.group(1)) + 1.5, 5.0)
                
                logger.warning(
                    f"Quota / Rate limit (429) hit on attempt {attempt}/{max_retries}. Waiting {delay:.1f}s before retrying..."
                )
                time.sleep(delay)
            else:
                raise

