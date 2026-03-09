import os
import logging
import asyncio
from google import genai
from .rate_limit_manager import manager
from dotenv import load_dotenv

load_dotenv()

# Logger setup
logger = logging.getLogger("ai_service")
handler = logging.StreamHandler()
formatter = logging.Formatter('[AI] %(message)s')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Config (V4 Priority - Validated Strings)
MODEL_PRIORITY = [
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
]

# Support multiple keys
KEYS_ENV = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
API_KEYS = [k.strip() for k in KEYS_ENV.split(",") if k.strip()]

from google.genai import types

class GeminiService:
    """
    Central service for Gemini requests with sequential fallback 
    and API key rotation support.
    """
    def __init__(self):
        self.clients = {key: genai.Client(api_key=key) for key in API_KEYS}

    def extract_json(self, text: str) -> str:
        """Robustly extract JSON string (object or array) from AI response."""
        if not text: return None
        text = text.strip()
        
        # 1. try simple strip of fences (common case)
        if "```json" in text:
            try:
                content = text.split("```json")[1].split("```")[0].strip()
                if content: return content
            except: pass
        if "```" in text:
            try:
                content = text.split("```")[1].split("```")[0].strip()
                if content: return content
            except: pass
            
        # 2. Find first and last markers for both { and [
        # We find the earliest start and latest end that form a valid structure
        start_obj = text.find("{")
        start_arr = text.find("[")
        
        # Determine if we should look for { } or [ ]
        # If both exist, pick the one that starts first
        if start_obj != -1 and (start_arr == -1 or start_obj < start_arr):
            # Probably an object
            end_obj = text.rfind("}")
            if end_obj != -1:
                return text[start_obj:end_obj+1]
        elif start_arr != -1:
            # Probably an array
            end_arr = text.rfind("]")
            if end_arr != -1:
                return text[start_arr:end_arr+1]
            
        return text

    async def generate_content(self, prompt: str, system_instruction: str = None):
        """
        Attempts to generate content by trying models/keys one by one
        to conserve requests while maintaining reliability.
        """
        if not API_KEYS:
            logger.error("No Gemini API keys found in .env")
            return None

        # Try API keys one by one (External rotation)
        for key_index, api_key in enumerate(API_KEYS):
            # For each key, try models in priority order (Internal fallback)
            for model in MODEL_PRIORITY:
                if manager.can_use(api_key, model):
                    result = await self._single_attempt(api_key, model, prompt, system_instruction, key_index)
                    if result:
                        return result
                    else:
                        logger.warning(f"Quota exceeded or error → Fallback from {model}")
        
        logger.error("AI service temporarily unavailable. No working models/keys found.")
        return None

    async def _single_attempt(self, api_key: str, model: str, prompt: str, system_instruction: str, key_index: int):
        """A single targeted request to a model."""
        client = self.clients.get(api_key)
        if not client: return None

        logger.info(f"Trying model: {model} (KEY_{key_index + 1})...")
        try:
            # Using the async 'aio' sub-client with proper config types
            config = None
            if system_instruction:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1 # Low temperature for more predictable JSON
                )
            
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )
            
            if not response or not response.text:
                logger.warning(f"Empty response from {model}")
                return None

            # Record success
            manager.record_usage(api_key, model)
            logger.info(f"✅ Success: {model} (KEY_{key_index + 1}) - Response length: {len(response.text)}")
            return response.text
            
        except Exception as e:
            err_msg = str(e).lower()
            if "429" in err_msg or "quota" in err_msg or "resource_exhausted" in err_msg:
                logger.warning(f"❌ Quota Hit: {model} (KEY_{key_index + 1})")
                manager.mark_exhausted(api_key, model)
            else:
                logger.error(f"❌ Error: {model} (KEY_{key_index + 1}): {e}")
            return None

# Global Singleton
gemini_service = GeminiService()
